"""
segmentation_evaluator.py — CLI evaluator for trained segmentation models.

Usage:
    python ai-engine/evaluation/segmentation/segmentation_evaluator.py \\
        --checkpoint ai-engine/weights/segmentation/segmentation_baseline/best_model.pth

    python ai-engine/evaluation/segmentation/segmentation_evaluator.py \\
        --checkpoint ... \\
        --num-samples 20 \\
        --split test \\
        --device cpu

    python ai-engine/evaluation/segmentation/segmentation_evaluator.py \\
        --checkpoint ... \\
        --all

Output directories:
    outputs/segmentation/evaluation/
    ├── segmentation_results.json
    ├── predictions/          ← saved binary mask PNGs
    ├── overlays/             ← overlay PNGs
    ├── comparisons/          ← side-by-side comparison PNGs
    └── measurements.json
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
from torch.utils.data import DataLoader
from tqdm import tqdm

# ── Path bootstrap ────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve()
_ENGINE_ROOT = _HERE.parents[2]
_PROJECT_ROOT = _ENGINE_ROOT.parent
sys.path.insert(0, str(_ENGINE_ROOT))

from config.settings import get_training_cfg, get_paths_cfg
from datasets.segmentation.kssd2025.kssd2025_dataset import KSSD2025Dataset
from evaluation.segmentation.segmentation_metrics import (
    compute_sample_metrics,
    compute_dataset_metrics,
    select_best_worst,
)
from evaluation.segmentation.visualization import (
    visualize_sample,
    save_categorised,
)
from models.unet.unet import build_unet
from preprocessing.segmentation_transforms import get_segmentation_transforms
from utils.logger import get_logger
from utils.segmentation.mask_utils import binarize
from utils.segmentation.measurement import measure_mask, measure_batch

log = get_logger(__name__)


# ── Checkpoint loader ─────────────────────────────────────────────────────────

def _load_model(checkpoint_path: Path, cfg: Dict, device: torch.device) -> torch.nn.Module:
    model = build_unet(cfg)
    ckpt = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()
    log.info("Checkpoint loaded", path=str(checkpoint_path), device=str(device))
    return model


# ── Main evaluation logic ─────────────────────────────────────────────────────

def evaluate(
    checkpoint_path: Path,
    cfg: Dict,
    paths: Dict,
    split: str = "test",
    num_samples: Optional[int] = 20,
    device_str: Optional[str] = None,
    threshold: float = 0.5,
    output_dir: Optional[Path] = None,
) -> Dict:
    """
    Run full evaluation on test split.

    Returns
    -------
    dict — full evaluation results (JSON serializable)
    """
    device = torch.device(device_str or ("cuda" if torch.cuda.is_available() else "cpu"))
    model = _load_model(checkpoint_path, cfg, device)

    #seg_cfg = cfg["segmentation"]
    seg_cfg = cfg.get("segmentation", cfg)
    splits_dir = paths["splits"]["segmentation_dir"]
    split_csv = Path(splits_dir) / f"{split}.csv"

    if not split_csv.exists():
        raise FileNotFoundError(
            f"Split CSV not found: {split_csv}\n"
            "Run train_segmentation.py once to generate splits."
        )

    transform = get_segmentation_transforms("test", seg_cfg["input_size"])
    dataset = KSSD2025Dataset(split_csv, transform=transform)
    log.info("Evaluation dataset loaded", split=split, samples=len(dataset))

    # Output directories
    if output_dir is None:
        output_dir = _PROJECT_ROOT / "outputs" / "segmentation" / "evaluation"
    output_dir = Path(output_dir)
    pred_dir   = output_dir / "predictions"
    vis_dir    = output_dir / "visualizations"
    for d in [output_dir, pred_dir, vis_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Determine which indices to visualize
    n_total = len(dataset)
    if num_samples is None:
        vis_indices = set(range(n_total))   # --all
    else:
        vis_indices = set(range(min(num_samples, n_total)))

    # ── Inference loop ────────────────────────────────────────────────────────
    all_preds:   List[np.ndarray] = []
    all_targets: List[np.ndarray] = []
    all_stems:   List[str]        = []
    all_metrics_per_sample: List[Dict] = []
    measurements: List[Dict] = []

    log.info("Running inference …", device=str(device))

    dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)

    with torch.no_grad():
        for idx, (image_t, mask_t) in enumerate(tqdm(dataloader, desc="Evaluating")):
            image_t = image_t.to(device)
            prob = model(image_t)[0, 0].cpu().numpy()      # [H, W]
            gt   = mask_t[0, 0].numpy()                    # [H, W]
            stem = dataset.get_stem(idx)

            all_preds.append(prob)
            all_targets.append(gt)
            all_stems.append(stem)

            # Per-sample metrics
            m = compute_sample_metrics(prob, gt, threshold=threshold)
            m["stem"] = stem
            all_metrics_per_sample.append(m)

            # Save predicted mask PNG
            pred_bin = binarize(prob, threshold)
            mask_img = Image.fromarray(pred_bin * 255, mode="L")
            mask_img.save(pred_dir / f"{stem}_mask.png")

            # Measurements
            meas = measure_mask(pred_bin)
            meas["stem"] = stem
            measurements.append(meas)

            # Visualization (for selected indices)
            if idx in vis_indices:
                # Load original image for visualization (un-transformed)
                raw_img = np.array(
                    Image.open(dataset.get_image_path(idx)).convert("L"),
                    dtype=np.float32
                ) / 255.0
                raw_gt = np.array(
                    Image.open(dataset.get_mask_path(idx)).convert("L"),
                    dtype=np.float32
                )
                raw_gt = (raw_gt > 0).astype(np.float32)

                # Resize pred to original image size for accurate visualization
                from PIL import Image as PILImage
                orig_h, orig_w = raw_img.shape
                prob_resized = np.array(
                    PILImage.fromarray((prob * 255).astype(np.uint8)).resize(
                        (orig_w, orig_h), PILImage.BILINEAR
                    ), dtype=np.float32
                ) / 255.0

                saved = visualize_sample(
                    image_arr=raw_img,
                    gt_mask=raw_gt,
                    pred_mask=prob_resized,
                    stem=stem,
                    output_dir=vis_dir,
                    regions=meas.get("all_regions", []),
                    metrics=m,
                    threshold=threshold,
                )

    # ── Aggregate metrics ─────────────────────────────────────────────────────
    scalar_metrics = compute_dataset_metrics(all_preds, all_targets, threshold)
    scalar_metrics.pop("per_sample", None)  # keep results clean

    # ── Best / worst categorisation ───────────────────────────────────────────
    categories = select_best_worst(all_metrics_per_sample, all_stems, n=5)
    for cat_name, stems_list in categories.items():
        for stem in stems_list:
            idx = all_stems.index(stem) if stem in all_stems else -1
            if idx >= 0:
                # Re-use already-saved comparison image
                comp_path = vis_dir / f"{stem}_comparison.png"
                if comp_path.exists():
                    save_categorised(
                        stem=stem,
                        saved_paths={"comparison": str(comp_path)},
                        category=cat_name,
                        base_vis_dir=vis_dir,
                    )

    # ── Save results ──────────────────────────────────────────────────────────
    results = {
        "checkpoint":       str(checkpoint_path),
        "split":            split,
        "num_samples":      n_total,
        "threshold":        threshold,
        "timestamp":        datetime.now().isoformat(),
        "aggregate_metrics": scalar_metrics,
        "per_sample_metrics": all_metrics_per_sample,
        "best_worst":       categories,
    }

    results_path = output_dir / "segmentation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    log.info("Results saved", path=str(results_path))

    meas_path = output_dir / "measurements.json"
    with open(meas_path, "w", encoding="utf-8") as f:
        json.dump(measurements, f, indent=2, default=str)
    log.info("Measurements saved", path=str(meas_path))

    # Console summary
    print("\n" + "=" * 60)
    print("Segmentation Evaluation Results")
    print("=" * 60)
    for k, v in scalar_metrics.items():
        if k.startswith("mean_"):
            metric = k[5:]
            std_k = f"std_{metric}"
            std_v = scalar_metrics.get(std_k, 0)
            print(f"  {metric:<20}: {v:.4f}  ± {std_v:.4f}")
    print(f"\n  Output dir: {output_dir}")
    print("=" * 60 + "\n")

    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Evaluate a trained segmentation model on KSSD2025."
    )
    p.add_argument(
        "--checkpoint", type=str, required=True,
        help="Path to best_model.pth checkpoint.",
    )
    p.add_argument(
        "--split", type=str, default="test",
        choices=["train", "val", "test"],
        help="Which split to evaluate on. Default: test",
    )
    p.add_argument(
        "--num-samples", type=int, default=20,
        help="Number of samples to visualize (default 20).",
    )
    p.add_argument(
        "--all", action="store_true",
        help="Visualize ALL test samples (overrides --num-samples).",
    )
    p.add_argument(
        "--threshold", type=float, default=0.5,
        help="Binarization threshold (default 0.5).",
    )
    p.add_argument(
        "--device", type=str, default=None,
        help="cpu | cuda | cuda:0 (default: auto-detect).",
    )
    p.add_argument(
        "--output-dir", type=str, default=None,
        help="Custom output directory.",
    )
    return p.parse_args()


def main():
    args = parse_args()
    cfg = get_training_cfg()
    paths = get_paths_cfg()

    num_samples = None if args.all else args.num_samples

    evaluate(
        checkpoint_path=Path(args.checkpoint),
        cfg=cfg,
        paths=paths,
        split=args.split,
        num_samples=num_samples,
        device_str=args.device,
        threshold=args.threshold,
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )


if __name__ == "__main__":
    main()
