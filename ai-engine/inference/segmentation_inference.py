"""
segmentation_inference.py — Standalone inference CLI for kidney stone segmentation.

Works independently from training — no training code imported.

Usage:
    python ai-engine/inference/segmentation_inference.py \\
        --image path/to/ct.tif \\
        --checkpoint ai-engine/weights/segmentation/segmentation_baseline/best_model.pth

    python ai-engine/inference/segmentation_inference.py \\
        --image path/to/ct.tif \\
        --checkpoint path/to/best_model.pth \\
        --threshold 0.5 \\
        --output-dir outputs/inference \\
        --device cpu

Output (per image):
    <output_dir>/
    ├── <stem>_mask.png          ← binary predicted mask
    ├── <stem>_overlay.png       ← mask overlaid on original CT
    └── <stem>_result.json       ← structured JSON result

JSON result format:
{
    "image": "path/to/ct.tif",
    "stone_detected": true,
    "num_regions": 2,
    "regions": [...],
    "segmentation": {
        "dice": null,        <- null when no ground truth
        "iou": null,
        "precision": null,
        "recall": null
    }
}
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
from PIL import Image

# ── Path bootstrap ────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve()
_ENGINE_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

from config.settings import get_training_cfg
from models.unet.unet import build_unet
from preprocessing.segmentation_transforms import get_segmentation_transforms
from utils.logger import get_logger
from utils.segmentation.mask_utils import binarize, overlay_mask_on_image
from utils.segmentation.measurement import measure_mask

log = get_logger(__name__)


# ── Model loader ──────────────────────────────────────────────────────────────

def _load_model(
    checkpoint_path: Path,
    cfg: Dict,
    device: torch.device,
) -> torch.nn.Module:
    model = build_unet(cfg)
    ckpt = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()
    log.info("Model loaded", checkpoint=str(checkpoint_path))
    return model


# ── Single image inference ────────────────────────────────────────────────────

@torch.no_grad()
def run_inference(
    image_path: Path,
    model: torch.nn.Module,
    transform,
    device: torch.device,
    threshold: float = 0.5,
    measurement_cfg: Optional[Dict] = None,
    gt_mask_path: Optional[Path] = None,
) -> Dict:
    """
    Run inference on a single image.

    Parameters
    ----------
    image_path      : path to input CT image
    model           : loaded PyTorch model
    transform       : segmentation transform (test phase)
    device          : torch device
    threshold       : binarization threshold
    measurement_cfg : measurement config dict
    gt_mask_path    : optional — if provided, computes segmentation metrics

    Returns
    -------
    Structured result dict (JSON serializable).
    """
    # Load image
    image_pil = Image.open(image_path)
    orig_w, orig_h = image_pil.size

    # Create dummy mask for transform (test mode)
    dummy_mask = Image.new("L", image_pil.size, 0)
    image_t, _ = transform(image_pil, dummy_mask)
    image_t = image_t.unsqueeze(0).to(device)   # [1, 1, H, W]

    # Forward pass
    prob = model(image_t)[0, 0].cpu().numpy()   # [H, W] — transform size
    pred_bin = binarize(prob, threshold)

    # Measurements on transform-sized mask
    meas = measure_mask(pred_bin, measurement_cfg)

    # Resize probability map back to original image size for overlay
    from PIL import Image as PILImage
    prob_orig = np.array(
        PILImage.fromarray((prob * 255).astype(np.uint8)).resize(
            (orig_w, orig_h), PILImage.BILINEAR
        ), dtype=np.float32
    ) / 255.0
    pred_bin_orig = binarize(prob_orig, threshold)

    # Segmentation metrics (only if GT provided)
    seg_metrics: Dict = {
        "dice": None, "iou": None, "precision": None, "recall": None
    }
    if gt_mask_path and gt_mask_path.exists():
        from evaluation.segmentation.segmentation_metrics import compute_sample_metrics
        gt_arr = (np.array(Image.open(gt_mask_path).convert("L")) > 0).astype(np.float32)
        seg_metrics = compute_sample_metrics(prob_orig, gt_arr, threshold)

    result = {
        "image":          str(image_path),
        "timestamp":      datetime.now().isoformat(),
        "original_size":  [orig_w, orig_h],
        "threshold":      threshold,
        "stone_detected": meas["detected"],
        "num_regions":    meas["num_regions"],
        "regions":        meas["all_regions"],
        "measurement_note": meas.get("NOTE", ""),
        "segmentation":   seg_metrics,
        "severity":       meas.get("severity"),
    }

    return result, prob_orig, pred_bin_orig


# ── Saving outputs ────────────────────────────────────────────────────────────

def save_outputs(
    image_path: Path,
    result: Dict,
    prob_orig: np.ndarray,
    pred_bin_orig: np.ndarray,
    output_dir: Path,
    regions: List[Dict],
) -> None:
    """Save mask PNG, overlay PNG, and result JSON."""
    stem = image_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load original for overlay
    orig_arr = np.array(Image.open(image_path).convert("L"), dtype=np.float32) / 255.0

    # Binary mask PNG
    mask_pil = Image.fromarray(pred_bin_orig * 255, mode="L")
    mask_path = output_dir / f"{stem}_mask.png"
    mask_pil.save(mask_path)

    # Overlay PNG
    overlay_arr = overlay_mask_on_image(orig_arr, pred_bin_orig)
    from evaluation.segmentation.visualization import _draw_bboxes
    overlay_pil = Image.fromarray(overlay_arr, mode="RGB")
    if regions:
        overlay_pil = _draw_bboxes(overlay_pil, regions)
    overlay_pil.save(output_dir / f"{stem}_overlay.png")

    # JSON result
    json_path = output_dir / f"{stem}_result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nOutputs saved:")
    print(f"  Mask    → {mask_path}")
    print(f"  Overlay → {output_dir / f'{stem}_overlay.png'}")
    print(f"  JSON    → {json_path}")
    print(f"\nStone detected: {result['stone_detected']}")
    print(f"Regions found : {result['num_regions']}")
    if result["regions"]:
        lr = result["regions"][0]
        print(f"Largest region:")
        print(f"  Area     = {lr['area_pixels']} px²")
        print(f"  Size     = {lr['width_pixels']} × {lr['height_pixels']} px")
        print(f"  Centroid = {lr['centroid']}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Standalone segmentation inference — KidneyStoneAI"
    )
    p.add_argument("--image",      type=str, required=True, help="Input CT image path.")
    p.add_argument("--checkpoint", type=str, required=True, help="Path to best_model.pth.")
    p.add_argument("--threshold",  type=float, default=0.5)
    p.add_argument("--device",     type=str, default=None, help="cpu | cuda")
    p.add_argument("--output-dir", type=str, default="outputs/segmentation/inference")
    p.add_argument(
        "--mask", type=str, default=None,
        help="Optional ground-truth mask path (enables metric computation).",
    )
    return p.parse_args()


def main():
    args = parse_args()
    cfg = get_training_cfg()

    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    image_size = cfg["segmentation"]["input_size"]
    transform = get_segmentation_transforms("test", image_size)

    model = _load_model(Path(args.checkpoint), cfg, device)

    result, prob_orig, pred_bin_orig = run_inference(
        image_path=Path(args.image),
        model=model,
        transform=transform,
        device=device,
        threshold=args.threshold,
        gt_mask_path=Path(args.mask) if args.mask else None,
    )

    save_outputs(
        image_path=Path(args.image),
        result=result,
        prob_orig=prob_orig,
        pred_bin_orig=pred_bin_orig,
        output_dir=Path(args.output_dir),
        regions=result.get("regions", []),
    )


if __name__ == "__main__":
    main()
