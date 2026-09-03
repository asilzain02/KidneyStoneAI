"""
segmentation_transforms.py — Paired image+mask transforms for KSSD2025.

CRITICAL RULE: Every spatial transformation applied to the image
MUST be applied identically to its mask. Pixel-value-only transforms
(e.g. brightness) are applied to the image ONLY.

Implementation uses a stateless functional approach with a shared
random state per sample pair.
"""

from __future__ import annotations

import random
from typing import Literal, Tuple

import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image


class SegmentationTransform:
    """
    Paired image+mask transform.

    Parameters
    ----------
    phase : {"train", "val", "test"}
    image_size : int   target spatial size (square)
    """

    def __init__(
        self,
        phase: Literal["train", "val", "test"],
        image_size: int = 256,
    ):
        self.phase = phase
        self.image_size = image_size

    def __call__(
        self,
        image: Image.Image,
        mask: Image.Image,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Apply transforms and return (image_tensor, mask_tensor).

        image_tensor : float32 [1, H, W] normalised to [0, 1]
        mask_tensor  : float32 [1, H, W] binary {0.0, 1.0}
        """
        # ── Convert to grayscale ─────────────────────────────────────────────
        image = image.convert("L")
        mask = mask.convert("L")

        # ── Resize ───────────────────────────────────────────────────────────
        image = TF.resize(image, [self.image_size, self.image_size])
        mask = TF.resize(
            mask,
            [self.image_size, self.image_size],
            interpolation=TF.InterpolationMode.NEAREST,  # preserve mask values
        )

        # ── Training augmentation (always paired) ────────────────────────────
        if self.phase == "train":
            # Horizontal flip
            if random.random() > 0.5:
                image = TF.hflip(image)
                mask = TF.hflip(mask)

            # Vertical flip — less common for CT but included
            if random.random() > 0.7:
                image = TF.vflip(image)
                mask = TF.vflip(mask)

            # Rotation (small — up to ±10°)
            angle = random.uniform(-10, 10)
            image = TF.rotate(image, angle)
            mask = TF.rotate(mask, angle)

            # Brightness / contrast — image ONLY (never mask)
            image = TF.adjust_brightness(image, brightness_factor=random.uniform(0.8, 1.2))
            image = TF.adjust_contrast(image, contrast_factor=random.uniform(0.8, 1.2))

        # ── To tensor ────────────────────────────────────────────────────────
        image_t = TF.to_tensor(image)  # [1, H, W], float32, [0,1]

        # Mask: convert to binary float tensor
        mask_arr = np.array(mask, dtype=np.float32)
        # Binarise: any positive pixel → 1
        mask_arr = (mask_arr > 0).astype(np.float32)
        mask_t = torch.from_numpy(mask_arr).unsqueeze(0)  # [1, H, W]

        return image_t, mask_t


def get_segmentation_transforms(
    phase: Literal["train", "val", "test"],
    image_size: int = 256,
) -> "SegmentationTransform":
    """Return a SegmentationTransform for the given phase."""
    return SegmentationTransform(phase=phase, image_size=image_size)
