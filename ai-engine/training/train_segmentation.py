"""
train_segmentation.py — CLI entry point for segmentation training.

Usage:
    python ai-engine/training/train_segmentation.py
    python ai-engine/training/train_segmentation.py --smoke
    python ai-engine/training/train_segmentation.py --experiment segmentation_baseline
    python ai-engine/training/train_segmentation.py --experiment segmentation_baseline --config ai-engine/config/segmentation_config.yaml
    python ai-engine/training/train_segmentation.py --resume ai-engine/weights/segmentation/segmentation_baseline/latest_checkpoint.pth
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ENGINE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

import yaml
from config.settings import get_training_cfg, get_paths_cfg
from datasets.kssd2025_adapter import KSSD2025DatasetAdapter
from datasets.split_builder import build_segmentation_splits
from models.unet.unet import build_unet
from preprocessing.segmentation_transforms import get_segmentation_transforms
from preprocessing.kssd2025_dataset import KSSD2025Dataset
from training.segmentation_trainer import SegmentationTrainer
from torch.utils.data import DataLoader
from utils.logger import get_logger

log = get_logger("train_segmentation")


def parse_args():
    p = argparse.ArgumentParser(description="Train KidneyStoneAI segmentation model")
    # ── Existing flags (unchanged) ────────────────────────────────────────────
    p.add_argument("--smoke", action="store_true", help="Smoke test: 2 epochs, 50 pairs")
    p.add_argument("--resume", type=str, default=None)
    p.add_argument("--epochs", type=int, default=None)
    p.add_argument("--batch-size", type=int, default=None)
    # ── New flags ─────────────────────────────────────────────────────────────
    p.add_argument(
        "--experiment", type=str, default="segmentation_baseline",
        help="Experiment name — weights saved under weights/segmentation/<name>/",
    )
    p.add_argument(
        "--config", type=str, default=None,
        help="Path to segmentation_config.yaml (overrides default training_config.yaml)",
    )
    p.add_argument(
        "--device", type=str, default=None,
        help="Device override: cpu | cuda | cuda:0 (default: auto-detect)",
    )
    return p.parse_args()


def _load_seg_config(config_path: str) -> dict:
    """Load segmentation_config.yaml and normalise to the internal cfg format."""
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    # Map segmentation_config.yaml keys → internal cfg["segmentation"] shape
    tr = raw.get("training", {})
    seg = {
        "input_size": raw.get("input", {}).get("size", 256),
        "in_channels": raw.get("model", {}).get("in_channels", 1),
        "out_channels": raw.get("model", {}).get("out_channels", 1),
        "base_features": raw.get("model", {}).get("base_features", 32),
        "loss": raw.get("loss", {}).get("name", "dice_bce"),
        "dice_weight": raw.get("loss", {}).get("dice_weight", 0.5),
        "bce_weight": raw.get("loss", {}).get("bce_weight", 0.5),
        "batch_size": tr.get("batch_size", 8),
        "num_epochs": tr.get("epochs", 50),
        "learning_rate": tr.get("learning_rate", 1e-4),
        "weight_decay": tr.get("weight_decay", 1e-4),
        "optimizer": tr.get("optimizer", "adam"),
        "scheduler": tr.get("scheduler", "reduce_on_plateau"),
        "scheduler_patience": tr.get("scheduler_patience", 5),
        "scheduler_factor": tr.get("scheduler_factor", 0.5),
        "early_stopping_patience": tr.get("early_stopping_patience", 10),
        "early_stopping_min_delta": tr.get("early_stopping_min_delta", 0.001),
        "smoke_epochs": raw.get("smoke", {}).get("epochs", 2),
        "smoke_samples": raw.get("smoke", {}).get("samples", 50),
    }
    splits = raw.get("splits", {})
    return {
        "segmentation": seg,
        "splits": {
            "train_ratio": splits.get("train_ratio", 0.70),
            "val_ratio": splits.get("val_ratio", 0.15),
            "random_seed": splits.get("seed", 42),
        },
        "seed": raw.get("seed", 42),
        "deterministic": raw.get("deterministic", True),
    }


def main():
    args = parse_args()
    if args.config:
        cfg = _load_seg_config(args.config)
        log.info("Loaded custom segmentation config", path=args.config)
    else:
        cfg = get_training_cfg()
    paths = get_paths_cfg()

    experiment_name = args.experiment
    log.info("Experiment", name=experiment_name)

    seg_cfg = cfg["segmentation"]
    splits_cfg = cfg["splits"]

    if args.smoke:
        log.info("=== SMOKE TEST MODE ===")
        num_epochs = seg_cfg["smoke_epochs"]
        smoke_n = seg_cfg["smoke_samples"]
        batch_size = 4
    else:
        num_epochs = args.epochs or seg_cfg["num_epochs"]
        smoke_n = 0
        batch_size = args.batch_size or seg_cfg["batch_size"]

    # ── Ensure manifests + splits exist ─────────────────────────────────────
    image_dir = paths["raw"]["segmentation_images"]
    label_dir = paths["raw"]["segmentation_labels"]
    manifest_path = paths["manifests"]["segmentation"]
    splits_dir = paths["splits"]["segmentation_dir"]

    if not Path(manifest_path).exists():
        log.info("Building KSSD2025 manifest …")
        adapter = KSSD2025DatasetAdapter(image_dir, label_dir)
        adapter.validate(compute_hashes=True)
        adapter.build_manifest(manifest_path)

    if not Path(splits_dir + "/train.csv").exists():
        log.info("Building segmentation splits …")
        build_segmentation_splits(
            manifest_path=manifest_path,
            output_dir=splits_dir,
            train_ratio=splits_cfg["train_ratio"],
            val_ratio=splits_cfg["val_ratio"],
            seed=splits_cfg["random_seed"],
        )

    # ── Per-experiment weights directory ─────────────────────────────────────
    # Override the default flat path with an isolated experiment directory.
    seg_weights_dir = str(
        Path(paths["weights"]["segmentation_best"]).parent.parent / experiment_name
    )

    # ── Datasets ─────────────────────────────────────────────────────────────
    train_tf = get_segmentation_transforms("train", seg_cfg["input_size"])
    val_tf = get_segmentation_transforms("val", seg_cfg["input_size"])

    train_ds = KSSD2025Dataset(splits_dir + "/train.csv", transform=train_tf,
                                smoke=args.smoke, smoke_n=smoke_n)
    val_ds = KSSD2025Dataset(splits_dir + "/val.csv", transform=val_tf,
                              smoke=args.smoke, smoke_n=smoke_n)

    log.info("Dataset sizes", train=len(train_ds), val=len(val_ds))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    # ── Model + Trainer ──────────────────────────────────────────────────────
    model = build_unet(cfg)

    import torch
    if args.device:
        device = torch.device(args.device)
        trainer = SegmentationTrainer(model, cfg, seg_weights_dir)
        trainer.device = device
        model.to(device)
    else:
        trainer = SegmentationTrainer(model, cfg, seg_weights_dir)

    start_epoch = 0
    if args.resume and Path(args.resume).exists():
        start_epoch = trainer.load_checkpoint(args.resume)

    trainer.train(train_loader, val_loader, num_epochs=num_epochs, start_epoch=start_epoch)

    log.info("Segmentation training complete", best_dice=trainer.best_dice)
    if args.smoke:
        log.info("=== SMOKE TEST PASSED — Full training NOT started ===")


if __name__ == "__main__":
    main()
