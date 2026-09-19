"""
transforms.py — EXP14 multi-view CT transforms.

Two phases:
  - MultiviewCTTransform  : builds the 3-channel tensor from a PIL Image
  - CTAugmentation        : wraps MultiviewCTTransform with training-time jitter

Channel layout (all spatially aligned):
  ch0 → original normalised grayscale  (OpenCV LAB L-channel → [0,1])
  ch1 → CLAHE-enhanced                  (applied to LAB L-channel)
  ch2 → soft-edge map                   (Gaussian-smoothed Sobel magnitude)

Val/Test: only the deterministic MultiviewCTTransform is applied.
Train:    CT-safe random augmentations precede channel construction.
"""

from __future__ import annotations

import math
import random
from typing import Tuple

import numpy as np
import torch
import torchvision.transforms as T
import torchvision.transforms.functional as TF
from PIL import Image

# ── ImageNet stats (EfficientNet pretrained on ImageNet) ──────────────────────
_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD  = (0.229, 0.224, 0.225)

# Try importing OpenCV; fall back to PIL-only CLAHE approximation if absent
try:
    import cv2 as _cv2
    _OPENCV_AVAILABLE = True
except ImportError:
    _OPENCV_AVAILABLE = False


# ── Low-level channel builders ─────────────────────────────────────────────────

def _pil_to_gray_np(img: Image.Image) -> np.ndarray:
    """Convert PIL RGB → uint8 grayscale ndarray [H, W]."""
    return np.array(img.convert("L"), dtype=np.uint8)


def _clahe_enhance(gray: np.ndarray, clip_limit: float, tile_size: int) -> np.ndarray:
    """
    Apply CLAHE to a uint8 grayscale array.
    Falls back to simple histogram equalization if OpenCV is unavailable.
    """
    if _OPENCV_AVAILABLE:
        clahe = _cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=(tile_size, tile_size),
        )
        return clahe.apply(gray)
    # PIL fallback: ImageOps.equalize
    from PIL import ImageOps
    pil = Image.fromarray(gray)
    return np.array(ImageOps.equalize(pil), dtype=np.uint8)


def _soft_edge_map(gray: np.ndarray) -> np.ndarray:
    """
    Compute a soft edge map using Sobel (via OpenCV) or gradient approximation.
    Returns a uint8 array scaled to [0, 255].
    """
    if _OPENCV_AVAILABLE:
        # Gaussian smooth first to reduce noise sensitivity
        blurred = _cv2.GaussianBlur(gray.astype(np.float32), (3, 3), sigmaX=1.0)
        sobelx  = _cv2.Sobel(blurred, _cv2.CV_32F, 1, 0, ksize=3)
        sobely  = _cv2.Sobel(blurred, _cv2.CV_32F, 0, 1, ksize=3)
        mag = np.sqrt(sobelx**2 + sobely**2)
    else:
        # NumPy fallback using finite differences
        g = gray.astype(np.float32)
        gx = np.gradient(g, axis=1)
        gy = np.gradient(g, axis=0)
        mag = np.sqrt(gx**2 + gy**2)

    # Normalize to [0, 255]
    if mag.max() > 0:
        mag = mag / mag.max() * 255.0
    return mag.astype(np.uint8)


def _build_three_channel_tensor(
    pil_img: Image.Image,
    clahe_clip: float = 2.0,
    clahe_tile: int = 8,
) -> torch.Tensor:
    """
    From a PIL image (any mode), produce a [3, H, W] float tensor with
    ImageNet normalisation applied independently per channel.

    ch0: original grayscale [0, 1]
    ch1: CLAHE-enhanced     [0, 1]
    ch2: soft-edge map      [0, 1]
    """
    gray = _pil_to_gray_np(pil_img)  # [H, W] uint8

    ch0 = gray.astype(np.float32) / 255.0
    ch1 = _clahe_enhance(gray, clahe_clip, clahe_tile).astype(np.float32) / 255.0
    ch2 = _soft_edge_map(gray).astype(np.float32) / 255.0

    # Stack → [H, W, 3] then → [3, H, W]
    arr = np.stack([ch0, ch1, ch2], axis=2)
    tensor = torch.from_numpy(arr).permute(2, 0, 1).float()  # [3, H, W]

    # Apply per-channel ImageNet normalisation
    mean = torch.tensor(_IMAGENET_MEAN).view(3, 1, 1)
    std  = torch.tensor(_IMAGENET_STD).view(3, 1, 1)
    tensor = (tensor - mean) / std

    return tensor


# ── Transform wrappers ─────────────────────────────────────────────────────────

class MultiviewCTTransform:
    """
    Deterministic transform for val/test.
    Resizes the PIL image then builds the 3-channel tensor.
    """

    def __init__(self, size: int = 224, clahe_clip: float = 2.0, clahe_tile: int = 8):
        self.size       = size
        self.clahe_clip = clahe_clip
        self.clahe_tile = clahe_tile
        self._resize    = T.Resize((size, size))

    def __call__(self, img: Image.Image) -> torch.Tensor:
        img = self._resize(img)
        return _build_three_channel_tensor(img, self.clahe_clip, self.clahe_tile)


