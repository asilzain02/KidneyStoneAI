"""
locked_model_external_evaluator.py

PURPOSE:
    Evaluate the Kaggle locked_model.pt independently on the external
    Axial CT Kidney Stone Dataset.

IMPORTANT:
    - This script is completely separate from external_evaluator.py.
    - No training or fine-tuning is performed.
    - No production model/checkpoint is modified.
    - The Kaggle MobileNetV4 architecture and preprocessing are reconstructed
      directly from the Kaggle experiment configuration.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np
import torch
import timm
from PIL import Image
from scipy.ndimage import (
    binary_closing,
    binary_fill_holes,
    binary_opening,
    generate_binary_structure,
    gaussian_filter,
    label as ndi_label,
)
from tqdm import tqdm


# ---------------------------------------------------------------------------
# Kaggle model constants
# ---------------------------------------------------------------------------

# PURPOSE:
# Keep the exact four-class ordering used by the locked Kaggle model.
CLASS_NAMES = ["Cyst", "Normal", "Stone", "Tumor"]

STONE_INDEX = 2

# PURPOSE:
# These are the exact optimized preprocessing parameters stored in
# artifacts/best_config.yaml from the Kaggle experiment.
CLAHE_CLIP_LIMIT = 3.7890929570277194
CLAHE_TILE_GRID = 8

WOLF_WINDOW = 15
WOLF_K = 0.6355353990939866

ROI_ALPHA = 0.26967112095782536
ROI_BETA = 0.5
ROI_BLUR_SIGMA = 3.0

IMAGE_SIZE = 224

# PURPOSE:
# This is the dropout value selected by the Kaggle Optuna experiment.
DROPOUT = 0.1911740650167767

# PURPOSE:
# Temperature obtained from the Kaggle calibration artifact.
TEMPERATURE = 0.8073326349258423

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


# ---------------------------------------------------------------------------
# Dataset discovery
# ---------------------------------------------------------------------------

def discover_dataset(data_root: Path) -> list[tuple[Path, str]]:
    """
    PURPOSE:
        Discover only the Original/Stone and Original/Non-Stone images.

    Returns:
        List of (image_path, binary_ground_truth) tuples.
    """

    stone_dir = data_root / "Stone"
    non_stone_dir = data_root / "Non-Stone"

    if not stone_dir.is_dir():
        raise FileNotFoundError(f"Missing directory: {stone_dir}")

    if not non_stone_dir.is_dir():
        raise FileNotFoundError(f"Missing directory: {non_stone_dir}")

    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

    records = []

    for directory, label in [
        (stone_dir, "STONE"),
        (non_stone_dir, "NON_STONE"),
    ]:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in extensions:
                records.append((path, label))

    return records


# ---------------------------------------------------------------------------
# Kaggle preprocessing
# ---------------------------------------------------------------------------

def robust_normalize(img: np.ndarray) -> np.ndarray:
    """
    PURPOSE:
        Reproduce the Kaggle robust percentile normalization.

    The locked experiment's saved preprocessing statistics are:
        lo = 0.0
        hi = 255.0

    Therefore this is effectively deterministic uint8 -> [0, 1]
    normalization for these external images.
    """

    arr = img.astype(np.float32)

    lo = 0.0
    hi = 255.0

    if hi <= lo:
        return np.zeros_like(arr, dtype=np.float32)

    return np.clip((arr - lo) / (hi - lo), 0.0, 1.0)


def apply_clahe(img_uint8: np.ndarray) -> np.ndarray:
    """
    PURPOSE:
        Apply the exact optimized CLAHE configuration from the Kaggle run.
    """

    clahe = cv2.createCLAHE(
        clipLimit=CLAHE_CLIP_LIMIT,
        tileGridSize=(CLAHE_TILE_GRID, CLAHE_TILE_GRID),
    )

    return clahe.apply(img_uint8)


def wolf_threshold(
    img_uint8: np.ndarray,
    window: int = WOLF_WINDOW,
    k: float = WOLF_K,
) -> np.ndarray:
    """
    PURPOSE:
        Reproduce the Kaggle Wolf-Jolion-Chassaing adaptive threshold.
    """

    img = img_uint8.astype(np.float64)

    mean = cv2.boxFilter(
        img,
        ddepth=-1,
        ksize=(window, window),
        normalize=True,
        borderType=cv2.BORDER_REFLECT,
    )

    mean_sq = cv2.boxFilter(
        img * img,
        ddepth=-1,
        ksize=(window, window),
        normalize=True,
        borderType=cv2.BORDER_REFLECT,
    )

    variance = np.maximum(mean_sq - mean * mean, 0.0)
    std = np.sqrt(variance)

    global_min = float(img_uint8.min())
    max_local_std = float(std.max())

    if max_local_std == 0:
        return np.zeros_like(img_uint8, dtype=np.uint8)

    threshold = (
        mean
        + k
        * (std / max_local_std - 1.0)
        * (mean - global_min)
    )

    return (
        (img.astype(np.float64) > threshold)
        .astype(np.uint8)
        * 255
    )


def clean_mask(
    mask_uint8: np.ndarray,
    struct_size: int = 3,
    min_object_frac: float = 0.001,
) -> np.ndarray:
    """
    PURPOSE:
        Reproduce the Kaggle morphology cleanup:
        opening -> closing -> hole filling -> small component removal.
    """

    mask = mask_uint8.astype(bool)

    structure = np.ones(
        (struct_size, struct_size),
        dtype=bool,
    )

    mask = binary_opening(mask, structure=structure)
    mask = binary_closing(mask, structure=structure)
    mask = binary_fill_holes(mask)

    min_size = max(
        1,
        int(round(min_object_frac * mask.size)),
    )

    labeled, number = ndi_label(
        mask,
        structure=generate_binary_structure(2, 2),
    )

    if number == 0:
        return np.zeros_like(mask_uint8)

    sizes = np.bincount(labeled.ravel())

    keep = np.where(sizes >= min_size)[0]
    keep = keep[keep != 0]

    if len(keep) == 0:
        return np.zeros_like(mask_uint8)

    cleaned = np.isin(labeled, keep)

    return cleaned.astype(np.uint8) * 255


def apply_kaggle_preprocessing(
    image: np.ndarray,
) -> np.ndarray:
    """
    PURPOSE:
        Reproduce the complete Kaggle 'full' preprocessing pipeline:

        grayscale
          -> robust normalization
          -> CLAHE
          -> Wolf threshold
          -> morphology
          -> QC
          -> ROI blend when QC passes
          -> 224x224 RGB
    """

    # Normalize into [0, 1].
    normalized = robust_normalize(image)

    # Convert back to uint8 for CLAHE/Wolf processing.
    normalized_u8 = (
        np.clip(normalized, 0.0, 1.0) * 255.0
    ).astype(np.uint8)

    # CLAHE.
    clahe_img = apply_clahe(normalized_u8)

    # Wolf adaptive threshold.
    raw_mask = wolf_threshold(clahe_img)

    # Morphological cleanup.
    mask = clean_mask(raw_mask)

    # ---------------------------------------------------------------
    # Kaggle QC gate
    # ---------------------------------------------------------------

    occupancy = float(mask.astype(bool).mean())

    n_components = 0

    if mask.any():
        _, n_components = ndi_label(
            mask.astype(bool),
            structure=generate_binary_structure(2, 2),
        )

    qc_passed = (
        0.005 <= occupancy <= 0.6
        and n_components <= 8
    )

    if not qc_passed:
        enhanced = clahe_img

    else:
        # -----------------------------------------------------------
        # ROI soft mask
        # -----------------------------------------------------------

        soft = (
            mask.astype(np.float32) / 255.0
        )

        soft = gaussian_filter(
            soft,
            sigma=ROI_BLUR_SIGMA,
        )

        peak = float(soft.max())

        if peak > 0:
            soft = soft / peak

        # -----------------------------------------------------------
        # Kaggle ROI blend
        # -----------------------------------------------------------

        clahe_float = clahe_img.astype(np.float32)

        normalized_float = normalized.astype(np.float32)

        normalized_255 = normalized_float * 255.0

        enhanced = (
            clahe_float * (1.0 + ROI_ALPHA * soft)
            + ROI_BETA
            * normalized_255
            * (1.0 - soft)
        )

        enhanced = np.clip(
            enhanced,
            0,
            255,
        ).astype(np.uint8)

    return enhanced


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def build_locked_model() -> torch.nn.Module:
    """
    PURPOSE:
        Reconstruct the exact Kaggle MobileNetV4 Conv Small classifier
        architecture used to create locked_model.pt.

    The backbone produces pooled features and the custom head is:
        Dropout -> Linear(4 classes)
    """

    backbone = timm.create_model(
        "mobilenetv4_conv_small.e2400_r224_in1k",
        pretrained=False,
        num_classes=0,
        global_pool="avg",
    )

    # PURPOSE:
    # Determine the actual pooled feature dimension instead of hardcoding it.
    with torch.no_grad():
        dummy = torch.zeros(
            1,
            3,
            IMAGE_SIZE,
            IMAGE_SIZE,
        )

        feature_dim = int(
            backbone(dummy).shape[-1]
        )

    # PURPOSE:
    # Match the Kaggle ClassifierHead:
    # dropout -> linear -> 4 class logits.
    head = torch.nn.Sequential(
        torch.nn.Dropout(DROPOUT),
        torch.nn.Linear(
            feature_dim,
            len(CLASS_NAMES),
        ),
    )

    class LockedModel(torch.nn.Module):
        """Standalone wrapper matching the Kaggle checkpoint structure."""

        def __init__(self):
            super().__init__()

            # PURPOSE:
            # Expose the same parameter namespaces used by the Kaggle model:
            # backbone.* and head.*.
            self.backbone = backbone
            self.head = head

        def forward(self, x):
            return self.head(self.backbone(x))

    return LockedModel()


def load_locked_model(
    checkpoint_path: Path,
    device: torch.device,
) -> torch.nn.Module:
    """
    PURPOSE:
        Load model_state from the Kaggle structured checkpoint.
    """

    checkpoint = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=False,
    )

    if "model_state" not in checkpoint:
        raise KeyError(
            "locked_model.pt does not contain the expected "
            "'model_state' key."
        )

    model = build_locked_model()

    # PURPOSE:
    # Load ONLY the neural-network weights. Optimizer, scheduler,
    # scaler and training metadata are intentionally ignored.
    model.load_state_dict(
        checkpoint["model_state"],
        strict=True,
    )

    model.to(device)
    model.eval()

    return model


# ---------------------------------------------------------------------------
# Image -> tensor
# ---------------------------------------------------------------------------

def image_to_tensor(image: np.ndarray) -> torch.Tensor:
    """
    PURPOSE:
        Convert the Kaggle-preprocessed grayscale image into the
        3-channel ImageNet-normalized tensor expected by MobileNetV4.
    """

    image = cv2.resize(
        image,
        (IMAGE_SIZE, IMAGE_SIZE),
        interpolation=cv2.INTER_LINEAR,
    )

    # The Kaggle pipeline replicates grayscale into RGB.
    rgb = np.stack(
        [image, image, image],
        axis=-1,
    ).astype(np.float32) / 255.0

    # ImageNet normalization.
    rgb = (
        rgb - IMAGENET_MEAN
    ) / IMAGENET_STD

    # HWC -> CHW.
    tensor = torch.from_numpy(
        rgb.transpose(2, 0, 1)
    ).float()

    return tensor


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def calculate_metrics(
    y_true: list[int],
    y_pred: list[int],
    stone_probs: list[float],
) -> dict:
    """
    PURPOSE:
        Calculate binary Stone vs Non-Stone external metrics.
    """

    tp = tn = fp = fn = 0

    for gt, pred in zip(y_true, y_pred):

        if gt == 1 and pred == 1:
            tp += 1

        elif gt == 0 and pred == 0:
            tn += 1

        elif gt == 0 and pred == 1:
            fp += 1

        elif gt == 1 and pred == 0:
            fn += 1

    total = tp + tn + fp + fn

    accuracy = (
        (tp + tn) / total
        if total else 0.0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp) else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) else 0.0
    )

    specificity = (
        tn / (tn + fp)
        if (tn + fp) else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    try:
        from sklearn.metrics import roc_auc_score

        roc_auc = float(
            roc_auc_score(
                y_true,
                stone_probs,
            )
        )

    except Exception:
        roc_auc = None

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall_sensitivity": recall,
        "specificity": specificity,
        "f1": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": [
            [tn, fp],
            [fn, tp],
        ],
        "counts": {
            "TP": tp,
            "TN": tn,
            "FP": fp,
            "FN": fn,
        },
    }


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def evaluate(args):
    """
    PURPOSE:
        Execute a completely independent inference-only evaluation of
        locked_model.pt against the external Original dataset.
    """

    data_root = Path(args.data_root).resolve()
    checkpoint_path = Path(args.checkpoint).resolve()
    output_dir = Path(args.output).resolve()

    print("=" * 70)
    print("LOCKED MODEL — INDEPENDENT EXTERNAL EVALUATION")
    print("=" * 70)
    print("Training: DISABLED")
    print("Fine-tuning: DISABLED")
    print("Augmentation: DISABLED")
    print("Dataset: Axial CT Kidney Stone Dataset")
    print("Subset: Original ONLY")
    print(f"Checkpoint: {checkpoint_path}")
    print("=" * 70)

    if not data_root.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {data_root}"
        )

    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint_path}"
        )

    records = discover_dataset(data_root)

    stone_count = sum(
        label == "STONE"
        for _, label in records
    )

    non_stone_count = sum(
        label == "NON_STONE"
        for _, label in records
    )

    print("\nDataset:")
    print(f"  Stone:     {stone_count}")
    print(f"  Non-Stone: {non_stone_count}")
    print(f"  Total:     {len(records)}")

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"\nDevice: {device}")

    if device.type == "cuda":
        print(
            f"GPU: {torch.cuda.get_device_name(0)}"
        )

    print("\nLoading MobileNetV4 locked model...")

    model = load_locked_model(
        checkpoint_path,
        device,
    )

    print("Model loaded successfully.")

    y_true = []
    y_pred = []
    stone_probs = []

    calibrated_stone_probs = []

    rows = []

    failed = 0

    print("\nRunning independent inference...")

    for image_path, ground_truth in tqdm(
        records,
        desc="Inference",
    ):

        try:
            # -------------------------------------------------------
            # Read exactly as grayscale.
            # -------------------------------------------------------

            image = cv2.imread(
                str(image_path),
                cv2.IMREAD_GRAYSCALE,
            )

            if image is None:
                raise ValueError(
                    "Unable to read image."
                )

            # -------------------------------------------------------
            # Exact Kaggle adaptive preprocessing.
            # -------------------------------------------------------

            processed = apply_kaggle_preprocessing(
                image
            )

            # -------------------------------------------------------
            # Convert to model tensor.
            # -------------------------------------------------------

            tensor = image_to_tensor(
                processed
            )

            tensor = tensor.unsqueeze(0).to(device)

            # -------------------------------------------------------
            # Inference only.
            # -------------------------------------------------------

            with torch.inference_mode():

                logits = model(tensor)

                probabilities = torch.softmax(
                    logits,
                    dim=1,
                )[0]

                # Raw prediction.
                predicted_index = int(
                    torch.argmax(
                        probabilities
                    ).item()
                )

                predicted_class = CLASS_NAMES[
                    predicted_index
                ]

                raw_stone_probability = float(
                    probabilities[STONE_INDEX].item()
                )

                # ---------------------------------------------------
                # Temperature-calibrated probability.
                # ---------------------------------------------------

                calibrated_probabilities = torch.softmax(
                    logits / TEMPERATURE,
                    dim=1,
                )[0]

                calibrated_stone_probability = float(
                    calibrated_probabilities[
                        STONE_INDEX
                    ].item()
                )

            # -------------------------------------------------------
            # Binary mapping.
            # -------------------------------------------------------

            gt_binary = (
                1
                if ground_truth == "STONE"
                else 0
            )

            predicted_binary = (
                1
                if predicted_class == "Stone"
                else 0
            )

            y_true.append(gt_binary)
            y_pred.append(predicted_binary)

            stone_probs.append(
                raw_stone_probability
            )

            calibrated_stone_probs.append(
                calibrated_stone_probability
            )

            rows.append(
                {
                    "image_path": str(image_path),
                    "filename": image_path.name,
                    "ground_truth": ground_truth,
                    "predicted_class": predicted_class,
                    "predicted_binary_class": (
                        "STONE"
                        if predicted_binary
                        else "NON_STONE"
                    ),
                    "cyst_probability": float(
                        probabilities[0].item()
                    ),
                    "normal_probability": float(
                        probabilities[1].item()
                    ),
                    "stone_probability": raw_stone_probability,
                    "tumor_probability": float(
                        probabilities[3].item()
                    ),
                    "calibrated_stone_probability":
                        calibrated_stone_probability,
                    "confidence": float(
                        probabilities[
                            predicted_index
                        ].item()
                    ),
                    "correct": (
                        gt_binary
                        == predicted_binary
                    ),
                }
            )

        except Exception as exc:

            failed += 1

            print(
                f"\nWARNING: Failed: "
                f"{image_path} -> {exc}"
            )

    # -------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------

    raw_metrics = calculate_metrics(
        y_true,
        y_pred,
        stone_probs,
    )

    calibrated_metrics = calculate_metrics(
        y_true,
        y_pred,
        calibrated_stone_probs,
    )

    # -------------------------------------------------------------------
    # Save results
    # -------------------------------------------------------------------

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        output_dir
        / "locked_model_external_results.json"
    )

    csv_path = (
        output_dir
        / "locked_model_external_predictions.csv"
    )

    result = {
        "dataset": "Axial CT Kidney Stone Dataset",
        "subset": "Original",
        "augmented_images_used": 0,
        "total_images": len(records),
        "evaluated_images": len(y_true),
        "failed_images": failed,
        "stone_images": stone_count,
        "non_stone_images": non_stone_count,
        "model": "MobileNetV4 Conv Small",
        "backbone": (
            "mobilenetv4_conv_small."
            "e2400_r224_in1k"
        ),
        "checkpoint": str(checkpoint_path),
        "device": device.type.upper(),
        "class_order": CLASS_NAMES,
        "mapping": {
            "Cyst": "NON_STONE",
            "Normal": "NON_STONE",
            "Stone": "STONE",
            "Tumor": "NON_STONE",
        },
        "preprocessing": {
            "clahe_clip_limit":
                CLAHE_CLIP_LIMIT,
            "clahe_tile_grid":
                CLAHE_TILE_GRID,
            "wolf_window":
                WOLF_WINDOW,
            "wolf_k":
                WOLF_K,
            "roi_alpha":
                ROI_ALPHA,
            "roi_beta":
                ROI_BETA,
            "roi_mask_blur_sigma":
                ROI_BLUR_SIGMA,
            "image_size":
                IMAGE_SIZE,
        },
        "calibration": {
            "temperature":
                TEMPERATURE,
        },
        "raw_probability_metrics":
            raw_metrics,
        "calibrated_probability_metrics":
            calibrated_metrics,
    }

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result,
            f,
            indent=4,
        )

    if rows:

        with open(
            csv_path,
            "w",
            newline="",
            encoding="utf-8",
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=list(rows[0].keys()),
            )

            writer.writeheader()
            writer.writerows(rows)

    # -------------------------------------------------------------------
    # Console summary
    # -------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("LOCKED MODEL EXTERNAL EVALUATION COMPLETE")
    print("=" * 70)

    print(
        f"Evaluated: {len(y_true)} / {len(records)}"
    )

    print("\nRaw probability metrics:")

    for key in [
        "accuracy",
        "precision",
        "recall_sensitivity",
        "specificity",
        "f1",
        "roc_auc",
    ]:

        print(
            f"  {key}: "
            f"{raw_metrics[key]}"
        )

    print("\nConfusion matrix:")
    print(
        np.array(
            raw_metrics[
                "confusion_matrix"
            ]
        )
    )

    print("\nResults:")
    print(json_path)
    print(csv_path)


def main():
    """
    PURPOSE:
        Parse command-line arguments and start the independent evaluation.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Independent evaluator for "
            "Kaggle locked_model.pt"
        )
    )

    parser.add_argument(
        "--data-root",
        required=True,
        help=(
            "Path to Original dataset containing "
            "Stone and Non-Stone directories."
        ),
    )

    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Path to locked_model.pt",
    )

    parser.add_argument(
        "--output",
        default=(
            "outputs/evaluation/"
            "locked_model_external"
        ),
        help="Output directory.",
    )

    args = parser.parse_args()

    evaluate(args)


if __name__ == "__main__":
    main()