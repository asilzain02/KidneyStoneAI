"""
kssd2025_inspector.py — KSSD2025 Dataset Inspection Utility.

Inspects the raw image/label directories and produces:
  - outputs/segmentation/dataset_inspection.json
  - outputs/segmentation/dataset_inspection.md

Usage (from project root):
    python ai-engine/datasets/segmentation/kssd2025/kssd2025_inspector.py

Does NOT modify any raw data. Read-only.
"""

from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image
from tqdm import tqdm

# ── Path bootstrap ────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve()
_ENGINE_ROOT = _HERE.parents[3]          # ai-engine/
_PROJECT_ROOT = _ENGINE_ROOT.parent      # project root
sys.path.insert(0, str(_ENGINE_ROOT))

from utils.logger import get_logger
from utils.seed_utils import set_seed

log = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


# ── File helpers ──────────────────────────────────────────────────────────────

def _collect(directory: Path) -> Dict[str, Path]:
    """Return {stem -> path} for all image-like files in directory."""
    return {
        p.stem: p
        for p in sorted(directory.iterdir())
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    }


def _extensions(directory: Path) -> Dict[str, int]:
    """Count file extensions found in directory."""
    counts: Dict[str, int] = collections.defaultdict(int)
    for p in directory.iterdir():
        if p.is_file():
            counts[p.suffix.lower()] += 1
    return dict(counts)


def _md5(path: Path) -> Optional[str]:
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _image_info(path: Path) -> Tuple[Optional[Tuple[int, int]], Optional[str], Optional[List]]:
    """Return (size_wh, mode, unique_values_if_small_range)."""
    try:
        with Image.open(path) as img:
            size = img.size  # (W, H)
            mode = img.mode
            arr = np.array(img)
        unique = sorted(set(arr.flatten().tolist()))
        return size, mode, unique
    except Exception:
        return None, None, None


# ── Inspector ─────────────────────────────────────────────────────────────────

