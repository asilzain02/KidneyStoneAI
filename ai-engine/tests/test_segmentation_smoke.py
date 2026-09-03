"""
test_segmentation_smoke.py — Full segmentation pipeline smoke test.

Verifies all 16 checks without running any full training.

Usage (from project root):
    python ai-engine/tests/test_segmentation_smoke.py

Expected outcome:
    All 16 checks PASS — prints a summary table.
    No .pth weight files are created.
    No model training is performed.
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
import torch

# ── Path bootstrap ────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve()
_ENGINE_ROOT = _HERE.parents[1]       # ai-engine/
_PROJECT_ROOT = _ENGINE_ROOT.parent   # project root
sys.path.insert(0, str(_ENGINE_ROOT))

# ── Test registry ─────────────────────────────────────────────────────────────
_tests: List[Tuple[str, Callable]] = []


def _register(name: str):
    def decorator(fn: Callable):
        _tests.append((name, fn))
        return fn
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS 1-4: Dataset
# ═══════════════════════════════════════════════════════════════════════════════

@_register("1. Dataset inspection runs")
def check_inspector():
    from datasets.segmentation.kssd2025.kssd2025_inspector import inspect
    image_dir = _PROJECT_ROOT / "datasets" / "raw" / "segmentation" / "kssd2025" / "data" / "image"
    label_dir = _PROJECT_ROOT / "datasets" / "raw" / "segmentation" / "kssd2025" / "data" / "label"
    report = inspect(image_dir, label_dir)
    assert report["summary"]["matched_pairs"] > 0, "No matched pairs found"
    assert report["summary"]["total_images"] > 0
    return f"{report['summary']['matched_pairs']} pairs found"


@_register("2. Dataset adapter discovers files")
def check_adapter():
    from datasets.kssd2025_adapter import KSSD2025DatasetAdapter
    image_dir = _PROJECT_ROOT / "datasets" / "raw" / "segmentation" / "kssd2025" / "data" / "image"
    label_dir = _PROJECT_ROOT / "datasets" / "raw" / "segmentation" / "kssd2025" / "data" / "label"
    adapter = KSSD2025DatasetAdapter(image_dir, label_dir)
    adapter.discover()
    pairs = adapter.get_pairs()
    assert len(pairs) > 0
    return f"{len(pairs)} pairs"


@_register("3. Split CSV generation works")
def check_splits():
    from datasets.kssd2025_adapter import KSSD2025DatasetAdapter
    from datasets.split_builder import build_segmentation_splits
    from PIL import Image

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        image_dir = tmp / "data" / "image"
        label_dir = tmp / "data" / "label"
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)

        for i in range(10):
            stem = f"smoke_img_{i:04d}"
            Image.new("L", (64, 64), color=100 + i).save(image_dir / f"{stem}.tif")
            Image.new("L", (64, 64), color=0).save(label_dir / f"{stem}.tif")

        manifest = tmp / "manifest.csv"
        splits_dir = tmp / "splits"

        adapter = KSSD2025DatasetAdapter(image_dir, label_dir)
        adapter.validate(compute_hashes=True)
        adapter.build_manifest(manifest)

        splits = build_segmentation_splits(
            manifest_path=manifest,
            output_dir=splits_dir,
            train_ratio=0.70,
            val_ratio=0.15,
            seed=42,
        )
        assert len(splits["train"]) > 0
        assert len(splits["val"]) > 0
        assert len(splits["test"]) > 0
        return f"train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}"


@_register("4. DataLoader loads one batch")
def check_dataloader():
    from datasets.kssd2025_adapter import KSSD2025DatasetAdapter
    from datasets.split_builder import build_segmentation_splits
    from datasets.segmentation.kssd2025.kssd2025_dataset import KSSD2025Dataset
    from preprocessing.segmentation_transforms import get_segmentation_transforms
    from torch.utils.data import DataLoader
    from PIL import Image

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        image_dir = tmp / "data" / "image"
        label_dir = tmp / "data" / "label"
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)

        for i in range(10):
            stem = f"smoke_img_{i:04d}"
            Image.new("L", (64, 64), color=100 + i).save(image_dir / f"{stem}.tif")
            Image.new("L", (64, 64), color=255).save(label_dir / f"{stem}.tif")

        manifest = tmp / "manifest.csv"
        splits_dir = tmp / "splits"

        adapter = KSSD2025DatasetAdapter(image_dir, label_dir)
        adapter.validate(compute_hashes=True)
        adapter.build_manifest(manifest)
        build_segmentation_splits(manifest, splits_dir, seed=42)

        transform = get_segmentation_transforms("train", 256)
        ds = KSSD2025Dataset(splits_dir / "train.csv", transform=transform, smoke=True, smoke_n=8)
        loader = DataLoader(ds, batch_size=4, shuffle=True, num_workers=0)
        imgs, masks = next(iter(loader))

        assert imgs.shape == (4, 1, 256, 256), f"Unexpected image shape {imgs.shape}"
        assert masks.shape == (4, 1, 256, 256), f"Unexpected mask shape {masks.shape}"
        assert imgs.dtype == torch.float32
        assert masks.dtype == torch.float32
        assert 0.0 <= imgs.min() and imgs.max() <= 1.0
        assert set(masks.unique().tolist()).issubset({0.0, 1.0})

        stem = ds.get_stem(0)
        assert isinstance(stem, str) and len(stem) > 0

        return f"batch shape: {tuple(imgs.shape)}, masks binary: True"


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS 5-7: Model
# ═══════════════════════════════════════════════════════════════════════════════

@_register("5. Model factory initializes UNet")
def check_model_factory():
    from models.segmentation.model_factory import create_segmentation_model, list_models
    cfg = {"model": {"name": "unet", "in_channels": 1, "out_channels": 1, "base_features": 32}}
    model = create_segmentation_model(cfg)
    assert model is not None
    models = list_models()
    assert "unet" in models
    n_params = sum(p.numel() for p in model.parameters())
    return f"UNet params: {n_params:,}"


@_register("6. Forward pass correct output shape")
def check_forward_pass():
    from models.segmentation.model_factory import create_segmentation_model
    cfg = {"model": {"name": "unet", "in_channels": 1, "out_channels": 1, "base_features": 32}}
    model = create_segmentation_model(cfg)
    model.eval()
    x = torch.randn(2, 1, 256, 256)
    with torch.no_grad():
        out = model(x)
    assert out.shape == (2, 1, 256, 256), f"Bad output shape: {out.shape}"
    assert out.min() >= 0.0 and out.max() <= 1.0, "Output not in [0,1]"
    return f"Output shape: {tuple(out.shape)}, range [{out.min():.3f}, {out.max():.3f}]"


@_register("7. Loss calculates and backprop works")
def check_loss_backprop():
    from models.segmentation.model_factory import create_segmentation_model
    from training.losses import get_segmentation_loss

    cfg_model = {"model": {"name": "unet", "in_channels": 1, "out_channels": 1, "base_features": 16}}
    cfg_loss  = {"segmentation": {"loss": "dice_bce", "dice_weight": 0.5, "bce_weight": 0.5}}
    model = create_segmentation_model(cfg_model)
    loss_fn = get_segmentation_loss(cfg_loss)

    x = torch.randn(2, 1, 128, 128)
    y = (torch.rand(2, 1, 128, 128) > 0.5).float()

    out = model(x)
    loss = loss_fn(out, y)
    assert torch.isfinite(loss), "Loss is NaN/Inf"

    loss.backward()
    # Check gradients flow
    for p in model.parameters():
        if p.requires_grad and p.grad is not None:
            assert torch.isfinite(p.grad).all()
            break

    return f"Loss = {loss.item():.4f}"


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS 8-10: Checkpoint
# ═══════════════════════════════════════════════════════════════════════════════

@_register("8. Checkpoint save and load")
def check_checkpoint():
    from models.segmentation.model_factory import create_segmentation_model

    cfg = {"model": {"name": "unet", "in_channels": 1, "out_channels": 1, "base_features": 16}}
    model_a = create_segmentation_model(cfg)

    with tempfile.TemporaryDirectory() as td:
        ckpt_path = Path(td) / "test_ckpt.pth"
        state = {
            "epoch": 5,
            "model_state_dict": model_a.state_dict(),
            "optimizer_state_dict": {},
            "best_dice": 0.85,
            "history": {"train_loss": [0.5, 0.4]},
        }
        torch.save(state, ckpt_path)

        # Load into a new model instance
        model_b = create_segmentation_model(cfg)
        ckpt = torch.load(ckpt_path, map_location="cpu")
        model_b.load_state_dict(ckpt["model_state_dict"])
        assert ckpt["epoch"] == 5
        assert ckpt["best_dice"] == 0.85

    return "Save/load OK"


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS 11-13: Evaluation + Visualization
# ═══════════════════════════════════════════════════════════════════════════════

@_register("9. Segmentation metrics compute correctly")
def check_metrics():
    from evaluation.segmentation.segmentation_metrics import compute_sample_metrics

    pred  = np.array([[0.9, 0.1], [0.8, 0.2]])
    gt    = np.array([[1.0, 0.0], [1.0, 0.0]])
    m = compute_sample_metrics(pred, gt, threshold=0.5)

    assert "dice" in m
    assert "iou" in m
    assert "specificity" in m
    assert "pixel_accuracy" in m
    assert 0.0 <= m["dice"] <= 1.0
    return f"dice={m['dice']:.4f}, specificity={m['specificity']:.4f}"


@_register("10. Visualization produces PNG files")
def check_visualization():
    from evaluation.segmentation.visualization import visualize_sample

    H, W = 64, 64
    image  = np.random.rand(H, W).astype(np.float32)
    gt     = (np.random.rand(H, W) > 0.7).astype(np.float32)
    pred   = np.random.rand(H, W).astype(np.float32)

    with tempfile.TemporaryDirectory() as td:
        saved = visualize_sample(
            image_arr=image,
            gt_mask=gt,
            pred_mask=pred,
            stem="smoke_001",
            output_dir=Path(td),
            save_comparison=True,
        )
        assert "comparison" in saved
        assert Path(saved["comparison"]).exists()

    return "PNG files created OK"


@_register("11. Connected component extraction works")
def check_morphology():
    from utils.segmentation.morphology import extract_components

    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[10:20, 10:20] = 1   # region 1
    mask[40:50, 40:50] = 1   # region 2

    regions = extract_components(mask, min_area=10)
    assert len(regions) >= 1
    assert "area_pixels" in regions[0]
    assert "bbox" in regions[0]
    assert "centroid" in regions[0]
    return f"{len(regions)} regions detected"


@_register("12. Measurement layer works")
def check_measurement():
    from utils.segmentation.measurement import measure_mask

    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[20:40, 20:40] = 1

    result = measure_mask(mask)
    assert "detected" in result
    assert result["detected"] is True
    assert result["num_regions"] >= 1
    assert result["largest_region"] is not None
    return f"detected={result['detected']}, regions={result['num_regions']}"


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS 14-16: JSON + CLI imports
# ═══════════════════════════════════════════════════════════════════════════════

@_register("13. JSON serialization works")
def check_json():
    from utils.segmentation.measurement import measure_mask

    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[20:40, 20:40] = 1
    result = measure_mask(mask)

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test.json"
        with open(p, "w") as f:
            json.dump(result, f, default=str)
        with open(p, "r") as f:
            loaded = json.load(f)
        assert loaded["detected"] == result["detected"]

    return "JSON round-trip OK"


@_register("14. Evaluator module imports cleanly")
def check_evaluator_import():
    from evaluation.segmentation.segmentation_evaluator import evaluate  # noqa
    from evaluation.segmentation.visualization import visualize_sample    # noqa
    from evaluation.segmentation.segmentation_metrics import compute_dataset_metrics  # noqa
    return "All evaluator imports OK"


@_register("15. Inference CLI module imports cleanly")
def check_inference_import():
    from inference.segmentation_inference import run_inference, save_outputs  # noqa
    return "Inference imports OK"


@_register("16. Model factory + losses unified")
def check_factory_losses():
    from models.segmentation.model_factory import create_segmentation_model
    from models.segmentation.losses import get_loss

    cfg = {
        "model": {"name": "unet", "in_channels": 1, "out_channels": 1, "base_features": 16},
        "loss":  {"name": "dice_bce", "dice_weight": 0.5, "bce_weight": 0.5},
    }
    model = create_segmentation_model(cfg)
    loss_fn = get_loss(cfg)

    x = torch.randn(2, 1, 64, 64)
    y = (torch.rand(2, 1, 64, 64) > 0.5).float()
    out = model(x)
    loss = loss_fn(out, y)
    assert torch.isfinite(loss)
    return f"Factory + loss OK, loss={loss.item():.4f}"


# ═══════════════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════════════

def run_smoke_tests() -> bool:
    print("\n" + "=" * 70)
    print("KidneyStoneAI — Segmentation Pipeline Smoke Tests")
    print("=" * 70)

    all_passed = True
    results = []

    for name, fn in _tests:
        start = time.time()
        try:
            detail = fn()
            elapsed = time.time() - start
            results.append(("PASS", name, detail or "", elapsed))
        except Exception as e:
            elapsed = time.time() - start
            results.append(("FAIL", name, str(e), elapsed))
            all_passed = False

    # Summary table
    print(f"\n{'Status':<6}  {'Check':<45}  {'Detail'}")
    print("-" * 90)
    for status, name, detail, t in results:
        icon = "[OK]" if status == "PASS" else "[XX]"
        print(f"{icon} {status:<4}  {name:<45}  {detail[:50]}")

    n_pass = sum(1 for s, _, _, _ in results if s == "PASS")
    n_fail = len(results) - n_pass

    print("\n" + "=" * 70)
    print(f"  PASSED: {n_pass}/{len(results)}")
    if n_fail > 0:
        print(f"  FAILED: {n_fail}/{len(results)}")
        print("\n  Failed checks:")
        for s, name, detail, _ in results:
            if s == "FAIL":
                print(f"    - {name}")
                print(f"      {detail}")
    print("=" * 70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
