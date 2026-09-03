"""
test_preprocessing.py — Tests for transforms and Dataset classes.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
from PIL import Image


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_rgb_image(h=224, w=224) -> Image.Image:
    arr = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def _make_gray_image(h=256, w=256) -> Image.Image:
    arr = np.random.randint(0, 255, (h, w), dtype=np.uint8)
    return Image.fromarray(arr, mode="L")


def _make_binary_mask(h=256, w=256) -> Image.Image:
    arr = np.zeros((h, w), dtype=np.uint8)
    arr[64:128, 64:128] = 255
    return Image.fromarray(arr, mode="L")


# ── Classification Transforms ─────────────────────────────────────────────────

class TestClassificationTransforms:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

    def test_train_transform_output_shape(self):
        from preprocessing.classification_transforms import get_classification_transforms
        tf = get_classification_transforms("train", 224)
        img = _make_rgb_image()
        t = tf(img)
        assert t.shape == (3, 224, 224)

    def test_val_transform_output_shape(self):
        from preprocessing.classification_transforms import get_classification_transforms
        tf = get_classification_transforms("val", 224)
        img = _make_rgb_image()
        t = tf(img)
        assert t.shape == (3, 224, 224)

    def test_test_transform_is_deterministic(self):
        from preprocessing.classification_transforms import get_classification_transforms
        tf = get_classification_transforms("test", 224)
        img = _make_rgb_image()
        t1 = tf(img)
        t2 = tf(img)
        assert torch.allclose(t1, t2)

    def test_normalization_applied(self):
        from preprocessing.classification_transforms import get_classification_transforms
        tf = get_classification_transforms("val", 224)
        img = _make_rgb_image()
        t = tf(img)
        # After ImageNet normalisation, values should be outside [0, 1]
        assert t.min() < 0 or t.max() > 1

    def test_output_is_float_tensor(self):
        from preprocessing.classification_transforms import get_classification_transforms
        tf = get_classification_transforms("val", 224)
        t = tf(_make_rgb_image())
        assert t.dtype == torch.float32


# ── Segmentation Transforms ───────────────────────────────────────────────────

class TestSegmentationTransforms:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

    def test_output_shapes(self):
        from preprocessing.segmentation_transforms import get_segmentation_transforms
        tf = get_segmentation_transforms("val", 256)
        img_t, mask_t = tf(_make_gray_image(), _make_binary_mask())
        assert img_t.shape == (1, 256, 256)
        assert mask_t.shape == (1, 256, 256)

    def test_mask_is_binary(self):
        from preprocessing.segmentation_transforms import get_segmentation_transforms
        tf = get_segmentation_transforms("val", 256)
        _, mask_t = tf(_make_gray_image(), _make_binary_mask())
        unique_vals = mask_t.unique().tolist()
        for v in unique_vals:
            assert v in (0.0, 1.0), f"Non-binary value in mask: {v}"

    def test_image_range(self):
        from preprocessing.segmentation_transforms import get_segmentation_transforms
        tf = get_segmentation_transforms("val", 256)
        img_t, _ = tf(_make_gray_image(), _make_binary_mask())
        assert img_t.min() >= 0.0
        assert img_t.max() <= 1.0

    def test_val_transform_is_deterministic(self):
        from preprocessing.segmentation_transforms import get_segmentation_transforms
        tf = get_segmentation_transforms("val", 256)
        img = _make_gray_image()
        mask = _make_binary_mask()
        i1, m1 = tf(img, mask)
        i2, m2 = tf(img, mask)
        assert torch.allclose(i1, i2)
        assert torch.allclose(m1, m2)

    def test_image_and_mask_same_spatial_size(self):
        from preprocessing.segmentation_transforms import get_segmentation_transforms
        tf = get_segmentation_transforms("train", 256)
        img_t, mask_t = tf(_make_gray_image(), _make_binary_mask())
        assert img_t.shape[1:] == mask_t.shape[1:]


# ── CTKidneyDataset & KSSD2025Dataset ────────────────────────────────────────

class TestCTKidneyDataset:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        self.tmpdir = Path(tempfile.mkdtemp())
        # Create minimal split CSV
        rows = []
        for cls, cls_id in [("Normal", 0), ("Stone", 2)]:
            for i in range(5):
                img_path = self.tmpdir / f"{cls}_{i}.jpg"
                _make_rgb_image().save(img_path)
                rows.append({"image_path": str(img_path), "class_name": cls, "class_id": cls_id})
        self.csv = self.tmpdir / "train.csv"
        pd.DataFrame(rows).to_csv(self.csv, index=False)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_len(self):
        from preprocessing.ct_kidney_dataset import CTKidneyDataset
        ds = CTKidneyDataset(self.csv)
        assert len(ds) == 10

    def test_getitem_returns_correct_types(self):
        from preprocessing.classification_transforms import get_classification_transforms
        from preprocessing.ct_kidney_dataset import CTKidneyDataset
        tf = get_classification_transforms("val")
        ds = CTKidneyDataset(self.csv, transform=tf)
        img_t, label = ds[0]
        assert isinstance(img_t, torch.Tensor)
        assert img_t.shape == (3, 224, 224)
        assert isinstance(label, int)

    def test_smoke_subset(self):
        from preprocessing.ct_kidney_dataset import CTKidneyDataset
        ds = CTKidneyDataset(self.csv, smoke=True, smoke_n=2)
        assert len(ds) == 4  # 2 classes × 2 samples

    def test_class_weights_shape(self):
        from preprocessing.ct_kidney_dataset import CTKidneyDataset
        ds = CTKidneyDataset(self.csv)
        w = ds.get_class_weights()
        assert w.shape[0] == 4  # NUM_CLASSES


class TestKSSD2025Dataset:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        self.tmpdir = Path(tempfile.mkdtemp())
        rows = []
        for i in range(8):
            img_path = self.tmpdir / f"img_{i}.tif"
            msk_path = self.tmpdir / f"msk_{i}.tif"
            _make_gray_image(128, 128).save(img_path)
            _make_binary_mask(128, 128).save(msk_path)
            rows.append({"image_path": str(img_path), "mask_path": str(msk_path)})
        self.csv = self.tmpdir / "train.csv"
        pd.DataFrame(rows).to_csv(self.csv, index=False)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_len(self):
        from preprocessing.kssd2025_dataset import KSSD2025Dataset
        ds = KSSD2025Dataset(self.csv)
        assert len(ds) == 8

    def test_getitem_shapes(self):
        from preprocessing.kssd2025_dataset import KSSD2025Dataset
        from preprocessing.segmentation_transforms import get_segmentation_transforms
        tf = get_segmentation_transforms("val", 256)
        ds = KSSD2025Dataset(self.csv, transform=tf)
        img_t, mask_t = ds[0]
        assert img_t.shape == (1, 256, 256)
        assert mask_t.shape == (1, 256, 256)

    def test_mask_is_binary(self):
        from preprocessing.kssd2025_dataset import KSSD2025Dataset
        from preprocessing.segmentation_transforms import get_segmentation_transforms
        tf = get_segmentation_transforms("val", 256)
        ds = KSSD2025Dataset(self.csv, transform=tf)
        _, mask_t = ds[0]
        for v in mask_t.unique().tolist():
            assert v in (0.0, 1.0)
