"""
test_models.py — Tests for classification and segmentation models.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch


class TestKidneyClassifier:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

    def test_classifier_initialization(self):
        from models.classifier import KidneyClassifier
        model = KidneyClassifier(num_classes=4, backbone="efficientnet_b0", pretrained=False)
        assert model is not None
        assert model.num_classes == 4
        assert model.backbone_name == "efficientnet_b0"

    def test_classifier_forward_pass_shape(self):
        from models.classifier import KidneyClassifier
        model = KidneyClassifier(num_classes=4, backbone="efficientnet_b0", pretrained=False)
        model.eval()
        x = torch.randn(2, 3, 224, 224)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (2, 4)

    def test_build_classifier_from_cfg(self):
        from models.classifier import build_classifier
        cfg = {"classification": {"num_classes": 3, "backbone": "efficientnet_b0", "pretrained": False, "dropout": 0.5}}
        model = build_classifier(cfg)
        assert model.num_classes == 3


class TestUNet:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

    def test_unet_initialization(self):
        from models.unet.unet import UNet
        model = UNet(in_channels=1, out_channels=1, base_features=16)
        assert model is not None

    def test_unet_forward_pass_shape(self):
        from models.unet.unet import UNet
        model = UNet(in_channels=1, out_channels=1, base_features=16)
        model.eval()
        x = torch.randn(2, 1, 256, 256)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (2, 1, 256, 256)
        assert out.min() >= 0.0
        assert out.max() <= 1.0

    def test_unet_forward_pass_different_size(self):
        # UNet should handle arbitrary sizes that are multiples of 16
        from models.unet.unet import UNet
        model = UNet(in_channels=1, out_channels=1, base_features=16)
        model.eval()
        x = torch.randn(1, 1, 128, 128)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (1, 1, 128, 128)

    def test_build_unet_from_cfg(self):
        from models.unet.unet import build_unet
        cfg = {"segmentation": {"in_channels": 1, "out_channels": 2, "base_features": 16}}
        model = build_unet(cfg)
        assert model.out_conv.out_channels == 2
