"""
compare_experiments.py — Aggregate experiment results into a comparison table.

Reads from:
    ai-engine/weights/experiments/<exp>/experiment_config_resolved.yaml
    outputs/experiments/<exp>/classification_results.json   (internal evaluation)
    outputs/experiments/<exp>/external/external_results.json (external evaluation)

Generates:
    outputs/experiments/final_comparison.csv
    outputs/experiments/final_comparison.json

Usage
-----
    python ai-engine/evaluation/compare_experiments.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

_ENGINE_ROOT = Path(__file__).parent.parent
_PROJECT_ROOT = _ENGINE_ROOT.parent
_EXP_WEIGHTS  = _ENGINE_ROOT / "weights" / "experiments"
_EXP_OUTPUTS  = _PROJECT_ROOT / "outputs" / "experiments"

sys.path.insert(0, str(_ENGINE_ROOT))


def _load_json(path: Path) -> Optional[Dict]:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def _load_yaml(path: Path) -> Optional[Dict]:
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f)
    return None


def _get(d: Optional[Dict], *keys, default=None) -> Any:
    """Safe nested dict accessor."""
    if d is None:
        return default
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, None)
        if d is None:
            return default
    return d


def collect_experiment_rows() -> List[Dict]:
    rows = []

    if not _EXP_WEIGHTS.exists():
        return rows

    for exp_dir in sorted(_EXP_WEIGHTS.iterdir()):
        if not exp_dir.is_dir() or exp_dir.name == "smoke":
            continue

        # ── Config ────────────────────────────────────────────────────────────
        resolved_cfg = _load_yaml(exp_dir / "experiment_config_resolved.yaml")
        override_cfg = _load_yaml(exp_dir / "experiment_config.yaml")
        clf           = _get(resolved_cfg, "classification") or {}
        meta          = _get(resolved_cfg, "_experiment_meta") or {}
        exp_id        = _get(override_cfg, "_experiment", "id") or exp_dir.name

        # ── Internal evaluation ───────────────────────────────────────────────
        int_path = _EXP_OUTPUTS / exp_dir.name / "classification_results.json"
        int_res  = _load_json(int_path)

        int_acc       = _get(int_res, "accuracy")
        int_macro_f1  = _get(int_res, "macro_f1")
        int_wt_f1     = _get(int_res, "weighted_f1")
        int_roc_auc   = _get(int_res, "roc_auc_macro_ovr")
        int_stone_p   = _get(int_res, "stone_precision")
        int_stone_r   = _get(int_res, "stone_recall")
        int_stone_f1  = _get(int_res, "stone_f1")

        # ── External evaluation ───────────────────────────────────────────────
        ext_path = _EXP_OUTPUTS / exp_dir.name / "external" / "external_results.json"
        ext_res  = _load_json(ext_path)

        ext_acc     = _get(ext_res, "metrics", "accuracy")
        ext_prec    = _get(ext_res, "metrics", "precision")
        ext_recall  = _get(ext_res, "metrics", "recall")
        ext_spec    = _get(ext_res, "metrics", "specificity")
        ext_f1      = _get(ext_res, "metrics", "f1")
        ext_roc     = _get(ext_res, "metrics", "roc_auc")
        tp          = _get(ext_res, "counts", "TP")
        tn          = _get(ext_res, "counts", "TN")
        fp          = _get(ext_res, "counts", "FP")
        fn          = _get(ext_res, "counts", "FN")

        # Status
        has_internal = int_res is not None
        has_external = ext_res is not None
        if has_internal and has_external:
            status = "COMPLETED"
        elif has_internal:
            status = "EXTERNAL EVALUATION PENDING"
        else:
            status = "NOT RUN"

        aug_cfg = clf.get("augmentation", {})
        aug_str = aug_cfg.get("strategy", "baseline") if isinstance(aug_cfg, dict) else str(aug_cfg)
        cw_cfg  = clf.get("class_weighting", {})
        cw_str  = str(cw_cfg.get("enabled", False)) if isinstance(cw_cfg, dict) else "false"
        tl_cfg  = clf.get("transfer_learning", {})
        tl_str  = tl_cfg.get("strategy", "standard") if isinstance(tl_cfg, dict) else "standard"

        row = {
            "Experiment":        exp_dir.name,
            "ID":                exp_id,
            "Status":            status,
            "Backbone":          clf.get("backbone", "NOT RUN"),
            "InputSize":         clf.get("input_size", "NOT RUN"),
            "BatchSize":         clf.get("batch_size", "NOT RUN"),
            "LearningRate":      clf.get("learning_rate", "NOT RUN"),
            "WeightDecay":       clf.get("weight_decay", "NOT RUN"),
            "Dropout":           clf.get("dropout", "NOT RUN"),
            "Augmentation":      aug_str,
            "ClassWeighting":    cw_str,
            "TransferLearning":  tl_str,
            # Internal
            "Int_Accuracy":      int_acc     if has_internal else "NOT RUN",
            "Int_MacroF1":       int_macro_f1 if has_internal else "NOT RUN",
            "Int_WeightedF1":    int_wt_f1   if has_internal else "NOT RUN",
            "Int_ROCAUC":        int_roc_auc if has_internal else "NOT RUN",
            "Int_Stone_P":       int_stone_p  if has_internal else "NOT RUN",
            "Int_Stone_R":       int_stone_r  if has_internal else "NOT RUN",
            "Int_Stone_F1":      int_stone_f1 if has_internal else "NOT RUN",
            # External
            "Ext_Accuracy":      ext_acc    if has_external else "NOT RUN",
            "Ext_Precision":     ext_prec   if has_external else "NOT RUN",
            "Ext_Recall":        ext_recall if has_external else "NOT RUN",
            "Ext_Specificity":   ext_spec   if has_external else "NOT RUN",
            "Ext_F1":            ext_f1     if has_external else "NOT RUN",
            "Ext_ROCAUC":        ext_roc    if has_external else "NOT RUN",
            "TP":                tp         if has_external else "NOT RUN",
            "TN":                tn         if has_external else "NOT RUN",
            "FP":                fp         if has_external else "NOT RUN",
            "FN":                fn         if has_external else "NOT RUN",
            # Meta
            "TrainingDuration_s": meta.get("training_duration_s", "NOT RUN"),
            "BestValAcc":        meta.get("best_val_acc", "NOT RUN"),
            "GPU":               meta.get("gpu", "NOT RUN"),
        }
        rows.append(row)

    # Sort: COMPLETED first, then by External ROC-AUC descending
    def sort_key(r):
        status_order = {"COMPLETED": 0, "EXTERNAL EVALUATION PENDING": 1, "NOT RUN": 2}
        ext_roc = r.get("Ext_ROCAUC")
        try:
            roc_val = float(ext_roc) if ext_roc not in (None, "NOT RUN") else -1.0
        except (TypeError, ValueError):
            roc_val = -1.0
        return (status_order.get(r["Status"], 3), -roc_val)

    rows.sort(key=sort_key)
    return rows


def main():
    rows = collect_experiment_rows()

    _EXP_OUTPUTS.mkdir(parents=True, exist_ok=True)

    if not rows:
        print("No experiment data found under ai-engine/weights/experiments/")
        print("Train at least one experiment first.")
        return

    fields = list(rows[0].keys())

    # CSV
    csv_path = _EXP_OUTPUTS / "final_comparison.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # JSON
    json_path = _EXP_OUTPUTS / "final_comparison.json"
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"\nComparison saved:")
    print(f"  {csv_path}")
    print(f"  {json_path}")
    print(f"\n{len(rows)} experiments compared.")

    # Quick summary table
    print(f"\n{'Experiment':<35} {'Status':<35} {'Ext_ROC':>8} {'Ext_F1':>8} {'FP':>6}")
    print("-" * 100)
    for r in rows:
        print(
            f"  {r['Experiment']:<33} {r['Status']:<35} "
            f"{str(r['Ext_ROCAUC']):>8} {str(r['Ext_F1']):>8} {str(r['FP']):>6}"
        )


if __name__ == "__main__":
    main()
