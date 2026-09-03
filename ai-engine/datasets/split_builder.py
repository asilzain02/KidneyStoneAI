"""
split_builder.py — Creates reproducible train/val/test splits.

Classification: stratified by class.
Segmentation:   paired (image+mask always stay together).

Output CSVs go to:
    datasets/splits/classification/{train,val,test}.csv
    datasets/splits/segmentation/{train,val,test}.csv
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

log = get_logger(__name__)


def _split_df(
    df: pd.DataFrame,
    train_ratio: float,
    val_ratio: float,
    seed: int,
    stratify_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split df into train / val / test DataFrames."""
    test_ratio = 1.0 - train_ratio - val_ratio
    assert test_ratio > 0, "train_ratio + val_ratio must be < 1.0"

    stratify = df[stratify_col].values if stratify_col else None

    df_train, df_tmp = train_test_split(
        df,
        test_size=(val_ratio + test_ratio),
        random_state=seed,
        stratify=stratify,
    )

    # Recompute stratify for the remaining rows
    stratify_tmp = df_tmp[stratify_col].values if stratify_col else None
    relative_test_ratio = test_ratio / (val_ratio + test_ratio)

    df_val, df_test = train_test_split(
        df_tmp,
        test_size=relative_test_ratio,
        random_state=seed,
        stratify=stratify_tmp,
    )

    return df_train, df_val, df_test


def build_classification_splits(
    manifest_path: str | Path,
    output_dir: str | Path,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42,
    exclude_invalid: bool = True,
) -> Dict[str, pd.DataFrame]:
    """
    Create stratified classification splits from a manifest CSV.

    Returns: {"train": df, "val": df, "test": df}
    """
    df = pd.read_csv(manifest_path)
    if exclude_invalid and "valid" in df.columns:
        df = df[df["valid"] == True].copy()

    # Remove duplicate hashes across the whole dataset before splitting
    if "image_hash" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset="image_hash", keep="first")
        removed = before - len(df)
        if removed:
            log.warning("Classification — removed duplicate-hash rows", removed=removed)

    train, val, test = _split_df(
        df, train_ratio, val_ratio, seed, stratify_col="class_name"
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _verify_no_overlap(train, val, test, id_col="image_path")

    train.to_csv(output_dir / "train.csv", index=False)
    val.to_csv(output_dir / "val.csv", index=False)
    test.to_csv(output_dir / "test.csv", index=False)

    log.info(
        "Classification splits saved",
        output_dir=str(output_dir),
        train=len(train), val=len(val), test=len(test),
    )
    return {"train": train, "val": val, "test": test}


def build_segmentation_splits(
    manifest_path: str | Path,
    output_dir: str | Path,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42,
    exclude_invalid: bool = True,
) -> Dict[str, pd.DataFrame]:
    """
    Create paired segmentation splits from a manifest CSV.
    Image-mask pairs are NEVER split across different sets.

    Returns: {"train": df, "val": df, "test": df}
    """
    df = pd.read_csv(manifest_path)
    if exclude_invalid:
        for col in ("image_valid", "mask_valid"):
            if col in df.columns:
                df = df[df[col] == True].copy()

    # Deduplicate by image hash
    if "image_hash" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset="image_hash", keep="first")
        removed = before - len(df)
        if removed:
            log.warning("Segmentation — removed duplicate-hash pairs", removed=removed)

    train, val, test = _split_df(
        df, train_ratio, val_ratio, seed, stratify_col=None
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _verify_no_overlap(train, val, test, id_col="image_path")

    train.to_csv(output_dir / "train.csv", index=False)
    val.to_csv(output_dir / "val.csv", index=False)
    test.to_csv(output_dir / "test.csv", index=False)

    log.info(
        "Segmentation splits saved",
        output_dir=str(output_dir),
        train=len(train), val=len(val), test=len(test),
    )
    return {"train": train, "val": val, "test": test}


def _verify_no_overlap(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    id_col: str = "image_path",
) -> None:
    """Assert no image appears in more than one split."""
    train_ids = set(train[id_col])
    val_ids = set(val[id_col])
    test_ids = set(test[id_col])

    tv = train_ids & val_ids
    tt = train_ids & test_ids
    vt = val_ids & test_ids

    if tv or tt or vt:
        raise RuntimeError(
            f"Data leakage detected! "
            f"train∩val={len(tv)}, train∩test={len(tt)}, val∩test={len(vt)}"
        )
    log.info("Split overlap check passed — no data leakage detected.")