def inspect(
    image_dir: Path,
    label_dir: Path,
    max_unique_values_display: int = 20,
) -> Dict:
    """
    Inspect KSSD2025 image/label directories.

    Returns a detailed report dict.
    """
    log.info("KSSD2025 Inspector — start", image_dir=str(image_dir), label_dir=str(label_dir))

    if not image_dir.exists():
        raise FileNotFoundError(f"Image dir not found: {image_dir}")
    if not label_dir.exists():
        raise FileNotFoundError(f"Label dir not found: {label_dir}")

    # ── File collection ───────────────────────────────────────────────────────
    images = _collect(image_dir)
    labels = _collect(label_dir)

    img_exts = _extensions(image_dir)
    lbl_exts = _extensions(label_dir)

    matched_stems = sorted(set(images) & set(labels))
    missing_labels = sorted(set(images) - set(labels))
    missing_images = sorted(set(labels) - set(images))

    log.info(
        "File discovery",
        images=len(images),
        labels=len(labels),
        matched=len(matched_stems),
        missing_labels=len(missing_labels),
        missing_images=len(missing_images),
    )

    # ── Per-pair analysis ─────────────────────────────────────────────────────
    image_dims: Dict[str, int] = collections.defaultdict(int)
    label_dims: Dict[str, int] = collections.defaultdict(int)
    image_modes: Dict[str, int] = collections.defaultdict(int)
    label_modes: Dict[str, int] = collections.defaultdict(int)

    all_label_unique_values: Dict[str, int] = collections.defaultdict(int)  # value → count of images
    empty_masks: List[str] = []
    corrupted_images: List[str] = []
    corrupted_labels: List[str] = []

    foreground_pixel_counts: List[int] = []
    total_pixel_counts: List[int] = []

    image_hash_map: Dict[str, List[str]] = collections.defaultdict(list)

    log.info("Analysing matched pairs …")
    for stem in tqdm(matched_stems, desc="Inspecting"):
        img_path = images[stem]
        lbl_path = labels[stem]

        # Image
        img_size, img_mode, _ = _image_info(img_path)
        if img_size is None:
            corrupted_images.append(str(img_path))
        else:
            image_dims[f"{img_size[0]}x{img_size[1]}"] += 1
            image_modes[img_mode or "unknown"] += 1
            img_hash = _md5(img_path)
            if img_hash:
                image_hash_map[img_hash].append(str(img_path))

        # Label
        lbl_size, lbl_mode, lbl_unique = _image_info(lbl_path)
        if lbl_size is None:
            corrupted_labels.append(str(lbl_path))
        else:
            label_dims[f"{lbl_size[0]}x{lbl_size[1]}"] += 1
            label_modes[lbl_mode or "unknown"] += 1

            if lbl_unique is not None:
                for v in lbl_unique:
                    all_label_unique_values[str(v)] += 1

                # Foreground = any pixel > 0
                try:
                    with Image.open(lbl_path) as img:
                        arr = np.array(img)
                    fg = int((arr > 0).sum())
                    total = int(arr.size)
                    foreground_pixel_counts.append(fg)
                    total_pixel_counts.append(total)
                    if fg == 0:
                        empty_masks.append(str(lbl_path))
                except Exception:
                    empty_masks.append(str(lbl_path))

    # ── Duplicate detection ───────────────────────────────────────────────────
    duplicate_groups = {
        h: paths for h, paths in image_hash_map.items() if len(paths) > 1
    }

    # ── Aggregate stats ───────────────────────────────────────────────────────
    total_fg = sum(foreground_pixel_counts)
    total_px = sum(total_pixel_counts)
    fg_ratio = total_fg / total_px if total_px > 0 else 0.0

    # Infer annotation type from unique label values
    all_unique_ints = sorted(int(k) for k in all_label_unique_values)
    if set(all_unique_ints) <= {0, 1}:
        annotation_type = "binary (0/1)"
    elif set(all_unique_ints) <= {0, 255}:
        annotation_type = "binary (0/255)"
    elif len(all_unique_ints) <= 10:
        annotation_type = f"multiclass ({len(all_unique_ints)} classes)"
    else:
        annotation_type = f"grayscale/continuous ({len(all_unique_ints)} unique values)"

    report = {
        "dataset": "KSSD2025",
        "image_dir": str(image_dir),
        "label_dir": str(label_dir),
        "summary": {
            "total_images": len(images),
            "total_labels": len(labels),
            "matched_pairs": len(matched_stems),
            "missing_labels": len(missing_labels),
            "missing_images": len(missing_images),
            "corrupted_images": len(corrupted_images),
            "corrupted_labels": len(corrupted_labels),
            "empty_masks": len(empty_masks),
            "duplicate_image_groups": len(duplicate_groups),
        },
        "file_extensions": {
            "images": img_exts,
            "labels": lbl_exts,
        },
        "image_dimension_distribution": dict(image_dims),
        "label_dimension_distribution": dict(label_dims),
        "image_mode_distribution": dict(image_modes),
        "label_mode_distribution": dict(label_modes),
        "label_unique_values": {
            "all_values_seen": all_unique_ints[:max_unique_values_display],
            "annotation_type_inference": annotation_type,
            "NOTE": (
                "Unique values are the union across all labels. "
                "Do NOT assume value=1 means stone without inspecting individual masks."
            ),
        },
        "foreground_pixels": {
            "total_foreground_pixels": total_fg,
            "total_pixels": total_px,
            "foreground_ratio": round(fg_ratio, 6),
            "foreground_percentage": round(fg_ratio * 100, 4),
            "mean_foreground_pixels_per_image": (
                round(total_fg / len(foreground_pixel_counts), 2)
                if foreground_pixel_counts else 0
            ),
        },
        "leakage_assessment": {
            "patient_ids_available": False,
            "patient_level_split": "not possible — no patient metadata in filenames",
            "duplicate_image_groups": len(duplicate_groups),
            "recommendation": (
                "Split by image index only. "
                "Apply hash-based deduplication before splitting. "
                "No patient-level leakage control is possible without metadata."
            ),
        },
        "missing_labels_list": missing_labels[:20],
        "missing_images_list": missing_images[:20],
        "corrupted_images_list": corrupted_images,
        "corrupted_labels_list": corrupted_labels,
        "empty_masks_list": empty_masks[:20],
    }

    return report


# ── Markdown report ───────────────────────────────────────────────────────────

