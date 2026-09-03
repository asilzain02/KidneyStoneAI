"""
inference.py — U-Net inference for kidney stone segmentation.

Loads a trained U-Net checkpoint and runs inference on a PIL Image,
returning a probability mask and binary mask.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import torch
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.unet.unet import UNet, build_unet
from preprocessing.segmentation_transforms import get_segmentation_transforms
from evaluation.segmentation_metrics import compute_sample_metrics
from utils.logger import get_logger

log = get_logger(__name__)


class SegmentationInference:
    """
    U-Net inference wrapper.

    Parameters
    ----------
    checkpoint_path : path to saved .pth weights
    cfg             : full training config dict
    device          : torch device (auto-detected if None)
    """

    def __init__(
        self,
        checkpoint_path: str | Path,
        cfg: Dict,
        device: Optional[torch.device] = None,
    ):
        self.device = device or torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.cfg = cfg
        self.image_size = cfg["segmentation"]["input_size"]
        self.transform = get_segmentation_transforms("test", self.image_size)

        self.model = build_unet(cfg)
        ckpt = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.to(self.device).eval()
        log.info("Segmentation model loaded", checkpoint=str(checkpoint_path))

    @torch.no_grad()
    def predict(
        self,
        image: Image.Image,
        threshold: float = 0.5,
    ) -> Dict:
        """
        Run inference on a single PIL Image.

        Returns
        -------
        dict:
            prob_mask   np.ndarray [H, W] float32 — raw probability
            binary_mask np.ndarray [H, W] uint8   — thresholded {0, 255}
            stone_area_pixels int               — positive pixels count
        """
        dummy_mask = Image.new("L", image.size, 0)
        image_t, _ = self.transform(image, dummy_mask)
        image_t = image_t.unsqueeze(0).to(self.device)  # [1, 1, H, W]

        prob = self.model(image_t)[0, 0].cpu().numpy()  # [H, W]
        binary = (prob > threshold).astype(np.uint8) * 255
        stone_pixels = int((binary > 0).sum())

        return {
            "prob_mask": prob,
            "binary_mask": binary,
            "stone_area_pixels": stone_pixels,
        }

    @torch.no_grad()
    def predict_with_gt(
        self,
        image: Image.Image,
        mask: Image.Image,
        threshold: float = 0.5,
    ) -> Dict:
        """
        Run inference with ground-truth mask. Returns prediction + metrics.
        """
        image_t, mask_t = self.transform(image, mask)
        image_t = image_t.unsqueeze(0).to(self.device)

        prob = self.model(image_t)[0, 0].cpu().numpy()
        metrics = compute_sample_metrics(prob, mask_t[0].numpy(), threshold)

        binary = (prob > threshold).astype(np.uint8) * 255
        return {
            "prob_mask": prob,
            "binary_mask": binary,
            "stone_area_pixels": int((binary > 0).sum()),
            **metrics,
        }
