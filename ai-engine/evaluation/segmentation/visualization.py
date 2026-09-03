"""
visualization.py — Segmentation visualization utilities.

Produces per-sample PNG files:
  A. Original CT image (grayscale)
  B. Ground-truth mask overlay
  C. Predicted mask overlay
  D. Side-by-side comparison: Original | GT | Pred | Error map (TP/FP/FN)

Error map color coding (configurable via COLORS dict):
  TP — green  (correctly detected stone)
  FP — red    (false alarm — predicted but no stone)
  FN — blue   (missed stone — present but not predicted)

All colors are centrally configured in COLORS. Never hardcoded elsewhere.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

# ── Centralised color configuration ──────────────────────────────────────────
# All visualization colors live here. Override by passing custom `colors` dict.
COLORS: Dict[str, Tuple[int, int, int]] = {
    "overlay_stone":  (255, 165,   0),   # orange — prediction overlay on CT
    "ground_truth":   (  0, 255,   0),   # green  — GT overlay on CT
    "true_positive":  (  0, 255,   0),   # green
    "false_positive": (255,   0,   0),   # red
    "false_negative": (  0,   0, 255),   # blue
    "bounding_box":   (255, 255,   0),   # yellow
    "text_bg":        (  0,   0,   0),   # black (label background)
    "text_fg":        (255, 255, 255),   # white
}

OVERLAY_ALPHA = 0.40   # transparency for mask overlays (0=invisible, 1=opaque)


# ── Core helpers ──────────────────────────────────────────────────────────────

def _to_rgb_pil(arr: np.ndarray) -> Image.Image:
    """Convert [H, W] float [0,1] or uint8 to RGB PIL Image."""
    if arr.dtype != np.uint8:
        arr = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    if arr.ndim == 2:
        return Image.fromarray(arr, mode="L").convert("RGB")
    return Image.fromarray(arr).convert("RGB")


def _overlay(
    base_rgb: Image.Image,
    mask_bin: np.ndarray,
    color: Tuple[int, int, int],
    alpha: float = OVERLAY_ALPHA,
) -> Image.Image:
    """
    Blend a binary mask over a base RGB image with semi-transparency.

    mask_bin : [H, W] float or uint8   positive pixels → overlay applied
    """
    overlay = Image.new("RGB", base_rgb.size, color)
    mask_pil = Image.fromarray((mask_bin > 0).astype(np.uint8) * 255, mode="L")
    result = Image.composite(overlay, base_rgb, mask_pil.point(lambda x: int(x * alpha)))
    return result


def _draw_bboxes(
    img: Image.Image,
    regions: List[Dict],
    color: Tuple[int, int, int] = COLORS["bounding_box"],
    width: int = 2,
) -> Image.Image:
    """Draw bounding boxes from region measurements onto image."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    for r in regions:
        bbox = r.get("bbox")
        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
    return img


# ── Error map ─────────────────────────────────────────────────────────────────

def make_error_map(
    pred_bin: np.ndarray,
    gt_bin: np.ndarray,
    colors: Optional[Dict] = None,
) -> Image.Image:
    """
    Create a TP/FP/FN error map.

    TP (green)  — both pred and GT positive
    FP (red)    — pred positive, GT negative
    FN (blue)   — pred negative, GT positive
    Background  — black
    """
    c = colors or COLORS
    H, W = pred_bin.shape
    error_rgb = np.zeros((H, W, 3), dtype=np.uint8)

    tp_mask = (pred_bin > 0) & (gt_bin > 0)
    fp_mask = (pred_bin > 0) & (gt_bin == 0)
    fn_mask = (pred_bin == 0) & (gt_bin > 0)

    error_rgb[tp_mask] = c["true_positive"]
    error_rgb[fp_mask] = c["false_positive"]
    error_rgb[fn_mask] = c["false_negative"]

    return Image.fromarray(error_rgb, mode="RGB")


# ── Per-sample visualization ──────────────────────────────────────────────────

