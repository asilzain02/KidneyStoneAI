"""
classification_transforms.py — torchvision transforms for CT kidney classification.

Strategy options:

  baseline  — original augmentation (unchanged from initial training)
  moderate  — adds GaussianBlur + slight elastic-style shifts (CT-appropriate)
  strong    — adds RandomGrayscale, GridDistortion-equivalent, stronger rotations

Validation / Test are always deterministic (no augmentation).
"""

from __future__ import annotations

from typing import Literal

import torchvision.transforms as T

# EfficientNet pretrained on ImageNet
_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD  = (0.229, 0.224, 0.225)


def get_classification_transforms(
    phase: Literal["train", "val", "test"],
    input_size: int = 224,
    strategy: str = "baseline",
) -> T.Compose:
    """
    Return a deterministic (val/test) or augmented (train) transform pipeline.

    Parameters
    ----------
    phase      : "train" | "val" | "test"
    input_size : int  (224 for B0, 256 for larger variants)
    strategy   : "baseline" | "moderate" | "strong"  (only applied to train)
    """
    # ── Validation / Test — always deterministic, no augmentation ─────────────
    if phase != "train":
        return T.Compose([
            T.Resize((input_size, input_size)),
            T.ToTensor(),
            T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
        ])

    # ── Training augmentation ─────────────────────────────────────────────────
    strategy = (strategy or "baseline").lower()

    if strategy == "baseline":
        return T.Compose([
            T.Resize((input_size + 32, input_size + 32)),
            T.RandomCrop(input_size),
            T.RandomHorizontalFlip(p=0.5),
            T.RandomRotation(degrees=10),
            T.ColorJitter(brightness=0.2, contrast=0.2),
            T.ToTensor(),
            T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
        ])

    elif strategy == "moderate":
        # Conservative additions appropriate for axial CT slices:
        # - Slight vertical flip (CT axial slices can appear mirrored in some
        #   acquisition protocols)
        # - GaussianBlur to simulate mild reconstruction kernel variation
        # - Slightly wider rotation (axial slices can have positioning offsets)
        return T.Compose([
            T.Resize((input_size + 32, input_size + 32)),
            T.RandomCrop(input_size),
            T.RandomHorizontalFlip(p=0.5),
            T.RandomVerticalFlip(p=0.2),
            T.RandomRotation(degrees=15),
            T.ColorJitter(brightness=0.25, contrast=0.25),
            T.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),
            T.ToTensor(),
            T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
        ])

    elif strategy == "strong":
        # Stronger augmentation — still medically conservative.
        # No colour-only transforms that break CT Hounsfield relationships.
        # RandomAffine provides shear+translate which simulate patient
        # positioning variation.
        return T.Compose([
            T.Resize((input_size + 48, input_size + 48)),
            T.RandomCrop(input_size),
            T.RandomHorizontalFlip(p=0.5),
            T.RandomVerticalFlip(p=0.3),
            T.RandomRotation(degrees=20),
            T.RandomAffine(degrees=0, translate=(0.05, 0.05), shear=5),
            T.ColorJitter(brightness=0.3, contrast=0.3),
            T.GaussianBlur(kernel_size=5, sigma=(0.1, 2.0)),
            T.ToTensor(),
            T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
        ])

    else:
        raise ValueError(
            f"Unknown augmentation strategy: '{strategy}'. "
            "Choose one of: baseline | moderate | strong"
        )

