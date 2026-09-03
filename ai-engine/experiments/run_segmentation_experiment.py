# """
# run_segmentation_experiment.py — Main manual entry point for segmentation ablation experiments.

# Execute a selected experiment with strictly validated configuration isolation.
# """

# from __future__ import annotations

# import argparse
# import subprocess
# import sys
# from pathlib import Path
# import json

# _HERE = Path(__file__).resolve()
# _ENGINE_ROOT = _HERE.parents[1]
# _PROJECT_ROOT = _ENGINE_ROOT.parent
# sys.path.insert(0, str(_ENGINE_ROOT))

# from utils.logger import get_logger
# from experiments.segmentation.experiment_config import (
#     load_baseline_yaml,
#     apply_experiment_config,
#     save_expanded_config
# )
# from experiments.segmentation.experiment_definitions import get_experiment_definition

# log = get_logger("run_experiment")

# # ==============================================================================
# # MANUALLY SELECT EXPERIMENT HERE (Used if no CLI flag provided)
# # ==============================================================================
# EXPERIMENT = "EXP00_BASELINE"


# def _run_training(exp_id: str, final_cfg: dict, config_path: Path, smoke: bool = False):
#     """Delegate explicitly to train_segmentation.py to guarantee isolation."""
#     log.info("Starting training process", experiment=exp_id)
#     cmd = [
#         sys.executable,
#         str(_ENGINE_ROOT / "training" / "train_segmentation.py"),
#         "--experiment", exp_id,
#         "--config", str(config_path)
#     ]
#     if smoke:
#         cmd.append("--smoke")
    
#     try:
#          subprocess.run(cmd, check=True)
#     except subprocess.CalledProcessError as e:
#          log.error(f"Training failed with exit code {e.returncode}. Isolation boundary intact.")
#          sys.exit(e.returncode)
         
#     # After successful training, we automatically evaluate on the TEST set
#     log.info("Training complete. Evaluating on TEST set.", experiment=exp_id)
#     from evaluation.segmentation.segmentation_evaluator import evaluate
#     from experiments.segmentation.experiment_comparison import update_experiment_results
#     from config.settings import get_paths_cfg
    
#     weights_root = Path(final_cfg["experiment"]["weights_root"])
#     best_weights = weights_root / exp_id / "best_model.pth"
    
#     outputs_root = Path(final_cfg["experiment"]["outputs_root"])
#     exp_dir = outputs_root / "experiments" / exp_id
#     test_out = exp_dir / "test_results"
#     test_out.mkdir(parents=True, exist_ok=True)
    
#     if not best_weights.exists():
#         log.warning("Best weights not found, skipping final test evaluation.")
#         return
        
#     final_report = evaluate(
#         checkpoint_path=best_weights,
#         cfg=final_cfg,
#         paths=get_paths_cfg(),
#         split="test",
#         output_dir=test_out,
#         num_samples=20
#     )
    
#     final_metrics = final_report["metrics"]["macro_avg"]
    
#     update_experiment_results(
#         exp_id=exp_id,
#         metrics=final_metrics,
#         training_meta={"best_epoch": "Auto", "training_time": "Logged in train logs", "parameter_count": "See model logs"},
#         outputs_root=outputs_root
#     )


# def _run_inference(exp_id: str, cfg: dict):
#     """Delegate inference-only experiments."""
#     log.info("Starting inference-only experiment mode", experiment=exp_id)
    
#     # Baseline checkpoints are loaded relative to output roots.
#     # We map specific IDs to specific downstream evaluators.
    
#     if exp_id == "EXP09_THRESHOLD":
#         from experiments.segmentation.threshold_optimizer import run_threshold_optimization
#         run_threshold_optimization(exp_id, cfg)
        
#     elif exp_id == "EXP10_POSTPROCESSING":
#         # Placeholder for postprocessing
#         log.info("Post-processing optimization not fully implemented yet.", stub_for=exp_id)
        
