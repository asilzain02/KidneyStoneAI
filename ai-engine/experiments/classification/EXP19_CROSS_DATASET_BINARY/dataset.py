"""
EXP19 Dataset Loader (Dataset A)
"""
from __future__ import annotations
import csv
from pathlib import Path
import torch
from torch.utils.data import Dataset
from PIL import Image

class Exp19Dataset(Dataset):
    def __init__(self, manifest_path: str | Path, split: str, root_dir: str | Path, transform=None):
        self.transform = transform
        self.samples = []
        self.split = split
        self.root_dir = Path(root_dir)
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["split"] == split:
                    lbl = int(row["label"])
                    path = self.root_dir / row["path"]
                    self.samples.append((str(path), lbl))
                    
    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor | Image.Image, int]:
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label
