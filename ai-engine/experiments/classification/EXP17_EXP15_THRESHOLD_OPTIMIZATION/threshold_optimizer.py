"""
threshold_optimizer.py — EXP17 Threshold Optimization
DO NOT EXECUTE AUTOMATICALLY.

Finds the optimal Stone-probability threshold using the INTERNAL validation
split, loading the frozen EXP15 (EfficientNet-B2 320x320) model.

Usage:
    python ai-engine/experiments/classification/EXP17_EXP15_THRESHOLD_OPTIMIZATION/threshold_optimizer.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
import yaml

_EXP_DIR      = Path(__file__).parent
_ENGINE_ROOT  = _EXP_DIR.parent.parent.parent
_PROJECT_ROOT = _ENGINE_ROOT.parent
sys.path.insert(0, str(_ENGINE_ROOT))

# Must import EXP15 architecture since we load its checkpoint
sys.path.insert(0, str(_ENGINE_ROOT / "experiments" / "classification" / "EXP15_EFFICIENTNET_B2_320"))
from model import build_exp15_model

from preprocessing.classification_transforms import get_classification_transforms

_OUT_DIR       = _EXP_DIR / "outputs"
_THRESH_DIR    = _OUT_DIR / "thresholds"
_THRESH_TSV    = _THRESH_DIR / "threshold_results.csv"
_THRESH_JSON   = _THRESH_DIR / "threshold_selection.json"


class ValidationDataset(Dataset):
    """Loads internal validation set for extracting P(Stone)."""
    def __init__(self, csv_path, transform=None, smoke=False):
        df = pd.read_csv(csv_path, encoding="utf-8")
        if smoke:
            df = df.head(40)
        self.paths = df["image_path"].tolist()
        self.labels = [2 if x.lower() == "stone" else 0 for x in df["class_name"]]
        self.transform = transform

    def __len__(self): return len(self.paths)
    def __getitem__(self, idx):
        img = Image.open(self.paths[idx]).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, self.labels[idx]


def evaluate_threshold(y_true, y_prob_stone, threshold):
    """Calculate binary metrics (Stone vs Non-Stone) for a given threshold."""
    y_pred = [1 if p >= threshold else 0 for p in y_prob_stone]
    tp=tn=fp=fn=0
    for g, p in zip(y_true, y_pred):
        if g == 2 and p == 1: tp += 1
        elif g == 0 and p == 0: tn += 1
        elif g == 0 and p == 1: fp += 1
        else: fn += 1

    acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    bal_acc = (rec + spec) / 2
    youden_j = rec + spec - 1
    
    try:
        from sklearn.metrics import matthews_corrcoef
        mcc = float(matthews_corrcoef([1 if x==2 else 0 for x in y_true], y_pred))
    except:
        mcc = 0.0

    return {
        "threshold": round(threshold, 3),
        "accuracy": round(acc, 6), "precision": round(prec, 6),
        "recall": round(rec, 6), "specificity": round(spec, 6),
        "f1": round(f1, 6), "balanced_accuracy": round(bal_acc, 6),
        "youden_j": round(youden_j, 6), "mcc": round(mcc, 6),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    cfg_path = _EXP_DIR / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    ckpt_path = _PROJECT_ROOT / cfg["experiment"]["source_checkpoint"]

    print("\n" + "=" * 66)
    print("  EXP17 — THRESHOLD OPTIMIZATION (INTERNAL VALIDATION)")
    print("=" * 66)
    print("  TRAINING:    DISABLED")
    print(f"  Checkpoint:  {ckpt_path}")
    print("=" * 66 + "\n")

    if not ckpt_path.exists():
        sys.exit(f"ERROR: Checkpoint not found: {ckpt_path}\nPlease run EXP15 training first.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Loading EXP15 model to {device}...")
    
    # Load config from EXP15 to ensure identical architecture creation
    with open(_PROJECT_ROOT / "ai-engine/experiments/classification/EXP15_EFFICIENTNET_B2_320/config.yaml", "r", encoding="utf-8") as f:
        cfg_15 = yaml.safe_load(f)

    model = build_exp15_model(cfg_15)
    ckpt = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()

    val_csv = _PROJECT_ROOT / cfg["data"]["val_csv"]
    tf = get_classification_transforms("val", int(cfg["data"]["input_size"]))
    ds = ValidationDataset(val_csv, transform=tf, smoke=args.smoke_test)
    loader = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)

    print(f"  Extracting probabilities from {len(ds)} validation samples...")
    y_true, y_prob = [], []
    with torch.no_grad():
        for imgs, lbls in tqdm(loader, desc="Inference"):
            logits = model(imgs.to(device))
            probs = torch.softmax(logits, dim=1).cpu()
            for i in range(len(lbls)):
                y_true.append(int(lbls[i]))
                y_prob.append(float(probs[i, 2]))  # Stone probability

    ts = cfg["threshold_search"]
    thresholds = np.arange(ts["start"], ts["end"] + 1e-6, ts["step"])
    results = [evaluate_threshold(y_true, y_prob, t) for t in thresholds]

    _THRESH_DIR.mkdir(parents=True, exist_ok=True)
    with open(_THRESH_TSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader(); writer.writerows(results)
    
    # Selection
    method = ts.get("selection_method", "max_f1")
    best_res = None
    best_val = -1.0
    for r in results:
        v = r["f1"] if method == "max_f1" else r.get(method, 0)
        min_spec = ts.get("minimum_specificity")
        if min_spec and r["specificity"] < min_spec:
            continue
        
        # Prefer higher specificity if F1 is equivalent (to 3 decimal places)
        if best_res is not None and round(v, 3) == round(best_val, 3):
            if r["specificity"] > best_res["specificity"]:
                best_val = v
                best_res = r
        elif v > best_val:
            best_val = v
            best_res = r

    if best_res is None:
        best_res = max(results, key=lambda x: x["f1"]) # fallback
        print("  WARNING: No threshold met specificity constraints. Falling back to max F1.")

    print(f"\n  Threshold selected by {method}: {best_res['threshold']}")
    for k in ["f1", "precision", "recall", "specificity"]:
        print(f"    {k:15s}: {best_res[k]:.4f}")

    sel = {
        "experiment": "EXP17_EXP15_THRESHOLD_OPTIMIZATION",
        "source_checkpoint": str(ckpt_path),
        "selected_threshold": best_res["threshold"],
        "selection_method": method,
        "validation_metrics_at_selected_threshold": best_res,
        "validation_dataset_size": len(y_true),
        "class_mapping": {"Stone": 2, "Non-Stone": 0}
    }
    with open(_THRESH_JSON, "w", encoding="utf-8") as f:
        json.dump(sel, f, indent=2)

    print(f"\n  Saved: {_THRESH_TSV}")
    print(f"  Saved: {_THRESH_JSON}")
    if args.smoke_test:
        print("  SMOKE TEST PASSED.")
    print("=" * 66 + "\n")


if __name__ == "__main__":
    main()
