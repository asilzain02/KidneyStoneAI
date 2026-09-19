"""
EXP19 Augmentation and Preprocessing
Uses mild CT-appropriate augmentation defined in config.
"""
from __future__ import annotations
import torch
import torchvision.transforms as T
import yaml
from pathlib import Path

_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD  = (0.229, 0.224, 0.225)

def get_exp19_transforms(phase: str, cfg: dict):
    size = int(cfg["model"]["input_size"])
    if phase == "train" and cfg["augmentation"].get("enabled", True):
        aug = cfg["augmentation"]
        return T.Compose([
            T.Resize((size + 32, size + 32)),
            T.RandomAffine(
                degrees=aug.get("rotation", 5),
                translate=(aug.get("translation", 0.05), aug.get("translation", 0.05)),
                scale=tuple(aug.get("scale", [0.95, 1.05]))
            ),
            T.RandomHorizontalFlip(p=aug.get("horizontal_flip", 0.5)),
            T.ColorJitter(
                brightness=aug.get("brightness", 0.1),
                contrast=aug.get("contrast", 0.1)
            ),
            T.RandomCrop(size),
            T.ToTensor(),
            T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD)
        ])
    else:
        return T.Compose([
            T.Resize((size, size)),
            T.ToTensor(),
            T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD)
        ])
