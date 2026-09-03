"""
unet.py — Standard U-Net for binary kidney-stone segmentation.

Architecture:
    Encoder: 4 downsampling blocks (double conv + max pool)
    Bottleneck: double conv
    Decoder: 4 upsampling blocks (upsample + concat + double conv)
    Output: 1×1 conv → sigmoid (binary mask probability)

Input:  [B, in_channels, H, W]   (grayscale CT → in_channels=1)
Output: [B, 1, H, W]             probability map in [0, 1]
"""

from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn
import torch.nn.functional as F


class _DoubleConv(nn.Module):
    """(Conv → BN → ReLU) × 2"""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class _Down(nn.Module):
    """MaxPool → DoubleConv"""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.pool = nn.MaxPool2d(2)
        self.conv = _DoubleConv(in_ch, out_ch)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(self.pool(x))


class _Up(nn.Module):
    """Bilinear upsample + skip connection concat + DoubleConv"""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
        self.conv = _DoubleConv(in_ch, out_ch)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        # Pad if spatial dims differ (odd input sizes)
        if x.shape != skip.shape:
            x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=True)
        x = torch.cat([skip, x], dim=1)
        return self.conv(x)


class UNet(nn.Module):
    """
    U-Net segmentation model.

    Parameters
    ----------
    in_channels   : input image channels (1 for grayscale CT)
    out_channels  : output channels      (1 for binary segmentation)
    base_features : feature count at first block (doubles each level)
    """

    def __init__(
        self,
        in_channels: int = 1,
        out_channels: int = 1,
        base_features: int = 32,
    ):
        super().__init__()
        f = base_features

        # Encoder
        self.enc1 = _DoubleConv(in_channels, f)
        self.enc2 = _Down(f, f * 2)
        self.enc3 = _Down(f * 2, f * 4)
        self.enc4 = _Down(f * 4, f * 8)

        # Bottleneck
        self.bottleneck = _Down(f * 8, f * 16)

        # Decoder
        self.dec4 = _Up(f * 16 + f * 8, f * 8)
        self.dec3 = _Up(f * 8 + f * 4, f * 4)
        self.dec2 = _Up(f * 4 + f * 2, f * 2)
        self.dec1 = _Up(f * 2 + f, f)

        # Output
        self.out_conv = nn.Conv2d(f, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder path
        e1 = self.enc1(x)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)

        # Bottleneck
        b = self.bottleneck(e4)

        # Decoder path with skip connections
        d4 = self.dec4(b, e4)
        d3 = self.dec3(d4, e3)
        d2 = self.dec2(d3, e2)
        d1 = self.dec1(d2, e1)

        return torch.sigmoid(self.out_conv(d1))


def build_unet(cfg: Dict) -> UNet:
    """Build a UNet from a config dict."""
    seg_cfg = cfg.get("segmentation", cfg)
    return UNet(
        in_channels=seg_cfg.get("in_channels", 1),
        out_channels=seg_cfg.get("out_channels", 1),
        base_features=seg_cfg.get("base_features", 32),
    )
