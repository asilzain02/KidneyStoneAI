"""
model.py — EXP18 Model
"""

from __future__ import annotations
import torch
import torch.nn as nn

try: import timm; _TIMM_OK = True
except ImportError: _TIMM_OK = False

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]

class EXP18Model(nn.Module):
    def __init__(self, dropout: float = 0.3, pretrained: bool = True):
        super().__init__()
        if not _TIMM_OK: raise ImportError("timm is required")
        self.backbone = timm.create_model("efficientnet_b2", pretrained=pretrained, num_classes=0)
        self.head = nn.Sequential(nn.Dropout(p=dropout), nn.Linear(self.backbone.num_features, 4))

    def forward(self, x: torch.Tensor) -> torch.Tensor: return self.head(self.backbone(x))

def build_exp18_model(cfg: dict) -> EXP18Model:
    return EXP18Model(dropout=float(cfg.get("model", {}).get("dropout", 0.3)), pretrained=bool(cfg.get("model", {}).get("pretrained", True)))

def count_parameters(model: nn.Module) -> int: return sum(p.numel() for p in model.parameters() if p.requires_grad)
