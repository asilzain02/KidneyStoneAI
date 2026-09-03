"""
losses.py — Segmentation loss functions.

Supports:
    DiceLoss         — Dice/F1 loss
    DiceBCELoss      — Weighted combination of Dice + BCE
    get_segmentation_loss(cfg) — factory function
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

class TverskyLoss(nn.Module):
    """
    Tversky Loss for binary segmentation.

    Tversky Index:
        TP / (TP + alpha * FP + beta * FN)

    alpha controls the penalty for false positives.
    beta controls the penalty for false negatives.
    """

    def __init__(
        self,
        alpha: float = 0.5,
        beta: float = 0.5,
        smooth: float = 1e-6,
    ):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.smooth = smooth

    def forward(
        self,
        inputs: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:

        # Inputs are model probabilities in the current pipeline.
        inputs = inputs.contiguous().view(-1)
        targets = targets.contiguous().view(-1)

        true_positive = (inputs * targets).sum()
        false_positive = ((1 - targets) * inputs).sum()
        false_negative = (targets * (1 - inputs)).sum()

        tversky_index = (
            true_positive + self.smooth
        ) / (
            true_positive
            + self.alpha * false_positive
            + self.beta * false_negative
            + self.smooth
        )

        return 1.0 - tversky_index


class DiceLoss(nn.Module):
    """
    Soft Dice Loss for binary segmentation.

    Loss = 1 - (2 * |pred ∩ target| + ε) / (|pred| + |target| + ε)
    """

    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        pred = pred.view(-1)
        target = target.view(-1)
        intersection = (pred * target).sum()
        dice = (2.0 * intersection + self.smooth) / (
            pred.sum() + target.sum() + self.smooth
        )
        return 1.0 - dice


class DiceBCELoss(nn.Module):
    """
    Weighted combination of Dice Loss and Binary Cross-Entropy.

    loss = dice_weight * DiceLoss + bce_weight * BCELoss
    """

    def __init__(
        self,
        dice_weight: float = 0.5,
        bce_weight: float = 0.5,
        smooth: float = 1.0,
    ):
        super().__init__()
        self.dice_weight = dice_weight
        self.bce_weight = bce_weight
        self.dice = DiceLoss(smooth=smooth)

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        dice_loss = self.dice(pred, target)
        bce_loss = F.binary_cross_entropy(pred, target)
        return self.dice_weight * dice_loss + self.bce_weight * bce_loss


# def get_segmentation_loss(cfg: dict) -> nn.Module:
#     """
#     Factory for segmentation loss based on config.

#     cfg["segmentation"]["loss"] options:
#         "dice"      → DiceLoss
#         "bce"       → BCELoss
#         "dice_bce"  → DiceBCELoss (default)
#     """
#     seg_cfg = cfg.get("segmentation", cfg)
#     loss_name = seg_cfg.get("loss", "dice_bce").lower()

#     if loss_name == "dice":
#         return DiceLoss()
#     elif loss_name == "bce":
#         return nn.BCELoss()
#     elif loss_name == "tversky":
#         return TverskyLoss(
#             alpha=cfg["loss"].get("alpha", 0.5),
#             beta=cfg["loss"].get("beta", 0.5),
#         )
#     elif loss_name == "dice_bce":
#         return DiceBCELoss(
#             dice_weight=seg_cfg.get("dice_weight", 0.5),
#             bce_weight=seg_cfg.get("bce_weight", 0.5),
#         )
#     else:
#         raise ValueError(f"Unknown segmentation loss: {loss_name}")

def get_segmentation_loss(cfg: dict) -> nn.Module:
    """
    Factory for segmentation loss based on config.

    cfg["segmentation"]["loss"] options:
        "dice"      → DiceLoss
        "bce"       → BCELoss
        "dice_bce"  → DiceBCELoss
        "tversky"   → TverskyLoss
    """

    seg_cfg = cfg.get("segmentation", cfg)

    loss_name = seg_cfg.get("loss", "dice_bce").lower()

    if loss_name == "dice":
        return DiceLoss()

    elif loss_name == "bce":
        return nn.BCELoss()

    elif loss_name == "tversky":
        return TverskyLoss(
            alpha=seg_cfg.get("alpha", 0.5),
            beta=seg_cfg.get("beta", 0.5),
        )

    elif loss_name == "dice_bce":
        return DiceBCELoss(
            dice_weight=seg_cfg.get("dice_weight", 0.5),
            bce_weight=seg_cfg.get("bce_weight", 0.5),
        )

    else:
        raise ValueError(
            f"Unknown segmentation loss: {loss_name}"
        )