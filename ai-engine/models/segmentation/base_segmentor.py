"""
base_segmentor.py — Abstract base class for all segmentation models.

Every segmentation model registered with the factory must:
  - Accept an input tensor of shape [B, C, H, W]
  - Return a probability map of shape [B, 1, H, W] in [0, 1]
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

import torch
import torch.nn as nn


class BaseSegmentor(nn.Module, ABC):
    """
    Abstract base segmentor.

    All segmentation models in this project must inherit from this class
    so they can be used interchangeably via the model factory.
    """

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Parameters
        ----------
        x : torch.Tensor  [B, in_channels, H, W]

        Returns
        -------
        torch.Tensor  [B, 1, H, W]  probability map in [0, 1]
        """
        ...

    @classmethod
    @abstractmethod
    def from_config(cls, cfg: Dict) -> "BaseSegmentor":
        """Construct from a config dict."""
        ...
