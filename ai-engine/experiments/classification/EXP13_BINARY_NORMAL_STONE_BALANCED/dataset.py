"""
dataset.py — EXP13 Binary Normal-vs-Stone Dataset

Reads from the EXISTING project split CSVs (train.csv / val.csv / test.csv).
Filters to keep ONLY Normal and Stone rows.

Does NOT copy or modify any image files.
Does NOT modify the existing split CSV files.

Labels:
    Normal -> 0
    Stone  -> 1
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset

# ── Constants ─────────────────────────────────────────────────────────────────
EXP13_CLASS_NAMES: List[str] = ["Normal", "Stone"]
EXP13_CLASS_TO_IDX: Dict[str, int] = {"Normal": 0, "Stone": 1}
ALLOWED_CLASSES = frozenset(EXP13_CLASS_NAMES)


class BinaryNormalStoneDataset(Dataset):
    """
    PyTorch Dataset for EXP13 binary classification.

    Reads an existing split CSV and keeps only Normal / Stone rows.
    Maps Normal->0, Stone->1.
    Does NOT copy images or modify any project file.

    Parameters
    ----------
    csv_path   : path to existing train.csv / val.csv / test.csv
    transform  : torchvision Compose transform
    smoke      : if True, use only first smoke_n samples per class
    smoke_n    : samples per class for smoke test
    """

    def __init__(
        self,
        csv_path: str | Path,
        transform: Optional[Callable] = None,
        smoke: bool = False,
        smoke_n: int = 30,
    ):
        self.transform = transform
        self.class_names = EXP13_CLASS_NAMES
        self.class_to_idx = EXP13_CLASS_TO_IDX

        df = pd.read_csv(csv_path)

        # Filter: keep only Normal and Stone
        df = df[df["class_name"].isin(ALLOWED_CLASSES)].reset_index(drop=True)

        if smoke:
            df = (
                df.groupby("class_name", group_keys=False)
                .apply(lambda g: g.head(smoke_n))
                .reset_index(drop=True)
            )

        self.image_paths: List[str] = df["image_path"].tolist()
        self.labels: List[int] = [
            EXP13_CLASS_TO_IDX[c] for c in df["class_name"].tolist()
        ]

        # Class counts for reporting
        self._normal_count = int((df["class_name"] == "Normal").sum())
        self._stone_count  = int((df["class_name"] == "Stone").sum())

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img = Image.open(self.image_paths[idx]).convert("RGB")
        label = self.labels[idx]
        if self.transform:
            img = self.transform(img)
        return img, label

    @property
    def normal_count(self) -> int:
        return self._normal_count

    @property
    def stone_count(self) -> int:
        return self._stone_count

    def get_labels(self) -> List[int]:
        """Return full label list (used by sampler)."""
        return self.labels

    def save_manifest(self, output_path: str | Path) -> None:
        """
        Save a record of all image paths and labels used in this dataset.
        Does NOT copy images — only records paths.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["path", "class_name", "class_id"])
            for path, label in zip(self.image_paths, self.labels):
                cls_name = EXP13_CLASS_NAMES[label]
                writer.writerow([path, cls_name, label])


class ExternalBinaryDataset(Dataset):
    """
    Loads the Axial CT Kidney Stone external dataset for inference ONLY.

    Safety:
        - model.eval() + torch.no_grad() enforced in evaluator
        - No labels from this dataset are ever used for training
        - No images are copied
        - Augmented directory is rejected

    Parameters
    ----------
    root      : path to the 'Original' directory
    transform : deterministic test transform (no augmentation)
    """

    def __init__(
        self,
        root: str | Path,
        transform: Optional[Callable] = None,
    ):
        self.root = Path(root).resolve()
        self.transform = transform

        # Safety check
        if self.root.name.lower() != "original":
            raise ValueError(
                f"SAFETY ERROR: External dataset root must be the 'Original' "
                f"directory. Got: {self.root}"
            )
        if "augmented" in str(self.root).lower():
            raise ValueError(
                "SAFETY ERROR: Augmented data detected in path. Refusing."
            )

        self.image_paths: List[Path] = []
        self.labels: List[int] = []
        self.filenames: List[str] = []

        # Stone = 1, Non-Stone = 0
        label_map = {"Stone": 1}  # everything else -> 0

        for cls_dir in sorted(self.root.iterdir()):
            if not cls_dir.is_dir():
                continue
            lbl = label_map.get(cls_dir.name, 0)
            for img_path in sorted(cls_dir.iterdir()):
                if img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
                    self.image_paths.append(img_path)
                    self.labels.append(lbl)
                    self.filenames.append(img_path.name)

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, str]:
        img = Image.open(self.image_paths[idx]).convert("RGB")
        label = self.labels[idx]
        if self.transform:
            img = self.transform(img)
        return img, label, str(self.image_paths[idx])

    @property
    def stone_count(self) -> int:
        return sum(1 for l in self.labels if l == 1)

    @property
    def non_stone_count(self) -> int:
        return sum(1 for l in self.labels if l == 0)
