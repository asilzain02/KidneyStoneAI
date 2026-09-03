"""
test_dataset_adapters.py — Tests for CT Kidney and KSSD2025 adapters.

Uses synthetic temporary directories so no real dataset is required
for the unit tests to pass. Integration tests hit the real dataset
paths and are marked with @pytest.mark.integration.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_fake_clf_dataset(root: Path, classes=("Normal", "Cyst", "Stone", "Tumor"), n=5):
    """Create n synthetic jpg images per class."""
    for cls in classes:
        cls_dir = root / cls
        cls_dir.mkdir(parents=True)
        for i in range(1, n + 1):
            img = Image.fromarray(
                np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
            )
            img.save(cls_dir / f"{cls}- ({i}).jpg")
    return root


def _make_fake_seg_dataset(image_dir: Path, label_dir: Path, n=10):
    """Create n synthetic tif image+label pairs with numeric stems."""
    image_dir.mkdir(parents=True)
    label_dir.mkdir(parents=True)
    for i in range(1, n + 1):
        img = Image.fromarray(
            np.random.randint(0, 255, (128, 128), dtype=np.uint8), mode="L"
        )
        # label — binary mask (some positive pixels)
        mask_arr = np.zeros((128, 128), dtype=np.uint8)
        mask_arr[32:64, 32:64] = 255
        mask = Image.fromarray(mask_arr, mode="L")
        img.save(image_dir / f"{i}.tif")
        mask.save(label_dir / f"{i}.tif")
    return image_dir, label_dir


# ── CT Kidney Adapter ─────────────────────────────────────────────────────────

class TestCTKidneyDatasetAdapter:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

        self.tmpdir = Path(tempfile.mkdtemp())
        _make_fake_clf_dataset(self.tmpdir)

        from datasets.ct_kidney_adapter import CTKidneyDatasetAdapter
        self.adapter = CTKidneyDatasetAdapter(self.tmpdir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_discover_finds_all_classes(self):
        self.adapter.discover()
        names = {r["class_name"] for r in self.adapter.get_records()}
        assert {"Normal", "Cyst", "Stone", "Tumor"}.issubset(names)

    def test_discover_total_count(self):
        self.adapter.discover()
        assert len(self.adapter.get_records()) == 20  # 4 classes × 5 images

    def test_class_ids_are_valid(self):
        self.adapter.discover()
        for rec in self.adapter.get_records():
            assert rec["class_id"] in (0, 1, 2, 3)

    def test_validate_marks_valid_images(self):
        report = self.adapter.validate(compute_hashes=False)
        assert report["valid"] == 20
        assert report["invalid"] == 0
        assert len(report["corrupted_files"]) == 0

    def test_validate_class_distribution(self):
        report = self.adapter.validate(compute_hashes=False)
        dist = report["class_distribution"]
        assert all(dist[c] == 5 for c in ["Normal", "Cyst", "Stone", "Tumor"])

    def test_validate_detects_corrupted_file(self):
        # Write a corrupted file
        cls_dir = self.tmpdir / "Normal"
        bad = cls_dir / "Normal- (999).jpg"
        bad.write_bytes(b"not an image")
        self.adapter.discover()
        report = self.adapter.validate(compute_hashes=False)
        assert report["invalid"] >= 1
        assert str(bad) in report["corrupted_files"]

    def test_validate_detects_duplicates(self):
        # Copy one file as another name
        import shutil as sh
        src = self.tmpdir / "Stone" / "Stone- (1).jpg"
        dst = self.tmpdir / "Stone" / "Stone- (99).jpg"
        sh.copy2(src, dst)
        self.adapter.discover()
        report = self.adapter.validate(compute_hashes=True)
        assert report["duplicate_groups"] >= 1

    def test_build_manifest_creates_csv(self):
        import pandas as pd
        manifest = self.tmpdir / "manifest.csv"
        self.adapter.validate(compute_hashes=False)
        df = self.adapter.build_manifest(manifest)
        assert manifest.exists()
        assert len(df) == 20
        assert "image_path" in df.columns
        assert "class_name" in df.columns
        assert "class_id" in df.columns


# ── KSSD2025 Adapter ──────────────────────────────────────────────────────────

class TestKSSD2025DatasetAdapter:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

        self.tmpdir = Path(tempfile.mkdtemp())
        self.image_dir = self.tmpdir / "image"
        self.label_dir = self.tmpdir / "label"
        _make_fake_seg_dataset(self.image_dir, self.label_dir, n=10)

        from datasets.kssd2025_adapter import KSSD2025DatasetAdapter
        self.adapter = KSSD2025DatasetAdapter(self.image_dir, self.label_dir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_discover_matches_all_pairs(self):
        self.adapter.discover()
        assert len(self.adapter.get_pairs()) == 10

    def test_discover_no_unmatched(self):
        self.adapter.discover()
        assert self.adapter._unmatched_images == []
        assert self.adapter._unmatched_labels == []

    def test_discover_detects_unmatched_image(self):
        # Add an image with no matching label
        extra = self.image_dir / "999.tif"
        Image.fromarray(np.zeros((64, 64), dtype=np.uint8), mode="L").save(extra)
        self.adapter.discover()
        assert "999" in self.adapter._unmatched_images

    def test_validate_valid_pairs(self):
        report = self.adapter.validate(compute_hashes=False)
        assert report["valid_images"] == 10
        assert report["valid_labels"] == 10
        assert len(report["corrupted_images"]) == 0

    def test_validate_detects_empty_mask(self):
        # Create a pair where mask is all zeros
        Image.fromarray(np.zeros((128, 128), dtype=np.uint8), mode="L").save(
            self.label_dir / "500.tif"
        )
        Image.fromarray(np.zeros((128, 128), dtype=np.uint8), mode="L").save(
            self.image_dir / "500.tif"
        )
        self.adapter.discover()
        report = self.adapter.validate(compute_hashes=False)
        empty_files = report["empty_mask_files"]
        assert any("500.tif" in f for f in empty_files)

    def test_validate_detects_corrupted_image(self):
        bad = self.image_dir / "bad.tif"
        bad.write_bytes(b"corrupt")
        # Need a matching label
        Image.fromarray(np.zeros((64, 64), dtype=np.uint8), mode="L").save(
            self.label_dir / "bad.tif"
        )
        self.adapter.discover()
        report = self.adapter.validate(compute_hashes=False)
        assert len(report["corrupted_images"]) >= 1

    def test_build_manifest_creates_csv(self):
        import pandas as pd
        manifest = self.tmpdir / "seg_manifest.csv"
        self.adapter.validate(compute_hashes=False)
        df = self.adapter.build_manifest(manifest)
        assert manifest.exists()
        assert len(df) == 10
        assert "image_path" in df.columns
        assert "mask_path" in df.columns

    def test_leakage_note_present(self):
        report = self.adapter.validate(compute_hashes=False)
        assert "leakage_note" in report
        assert "Patient-level" in report["leakage_note"]
