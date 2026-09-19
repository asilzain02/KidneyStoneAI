"""
transforms.py — EXP18 CT-Specific Augmentation Transform.
"""

from __future__ import annotations
import random
import torch
import torchvision.transforms as T
import torchvision.transforms.functional as TF
from PIL import Image

_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD  = (0.229, 0.224, 0.225)

class CTWindowAugmentation(torch.nn.Module):
    """
    Simulates varied window/level CT captures by shifting and stretching
    intensities dynamically while restricting bounds [0, 1].
    """
    def __init__(self, prob=0.5, shift_range=(-0.05, 0.05), scale_range=(0.9, 1.1)):
        super().__init__()
        self.prob = prob
        self.shift_range = shift_range
        self.scale_range = scale_range

    def forward(self, img_tensor: torch.Tensor) -> torch.Tensor:
        if random.random() > self.prob: return img_tensor
        shift = random.uniform(*self.shift_range)
        scale = random.uniform(*self.scale_range)
        # Apply transformation
        img_tensor = img_tensor * scale + shift
        return torch.clamp(img_tensor, 0.0, 1.0)


class CTB2SafeAugmentation:
    def __init__(self, size: int, cfg: dict):
        self.size = size
        a = cfg.get("augmentation", {})
        self.rot = a.get("rotation_degrees", 7)
        self.tr  = a.get("translate", 0.05)
        self.sc  = a.get("scale_range", [0.95, 1.05])
        self.hf  = a.get("horizontal_flip_p", 0.5)
        self.bj  = a.get("brightness_jitter", 0.1)
        self.cj  = a.get("contrast_jitter", 0.2)
        self.gm  = a.get("gamma_range", [0.85, 1.15])
        
        self.win = CTWindowAugmentation(
            prob=a.get("intensity_window_prob", 0.5),
            shift_range=a.get("intensity_shift_range", [-0.05, 0.05]),
            scale_range=a.get("intensity_scale_range", [0.9, 1.1])
        )

        self._resize = T.Resize((size + 32, size + 32))
        self._crop = T.RandomCrop(size)

    def __call__(self, img: Image.Image) -> torch.Tensor:
        # 1. PIL Spatial
        img = self._resize(img)
        angle = random.uniform(-self.rot, self.rot)
        tx, ty = random.uniform(-self.tr*img.width, self.tr*img.width), random.uniform(-self.tr*img.height, self.tr*img.height)
        scale = random.uniform(*self.sc)
        img = TF.affine(img, angle=angle, translate=(int(tx), int(ty)), scale=scale, shear=0)
        if random.random() < self.hf: img = TF.hflip(img)
        img = self._crop(img)

        # 2. PIL Intensity
        img = TF.adjust_brightness(img, 1.0 + random.uniform(-self.bj, self.bj))
        img = TF.adjust_contrast(img, 1.0 + random.uniform(-self.cj, self.cj))
        img = TF.adjust_gamma(img, random.uniform(*self.gm))

        # 3. Tensor Operations (CT Windowing -> ImageNet Norm)
        t = TF.to_tensor(img)  # [0, 1]
        t = self.win(t)
        return TF.normalize(t, mean=_IMAGENET_MEAN, std=_IMAGENET_STD)

class DeterministicCTTransform:
    def __init__(self, size: int): self.rs = T.Resize((size, size))
    def __call__(self, img: Image.Image) -> torch.Tensor:
        return TF.normalize(TF.to_tensor(self.rs(img)), mean=_IMAGENET_MEAN, std=_IMAGENET_STD)

def get_exp18_transforms(phase: str, size: int, cfg: dict) -> object:
    if phase == "train":
        return CTB2SafeAugmentation(size, cfg)
    return DeterministicCTTransform(size)
