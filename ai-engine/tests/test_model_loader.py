"""
test_model_loader.py — Pytest specifications for the Safe Model Loader.
"""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn
from collections import OrderedDict
from pathlib import Path

from models.loader import _detect_architecture, load_model_safely

# Setup fixture directories conditionally if actual models are accessible for unit testing.
ENGINE_ROOT = Path(__file__).parent.parent
B0_CKPT = ENGINE_ROOT / "weights" / "classification" / "final_candidate_exp02a.pth"
B2_CKPT = ENGINE_ROOT / "experiments" / "classification" / "EXP15_EFFICIENTNET_B2_320" / "outputs" / "checkpoints" / "best_model_exp15_b2_320.pth"

# Creating a mock checkpoint structure generator to avoid relying heavily on multi-megabyte files in CI
def _create_mock_state_dict(channels: int) -> OrderedDict:
    # A simplified state dictionary resembling timm EfficientNet output.
    sd = OrderedDict()
    sd["backbone.conv_stem.weight"] = torch.randn(32, 3, 3, 3)
    sd["backbone.conv_head.weight"] = torch.randn(channels, channels // 4, 1, 1)
    sd["head.1.weight"] = torch.randn(4, channels)
    sd["head.1.bias"] = torch.randn(4)
    # Include DataParallel module test prefix if needed
    return sd

def test_architecture_detection_b0():
    """Detects B0 cleanly via 1280 conv_head fallback."""
    sd = _create_mock_state_dict(1280)
    bb, size = _detect_architecture(sd, {})
    assert bb == "efficientnet_b0"
    assert size == 224

def test_architecture_detection_b2():
    """Detects B2 cleanly via explicit metadata config."""
    sd = _create_mock_state_dict(1408)
    # Using the exact EXP15 nested structure
    meta = {
        "config": {
            "model": {"backbone": "efficientnet_b2"},
            "training": {"input_size": 320}
        }
    }
    bb, size = _detect_architecture(sd, meta)
    assert bb == "efficientnet_b2"
    assert size == 320
    
def test_architecture_detection_b2_fallback():
    """Detects B2 cleanly via 1408 fallback if config is absent."""
    sd = _create_mock_state_dict(1408)
    bb, size = _detect_architecture(sd, {}) # No config
    assert bb == "efficientnet_b2"
    assert size == 320

def test_dataparallel_normalization():
    """Test standard module wrapper boundary stripping."""
    from models.loader import _strip_module_prefix
    
    sd = OrderedDict()
    sd["module.backbone.conv_head.weight"] = torch.randn(1280, 320, 1, 1)
    sd["module.head.weight"] = torch.randn(4, 1280)
    
    clean_sd = _strip_module_prefix(sd)
    assert "backbone.conv_head.weight" in clean_sd
    assert "module.backbone.conv_head.weight" not in clean_sd

@pytest.mark.skipif(not B0_CKPT.exists(), reason="Requires actual local baseline B0 checkpoint")
def test_load_existing_b0_checkpoint():
    """TEST 1: Load existing B0 production checkpoint cleanly."""
    device = torch.device("cpu")
    model, input_size, backbone = load_model_safely(B0_CKPT, device)
    
    assert backbone == "efficientnet_b0"
    assert input_size == 224
    assert hasattr(model.backbone, "conv_head")
    assert model.backbone.conv_head.weight.shape[0] == 1280

@pytest.mark.skipif(not B2_CKPT.exists(), reason="Requires actual local EXP15 B2 checkpoint")
def test_load_exp15_b2_checkpoint():
    """TEST 2: Load EXP15 B2 checkpoint cleanly."""
    device = torch.device("cpu")
    model, input_size, backbone = load_model_safely(B2_CKPT, device)
    
    assert backbone == "efficientnet_b2"
    assert input_size == 320
    assert hasattr(model.backbone, "conv_head")
    assert model.backbone.conv_head.weight.shape[0] == 1408

def test_mismatched_architecture_throws_error(tmp_path):
    """TEST 3: Intentional mismatch throws expected strict error rather than partial loaded tensors."""
    checkpoint_path = tmp_path / "mock_b2.pth"
    sd = _create_mock_state_dict(1408)
    
    # Intentionally malform B2 representation to trick loader but not the class shapes
    meta = {
        "config": {
            "model": {"backbone": "efficientnet_b0"} # Lie about architecture
        }
    }
    torch.save({"model_state_dict": sd, **meta}, checkpoint_path)
    
    with pytest.raises(RuntimeError) as exc:
        load_model_safely(checkpoint_path, torch.device("cpu"))
        
    err_str = str(exc.value)
    assert "Shape mismatch" in err_str or "Mismatch" in err_str or "Missing" in err_str

@pytest.mark.skipif(not B0_CKPT.exists() or not B2_CKPT.exists(), reason="Requires both models")
def test_gradcam_target_resolution():
    """TEST 5: Grad-CAM target layer resolution for both architectures."""
    device = torch.device("cpu")
    
    model_b0, _, _ = load_model_safely(B0_CKPT, device)
    model_b2, _, _ = load_model_safely(B2_CKPT, device)
    
    import sys
    sys.path.insert(0, str(ENGINE_ROOT))
    from gradcam.gradcam_generator import GradCAMGenerator
    
    gc_b0 = GradCAMGenerator(model_b0, device=device)
    gc_b2 = GradCAMGenerator(model_b2, device=device)
    
    assert gc_b0._find_target_layer() is not None
    assert gc_b2._find_target_layer() is not None

