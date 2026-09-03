"""
experiment_registry.py — Segmentation experiment registry.

Records all segmentation experiments to:
    outputs/segmentation/experiment_registry.json

Usage:
    from utils.experiment_registry import SegmentationRegistry
    registry = SegmentationRegistry()
    registry.register(experiment_name="segmentation_baseline", metadata={...})
    registry.save()
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger

log = get_logger(__name__)


class SegmentationRegistry:
    """
    Persistent registry of segmentation experiments.

    Records:
      - experiment name
      - model architecture
      - training configuration
      - best metrics
      - checkpoint path
      - timestamp
    """

    def __init__(
        self,
        registry_path: Optional[Path] = None,
    ):
        if registry_path is None:
            # Default: project_root/outputs/segmentation/experiment_registry.json
            _engine_root = Path(__file__).resolve().parents[1]
            _project_root = _engine_root.parent
            registry_path = _project_root / "outputs" / "segmentation" / "experiment_registry.json"

        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._records: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except Exception:
                return []
        return []

    def register(
        self,
        experiment_name: str,
        model: str = "unet",
        encoder: str = "none",
        input_size: int = 256,
        batch_size: int = 8,
        learning_rate: float = 1e-4,
        optimizer: str = "adam",
        scheduler: str = "reduce_on_plateau",
        loss: str = "dice_bce",
        augmentation: bool = True,
        epochs_trained: int = 0,
        best_epoch: int = 0,
        best_val_dice: float = 0.0,
        test_dice: Optional[float] = None,
        test_iou: Optional[float] = None,
        checkpoint_path: str = "",
        seed: int = 42,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register or update an experiment record."""
        record = {
            "experiment_name":  experiment_name,
            "model":            model,
            "encoder":          encoder,
            "input_size":       input_size,
            "batch_size":       batch_size,
            "learning_rate":    learning_rate,
            "optimizer":        optimizer,
            "scheduler":        scheduler,
            "loss":             loss,
            "augmentation":     augmentation,
            "epochs_trained":   epochs_trained,
            "best_epoch":       best_epoch,
            "best_val_dice":    best_val_dice,
            "test_dice":        test_dice,
            "test_iou":         test_iou,
            "checkpoint_path":  checkpoint_path,
            "seed":             seed,
            "timestamp":        datetime.now().isoformat(),
        }
        if extra:
            record.update(extra)

        # Update if exists, otherwise append
        for i, existing in enumerate(self._records):
            if existing.get("experiment_name") == experiment_name:
                self._records[i] = record
                log.info("Registry — updated experiment", name=experiment_name)
                return

        self._records.append(record)
        log.info("Registry — registered experiment", name=experiment_name)

    def save(self) -> None:
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self._records, f, indent=2, default=str)
        log.info("Experiment registry saved", path=str(self.registry_path))

    def get(self, experiment_name: str) -> Optional[Dict]:
        for r in self._records:
            if r.get("experiment_name") == experiment_name:
                return r
        return None

    def list_experiments(self) -> List[str]:
        return [r["experiment_name"] for r in self._records]

    def best_experiment(self, metric: str = "test_dice") -> Optional[Dict]:
        valid = [r for r in self._records if r.get(metric) is not None]
        if not valid:
            return None
        return max(valid, key=lambda r: r[metric])