def visualize_sample(
    image_arr: np.ndarray,
    gt_mask: np.ndarray,
    pred_mask: np.ndarray,
    stem: str,
    output_dir: Path,
    regions: Optional[List[Dict]] = None,
    metrics: Optional[Dict] = None,
    colors: Optional[Dict] = None,
    threshold: float = 0.5,
    save_comparison: bool = True,
    save_overlays: bool = True,
) -> Dict[str, str]:
    """
    Generate and save all visualizations for one sample.

    Parameters
    ----------
    image_arr  : [H, W] float [0,1] or uint8 grayscale
    gt_mask    : [H, W] binary {0,1} or {0,255}
    pred_mask  : [H, W] probability [0,1]
    stem       : filename stem (used for output filenames)
    output_dir : directory to write outputs
    regions    : list of region dicts from measurement.py
    metrics    : dict of metric scalars to embed in comparison title
    colors     : color override dict (uses COLORS by default)

    Returns
    -------
    dict of {label: saved_filepath}
    """
    c = colors or COLORS
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Normalise arrays
    img_arr = np.squeeze(image_arr)
    if img_arr.max() <= 1.0:
        img_arr = (img_arr * 255).astype(np.uint8)
    else:
        img_arr = img_arr.astype(np.uint8)

    gt_bin  = (np.squeeze(gt_mask) > 0).astype(np.uint8)
    pred_bin = (np.squeeze(pred_mask) > threshold).astype(np.uint8)

    base_rgb = _to_rgb_pil(img_arr)
    saved: Dict[str, str] = {}

    # A. Original CT
    orig_path = output_dir / f"{stem}_original.png"
    base_rgb.save(orig_path)
    saved["original"] = str(orig_path)

    # B. Ground truth mask overlay
    gt_overlay = _overlay(base_rgb, gt_bin, c["ground_truth"])
    if regions:
        gt_overlay = _draw_bboxes(gt_overlay, regions, c["bounding_box"])
    gt_path = output_dir / f"{stem}_ground_truth.png"
    gt_overlay.save(gt_path)
    saved["ground_truth"] = str(gt_path)

    # C. Predicted mask overlay
    pred_overlay = _overlay(base_rgb, pred_bin, c["overlay_stone"])
    if regions:
        pred_overlay = _draw_bboxes(pred_overlay, regions, c["bounding_box"])
    pred_path = output_dir / f"{stem}_prediction.png"
    pred_overlay.save(pred_path)
    saved["prediction"] = str(pred_path)

    # D. Error map
    error_map = make_error_map(pred_bin, gt_bin, c)
    error_path = output_dir / f"{stem}_error_map.png"
    error_map.save(error_path)
    saved["error_map"] = str(error_path)

    # E. Side-by-side comparison
    if save_comparison:
        panel_w, panel_h = base_rgb.size
        n_panels = 4
        comp = Image.new("RGB", (panel_w * n_panels, panel_h + 24), (20, 20, 20))

        # Draw panels
        comp.paste(base_rgb,    (0,          24))
        comp.paste(gt_overlay,  (panel_w,    24))
        comp.paste(pred_overlay,(panel_w*2,  24))
        comp.paste(error_map,   (panel_w*3,  24))

        # Labels
        draw = ImageDraw.Draw(comp)
        labels = ["Original CT", "Ground Truth", "Prediction", "TP/FP/FN"]
        for i, label in enumerate(labels):
            draw.text((i * panel_w + 4, 4), label, fill=c["text_fg"])

        # Metrics subtitle
        if metrics:
            m_text = (
                f"Dice={metrics.get('dice', 0):.3f}  "
                f"IoU={metrics.get('iou', 0):.3f}  "
                f"Prec={metrics.get('precision', 0):.3f}  "
                f"Rec={metrics.get('recall', 0):.3f}"
            )
            draw.text((4, panel_h + 8), m_text, fill=(200, 200, 200))

        comp_path = output_dir / f"{stem}_comparison.png"
        comp.save(comp_path)
        saved["comparison"] = str(comp_path)

    return saved


# ── Best / worst directory routing ────────────────────────────────────────────

def save_categorised(
    stem: str,
    saved_paths: Dict[str, str],
    category: str,
    base_vis_dir: Path,
) -> None:
    """
    Copy comparison image to categorised subdirectory (best/worst/fp/fn).
    Uses symlink-free copy to avoid platform issues.
    """
    import shutil
    cat_dir = base_vis_dir / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    comp = saved_paths.get("comparison")
    if comp and Path(comp).exists():
        dest = cat_dir / Path(comp).name
        if not dest.exists():
            shutil.copy2(comp, dest)
