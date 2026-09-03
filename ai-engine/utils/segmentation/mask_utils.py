"""
mask_utils.py — Binary mask format helpers.

Provides:
  - binarize(arr, threshold) → np.uint8 [H, W]
  - to_pil_mask(arr)         → PIL.Image (mode="L")
  - from_pil_mask(pil)       → np.uint8 [H, W]
  - resize_mask(arr, size)   → np.uint8 [H, W]  (nearest-neighbor)
  - overlay_mask_on_image    → np.uint8 [H, W, 3]
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from PIL import Image


def binarize(
    arr: np.ndarray,
    threshold: float = 0.5,
) -> np.ndarray:
    """
    Binarize a probability map or grayscale mask.

    Returns
    -------
    np.ndarray  dtype=uint8  values in {0, 1}
    """
    arr = np.squeeze(np.asarray(arr, dtype=np.float32))
    return (arr > threshold).astype(np.uint8)


def to_pil_mask(arr: np.ndarray, scale_255: bool = True) -> Image.Image:
    """
    Convert a binary [H, W] uint8 array to a PIL grayscale image.

    Parameters
    ----------
    scale_255 : if True, multiplies by 255 (so mask is {0, 255})
    """
    arr = np.squeeze(arr).astype(np.uint8)
    if scale_255:
        arr = arr * 255
    return Image.fromarray(arr, mode="L")


def from_pil_mask(pil: Image.Image, threshold: int = 128) -> np.ndarray:
    """
    Convert a PIL grayscale image to a binary [H, W] uint8 array.

    Pixels >= threshold are set to 1, else 0.
    """
    arr = np.array(pil.convert("L"), dtype=np.uint8)
    return (arr >= threshold).astype(np.uint8)


def resize_mask(arr: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """
    Resize a binary mask using nearest-neighbor interpolation.

    Parameters
    ----------
    arr  : [H, W] binary uint8
    size : (width, height) target size

    Returns
    -------
    np.ndarray  [size[1], size[0]]  dtype=uint8
    """
    pil = to_pil_mask(arr, scale_255=True)
    pil = pil.resize(size, resample=Image.NEAREST)
    return from_pil_mask(pil)


def overlay_mask_on_image(
    image_arr: np.ndarray,
    mask_arr: np.ndarray,
    color: Tuple[int, int, int] = (255, 165, 0),
    alpha: float = 0.4,
) -> np.ndarray:
    """
    Blend a binary mask over a grayscale [H, W] image.

    Parameters
    ----------
    image_arr : [H, W] float [0,1] or uint8 grayscale
    mask_arr  : [H, W] binary {0,1}
    color     : RGB tuple for mask region
    alpha     : float [0,1] opacity of the overlay

    Returns
    -------
    np.ndarray  [H, W, 3]  uint8 RGB composite
    """
    img = np.squeeze(image_arr)
    if img.max() <= 1.0:
        img = (img * 255).astype(np.uint8)
    else:
        img = img.astype(np.uint8)

    # Expand to RGB
    rgb = np.stack([img, img, img], axis=-1)

    mask = (np.squeeze(mask_arr) > 0)
    overlay = np.array(color, dtype=np.uint8)

    # Blend
    blended = rgb.copy().astype(np.float32)
    blended[mask] = (1 - alpha) * rgb[mask].astype(np.float32) + alpha * overlay

    return np.clip(blended, 0, 255).astype(np.uint8)
