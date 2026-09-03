"""
classification_metrics.py — Full classification evaluation.

Computes per-class and aggregate metrics including Stone-specific reporting.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]


def compute_classification_metrics(
    y_true: List[int],
    y_pred: List[int],
    y_prob: Optional[np.ndarray] = None,  # [N, num_classes] softmax probabilities
    class_names: Optional[List[str]] = None,
) -> Dict:
    """
    Compute full classification evaluation metrics.

    Parameters
    ----------
    y_true      : ground-truth label indices
    y_pred      : predicted label indices
    y_prob      : softmax probabilities (needed for ROC-AUC)
    class_names : list of class name strings

    Returns
    -------
    dict with all metrics
    """
    names = class_names or CLASS_NAMES
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    accuracy = float(accuracy_score(y_true, y_pred))

    precision_per_class, recall_per_class, f1_per_class, support = (
        precision_recall_fscore_support(y_true, y_pred, labels=list(range(len(names))), zero_division=0)
    )

    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(names)))).tolist()

    # Per-class dict
    per_class = {}
    for i, name in enumerate(names):
        per_class[name] = {
            "precision": float(precision_per_class[i]),
            "recall": float(recall_per_class[i]),
            "f1": float(f1_per_class[i]),
            "support": int(support[i]),
        }

    # AUC — multi-class OVR
    auc_scores = None
    if y_prob is not None:
        try:
            auc_scores = float(
                roc_auc_score(y_true, y_prob, multi_class="ovr", average="macro")
            )
        except ValueError:
            auc_scores = None   # can fail with single class present

    # Stone-specific highlight
    stone_idx = names.index("Stone") if "Stone" in names else None
    stone_metrics = per_class.get("Stone", {}) if stone_idx is not None else {}

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "roc_auc_macro_ovr": auc_scores,
        "per_class": per_class,
        "stone_precision": stone_metrics.get("precision"),
        "stone_recall": stone_metrics.get("recall"),
        "stone_f1": stone_metrics.get("f1"),
        "confusion_matrix": cm,
        "class_names": names,
        "report": classification_report(
            y_true, y_pred, target_names=names, zero_division=0
        ),
    }
