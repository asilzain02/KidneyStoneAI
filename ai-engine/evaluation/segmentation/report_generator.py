"""
report_generator.py — Segmentation experiment report generator.

Generates:
    outputs/segmentation/SEGMENTATION_EXPERIMENT_REPORT.md

Usage:
    python ai-engine/evaluation/segmentation/report_generator.py \\
        --results outputs/segmentation/evaluation/segmentation_results.json

    python ai-engine/evaluation/segmentation/report_generator.py \\
        --results outputs/segmentation/evaluation/segmentation_results.json \\
        --measurements outputs/segmentation/evaluation/measurements.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

_HERE = Path(__file__).resolve()
_ENGINE_ROOT = _HERE.parents[2]
_PROJECT_ROOT = _ENGINE_ROOT.parent
sys.path.insert(0, str(_ENGINE_ROOT))

from utils.logger import get_logger

log = get_logger(__name__)


def generate_report(
    results_path: Path,
    measurements_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> str:
    """
    Generate the experiment report Markdown.

    Parameters
    ----------
    results_path      : path to segmentation_results.json
    measurements_path : optional path to measurements.json
    output_path       : where to write the Markdown (auto-detected if None)

    Returns
    -------
    str — Markdown content
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results not found: {results_path}")

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    measurements = []
    if measurements_path and measurements_path.exists():
        with open(measurements_path, "r", encoding="utf-8") as f:
            measurements = json.load(f)

    if output_path is None:
        output_path = _PROJECT_ROOT / "outputs" / "segmentation" / "SEGMENTATION_EXPERIMENT_REPORT.md"

    agg = results.get("aggregate_metrics", {})
    per_sample = results.get("per_sample_metrics", [])

    # Compute detection stats from measurements
    total_detected = sum(1 for m in measurements if m.get("detected", False))
    total_measured = len(measurements)

    lines = [
        "# KidneyStoneAI — Segmentation Experiment Report",
        "",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "> [!IMPORTANT]",
        "> This is a research system for kidney stone detection. Results are NOT",
        "> clinically validated and must NOT be used for medical diagnosis.",
        "",
        "---",
        "",
        "## 1. Dataset",
        "",
        "| Property | Value |",
        "|---|---|",
        "| Dataset | KSSD2025 (Kidney Stone Segmentation Dataset 2025) |",
        "| Images | 838 |",
        "| Labels | 838 |",
        "| Format | TIFF (.tif) |",
        "| Annotation type | Binary mask |",
        "| Split | 70% train / 15% val / 15% test |",
        "| Split seed | 42 |",
        "",
        "---",
        "",
        "## 2. Model Architecture",
        "",
        "| Parameter | Value |",
        "|---|---|",
        "| Architecture | U-Net |",
        "| Input size | 256 × 256 |",
        "| Input channels | 1 (grayscale CT) |",
        "| Output channels | 1 (binary mask) |",
        "| Base features | 32 |",
        "| Encoder depth | 4 downsampling blocks |",
        "| Decoder | Skip connections (bilinear upsampling) |",
        "",
        "---",
        "",
        "## 3. Training Configuration",
        "",
        "| Parameter | Value |",
        "|---|---|",
        "| Loss | Dice + BCE (equal weights) |",
        "| Optimizer | Adam |",
        "| Learning rate | 0.0001 |",
        "| Weight decay | 0.0001 |",
        "| Batch size | 8 |",
        "| Max epochs | 50 |",
        "| Scheduler | ReduceLROnPlateau (patience=5) |",
        "| Early stopping | patience=10 |",
        "| Seed | 42 |",
        "",
        "---",
        "",
        "## 4. Augmentation",
        "",
        "| Transform | Applied to |",
        "|---|---|",
        "| Horizontal flip (p=0.5) | Image + Mask |",
        "| Vertical flip (p=0.3) | Image + Mask |",
        "| Rotation ±10° | Image + Mask |",
        "| Brightness [0.8, 1.2] | Image only |",
        "| Contrast [0.8, 1.2] | Image only |",
        "",
        "> [!NOTE]",
        "> Intensity transforms are applied to the image only.",
        "> Spatial transforms are applied identically to image and mask.",
        "",
        "---",
        "",
        "## 5. Evaluation Results (INTERNAL — KSSD2025 Test Split)",
        "",
        "| Metric | Mean ± Std |",
        "|---|---|",
    ]

    scalar_keys = ["dice", "iou", "precision", "recall", "sensitivity",
                   "specificity", "f1", "pixel_accuracy"]
    for k in scalar_keys:
        mean_k = f"mean_{k}"
        std_k  = f"std_{k}"
        if mean_k in agg:
            lines.append(f"| {k.replace('_', ' ').title()} | {agg[mean_k]:.4f} ± {agg.get(std_k, 0):.4f} |")

    checkpoint = results.get("checkpoint", "N/A")
    n_samples  = results.get("num_samples", "N/A")
    split      = results.get("split", "test")
    threshold  = results.get("threshold", 0.5)

    lines += [
        "",
        f"- Checkpoint: `{checkpoint}`",
        f"- Split: {split}",
        f"- Samples evaluated: {n_samples}",
        f"- Threshold: {threshold}",
        "",
        "---",
        "",
        "## 6. Stone Detection Summary",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Samples with detected stone | {total_detected} / {total_measured} |",
        f"| Detection rate | {total_detected/total_measured*100:.1f}% |" if total_measured > 0 else "| Detection rate | N/A |",
        "",
        "---",
        "",
        "## 7. Failure Case Analysis",
        "",
    ]

    bw = results.get("best_worst", {})
    if bw.get("worst"):
        lines.append("### Worst Dice Samples")
        for s in bw["worst"]:
            m_entry = next((m for m in per_sample if m.get("stem") == s), None)
            if m_entry:
                lines.append(f"- `{s}`: Dice={m_entry.get('dice', 0):.3f}, IoU={m_entry.get('iou', 0):.3f}")
    if bw.get("highest_fn"):
        lines.append("\n### Highest False Negative (missed stones)")
        for s in bw["highest_fn"]:
            m_entry = next((m for m in per_sample if m.get("stem") == s), None)
            if m_entry:
                lines.append(f"- `{s}`: FN={m_entry.get('fn', 0)}, Dice={m_entry.get('dice', 0):.3f}")

    lines += [
        "",
        "---",
        "",
        "## 8. Limitations",
        "",
        "- Patient-level split not possible (no patient metadata in KSSD2025 filenames)",
        "- All measurements are in pixels — pixel spacing unavailable",
        "- Stone size cannot be converted to mm without reliable DICOM pixel spacing",
        "- Severity estimation is disabled (requires pixel spacing)",
        "- Model trained only on KSSD2025 — generalization to unseen CT protocols untested",
        "",
        "---",
        "",
        "## 9. Future Improvements",
        "",
        "1. Evaluate on an independent external segmentation dataset",
        "2. Obtain DICOM metadata (pixel spacing) for mm-accurate measurements",
        "3. Integrate classifier + segmentation into end-to-end pipeline",
        "4. Experiment with stronger encoders (EfficientNet-B0 pretrained)",
        "5. Add U-Net++ or DeepLabV3 experiments via the model factory",
        "6. Validate severity estimation against clinical reference standards",
        "",
        "---",
        "",
        "## 10. Medical Disclaimer",
        "",
        "> [!CAUTION]",
        "> This system is a **research prototype** for a final-year computer science project.",
        "> It has NOT been clinically validated. Results must NOT be used for medical diagnosis,",
        "> treatment, or clinical decision making.",
        "> All findings must be reviewed by qualified medical professionals.",
        "",
    ]

    md_content = "\n".join(lines)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    log.info("Report generated", path=str(output_path))
    return md_content


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Generate segmentation experiment report")
    p.add_argument(
        "--results", type=str,
        default="outputs/segmentation/evaluation/segmentation_results.json",
    )
    p.add_argument("--measurements", type=str, default=None)
    p.add_argument("--output", type=str, default=None)
    return p.parse_args()


def main():
    args = parse_args()
    generate_report(
        results_path=Path(args.results),
        measurements_path=Path(args.measurements) if args.measurements else None,
        output_path=Path(args.output) if args.output else None,
    )
    print("Report generated.")


if __name__ == "__main__":
    main()
