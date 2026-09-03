"""
settings.py — Configuration loader for KidneyStoneAI AI Engine.

Loads training_config.yaml and paths_config.yaml.
Environment variables override path defaults.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml


# ── Module-level constants ────────────────────────────────────────────────────

_CONFIG_DIR = Path(__file__).parent
_TRAINING_CONFIG_PATH = _CONFIG_DIR / "training_config.yaml"
_PATHS_CONFIG_PATH = _CONFIG_DIR / "paths_config.yaml"

# ── ENV-var interpolation ─────────────────────────────────────────────────────

_ENV_PATTERN = re.compile(r"\$\{([^:}]+)(?::([^}]*))?\}")


def _interpolate(value: str) -> str:
    """Replace ${VAR_NAME:default} placeholders with env values."""
    def _replace(match: re.Match) -> str:
        var_name = match.group(1).strip()
        default = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(var_name, default)

    while _ENV_PATTERN.search(value):
        value = _ENV_PATTERN.sub(_replace, value)
    return value


def _resolve_values(obj: Any) -> Any:
    """Recursively interpolate env-var placeholders in a nested dict/list."""
    if isinstance(obj, dict):
        return {k: _resolve_values(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_values(v) for v in obj]
    if isinstance(obj, str):
        return _interpolate(obj)
    return obj


# ── Public loaders ────────────────────────────────────────────────────────────

def load_training_config() -> Dict[str, Any]:
    """Return the training configuration as a plain dict."""
    with open(_TRAINING_CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return _resolve_values(raw)


def load_paths_config() -> Dict[str, Any]:
    """Return the resolved path configuration as a plain dict."""
    with open(_PATHS_CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    # Two-pass resolution so ${data_root} inside other keys also resolves.
    resolved = _resolve_values(raw)
    return _resolve_values(resolved)


def get_training_cfg() -> Dict[str, Any]:
    return load_training_config()


def get_paths_cfg() -> Dict[str, Any]:
    return load_paths_config()
