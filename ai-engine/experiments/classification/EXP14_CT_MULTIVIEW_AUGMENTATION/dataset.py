"""
dataset.py — EXP14 dataset loader.

Reads the existing project split CSVs — does NOT modify them.
Applies the EXP14 three-channel multi-view transform.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Tuple

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset

CLASS_NAMES  = ["Normal", "Cyst", "Stone", "Tumor"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASS_NAMES)}


class CTKidneyMultiviewDataset(Dataset):
    """
    Standard 4-class CT kidney dataset; uses the EXP14 multi-view transform.

    Parameters
    ----------
    csv_path  : one of train.csv / val.csv / test.csv  (read-only)
    transform : get_exp14_transforms(phase, cfg)
    smoke     : if True, use only first smoke_n samples per class
    smoke_n   : samples per class for smoke test
    """

    def __init__(
        self,
        csv_path: str | Path,
        transform: Optional[Callable] = None,
        smoke: bool = False,
        smoke_n: int = 20,
    ):
        self.transform = transform
        df = pd.read_csv(csv_path, encoding="utf-8")
        # keep all classes (Normal, Cyst, Stone, Tumor)
        df = df[df["class_name"].isin(CLASS_NAMES)].reset_index(drop=True)

        if smoke:
            df = (
                df.groupby("class_name", group_keys=False)
                  .apply(lambda g: g.head(smoke_n))
                  .reset_index(drop=True)
            )

        self.image_paths: List[str] = df["image_path"].tolist()
        self.labels: List[int] = [CLASS_TO_IDX[c] for c in df["class_name"]]
        self._counts = df["class_name"].value_counts().to_dict()

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img   = Image.open(self.image_paths[idx]).convert("RGB")
        label = self.labels[idx]
        if self.transform:
            img = self.transform(img)
        return img, label

    def class_counts(self) -> dict:
        return {c: self._counts.get(c, 0) for c in CLASS_NAMES}
