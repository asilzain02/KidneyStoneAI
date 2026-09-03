"""
image_utils.py — Image loading, validation, and hashing helpers.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def load_image(path: Path | str, mode: str = "RGB") -> Optional[Image.Image]:
    """Load an image from disk. Returns None if the file is corrupted."""
    try:
        img = Image.open(path)
        img.verify()          # checks integrity
        img = Image.open(path).convert(mode)
        return img
    except Exception:
        return None


def get_image_size(path: Path | str) -> Optional[Tuple[int, int]]:
    """Return (width, height) or None if unreadable."""
    try:
        with Image.open(path) as img:
            return img.size  # (width, height)
    except Exception:
        return None


def compute_hash(path: Path | str, algorithm: str = "md5") -> Optional[str]:
    """Compute a file hash for duplicate detection. Returns None on error."""
    h = hashlib.new(algorithm)
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def is_valid_image(path: Path | str) -> bool:
    """Return True if the file can be opened and decoded as an image."""
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def is_empty_mask(path: Path | str) -> bool:
    """Return True if a mask image has no positive (>0) pixels."""
    try:
        with Image.open(path) as img:
            arr = np.array(img)
        return arr.max() == 0
    except Exception:
        return True  # treat unreadable masks as empty


def mask_unique_values(path: Path | str) -> list:
    """Return sorted unique pixel values in a mask image."""
    try:
        with Image.open(path) as img:
            arr = np.array(img)
        return sorted(set(arr.flatten().tolist()))
    except Exception:
        return []
