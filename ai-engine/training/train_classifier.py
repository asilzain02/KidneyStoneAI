"""
train_classifier.py — CLI entry point for classification training.

Usage:
    # Full training (baseline)
    python ai-engine/training/train_classifier.py

    # Named experiment (loads experiment_config.yaml overrides)
    python ai-engine/training/train_classifier.py --experiment exp03_lr_0003

    # Smoke test
    python ai-engine/training/train_classifier.py --smoke
    python ai-engine/training/train_classifier.py --smoke --experiment exp02_augmentation_moderate

    # Resume from checkpoint
    python ai-engine/training/train_classifier.py --resume ai-engine/weights/classification/latest_checkpoint.pth

    # Ad-hoc overrides (take priority over everything)
    python ai-engine/training/train_classifier.py --lr 0.0003 --epochs 30

Checkpoint location:
    --experiment baseline  →  ai-engine/weights/experiments/baseline/
    --experiment exp03_*   →  ai-engine/weights/experiments/exp03_*/
    (no --experiment)      →  ai-engine/weights/classification/   ← default (backward compat)
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from pathlib import Path

# Make ai-engine the root for all imports
_ENGINE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

from config.settings import get_training_cfg, get_paths_cfg
from config.experiment_loader import (
    load_experiment_cfg,
    save_experiment_cfg,
    register_experiment,
    get_experiment_dir,
)
from datasets.ct_kidney_adapter import CTKidneyDatasetAdapter
from datasets.split_builder import build_classification_splits
from models.classifier import build_classifier
from preprocessing.classification_transforms import get_classification_transforms
from preprocessing.ct_kidney_dataset import CTKidneyDataset
from training.classification_trainer import ClassificationTrainer
from torch.utils.data import DataLoader
from utils.logger import get_logger
import torch

log = get_logger("train_classifier")


def parse_args():
    p = argparse.ArgumentParser(description="Train KidneyStoneAI classifier")
    p.add_argument(
        "--experiment", type=str, default=None,
        help=(
            "Experiment name (folder under ai-engine/weights/experiments/). "
            "e.g. baseline | exp02_augmentation_moderate | exp03_lr_0003 | exp04_class_weighting"
        ),
    )
    p.add_argument("--smoke",      action="store_true", help="Smoke test: 2 epochs, 50 samples/class")
    p.add_argument("--resume",     type=str,   default=None, help="Path to checkpoint to resume")
    p.add_argument("--epochs",     type=int,   default=None, help="Override number of epochs")
    p.add_argument("--batch-size", type=int,   default=None, help="Override batch size")
    p.add_argument("--lr",         type=float, default=None, help="Override learning rate")
    return p.parse_args()


def _resolve_weights_dir(experiment_name: str | None, smoke: bool) -> Path:
    """Return the checkpoint directory for this run."""
    engine_root = Path(__file__).parent.parent
    if smoke and experiment_name is None:
        return engine_root / "weights" / "experiments" / "smoke"
    if experiment_name:
        base = engine_root / "weights" / "experiments" / experiment_name
        return base / "smoke" if smoke else base
    # No experiment name → legacy path for backward compatibility
    return Path(engine_root / "weights" / "classification")


def main():
    args = parse_args()
    start_time = time.time()

    # ── Load config ───────────────────────────────────────────────────────────
    base_cfg = get_training_cfg()
    if args.experiment:
        cfg = load_experiment_cfg(args.experiment, base_cfg)
        log.info(f"Experiment loaded: {args.experiment}")
    else:
        cfg = base_cfg

    clf_cfg = cfg["classification"]
    splits_cfg = cfg["splits"]
    paths = get_paths_cfg()

    # ── Ad-hoc CLI overrides (highest priority) ───────────────────────────────
    if args.lr:
        clf_cfg["learning_rate"] = args.lr
    if args.batch_size:
        clf_cfg["batch_size"] = args.batch_size
    if args.epochs:
        clf_cfg["num_epochs"] = args.epochs

    # ── Smoke vs full ─────────────────────────────────────────────────────────
    if args.smoke:
        log.info("=== SMOKE TEST MODE ===")
        num_epochs = clf_cfg.get("smoke_epochs", 2)
        smoke_n    = clf_cfg.get("smoke_samples_per_class", 50)
        batch_size = 8
    else:
        num_epochs = clf_cfg.get("num_epochs", 50)
        smoke_n    = 0
        batch_size = clf_cfg.get("batch_size", 32)

    # ── Checkpoint directory ──────────────────────────────────────────────────
    weights_dir = _resolve_weights_dir(args.experiment, args.smoke)
    weights_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Checkpoint directory: {weights_dir}")

    # ── Manifests + splits ────────────────────────────────────────────────────
    clf_root     = paths["raw"]["classification"]
    manifest_path = paths["manifests"]["classification"]
    splits_dir    = paths["splits"]["classification_dir"]

    if not Path(manifest_path).exists():
        log.info("Building CT Kidney manifest …")
        adapter = CTKidneyDatasetAdapter(clf_root)
        adapter.validate(compute_hashes=True)
        adapter.build_manifest(manifest_path)

    if not Path(splits_dir + "/train.csv").exists():
        log.info("Building classification splits …")
        build_classification_splits(
            manifest_path=manifest_path,
            output_dir=splits_dir,
            train_ratio=splits_cfg["train_ratio"],
            val_ratio=splits_cfg["val_ratio"],
            seed=splits_cfg["random_seed"],
        )

    # ── Augmentation strategy ─────────────────────────────────────────────────
    aug_strategy = clf_cfg.get("augmentation", {})
    if isinstance(aug_strategy, dict):
        aug_strategy = aug_strategy.get("strategy", "baseline")
    aug_strategy = str(aug_strategy)

    train_tf = get_classification_transforms("train", clf_cfg["input_size"], strategy=aug_strategy)
    val_tf   = get_classification_transforms("val",   clf_cfg["input_size"])

    log.info(f"Augmentation strategy: {aug_strategy}")

    # ── Datasets ──────────────────────────────────────────────────────────────
    train_ds = CTKidneyDataset(
        splits_dir + "/train.csv", transform=train_tf,
        smoke=args.smoke, smoke_n=smoke_n,
    )
    val_ds = CTKidneyDataset(
        splits_dir + "/val.csv", transform=val_tf,
        smoke=args.smoke, smoke_n=smoke_n,
    )

    log.info("Dataset sizes", train=len(train_ds), val=len(val_ds))

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        num_workers=0, pin_memory=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=0, pin_memory=True,
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    model = build_classifier(cfg)
    log.info("Model built", backbone=clf_cfg["backbone"])

    # ── Trainer ───────────────────────────────────────────────────────────────
    trainer = ClassificationTrainer(model, cfg, weights_dir)

    start_epoch = 0
    if args.resume and Path(args.resume).exists():
        # Need optimizer set up first to load its state
        trainer._setup_training()
        start_epoch = trainer.load_checkpoint(args.resume)

    history = trainer.train(train_loader, val_loader, num_epochs=num_epochs, start_epoch=start_epoch)

    elapsed = time.time() - start_time

    log.info(
        "Training finished",
        best_val_acc=trainer.best_val_acc,
        weights=str(weights_dir),
        elapsed_s=f"{elapsed:.1f}",
    )

    # ── Save experiment metadata ──────────────────────────────────────────────
    if args.experiment and not args.smoke:
        meta = {
            "experiment": args.experiment,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "backbone": clf_cfg.get("backbone", "efficientnet_b0"),
            "input_size": clf_cfg.get("input_size", 224),
            "batch_size": batch_size,
            "learning_rate": clf_cfg.get("learning_rate"),
            "weight_decay": clf_cfg.get("weight_decay"),
            "optimizer": clf_cfg.get("optimizer"),
            "scheduler": clf_cfg.get("scheduler"),
            "dropout": clf_cfg.get("dropout"),
            "augmentation_strategy": aug_strategy,
            "class_weighting_enabled": clf_cfg.get("class_weighting", {}).get("enabled", False),
            "transfer_learning_strategy": clf_cfg.get("transfer_learning", {}).get("strategy", "standard"),
            "seed": cfg.get("seed", 42),
            "num_epochs_requested": num_epochs,
            "best_val_acc": trainer.best_val_acc,
            "training_duration_s": round(elapsed, 1),
            "device": str(trainer.device),
            "pytorch_version": torch.__version__,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        }
        save_experiment_cfg(args.experiment, cfg, extra_meta=meta)
        register_experiment(args.experiment, args.experiment, status="training_completed")
        log.info("Experiment metadata saved", experiment=args.experiment)

    if args.smoke:
        log.info("=== SMOKE TEST PASSED — Full training NOT started ===")


if __name__ == "__main__":
    main()
