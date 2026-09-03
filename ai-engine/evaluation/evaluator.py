"""
evaluator.py — Evaluation runner that saves JSON results.

Usage:
    python evaluation/evaluator.py --task classification --checkpoint weights/classification/best_model.pth
    python evaluation/evaluator.py --task segmentation --checkpoint weights/segmentation/best_model.pth
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

_ENGINE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

from config.settings import get_training_cfg, get_paths_cfg
from evaluation.classification_metrics import compute_classification_metrics
from evaluation.segmentation_metrics import compute_segmentation_metrics
from models.classifier import build_classifier
from models.unet.unet import build_unet
from preprocessing.classification_transforms import get_classification_transforms
from preprocessing.ct_kidney_dataset import CTKidneyDataset
from preprocessing.kssd2025_dataset import KSSD2025Dataset
from preprocessing.segmentation_transforms import get_segmentation_transforms
from utils.logger import get_logger

log = get_logger("evaluator")


def evaluate_classification(checkpoint: str | Path, cfg: dict, paths: dict) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_classifier(cfg)
    ckpt = torch.load(checkpoint, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()

    splits_dir = paths["splits"]["classification_dir"]
    tf = get_classification_transforms("test", cfg["classification"]["input_size"])
    ds = CTKidneyDataset(splits_dir + "/test.csv", transform=tf)
    loader = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)

    y_true, y_pred, y_probs = [], [], []
    with torch.no_grad():
        for images, labels in tqdm(loader, desc="Evaluating classifier"):
            logits = model(images.to(device))
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            preds = logits.argmax(dim=1).cpu().tolist()
            y_probs.extend(probs.tolist())
            y_pred.extend(preds)
            y_true.extend(labels.tolist())

    return compute_classification_metrics(
        y_true, y_pred,
        y_prob=np.array(y_probs),
        class_names=cfg["classification"]["class_names"],
    )


def evaluate_segmentation(checkpoint: str | Path, cfg: dict, paths: dict) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_unet(cfg)
    ckpt = torch.load(checkpoint, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()

    splits_dir = paths["splits"]["segmentation_dir"]
    tf = get_segmentation_transforms("test", cfg["segmentation"]["input_size"])
    ds = KSSD2025Dataset(splits_dir + "/test.csv", transform=tf)
    loader = DataLoader(ds, batch_size=8, shuffle=False, num_workers=0)

    all_preds, all_targets = [], []
    with torch.no_grad():
        for images, masks in tqdm(loader, desc="Evaluating segmentation"):
            preds = model(images.to(device)).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(masks.numpy())

    return compute_segmentation_metrics(all_preds, all_targets)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=["classification", "segmentation"], required=True)
    p.add_argument("--checkpoint", type=str, required=True)
    p.add_argument("--output", type=str, default=None)
    args = p.parse_args()

    cfg = get_training_cfg()
    paths = get_paths_cfg()

    if args.task == "classification":
        results = evaluate_classification(args.checkpoint, cfg, paths)
    else:
        results = evaluate_segmentation(args.checkpoint, cfg, paths)

    # Print to console
    print(json.dumps({k: v for k, v in results.items() if k != "report"}, indent=2))
    if "report" in results:
        print("\nClassification Report:\n", results["report"])

    # Save
    output_path = args.output or f"outputs/evaluation/{args.task}_results.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    serializable = {k: v for k, v in results.items() if k != "report"}
    with open(output_path, "w") as f:
        json.dump(serializable, f, indent=2)
    log.info("Results saved", path=output_path)


if __name__ == "__main__":
    main()
