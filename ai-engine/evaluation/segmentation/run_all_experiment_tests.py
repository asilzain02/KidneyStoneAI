"""
run_all_experiment_tests.py

FINAL TEST COMPARISON ONLY

This script DOES NOT:
    - train models
    - load models into GPU
    - run inference
    - regenerate test results

It ONLY:
    1. Scans experiment directories.
    2. Reads existing segmentation_results.json files.
    3. Extracts aggregate test metrics.
    4. Builds a comparison table.
    5. Ranks experiments by Dice.
    6. Saves final comparison JSON/CSV.
    7. Prints the best experiment.

Expected structure:

outputs/
└── segmentation/
    └── experiments/
        ├── EXP00_BASELINE/
        │   └── test_results/
        │       └── segmentation_results.json
        ├── EXP01_LOSS_DICE_BCE/
        │   └── test_results/
        │       └── segmentation_results.json
        ├── EXP02_LOSS_TVERSKY/
        │   └── test_results/
        │       └── segmentation_results.json
        └── ...

Run:

python ai-engine/evaluation/segmentation/run_all_experiment_tests.py
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# PATH SETUP
# =============================================================================

_HERE = Path(__file__).resolve()

# ai-engine/evaluation/segmentation/
_ENGINE_ROOT = _HERE.parents[2]

# Project root
_PROJECT_ROOT = _ENGINE_ROOT.parent

# Experiment output directory
EXPERIMENTS_ROOT = (
    _PROJECT_ROOT
    / "outputs"
    / "segmentation"
    / "experiments"
)


# =============================================================================
# EXPERIMENTS TO COMPARE
# =============================================================================
#
# Keep this list manually controlled.
#
# If you only want to compare completed experiments, list them here.
#
# Add/remove IDs as required.
# =============================================================================

EXPERIMENT_IDS = [
    "EXP00_BASELINE",
    "EXP01_LOSS_DICE_BCE",
    "EXP02_LOSS_TVERSKY",
    "EXP03_LEARNING_RATE",
    "EXP04_AUGMENTATION",
    "EXP05_INPUT_RESOLUTION",
    "EXP12_ARCHITECTURE",
]


# =============================================================================
# METRICS
# =============================================================================

METRIC_NAMES = [
    "dice",
    "iou",
    "precision",
    "recall",
    "sensitivity",
    "specificity",
    "f1",
    "pixel_accuracy",
]


# =============================================================================
# SAFE FLOAT CONVERSION
# =============================================================================

def safe_float(value: Any) -> Optional[float]:
    """
    Convert a value to float.

    Returns None for:
        - missing values
        - null
        - invalid strings
    """

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# =============================================================================
# EXTRACT METRICS
# =============================================================================

def extract_metrics(results: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Extract metrics from segmentation_evaluator.py output.

    Expected evaluator structure:

    {
        "aggregate_metrics": {
            "mean_dice": ...,
            "std_dice": ...,
            "mean_iou": ...,
            "std_iou": ...,
            "mean_precision": ...,
            "mean_recall": ...,
            "mean_sensitivity": ...,
            "mean_specificity": ...,
            "mean_f1": ...,
            "mean_pixel_accuracy": ...
        }
    }

    The evaluator creates scalar_metrics and stores them under
    "aggregate_metrics".
    """

    aggregate = results.get("aggregate_metrics", {})

    if not isinstance(aggregate, dict):
        aggregate = {}

    metrics = {}

    for metric in METRIC_NAMES:
        value = aggregate.get(f"mean_{metric}")

        metrics[metric] = safe_float(value)

    return metrics


# =============================================================================
# LOAD ONE EXPERIMENT
# =============================================================================

