"""
classifier.py — EfficientNet-B0 based four-class kidney CT classifier.

Uses timm for model construction so the backbone is easy to swap later.
"""

from __future__ import annotations

from typing import Dict, Optional

import torch
import torch.nn as nn

try:
    import timm
    _TIMM_AVAILABLE = True
except ImportError:
    _TIMM_AVAILABLE = False


NUM_CLASSES = 4
CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]


class KidneyClassifier(nn.Module):
    """
    Transfer-learning classifier built on EfficientNet-B0.

    Parameters
    ----------
    num_classes : int      (default 4)
    backbone    : str      timm model name (default 'efficientnet_b0')
    pretrained  : bool     load ImageNet weights
    dropout     : float    dropout before the classification head
    """

    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        backbone: str = "efficientnet_b0",
        pretrained: bool = True,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.num_classes = num_classes
        self.backbone_name = backbone

        if not _TIMM_AVAILABLE:
            raise ImportError("timm is required: pip install timm")

        # Build backbone — num_classes=0 removes the default head
        self.backbone = timm.create_model(
            backbone,
            pretrained=pretrained,
            num_classes=0,   # remove classifier head
        )
        in_features = self.backbone.num_features

        # Custom classification head
        self.head = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)   # [B, in_features]
        logits = self.head(features)  # [B, num_classes]
        return logits

    def get_feature_extractor(self) -> nn.Module:
        """Return backbone without head — useful for Grad-CAM."""
        return self.backbone

    def freeze_backbone(self) -> None:
        """Freeze all backbone parameters (fine-tune head only)."""
        for param in self.backbone.parameters():
            param.requires_grad = False

    def unfreeze_backbone(self) -> None:
        """Unfreeze backbone for full fine-tuning."""
        for param in self.backbone.parameters():
            param.requires_grad = True


def build_classifier(cfg: Dict) -> KidneyClassifier:
    """
    Build a KidneyClassifier from a config dict.

    Expected keys (with defaults):
        backbone, num_classes, pretrained, dropout
    """
    clf_cfg = cfg.get("classification", cfg)
    return KidneyClassifier(
        num_classes=clf_cfg.get("num_classes", NUM_CLASSES),
        backbone=clf_cfg.get("backbone", "efficientnet_b0"),
        pretrained=clf_cfg.get("pretrained", True),
        dropout=clf_cfg.get("dropout", 0.3),
    )
