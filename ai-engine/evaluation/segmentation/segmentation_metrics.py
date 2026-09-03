"""
segmentation_metrics.py — Extended binary segmentation metrics.

Extends the base metrics (Dice, IoU, Precision, Recall) with:
  - Specificity
  - F1  (same as Dice for binary, included for completeness)
  - Pixel Accuracy
  - Sensitivity (same as Recall, alias)
  - Hausdorff distance (optional, requires scipy)

All functions accept:
  pred   : np.ndarray or torch.Tensor — probability map or binary mask
  target : np.ndarray or torch.Tensor — binary ground truth

Threshold is applied internally when pred is a probability map.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import torch


# ── Conversion helper ─────────────────────────────────────────────────────────

def _to_numpy(t) -> np.ndarray:
    if isinstance(t, torch.Tensor):
        return t.detach().cpu().numpy()
    return np.asarray(t, dtype=np.float32)


# ── Core metrics ──────────────────────────────────────────────────────────────

def compute_sample_metrics(
    pred: np.ndarray,
    target: np.ndarray,
    threshold: float = 0.5,
    smooth: float = 1e-6,
    include_hausdorff: bool = False,
) -> Dict[str, float]:
    """
    Compute full binary segmentation metrics for one sample.

    Parameters
    ----------
    pred     : probability map [H, W] or [1, H, W]  in [0, 1]
    target   : binary ground truth [H, W] or [1, H, W]  in {0, 1}
    threshold: binarization threshold
    smooth   : numerical stability epsilon

    Returns
    -------
    dict with keys:
        dice, iou, precision, recall, specificity, f1,
        pixel_accuracy, sensitivity, tp, fp, fn, tn
    """
    pred = _to_numpy(pred).flatten()
    target = _to_numpy(target).flatten().astype(np.float32)
    pred_bin = (pred > threshold).astype(np.float32)

    tp = float((pred_bin * target).sum())
    fp = float((pred_bin * (1 - target)).sum())
    fn = float(((1 - pred_bin) * target).sum())
    tn = float(((1 - pred_bin) * (1 - target)).sum())

    dice        = (2 * tp + smooth) / (2 * tp + fp + fn + smooth)
    iou         = (tp + smooth) / (tp + fp + fn + smooth)
    precision   = (tp + smooth) / (tp + fp + smooth)
    recall      = (tp + smooth) / (tp + fn + smooth)        # sensitivity
    specificity = (tn + smooth) / (tn + fp + smooth)
    f1          = dice                                       # same as dice for binary
    pixel_acc   = (tp + tn + smooth) / (tp + tn + fp + fn + smooth)

    result = {
        "dice":          round(float(dice), 6),
        "iou":           round(float(iou), 6),
        "precision":     round(float(precision), 6),
        "recall":        round(float(recall), 6),
        "sensitivity":   round(float(recall), 6),   # alias
        "specificity":   round(float(specificity), 6),
        "f1":            round(float(f1), 6),
        "pixel_accuracy": round(float(pixel_acc), 6),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
    }

    if include_hausdorff:
        result["hausdorff_distance"] = _hausdorff(pred_bin, target)

    return result


def compute_dataset_metrics(
    preds: List,
    targets: List,
    threshold: float = 0.5,
    include_hausdorff: bool = False,
) -> Dict[str, float]:
    """
    Average metrics over a list of (pred, target) pairs.

    Returns mean and std for each metric.
    """
    all_m = [
        compute_sample_metrics(p, t, threshold, include_hausdorff=include_hausdorff)
        for p, t in zip(preds, targets)
    ]

    scalar_keys = [
        "dice", "iou", "precision", "recall", "sensitivity",
        "specificity", "f1", "pixel_accuracy",
    ]
    if include_hausdorff:
        scalar_keys.append("hausdorff_distance")

    result: Dict[str, float] = {}
    for k in scalar_keys:
        vals = [m[k] for m in all_m if k in m]
        if vals:
            result[f"mean_{k}"] = round(float(np.mean(vals)), 6)
            result[f"std_{k}"]  = round(float(np.std(vals)), 6)

    # Also return raw per-sample metrics
    result["per_sample"] = all_m  # type: ignore[assignment]
    return result


# ── Best / worst sample selection ─────────────────────────────────────────────

def select_best_worst(
    per_sample_metrics: List[Dict],
    stems: List[str],
    n: int = 5,
    metric: str = "dice",
) -> Dict[str, List[str]]:
    """
    Select stems of best and worst performing samples.

    Returns
    -------
    dict with keys: best, worst, highest_fp, highest_fn
    """
    paired = list(zip(stems, per_sample_metrics))

    sorted_by_metric = sorted(paired, key=lambda x: x[1].get(metric, 0))

    worst_stems = [s for s, _ in sorted_by_metric[:n]]
    best_stems  = [s for s, _ in sorted_by_metric[-n:]]

    # Highest FP (false positive heavy)
    sorted_fp = sorted(paired, key=lambda x: x[1].get("fp", 0), reverse=True)
    fp_stems  = [s for s, _ in sorted_fp[:n]]

    # Highest FN (missed stones)
    sorted_fn = sorted(paired, key=lambda x: x[1].get("fn", 0), reverse=True)
    fn_stems  = [s for s, _ in sorted_fn[:n]]

    return {
        "best":           best_stems,
        "worst":          worst_stems,
        "highest_fp":     fp_stems,
        "highest_fn":     fn_stems,
    }


# ── Hausdorff distance (optional) ─────────────────────────────────────────────

def _hausdorff(pred_bin: np.ndarray, target: np.ndarray) -> float:
    """
    Compute Hausdorff distance between predicted and target binary masks.
    Requires scipy. Returns -1.0 if scipy not available or masks are empty.
    """
    try:
        from scipy.spatial.distance import directed_hausdorff
        pred_pts = np.argwhere(pred_bin.reshape(-1) > 0.5)
        tgt_pts  = np.argwhere(target.reshape(-1) > 0.5)
        if len(pred_pts) == 0 or len(tgt_pts) == 0:
            return -1.0
        h1 = directed_hausdorff(pred_pts, tgt_pts)[0]
        h2 = directed_hausdorff(tgt_pts, pred_pts)[0]
        return round(float(max(h1, h2)), 4)
    except Exception:
        return -1.0