def load_experiment(exp_id: str) -> Dict[str, Any]:
    """
    Load existing test results for one experiment.

    IMPORTANT:
    This function never runs evaluation.
    """

    exp_dir = EXPERIMENTS_ROOT / exp_id
    test_dir = exp_dir / "test_results"

    results_path = test_dir / "segmentation_results.json"

    row = {
        "experiment": exp_id,
        "name": exp_id,
        "category": "Unknown",
        "changed_parameter": "",
        "experimental_value": "",
        "dice": None,
        "iou": None,
        "precision": None,
        "recall": None,
        "sensitivity": None,
        "specificity": None,
        "f1": None,
        "pixel_accuracy": None,
        "status": "MISSING",
        "results_file": str(results_path),
    }

    # -------------------------------------------------------------------------
    # Check experiment directory
    # -------------------------------------------------------------------------

    if not exp_dir.exists():
        row["status"] = "EXPERIMENT_DIR_MISSING"
        return row

    # -------------------------------------------------------------------------
    # Check test result
    # -------------------------------------------------------------------------

    if not results_path.exists():
        row["status"] = "TEST_RESULTS_MISSING"
        return row

    # -------------------------------------------------------------------------
    # Load JSON
    # -------------------------------------------------------------------------

    try:
        with open(results_path, "r", encoding="utf-8") as f:
            results = json.load(f)

    except Exception as exc:
        row["status"] = f"JSON_ERROR: {exc}"
        return row

    # -------------------------------------------------------------------------
    # Extract metadata
    # -------------------------------------------------------------------------

    row["name"] = results.get("name", exp_id)
    row["category"] = results.get("category", "Unknown")
    row["changed_parameter"] = results.get(
        "changed_parameter",
        "",
    )
    row["experimental_value"] = results.get(
        "experimental_value",
        "",
    )

    # -------------------------------------------------------------------------
    # Extract aggregate metrics
    # -------------------------------------------------------------------------

    metrics = extract_metrics(results)

    for metric, value in metrics.items():
        row[metric] = value

    # -------------------------------------------------------------------------
    # Determine status
    # -------------------------------------------------------------------------

    if metrics["dice"] is None:
        row["status"] = "METRICS_MISSING"
    else:
        row["status"] = "OK"

    return row


# =============================================================================
# LOAD ALL EXPERIMENTS
# =============================================================================

def load_all_experiments() -> List[Dict[str, Any]]:
    """
    Read all configured experiments.
    """

    rows = []

    print("\n" + "=" * 100)
    print("LOADING EXISTING TEST RESULTS")
    print("=" * 100)

    print(f"\nExperiment root:")
    print(EXPERIMENTS_ROOT)

    for exp_id in EXPERIMENT_IDS:

        row = load_experiment(exp_id)

        rows.append(row)

        if row["status"] == "OK":
            print(
                f"  [OK]      {exp_id:<28} "
                f"Dice={row['dice']:.4f}"
            )

        else:
            print(
                f"  [SKIP]    {exp_id:<28} "
                f"{row['status']}"
            )

    return rows


# =============================================================================
# RANK EXPERIMENTS
# =============================================================================

