"""
morphology.py — Connected component analysis for predicted segmentation masks.

Provides:
  - extract_components(mask_bin, min_area)  → List[Dict]
  - Each component dict contains:
      label        : int
      area_pixels  : int
      bbox         : [x1, y1, x2, y2]  (column-major: x=col, y=row)
      centroid     : [cx, cy]
      width_pixels : int
      height_pixels: int
      perimeter    : float  (optional, requires scipy)

IMPORTANT: pixel spacing is NOT available for KSSD2025.
All measurements are in pixels. Do NOT claim mm measurements.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np


def extract_components(
    mask_bin: np.ndarray,
    min_area: int = 10,
) -> List[Dict]:
    """
    Extract connected components from a binary mask.

    Uses scipy.ndimage for labelling (more robust than cv2 for CI environments).
    Falls back to a simple numpy implementation if scipy is unavailable.

    Parameters
    ----------
    mask_bin : [H, W] binary uint8 {0, 1}
    min_area : ignore components smaller than this (pixels)

    Returns
    -------
    List of region dicts, sorted by area descending.
    """
    mask = (np.squeeze(mask_bin) > 0).astype(np.uint8)

    try:
        from scipy.ndimage import label
        labeled, n_labels = label(mask)
        return _regions_from_labeled(labeled, n_labels, min_area)
    except ImportError:
        # Fallback: basic bounding-box approach (no per-component separation)
        return _fallback_single_region(mask, min_area)


def _regions_from_labeled(
    labeled: np.ndarray,
    n_labels: int,
    min_area: int,
) -> List[Dict]:
    regions = []
    for lbl in range(1, n_labels + 1):
        component = (labeled == lbl)
        area = int(component.sum())
        if area < min_area:
            continue

        rows = np.where(component.any(axis=1))[0]
        cols = np.where(component.any(axis=0))[0]

        if len(rows) == 0 or len(cols) == 0:
            continue

        r_min, r_max = int(rows.min()), int(rows.max())
        c_min, c_max = int(cols.min()), int(cols.max())

        # Centroid
        ys, xs = np.where(component)
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))

        w = c_max - c_min + 1
        h = r_max - r_min + 1

        regions.append({
            "label":          lbl,
            "area_pixels":    area,
            "bbox":           [c_min, r_min, c_max, r_max],  # [x1, y1, x2, y2]
            "centroid":       [round(cx, 2), round(cy, 2)],
            "width_pixels":   w,
            "height_pixels":  h,
            "perimeter":      _perimeter(component),
        })

    return sorted(regions, key=lambda r: r["area_pixels"], reverse=True)


def _perimeter(component: np.ndarray) -> float:
    """Estimate perimeter by counting boundary pixels."""
    try:
        from scipy.ndimage import binary_erosion
        interior = binary_erosion(component)
        boundary = component & ~interior
        return float(boundary.sum())
    except Exception:
        return -1.0


def _fallback_single_region(mask: np.ndarray, min_area: int) -> List[Dict]:
    """Return a single bounding box if the mask is non-empty (no scipy)."""
    area = int(mask.sum())
    if area < min_area:
        return []

    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]

    if len(rows) == 0:
        return []

    r_min, r_max = int(rows.min()), int(rows.max())
    c_min, c_max = int(cols.min()), int(cols.max())

    ys, xs = np.where(mask)

    return [{
        "label":          1,
        "area_pixels":    area,
        "bbox":           [c_min, r_min, c_max, r_max],
        "centroid":       [round(float(np.mean(xs)), 2), round(float(np.mean(ys)), 2)],
        "width_pixels":   c_max - c_min + 1,
        "height_pixels":  r_max - r_min + 1,
        "perimeter":      -1.0,  # not computed in fallback
    }]
