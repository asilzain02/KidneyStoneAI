"""
model.py — EXP15 model.

EfficientNet-B2 with a 4-class head.
(Baseline is EfficientNet-B0 at 224x224. EXP15 is B2 at 320x320).
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

class EXP15Model(nn.Module):
    def __init__(self, dropout: float = 0.3, pretrained: bool = True):
        super().__init__()
        if not _TIMM_OK:
            raise ImportError("timm is required: pip install timm")
        # EXP15 changes EfficientNet-B0 to EfficientNet-B2
        self.backbone = timm.create_model(
            "efficientnet_b2", pretrained=pretrained, num_classes=0
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

def build_exp15_model(cfg: dict) -> EXP15Model:
    m_cfg = cfg.get("model", {})
    return EXP15Model(
        dropout   = float(m_cfg.get("dropout", 0.3)),
        pretrained= bool(m_cfg.get("pretrained", True)),
    )

def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
