"""
mask_processor.py — Segmentation mask postprocessing.

Supports:
  - Probability thresholding
  - Binary mask generation
  - Optional connected-component cleanup (keep N largest)
  - Mask statistics (area in pixels, bounding box, component count)

NOTE: Physical stone size in mm is NOT calculated here because
valid pixel-spacing DICOM metadata is not available in this dataset.
Do NOT fabricate medical measurements.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
from PIL import Image

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


class MaskProcessor:
    """
    Postprocessing pipeline for a binary segmentation mask.

    Parameters
    ----------
    threshold       : float in [0, 1] — probability cutoff
    min_component_size : int — connected components smaller than this (pixels) are removed
    keep_n_largest  : int — if > 0, keep only top-N largest components (requires cv2)
    """

    def __init__(
        self,
        threshold: float = 0.5,
        min_component_size: int = 50,
        keep_n_largest: int = 0,
    ):
        self.threshold = threshold
        self.min_component_size = min_component_size
        self.keep_n_largest = keep_n_largest

    def binarize(self, prob_mask: np.ndarray) -> np.ndarray:
        """Threshold probability map → binary uint8 {0, 1}."""
        return (prob_mask > self.threshold).astype(np.uint8)

    def clean_components(self, binary_mask: np.ndarray) -> np.ndarray:
        """
        Remove small connected components and optionally keep only top-N.
        Requires OpenCV. Falls back to raw mask if cv2 not available.
        """
        if not _CV2_AVAILABLE:
            return binary_mask

        n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            binary_mask, connectivity=8
        )

        # stats columns: x, y, w, h, area
        # label 0 is background
        component_areas = [(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, n_labels)]
        component_areas.sort(key=lambda x: x[1], reverse=True)

        if self.keep_n_largest > 0:
            keep = {lbl for lbl, area in component_areas[: self.keep_n_largest]
                    if area >= self.min_component_size}
        else:
            keep = {lbl for lbl, area in component_areas
                    if area >= self.min_component_size}

        clean = np.zeros_like(binary_mask)
        for lbl in keep:
            clean[labels == lbl] = 1
        return clean

    def get_statistics(self, binary_mask: np.ndarray) -> Dict:
        """
        Compute mask statistics.

        Returns dict with:
            stone_area_pixels   : positive pixel count
            total_pixels        : total pixels
            coverage_ratio      : stone_area / total
            num_components      : number of connected components (requires cv2)
            bounding_box        : (x, y, w, h) or None
        """
        stone_pixels = int(binary_mask.sum())
        total_pixels = int(binary_mask.size)
        coverage = stone_pixels / total_pixels if total_pixels > 0 else 0.0

        num_components = None
        bbox = None
        if _CV2_AVAILABLE and stone_pixels > 0:
            n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
                binary_mask.astype(np.uint8), connectivity=8
            )
            num_components = n_labels - 1  # exclude background
            if num_components > 0:
                # Bounding box of all stone pixels
                rows = np.any(binary_mask, axis=1)
                cols = np.any(binary_mask, axis=0)
                rmin, rmax = np.where(rows)[0][[0, -1]]
                cmin, cmax = np.where(cols)[0][[0, -1]]
                bbox = (int(cmin), int(rmin), int(cmax - cmin), int(rmax - rmin))

        return {
            "stone_area_pixels": stone_pixels,
            "total_pixels": total_pixels,
            "coverage_ratio": float(coverage),
            "num_components": num_components,
            "bounding_box": bbox,
            "pixel_spacing_mm_note": (
                "Physical stone size cannot be computed: "
                "pixel spacing (DICOM metadata) is not available."
            ),
        }

    def process(self, prob_mask: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Full pipeline: threshold → clean → statistics.

        Returns (binary_mask uint8, statistics dict)
        """
        binary = self.binarize(prob_mask)
        cleaned = self.clean_components(binary)
        stats = self.get_statistics(cleaned)
        return cleaned, stats

    def to_pil(self, binary_mask: np.ndarray) -> Image.Image:
        """Convert binary uint8 {0,1} mask to PIL Image (mode='L')."""
        return Image.fromarray((binary_mask * 255).astype(np.uint8), mode="L")
