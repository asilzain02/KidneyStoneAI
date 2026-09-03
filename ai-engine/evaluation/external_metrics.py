"""
external_metrics.py — Metrics strictly mapping to the binary representation bounds
of STONE vs NON_STONE.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

def compute_external_binary_metrics(
    y_true: List[str],
    y_pred: List[str],
    stone_probabilities: Optional[List[float]] = None
) -> Dict:
    """
    Targeted evaluation measuring independent success specifically mapping to Binary STONE arrays.
    
    Positive Class = STONE
    Negative Class = NON_STONE
    """
    
    # Map purely to binary arrays for sklearn 
    # STONE = 1, NON_STONE = 0
    yt_bin = [1 if gt == "STONE" else 0 for gt in y_true]
    yp_bin = [1 if pr == "STONE" else 0 for pr in y_pred]

    if not yt_bin:
        return {}

    acc = float(accuracy_score(yt_bin, yp_bin))
    precision = float(precision_score(yt_bin, yp_bin, zero_division=0))
    recall = float(recall_score(yt_bin, yp_bin, zero_division=0))
    f1 = float(f1_score(yt_bin, yp_bin, zero_division=0))
    
    # Specificity = TN / (TN + FP)
    cm = confusion_matrix(yt_bin, yp_bin, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    
    roc_auc = None
    if stone_probabilities:
        try:
            roc_auc = float(roc_auc_score(yt_bin, stone_probabilities))
        except ValueError:
            # Fails natively if only one class exists in the subset bounds
            pass

    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": cm.tolist(),
        "counts": {
            "TP": int(tp),
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn)
        }
    }
