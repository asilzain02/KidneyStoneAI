"""
segmentation_trainer.py — Full training loop for U-Net segmentation.

Features:
 - GPU/CPU autodetect
 - Configurable loss (Dice / BCE / Dice+BCE)
 - Dice Score tracked for best-model selection
 - Checkpointing + early stopping + resume
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.losses import get_segmentation_loss
from utils.logger import get_logger
from utils.seed_utils import set_seed

log = get_logger(__name__)


def _dice_score(pred: torch.Tensor, target: torch.Tensor, smooth: float = 1.0) -> float:
    pred_bin = (pred > 0.5).float()
    intersection = (pred_bin * target).sum()
    return (
        (2.0 * intersection + smooth) / (pred_bin.sum() + target.sum() + smooth)
    ).item()


class SegmentationTrainer:
    def __init__(
        self,
        model: nn.Module,
        cfg: Dict,
        weights_dir: str | Path,
    ):
        self.model = model
        self.cfg = cfg["segmentation"]
        self.weights_dir = Path(weights_dir)
        self.weights_dir.mkdir(parents=True, exist_ok=True)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        log.info("SegmentationTrainer initialized", device=str(self.device))

        set_seed(cfg.get("seed", 42), cfg.get("deterministic", True))
        self.model.to(self.device)
        self._setup_training(cfg)

        self.best_dice = 0.0
        self.epochs_no_improve = 0
        self.history: Dict = {
            "train_loss": [], "train_dice": [], "val_loss": [], "val_dice": []
        }

    def _setup_training(self, cfg: Dict) -> None:
        c = self.cfg
        lr = float(c.get("learning_rate", 1e-4))
        wd = float(c.get("weight_decay", 1e-4))

        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=lr, weight_decay=wd
        )
        self.criterion = get_segmentation_loss(cfg)

        sched = c.get("scheduler", "reduce_on_plateau").lower()
        if sched == "reduce_on_plateau":
            self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                patience=c.get("scheduler_patience", 5),
                factor=c.get("scheduler_factor", 0.5),
                mode="max",
            )
        elif sched == "cosine_annealing":
            self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, T_max=c.get("num_epochs", 50)
            )
        else:
            self.scheduler = None

    def _train_epoch(self, loader: DataLoader) -> Dict[str, float]:
        self.model.train()
        total_loss, total_dice, n = 0.0, 0.0, 0
        for images, masks in tqdm(loader, desc="Train", leave=False):
            images, masks = images.to(self.device), masks.to(self.device)
            self.optimizer.zero_grad()
            preds = self.model(images)
            loss = self.criterion(preds, masks)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
            total_dice += _dice_score(preds.detach(), masks)
            n += 1
        return {"loss": total_loss / n, "dice": total_dice / n}

    @torch.no_grad()
    def _val_epoch(self, loader: DataLoader) -> Dict[str, float]:
        self.model.eval()
        total_loss, total_dice, n = 0.0, 0.0, 0
        for images, masks in tqdm(loader, desc="Val  ", leave=False):
            images, masks = images.to(self.device), masks.to(self.device)
            preds = self.model(images)
            total_loss += self.criterion(preds, masks).item()
            total_dice += _dice_score(preds, masks)
            n += 1
        return {"loss": total_loss / n, "dice": total_dice / n}

    def _save_checkpoint(self, epoch: int, is_best: bool = False) -> None:
        state = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "best_dice": self.best_dice,
            "history": self.history,
        }
        torch.save(state, self.weights_dir / "latest_checkpoint.pth")
        if is_best:
            torch.save(state, self.weights_dir / "best_model.pth")
            log.info("New best segmentation model", epoch=epoch, dice=self.best_dice)

    def load_checkpoint(self, checkpoint_path: str | Path) -> int:
        ckpt = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        self.best_dice = ckpt.get("best_dice", 0.0)
        self.history = ckpt.get("history", self.history)
        return ckpt["epoch"] + 1

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: Optional[int] = None,
        start_epoch: int = 0,
    ) -> Dict:
        epochs = num_epochs or self.cfg.get("num_epochs", 50)
        patience = self.cfg.get("early_stopping_patience", 10)
        min_delta = float(self.cfg.get("early_stopping_min_delta", 0.001))

        for epoch in range(start_epoch, start_epoch + epochs):
            train_m = self._train_epoch(train_loader)
            val_m = self._val_epoch(val_loader)

            if isinstance(self.scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                self.scheduler.step(val_m["dice"])
            elif self.scheduler:
                self.scheduler.step()

            self.history["train_loss"].append(train_m["loss"])
            self.history["train_dice"].append(train_m["dice"])
            self.history["val_loss"].append(val_m["loss"])
            self.history["val_dice"].append(val_m["dice"])

            is_best = val_m["dice"] > self.best_dice + min_delta
            if is_best:
                self.best_dice = val_m["dice"]
                self.epochs_no_improve = 0
            else:
                self.epochs_no_improve += 1

            self._save_checkpoint(epoch, is_best)
            log.info(
                f"Epoch {epoch + 1}/{start_epoch + epochs}",
                train_loss=f"{train_m['loss']:.4f}",
                train_dice=f"{train_m['dice']:.4f}",
                val_loss=f"{val_m['loss']:.4f}",
                val_dice=f"{val_m['dice']:.4f}",
                best_dice=f"{self.best_dice:.4f}",
            )

            if self.epochs_no_improve >= patience:
                log.info("Early stopping triggered")
                break

        with open(self.weights_dir / "training_history.json", "w") as f:
            json.dump(self.history, f, indent=2)

        return self.history
