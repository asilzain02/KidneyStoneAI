"""
experiment_loader.py — Loads and merges per-experiment config overrides.

Each experiment lives in:
    ai-engine/weights/experiments/<exp_name>/experiment_config.yaml

That YAML contains only the keys that DIFFER from the baseline.
The loader deep-merges those overrides on top of the base training config.

Usage
-----
    from config.experiment_loader import load_experiment_cfg, save_experiment_cfg

    cfg = load_experiment_cfg("exp03_lr_0003")
    # cfg["classification"]["learning_rate"] == 0.0003
"""

from __future__ import annotations

import copy
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

_ENGINE_ROOT = Path(__file__).parent.parent
_EXPERIMENTS_DIR = _ENGINE_ROOT / "weights" / "experiments"


def _deep_merge(base: Dict, overrides: Dict) -> Dict:
    """Recursively merge *overrides* into a copy of *base*."""
    result = copy.deepcopy(base)
    for key, val in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def get_experiment_dir(experiment_name: str) -> Path:
    return _EXPERIMENTS_DIR / experiment_name


def load_experiment_cfg(
    experiment_name: str,
    base_cfg: Optional[Dict] = None,
) -> Dict:
    """
    Load base training config and apply experiment overrides.

    Parameters
    ----------
    experiment_name : str   e.g. "exp03_lr_0003"
    base_cfg        : dict  if None, loads from settings.py

    Returns
    -------
    Merged config dict
    """
    if base_cfg is None:
        import sys
        sys.path.insert(0, str(_ENGINE_ROOT))
        from config.settings import get_training_cfg
        base_cfg = get_training_cfg()

    exp_dir = get_experiment_dir(experiment_name)
    override_path = exp_dir / "experiment_config.yaml"

    if not override_path.exists():
        # No overrides — use base config unmodified
        return copy.deepcopy(base_cfg)

    with open(override_path, "r", encoding="utf-8") as f:
        overrides = yaml.safe_load(f) or {}

    merged = _deep_merge(base_cfg, overrides)
    return merged


def save_experiment_cfg(
    experiment_name: str,
    cfg: Dict,
    extra_meta: Optional[Dict] = None,
) -> Path:
    """
    Persist the merged config (+ optional metadata) into the experiment dir.

    Returns path to the saved file.
    """
    exp_dir = get_experiment_dir(experiment_name)
    exp_dir.mkdir(parents=True, exist_ok=True)

    saved = copy.deepcopy(cfg)
    if extra_meta:
        saved["_experiment_meta"] = extra_meta

    out_path = exp_dir / "experiment_config_resolved.yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(saved, f, default_flow_style=False, sort_keys=False)

    return out_path


def register_experiment(
    experiment_id: str,
    name: str,
    status: str = "implemented",
) -> None:
    """
    Upsert an entry in outputs/experiments/experiment_registry.json.
    """
    import json

    registry_path = _ENGINE_ROOT.parent / "outputs" / "experiments" / "experiment_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    registry: list = []
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)

    # Find or create entry
    entry = next((e for e in registry if e.get("experiment_id") == experiment_id), None)
    if entry is None:
        entry = {}
        registry.append(entry)

    entry.update({
        "experiment_id": experiment_id,
        "name": name,
        "status": status,
        "training_completed": entry.get("training_completed", False),
        "internal_evaluation_completed": entry.get("internal_evaluation_completed", False),
        "external_evaluation_completed": entry.get("external_evaluation_completed", False),
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
    })

    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
