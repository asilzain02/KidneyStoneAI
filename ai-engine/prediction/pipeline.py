"""
pipeline.py — End-to-end KidneyStoneAI prediction pipeline.

Flow:
    CT Image
        ↓  Preprocessing
        ↓  EfficientNet-B0 → Classification result
        ↓  (if Stone) U-Net → Segmentation mask + stats
        ↓  Grad-CAM → Heatmap overlay
        ↓  Structured result dict

Each component (classify / segment / gradcam) is independently callable.

Usage:
    python prediction/pipeline.py --image path/to/ct.jpg
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

_ENGINE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

from config.settings import get_training_cfg, get_paths_cfg
from gradcam.gradcam_generator import GradCAMGenerator
from gradcam.visualizer import save_gradcam_result
from models.classifier import build_classifier
from postprocessing.mask_processor import MaskProcessor
from preprocessing.classification_transforms import get_classification_transforms
from segmentation.inference import SegmentationInference
from utils.logger import get_logger

log = get_logger("pipeline")

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]


class PredictionPipeline:
    """
    Orchestrates classification → (optional) segmentation → Grad-CAM.

    Parameters
    ----------
    clf_checkpoint  : path to classification best_model.pth
    seg_checkpoint  : path to segmentation best_model.pth (optional)
    cfg             : training config dict
    gradcam_output_dir : directory to save Grad-CAM images
    threshold       : segmentation probability threshold
    """

    def __init__(
        self,
        clf_checkpoint: str | Path,
        cfg: Dict,
        seg_checkpoint: Optional[str | Path] = None,
        gradcam_output_dir: Optional[str | Path] = None,
        threshold: float = 0.5,
    ):
        self.cfg = cfg
        self.threshold = threshold
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.gradcam_output_dir = gradcam_output_dir or "outputs/gradcam"
        self.class_names = cfg["classification"].get("class_names", CLASS_NAMES)

        # Classification model
        self._clf_model = build_classifier(cfg)
        ckpt = torch.load(clf_checkpoint, map_location=self.device)
        self._clf_model.load_state_dict(ckpt["model_state_dict"])
        self._clf_model.to(self.device).eval()
        log.info("Classifier loaded", checkpoint=str(clf_checkpoint))

        # Segmentation model (optional)
        self._seg_infer = None
        if seg_checkpoint and Path(seg_checkpoint).exists():
            self._seg_infer = SegmentationInference(seg_checkpoint, cfg, self.device)

        # Grad-CAM
        self._gradcam = GradCAMGenerator(
            self._clf_model,
            class_names=self.class_names,
            device=self.device,
        )

        # Classification transform (val/test — no augmentation)
        self._clf_transform = get_classification_transforms(
            "test", cfg["classification"]["input_size"]
        )

        # Mask postprocessor
        self._mask_proc = MaskProcessor(threshold=threshold)

    # ── Individual components (independently callable) ───────────────────────

    def classify(self, image: Image.Image) -> Dict:
        """Run classification only. Returns class + probabilities."""
        img_rgb = image.convert("RGB")
        tensor = self._clf_transform(img_rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self._clf_model(tensor)
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()

        pred_id = int(np.argmax(probs))
        return {
            "predicted_class": self.class_names[pred_id],
            "predicted_class_id": pred_id,
            "confidence": float(probs[pred_id]),
            "class_probabilities": {
                n: float(probs[i]) for i, n in enumerate(self.class_names)
            },
        }

    def segment(self, image: Image.Image) -> Dict:
        """Run segmentation only (requires seg model loaded)."""
        if self._seg_infer is None:
            raise RuntimeError("No segmentation model loaded.")
        result = self._seg_infer.predict(image, self.threshold)
        _, stats = self._mask_proc.process(result["prob_mask"])
        result["mask_statistics"] = stats
        return result

    def gradcam(self, image: Image.Image, stem: str = "result") -> Dict:
        """Run Grad-CAM only and save results."""
        img_rgb = image.convert("RGB")
        img_np = np.array(img_rgb).astype(np.float32) / 255.0
        tensor = self._clf_transform(img_rgb).unsqueeze(0)
        result = self._gradcam.generate(tensor, img_np)
        saved = save_gradcam_result(result, self.gradcam_output_dir, stem)
        result["saved_files"] = saved
        return result

    # ── Full pipeline ─────────────────────────────────────────────────────────

    def predict(
        self,
        image: Image.Image,
        stem: str = "prediction",
        run_segmentation: bool = True,
        run_gradcam: bool = True,
    ) -> Dict:
        """
        Full prediction pipeline.

        Returns structured prediction result dict.
        """
        output: Dict = {"stem": stem}

        # 1. Classification
        clf_result = self.classify(image)
        output["classification"] = clf_result
        log.info(
            "Classification",
            predicted=clf_result["predicted_class"],
            confidence=f"{clf_result['confidence']:.3f}",
        )

        # 2. Segmentation (only if Stone or explicitly requested)
        is_stone = clf_result["predicted_class"] == "Stone"
        if run_segmentation and (is_stone or self._seg_infer is not None):
            if self._seg_infer is not None:
                seg_result = self.segment(image)
                output["segmentation"] = {
                    "stone_area_pixels": seg_result["stone_area_pixels"],
                    "mask_statistics": seg_result.get("mask_statistics", {}),
                }
                log.info(
                    "Segmentation",
                    stone_pixels=seg_result["stone_area_pixels"],
                )
            else:
                output["segmentation"] = {
                    "note": "Segmentation model not loaded."
                }

        # 3. Grad-CAM
        if run_gradcam:
            cam_result = self.gradcam(image, stem=stem)
            output["gradcam"] = {
                "predicted_class": cam_result["predicted_class"],
                "confidence": cam_result["confidence"],
                "saved_files": cam_result.get("saved_files", {}),
            }

        return output


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run KidneyStoneAI inference pipeline")
    parser.add_argument("--image", required=True, help="Path to input CT image")
    parser.add_argument("--clf-checkpoint", default=None)
    parser.add_argument("--seg-checkpoint", default=None)
    parser.add_argument("--output-dir", default="outputs/predictions")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--no-seg", action="store_true")
    parser.add_argument("--no-gradcam", action="store_true")
    args = parser.parse_args()

    cfg = get_training_cfg()
    paths = get_paths_cfg()

    clf_ckpt = args.clf_checkpoint or paths["weights"]["classification_best"]
    seg_ckpt = args.seg_checkpoint or paths["weights"]["segmentation_best"]

    if not Path(clf_ckpt).exists():
        log.error("Classification checkpoint not found", path=clf_ckpt)
        sys.exit(1)

    pipeline = PredictionPipeline(
        clf_checkpoint=clf_ckpt,
        cfg=cfg,
        seg_checkpoint=seg_ckpt if Path(seg_ckpt).exists() else None,
        gradcam_output_dir=str(Path(args.output_dir) / "gradcam"),
        threshold=args.threshold,
    )

    image = Image.open(args.image)
    stem = Path(args.image).stem
    result = pipeline.predict(
        image,
        stem=stem,
        run_segmentation=not args.no_seg,
        run_gradcam=not args.no_gradcam,
    )

    out_path = Path(args.output_dir) / f"{stem}_prediction.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(
            {k: v for k, v in result.items() if not isinstance(v, np.ndarray)},
            f,
            indent=2,
        )
    log.info("Prediction saved", path=str(out_path))
    print(json.dumps(result["classification"], indent=2))


if __name__ == "__main__":
    main()
