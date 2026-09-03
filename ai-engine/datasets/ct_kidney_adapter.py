"""
ct_kidney_adapter.py — Dataset adapter for the CT Kidney Dataset.

Discovers, validates, and builds manifests/splits for the
four-class kidney CT classification dataset.

Expected structure (DO NOT modify raw data):
    datasets/raw/classification/ct-kidney/
        Cyst/      Cyst- (N).jpg
        Normal/    Normal- (N).jpg
        Stone/     Stone- (N).jpg
        Tumor/     Tumor- (N).jpg
"""

from __future__ import annotations

import collections
import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from tqdm import tqdm

# Add project root so we can import utils from anywhere
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.image_utils import (
    compute_hash,
    get_image_size,
    is_valid_image,
    SUPPORTED_EXTENSIONS,
)
from utils.logger import get_logger

log = get_logger(__name__)

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]
CLASS_TO_ID = {c: i for i, c in enumerate(CLASS_NAMES)}


class CTKidneyDatasetAdapter:
    """
    Adapter for the CT Kidney Dataset.

    Parameters
    ----------
    root_dir : Path-like
        Path to the ct-kidney folder containing class sub-directories.
    """

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir).resolve()
        self._records: List[Dict] = []
        self._validation_report: Dict = {}

    # ── Public API ───────────────────────────────────────────────────────────

    def discover(self) -> "CTKidneyDatasetAdapter":
        """Scan all class directories and collect image paths."""
        if not self.root_dir.exists():
            raise FileNotFoundError(f"Dataset root not found: {self.root_dir}")

        found_classes = sorted([p.name for p in self.root_dir.iterdir() if p.is_dir()])
        log.info("CT Kidney — discovered class folders", classes=found_classes)

        records = []
        for class_name in found_classes:
            class_dir = self.root_dir / class_name
            images = sorted(
                p for p in class_dir.iterdir()
                if p.suffix.lower() in SUPPORTED_EXTENSIONS
            )
            log.info(f"  {class_name}: {len(images)} files")
            for img_path in images:
                records.append({
                    "image_path": str(img_path),
                    "class_name": class_name,
                    "class_id": CLASS_TO_ID.get(class_name, -1),
                    "dataset_name": "ct-kidney",
                })

        self._records = records
        log.info("CT Kidney — total discovered", total=len(records))
        return self

    def validate(self, compute_hashes: bool = True) -> Dict:
        """
        Validate every discovered image.

        Returns a report dict with:
            total, valid, invalid, corrupted, duplicates,
            class_distribution, dimension_stats
        """
        if not self._records:
            self.discover()

        log.info("CT Kidney — starting validation …")
        total = len(self._records)
        valid_count = 0
        invalid_count = 0
        corrupted: List[str] = []
        hash_map: Dict[str, List[str]] = collections.defaultdict(list)
        dimensions: Dict[str, int] = collections.defaultdict(int)
        class_dist: Dict[str, int] = collections.defaultdict(int)

        validated_records = []
        for rec in tqdm(self._records, desc="Validating CT Kidney"):
            path = rec["image_path"]
            ok = is_valid_image(path)
            size = get_image_size(path) if ok else None
            h = compute_hash(path) if (ok and compute_hashes) else None

            if ok:
                valid_count += 1
                dim_key = f"{size[0]}x{size[1]}" if size else "unknown"
                dimensions[dim_key] += 1
                class_dist[rec["class_name"]] += 1
                if h:
                    hash_map[h].append(path)
                rec.update({
                    "image_hash": h,
                    "width": size[0] if size else None,
                    "height": size[1] if size else None,
                    "valid": True,
                })
            else:
                invalid_count += 1
                corrupted.append(path)
                rec.update({
                    "image_hash": None,
                    "width": None,
                    "height": None,
                    "valid": False,
                })
            validated_records.append(rec)

        # Detect duplicates (same hash, different paths)
        duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}

        self._records = validated_records
        self._validation_report = {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "corrupted_files": corrupted,
            "duplicate_groups": len(duplicates),
            "duplicate_files": sum(len(v) for v in duplicates.values()),
            "duplicates": duplicates,
            "class_distribution": dict(class_dist),
            "dimension_distribution": dict(dimensions),
        }

        log.info("CT Kidney — validation complete", **{
            k: v for k, v in self._validation_report.items()
            if k not in ("corrupted_files", "duplicates")
        })
        return self._validation_report

    def build_manifest(self, output_path: str | Path) -> pd.DataFrame:
        """
        Write a CSV manifest of all valid images.

        Columns: image_path, class_name, class_id, dataset_name,
                 image_hash, width, height
        """
        if not self._records:
            self.validate()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(
            [r for r in self._records if r.get("valid", False)]
        )
        df = df[["image_path", "class_name", "class_id",
                 "dataset_name", "image_hash", "width", "height"]]
        df.to_csv(output_path, index=False)
        log.info("CT Kidney — manifest written", path=str(output_path), rows=len(df))
        return df

    def get_statistics(self) -> Dict:
        """Return the cached validation report (runs validate() if needed)."""
        if not self._validation_report:
            self.validate()
        return self._validation_report

    def get_records(self) -> List[Dict]:
        """Return all records (validated if already validated, else raw)."""
        if not self._records:
            self.discover()
        return self._records
