"""
base_segmentation_dataset.py — Abstract base class for all segmentation datasets.

Every concrete segmentation dataset must implement:
  - __len__
  - __getitem__ → (image_tensor, mask_tensor)
  - get_stem(idx) → str   (filename stem for visualization linkback)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

import torch
from torch.utils.data import Dataset


class BaseSegmentationDataset(Dataset, ABC):
    """
    Abstract base for image segmentation datasets.

    Subclasses return:
        image_tensor : float32 [1, H, W] normalised [0, 1]
        mask_tensor  : float32 [1, H, W] binary {0.0, 1.0}
    """

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]: ...

    @abstractmethod
    def get_stem(self, idx: int) -> str:
        """Return filename stem for sample at index (used during visualization)."""
        ...

    def get_image_path(self, idx: int) -> str:
        """Return raw image path for sample. Optional — override if needed."""
        raise NotImplementedError

    def get_mask_path(self, idx: int) -> str:
        """Return raw mask path for sample. Optional — override if needed."""
        raise NotImplementedError
