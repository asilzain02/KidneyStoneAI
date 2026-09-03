"""
experiment_definitions.py — Central registry of hardcoded, controlled segmentation ablations.

Each experiment defines exactly ONE semantic parameter override off the baseline.
"""

from __future__ import annotations

from typing import Dict, List, Any

EXPERIMENTS: List[Dict[str, Any]] = [
    {
        "id": "EXP00_BASELINE",
        "name": "Baseline Segmentation",
        "category": "Baseline",
        "changed_parameter": None,
        "baseline_value": None,
        "experimental_value": None,
        "requires_training": True,
        "config_override": {}
    },
    {
        "id": "EXP01_LOSS_DICE_BCE",
        "name": "Loss Ablation (Dice + BCE)",
        "category": "Loss",
        "changed_parameter": "loss",
        "baseline_value": "dice_bce (weight 0.5/0.5)",
        "experimental_value": "dice_bce (weight 0.5/0.5 explicitly)",
        "requires_training": True,
        "config_override": {
            "loss": {
                "name": "dice_bce",
                "dice_weight": 0.5,
                "bce_weight": 0.5
            }
        }
    },
    {
        "id": "EXP02_LOSS_TVERSKY",
        "name": "Loss Ablation (Tversky)",
        "category": "Loss",
        "changed_parameter": "loss",
        "baseline_value": "dice_bce",
        "experimental_value": "tversky",
        "requires_training": True,
        "config_override": {
            "loss": {
                "name": "tversky",
                "alpha": 0.5,
                "beta": 0.5
            }
        }
    },
    {
        "id": "EXP03_LEARNING_RATE",
        "name": "Learning Rate Ablation",
        "category": "Optimization",
        "changed_parameter": "training.learning_rate",
        "baseline_value": 0.0001,
        "experimental_value": 0.001,
        "requires_training": True,
        "config_override": {
            "training": {
                "learning_rate": 0.001
            }
        }
    },
    {
        "id": "EXP04_AUGMENTATION",
        "name": "Data Augmentation Ablation",
        "category": "Data",
        "changed_parameter": "augmentation",
        "baseline_value": "baseline augmentation",
        "experimental_value": "heavy augmentation",
        "requires_training": True,
        "config_override": {
            "augmentation": {
                "horizontal_flip_prob": 0.5,
                "vertical_flip_prob": 0.5,
                "rotation_degrees": 25,
                "brightness_range": [0.6, 1.4],
                "contrast_range": [0.6, 1.4]
            }
        }
    },
    {
        "id": "EXP05_INPUT_RESOLUTION",
        "name": "Input Resolution Ablation",
        "category": "Architecture",
        "changed_parameter": "input.size",
        "baseline_value": 256,
        "experimental_value": 512,
        "requires_training": True,
        "config_override": {
            "input": {
                "size": 512
            }
        }
    },
    {
        "id": "EXP06_NORMALIZATION",
        "name": "Normalization Ablation",
        "category": "Preprocessing",
        "changed_parameter": "preprocessing.normalization",
        "baseline_value": "min_max",
        "experimental_value": "z_score",
        "requires_training": True,
        "config_override": {
            "preprocessing": {
                "normalization": "z_score"
            }
        }
    },
    {
        "id": "EXP07_BATCH_SIZE",
        "name": "Batch Size Ablation",
        "category": "Optimization",
        "changed_parameter": "training.batch_size",
        "baseline_value": 8,
        "experimental_value": 16,
        "requires_training": True,
        "config_override": {
            "training": {
                "batch_size": 16
            }
        }
    },
    {
        "id": "EXP08_SCHEDULER",
        "name": "Scheduler Ablation",
        "category": "Optimization",
        "changed_parameter": "training.scheduler",
        "baseline_value": "reduce_on_plateau",
        "experimental_value": "cosine_annealing",
        "requires_training": True,
        "config_override": {
            "training": {
                "scheduler": "cosine_annealing"
            }
        }
    },
    {
        "id": "EXP09_THRESHOLD",
        "name": "Threshold Optimization",
        "category": "Inference",
        "changed_parameter": "evaluation.threshold",
        "baseline_value": 0.5,
        "experimental_value": "dynamic sweep [0.3 - 0.7]",
        "requires_training": False,
        "config_override": {}
    },
    {
        "id": "EXP10_POSTPROCESSING",
        "name": "Morphological Post-processing Filter",
        "category": "Inference",
        "changed_parameter": "inference.postprocessing",
        "baseline_value": "none",
        "experimental_value": "connected component area thresholding",
        "requires_training": False,
        "config_override": {}
    },
    {
        "id": "EXP11_ENCODER",
        "name": "Encoder / Backbone Setup",
        "category": "Architecture",
        "changed_parameter": "model.encoder",
        "baseline_value": "none (train from scratch)",
        "experimental_value": "pretrained resnet34 or efficientnet",
        "requires_training": True,
        "config_override": {
            "model": {
                "encoder": "resnet34",
                "pretrained": True
            }
        }
    },
    {
        "id": "EXP12_ARCHITECTURE",
        "name": "Segmentation Architecture Ablation",
        "category": "Architecture",
        "changed_parameter": "model.name",
        "baseline_value": "unet",
        "experimental_value": "unetplusplus",
        "requires_training": True,
        "config_override": {
            "model": {
                "name": "unetplusplus"
            }
        }
    },
    {
        "id": "EXP13_ERROR_ANALYSIS",
        "name": "Error Analysis Visualization",
        "category": "Analysis",
        "changed_parameter": "analysis mode",
        "baseline_value": "none",
        "experimental_value": "error_analysis_report",
        "requires_training": False,
        "config_override": {}
    },
    {
        "id": "EXP14_SMALL_STONE_ANALYSIS",
        "name": "Small Stone Performance Analysis",
        "category": "Analysis",
        "changed_parameter": "analysis mode",
        "baseline_value": "none",
        "experimental_value": "size_stratified_evaluation",
        "requires_training": False,
        "config_override": {}
    },
    {
        "id": "EXP15_2_5D",
        "name": "2.5D Multi-slice Adjoining Input",
        "category": "Architecture/Data",
        "changed_parameter": "model.in_channels / dataset slices",
        "baseline_value": 1,
        "experimental_value": 3,
        "requires_training": True,
        "config_override": {
            "model": {
                "in_channels": 3
            },
            "dataset": {
                "slices_per_sample": 3
            }
        }
    }
]

def get_experiment_definition(exp_id: str) -> Dict[str, Any]:
    for exp in EXPERIMENTS:
        if exp["id"] == exp_id:
            return exp
    raise ValueError(f"Unknown experiment ID: {exp_id}")
