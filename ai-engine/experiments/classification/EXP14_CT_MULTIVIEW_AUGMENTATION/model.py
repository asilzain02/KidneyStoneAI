"""
model.py — EXP14 model.

EfficientNet-B0 with a 4-class head.
Architecture UNCHANGED from baseline — isolates augmentation/preprocessing.
"""

from __future__ import annotations

import torch
import torch.nn as nn

try:
    import timm
    _TIMM_OK = True
except ImportError:
    _TIMM_OK = False

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]


class EXP14Model(nn.Module):
    """
    EfficientNet-B0 + 4-class head for EXP14.
    Identical architecture to the production baseline.
    """

    def __init__(self, dropout: float = 0.3, pretrained: bool = True):
        super().__init__()
        if not _TIMM_OK:
            raise ImportError("timm is required: pip install timm")
        self.backbone = timm.create_model(
            "efficientnet_b0", pretrained=pretrained, num_classes=0
        )
        in_features = self.backbone.num_features
        self.head = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, 4),
        )
        self.num_classes = 4
        self.class_names = CLASS_NAMES

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(x))


def build_exp14_model(cfg: dict) -> EXP14Model:
    m_cfg = cfg.get("model", {})
    return EXP14Model(
        dropout   = float(m_cfg.get("dropout", 0.3)),
        pretrained= bool(m_cfg.get("pretrained", True)),
    )


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
