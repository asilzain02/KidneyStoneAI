"""
dataset.py — EXP16 standard 4-class CT dataset.
Identical to baseline; uses project split CSVs (read-only).
Class weights are NOT computed here — computed in train_exp16.py from labels.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset

CLASS_NAMES  = ["Normal", "Cyst", "Stone", "Tumor"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASS_NAMES)}
NUM_CLASSES  = 4


class CTKidneyDataset16(Dataset):
    def __init__(
        self,
        csv_path: str | Path,
        transform: Optional[Callable] = None,
        smoke: bool = False,
        smoke_n: int = 10,
    ):
        self.transform = transform
        df = pd.read_csv(csv_path, encoding="utf-8")
        df = df[df["class_name"].isin(CLASS_NAMES)].reset_index(drop=True)
        if smoke:
            df = (df.groupby("class_name", group_keys=False)
                    .apply(lambda g: g.head(smoke_n))
                    .reset_index(drop=True))
        self.image_paths: List[str] = df["image_path"].tolist()
        self.labels: List[int] = [CLASS_TO_IDX[c] for c in df["class_name"]]
        self._counts = df["class_name"].value_counts().to_dict()

    def __len__(self): return len(self.image_paths)

    def __getitem__(self, idx):
        img = Image.open(self.image_paths[idx]).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, self.labels[idx]

    def class_counts(self) -> dict:
        return {c: self._counts.get(c, 0) for c in CLASS_NAMES}

    def get_labels(self) -> List[int]:
        return self.labels


def compute_class_weights_inverse_sqrt(
    labels: List[int],
    num_classes: int = 4,
    normalize: bool = True,
) -> torch.Tensor:
    """
    Compute class weights using inverse-square-root frequency.

    weight_i ∝ 1 / sqrt(count_i)

    Then optionally normalise so that mean(weights) ≈ 1.0.
    This is softer than pure inverse-frequency and avoids extreme
    Stone-class amplification seen with WeightedRandomSampler.

    Parameters
    ----------
    labels      : list of integer class labels from training split ONLY
    num_classes : 4
    normalize   : if True, scale so mean weight = 1.0

    Returns
    -------
    torch.Tensor of shape [num_classes]
    """
    counts = np.zeros(num_classes, dtype=np.float64)
    for lbl in labels:
        counts[lbl] += 1

    # Avoid division by zero
    counts = np.maximum(counts, 1.0)

    raw_weights = 1.0 / np.sqrt(counts)

    if normalize:
        raw_weights = raw_weights / raw_weights.mean()

    return torch.tensor(raw_weights, dtype=torch.float32)
