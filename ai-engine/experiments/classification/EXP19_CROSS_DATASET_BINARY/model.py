"""
EXP19 Model Definition
Binary variant of EfficientNet.
"""
from __future__ import annotations
import torch
import torch.nn as nn
import timm

class Exp19SqueezeModel(nn.Module):
    def __init__(self, name="efficientnet_b0", pretrained=True, num_classes=2):
        super().__init__()
        self.backbone = timm.create_model(name, pretrained=pretrained, num_classes=0)
        self.head = nn.Linear(self.backbone.num_features, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(x))

def build_exp19_model(cfg: dict) -> nn.Module:
    model_cfg = cfg["model"]
    return Exp19SqueezeModel(
        name=model_cfg["name"],
        pretrained=model_cfg["pretrained"],
        num_classes=model_cfg["num_classes"]
    )

def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