class CTMultiviewAugmentation:
    """
    Training-time CT-safe augmentation + multi-view channel construction.

    Strategy:
      1. PIL-level spatial jitter (rotation, translate, scale, h-flip)
      2. PIL-level intensity jitter (brightness/contrast)
      3. Random gamma perturbation
      4. Resize to target size
      5. Build 3-channel tensor (original | CLAHE | soft-edge)

    NO vertical flip (anatomically unsafe for abdominal CT).
    NO aggressive elastic deformation.
    NO colour-only transforms that destroy HU relationships.
    """

    def __init__(
        self,
        size: int = 224,
        rotation_degrees: float = 10,
        translate: float = 0.05,
        scale_range: Tuple[float, float] = (0.95, 1.05),
        horizontal_flip_p: float = 0.5,
        brightness_jitter: float = 0.15,
        contrast_jitter: float = 0.15,
        gaussian_blur_p: float = 0.3,
        gaussian_blur_sigma: Tuple[float, float] = (0.5, 1.5),
        gamma_range: Tuple[float, float] = (0.85, 1.15),
        clahe_clip: float = 2.0,
        clahe_tile: int = 8,
    ):
        self.size                = size
        self.rotation_degrees    = rotation_degrees
        self.translate           = translate
        self.scale_range         = scale_range
        self.horizontal_flip_p   = horizontal_flip_p
        self.brightness_jitter   = brightness_jitter
        self.contrast_jitter     = contrast_jitter
        self.gaussian_blur_p     = gaussian_blur_p
        self.gaussian_blur_sigma = gaussian_blur_sigma
        self.gamma_range         = gamma_range
        self.clahe_clip          = clahe_clip
        self.clahe_tile          = clahe_tile

        # Resize to slightly larger first; random crop to target
        self._resize = T.Resize((size + 32, size + 32))
        self._crop   = T.RandomCrop(size)

    def __call__(self, img: Image.Image) -> torch.Tensor:
        # ── Spatial augmentations (PIL) ───────────────────────────────────────
        img = self._resize(img)

        # Random rotation
        angle = random.uniform(-self.rotation_degrees, self.rotation_degrees)
        img = TF.rotate(img, angle)

        # Random translate + scale (affine)
        max_dx = self.translate * img.width
        max_dy = self.translate * img.height
        tx = random.uniform(-max_dx, max_dx)
        ty = random.uniform(-max_dy, max_dy)
        scale = random.uniform(*self.scale_range)
        img = TF.affine(img, angle=0, translate=(int(tx), int(ty)),
                        scale=scale, shear=0)

        # Horizontal flip (NO vertical flip)
        if random.random() < self.horizontal_flip_p:
            img = TF.hflip(img)

        # Random crop to target size
        img = self._crop(img)

        # ── Intensity augmentations (PIL) ─────────────────────────────────────
        bf = 1.0 + random.uniform(-self.brightness_jitter, self.brightness_jitter)
        cf = 1.0 + random.uniform(-self.contrast_jitter,   self.contrast_jitter)
        img = TF.adjust_brightness(img, bf)
        img = TF.adjust_contrast(img, cf)

        # Gentle Gaussian blur to simulate CT reconstruction kernel variation
        if random.random() < self.gaussian_blur_p:
            sigma = random.uniform(*self.gaussian_blur_sigma)
            # kernel size must be odd and >= 1
            ks = max(3, int(sigma * 3) | 1)
            img = TF.gaussian_blur(img, kernel_size=ks, sigma=sigma)

        # ── Gamma perturbation ────────────────────────────────────────────────
        gamma = random.uniform(*self.gamma_range)
        img = TF.adjust_gamma(img, gamma)

        # ── Build 3-channel tensor ────────────────────────────────────────────
        return _build_three_channel_tensor(img, self.clahe_clip, self.clahe_tile)


def get_exp14_transforms(phase: str, cfg: dict) -> object:
    """
    Return the appropriate transform for EXP14.

    Parameters
    ----------
    phase : 'train' | 'val' | 'test'
    cfg   : full experiment config dict
    """
    size     = int(cfg["training"]["input_size"])
    mv_cfg   = cfg.get("multiview", {})
    aug_cfg  = cfg.get("augmentation", {})

    clahe_clip = float(mv_cfg.get("clahe_clip_limit", 2.0))
    clahe_tile = int(mv_cfg.get("clahe_tile_size", 8))

    if phase != "train":
        return MultiviewCTTransform(size=size, clahe_clip=clahe_clip,
                                    clahe_tile=clahe_tile)
    return CTMultiviewAugmentation(
        size               = size,
        rotation_degrees   = float(aug_cfg.get("rotation_degrees", 10)),
        translate          = float(aug_cfg.get("translate", 0.05)),
        scale_range        = tuple(aug_cfg.get("scale_range", [0.95, 1.05])),
        horizontal_flip_p  = float(aug_cfg.get("horizontal_flip_p", 0.5)),
        brightness_jitter  = float(aug_cfg.get("brightness_jitter", 0.15)),
        contrast_jitter    = float(aug_cfg.get("contrast_jitter", 0.15)),
        gaussian_blur_p    = float(aug_cfg.get("gaussian_blur_p", 0.3)),
        gaussian_blur_sigma= tuple(aug_cfg.get("gaussian_blur_sigma",
                                               [0.5, 1.5])),
        gamma_range        = tuple(aug_cfg.get("gamma_range", [0.85, 1.15])),
        clahe_clip         = clahe_clip,
        clahe_tile         = clahe_tile,
    )
