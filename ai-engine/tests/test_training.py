"""
test_training.py — Tests for losses.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch


class TestLosses:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

    def test_dice_loss_perfect_match(self):
        from training.losses import DiceLoss
        loss_fn = DiceLoss(smooth=1.0)
        pred = torch.ones(1, 1, 64, 64)
        target = torch.ones(1, 1, 64, 64)
        loss = loss_fn(pred, target)
        # Loss = 1 - Dice, Dice = (2*4096+1)/(8192+1) = 8193/8193 = 1 -> Loss = 0
        assert torch.allclose(loss, torch.tensor(0.0))

    def test_dice_loss_complete_mismatch(self):
        from training.losses import DiceLoss
        loss_fn = DiceLoss(smooth=1.0)
        pred = torch.zeros(1, 1, 64, 64)
        target = torch.ones(1, 1, 64, 64)
        loss = loss_fn(pred, target)
        # Loss = 1 - (2*0+1)/(0+4096+1) = 1 - 1/4097 approx 0.9997
        assert loss > 0.99

    def test_dice_bce_loss(self):
        from training.losses import DiceBCELoss
        loss_fn = DiceBCELoss(dice_weight=0.5, bce_weight=0.5, smooth=1.0)
        pred = torch.full((1, 1, 64, 64), 0.5)
        target = torch.ones(1, 1, 64, 64)
        loss = loss_fn(pred, target)
        assert loss > 0.0

    def test_get_segmentation_loss(self):
        from training.losses import get_segmentation_loss, DiceLoss, DiceBCELoss
        cfg_dice = {"segmentation": {"loss": "dice"}}
        loss_dice = get_segmentation_loss(cfg_dice)
        assert isinstance(loss_dice, DiceLoss)

        cfg_bce = {"segmentation": {"loss": "bce"}}
        loss_bce = get_segmentation_loss(cfg_bce)
        assert isinstance(loss_bce, torch.nn.BCELoss)

        cfg_dice_bce = {"segmentation": {"loss": "dice_bce", "dice_weight": 0.5, "bce_weight": 0.5}}
        loss_dice_bce = get_segmentation_loss(cfg_dice_bce)
        assert isinstance(loss_dice_bce, DiceBCELoss)
