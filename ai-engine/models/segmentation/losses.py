"""
losses.py — Extended segmentation loss factory.

Re-exports DiceLoss and DiceBCELoss from training/losses.py and adds:
  - BCEWithLogitsLoss (for raw logit outputs, no sigmoid in model)

Factory function: get_loss(config)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

import torch.nn as nn

sys.path.insert(0, str(Path(__file__).parents[2]))

# Re-export existing losses — no duplication
from training.losses import DiceLoss, DiceBCELoss, get_segmentation_loss  # noqa: F401


def get_loss(config: Dict) -> nn.Module:
    """
    Extended loss factory.

    Reads config["loss"]["name"] (segmentation_config.yaml format).
    Falls back to config["segmentation"]["loss"] for backward compat.

    Supported:
        dice            → DiceLoss
        bce             → nn.BCELoss  (model must output [0,1] probabilities)
        dice_bce        → DiceBCELoss (model must output [0,1] probabilities)
        bce_with_logits → nn.BCEWithLogitsLoss (model outputs raw logits)
    """
    # Support both config formats
    loss_cfg = config.get("loss", {})
    if loss_cfg and "name" in loss_cfg:
        name = loss_cfg["name"].lower()
        dice_w = float(loss_cfg.get("dice_weight", 0.5))
        bce_w = float(loss_cfg.get("bce_weight", 0.5))
    else:
        # Legacy training_config.yaml format
        seg = config.get("segmentation", config)
        name = seg.get("loss", "dice_bce").lower()
        dice_w = float(seg.get("dice_weight", 0.5))
        bce_w = float(seg.get("bce_weight", 0.5))

    if name == "dice":
        return DiceLoss()
    elif name == "bce":
        return nn.BCELoss()
    elif name == "dice_bce":
        return DiceBCELoss(dice_weight=dice_w, bce_weight=bce_w)
    elif name == "bce_with_logits":
        return nn.BCEWithLogitsLoss()
    else:
        raise ValueError(
            f"Unknown loss '{name}'. "
            "Use: dice | bce | dice_bce | bce_with_logits"
        )
