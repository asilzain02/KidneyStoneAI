"""
segmentation_metrics.py — Dice, IoU, Precision, Recall for binary segmentation.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import torch


def _to_numpy(t) -> np.ndarray:
    if isinstance(t, torch.Tensor):
        return t.detach().cpu().numpy()
    return np.asarray(t)


def compute_sample_metrics(
    pred: np.ndarray,
    target: np.ndarray,
    threshold: float = 0.5,
    smooth: float = 1e-6,
) -> Dict[str, float]:
    """
    Compute binary segmentation metrics for a single prediction-target pair.

    Parameters
    ----------
    pred    : probability map [H, W] or [1, H, W] in [0, 1]
    target  : binary ground-truth [H, W] or [1, H, W] in {0, 1}
    """
    pred = _to_numpy(pred).flatten()
    target = _to_numpy(target).flatten().astype(np.float32)
    pred_bin = (pred > threshold).astype(np.float32)

    tp = (pred_bin * target).sum()
    fp = (pred_bin * (1 - target)).sum()
    fn = ((1 - pred_bin) * target).sum()

    dice = (2 * tp + smooth) / (2 * tp + fp + fn + smooth)
    iou = (tp + smooth) / (tp + fp + fn + smooth)
    precision = (tp + smooth) / (tp + fp + smooth)
    recall = (tp + smooth) / (tp + fn + smooth)

    return {
        "dice": float(dice),
        "iou": float(iou),
        "precision": float(precision),
        "recall": float(recall),
    }


def compute_segmentation_metrics(
    preds: List,
    targets: List,
    threshold: float = 0.5,
) -> Dict[str, float]:
    """
    Compute averaged segmentation metrics over a list of samples.

    Returns mean Dice, IoU, Precision, Recall.
    """
    all_metrics = [
        compute_sample_metrics(p, t, threshold)
        for p, t in zip(preds, targets)
    ]

    keys = ["dice", "iou", "precision", "recall"]
    return {
        k: float(np.mean([m[k] for m in all_metrics]))
        for k in keys
    }
