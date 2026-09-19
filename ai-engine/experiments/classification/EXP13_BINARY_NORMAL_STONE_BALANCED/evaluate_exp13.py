"""
evaluate_exp13.py — EXP13 External Evaluation

INFERENCE ONLY.
Does NOT train, fine-tune, or modify model weights.

Evaluates the binary EXP13 checkpoint against the completely independent
Axial CT Kidney Stone external dataset (Original subset ONLY).

Usage
-----
    # Default: uses best checkpoint, default external root
    python ai-engine/experiments/classification/EXP13_BINARY_NORMAL_STONE_BALANCED/evaluate_exp13.py

    # Custom checkpoint
    python .../evaluate_exp13.py --checkpoint path/to/best_model_exp13.pth

    # Custom external data root
    python .../evaluate_exp13.py --external-root "datasets/raw/.../Original"

Output
------
    outputs/metrics/external_results.json
    outputs/predictions/external_predictions.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_EXP_DIR     = Path(__file__).parent
_ENGINE_ROOT = _EXP_DIR.parent.parent.parent
_PROJECT_ROOT = _ENGINE_ROOT.parent

sys.path.insert(0, str(_ENGINE_ROOT))

import torch
from torch.utils.data import DataLoader

from preprocessing.classification_transforms import get_classification_transforms
from utils.logger import get_logger

from dataset import ExternalBinaryDataset
from train_exp13 import build_binary_efficientnet, _binary_epoch_metrics

log = get_logger("EXP13_eval")

_OUT_DIR    = _EXP_DIR / "outputs"
_CKPT_DIR   = _OUT_DIR / "checkpoints"
_METRICS_DIR = _OUT_DIR / "metrics"
_PRED_DIR   = _OUT_DIR / "predictions"

DEFAULT_CHECKPOINT = _CKPT_DIR / "best_model_exp13_binary_normal_stone_balanced.pth"
DEFAULT_EXT_ROOT   = (
    _PROJECT_ROOT
    / "datasets" / "raw" / "classification" / "additional_dataset"
    / "Kidney Stone Dataset" / "Original"
)


def compute_full_metrics(y_true, y_pred, y_prob_stone):
    tp = tn = fp = fn = 0
    for gt, pr in zip(y_true, y_pred):
        if gt == 1 and pr == 1: tp += 1
        elif gt == 0 and pr == 0: tn += 1
        elif gt == 0 and pr == 1: fp += 1
        else: fn += 1

    total  = tp + tn + fp + fn
    acc    = (tp + tn) / total  if total          > 0 else 0.0
    prec   = tp / (tp + fp)    if (tp + fp)       > 0 else 0.0
    rec    = tp / (tp + fn)    if (tp + fn)       > 0 else 0.0
    spec   = tn / (tn + fp)    if (tn + fp)       > 0 else 0.0
    f1     = 2*prec*rec/(prec+rec) if (prec+rec)  > 0 else 0.0

    try:
        from sklearn.metrics import (
            roc_auc_score, matthews_corrcoef, balanced_accuracy_score
        )
        roc_auc = float(roc_auc_score(y_true, y_prob_stone))
        mcc     = float(matthews_corrcoef(y_true, y_pred))
        bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    except Exception:
        roc_auc = bal_acc = mcc = None

    return {
        "accuracy":         round(acc,  6),
        "precision":        round(prec, 6),
        "recall":           round(rec,  6),
        "specificity":      round(spec, 6),
        "f1":               round(f1,   6),
        "roc_auc":          round(roc_auc, 6) if roc_auc is not None else None,
        "balanced_accuracy":round(bal_acc, 6) if bal_acc is not None else None,
        "mcc":              round(mcc,  6) if mcc  is not None else None,
        "TP": tp, "TN": tn, "FP": fp, "FN": fn,
        "confusion_matrix": [[tn, fp], [fn, tp]],
    }


def main():
    parser = argparse.ArgumentParser(description="EXP13 External Evaluation — Inference Only")
    parser.add_argument("--checkpoint",    type=str, default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--external-root", type=str, default=str(DEFAULT_EXT_ROOT))
    args = parser.parse_args()

    ckpt_path = Path(args.checkpoint).resolve()
    ext_root  = Path(args.external_root).resolve()

    # ── Safety banner ─────────────────────────────────────────────────────────
    print("\n" + "=" * 64)
    print("  EXP13 — EXTERNAL EVALUATION")
    print("=" * 64)
    print("  TRAINING:    DISABLED")
    print("  FINE-TUNING: DISABLED")
    print("  DATASET:     EXTERNAL — Axial CT Kidney Stone")
    print("  SUBSET:      ORIGINAL ONLY")
    print("  AUGMENTED:   EXCLUDED")
    print(f"  Checkpoint:  {ckpt_path}")
    print(f"  External:    {ext_root}")
    print("=" * 64 + "\n")

    if not ckpt_path.exists():
        print(f"ERROR: Checkpoint not found: {ckpt_path}")
        print("Please run train_exp13.py first.")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device.type.upper()}")
    if device.type == "cuda":
        print(f"  GPU:    {torch.cuda.get_device_name(0)}")

    # ── Load model ────────────────────────────────────────────────────────────
    ckpt = torch.load(ckpt_path, map_location=device)

    # Verify checkpoint is EXP13 (binary)
    n_classes = ckpt.get("num_classes", None)
    exp_tag   = ckpt.get("experiment", "")
    if n_classes != 2 or "EXP13" not in exp_tag:
        print(f"WARNING: Checkpoint may not be from EXP13.")
        print(f"  experiment tag : {exp_tag}")
        print(f"  num_classes    : {n_classes}")

    import yaml
    with open(_EXP_DIR / "config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    model = build_binary_efficientnet(
        dropout=float(cfg["model"]["dropout"]),
        pretrained=False,   # loading from checkpoint, not ImageNet
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()   # STRICTLY EVAL MODE — no gradients, no weight updates

    input_size = int(cfg["training"]["input_size"])
    transform  = get_classification_transforms("test", input_size)

    # ── External dataset ──────────────────────────────────────────────────────
    ext_ds = ExternalBinaryDataset(ext_root, transform=transform)
    print(f"\n  External dataset:")
    print(f"    Stone     : {ext_ds.stone_count}")
    print(f"    Non-Stone : {ext_ds.non_stone_count}")
    print(f"    Total     : {len(ext_ds)}\n")

    ext_loader = DataLoader(ext_ds, batch_size=32, shuffle=False,
                            num_workers=0, pin_memory=True)

    # ── Inference ─────────────────────────────────────────────────────────────
    print("  Running inference …")
    y_true:       list = []
    y_pred:       list = []
    y_prob_stone: list = []
    csv_rows:     list = []

    with torch.no_grad():
        for batch in ext_loader:
            images, labels, paths = batch
            images = images.to(device)
            logits = model(images)
            probs  = torch.softmax(logits, dim=1).cpu()

            for i in range(len(labels)):
                gt   = int(labels[i].item())
                prob_stone = float(probs[i, 1].item())
                pred = 1 if prob_stone >= 0.5 else 0
                correct = (pred == gt)

                y_true.append(gt)
                y_pred.append(pred)
                y_prob_stone.append(prob_stone)

                csv_rows.append({
                    "image_path":                 paths[i],
                    "filename":                   Path(paths[i]).name,
                    "ground_truth":               "Stone" if gt == 1 else "Non-Stone",
                    "predicted_class":            "Stone" if pred == 1 else "Non-Stone",
                    "predicted_probability_stone": round(prob_stone, 6),
                    "correct":                    correct,
                })

    # ── Compute metrics ───────────────────────────────────────────────────────
    metrics = compute_full_metrics(y_true, y_pred, y_prob_stone)

    print(f"\n  External Evaluation Results:")
    print(f"  {'Accuracy':20s}: {metrics['accuracy']:.6f}")
    print(f"  {'Precision':20s}: {metrics['precision']:.6f}")
    print(f"  {'Recall':20s}: {metrics['recall']:.6f}")
    print(f"  {'Specificity':20s}: {metrics['specificity']:.6f}")
    print(f"  {'F1':20s}: {metrics['f1']:.6f}")
    if metrics["roc_auc"] is not None:
        print(f"  {'ROC-AUC':20s}: {metrics['roc_auc']:.6f}")
    if metrics["balanced_accuracy"] is not None:
        print(f"  {'Balanced Acc':20s}: {metrics['balanced_accuracy']:.6f}")
    if metrics["mcc"] is not None:
        print(f"  {'MCC':20s}: {metrics['mcc']:.6f}")
    print(f"\n  Confusion matrix:")
    print(f"    TN={metrics['TN']:5d}  FP={metrics['FP']:5d}")
    print(f"    FN={metrics['FN']:5d}  TP={metrics['TP']:5d}")

    # ── Baseline comparison ───────────────────────────────────────────────────
    print(f"\n  Comparison vs RECORDED BASELINE")
    print(f"  (Baseline checkpoint: 4-class model — exact file TBD by user)")
    print(f"  {'Metric':20s}  {'Baseline':10s}  {'EXP13':10s}  {'Delta':10s}")
    baselines = {
        "Accuracy":    0.6064,
        "Precision":   0.5687,
        "Recall":      0.6639,
        "Specificity": 0.5557,
        "F1":          0.6126,
        "ROC-AUC":     0.6981,
    }
    metric_map = {
        "Accuracy": "accuracy", "Precision": "precision", "Recall": "recall",
        "Specificity": "specificity", "F1": "f1", "ROC-AUC": "roc_auc",
    }
    for name, base_val in baselines.items():
        key = metric_map[name]
        exp_val = metrics.get(key)
        if exp_val is not None:
            delta = exp_val - base_val
            sign = "+" if delta >= 0 else ""
            print(f"  {name:20s}  {base_val:.4f}      {exp_val:.4f}      {sign}{delta:.4f}")

    # ── Save results ──────────────────────────────────────────────────────────
    _METRICS_DIR.mkdir(parents=True, exist_ok=True)
    _PRED_DIR.mkdir(parents=True, exist_ok=True)

    result_doc = {
        "experiment": "EXP13_BINARY_NORMAL_STONE_BALANCED",
        "checkpoint": str(ckpt_path),
        "external_dataset": str(ext_root),
        "total_images": len(y_true),
        "stone_images": ext_ds.stone_count,
        "non_stone_images": ext_ds.non_stone_count,
        "augmented_images_used": 0,
        "training_used_external": False,
        "threshold": 0.5,
        "metrics": metrics,
        "baseline_comparison": {
            name: {
                "baseline": base_val,
                "exp13": metrics.get(metric_map[name]),
                "delta": (
                    round(metrics[metric_map[name]] - base_val, 6)
                    if metrics.get(metric_map[name]) is not None else None
                ),
            }
            for name, base_val in baselines.items()
        },
    }

    ext_json = _METRICS_DIR / "external_results.json"
    with open(ext_json, "w") as f:
        json.dump(result_doc, f, indent=2)

    ext_csv = _PRED_DIR / "external_predictions.csv"
    fields = ["image_path", "filename", "ground_truth", "predicted_class",
              "predicted_probability_stone", "correct"]
    with open(ext_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\n  Saved: {ext_json}")
    print(f"  Saved: {ext_csv}")
    print("\n" + "=" * 64)
    print("  EXTERNAL EVALUATION COMPLETE")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
