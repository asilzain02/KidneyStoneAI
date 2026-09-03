"""
external_evaluator.py — CLI Executor evaluating independently against the Axial CT Kidney Stone Data
"""

from __future__ import annotations

import argparse
import sys
import json
import csv
from pathlib import Path
from tqdm import tqdm
from PIL import Image

import torch

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import get_training_cfg
from datasets.external.axial_kidney_stone_adapter import AxialKidneyStoneAdapter
from evaluation.external_metrics import compute_external_binary_metrics
from models.classifier import build_classifier
from preprocessing.classification_transforms import get_classification_transforms

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]

def map_four_class_to_binary(class_name: str) -> str:
    """
    CRITICAL: Validates mapping logic. 
    Stone -> STONE
    Normal / Cyst / Tumor -> NON_STONE
    """
    if class_name == "Stone":
        return "STONE"
    return "NON_STONE"

def evaluate_external(args: argparse.Namespace) -> None:
    # 1. Safety Checks
    print("============================================================")
    print("EXTERNAL EVALUATION MODE")
    print("============================================================")
    print("Training: DISABLED")
    print("Fine-tuning: DISABLED")
    print("Dataset: Axial CT Kidney Stone Dataset")
    print("Subset: Original ONLY")
    print("Augmented data: EXCLUDED")
    print(f"Checkpoint: {args.checkpoint}")
    print("============================================================")
    
    cfg = get_training_cfg()
    
    # 2. Discover External Data
    data_root = Path(args.data_root).resolve()

    if data_root.name.lower() != "original":
        raise ValueError(
            f"SAFETY ERROR: External evaluation must use the Original dataset only. "
            f"Received: {data_root}"
        )

    if "augmented" in str(data_root).lower():
        raise ValueError(
            "SAFETY ERROR: Augmented dataset is strictly prohibited for external evaluation."
        )

    adapter = AxialKidneyStoneAdapter(args.data_root)
    adapter.discover()
    
    if adapter.get_stats()["valid"] == 0:
        print("FAILED: No valid external Original boundaries found.")
        return
        
    records = adapter.get_records()
    
    # 3. Model Loading
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nDevice: {device.type.upper()}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        
    # Re-use classification architecture (NO RE-TRAINING)
    model = build_classifier(cfg)
    
    ckpt_path = Path(args.checkpoint)
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Missing Checkpoint: {ckpt_path}")
        
    checkpoint = torch.load(ckpt_path, map_location=device)
    # Handle direct state_dicts or structured checkpoints
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)
        
    model.to(device)
    model.eval() # STRICT EVAL MODE
    
    # 4. Preprocessing natively bounding to deterministic values, no flip/crop augmentations
    input_size = cfg["classification"].get("input_size", 224)   # input_size = cfg.get("input_size", 224)
    transforms = get_classification_transforms("test", input_size)
    
    # 5. Inference
    y_true_bin = []
    y_pred_bin = []
    prob_stone_list = []
    csv_rows = []
    
    print("\nRunning Independent External Inference...")
    with torch.no_grad():
        for rec in tqdm(records, desc="Inference"):
            img_path = rec["image_path"]
            gt_bin = rec["ground_truth"]
            
            try:
                img = Image.open(img_path).convert("RGB")
            except Exception:
                continue
                
            tensor = transforms(img).unsqueeze(0).to(device)
            logits = model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()
            
            pred_idx = int(torch.argmax(logits, dim=1).item())
            pred_class = CLASS_NAMES[pred_idx]
            
            # Map logic bounds from existing metrics
            pred_bin = map_four_class_to_binary(pred_class)
            
            y_true_bin.append(gt_bin)
            y_pred_bin.append(pred_bin)
            
            stone_idx = CLASS_NAMES.index("Stone")
            stone_prob = float(probs[stone_idx])
            prob_stone_list.append(stone_prob)
            
            row = {
                "image_path": img_path,
                "filename": rec["filename"],
                "ground_truth": gt_bin,
                "predicted_class": pred_class,
                "predicted_binary_class": pred_bin,
                "normal_probability": float(probs[0]),
                "cyst_probability": float(probs[1]),
                "stone_probability": float(probs[2]),
                "tumor_probability": float(probs[3]),
                "confidence": float(probs[pred_idx]),
                "correct": (gt_bin == pred_bin)
            }
            csv_rows.append(row)
            img.close()
            
    # 6. Logging
    metrics = compute_external_binary_metrics(y_true_bin, y_pred_bin, prob_stone_list)
    
    output_dir = Path(args.output) / "external"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / "external_results.json"
    csv_path = output_dir / "external_predictions.csv"

    evaluated_images = len(y_true_bin)
    
    result_dict = {
        "dataset": "Axial CT Kidney Stone Dataset",
        "subset": "Original",
        "augmented_images_used": 0,
        "total_images": adapter.get_stats()["total"],
        "total_discovered_images": adapter.get_stats()["total"],
        "total_evaluated_images": evaluated_images,
        "failed_images": adapter.get_stats()["total"] - evaluated_images,
        "stone_images": adapter.get_stats()["stone"],
        "non_stone_images": adapter.get_stats()["non_stone"],
        "model": "EfficientNet-B0",
        "checkpoint": str(ckpt_path),
        "device": device.type.upper(),
        "mapping": {
            "Stone": "STONE",
            "Normal": "NON_STONE",
            "Cyst": "NON_STONE",
            "Tumor": "NON_STONE"
        },
        "metrics": {
            "accuracy": metrics.get("accuracy"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "specificity": metrics.get("specificity"),
            "f1": metrics.get("f1"),
            "roc_auc": metrics.get("roc_auc")
        },
        "confusion_matrix": metrics.get("confusion_matrix"),
        "counts": metrics.get("counts")
    }
    
    with open(json_path, "w") as f:
        json.dump(result_dict, f, indent=4)

    csv_fields = [
        "image_path",
        "filename",
        "ground_truth",
        "predicted_class",
        "predicted_binary_class",
        "normal_probability",
        "cyst_probability",
        "stone_probability",
        "tumor_probability",
        "confidence",
        "correct",
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(csv_rows)

    # with open(csv_path, "w", newline="") as f:
    #     writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
    #     writer.writeheader()
    #     writer.writerows(csv_rows)
        
    print("\nExternal Dataset Evaluation Complete.")
    print(f"Results saved to: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="External Dataset Evaluator (Inference Only)")
    parser.add_argument("--data-root", type=str, default="datasets/raw/classification/additional_dataset/Kidney Stone Dataset/Original",
                        help="Path to Original subset. Must explicitly isolate bounding out Augmented data.")
    parser.add_argument("--checkpoint", type=str, default="ai-engine/weights/classification/best_model.pth",
                        help="Path to the pretrained classification PyTorch checkpoint")
    parser.add_argument("--output", type=str, default="outputs/evaluation",
                        help="Base output dir where /external logging happens")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Batch limit logic scaling (currently unused for strict 1-by-1 evaluation boundary precision looping).")
    
    args = parser.parse_args()
    evaluate_external(args)

if __name__ == "__main__":
    main()
