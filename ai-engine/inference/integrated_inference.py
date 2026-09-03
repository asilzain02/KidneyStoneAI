"""
integrated_inference.py

End-to-end Kidney Stone AI inference.

Input:
    One CT image (.jpg, .jpeg, .png, .tif, .tiff)

Runs:
    1. Classification
    2. EXP02 Tversky segmentation
    3. Stone mask measurement
    4. Integrated consistency analysis
    5. Visualization
    6. JSON result

Usage:
    python ai-engine/inference/integrated_inference.py \
        --image "path/to/ct_image.jpg"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw

# ============================================================================
# PATH SETUP
# ============================================================================

HERE = Path(__file__).resolve()
ENGINE_ROOT = HERE.parents[1]
PROJECT_ROOT = ENGINE_ROOT.parent

sys.path.insert(0, str(ENGINE_ROOT))

# ============================================================================
# PROJECT IMPORTS
# ============================================================================

from config.settings import get_training_cfg

from models.classifier import build_classifier
from models.unet.unet import build_unet

from preprocessing.classification_transforms import (
    get_classification_transforms
)

from preprocessing.segmentation_transforms import (
    get_segmentation_transforms
)


# ============================================================================
# CONSTANTS
# ============================================================================

CLASS_NAMES = [
    "Normal",
    "Cyst",
    "Stone",
    "Tumor",
]

STONE_INDEX = CLASS_NAMES.index("Stone")

CLASSIFICATION_CHECKPOINT = (
    ENGINE_ROOT / "weights" / "classification" / "final_candidate_exp02a.pth"
)

SEGMENTATION_CHECKPOINT = (
    ENGINE_ROOT / "weights" / "segmentation" / "FINAL_SEGMENTATION_MODEL.pth"
)

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT / "outputs" / "integrated_inference"
)


# ============================================================================
# DEVICE
# ============================================================================

def get_device():
    return torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )


# ============================================================================
# LOAD CLASSIFICATION MODEL
# ============================================================================

def load_classification_model(cfg, device):

    print("\nLoading classification model...")
    print(f"Checkpoint: {CLASSIFICATION_CHECKPOINT}")

    if not CLASSIFICATION_CHECKPOINT.exists():
        raise FileNotFoundError(
            f"Classification checkpoint not found:\n"
            f"{CLASSIFICATION_CHECKPOINT}"
        )

    model = build_classifier(cfg)

    checkpoint = torch.load(
        CLASSIFICATION_CHECKPOINT,
        map_location=device
    )

    state_dict = checkpoint.get(
        "model_state_dict",
        checkpoint
    )

    model.load_state_dict(state_dict)

    model.to(device)
    model.eval()

    print("Classification model loaded.")

    return model


# ============================================================================
# LOAD SEGMENTATION MODEL
# ============================================================================

def load_segmentation_model(cfg, device):

    print("\nLoading EXP02 segmentation model...")
    print(f"Checkpoint: {SEGMENTATION_CHECKPOINT}")

    if not SEGMENTATION_CHECKPOINT.exists():
        raise FileNotFoundError(
            f"Segmentation checkpoint not found:\n"
            f"{SEGMENTATION_CHECKPOINT}"
        )

    model = build_unet(cfg)

    checkpoint = torch.load(
        SEGMENTATION_CHECKPOINT,
        map_location=device
    )

    state_dict = checkpoint.get(
        "model_state_dict",
        checkpoint
    )

    model.load_state_dict(state_dict)

    model.to(device)
    model.eval()

    print("EXP02 Tversky segmentation model loaded.")

    return model


# ============================================================================
# CLASSIFICATION
# ============================================================================

def run_classification(
    model,
    image,
    cfg,
    device
):

    input_size = (
        cfg.get("classification", {})
        .get("input_size", 224)
    )

    transform = get_classification_transforms(
        "test",
        input_size
    )

    tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():

        logits = model(tensor)

        probabilities = torch.softmax(
            logits,
            dim=1
        )[0]

    probabilities_np = (
        probabilities
        .detach()
        .cpu()
        .numpy()
    )

    predicted_index = int(
        np.argmax(probabilities_np)
    )

    predicted_class = CLASS_NAMES[
        predicted_index
    ]

    confidence = float(
        probabilities_np[predicted_index]
    )

    class_probabilities = {
        CLASS_NAMES[i]: float(
            probabilities_np[i]
        )
        for i in range(len(CLASS_NAMES))
    }

    return {
        "predicted_class": predicted_class,
        "predicted_class_id": predicted_index,
        "confidence": confidence,
        "class_probabilities": class_probabilities,
    }


# ============================================================================
# SEGMENTATION TRANSFORM ADAPTER
# ============================================================================

def prepare_segmentation_input(
    image,
    transform,
    input_size
):
    """
    Tries to use the project's existing segmentation
    transform without changing its implementation.

    Supports common transform styles:
        transform(PIL)
        transform(np_array)
        transform(image=np_array)
    """

    image_np = np.array(image.convert("L"))

    # ------------------------------------------------------------------------
    # Try dictionary-style transform
    # ------------------------------------------------------------------------

    try:

        result = transform(
            image=image_np
        )

        if isinstance(result, dict):

            result_image = result.get("image")

            if result_image is not None:
                tensor = result_image

                if not torch.is_tensor(tensor):
                    tensor = torch.as_tensor(
                        tensor,
                        dtype=torch.float32
                    )

                return tensor

    except Exception:
        pass

    # ------------------------------------------------------------------------
    # Try PIL transform
    # ------------------------------------------------------------------------

    try:

        result = transform(image)

        if isinstance(result, dict):
            result = result["image"]

        if torch.is_tensor(result):
            return result

        return torch.as_tensor(
            result,
            dtype=torch.float32
        )

    except Exception:
        pass

    # ------------------------------------------------------------------------
    # Fallback preprocessing
    # ------------------------------------------------------------------------

    resized = image.convert("L").resize(
        (input_size, input_size)
    )

    arr = np.asarray(
        resized,
        dtype=np.float32
    ) / 255.0

    tensor = torch.from_numpy(arr)

    tensor = tensor.unsqueeze(0)

    return tensor


# ============================================================================
# SEGMENTATION
# ============================================================================

def run_segmentation(
    model,
    image,
    cfg,
    device,
    threshold=0.5
):

    seg_cfg = cfg.get(
        "segmentation",
        cfg
    )

    input_size = seg_cfg.get(
        "input_size",
        cfg.get("input", {}).get(
            "size",
            256
        )
    )

    transform = get_segmentation_transforms(
        "test",
        input_size
    )

    tensor = prepare_segmentation_input(
        image=image,
        transform=transform,
        input_size=input_size
    )

    # Ensure CHW format
    if tensor.ndim == 2:
        tensor = tensor.unsqueeze(0)

    # Ensure batch dimension
    if tensor.ndim == 3:
        tensor = tensor.unsqueeze(0)

    tensor = tensor.to(
        device=device,
        dtype=torch.float32
    )

    with torch.no_grad():

        prediction = model(tensor)

    # U-Net output expected to be [B,1,H,W]
    prediction = prediction.squeeze()

    probability_mask = (
        prediction
        .detach()
        .cpu()
        .numpy()
    )

    binary_mask = (
        probability_mask >= threshold
    ).astype(np.uint8)

    return {
        "probability_mask": probability_mask,
        "binary_mask": binary_mask,
        "threshold": threshold,
    }


# ============================================================================
# MASK MEASUREMENTS
# ============================================================================

def calculate_mask_measurements(mask):

    total_pixels = int(mask.size)

    stone_pixels = int(
        np.sum(mask > 0)
    )

    percentage = (
        stone_pixels / total_pixels * 100
        if total_pixels > 0
        else 0.0
    )

    ys, xs = np.where(mask > 0)

    if len(xs) == 0:

        return {
            "detected": False,
            "area_pixels": 0,
            "area_percentage": 0.0,
            "bounding_box": None,
        }

    x_min = int(xs.min())
    x_max = int(xs.max())
    y_min = int(ys.min())
    y_max = int(ys.max())

    return {
        "detected": True,
        "area_pixels": stone_pixels,
        "area_percentage": percentage,
        "bounding_box": {
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max,
            "width": x_max - x_min + 1,
            "height": y_max - y_min + 1,
        },
    }


# ============================================================================
# INTEGRATION LOGIC
# ============================================================================

def generate_integrated_interpretation(
    classification,
    segmentation_measurements
):

    predicted_class = (
        classification["predicted_class"]
    )

    classifier_confidence = (
        classification["confidence"]
    )

    segmentation_detected = (
        segmentation_measurements["detected"]
    )

    # ------------------------------------------------------------------------
    # Agreement
    # ------------------------------------------------------------------------

    if predicted_class == "Stone":

        if segmentation_detected:

            status = "CONSISTENT"

            message = (
                "Classification predicts kidney stone "
                "and segmentation detected a corresponding "
                "region."
            )

        else:

            status = "PARTIAL_DISAGREEMENT"

            message = (
                "Classification predicts kidney stone, "
                "but segmentation did not detect a region."
            )

    else:

        if segmentation_detected:

            status = "DISAGREEMENT"

            message = (
                "Classification predicts a non-stone condition, "
                "but segmentation detected a region."
            )

        else:

            status = "CONSISTENT"

            message = (
                "Classification predicts a non-stone condition "
                "and segmentation did not detect a region."
            )

    return {
        "status": status,
        "message": message,
        "classifier_prediction": predicted_class,
        "classifier_confidence": classifier_confidence,
        "segmentation_detected": segmentation_detected,
    }


# ============================================================================
# VISUALIZATION
# ============================================================================

def create_visualization(
    image,
    segmentation,
    classification,
    output_path
):

    original = image.convert("RGB")

    original_np = np.array(original)

    mask = segmentation["binary_mask"]

    # Resize mask to original image dimensions
    mask_img = Image.fromarray(
        (mask * 255).astype(np.uint8)
    )

    mask_img = mask_img.resize(
        original.size,
        Image.Resampling.NEAREST
    )

    mask_np = np.array(mask_img)

    overlay = original_np.copy()

    # Green segmentation overlay
    green = np.zeros_like(
        original_np
    )

    green[:, :, 1] = 255

    alpha = 0.45

    selected = mask_np > 0

    overlay[selected] = (
        original_np[selected] * (1 - alpha)
        + green[selected] * alpha
    ).astype(np.uint8)

    overlay_image = Image.fromarray(
        overlay
    )

    # Draw bounding box
    measurements = calculate_mask_measurements(
        mask_np
    )

    draw = ImageDraw.Draw(
        overlay_image
    )

    bbox = measurements["bounding_box"]

    if bbox:

        draw.rectangle(
            [
                bbox["x_min"],
                bbox["y_min"],
                bbox["x_max"],
                bbox["y_max"],
            ],
            outline="red",
            width=3
        )

    # ------------------------------------------------------------------------
    # Create side-by-side image
    # ------------------------------------------------------------------------

    width, height = original.size

    canvas = Image.new(
        "RGB",
        (width * 3, height + 100),
        "black"
    )

    canvas.paste(
        original,
        (0, 100)
    )

    canvas.paste(
        Image.fromarray(
            np.stack(
                [mask_np * 255] * 3,
                axis=-1
            ).astype(np.uint8)
        ),
        (width, 100)
    )

    canvas.paste(
        overlay_image,
        (width * 2, 100)
    )

    draw = ImageDraw.Draw(
        canvas
    )

    draw.text(
        (10, 20),
        "Original CT",
        fill="white"
    )

    draw.text(
        (width + 10, 20),
        "Segmentation Mask",
        fill="white"
    )

    draw.text(
        (width * 2 + 10, 20),
        "Integrated Result",
        fill="white"
    )

    predicted_class = classification[
        "predicted_class"
    ]

    confidence = classification[
        "confidence"
    ]

    draw.text(
        (10, 55),
        f"Classification: {predicted_class} "
        f"({confidence:.3f})",
        fill="white"
    )

    draw.text(
        (width + 10, 55),
        f"Stone pixels: "
        f"{measurements['area_pixels']}",
        fill="white"
    )

    draw.text(
        (width * 2 + 10, 55),
        f"Detected: "
        f"{measurements['detected']}",
        fill="white"
    )

    canvas.save(
        output_path
    )


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_pipeline(
    image_path,
    output_dir,
    threshold=0.5
):

    image_path = Path(
        image_path
    ).resolve()

    output_dir = Path(
        output_dir
    ).resolve()

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    if not image_path.exists():
        raise FileNotFoundError(
            f"Input image not found:\n{image_path}"
        )

    print("\n" + "=" * 70)
    print("KIDNEY STONE AI — INTEGRATED INFERENCE")
    print("=" * 70)

    print(f"Input : {image_path}")
    print(f"Output: {output_dir}")

    device = get_device()

    print(f"Device: {device}")

    cfg = get_training_cfg()

    image = Image.open(
        image_path
    ).convert("RGB")

    print(
        f"Image size: {image.size}"
    )

    # ------------------------------------------------------------------------
    # Load models
    # ------------------------------------------------------------------------

    classification_model = (
        load_classification_model(
            cfg,
            device
        )
    )

    segmentation_model = (
        load_segmentation_model(
            cfg,
            device
        )
    )

    # ------------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------------

    print("\nRunning classification...")

    classification_result = (
        run_classification(
            classification_model,
            image,
            cfg,
            device
        )
    )

    print("\nClassification Result")

    print(
        f"  Prediction : "
        f"{classification_result['predicted_class']}"
    )

    print(
        f"  Confidence : "
        f"{classification_result['confidence']:.4f}"
    )

    for name, probability in (
        classification_result[
            "class_probabilities"
        ].items()
    ):

        print(
            f"  {name:<10}: "
            f"{probability:.4f}"
        )

    # ------------------------------------------------------------------------
    # Segmentation
    # ------------------------------------------------------------------------

    print("\nRunning EXP02 segmentation...")

    segmentation_result = (
        run_segmentation(
            segmentation_model,
            image,
            cfg,
            device,
            threshold
        )
    )

    measurements = (
        calculate_mask_measurements(
            segmentation_result[
                "binary_mask"
            ]
        )
    )

    print("\nSegmentation Result")

    print(
        f"  Detected       : "
        f"{measurements['detected']}"
    )

    print(
        f"  Area pixels    : "
        f"{measurements['area_pixels']}"
    )

    print(
        f"  Area percentage: "
        f"{measurements['area_percentage']:.4f}%"
    )

    # ------------------------------------------------------------------------
    # Integration
    # ------------------------------------------------------------------------

    integrated = (
        generate_integrated_interpretation(
            classification_result,
            measurements
        )
    )

    print("\nIntegrated Interpretation")

    print(
        f"  Status : "
        f"{integrated['status']}"
    )

    print(
        f"  Result : "
        f"{integrated['message']}"
    )

    # ------------------------------------------------------------------------
    # Save mask
    # ------------------------------------------------------------------------

    mask_path = (
        output_dir / "segmentation_mask.png"
    )

    Image.fromarray(
        (
            segmentation_result[
                "binary_mask"
            ] * 255
        ).astype(np.uint8)
    ).resize(
        image.size,
        Image.Resampling.NEAREST
    ).save(mask_path)

    # ------------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------------

    visualization_path = (
        output_dir / "integrated_result.png"
    )

    create_visualization(
        image=image,
        segmentation=segmentation_result,
        classification=classification_result,
        output_path=visualization_path
    )

    # ------------------------------------------------------------------------
    # JSON result
    # ------------------------------------------------------------------------

    result = {
        "timestamp": datetime.now().isoformat(),

        "input": {
            "image": str(image_path),
            "width": image.width,
            "height": image.height,
        },

        "models": {
            "classification_checkpoint": str(
                CLASSIFICATION_CHECKPOINT
            ),
            "segmentation_checkpoint": str(
                SEGMENTATION_CHECKPOINT
            ),
            "segmentation_experiment": (
                "EXP02_LOSS_TVERSKY"
            ),
            "segmentation_threshold": threshold,
        },

        "classification": (
            classification_result
        ),

        "segmentation": {
            "detected": measurements[
                "detected"
            ],
            "area_pixels": measurements[
                "area_pixels"
            ],
            "area_percentage": measurements[
                "area_percentage"
            ],
            "bounding_box": measurements[
                "bounding_box"
            ],
        },

        "integrated_result": integrated,

        "outputs": {
            "mask": str(mask_path),
            "visualization": str(
                visualization_path
            ),
        },
    }

    result_path = (
        output_dir / "integrated_result.json"
    )

    with open(
        result_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=4
        )

    print("\n" + "=" * 70)
    print("INFERENCE COMPLETE")
    print("=" * 70)

    print(
        f"JSON          : {result_path}"
    )

    print(
        f"Segmentation  : {mask_path}"
    )

    print(
        f"Visualization : {visualization_path}"
    )

    print("=" * 70 + "\n")

    return result


# ============================================================================
# CLI
# ============================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Integrated Kidney Stone "
            "Classification + Segmentation"
        )
    )

    parser.add_argument(
        "--image",
        required=True,
        help="Path to CT image"
    )

    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Segmentation threshold"
    )

    args = parser.parse_args()

    run_pipeline(
        image_path=args.image,
        output_dir=args.output,
        threshold=args.threshold
    )


if __name__ == "__main__":
    main()