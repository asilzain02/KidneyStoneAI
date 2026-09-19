"""
loader.py — Dynamic and safe classification model loader.

Allows the AI Engine inference pipeline to cleanly decouple from hardcoded
architecture names. Automatically constructs the compatible EfficientNet
variant (B0 or B2) depending on what is detected inside the checkpoint.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, Any

import torch
import torch.nn as nn

from models.classifier import KidneyClassifier
from utils.logger import get_logger

log = get_logger("model_loader")


def _detect_architecture(state_dict: Dict[str, torch.Tensor], ckpt_meta: Dict[str, Any]) -> Tuple[str, int]:
    """
    Determine the backbone architecture and input size from a checkpoint.
    
    PRIORITY 1: Explicit Checkpoint Metadata (as written in EXP15).
    PRIORITY 2: state_dict tensor shape inference (fallback for older checkpoints).
    """
    
    # Priority 1: Metadata
    cfg = ckpt_meta.get("config", {})
    if "model" in cfg and "backbone" in cfg["model"]:
        bb = cfg["model"]["backbone"]
        # Look for input size
        size = 224
        if "training" in cfg and "input_size" in cfg["training"]:
            size = cfg["training"]["input_size"]
        elif "classification" in cfg and "input_size" in cfg["classification"]:
            size = cfg["classification"]["input_size"]
        elif bb == "efficientnet_b2":
            size = 320
            
        log.info(f"Architecture detected from metadata: {bb} (Input: {size})")
        return bb, size

    # Priority 2: State Dict Heuristic Analysis
    # The timm efficientnet_bx families always contain a backbone.conv_head.weight
    # Wait, check if DataParallel prefix exists.
    shape_target = None
    for k, v in state_dict.items():
        if k.endswith("conv_head.weight"):
            shape_target = v.shape
            break
            
    if shape_target is None:
        raise RuntimeError("Checkpoint missing 'conv_head.weight', cannot infer EfficientNet variant.")

    channels = shape_target[0]
    
    if channels == 1280:
        log.info("Architecture inferred from tensor shapes: efficientnet_b0 (Input: 224)")
        return "efficientnet_b0", 224
    elif channels == 1408:
        log.info("Architecture inferred from tensor shapes: efficientnet_b2 (Input: 320)")
        return "efficientnet_b2", 320
    else:
        raise RuntimeError(f"Unknown conv_head channel size: {channels}. Cannot deduce architecture.")


def _strip_module_prefix(state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """Remove 'module.' prefix appended by DataParallel."""
    normalized = {}
    for k, v in state_dict.items():
        if k.startswith("module."):
            normalized[k[7:]] = v
        else:
            normalized[k] = v
    return normalized


def load_model_safely(
    checkpoint_path: str | Path,
    device: torch.device,
    expected_num_classes: int = 4
) -> Tuple[nn.Module, int, str]:
    """
    Instantiates the correct KidneyClassifier variant by strictly inspecting
    the checkpoint, ensuring no shape mismatches occur.
    
    Returns:
        tuple containing: (loaded_model, required_input_size, backbone_name)
    """
    path = Path(checkpoint_path)
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")

    ckpt = torch.load(path, map_location=device)
    
    # Handle multiple common structure nests
    if "model_state_dict" in ckpt:
        sd_raw = ckpt["model_state_dict"]
    elif "state_dict" in ckpt:
        sd_raw = ckpt["state_dict"]
    else:
        sd_raw = ckpt # Assuming raw state_dict
        
    sd = _strip_module_prefix(sd_raw)
    
    # Extract structural metadata (if present) to help deduction
    meta = {k: v for k, v in ckpt.items() if k not in ["model_state_dict", "state_dict", "optimizer_state_dict"]}
    
    backbone_name, input_size = _detect_architecture(sd, meta)
    
    # Build model cleanly
    model = KidneyClassifier(
        num_classes=expected_num_classes,
        backbone=backbone_name,
        pretrained=False # No need to redownload ImageNet weights
    )
    
    model_sd = model.state_dict()
    
    # STRICT VALIDATION
    ckpt_keys = set(sd.keys())
    model_keys = set(model_sd.keys())
    
    missing = model_keys - ckpt_keys
    unexpected = ckpt_keys - model_keys
    
    if missing or unexpected:
        err_msg = [f"Checkpoint architecture mismatch! Requested: {backbone_name}"]
        if missing:
            err_msg.append(f"Missing keys: {len(missing)} (e.g., {list(missing)[:3]})")
        if unexpected:
            err_msg.append(f"Unexpected keys: {len(unexpected)} (e.g., {list(unexpected)[:3]})")
        raise RuntimeError("\n".join(err_msg))
        
    # Shape validation
    for k in ckpt_keys:
        if sd[k].shape != model_sd[k].shape:
            raise RuntimeError(
                f"Shape mismatch! Key: {k}\n"
                f"  checkpoint: {list(sd[k].shape)}\n"
                f"  model:      {list(model_sd[k].shape)}\n"
                f"Checkpoint belongs to a different architecture or num_classes."
            )
            
    # Load strictly
    model.load_state_dict(sd, strict=True)
    model.to(device).eval()
    
    log.info(f"Classification model loaded successfully ({backbone_name})")
    
    return model, input_size, backbone_name

