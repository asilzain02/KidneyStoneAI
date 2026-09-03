"""
gradcam_generator.py — Grad-CAM explainability for EfficientNet-B0 classifier.

Uses pytorch-grad-cam (grad-cam package) to generate class activation maps.

Output per prediction:
  - original RGB image (numpy)
  - Grad-CAM heatmap (numpy)
  - heatmap overlay on original (numpy)
  - predicted class name
  - prediction confidence (softmax probability)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

log = get_logger(__name__)

# pytorch-grad-cam imports
try:
    from pytorch_grad_cam import GradCAM
    from pytorch_grad_cam.utils.image import show_cam_on_image
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
    _GRADCAM_AVAILABLE = True
except ImportError:
    _GRADCAM_AVAILABLE = False
    log.warning("pytorch-grad-cam not installed. pip install grad-cam")

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]


class GradCAMGenerator:
    """
    Wraps pytorch-grad-cam to generate Grad-CAM visualizations.

    Parameters
    ----------
    model       : KidneyClassifier (nn.Module)
    target_layer: the conv layer to hook. If None, auto-detects EfficientNet's last conv.
    class_names : list of class name strings
    device      : torch device
    """

    def __init__(
        self,
        model: torch.nn.Module,
        target_layer=None,
        class_names: Optional[list] = None,
        device: Optional[torch.device] = None,
    ):
        if not _GRADCAM_AVAILABLE:
            raise ImportError("Install grad-cam: pip install grad-cam")

        self.model = model
        self.class_names = class_names or CLASS_NAMES
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device).eval()

        # Auto-detect target layer for EfficientNet-B0
        if target_layer is None:
            target_layer = self._find_target_layer()

        self.cam = GradCAM(model=model, target_layers=[target_layer])

    def _find_target_layer(self):
        """Return the last convolutional layer of the backbone."""
        # For timm EfficientNet the last conv is backbone.conv_head
        try:
            return self.model.backbone.conv_head
        except AttributeError:
            pass
        # Fallback: find last Conv2d
        last_conv = None
        for module in self.model.modules():
            if isinstance(module, torch.nn.Conv2d):
                last_conv = module
        if last_conv is None:
            raise RuntimeError("Could not find a Conv2d layer for Grad-CAM.")
        return last_conv

    def generate(
        self,
        image_tensor: torch.Tensor,       # [1, 3, H, W] preprocessed
        original_rgb: np.ndarray,         # [H, W, 3] float32 in [0, 1]
        target_class: Optional[int] = None,  # None → use predicted class
    ) -> Dict:
        """
        Generate Grad-CAM for a single image.

        Returns
        -------
        dict with keys:
            original_rgb   np.ndarray [H, W, 3]
            heatmap        np.ndarray [H, W]   (raw CAM values 0..1)
            overlay        np.ndarray [H, W, 3]
            predicted_class str
            predicted_class_id int
            confidence     float
            class_probabilities dict[str, float]
        """
        image_tensor = image_tensor.to(self.device)

        # Forward pass to get probabilities
        with torch.no_grad():
            logits = self.model(image_tensor)
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()

        pred_class_id = int(np.argmax(probs))
        pred_class_name = self.class_names[pred_class_id]
        confidence = float(probs[pred_class_id])

        # Grad-CAM
        cam_target = (
            [ClassifierOutputTarget(target_class)]
            if target_class is not None
            else [ClassifierOutputTarget(pred_class_id)]
        )

        grayscale_cam = self.cam(
            input_tensor=image_tensor, targets=cam_target
        )[0]  # [H, W]

        # Resize original to match CAM if needed
        h, w = grayscale_cam.shape
        orig_resized = np.array(
            Image.fromarray((original_rgb * 255).astype(np.uint8)).resize((w, h))
        ).astype(np.float32) / 255.0

        overlay = show_cam_on_image(orig_resized, grayscale_cam, use_rgb=True)

        return {
            "original_rgb": (original_rgb * 255).astype(np.uint8),
            "heatmap": grayscale_cam,
            "overlay": overlay,
            "predicted_class": pred_class_name,
            "predicted_class_id": pred_class_id,
            "confidence": confidence,
            "class_probabilities": {
                name: float(probs[i])
                for i, name in enumerate(self.class_names)
            },
        }
