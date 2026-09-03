"""
ct_kidney_dataset.py — PyTorch Dataset for CT Kidney classification.

Reads from a split CSV (train.csv / val.csv / test.csv) produced
by split_builder.py.

CSV columns: image_path, class_name, class_id, ...
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Tuple

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]
CLASS_TO_ID = {c: i for i, c in enumerate(CLASS_NAMES)}


class CTKidneyDataset(Dataset):
    """
    Parameters
    ----------
    csv_path : path to train/val/test split CSV
    transform : torchvision Compose (from classification_transforms.py)
    class_names : optional override for class ordering
    smoke : if True, keep only first `smoke_n` samples per class
    smoke_n : number of samples per class for smoke test
    """

    def __init__(
        self,
        csv_path: str | Path,
        transform: Optional[Callable] = None,
        class_names: Optional[List[str]] = None,
        smoke: bool = False,
        smoke_n: int = 50,
    ):
        self.transform = transform
        self.class_names = class_names or CLASS_NAMES
        self.class_to_id = {c: i for i, c in enumerate(self.class_names)}

        df = pd.read_csv(csv_path)

        if smoke:
            df = (
                df.groupby("class_name", group_keys=False)
                .apply(lambda g: g.head(smoke_n))
                .reset_index(drop=True)
            )

        self.image_paths: List[str] = df["image_path"].tolist()
        self.labels: List[int] = [
            self.class_to_id.get(c, -1) for c in df["class_name"].tolist()
        ]

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img = Image.open(self.image_paths[idx]).convert("RGB")
        label = self.labels[idx]
        if self.transform:
            img = self.transform(img)
        return img, label

    def get_class_weights(self) -> torch.Tensor:
        """Return inverse-frequency class weights for weighted loss."""
        counts = torch.zeros(len(self.class_names))
        for lbl in self.labels:
            counts[lbl] += 1
        weights = 1.0 / counts.clamp(min=1)
        return weights / weights.sum() * len(self.class_names)
