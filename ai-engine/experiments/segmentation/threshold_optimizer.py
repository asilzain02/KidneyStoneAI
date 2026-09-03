"""
threshold_optimizer.py — Inference only experiment (EXP09).
Evaluates multiple thresholds on the validation set, then applies best to test set.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any

_HERE = Path(__file__).resolve()
_ENGINE_ROOT = _HERE.parents[2]
if str(_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_ENGINE_ROOT))

from experiments.segmentation.experiment_comparison import update_experiment_results
from evaluation.segmentation.segmentation_evaluator import evaluate
from utils.logger import get_logger

log = get_logger("threshold_optimizer")

THRESHOLDS_TO_TEST = [0.3, 0.4, 0.5, 0.6, 0.7]

def run_threshold_optimization(exp_id: str, cfg: Dict[str, Any]):
    """
    Finds the optimal threshold on validation data.
    Evaluates final performance strictly on the untouched test split.
    Uses the Baseline checkpoint, without retraining.
    """
    log.info("Starting threshold optimization (EXP09_THRESHOLD)")

    weights_root = Path(cfg["experiment"]["weights_root"])
   # weights_root = Path(cfg["weights"])
    baseline_weights = weights_root / "EXP00_BASELINE" / "latest_checkpoint.pth"

    if not baseline_weights.exists():
        log.error("Baseline weights missing. You must run EXP00_BASELINE first.", path=str(baseline_weights))
        return

    splits_dir = Path(cfg["splits"]["output_dir"])
    val_csv = splits_dir / "val.csv"
    test_csv = splits_dir / "test.csv"
    
    outputs_root = Path(cfg["experiment"]["outputs_root"])
    exp_dir = outputs_root / "experiments" / exp_id
    
    best_threshold = 0.5
    best_dice = -1.0
    
    log.info("Phase 1: Validating thresholds on Validation set")
    for t in THRESHOLDS_TO_TEST:
        log.info(f"Evaluating threshold: {t}")
        # Evaluate on VAL using memory-intensive evaluate.
        # We temporarily override output_dir into a trash dir if we don't want to save outputs
        # But for correctness, it's fine to save them under exp_dir / "val_search"
        search_dir = exp_dir / "val_search" / f"thresh_{t}"
        search_dir.mkdir(parents=True, exist_ok=True)
        
        # Override config dynamically for this run
        cfg["evaluation"]["threshold"] = t
        cfg["visualization"]["enabled"] = False # Don't visualize tuning
        
        # We must load the evaluator cleanly
        from config.settings import get_paths_cfg
        report = evaluate(
            checkpoint_path=baseline_weights,
            cfg=cfg,
            paths=get_paths_cfg(),
            split="val",
            output_dir=search_dir,
            threshold=t
        )
        
        current_dice = report.get("aggregate_metrics", {}).get("mean_dice", 0)
        # fallback for old structure
        if "metrics" in report and "macro_avg" in report["metrics"]:
             current_dice = report["metrics"]["macro_avg"].get("dice", 0)
        log.info(f"Threshold {t}: Validation Dice = {current_dice:.4f}")
        
        if current_dice > best_dice:
            best_dice = current_dice
            best_threshold = t
            
    log.info(f"Optimization complete. Best threshold is {best_threshold} (Val Dice: {best_dice:.4f})")
    
    # Run Phase 2: TEST set (untouched)
    log.info("Phase 2: Final Test split evaluation using selected threshold")
    
    cfg["evaluation"]["threshold"] = best_threshold
    cfg["visualization"]["enabled"] = True
    test_out = exp_dir / "test_results"
    test_out.mkdir(parents=True, exist_ok=True)
    
    final_report = evaluate(
        checkpoint_path=baseline_weights,
        cfg=cfg,
        paths=get_paths_cfg(),
        split="test",
        output_dir=test_out,
        threshold=best_threshold
    )
    
    final_metrics = final_report.get("aggregate_metrics", {})
    if "metrics" in final_report and "macro_avg" in final_report["metrics"]:
         final_metrics = final_report["metrics"]["macro_avg"]
    
    # Store results dynamically
    update_experiment_results(
        exp_id=exp_id,
        metrics=final_metrics,
        training_meta={"best_epoch": "Validation Selected", "training_time": "Inference Only", "parameter_count": "baseline"},
        outputs_root=outputs_root
    )
    
    log.info(f"Threshold optimization saved to {test_out}")