#     elif exp_id in ["EXP13_ERROR_ANALYSIS", "EXP14_SMALL_STONE_ANALYSIS"]:
#         from experiments.segmentation.error_analysis import run_error_analysis
#         run_error_analysis(exp_id, cfg)
        
#     else:
#         raise NotImplementedError(f"Inference pipeline for {exp_id} is missing.")


# def parse_args():
#     p = argparse.ArgumentParser("Segment Ablation Framework Runner")
#     p.add_argument("--experiment", type=str, default=None,
#                    help="Override the hardcoded EXPERIMENT constant")
#     p.add_argument("--smoke", action="store_true", help="Run with smoke test config.")
#     return p.parse_args()


# def main():
#     args = parse_args()
#     exp_id = args.experiment if args.experiment else EXPERIMENT
    
#     print(f"\nInitializing Experiment Engine for: {exp_id}\n")
    
#     # 1. Load baseline
#     baseline_cfg = load_baseline_yaml()
    
#     # 2. Extract and Validate the Delta safely
#     try:
#         final_cfg = apply_experiment_config(baseline_cfg, exp_id)
#     except Exception as e:
#         log.error("Failed to apply experiment config safely", error=str(e))
#         sys.exit(1)
        
#     # 3. Save effective config isolated
#     outputs_root = _PROJECT_ROOT / final_cfg.get("experiment", {}).get("outputs_root", "outputs/segmentation")
#     exp_dir = outputs_root / "experiments" / exp_id
#     exp_dir.mkdir(parents=True, exist_ok=True)
    
#     config_path = exp_dir / "effective_config.yaml"
#     save_expanded_config(final_cfg, config_path)
    
#     # Write experiment metadataset as JSON for comparison builder
#     meta_path = exp_dir / "experiment_meta.json"
#     exp_def = get_experiment_definition(exp_id)
#     with open(meta_path, "w", encoding="utf-8") as f:
#         json.dump(exp_def, f, indent=4)
    
#     # 4. Route Execution explicitly preserving Baseline state
#     if exp_def["requires_training"]:
#         _run_training(exp_id, final_cfg, config_path, smoke=args.smoke)
#     else:
#         _run_inference(exp_id, final_cfg)
        
#     log.info("Experiment workflow completed successfully.", experiment=exp_id)


# if __name__ == "__main__":
#     main()


