"""
experiment_comparison.py — Centralized experiment reporting and tracking.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Any

from utils.logger import get_logger

log = get_logger(__name__)

CSV_HEADERS = [
    "Experiment",
    "Changed Parameter",
    "Baseline Value",
    "Experimental Value",
    "Dice",
    "IoU",
    "Precision",
    "Recall",
    "Sensitivity",
    "Specificity",
    "F1",
    "Pixel Accuracy",
    "Best Epoch",
    "Training Time",
    "Parameter Count",
    "Dice Delta",
    "IoU Delta",
    "Precision Delta",
    "Recall Delta",
    "F1 Delta"
]


def update_experiment_results(
    exp_id: str,
    metrics: Dict[str, float],
    training_meta: Dict[str, Any],
    outputs_root: Path
):
    """
    Append or update the experiment_results.csv file with the real metrics.
    Only writes actual execution data. No fake results.
    """
    csv_path = outputs_root / "experiments" / "experiment_results.csv"
    
    # 1. Read existing to find if we're updating or appending
    rows = []
    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
                
    # Extract baseline metrics to calculate deltas
    baseline_metrics = {}
    for r in rows:
        if r["Experiment"] == "EXP00_BASELINE":
            baseline_metrics = {k: float(v) for k, v in r.items() if v and _is_float(v)}
            break
            
    # Calculate deltas if baseline exists
    dice_delta = ""
    iou_delta = ""
    prec_delta = ""
    rec_delta = ""
    f1_delta = ""
    
    if baseline_metrics and exp_id != "EXP00_BASELINE":
        dice_delta = f"{metrics.get('dice', 0.0) - baseline_metrics.get('Dice', 0.0):.4f}"
        iou_delta = f"{metrics.get('iou', 0.0) - baseline_metrics.get('IoU', 0.0):.4f}"
        prec_delta = f"{metrics.get('precision', 0.0) - baseline_metrics.get('Precision', 0.0):.4f}"
        rec_delta = f"{metrics.get('recall', 0.0) - baseline_metrics.get('Recall', 0.0):.4f}"
        f1_delta = f"{metrics.get('f1', 0.0) - baseline_metrics.get('F1', 0.0):.4f}"

    # Load experiment definition
    exp_dir = outputs_root / "experiments" / exp_id
    meta_path = exp_dir / "experiment_meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {}

    row_data = {
        "Experiment": exp_id,
        "Changed Parameter": meta.get("changed_parameter", ""),
        "Baseline Value": str(meta.get("baseline_value", "")),
        "Experimental Value": str(meta.get("experimental_value", "")),
        "Dice": f"{metrics.get('dice', 0.0):.4f}",
        "IoU": f"{metrics.get('iou', 0.0):.4f}",
        "Precision": f"{metrics.get('precision', 0.0):.4f}",
        "Recall": f"{metrics.get('recall', 0.0):.4f}",
        "Sensitivity": f"{metrics.get('sensitivity', 0.0):.4f}",
        "Specificity": f"{metrics.get('specificity', 0.0):.4f}",
        "F1": f"{metrics.get('f1', 0.0):.4f}",
        "Pixel Accuracy": f"{metrics.get('pixel_accuracy', 0.0):.4f}",
        "Best Epoch": str(training_meta.get("best_epoch", "N/A")),
        "Training Time": str(training_meta.get("training_time", "N/A")),
        "Parameter Count": str(training_meta.get("parameter_count", "N/A")),
        "Dice Delta": dice_delta,
        "IoU Delta": iou_delta,
        "Precision Delta": prec_delta,
        "Recall Delta": rec_delta,
        "F1 Delta": f1_delta
    }

    # Replace existing row if it exists, else append
    replaced = False
    for i, r in enumerate(rows):
        if r["Experiment"] == exp_id:
            rows[i] = row_data
            replaced = True
            break
            
    if not replaced:
        rows.append(row_data)
        
    # Write back
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
        
    log.info("Appended results to experiment comparison", path=str(csv_path))


def _is_float(v: str) -> bool:
    try:
        float(v)
        return True
    except ValueError:
        return False
