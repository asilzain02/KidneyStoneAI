"""
threshold_analysis.py — Sweep Stone detection thresholds on the external dataset.

INFERENCE ONLY — does not retrain or modify model weights.

Usage
-----
    python ai-engine/evaluation/threshold_analysis.py

    python ai-engine/evaluation/threshold_analysis.py \\
        --checkpoint ai-engine/weights/classification/best_model.pth \\
        --data-root "datasets/raw/classification/additional_dataset/Kidney Stone Dataset/Original"

Outputs
-------
    outputs/experiments/threshold/threshold_results.csv
    outputs/experiments/threshold/threshold_results.json
    outputs/experiments/threshold/threshold_vs_metrics.png
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

_ENGINE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

from config.settings import get_training_cfg
from datasets.external.axial_kidney_stone_adapter import AxialKidneyStoneAdapter
from models.classifier import build_classifier
from preprocessing.classification_transforms import get_classification_transforms

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]
STONE_IDX   = CLASS_NAMES.index("Stone")

THRESHOLDS  = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]


def _binary_metrics(y_true: List[int], stone_probs: List[float], threshold: float) -> Dict:
    """Compute binary metrics for a given Stone-probability threshold."""
    y_pred = [1 if p >= threshold else 0 for p in stone_probs]

    tp = tn = fp = fn = 0
    for gt, pr in zip(y_true, y_pred):
        if gt == 1 and pr == 1: tp += 1
        elif gt == 0 and pr == 0: tn += 1
        elif gt == 0 and pr == 1: fp += 1
        else: fn += 1

    total = tp + tn + fp + fn
    accuracy    = (tp + tn) / total if total else 0.0
    precision   = tp / (tp + fp)   if (tp + fp)   else 0.0
    recall      = tp / (tp + fn)   if (tp + fn)   else 0.0
    specificity = tn / (tn + fp)   if (tn + fp)   else 0.0
    f1          = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

    # ROC-AUC (same for every threshold — computed once using probs)
    return {
        "threshold": threshold,
        "accuracy":    round(accuracy,    6),
        "precision":   round(precision,   6),
        "recall":      round(recall,      6),
        "specificity": round(specificity, 6),
        "f1":          round(f1,          6),
        "TP": tp, "TN": tn, "FP": fp, "FN": fn,
    }


def _compute_roc_auc(y_true: List[int], stone_probs: List[float]) -> float:
    """Simple trapezoidal ROC-AUC from scratch (no sklearn needed)."""
    try:
        from sklearn.metrics import roc_auc_score
        return float(roc_auc_score(y_true, stone_probs))
    except Exception:
        return float("nan")


def run_threshold_analysis(args: argparse.Namespace) -> None:
    print("\n============================================================")
    print("THRESHOLD ANALYSIS — INFERENCE ONLY")
    print("============================================================")
    print("Training:      DISABLED")
    print("Fine-tuning:   DISABLED")
    print("Dataset:       External — Axial CT Kidney Stone Dataset")
    print("Subset:        Original ONLY")
    print("Augmented:     EXCLUDED")
    print(f"Checkpoint:    {args.checkpoint}")
    print("============================================================\n")

    cfg = get_training_cfg()

    # ── Discover external data ────────────────────────────────────────────────
    data_root = Path(args.data_root).resolve()
    if "augmented" in str(data_root).lower():
        raise ValueError("SAFETY ERROR: Augmented path detected. Refusing.")
    if data_root.name.lower() != "original":
        raise ValueError(
            f"SAFETY ERROR: Must point to the 'Original' directory. Got: {data_root}"
        )

    adapter = AxialKidneyStoneAdapter(str(data_root))
    adapter.discover()
    records = adapter.get_records()

    if not records:
        print("ERROR: No valid images found.")
        return

    # ── Load model ────────────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device.type.upper()}")
    if device.type == "cuda":
        print(f"GPU:    {torch.cuda.get_device_name(0)}\n")

    model = build_classifier(cfg)
    ckpt  = torch.load(args.checkpoint, map_location=device)
    state = ckpt.get("model_state_dict", ckpt)
    model.load_state_dict(state)
    model.to(device)
    model.eval()

    input_size = cfg["classification"].get("input_size", 224)
    transform  = get_classification_transforms("test", input_size)

    # ── Collect raw probabilities per image ───────────────────────────────────
    print("Collecting stone probabilities …")
    y_true_bin:    List[int]   = []
    stone_probs:   List[float] = []
    prediction_rows: List[Dict] = []

    with torch.no_grad():
        for rec in tqdm(records, desc="Inference"):
            try:
                img = Image.open(rec["image_path"]).convert("RGB")
            except Exception:
                continue

            tensor = transform(img).unsqueeze(0).to(device)
            logits = model(tensor)
            probs  = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

            pred_idx   = int(np.argmax(probs))
            pred_class = CLASS_NAMES[pred_idx]
            stone_prob = float(probs[STONE_IDX])

            gt_bin = 1 if rec["ground_truth"] == "STONE" else 0
            y_true_bin.append(gt_bin)
            stone_probs.append(stone_prob)

            prediction_rows.append({
                "image_path":    rec["image_path"],
                "filename":      rec["filename"],
                "ground_truth":  rec["ground_truth"],
                "predicted_class": pred_class,
                "normal_prob":   round(float(probs[0]), 6),
                "cyst_prob":     round(float(probs[1]), 6),
                "stone_prob":    round(stone_prob, 6),
                "tumor_prob":    round(float(probs[3]), 6),
                "confidence":    round(float(probs[pred_idx]), 6),
            })
            img.close()

    roc_auc = _compute_roc_auc(y_true_bin, stone_probs)
    print(f"\nROC-AUC (continuous, threshold-independent): {roc_auc:.6f}")

    # ── Sweep thresholds ──────────────────────────────────────────────────────
    print("\nThreshold sweep …")
    threshold_rows: List[Dict] = []
    for thr in THRESHOLDS:
        row = _binary_metrics(y_true_bin, stone_probs, thr)
        row["roc_auc"] = round(roc_auc, 6)
        threshold_rows.append(row)
        print(
            f"  thr={thr:.2f}  acc={row['accuracy']:.4f}  "
            f"prec={row['precision']:.4f}  rec={row['recall']:.4f}  "
            f"spec={row['specificity']:.4f}  F1={row['f1']:.4f}  "
            f"TP={row['TP']}  FP={row['FP']}  FN={row['FN']}  TN={row['TN']}"
        )

    # ── Save outputs ──────────────────────────────────────────────────────────
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path  = out_dir / "threshold_results.csv"
    json_path = out_dir / "threshold_results.json"

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["threshold","accuracy","precision","recall",
                           "specificity","f1","roc_auc","TP","TN","FP","FN"]
        )
        writer.writeheader()
        writer.writerows(threshold_rows)

    with open(json_path, "w") as f:
        json.dump({
            "checkpoint":    args.checkpoint,
            "total_images":  len(y_true_bin),
            "stone_images":  sum(y_true_bin),
            "non_stone_images": len(y_true_bin) - sum(y_true_bin),
            "roc_auc":       round(roc_auc, 6),
            "threshold_results": threshold_rows,
        }, f, indent=2)

    print(f"\nSaved: {csv_path}")
    print(f"Saved: {json_path}")

    # ── Plot ──────────────────────────────────────────────────────────────────
    _plot_threshold_metrics(threshold_rows, out_dir)


def _plot_threshold_metrics(rows: List[Dict], out_dir: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        thresholds  = [r["threshold"]    for r in rows]
        precisions  = [r["precision"]    for r in rows]
        recalls     = [r["recall"]       for r in rows]
        specificities = [r["specificity"] for r in rows]
        f1s         = [r["f1"]           for r in rows]
        accuracies  = [r["accuracy"]     for r in rows]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(thresholds, precisions,    marker="o", label="Precision",    linewidth=2)
        ax.plot(thresholds, recalls,       marker="s", label="Recall",       linewidth=2)
        ax.plot(thresholds, specificities, marker="^", label="Specificity",  linewidth=2)
        ax.plot(thresholds, f1s,           marker="D", label="F1",           linewidth=2)
        ax.plot(thresholds, accuracies,    marker="x", label="Accuracy",     linewidth=2, linestyle="--")

        ax.set_xlabel("Stone Probability Threshold", fontsize=12)
        ax.set_ylabel("Metric Value", fontsize=12)
        ax.set_title("Threshold vs. Binary Stone Detection Metrics\n(External Axial CT Dataset)", fontsize=13)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xticks(thresholds)
        ax.set_xlim(0.05, 0.95)
        ax.set_ylim(0, 1.05)

        fig.tight_layout()
        plot_path = out_dir / "threshold_vs_metrics.png"
        fig.savefig(plot_path, dpi=150)
        plt.close(fig)
        print(f"Saved: {plot_path}")
    except ImportError:
        print("matplotlib not available — skipping plot.")


def main():
    parser = argparse.ArgumentParser(description="Threshold Analysis — Inference Only")
    parser.add_argument(
        "--checkpoint", type=str,
        default="ai-engine/weights/classification/best_model.pth",
    )
    parser.add_argument(
        "--data-root", type=str,
        default="datasets/raw/classification/additional_dataset/Kidney Stone Dataset/Original",
    )
    parser.add_argument(
        "--output", type=str,
        default="outputs/experiments/threshold",
    )
    args = parser.parse_args()
    run_threshold_analysis(args)


if __name__ == "__main__":
    main()