"""
run_segmentation_experiment.py — Main manual entry point for segmentation ablation experiments.

Execute a selected experiment with strictly validated configuration isolation.

Supports:
    --experiment EXP_ID
    --smoke
    --resume

Example:
    python ai-engine/experiments/run_segmentation_experiment.py \
        --experiment EXP05_INPUT_RESOLUTION \
        --resume
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# ==============================================================================
# PATH SETUP
# ==============================================================================

_HERE = Path(__file__).resolve()
_ENGINE_ROOT = _HERE.parents[1]
_PROJECT_ROOT = _ENGINE_ROOT.parent

sys.path.insert(0, str(_ENGINE_ROOT))


# ==============================================================================
# PROJECT IMPORTS
# ==============================================================================

from utils.logger import get_logger

from experiments.segmentation.experiment_config import (
    load_baseline_yaml,
    apply_experiment_config,
    save_expanded_config,
)

from experiments.segmentation.experiment_definitions import (
    get_experiment_definition,
)


log = get_logger("run_experiment")


# ==============================================================================
# MANUALLY SELECT EXPERIMENT HERE
# ==============================================================================

# Used when --experiment is NOT provided.
EXPERIMENT = "EXP00_BASELINE"


# ==============================================================================
# TRAINING
# ==============================================================================

def _run_training(
    exp_id: str,
    final_cfg: dict,
    config_path: Path,
    smoke: bool = False,
    resume: bool = False,
):
    """
    Delegate training explicitly to train_segmentation.py.

    Isolation guarantees:
        - Experiment receives its own effective_config.yaml
        - Experiment receives its own weights directory
        - Resume only uses the selected experiment checkpoint
        - No other experiment checkpoint is touched
    """

    log.info(
        "Starting training process",
        experiment=exp_id,
        resume=resume,
    )

    # --------------------------------------------------------------------------
    # BUILD TRAINING COMMAND
    # --------------------------------------------------------------------------

    cmd = [
        sys.executable,
        str(_ENGINE_ROOT / "training" / "train_segmentation.py"),
        "--experiment",
        exp_id,
        "--config",
        str(config_path),
    ]

    # --------------------------------------------------------------------------
    # SMOKE TEST
    # --------------------------------------------------------------------------

    if smoke:
        cmd.append("--smoke")

        log.info(
            "Smoke test mode enabled",
            experiment=exp_id,
        )

    # --------------------------------------------------------------------------
    # RESUME
    # --------------------------------------------------------------------------

    if resume:

        weights_root = Path(
            final_cfg["experiment"]["weights_root"]
        )

        resume_checkpoint = (
            weights_root
            / exp_id
            / "latest_checkpoint.pth"
        )

        log.info(
            "Resume requested",
            experiment=exp_id,
            checkpoint=str(resume_checkpoint),
        )

        # ----------------------------------------------------------------------
        # CHECKPOINT MUST EXIST
        # ----------------------------------------------------------------------

        # if not resume_checkpoint.exists():

        #     log.error(
        #         "Resume checkpoint not found",
        #         experiment=exp_id,
        #         path=str(resume_checkpoint),
        #     )

        #     print("\n" + "=" * 60)
        #     print("RESUME CHECKPOINT NOT FOUND")
        #     print("=" * 60)
        #     print(f"Experiment : {exp_id}")
        #     print(f"Expected   : {resume_checkpoint}")
        #     print("=" * 60)
        #     print(
        #         "\nRun the experiment normally first so that "
        #         "latest_checkpoint.pth is created."
        #     )

        #     sys.exit(1)

        # log.info(
        #     "Resume checkpoint found",
        #     experiment=exp_id,
        #     checkpoint=str(resume_checkpoint),
        # )

        # # train_segmentation.py must support --resume
        # cmd.append("--resume")

        if resume:
            checkpoint_path = (
                _ENGINE_ROOT.parent
                / "ai-engine"
                / "weights"
                / exp_id
                / "latest_checkpoint.pth"
            )

            if not checkpoint_path.exists():
                log.error(
                    "Resume checkpoint not found",
                    experiment=exp_id,
                    checkpoint=str(checkpoint_path)
                )
                sys.exit(1)

            log.info(
                "Resume checkpoint found",
                experiment=exp_id,
                checkpoint=str(checkpoint_path)
            )

            cmd.extend([
                "--resume",
                str(checkpoint_path)
            ])

    # --------------------------------------------------------------------------
    # DISPLAY COMMAND
    # --------------------------------------------------------------------------

    print("\n" + "=" * 60)
    print("TRAINING COMMAND")
    print("=" * 60)

    print(" ".join(f'"{x}"' if " " in x else x for x in cmd))

    print("=" * 60 + "\n")

    # --------------------------------------------------------------------------
    # START TRAINING
    # --------------------------------------------------------------------------

    try:

        subprocess.run(
            cmd,
            check=True,
        )

    except subprocess.CalledProcessError as e:

        log.error(
            f"Training failed with exit code {e.returncode}. "
            "Isolation boundary intact.",
            experiment=exp_id,
        )

        sys.exit(e.returncode)

    # ==========================================================================
    # TEST EVALUATION
    # ==========================================================================

    log.info(
        "Training complete. Evaluating on TEST set.",
        experiment=exp_id,
    )

    from evaluation.segmentation.segmentation_evaluator import (
        evaluate,
    )

    from experiments.segmentation.experiment_comparison import (
        update_experiment_results,
    )

    from config.settings import (
        get_paths_cfg,
    )

    # --------------------------------------------------------------------------
    # BEST MODEL
    # --------------------------------------------------------------------------

    weights_root = Path(
        final_cfg["experiment"]["weights_root"]
    )

    best_weights = (
        weights_root
        / exp_id
        / "best_model.pth"
    )

    # --------------------------------------------------------------------------
    # OUTPUT DIRECTORY
    # --------------------------------------------------------------------------

    outputs_root = Path(
        final_cfg["experiment"]["outputs_root"]
    )

    exp_dir = (
        outputs_root
        / "experiments"
        / exp_id
    )

    test_out = exp_dir / "test_results"

    test_out.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------------------------
    # CHECK BEST MODEL
    # --------------------------------------------------------------------------

    if not best_weights.exists():

        log.warning(
            "Best weights not found, skipping final test evaluation.",
            experiment=exp_id,
            path=str(best_weights),
        )

        return

    # --------------------------------------------------------------------------
    # EVALUATE
    # --------------------------------------------------------------------------

    final_report = evaluate(
        checkpoint_path=best_weights,
        cfg=final_cfg,
        paths=get_paths_cfg(),
        split="test",
        output_dir=test_out,
        num_samples=20,
    )

    # --------------------------------------------------------------------------
    # EXTRACT METRICS
    # --------------------------------------------------------------------------

    final_metrics = (
        final_report["metrics"]["macro_avg"]
    )

    # --------------------------------------------------------------------------
    # UPDATE EXPERIMENT RESULTS
    # --------------------------------------------------------------------------

    update_experiment_results(
        exp_id=exp_id,
        metrics=final_metrics,
        training_meta={
            "best_epoch": "Auto",
            "training_time": "Logged in train logs",
            "parameter_count": "See model logs",
        },
        outputs_root=outputs_root,
    )

    log.info(
        "Test evaluation completed",
        experiment=exp_id,
        output_dir=str(test_out),
    )


# ==============================================================================
# INFERENCE-ONLY EXPERIMENTS
# ==============================================================================

def _run_inference(
    exp_id: str,
    cfg: dict,
):
    """
    Delegate inference-only experiments.
    """

    log.info(
        "Starting inference-only experiment mode",
        experiment=exp_id,
    )

    # --------------------------------------------------------------------------
    # EXP09 — THRESHOLD OPTIMIZATION
    # --------------------------------------------------------------------------

    if exp_id == "EXP09_THRESHOLD":

        from experiments.segmentation.threshold_optimizer import (
            run_threshold_optimization,
        )

        run_threshold_optimization(
            exp_id,
            cfg,
        )

    # --------------------------------------------------------------------------
    # EXP10 — POST PROCESSING
    # --------------------------------------------------------------------------

    elif exp_id == "EXP10_POSTPROCESSING":

        log.info(
            "Post-processing optimization not fully implemented yet.",
            stub_for=exp_id,
        )

    # --------------------------------------------------------------------------
    # EXP13 / EXP14 — ERROR ANALYSIS
    # --------------------------------------------------------------------------

    elif exp_id in [
        "EXP13_ERROR_ANALYSIS",
        "EXP14_SMALL_STONE_ANALYSIS",
    ]:

        from experiments.segmentation.error_analysis import (
            run_error_analysis,
        )

        run_error_analysis(
            exp_id,
            cfg,
        )

    # --------------------------------------------------------------------------
    # UNKNOWN INFERENCE EXPERIMENT
    # --------------------------------------------------------------------------

    else:

        raise NotImplementedError(
            f"Inference pipeline for {exp_id} is missing."
        )


# ==============================================================================
# ARGUMENT PARSER
# ==============================================================================

def parse_args():

    p = argparse.ArgumentParser(
        "Segment Ablation Framework Runner"
    )

    # --------------------------------------------------------------------------
    # EXPERIMENT
    # --------------------------------------------------------------------------

    p.add_argument(
        "--experiment",
        type=str,
        default=None,
        help=(
            "Override the hardcoded EXPERIMENT constant."
        ),
    )

    # --------------------------------------------------------------------------
    # SMOKE TEST
    # --------------------------------------------------------------------------

    p.add_argument(
        "--smoke",
        action="store_true",
        help=(
            "Run with smoke-test configuration."
        ),
    )

    # --------------------------------------------------------------------------
    # RESUME
    # --------------------------------------------------------------------------

    p.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume training from the selected "
            "experiment's latest_checkpoint.pth."
        ),
    )

    return p.parse_args()


# ==============================================================================
# MAIN
# ==============================================================================

def main():

    args = parse_args()

    # --------------------------------------------------------------------------
    # SELECT EXPERIMENT
    # --------------------------------------------------------------------------

    exp_id = (
        args.experiment
        if args.experiment
        else EXPERIMENT
    )

    print(
        f"\nInitializing Experiment Engine for: {exp_id}\n"
    )

    # ==========================================================================
    # 1. LOAD BASELINE
    # ==========================================================================

    baseline_cfg = load_baseline_yaml()

    # ==========================================================================
    # 2. APPLY EXPERIMENT OVERRIDE
    # ==========================================================================

    try:

        final_cfg = apply_experiment_config(
            baseline_cfg,
            exp_id,
        )

    except Exception as e:

        log.error(
            "Failed to apply experiment config safely",
            experiment=exp_id,
            error=str(e),
        )

        sys.exit(1)

    # ==========================================================================
    # 3. CREATE ISOLATED EXPERIMENT DIRECTORY
    # ==========================================================================

    outputs_root = _PROJECT_ROOT / (
        final_cfg
        .get("experiment", {})
        .get(
            "outputs_root",
            "outputs/segmentation",
        )
    )

    exp_dir = (
        outputs_root
        / "experiments"
        / exp_id
    )

    exp_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ==========================================================================
    # 4. SAVE EFFECTIVE CONFIG
    # ==========================================================================

    config_path = (
        exp_dir
        / "effective_config.yaml"
    )

    save_expanded_config(
        final_cfg,
        config_path,
    )

    # ==========================================================================
    # 5. SAVE EXPERIMENT METADATA
    # ==========================================================================

    meta_path = (
        exp_dir
        / "experiment_meta.json"
    )

    exp_def = get_experiment_definition(
        exp_id
    )

    with open(
        meta_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            exp_def,
            f,
            indent=4,
        )

    # ==========================================================================
    # 6. DISPLAY EXPERIMENT MODE
    # ==========================================================================

    print("=" * 60)
    print("EXPERIMENT EXECUTION")
    print("=" * 60)

    print(f"Experiment : {exp_id}")
    print(
        f"Training   : "
        f"{exp_def['requires_training']}"
    )
    print(
        f"Resume     : "
        f"{args.resume}"
    )
    print(
        f"Smoke      : "
        f"{args.smoke}"
    )
    print(
        f"Config     : "
        f"{config_path}"
    )

    print("=" * 60)

    # ==========================================================================
    # 7. VALIDATE RESUME USAGE
    # ==========================================================================

    if args.resume and not exp_def["requires_training"]:

        log.error(
            "--resume can only be used with training experiments.",
            experiment=exp_id,
        )

        print(
            "\nERROR: --resume cannot be used with "
            "an inference-only experiment."
        )

        sys.exit(1)

    # ==========================================================================
    # 8. ROUTE EXECUTION
    # ==========================================================================

    if exp_def["requires_training"]:

        _run_training(
            exp_id=exp_id,
            final_cfg=final_cfg,
            config_path=config_path,
            smoke=args.smoke,
            resume=args.resume,
        )

    else:

        _run_inference(
            exp_id=exp_id,
            cfg=final_cfg,
        )

    # ==========================================================================
    # 9. COMPLETE
    # ==========================================================================

    log.info(
        "Experiment workflow completed successfully.",
        experiment=exp_id,
    )


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    main()