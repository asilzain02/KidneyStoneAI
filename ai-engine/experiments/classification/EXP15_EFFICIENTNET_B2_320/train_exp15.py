"""
train_exp15.py — EXP15_EFFICIENTNET_B2_320 training entry point.

DO NOT execute automatically.
Start manually:
    python ai-engine/experiments/classification/EXP15_EFFICIENTNET_B2_320/train_exp15.py

Smoke test (safe):
    python ai-engine/experiments/classification/EXP15_EFFICIENTNET_B2_320/train_exp15.py --smoke-test
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
from preprocessing.classification_transforms import get_classification_transforms

from dataset import CTKidneyDataset15
from model   import build_exp15_model, count_parameters

log = get_logger("EXP15")

_CFG_PATH    = _EXP_DIR / "config.yaml"
_OUT_DIR     = _EXP_DIR / "outputs"
_CKPT_DIR    = _OUT_DIR / "checkpoints"
_LOG_DIR     = _OUT_DIR / "logs"
_METRICS_DIR = _OUT_DIR / "metrics"


def load_cfg() -> dict:
    with open(_CFG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _compute_epoch_stats(all_logits, all_labels, num_classes: int = 4) -> dict:
    preds = torch.tensor(all_logits).argmax(dim=1)
    lbls  = torch.tensor(all_labels)
    acc = (preds == lbls).sum().item() / len(lbls)

    precisions, recalls, f1s = [], [], []
    for c in range(num_classes):
        tp = ((preds == c) & (lbls == c)).sum().item()
        fp = ((preds == c) & (lbls != c)).sum().item()
        fn = ((preds != c) & (lbls == c)).sum().item()
        p  = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f  = 2*p*r/(p+r) if (p+r) > 0 else 0.0
        precisions.append(p); recalls.append(r); f1s.append(f)

    return {
        "accuracy": round(acc, 6),
        "macro_f1": round(sum(f1s)/num_classes, 6),
        "per_class_f1": [round(x, 6) for x in f1s],
        "per_class_recall": [round(x, 6) for x in recalls],
        "per_class_precision": [round(x, 6) for x in precisions],
    }


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

    return total_loss / len(all_labels), all_logits, all_labels


def main():
    parser = argparse.ArgumentParser(description="EXP15 Training")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    cfg = load_cfg()
    t   = cfg["training"]
    seed = int(cfg["experiment"]["seed"])
    set_seed(seed, deterministic=bool(cfg["experiment"]["deterministic"]))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("\n" + "=" * 66)
    print("  EXPERIMENT: EXP15_EFFICIENTNET_B2_320")
    print("=" * 66)
    print("  Backbone : EfficientNet-B2  (CHANGED)")
    print("  Input    : 320x320        (CHANGED)")
    print(f"  Device   : {device}")
    print("=" * 66 + "\n")

    smoke   = args.smoke_test
    smoke_n = 15
    input_size = int(t["input_size"])

    train_tf = get_classification_transforms("train", input_size, strategy=t.get("augmentation_strategy", "baseline"))
    val_tf   = get_classification_transforms("val",   input_size)
    test_tf  = get_classification_transforms("test",  input_size)

    train_ds = CTKidneyDataset15(_PROJECT_ROOT / cfg["data"]["train_csv"], transform=train_tf, smoke=smoke, smoke_n=smoke_n)
    val_ds   = CTKidneyDataset15(_PROJECT_ROOT / cfg["data"]["val_csv"],   transform=val_tf)
    test_ds  = CTKidneyDataset15(_PROJECT_ROOT / cfg["data"]["test_csv"],  transform=test_tf)

    batch_size = int(t["batch_size"])
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,  num_workers=0, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=True)

    model = build_exp15_model(cfg).to(device)
    n_params = count_parameters(model)
    print(f"\n  Model params: {n_params:,}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=float(t["learning_rate"]), weight_decay=float(t["weight_decay"]))
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=int(t["scheduler_T_max"]))
    criterion = nn.CrossEntropyLoss()

    ckpt_dir = _CKPT_DIR / "smoke" if smoke else _CKPT_DIR
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _METRICS_DIR.mkdir(parents=True, exist_ok=True)

    best_ckpt   = ckpt_dir / cfg["output"]["checkpoint_name"]
    latest_ckpt = ckpt_dir / cfg["output"]["latest_name"]
    hist_path   = _LOG_DIR / ("training_history_smoke.json" if smoke else "training_history.json")

    best_val_f1 = 0.0
    no_improve  = 0
    history     = []
    num_epochs  = 2 if smoke else int(t["num_epochs"])
    patience    = int(t["early_stopping_patience"])
    t0 = time.time()

    for epoch in range(num_epochs):
        ep_t0  = time.time()
        cur_lr = optimizer.param_groups[0]["lr"]

        tr_loss, tr_log, tr_lbl = run_epoch(model, train_loader, criterion, optimizer, device, True, f"Ep {epoch+1} T")
        vl_loss, vl_log, vl_lbl = run_epoch(model, val_loader, criterion, optimizer, device, False, f"Ep {epoch+1} V")
        scheduler.step()

        tr_stats = _compute_epoch_stats(tr_log, tr_lbl)
        vl_stats = _compute_epoch_stats(vl_log, vl_lbl)

        history.append({
            "epoch": epoch + 1, "train_loss": round(tr_loss,6), "train_macro_f1": tr_stats["macro_f1"],
            "val_loss": round(vl_loss,6), "val_macro_f1": vl_stats["macro_f1"], "elapsed_s": round(time.time()-ep_t0, 2)
        })

        is_best = vl_stats["macro_f1"] > best_val_f1
        if is_best:
            best_val_f1 = vl_stats["macro_f1"]
            no_improve  = 0
            state = {
                "epoch": epoch + 1, "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_val_macro_f1": best_val_f1, "class_names": ["Normal","Cyst","Stone","Tumor"],
                "experiment_name": "EXP15_EFFICIENTNET_B2_320", "config": cfg, "seed": seed,
            }
            torch.save(state, best_ckpt)
        else:
            no_improve += 1

        torch.save({**state, "epoch": epoch+1}, latest_ckpt)  # type: ignore
        log.info(f"Ep {epoch+1}/{num_epochs}", tr_loss=f"{tr_loss:.4f}", tr_f1=f"{tr_stats['macro_f1']:.4f}",
                 vl_loss=f"{vl_loss:.4f}", vl_f1=f"{vl_stats['macro_f1']:.4f}", best_f1=f"{best_val_f1:.4f}")

        if not smoke and no_improve >= patience:
            log.info("Early stopping", epoch=epoch+1); break

    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    if not smoke:
        te_loss, te_log, te_lbl = run_epoch(model, test_loader, criterion, optimizer, device, False, "Test")
        te_stats = _compute_epoch_stats(te_log, te_lbl)
        with open(_METRICS_DIR / "test_results.json", "w", encoding="utf-8") as f:
            json.dump({"split": "test", "loss": round(te_loss,6), **te_stats}, f, indent=2)

        meta = {
            "experiment_id": "EXP15_EFFICIENTNET_B2_320", "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "seed": seed, "device": str(device), "backbone": "efficientnet_b2", "input_size": input_size,
            "trainable_params": n_params, "training_duration_s": round(time.time()-t0, 1)
        }
        with open(_LOG_DIR / "experiment_metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    print("\n" + "=" * 66)
    if smoke:
        print("  SMOKE TEST PASSED — Full training NOT started")
    else:
        print("  TRAINING COMPLETE")
    print("=" * 66 + "\n")

if __name__ == "__main__":
    main()
