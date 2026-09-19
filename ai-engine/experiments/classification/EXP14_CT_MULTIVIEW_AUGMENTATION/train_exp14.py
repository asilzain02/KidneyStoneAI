"""
train_exp14.py — EXP14_CT_MULTIVIEW_AUGMENTATION training entry point.

DO NOT execute automatically.
Start manually:
    python ai-engine/experiments/classification/EXP14_CT_MULTIVIEW_AUGMENTATION/train_exp14.py

Smoke test (safe, ~1 min):
    python ai-engine/experiments/classification/EXP14_CT_MULTIVIEW_AUGMENTATION/train_exp14.py --smoke-test
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

_EXP_DIR     = Path(__file__).parent
_ENGINE_ROOT = _EXP_DIR.parent.parent.parent
_PROJECT_ROOT = _ENGINE_ROOT.parent
sys.path.insert(0, str(_ENGINE_ROOT))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
import yaml

from utils.seed_utils import set_seed
from utils.logger import get_logger

from dataset   import CTKidneyMultiviewDataset
from model     import build_exp14_model, count_parameters
from transforms import get_exp14_transforms

log = get_logger("EXP14")

_CFG_PATH    = _EXP_DIR / "config.yaml"
_OUT_DIR     = _EXP_DIR / "outputs"
_CKPT_DIR    = _OUT_DIR / "checkpoints"
_LOG_DIR     = _OUT_DIR / "logs"
_METRICS_DIR = _OUT_DIR / "metrics"


def load_cfg() -> dict:
    with open(_CFG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Metric helpers ─────────────────────────────────────────────────────────────

def _compute_epoch_stats(all_logits, all_labels, num_classes: int = 4) -> dict:
    preds = torch.tensor(all_logits).argmax(dim=1)
    lbls  = torch.tensor(all_labels)
    correct = (preds == lbls).sum().item()
    acc = correct / len(lbls)

    # Per-class precision, recall, F1
    precisions, recalls, f1s = [], [], []
    for c in range(num_classes):
        tp = ((preds == c) & (lbls == c)).sum().item()
        fp = ((preds == c) & (lbls != c)).sum().item()
        fn = ((preds != c) & (lbls == c)).sum().item()
        p  = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f  = 2*p*r/(p+r) if (p+r) > 0 else 0.0
        precisions.append(p); recalls.append(r); f1s.append(f)

    macro_f1 = sum(f1s) / num_classes
    return {
        "accuracy": round(acc, 6),
        "macro_f1": round(macro_f1, 6),
        "per_class_f1": [round(x, 6) for x in f1s],
        "per_class_recall": [round(x, 6) for x in recalls],
        "per_class_precision": [round(x, 6) for x in precisions],
    }


# ── One epoch ─────────────────────────────────────────────────────────────────

def run_epoch(model, loader, criterion, optimizer, device, train: bool,
              desc: str = "") -> tuple[float, list, list]:
    model.train() if train else model.eval()
    total_loss = 0.0
    all_logits, all_labels = [], []

    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        pbar = tqdm(loader, desc=desc, leave=False, dynamic_ncols=True)
        for images, labels in pbar:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            loss   = criterion(logits, labels)
            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * images.size(0)
            all_logits.extend(logits.detach().cpu().tolist())
            all_labels.extend(labels.cpu().tolist())
            pbar.set_postfix(loss=f"{loss.item():.4f}")

    avg_loss = total_loss / len(all_labels)
    return avg_loss, all_logits, all_labels


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="EXP14 Training")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Tiny 2-epoch test; does NOT overwrite full checkpoints.")
    args = parser.parse_args()

    cfg = load_cfg()
    t   = cfg["training"]
    seed = int(cfg["experiment"]["seed"])
    set_seed(seed, deterministic=bool(cfg["experiment"]["deterministic"]))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── Safety header ──────────────────────────────────────────────────────────
    print("\n" + "=" * 66)
    print("  EXPERIMENT: EXP14_CT_MULTIVIEW_AUGMENTATION")
    print("=" * 66)
    print("  Scientific goal  : CT multi-view + CT-safe augmentation")
    print("  Backbone         : EfficientNet-B0 (unchanged)")
    print("  Input channels   : 3  (original | CLAHE | soft-edge)")
    print("  Loss             : CrossEntropyLoss (NO class weighting)")
    print("  Sampler          : None (natural distribution)")
    print(f"  Device           : {device}")
    if device.type == "cuda":
        print(f"  GPU              : {torch.cuda.get_device_name(0)}")
    print("=" * 66 + "\n")

    # ── Datasets ───────────────────────────────────────────────────────────────
    smoke   = args.smoke_test
    smoke_n = 15

    train_tf = get_exp14_transforms("train", cfg)
    val_tf   = get_exp14_transforms("val",   cfg)
    test_tf  = get_exp14_transforms("test",  cfg)

    train_ds = CTKidneyMultiviewDataset(
        _PROJECT_ROOT / cfg["data"]["train_csv"], transform=train_tf,
        smoke=smoke, smoke_n=smoke_n)
    val_ds   = CTKidneyMultiviewDataset(
        _PROJECT_ROOT / cfg["data"]["val_csv"],   transform=val_tf)
    test_ds  = CTKidneyMultiviewDataset(
        _PROJECT_ROOT / cfg["data"]["test_csv"],  transform=test_tf)

    print("  Dataset counts (filtered to Normal/Cyst/Stone/Tumor):")
    for split, ds in [("train", train_ds), ("val", val_ds), ("test", test_ds)]:
        cc = ds.class_counts()
        print(f"    {split:5s}: Normal={cc['Normal']}  Cyst={cc['Cyst']}"
              f"  Stone={cc['Stone']}  Tumor={cc['Tumor']}  Total={len(ds)}")

    batch_size  = int(t["batch_size"])
    num_epochs  = 2 if smoke else int(t["num_epochs"])
    patience    = int(t["early_stopping_patience"])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=0, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False,
                              num_workers=0, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=batch_size, shuffle=False,
                              num_workers=0, pin_memory=True)

    # ── Model ──────────────────────────────────────────────────────────────────
    model = build_exp14_model(cfg).to(device)
    n_params = count_parameters(model)
    print(f"\n  Model: EfficientNet-B0, 4-class head, 3-ch input")
    print(f"  Trainable parameters: {n_params:,}")

    # ── Optimizer / Scheduler / Loss ──────────────────────────────────────────
    lr  = float(t["learning_rate"])
    wd  = float(t["weight_decay"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=int(t["scheduler_T_max"]))
    criterion = nn.CrossEntropyLoss()

    # ── Paths ──────────────────────────────────────────────────────────────────
    if smoke:
        ckpt_dir = _CKPT_DIR / "smoke"
    else:
        ckpt_dir = _CKPT_DIR
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _METRICS_DIR.mkdir(parents=True, exist_ok=True)

    best_ckpt   = ckpt_dir / cfg["output"]["checkpoint_name"]
    latest_ckpt = ckpt_dir / cfg["output"]["latest_name"]
    hist_path   = _LOG_DIR / ("training_history_smoke.json" if smoke
                               else "training_history.json")

    # ── Training loop ─────────────────────────────────────────────────────────
    best_val_f1       = 0.0
    no_improve        = 0
    history           = []
    t0                = time.time()

    print(f"\n{'='*66}")
    print(f"  {'SMOKE TEST' if smoke else 'TRAINING'}  — {num_epochs} epoch(s)")
    print(f"{'='*66}\n")

    for epoch in range(num_epochs):
        ep_t0  = time.time()
        cur_lr = optimizer.param_groups[0]["lr"]

        tr_loss, tr_log, tr_lbl = run_epoch(
            model, train_loader, criterion, optimizer, device, train=True,
            desc=f"Epoch {epoch+1}/{num_epochs} [train]")
        vl_loss, vl_log, vl_lbl = run_epoch(
            model, val_loader, criterion, optimizer, device, train=False,
            desc=f"Epoch {epoch+1}/{num_epochs} [val]  ")
        scheduler.step()

        tr_stats = _compute_epoch_stats(tr_log, tr_lbl)
        vl_stats = _compute_epoch_stats(vl_log, vl_lbl)

        hist_row = {
            "epoch":              epoch + 1,
            "train_loss":         round(tr_loss, 6),
            "train_accuracy":     tr_stats["accuracy"],
            "train_macro_f1":     tr_stats["macro_f1"],
            "val_loss":           round(vl_loss, 6),
            "val_accuracy":       vl_stats["accuracy"],
            "val_macro_f1":       vl_stats["macro_f1"],
            "val_per_class_f1":   vl_stats["per_class_f1"],
            "val_per_class_recall": vl_stats["per_class_recall"],
            "learning_rate":      cur_lr,
            "elapsed_s":          round(time.time() - ep_t0, 2),
        }
        history.append(hist_row)

        is_best = vl_stats["macro_f1"] > best_val_f1
        if is_best:
            best_val_f1 = vl_stats["macro_f1"]
            no_improve  = 0
            state = {
                "epoch": epoch + 1,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_val_acc": vl_stats["accuracy"],
                "best_val_macro_f1": best_val_f1,
                "class_names": ["Normal","Cyst","Stone","Tumor"],
                "experiment_name": "EXP14_CT_MULTIVIEW_AUGMENTATION",
                "config": cfg,
                "seed": seed,
            }
            torch.save(state, best_ckpt)
        else:
            no_improve += 1

        torch.save({**state, "epoch": epoch+1}, latest_ckpt)  # type: ignore

        log.info(
            f"Epoch {epoch+1}/{num_epochs}",
            tr_loss=f"{tr_loss:.4f}", tr_f1=f"{tr_stats['macro_f1']:.4f}",
            vl_loss=f"{vl_loss:.4f}", vl_f1=f"{vl_stats['macro_f1']:.4f}",
            best_f1=f"{best_val_f1:.4f}", new_best=is_best,
        )

        if not smoke and no_improve >= patience:
            log.info("Early stopping", epoch=epoch+1, patience=patience)
            break

    # ── Save history ───────────────────────────────────────────────────────────
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    # ── Final test evaluation ──────────────────────────────────────────────────
    if not smoke:
        test_loss, te_log, te_lbl = run_epoch(
            model, test_loader, criterion, optimizer, device, train=False,
            desc="Test eval")
        te_stats = _compute_epoch_stats(te_log, te_lbl)
        test_result = {"split": "test", "loss": round(test_loss, 6), **te_stats}
        with open(_METRICS_DIR / "test_results.json", "w", encoding="utf-8") as f:
            json.dump(test_result, f, indent=2)

        # Save experiment metadata
        meta = {
            "experiment_id": "EXP14_CT_MULTIVIEW_AUGMENTATION",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "seed": seed, "device": str(device),
            "pytorch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
            "backbone": "efficientnet_b0",
            "in_channels": 3,
            "num_classes": 4,
            "class_names": ["Normal","Cyst","Stone","Tumor"],
            "trainable_params": n_params,
            "optimizer": "AdamW",
            "learning_rate": lr, "weight_decay": wd,
            "batch_size": batch_size, "input_size": int(t["input_size"]),
            "num_epochs_trained": len(history),
            "best_val_macro_f1": best_val_f1,
            "intentional_changes": [
                "Three-channel multi-view input (original|CLAHE|soft-edge)",
                "CT-safe augmentation pipeline",
            ],
            "training_duration_s": round(time.time() - t0, 1),
        }
        with open(_LOG_DIR / "experiment_metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    print("\n" + "=" * 66)
    if smoke:
        print("  SMOKE TEST PASSED — Full training NOT started")
        print("  Run external eval after full training:")
        print("    python .../evaluate_exp14.py")
    else:
        print("  TRAINING COMPLETE")
        print(f"  Best val Macro-F1 : {best_val_f1:.4f}")
        print(f"  Checkpoint        : {best_ckpt}")
    print("=" * 66 + "\n")


if __name__ == "__main__":
    main()