def rank_experiments(
    rows: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Rank only experiments that have valid Dice values.

    Higher Dice = better.
    """

    valid_rows = [
        row
        for row in rows
        if row.get("dice") is not None
    ]

    valid_rows.sort(
        key=lambda row: row["dice"],
        reverse=True,
    )

    for rank, row in enumerate(valid_rows, start=1):
        row["dice_rank"] = rank

    return valid_rows


# =============================================================================
# PRINT COMPARISON
# =============================================================================

def print_comparison(rows: List[Dict[str, Any]]) -> None:

    print("\n")
    print("=" * 120)
    print("FINAL TEST COMPARISON")
    print("=" * 120)

    if not rows:
        print("\nNo valid test results found.")
        return

    headers = [
        "Rank",
        "Experiment",
        "Dice",
        "IoU",
        "Precision",
        "Recall",
        "F1",
        "Specificity",
        "Pixel Acc",
    ]

    print(
        f"{headers[0]:<6}"
        f"{headers[1]:<30}"
        f"{headers[2]:>10}"
        f"{headers[3]:>10}"
        f"{headers[4]:>12}"
        f"{headers[5]:>10}"
        f"{headers[6]:>10}"
        f"{headers[7]:>14}"
        f"{headers[8]:>12}"
    )

    print("-" * 120)

    for row in rows:

        def fmt(value):
            if value is None:
                return "N/A"
            return f"{value:.4f}"

        print(
            f"{row['dice_rank']:<6}"
            f"{row['experiment']:<30}"
            f"{fmt(row['dice']):>10}"
            f"{fmt(row['iou']):>10}"
            f"{fmt(row['precision']):>12}"
            f"{fmt(row['recall']):>10}"
            f"{fmt(row['f1']):>10}"
            f"{fmt(row['specificity']):>14}"
            f"{fmt(row['pixel_accuracy']):>12}"
        )


# =============================================================================
# PRINT DETAILED RESULTS
# =============================================================================

def print_detailed_results(rows: List[Dict[str, Any]]) -> None:

    print("\n")
    print("=" * 100)
    print("DETAILED EXPERIMENT RESULTS")
    print("=" * 100)

    for row in rows:

        print("\n" + "-" * 100)

        print(f"Experiment          : {row['experiment']}")
        print(f"Name                 : {row['name']}")
        print(f"Category             : {row['category']}")
        print(f"Changed parameter    : {row['changed_parameter']}")
        print(f"Experimental value   : {row['experimental_value']}")

        print("\nMetrics:")

        for metric in METRIC_NAMES:

            value = row.get(metric)

            if value is None:
                print(f"  {metric:<20}: N/A")
            else:
                print(f"  {metric:<20}: {value:.4f}")


# =============================================================================
# BEST EXPERIMENT
# =============================================================================

def print_best_experiment(rows: List[Dict[str, Any]]) -> None:

    print("\n")
    print("=" * 100)
    print("BEST EXPERIMENT BY TEST DICE")
    print("=" * 100)

    if not rows:
        print("\nNo valid experiments available.")
        return

    best = rows[0]

    print(f"\nExperiment : {best['experiment']}")
    print(f"Name       : {best['name']}")
    print(f"Category   : {best['category']}")

    print("\nMetrics:")

    for metric in METRIC_NAMES:

        value = best.get(metric)

        if value is None:
            print(f"  {metric:<20}: N/A")
        else:
            print(f"  {metric:<20}: {value:.4f}")

    print("\n" + "=" * 100)


# =============================================================================
# SAVE JSON
# =============================================================================

def save_json(rows: List[Dict[str, Any]]) -> Path:

    output_path = EXPERIMENTS_ROOT / "FINAL_TEST_COMPARISON.json"

    payload = {
        "generated_at": datetime.now().isoformat(),
        "comparison_type": "existing_test_results_only",
        "ranking_metric": "dice",
        "higher_is_better": True,
        "experiments": rows,
    }

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            payload,
            f,
            indent=4,
            default=str,
        )

    return output_path


# =============================================================================
# SAVE CSV
# =============================================================================

def save_csv(rows: List[Dict[str, Any]]) -> Path:

    output_path = EXPERIMENTS_ROOT / "FINAL_TEST_COMPARISON.csv"

    fieldnames = [
        "dice_rank",
        "experiment",
        "name",
        "category",
        "changed_parameter",
        "experimental_value",
        "dice",
        "iou",
        "precision",
        "recall",
        "sensitivity",
        "specificity",
        "f1",
        "pixel_accuracy",
        "status",
        "results_file",
    ]

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        writer.writerows(rows)

    return output_path


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("\n")
    print("=" * 100)
    print("SEGMENTATION FINAL COMPARISON")
    print("=" * 100)

    print("\nMODE:")
    print("  Existing test results ONLY")
    print("  Training          : NO")
    print("  Inference         : NO")
    print("  GPU computation   : NO")
    print("  Checkpoints       : NOT MODIFIED")

    # -------------------------------------------------------------------------
    # Load
    # -------------------------------------------------------------------------

    all_rows = load_all_experiments()

    # -------------------------------------------------------------------------
    # Rank
    # -------------------------------------------------------------------------

    ranked_rows = rank_experiments(all_rows)

    # -------------------------------------------------------------------------
    # Print
    # -------------------------------------------------------------------------

    print_comparison(ranked_rows)

    print_detailed_results(ranked_rows)

    print_best_experiment(ranked_rows)

    # -------------------------------------------------------------------------
    # Save
    # -------------------------------------------------------------------------

    json_path = save_json(ranked_rows)
    csv_path = save_csv(ranked_rows)

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------

    print("\n")
    print("=" * 100)
    print("FINAL COMPARISON FILES")
    print("=" * 100)

    print(f"\nJSON:")
    print(f"  {json_path}")

    print(f"\nCSV:")
    print(f"  {csv_path}")

    print("\n")
    print("=" * 100)
    print("COMPARISON COMPLETE")
    print("=" * 100)
    print()


if __name__ == "__main__":
    main()