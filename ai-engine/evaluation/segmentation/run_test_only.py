"""
run_test_only.py
================

Manual TEST-ONLY entry point for segmentation experiments.

Purpose:
    Evaluate an already-trained segmentation model without retraining.

Expected project structure:

KidneyStoneAI/
│
├── ai-engine/
│   ├── weights/
│   │   └── EXP02_LOSS_TVERSKY/
│   │       └── best_model.pth
│   │
│   └── evaluation/
│       └── segmentation/
│           ├── run_test_only.py
│           └── segmentation_evaluator.py
│
└── outputs/
    └── segmentation/
        └── experiments/
            └── EXP02_LOSS_TVERSKY/
                ├── effective_config.yaml
                └── test_results/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


# ==============================================================================
# PROJECT PATHS
# ==============================================================================

# This file:
#
# ai-engine/
#     evaluation/
#         segmentation/
#             run_test_only.py
#
# parents[0] = segmentation
# parents[1] = evaluation
# parents[2] = ai-engine
# parents[3] = KidneyStoneAI

HERE = Path(__file__).resolve()
ENGINE_ROOT = HERE.parents[2]
PROJECT_ROOT = HERE.parents[3]

# Make ai-engine importable
sys.path.insert(0, str(ENGINE_ROOT))


# ==============================================================================
# MANUALLY SELECT EXPERIMENT HERE
# ==============================================================================

EXP_ID = "EXP02_LOSS_TVERSKY"

# Number of test samples.
#
# None = evaluate the complete TEST set.
#
# For a quick smoke test:
# NUM_SAMPLES = 20
#
# For final evaluation:
NUM_SAMPLES = None


# ==============================================================================
# PATHS
# ==============================================================================

CONFIG_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "segmentation"
    / "experiments"
    / EXP_ID
    / "effective_config.yaml"
)

WEIGHTS_PATH = (
    ENGINE_ROOT
    / "weights"
    / EXP_ID
    / "best_model.pth"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "segmentation"
    / "experiments"
    / EXP_ID
    / "test_results"
)


# ==============================================================================
# IMPORTS
# ==============================================================================

from evaluation.segmentation.segmentation_evaluator import evaluate
from config.settings import get_paths_cfg


# ==============================================================================
# CONFIGURATION HELPERS
# ==============================================================================

def load_config() -> dict:
    """
    Load the exact effective configuration generated for this experiment.
    """

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "\n"
            "Effective configuration not found.\n"
            f"Expected:\n{CONFIG_PATH}\n\n"
            "Make sure the experiment was executed at least once and "
            "effective_config.yaml was generated."
        )

    print(f"Loading config:")
    print(f"  {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise ValueError(
            f"Invalid YAML configuration: {CONFIG_PATH}"
        )

    return cfg


def normalize_segmentation_config(cfg: dict) -> dict:
    """
    Make the configuration compatible with segmentation_evaluator.py.

    The evaluator expects:

        cfg["segmentation"]["input_size"]

    Some configurations may instead have segmentation parameters at
    another level. This function preserves the original configuration
    and only fills missing evaluator-required fields when possible.
    """

    # ------------------------------------------------------------------
    # Ensure segmentation section exists
    # ------------------------------------------------------------------

    if "segmentation" not in cfg or cfg["segmentation"] is None:
        cfg["segmentation"] = {}

    seg_cfg = cfg["segmentation"]

    if not isinstance(seg_cfg, dict):
        raise ValueError(
            "cfg['segmentation'] must be a dictionary."
        )

    # ------------------------------------------------------------------
    # input_size
    # ------------------------------------------------------------------

    if "input_size" not in seg_cfg:

        # Possible top-level location
        if "input_size" in cfg:
            seg_cfg["input_size"] = cfg["input_size"]

        # Possible image_size location
        elif "image_size" in cfg:
            seg_cfg["input_size"] = cfg["image_size"]

        # Possible data configuration
        elif (
            isinstance(cfg.get("data"), dict)
            and "input_size" in cfg["data"]
        ):
            seg_cfg["input_size"] = cfg["data"]["input_size"]

        # Possible dataset configuration
        elif (
            isinstance(cfg.get("dataset"), dict)
            and "input_size" in cfg["dataset"]
        ):
            seg_cfg["input_size"] = cfg["dataset"]["input_size"]

    # ------------------------------------------------------------------
    # Validate input_size
    # ------------------------------------------------------------------

    if "input_size" not in seg_cfg:
        raise KeyError(
            "\n"
            "Could not find segmentation.input_size.\n\n"
            "The evaluator requires:\n"
            "    cfg['segmentation']['input_size']\n\n"
            "Checked:\n"
            "    cfg['segmentation']['input_size']\n"
            "    cfg['input_size']\n"
            "    cfg['image_size']\n"
            "    cfg['data']['input_size']\n"
            "    cfg['dataset']['input_size']\n\n"
            f"Config file:\n{CONFIG_PATH}"
        )

    # ------------------------------------------------------------------
    # Loss compatibility
    #
    # This does not affect inference, but keeps the experiment config
    # structurally consistent.
    # ------------------------------------------------------------------

    if "loss" not in seg_cfg:

        if "loss" in cfg:
            seg_cfg["loss"] = cfg["loss"]

    return cfg


# ==============================================================================
# DISPLAY CONFIGURATION
# ==============================================================================

def print_experiment_information(cfg: dict) -> None:

    print()
    print("=" * 60)
    print("KIDNEY STONE SEGMENTATION — TEST ONLY")
    print("=" * 60)

    print(f"Experiment:")
    print(f"  {EXP_ID}")

    print()
    print("Checkpoint:")
    print(f"  {WEIGHTS_PATH}")

    print()
    print("Effective config:")
    print(f"  {CONFIG_PATH}")

    print()
    print("Output directory:")
    print(f"  {OUTPUT_DIR}")

    print()
    print("Input size:")
    print(f"  {cfg['segmentation']['input_size']}")

    print()
    print("Number of test samples:")
    print(f"  {'ALL' if NUM_SAMPLES is None else NUM_SAMPLES}")

    print("=" * 60)
    print()


# ==============================================================================
# MAIN TEST FUNCTION
# ==============================================================================

def run_test() -> dict:

    # ------------------------------------------------------------------
    # Validate checkpoint
    # ------------------------------------------------------------------

    if not WEIGHTS_PATH.exists():

        raise FileNotFoundError(
            "\n"
            "Trained model checkpoint not found.\n"
            f"Expected:\n{WEIGHTS_PATH}\n\n"
            "Make sure the experiment has been trained successfully."
        )

    # ------------------------------------------------------------------
    # Create output directory
    # ------------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ------------------------------------------------------------------
    # Load configuration
    # ------------------------------------------------------------------

    cfg = load_config()

    # ------------------------------------------------------------------
    # Normalize configuration
    # ------------------------------------------------------------------

    cfg = normalize_segmentation_config(cfg)

    # ------------------------------------------------------------------
    # Display information
    # ------------------------------------------------------------------

    print_experiment_information(cfg)

    # ------------------------------------------------------------------
    # Get project paths
    # ------------------------------------------------------------------

    paths = get_paths_cfg()

    # ------------------------------------------------------------------
    # Run TEST evaluation
    # ------------------------------------------------------------------

    print("Starting TEST evaluation...")
    print()

    report = evaluate(
        checkpoint_path=WEIGHTS_PATH,
        cfg=cfg,
        paths=paths,
        split="test",
        output_dir=OUTPUT_DIR,
        num_samples=NUM_SAMPLES,
    )

    # ------------------------------------------------------------------
    # Save complete report
    # ------------------------------------------------------------------

    report_path = OUTPUT_DIR / "test_report.json"

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            indent=4,
            default=str
        )

    # ------------------------------------------------------------------
    # Save test configuration copy
    #
    # This guarantees that the test result directory contains the
    # exact configuration used for evaluation.
    # ------------------------------------------------------------------

    test_config_path = OUTPUT_DIR / "test_config.yaml"

    with open(
        test_config_path,
        "w",
        encoding="utf-8"
    ) as f:

        yaml.safe_dump(
            cfg,
            f,
            sort_keys=False
        )

    # ------------------------------------------------------------------
    # Extract metrics
    # ------------------------------------------------------------------

    metrics = {}

    if isinstance(report, dict):

        if "metrics" in report:

            metrics = report["metrics"]

    # ------------------------------------------------------------------
    # Display results
    # ------------------------------------------------------------------

    print()
    print("=" * 60)
    print("TEST EVALUATION COMPLETE")
    print("=" * 60)

    print()
    print(f"Experiment:")
    print(f"  {EXP_ID}")

    print()
    print(f"Results saved to:")
    print(f"  {OUTPUT_DIR}")

    print()
    print(f"Test report:")
    print(f"  {report_path}")

    print()
    print(f"Test configuration:")
    print(f"  {test_config_path}")

    print()
    print("-" * 60)
    print("METRICS")
    print("-" * 60)

    if metrics:

        # Macro average is what your experiment runner previously used.
        macro = metrics.get("macro_avg")

        if isinstance(macro, dict):

            for name, value in macro.items():

                if isinstance(value, (int, float)):
                    print(
                        f"  {name:<20}: {value:.4f}"
                    )
                else:
                    print(
                        f"  {name:<20}: {value}"
                    )

        else:

            for name, value in metrics.items():

                if isinstance(value, (int, float)):
                    print(
                        f"  {name:<20}: {value:.4f}"
                    )
                else:
                    print(
                        f"  {name:<20}: {value}"
                    )

    else:

        print("  Metrics were returned in the evaluator report.")

    print()
    print("=" * 60)
    print()

    return report


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main():

    try:

        run_test()

    except KeyboardInterrupt:

        print()
        print("Test evaluation interrupted by user.")
        sys.exit(130)

    except Exception as e:

        print()
        print("=" * 60)
        print("TEST EVALUATION FAILED")
        print("=" * 60)
        print()
        print(f"Error: {type(e).__name__}")
        print(f"Message: {e}")
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()