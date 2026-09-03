"""
leakage_checker.py — Hash-based duplicate / cross-split leakage detection.
"""

from __future__ import annotations

import collections
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

log = get_logger(__name__)


def find_cross_dataset_duplicates(
    clf_manifest: str | Path,
    seg_manifest: str | Path,
) -> Dict:
    """
    Compare classification and segmentation manifests for identical images
    (same hash). Reports potential cross-dataset leakage.

    NOTE: Patient-level leakage cannot be checked if no patient ID exists.
    """
    clf_df = pd.read_csv(clf_manifest)
    seg_df = pd.read_csv(seg_manifest)

    clf_hashes: Set[str] = set(clf_df["image_hash"].dropna().tolist())
    seg_hashes: Set[str] = set(seg_df["image_hash"].dropna().tolist())

    common = clf_hashes & seg_hashes
    report = {
        "clf_unique_hashes": len(clf_hashes),
        "seg_unique_hashes": len(seg_hashes),
        "common_hashes": len(common),
        "common_hash_values": list(common),
        "leakage_risk": len(common) > 0,
        "note": (
            "Common hashes indicate the same image file appears in both datasets. "
            "These should be excluded from evaluation boundaries. "
            "Patient-level leakage cannot be determined without patient IDs."
        ),
    }
    if common:
        log.warning(
            "Cross-dataset hash overlap detected",
            common_hashes=len(common),
        )
    else:
        log.info("No cross-dataset hash overlap detected.")

    return report


def check_intra_split_duplicates(split_dir: str | Path, id_col: str = "image_path") -> Dict:
    """
    Verify no duplicate image appears within a split directory
    (train.csv, val.csv, test.csv).
    """
    split_dir = Path(split_dir)
    results = {}
    for csv_file in ["train.csv", "val.csv", "test.csv"]:
        p = split_dir / csv_file
        if not p.exists():
            continue
        df = pd.read_csv(p)
        dupes = df[id_col].duplicated().sum()
        results[csv_file] = int(dupes)
        if dupes:
            log.warning(f"{csv_file}: {dupes} duplicate rows found.")

    return results
