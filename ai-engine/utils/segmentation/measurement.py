"""
measurement.py — Stone region measurement layer.

Extracts per-region geometric properties from predicted binary masks.
All measurements are in pixels.

DO NOT report millimeters — pixel spacing is not available for KSSD2025.
DO NOT claim clinical severity — this is an experimental research heuristic.

Output format:
{
    "detected": bool,
    "num_regions": int,
    "largest_region": {
        "area_pixels": int,
        "bbox": [x1, y1, x2, y2],
        "centroid": [cx, cy],
        "width_pixels": int,
        "height_pixels": int,
        "perimeter": float
    },
    "all_regions": [...],
    "severity": null  (or dict if enabled via config)
}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))

from utils.segmentation.morphology import extract_components


def measure_mask(
    pred_bin: np.ndarray,
    measurement_cfg: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Measure stone regions from a binary predicted mask.

    Parameters
    ----------
    pred_bin        : [H, W] binary {0, 1}
    measurement_cfg : optional config dict (from segmentation_config.yaml)
                      Keys: min_region_area_pixels, severity.enabled, ...

    Returns
    -------
    dict  — structured measurement result (JSON serializable)
    """
    cfg = measurement_cfg or {}
    min_area = int(cfg.get("min_region_area_pixels", 10))

    regions = extract_components(pred_bin, min_area=min_area)
    detected = len(regions) > 0

    result: Dict[str, Any] = {
        "detected":    detected,
        "num_regions": len(regions),
        "largest_region": regions[0] if regions else None,
        "all_regions": regions,
        "NOTE": (
            "All measurements are in pixels. "
            "Pixel spacing is not available for KSSD2025. "
            "Do NOT interpret sizes in millimeters."
        ),
        "severity": None,
    }

    # ── Experimental severity heuristic (disabled by default) ─────────────────
    severity_cfg = cfg.get("severity", {})
    if severity_cfg.get("enabled", False) and regions:
        largest = regions[0]
        result["severity"] = _estimate_severity(largest, severity_cfg)
    else:
        result["severity"] = {
            "enabled": False,
            "disclaimer": (
                "Severity estimation is disabled. "
                "Enable only when reliable pixel spacing (mm/pixel) is available. "
                "This is an experimental engineering heuristic — NOT a clinical diagnosis."
            ),
        }

    return result


def measure_batch(
    pred_bins: List[np.ndarray],
    stems: Optional[List[str]] = None,
    measurement_cfg: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """Measure a list of masks. Returns a list of measurement dicts."""
    stems = stems or [str(i) for i in range(len(pred_bins))]
    results = []
    for i, pred in enumerate(pred_bins):
        m = measure_mask(pred, measurement_cfg)
        m["stem"] = stems[i]
        results.append(m)
    return results


# ── Severity heuristic (internal — only called when explicitly enabled) ───────

def _estimate_severity(region: Dict, severity_cfg: Dict) -> Dict:
    """
    Experimental severity estimation from pixel dimensions.

    ONLY used when pixel_spacing_mm is explicitly provided in config.
    """
    px_spacing = severity_cfg.get("pixel_spacing_mm")
    disclaimer = (
        "EXPERIMENTAL HEURISTIC ONLY. NOT FOR CLINICAL USE. "
        "Severity categories are approximate and have not been validated "
        "against any clinical reference standard."
    )

    if not px_spacing:
        return {
            "enabled": True,
            "level": "unknown",
            "reason": "pixel_spacing_mm not configured — cannot convert to mm",
            "disclaimer": disclaimer,
        }

    area_mm2 = region["area_pixels"] * (px_spacing ** 2)
    max_dim_mm = max(region["width_pixels"], region["height_pixels"]) * px_spacing

    small_max = severity_cfg.get("small_max_mm", 6)
    mod_max   = severity_cfg.get("moderate_max_mm", 10)

    if max_dim_mm <= small_max:
        level = "small"
    elif max_dim_mm <= mod_max:
        level = "moderate"
    else:
        level = "large"

    return {
        "enabled":        True,
        "level":          level,
        "max_dim_mm":     round(max_dim_mm, 2),
        "area_mm2":       round(area_mm2, 2),
        "pixel_spacing":  px_spacing,
        "disclaimer":     disclaimer,
    }
