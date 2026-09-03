"""
classification_trainer.py — Full training loop for EfficientNet-B0 classifier.

Features:
 - GPU/CPU autodetect
 - Configurable epochs, batch size, LR, optimizer, scheduler
 - Best-model checkpointing (by val accuracy)
 - Early stopping
 - Resume from checkpoint
 - Deterministic seed
 - Per-epoch train/val logging
 - Balanced class weighting (computed from training split labels only)
 - Staged transfer learning (freeze backbone → train head → unfreeze → fine-tune)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.seed_utils import set_seed

log = get_logger(__name__)


class ClassificationTrainer:
    """
    Parameters
    ----------
    model       : nn.Module (KidneyClassifier)
    cfg         : full training config dict (from settings.py)
    weights_dir : directory to save checkpoints
    """

    def __init__(
        self,
        model: nn.Module,
        cfg: Dict,
        weights_dir: str | Path,
    ):
        self.model = model
        self.cfg = cfg["classification"]
        self.full_cfg = cfg
        self.weights_dir = Path(weights_dir)
        self.weights_dir.mkdir(parents=True, exist_ok=True)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        log.info("ClassificationTrainer initialized", device=str(self.device))

        seed = cfg.get("seed", 42)
        deterministic = cfg.get("deterministic", True)
        set_seed(seed, deterministic)

        self.model.to(self.device)

        self.best_val_acc = 0.0
        self.epochs_no_improve = 0
        self.history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

        # Will be set up after we know class weights (need train loader)
        self.optimizer = None
        self.scheduler = None
        self.criterion = None

    # ── Class weight computation ───────────────────────────────────────────────

    def _compute_class_weights(self, train_loader: DataLoader) -> Optional[torch.Tensor]:
        """
        Compute balanced class weights from training labels ONLY.
        Uses the sklearn 'balanced' formula:
            weight[c] = n_samples / (n_classes * count[c])
        """
        cw_cfg = self.cfg.get("class_weighting", {})
        if not cw_cfg.get("enabled", False):
            return None

        strategy = cw_cfg.get("strategy", "balanced").lower()
        if strategy == "none":
            return None

        log.info("Computing class weights from training split …")
        label_counts: Dict[int, int] = {}
        for _, labels in train_loader:
            for lbl in labels.tolist():
                label_counts[lbl] = label_counts.get(lbl, 0) + 1

        num_classes = self.cfg.get("num_classes", 4)
        class_names = self.cfg.get("class_names", ["Normal", "Cyst", "Stone", "Tumor"])
        n_samples = sum(label_counts.values())

        weights = []
        for i in range(num_classes):
            count = label_counts.get(i, 1)
            w = n_samples / (num_classes * count)
            weights.append(w)
            log.info(
                f"  Class weight",
                cls=class_names[i] if i < len(class_names) else str(i),
                count=count,
                weight=f"{w:.4f}",
            )

        return torch.tensor(weights, dtype=torch.float32).to(self.device)

    # ── Optimizer / scheduler / loss setup ────────────────────────────────────

    def _setup_training(
        self,
        class_weights: Optional[torch.Tensor] = None,
        staged_head_only: bool = False,
    ) -> None:
        """
        Configure optimizer, scheduler, and loss.

        Parameters
        ----------
        class_weights    : optional weight tensor for CrossEntropyLoss
        staged_head_only : if True, use head_lr and only pass head params
        """
        c = self.cfg
        tl_cfg = c.get("transfer_learning", {})
        strategy = tl_cfg.get("strategy", "standard").lower()

        lr = float(c.get("learning_rate", 1e-3))
        wd = float(c.get("weight_decay", 1e-4))
        opt_name = c.get("optimizer", "adamw").lower()

        if staged_head_only:
            head_lr = float(tl_cfg.get("head_lr", lr))
            params = self.model.head.parameters()
            effective_lr = head_lr
            log.info("Staged TL — Stage 1: training HEAD only", head_lr=head_lr)
        elif strategy == "staged" and not staged_head_only:
            # Stage 2: two param groups — backbone at backbone_lr, head at head_lr
            head_lr = float(tl_cfg.get("head_lr", lr))
            backbone_lr = float(tl_cfg.get("backbone_lr", lr * 0.01))
            log.info(
                "Staged TL — Stage 2: full fine-tune",
                backbone_lr=backbone_lr,
                head_lr=head_lr,
            )
            param_groups = [
                {"params": self.model.backbone.parameters(), "lr": backbone_lr, "weight_decay": wd},
                {"params": self.model.head.parameters(),     "lr": head_lr,     "weight_decay": wd},
            ]
            if opt_name == "adamw":
                self.optimizer = torch.optim.AdamW(param_groups)
            elif opt_name == "adam":
                self.optimizer = torch.optim.Adam(param_groups)
            else:
                self.optimizer = torch.optim.SGD(param_groups, momentum=0.9)
            effective_lr = backbone_lr  # for scheduler T_max reference only
            params = None  # already set above
        else:
            params = self.model.parameters()
            effective_lr = lr

        # Single param-group path
        if params is not None:
            if opt_name == "adamw":
                self.optimizer = torch.optim.AdamW(params, lr=effective_lr, weight_decay=wd)
            elif opt_name == "adam":
                self.optimizer = torch.optim.Adam(params, lr=effective_lr, weight_decay=wd)
            else:
                self.optimizer = torch.optim.SGD(params, lr=effective_lr, weight_decay=wd, momentum=0.9)

        # Scheduler
        sched = c.get("scheduler", "cosine_annealing").lower()
        t_max = c.get("scheduler_T_max", c.get("num_epochs", 50))
        if sched == "cosine_annealing":
            self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, T_max=t_max
            )
        elif sched == "step":
            self.scheduler = torch.optim.lr_scheduler.StepLR(
                self.optimizer, step_size=10, gamma=0.5
            )
        else:
            self.scheduler = None

        # Loss
        self.criterion = nn.CrossEntropyLoss(weight=class_weights)

    # ── Epoch loops ───────────────────────────────────────────────────────────

    def _train_epoch(self, loader: DataLoader) -> Dict[str, float]:
        self.model.train()
        total_loss, correct, total = 0.0, 0, 0
        for images, labels in tqdm(loader, desc="Train", leave=False):
            images, labels = images.to(self.device), labels.to(self.device)
            self.optimizer.zero_grad()
            logits = self.model(images)
            loss = self.criterion(logits, labels)
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item() * images.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += images.size(0)

        return {"loss": total_loss / total, "acc": correct / total}

    @torch.no_grad()
    def _val_epoch(self, loader: DataLoader) -> Dict[str, float]:
        self.model.eval()
        total_loss, correct, total = 0.0, 0, 0
        for images, labels in tqdm(loader, desc="Val  ", leave=False):
            images, labels = images.to(self.device), labels.to(self.device)
            logits = self.model(images)
            loss = self.criterion(logits, labels)
            total_loss += loss.item() * images.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += images.size(0)
        return {"loss": total_loss / total, "acc": correct / total}

    # ── Checkpoint management ─────────────────────────────────────────────────

    def _save_checkpoint(self, epoch: int, is_best: bool = False) -> None:
        state = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "best_val_acc": self.best_val_acc,
            "history": self.history,
        }
        latest = self.weights_dir / "latest_checkpoint.pth"
        torch.save(state, latest)
        if is_best:
            best = self.weights_dir / "best_model.pth"
            torch.save(state, best)
            log.info("New best model saved", epoch=epoch, val_acc=self.best_val_acc)

    def load_checkpoint(self, checkpoint_path: str | Path) -> int:
        """Load checkpoint and return the next epoch to continue from."""
        ckpt = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        if self.optimizer and "optimizer_state_dict" in ckpt:
            self.optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        self.best_val_acc = ckpt.get("best_val_acc", 0.0)
        self.history = ckpt.get("history", self.history)
        start_epoch = ckpt["epoch"] + 1
        log.info("Checkpoint loaded", resume_from_epoch=start_epoch)
        return start_epoch

    # ── Core epoch loop ───────────────────────────────────────────────────────

    def _run_epochs(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int,
        start_epoch: int,
    ) -> None:
        patience = self.cfg.get("early_stopping_patience", 10)
        min_delta = float(self.cfg.get("early_stopping_min_delta", 0.001))

        for epoch in range(start_epoch, start_epoch + num_epochs):
            train_metrics = self._train_epoch(train_loader)
            val_metrics = self._val_epoch(val_loader)

            if self.scheduler:
                self.scheduler.step()

            self.history["train_loss"].append(train_metrics["loss"])
            self.history["train_acc"].append(train_metrics["acc"])
            self.history["val_loss"].append(val_metrics["loss"])
            self.history["val_acc"].append(val_metrics["acc"])

            is_best = val_metrics["acc"] > self.best_val_acc + min_delta
            if is_best:
                self.best_val_acc = val_metrics["acc"]
                self.epochs_no_improve = 0
            else:
                self.epochs_no_improve += 1

            self._save_checkpoint(epoch, is_best=is_best)

            log.info(
                f"Epoch {epoch + 1}/{start_epoch + num_epochs}",
                train_loss=f"{train_metrics['loss']:.4f}",
                train_acc=f"{train_metrics['acc']:.4f}",
                val_loss=f"{val_metrics['loss']:.4f}",
                val_acc=f"{val_metrics['acc']:.4f}",
                best_val_acc=f"{self.best_val_acc:.4f}",
            )

            if self.epochs_no_improve >= patience:
                log.info("Early stopping triggered", patience=patience)
                break

    # ── Public train entry point ──────────────────────────────────────────────

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: Optional[int] = None,
        start_epoch: int = 0,
    ) -> Dict:
        """
        Run the full training loop.

        Supports:
        - Standard training (strategy: standard)
        - Staged transfer learning (strategy: staged)
        - Balanced class weighting (class_weighting.enabled: true)
        """
        epochs = num_epochs or self.cfg.get("num_epochs", 50)
        tl_cfg = self.cfg.get("transfer_learning", {})
        tl_strategy = tl_cfg.get("strategy", "standard").lower()

        # Compute class weights from training data (if enabled)
        class_weights = self._compute_class_weights(train_loader)

        if tl_strategy == "staged":
            # ── Stage 1: freeze backbone, train head ──────────────────────────
            head_epochs = int(tl_cfg.get("head_epochs", 10))
            self.model.freeze_backbone()
            self._setup_training(class_weights=class_weights, staged_head_only=True)

            log.info(
                f"Staged TL Stage 1/{head_epochs} epochs (backbone frozen)"
            )
            self._run_epochs(train_loader, val_loader, head_epochs, start_epoch)

            # ── Stage 2: unfreeze backbone, fine-tune ─────────────────────────
            self.model.unfreeze_backbone()
            self.epochs_no_improve = 0  # reset early-stopping counter
            self._setup_training(class_weights=class_weights, staged_head_only=False)

            remaining = epochs - head_epochs
            if remaining > 0:
                log.info(
                    f"Staged TL Stage 2/{remaining} epochs (full fine-tune)"
                )
                self._run_epochs(
                    train_loader, val_loader, remaining,
                    start_epoch + head_epochs,
                )
        else:
            # ── Standard training ─────────────────────────────────────────────
            self._setup_training(class_weights=class_weights, staged_head_only=False)
            self._run_epochs(train_loader, val_loader, epochs, start_epoch)

        # Save training history
        history_path = self.weights_dir / "training_history.json"
        with open(history_path, "w") as f:
            json.dump(self.history, f, indent=2)

        log.info("Training complete", best_val_acc=self.best_val_acc)
        return self.history
