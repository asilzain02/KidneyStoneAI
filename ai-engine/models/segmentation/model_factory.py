"""
model_factory.py — Segmentation model factory.

Usage:
    from models.segmentation.model_factory import create_segmentation_model
    model = create_segmentation_model(config)

Currently registered:
    unet → UNet (models/unet/unet.py)

Extension points:
    To add UNet++:  register "unetplusplus" below.
    To add DeepLab: register "deeplab" below.
    To add FPN:     register "fpn" below.
    Do NOT modify existing registrations.
"""

from __future__ import annotations

from typing import Dict

import sys
from pathlib import Path

import torch.nn as nn

sys.path.insert(0, str(Path(__file__).parents[2]))

from models.unet.unet import UNet


# ── Registry ──────────────────────────────────────────────────────────────────
# Map model name (lowercase) → constructor callable(cfg: Dict) → nn.Module

def _build_unet(cfg: Dict) -> UNet:
    model_cfg = cfg.get("model", cfg)
    return UNet(
        in_channels=model_cfg.get("in_channels", 1),
        out_channels=model_cfg.get("out_channels", 1),
        base_features=model_cfg.get("base_features", 32),
    )


_REGISTRY: Dict[str, callable] = {
    "unet": _build_unet,
    # "unetplusplus": _build_unetplusplus,   # future
    # "deeplab":      _build_deeplab,         # future
    # "fpn":          _build_fpn,             # future
}


# ── Public API ────────────────────────────────────────────────────────────────

def create_segmentation_model(config: Dict) -> nn.Module:
    """
    Instantiate a segmentation model from a config dict.

    The config must contain:
        config["model"]["name"]  →  one of the registered model names

    Parameters
    ----------
    config : dict
        Full or partial config. The factory reads config["model"].

    Returns
    -------
    nn.Module
        Constructed (untrained) segmentation model.

    Raises
    ------
    ValueError
        If the model name is not registered.
    """
    model_cfg = config.get("model", config)
    name = model_cfg.get("name", "unet").lower()

    if name not in _REGISTRY:
        available = list(_REGISTRY.keys())
        raise ValueError(
            f"Unknown segmentation model '{name}'. "
            f"Available: {available}"
        )

    return _REGISTRY[name](config)


def list_models() -> list:
    """Return a list of all registered model names."""
    return list(_REGISTRY.keys())
