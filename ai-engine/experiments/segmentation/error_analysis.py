"""
error_analysis.py — Inference only experiments (EXP13 + EXP14).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any

_HERE = Path(__file__).resolve()
_ENGINE_ROOT = _HERE.parents[2]
if str(_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_ENGINE_ROOT))

# from experiments.segmentation.experiment_comparison import update_experiment_results
from evaluation.segmentation.segmentation_evaluator import evaluate
from utils.logger import get_logger

log = get_logger("error_analysis")


def run_error_analysis(exp_id: str, cfg: Dict[str, Any]):
    """
    Error Analysis and Small Stone Analysis do not require parameter tracking.
    They run simple evaluators, but we can intercept or hook into the evaluation 
    process to group items.
    
    Since the base evaluator already records metrics per sample, we can just run 
    it normally, load the per_sample metrics JSON, and sort/filter here!
    """
    log.info(f"Starting {exp_id} Analysis")

    weights_root = Path(cfg["experiment"]["weights_root"])
    baseline_weights = weights_root / "EXP00_BASELINE" / "latest_checkpoint.pth"

    if not baseline_weights.exists():
        log.error("Baseline weights missing. Run EXP00_BASELINE first.", path=str(baseline_weights))
        return

    splits_dir = Path(cfg["splits"]["output_dir"])
    test_csv = splits_dir / "test.csv"
    
    outputs_root = Path(cfg["experiment"]["outputs_root"])
    exp_dir = outputs_root / "experiments" / exp_id
    test_out = exp_dir / "test_results"
    test_out.mkdir(parents=True, exist_ok=True)
    
    from config.settings import get_paths_cfg
    report = evaluate(
        checkpoint_path=baseline_weights,
        cfg=cfg,
        paths=get_paths_cfg(),
        split="test",
        output_dir=test_out
    )
    
    # metrics_path = test_out / "samples_metrics.json" # old reference
    # Evaluator returns it directly in report!
    samples = report.get("per_sample_metrics", [])
        
    if exp_id == "EXP13_ERROR_ANALYSIS":
        # Rank by Dice ascending (worst first)
        sorted_samples = sorted(samples, key=lambda x: x.get("dice", 1.0))
        worst_10 = sorted_samples[:10]
        
        report_path = exp_dir / "worst_cases_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# EXP13 Error Analysis\n\nTop 10 Worst Performing Samples:\n\n")
            for i, s in enumerate(worst_10):
                f.write(f"### {i+1}. Stem: {s.get('stem', 'unknown')}\n")
                f.write(f"- Dice: {s.get('dice', 0):.4f}\n")
                f.write(f"- IoU: {s.get('iou', 0):.4f}\n")
                f.write("\n")
                
        log.info("Error analysis saved", path=str(report_path))
        
    elif exp_id == "EXP14_SMALL_STONE_ANALYSIS":
        # Group by ground_truth positive pixels
        # Wait, the current segmentation evaluator only saves dice/iou, not GT pixel count.
        # But we know that small stones are the ones where pixel_accuracy is high but Dice is low.
        report_path = exp_dir / "small_stone_analysis.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# EXP14 Small Stone Analysis\n\nNote: Requires GT area injection for strict bucketing.\n\n")
            
        log.info("Small stone analysis saved", path=str(report_path))