def _make_markdown(report: Dict) -> str:
    s = report["summary"]
    fe = report["foreground_pixels"]
    luv = report["label_unique_values"]
    leak = report["leakage_assessment"]

    lines = [
        "# KSSD2025 Dataset Inspection Report",
        "",
        f"**Image dir**: `{report['image_dir']}`",
        f"**Label dir**: `{report['label_dir']}`",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total images | {s['total_images']} |",
        f"| Total labels | {s['total_labels']} |",
        f"| Matched pairs | {s['matched_pairs']} |",
        f"| Missing labels | {s['missing_labels']} |",
        f"| Missing images | {s['missing_images']} |",
        f"| Corrupted images | {s['corrupted_images']} |",
        f"| Corrupted labels | {s['corrupted_labels']} |",
        f"| Empty masks | {s['empty_masks']} |",
        f"| Duplicate image groups | {s['duplicate_image_groups']} |",
        "",
        "## File Extensions",
        "",
        f"**Images**: {report['file_extensions']['images']}",
        f"**Labels**: {report['file_extensions']['labels']}",
        "",
        "## Image Dimensions",
        "",
    ]

    for dim, cnt in report["image_dimension_distribution"].items():
        lines.append(f"- `{dim}`: {cnt} images")

    lines += [
        "",
        "## Label Dimensions",
        "",
    ]
    for dim, cnt in report["label_dimension_distribution"].items():
        lines.append(f"- `{dim}`: {cnt} labels")

    lines += [
        "",
        "## Label Pixel Values",
        "",
        f"- **Unique values across dataset**: `{luv['all_values_seen']}`",
        f"- **Inferred annotation type**: {luv['annotation_type_inference']}",
        f"- ⚠️  {luv['NOTE']}",
        "",
        "## Foreground Pixel Statistics",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total foreground pixels | {fe['total_foreground_pixels']:,} |",
        f"| Total pixels | {fe['total_pixels']:,} |",
        f"| Foreground ratio | {fe['foreground_ratio']:.6f} |",
        f"| Foreground percentage | {fe['foreground_percentage']:.4f}% |",
        f"| Mean fg pixels / image | {fe['mean_foreground_pixels_per_image']:,.2f} |",
        "",
        "## Data Leakage Assessment",
        "",
        f"- Patient IDs available: **{leak['patient_ids_available']}**",
        f"- Patient-level split: {leak['patient_level_split']}",
        f"- Duplicate image groups: **{leak['duplicate_image_groups']}**",
        f"- Recommendation: {leak['recommendation']}",
        "",
        "> [!NOTE]",
        "> This is a read-only inspection. No raw data was modified.",
    ]
    return "\n".join(lines)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    set_seed(42)

    # Resolve paths relative to project root
    image_dir = _PROJECT_ROOT / "datasets" / "raw" / "segmentation" / "kssd2025" / "data" / "image"
    label_dir = _PROJECT_ROOT / "datasets" / "raw" / "segmentation" / "kssd2025" / "data" / "label"
    output_dir = _PROJECT_ROOT / "outputs" / "segmentation"
    output_dir.mkdir(parents=True, exist_ok=True)

    report = inspect(image_dir, label_dir)

    json_path = output_dir / "dataset_inspection.json"
    md_path = output_dir / "dataset_inspection.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    log.info("Inspection JSON saved", path=str(json_path))

    md_content = _make_markdown(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    log.info("Inspection Markdown saved", path=str(md_path))

    # ── Console summary ───────────────────────────────────────────────────────
    s = report["summary"]
    fe = report["foreground_pixels"]
    print("\n" + "=" * 60)
    print("KSSD2025 Dataset Inspection")
    print("=" * 60)
    print(f"  Images          : {s['total_images']}")
    print(f"  Labels          : {s['total_labels']}")
    print(f"  Matched pairs   : {s['matched_pairs']}")
    print(f"  Missing labels  : {s['missing_labels']}")
    print(f"  Missing images  : {s['missing_images']}")
    print(f"  Corrupted imgs  : {s['corrupted_images']}")
    print(f"  Corrupted lbls  : {s['corrupted_labels']}")
    print(f"  Empty masks     : {s['empty_masks']}")
    print(f"  Duplicate groups: {s['duplicate_image_groups']}")
    print(f"  Foreground %    : {fe['foreground_percentage']:.4f}%")
    print(f"  Label values    : {report['label_unique_values']['all_values_seen']}")
    print(f"  Annotation type : {report['label_unique_values']['annotation_type_inference']}")
    print(f"\n  Image extensions: {report['file_extensions']['images']}")
    print(f"  Label extensions: {report['file_extensions']['labels']}")
    print("\n  Image dimensions:")
    for dim, cnt in report["image_dimension_distribution"].items():
        print(f"    {dim}: {cnt}")
    print("\n  Label dimensions:")
    for dim, cnt in report["label_dimension_distribution"].items():
        print(f"    {dim}: {cnt}")
    print("=" * 60)
    print(f"  Report saved → {json_path}")
    print(f"               → {md_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
