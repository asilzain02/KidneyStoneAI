"""
kssd2025_adapter.py — Dataset adapter for the KSSD2025 segmentation dataset.

Expected structure (DO NOT modify raw data):
    datasets/raw/segmentation/kssd2025/data/
        image/   *.tif   (CT images, numeric stem names e.g. 1.tif, 10.tif)
        label/   *.tif   (binary masks, matching numeric stems)

Image-to-label correspondence is determined programmatically by
matching file stems (without extension) across both directories.
"""

from __future__ import annotations

import collections
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.image_utils import (
    compute_hash,
    get_image_size,
    is_empty_mask,
    is_valid_image,
    mask_unique_values,
    SUPPORTED_EXTENSIONS,
)
from utils.logger import get_logger

log = get_logger(__name__)


class KSSD2025DatasetAdapter:
    """
    Adapter for the KSSD2025 Kidney Stone Segmentation Dataset.

    Parameters
    ----------
    image_dir : Path-like
        Path to …/kssd2025/data/image/
    label_dir : Path-like
        Path to …/kssd2025/data/label/
    """

    def __init__(self, image_dir: str | Path, label_dir: str | Path):
        self.image_dir = Path(image_dir).resolve()
        self.label_dir = Path(label_dir).resolve()
        self._pairs: List[Dict] = []
        self._validation_report: Dict = {}

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _collect_files(self, directory: Path) -> Dict[str, Path]:
        """Return dict {stem → path} for all image-like files in directory."""
        return {
            p.stem: p
            for p in sorted(directory.iterdir())
            if p.suffix.lower() in SUPPORTED_EXTENSIONS
        }

    # ── Public API ────────────────────────────────────────────────────────────

    def discover(self) -> "KSSD2025DatasetAdapter":
        """
        Match image files to label files by stem.

        Raises RuntimeError if either directory is missing.
        Unmatched files are logged and reported but do NOT raise.
        """
        if not self.image_dir.exists():
            raise FileNotFoundError(f"Image dir not found: {self.image_dir}")
        if not self.label_dir.exists():
            raise FileNotFoundError(f"Label dir not found: {self.label_dir}")

        images = self._collect_files(self.image_dir)
        labels = self._collect_files(self.label_dir)

        log.info(
            "KSSD2025 — discovered",
            images=len(images),
            labels=len(labels),
        )

        matched_stems = sorted(set(images.keys()) & set(labels.keys()))
        unmatched_images = sorted(set(images.keys()) - set(labels.keys()))
        unmatched_labels = sorted(set(labels.keys()) - set(images.keys()))

        if unmatched_images:
            log.warning(
                "KSSD2025 — images without labels",
                count=len(unmatched_images),
                examples=unmatched_images[:5],
            )
        if unmatched_labels:
            log.warning(
                "KSSD2025 — labels without images",
                count=len(unmatched_labels),
                examples=unmatched_labels[:5],
            )

        pairs = []
        for stem in matched_stems:
            pairs.append({
                "image_path": str(images[stem]),
                "mask_path": str(labels[stem]),
                "dataset_name": "kssd2025",
                "stem": stem,
            })

        self._pairs = pairs
        log.info("KSSD2025 — matched pairs", pairs=len(pairs))

        # Surface mismatch info on the object for later reporting
        self._unmatched_images = unmatched_images
        self._unmatched_labels = unmatched_labels
        return self

    def validate(self, compute_hashes: bool = True) -> Dict:
        """
        Validate every matched image-mask pair.

        Returns a detailed validation report.
        """
        if not self._pairs:
            self.discover()

        log.info("KSSD2025 — starting validation …")
        total = len(self._pairs)
        valid_images = 0
        valid_labels = 0
        corrupted_images: List[str] = []
        corrupted_labels: List[str] = []
        empty_masks: List[str] = []
        image_hash_map: Dict[str, List[str]] = collections.defaultdict(list)
        image_dims: Dict[str, int] = collections.defaultdict(int)
        mask_dims: Dict[str, int] = collections.defaultdict(int)
        mask_value_distribution: Dict[str, int] = collections.defaultdict(int)

        validated_pairs = []
        for pair in tqdm(self._pairs, desc="Validating KSSD2025"):
            img_path = pair["image_path"]
            msk_path = pair["mask_path"]

            img_ok = is_valid_image(img_path)
            msk_ok = is_valid_image(msk_path)

            img_size = get_image_size(img_path) if img_ok else None
            msk_size = get_image_size(msk_path) if msk_ok else None
            img_hash = compute_hash(img_path) if (img_ok and compute_hashes) else None
            msk_hash = compute_hash(msk_path) if (msk_ok and compute_hashes) else None
            empty = is_empty_mask(msk_path) if msk_ok else True
            msk_vals = mask_unique_values(msk_path) if msk_ok else []

            if img_ok:
                valid_images += 1
                if img_size:
                    image_dims[f"{img_size[0]}x{img_size[1]}"] += 1
                if img_hash:
                    image_hash_map[img_hash].append(img_path)
            else:
                corrupted_images.append(img_path)

            if msk_ok:
                valid_labels += 1
                if msk_size:
                    mask_dims[f"{msk_size[0]}x{msk_size[1]}"] += 1
                for v in msk_vals:
                    mask_value_distribution[str(v)] += 1
            else:
                corrupted_labels.append(msk_path)

            if empty:
                empty_masks.append(msk_path)

            pair.update({
                "image_hash": img_hash,
                "mask_hash": msk_hash,
                "width": img_size[0] if img_size else None,
                "height": img_size[1] if img_size else None,
                "image_valid": img_ok,
                "mask_valid": msk_ok,
                "mask_empty": empty,
                "mask_values": str(msk_vals),
            })
            validated_pairs.append(pair)

        duplicate_image_groups = {
            h: paths for h, paths in image_hash_map.items() if len(paths) > 1
        }

        self._pairs = validated_pairs
        self._validation_report = {
            "total_pairs": total,
            "valid_images": valid_images,
            "valid_labels": valid_labels,
            "corrupted_images": corrupted_images,
            "corrupted_labels": corrupted_labels,
            "empty_masks": len(empty_masks),
            "empty_mask_files": empty_masks,
            "duplicate_image_groups": len(duplicate_image_groups),
            "image_dimension_distribution": dict(image_dims),
            "mask_dimension_distribution": dict(mask_dims),
            "mask_pixel_value_distribution": dict(mask_value_distribution),
            "unmatched_images": getattr(self, "_unmatched_images", []),
            "unmatched_labels": getattr(self, "_unmatched_labels", []),
            "leakage_note": (
                "Patient-level identifiers are not available in KSSD2025 filenames. "
                "Patient-level leakage prevention cannot be guaranteed. "
                "Duplicate-hash detection has been applied as a best-effort measure."
            ),
        }

        log.info("KSSD2025 — validation complete", **{
            k: v for k, v in self._validation_report.items()
            if isinstance(v, (int, str))
        })
        return self._validation_report

    def build_manifest(self, output_path: str | Path) -> pd.DataFrame:
        """Write a CSV manifest with columns for each image-mask pair."""
        if not self._pairs:
            self.validate()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(
            [p for p in self._pairs if p.get("image_valid") and p.get("mask_valid")]
        )
        cols = ["image_path", "mask_path", "dataset_name",
                "image_hash", "mask_hash", "width", "height"]
        df = df[[c for c in cols if c in df.columns]]
        df.to_csv(output_path, index=False)
        log.info("KSSD2025 — manifest written", path=str(output_path), rows=len(df))
        return df

    def get_statistics(self) -> Dict:
        if not self._validation_report:
            self.validate()
        return self._validation_report

    def get_pairs(self) -> List[Dict]:
        if not self._pairs:
            self.discover()
        return self._pairs
