"""
axial_kidney_stone_adapter.py — External dataset adapter for the Axial CT Kidney Stone Dataset.

This adapter explicitly loads validation inference bounds over the 'Original' subset,
dropping the 'Augmented' paths completely.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.image_utils import load_image
from utils.logger import get_logger

log = get_logger(__name__)

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

class AxialKidneyStoneAdapter:
    """
    Independent external evaluation adapter exclusively bound to the 
    Original/Stone and Original/Non-Stone directories.
    """
    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.original_dir = self.root_dir / "Original"
        self.augmented_dir = self.root_dir / "Augmented"
        
        self.stone_dir = self.original_dir / "Stone"
        self.non_stone_dir = self.original_dir / "Non-Stone"

        self.records: List[Dict] = []
        self._stats = {
            "total": 0,
            "stone": 0,
            "non_stone": 0,
            "valid": 0,
            "invalid": 0,
            "augmented_used": 0
        }

    def _validate_structure(self) -> None:
        """Pre-check validation matching user specifications strictly."""
        # Strictly exclude augmented data intercepts
        if "Augmented" in str(self.root_dir.absolute()):
            raise ValueError(f"CRITICAL ERROR: Refusing to evaluate against Augmented directory: {self.root_dir}")
            
        if not self.original_dir.exists() and (self.root_dir.name in ["Stone", "Non-Stone"]):
            # For direct subsets allowed via CLI manual mappings
            self.original_dir = self.root_dir.parent
            self.stone_dir = self.original_dir / "Stone"
            self.non_stone_dir = self.original_dir / "Non-Stone"
            
        if not self.original_dir.exists():
            # If the user literally pointed it precisely at exactly Original
            if self.root_dir.name == "Original":
                self.original_dir = self.root_dir
                self.stone_dir = self.original_dir / "Stone"
                self.non_stone_dir = self.original_dir / "Non-Stone"
            else:
                raise FileNotFoundError(f"Original directory not found under: {self.root_dir}")

        if not self.stone_dir.exists() or not self.stone_dir.is_dir():
            raise FileNotFoundError(f"Missing required Stone directory: {self.stone_dir}")
        if not self.non_stone_dir.exists() or not self.non_stone_dir.is_dir():
            raise FileNotFoundError(f"Missing required Non-Stone directory: {self.non_stone_dir}")

    def discover(self) -> None:
        """Discover items internally inside defined classification boundaries."""
        self._validate_structure()

        self._scan_directory(self.stone_dir, "STONE")
        self._scan_directory(self.non_stone_dir, "NON_STONE")

        log.info(
            "External Dataset Validation Phase",
            dataset="Axial CT Kidney Stone Dataset",
            source="Original",
            stone=self._stats["stone"],
            non_stone=self._stats["non_stone"],
            augmented_used=self._stats["augmented_used"],
            valid=self._stats["valid"],
            invalid=self._stats["invalid"]
        )
        
        self.print_report()

    def _scan_directory(self, dir_path: Path, ground_truth: str) -> None:
        """Scans isolated tree mapping matching properties strictly."""
        for entry in dir_path.glob("**/*"):
            if entry.is_file():
                ext = entry.suffix.lower()
                if ext not in SUPPORTED_EXT:
                    continue
                
                # Check file opens safely
                img = load_image(entry)
                
                self._stats["total"] += 1
                
                if img is None:
                    self._stats["invalid"] += 1
                    continue
                    
                self._stats["valid"] += 1
                if ground_truth == "STONE":
                    self._stats["stone"] += 1
                else:
                    self._stats["non_stone"] += 1
                    
                self.records.append({
                    "image_path": str(entry.absolute()),
                    "filename": entry.name,
                    "ground_truth": ground_truth,
                })
                # Close memory
                img.close()

    def print_report(self) -> None:
        print("\nExternal Dataset Validation")
        print("-" * 27)
        print("Dataset: Axial CT Kidney Stone Dataset")
        print("Source: Original\n")
        print(f"Stone images: {self._stats['stone']}")
        print(f"Non-Stone images: {self._stats['non_stone']}")
        print(f"Total images: {self._stats['total']}\n")
        print(f"Augmented images used: {self._stats['augmented_used']}\n")
        print(f"Valid images: {self._stats['valid']}")
        print(f"Invalid images: {self._stats['invalid']}\n")
        if self._stats["valid"] > 0:
            print("Status: READY\n")
        else:
            print("Status: FAILED\n")

    def get_records(self) -> List[Dict]:
        return self.records

    def get_stats(self) -> Dict:
        return self._stats
