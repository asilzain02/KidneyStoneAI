"""
test_external_evaluation.py — Validating strictly the external mappings natively.
"""

from __future__ import annotations

import os
import pytest
from pathlib import Path

from evaluation.external_metrics import compute_external_binary_metrics
from evaluation.external_evaluator import map_four_class_to_binary
from datasets.external.axial_kidney_stone_adapter import AxialKidneyStoneAdapter

def test_map_four_class_to_binary():
    assert map_four_class_to_binary("Stone") == "STONE"
    assert map_four_class_to_binary("Normal") == "NON_STONE"
    assert map_four_class_to_binary("Cyst") == "NON_STONE"
    assert map_four_class_to_binary("Tumor") == "NON_STONE"

def test_adapter_rejects_augmented(tmp_path):
    root = tmp_path / "Augmented"
    root.mkdir()
    adapter = AxialKidneyStoneAdapter(root)
    
    with pytest.raises(ValueError) as excinfo:
        adapter._validate_structure()
        
    assert "CRITICAL ERROR: Refusing to evaluate against Augmented directory" in str(excinfo.value)

def test_adapter_valid_bounds(tmp_path):
    orig = tmp_path / "Original"
    (orig / "Stone").mkdir(parents=True)
    (orig / "Non-Stone").mkdir(parents=True)
    
    # Touch dummies
    (orig / "Stone" / "1.jpg").touch()
    (orig / "Non-Stone" / "2.png").touch()
    (orig / "Non-Stone" / "bad.txt").touch() # Unsupported
    
    adapter = AxialKidneyStoneAdapter(orig)
    
    # Just validate structure since `load_image_verified` mocks images realistically via binary
    adapter._validate_structure()
    
    assert adapter.stone_dir == orig / "Stone"
    assert adapter.non_stone_dir == orig / "Non-Stone"

def test_metric_calculation():
    # Synthetic inference loop dummy array
    y_true = ["STONE", "NON_STONE", "NON_STONE", "STONE"]
    y_pred = ["STONE", "NON_STONE", "STONE", "NON_STONE"]
    probs = [0.9, 0.1, 0.8, 0.2]
    
    metrics = compute_external_binary_metrics(y_true, y_pred, probs)
    
    assert metrics["accuracy"] == 0.5
    assert metrics["counts"]["TP"] == 1
    assert metrics["counts"]["TN"] == 1
    assert metrics["counts"]["FP"] == 1
    assert metrics["counts"]["FN"] == 1

def test_metric_calculation_missing():
    mt = compute_external_binary_metrics([], [], [])
    assert mt == {}
