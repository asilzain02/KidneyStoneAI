"""
test_evaluation.py — Tests for evaluation metrics.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np

import pytest


class TestEvaluationMetrics:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

    def test_compute_classification_metrics(self):
        from evaluation.classification_metrics import compute_classification_metrics
        y_true = [0, 1, 2, 2, 3]
        y_pred = [0, 1, 2, 3, 3] # One mistake: predicted 3 instead of 2 for fourth item.
        names = ["Normal", "Cyst", "Stone", "Tumor"]
        
        # Fake probs just to make roc_auc work, giving correct class 0.8, others 0.2/3 except the mistake.
        y_prob = np.array([
            [0.8, 0.1, 0.05, 0.05],
            [0.05, 0.8, 0.1, 0.05],
            [0.1, 0.05, 0.8, 0.05],
            [0.1, 0.05, 0.1, 0.75], # Mistake
            [0.05, 0.1, 0.05, 0.8]
        ])

        results = compute_classification_metrics(y_true, y_pred, y_prob, names)
        assert results["accuracy"] == 0.8 # 4/5 correct
        assert "Stone" in results["per_class"]
        assert results["stone_precision"] == 1.0 # predicted stone once, it was correct
        assert results["stone_recall"] == 0.5 # it was stone twice, predicted once
        assert results["roc_auc_macro_ovr"] is not None

    def test_compute_segmentation_metrics(self):
        from evaluation.segmentation_metrics import compute_sample_metrics, compute_segmentation_metrics
        target = np.zeros((10, 10))
        target[2:5, 2:5] = 1 # 3*3 = 9 pixels

        pred = np.zeros((10, 10))
        pred[2:5, 2:5] = 0.9

        res1 = compute_sample_metrics(pred, target, threshold=0.5)
        # Should be perfect Dice
        assert res1["dice"] > 0.99
        assert res1["iou"] > 0.99

        pred2 = np.zeros((10, 10))
        pred2[2:5, 2:5] = 0.9
        pred2[5:8, 5:8] = 0.9 # Extra 9 pixels, 18 total pred, 9 target. Intersection 9.
        res2 = compute_sample_metrics(pred2, target, threshold=0.5)
        # Dice = 2*9 / (18+9) = 18/27 = 0.666
        assert abs(res2["dice"] - 0.666) < 0.05

        # compute_segmentation_metrics
        preds = [pred, pred2]
        targets = [target, target]
        avg_res = compute_segmentation_metrics(preds, targets)
        expected_avg_dice = (res1["dice"] + res2["dice"]) / 2
        assert abs(avg_res["dice"] - expected_avg_dice) < 0.01
