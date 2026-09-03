"""
kssd2025_adapter.py — Shim re-exporting the KSSD2025 adapter.

The canonical implementation lives at:
    ai-engine/datasets/kssd2025_adapter.py

This module re-exports it unchanged so that code under
datasets/segmentation/kssd2025/ can import from the modular package
without code duplication.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure ai-engine root is importable
sys.path.insert(0, str(Path(__file__).parents[3]))

from datasets.kssd2025_adapter import KSSD2025DatasetAdapter  # noqa: F401

__all__ = ["KSSD2025DatasetAdapter"]
