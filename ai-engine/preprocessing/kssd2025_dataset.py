"""
kssd2025_dataset.py — PyTorch Dataset for KSSD2025 segmentation.

Reads from a split CSV produced by split_builder.py.
CSV columns: image_path, mask_path, ...

Returns: (image_tensor [1,H,W], mask_tensor [1,H,W])
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Tuple

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset


class KSSD2025Dataset(Dataset):
    """
    Parameters
    ----------
    csv_path   : path to train/val/test split CSV
    transform  : SegmentationTransform callable  (image, mask) → (tensor, tensor)
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

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        image = Image.open(self.image_paths[idx])
        mask = Image.open(self.mask_paths[idx])

        if self.transform:
            image_t, mask_t = self.transform(image, mask)
        else:
            # Fallback: basic conversion without augmentation
            import torchvision.transforms.functional as TF
            import numpy as np
            image_t = TF.to_tensor(image.convert("L"))
            mask_arr = (np.array(mask.convert("L")) > 0).astype("float32")
            mask_t = torch.from_numpy(mask_arr).unsqueeze(0)

        return image_t, mask_t
