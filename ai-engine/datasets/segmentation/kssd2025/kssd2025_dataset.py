"""
kssd2025_dataset.py — Extended PyTorch Dataset for KSSD2025 segmentation.

Extends the existing preprocessing.kssd2025_dataset with:
  - get_stem(idx)  for visualization linkback
  - get_image_path / get_mask_path for evaluation scripts
  - Inherits BaseSegmentationDataset

Reads from a split CSV produced by split_builder.py.
CSV columns: image_path, mask_path, [stem], ...

Returns: (image_tensor [1,H,W], mask_tensor [1,H,W])
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset

import sys
sys.path.insert(0, str(Path(__file__).parents[3]))

from datasets.segmentation.base_segmentation_dataset import BaseSegmentationDataset


class KSSD2025Dataset(BaseSegmentationDataset):
    """
    KSSD2025 PyTorch Dataset with full visualization support.

    Parameters
    ----------
    csv_path   : path to train/val/test split CSV
    transform  : callable (image_pil, mask_pil) → (image_tensor, mask_tensor)
    smoke      : if True, keep only first `smoke_n` pairs
    smoke_n    : sample count for smoke test
    """

    def __init__(
        self,
        csv_path: str | Path,
        transform: Optional[Callable] = None,
        smoke: bool = False,
        smoke_n: int = 50,
    ):
        self.transform = transform
        df = pd.read_csv(csv_path)

        if smoke:
            df = df.head(smoke_n)

        self.image_paths = df["image_path"].tolist()
        self.mask_paths = df["mask_path"].tolist()

        # Derive stems from image paths if not in CSV
        if "stem" in df.columns:
            self.stems = df["stem"].tolist()
        else:
            self.stems = [Path(p).stem for p in self.image_paths]

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        image = Image.open(self.image_paths[idx])
        mask = Image.open(self.mask_paths[idx])

        if self.transform:
            image_t, mask_t = self.transform(image, mask)
        else:
            import torchvision.transforms.functional as TF
            image_t = TF.to_tensor(image.convert("L"))
            mask_arr = (np.array(mask.convert("L")) > 0).astype("float32")
            mask_t = torch.from_numpy(mask_arr).unsqueeze(0)

        return image_t, mask_t

    def get_stem(self, idx: int) -> str:
        return self.stems[idx]

    def get_image_path(self, idx: int) -> str:
        return self.image_paths[idx]

    def get_mask_path(self, idx: int) -> str:
        return self.mask_paths[idx]
