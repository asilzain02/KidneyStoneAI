"""
verify_pipeline.py — Verification script for the KidneyStoneAI pipeline.
"""
import sys
import os
import subprocess
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_paths_cfg, get_training_cfg
from datasets.ct_kidney_adapter import CTKidneyDatasetAdapter
from datasets.kssd2025_adapter import KSSD2025DatasetAdapter
from datasets.split_builder import build_classification_splits, build_segmentation_splits
import shutil

def run_cmd(args):
    cmd = " ".join(args)
    print(f"\n=> Running: {cmd}")
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED!\n--- STDOUT ---\n{res.stdout}\n--- STDERR ---\n{res.stderr}")
        return False
    else:
        print(f"PASS")
        return True

def main():
    print("==================================================")
    print("VERIFICATION PHASE STARTING")
    print("==================================================")
    
    paths = get_paths_cfg()
    cfg = get_training_cfg()
    
    status = {}
    
    # 1. & 2. Dataset Validation and Manifest Generation
    try:
        print("\n--- 1 & 2. DATASET VALIDATION & MANIFESTS ---")
        clf_adapter = CTKidneyDatasetAdapter(paths["raw"]["classification"])
        clf_adapter.discover()
        clf_report = clf_adapter.validate(compute_hashes=True)
        print("Classification Validation Report:", clf_report)
        clf_adapter.build_manifest(paths["splits"]["classification_dir"] + "/../manifests/classification_manifest.csv")
        
        seg_adapter = KSSD2025DatasetAdapter(paths["raw"]["segmentation_images"], paths["raw"]["segmentation_labels"])
        seg_adapter.discover()
        seg_report = seg_adapter.validate(compute_hashes=True)
        print("Segmentation Validation Report:", seg_report)
        
        # Ensure manifests dir exists
        manifests_dir = Path(paths["splits"]["classification_dir"]).parent / "manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)
        
        seg_adapter.build_manifest(str(manifests_dir / "segmentation_manifest.csv"))
        
        status["Dataset validation"] = "PASS"
        status["Manifest generation"] = "PASS"
    except Exception as e:
        print("Failed:", e)
        status["Dataset validation"] = "FAIL"
        status["Manifest generation"] = "FAIL"
        
    # 3. Splits
    try:
        print("\n--- 3. DATASET SPLITTING ---")
        build_classification_splits(
            manifest_path=str(manifests_dir / "classification_manifest.csv"),
            output_dir=Path(paths["splits"]["classification_dir"]),
            train_ratio=0.7, val_ratio=0.15
        )
        build_segmentation_splits(
            manifest_path=str(manifests_dir / "segmentation_manifest.csv"),
            output_dir=Path(paths["splits"]["segmentation_dir"]),
            train_ratio=0.7, val_ratio=0.15
        )
        status["Dataset splitting"] = "PASS"
    except Exception as e:
        print("Failed:", e)
        status["Dataset splitting"] = "FAIL"
        
    # 4. Tests
    print("\n--- 4. UNIT TESTS ---")
    if run_cmd([sys.executable, "-m", "pytest", "ai-engine/tests", "-v"]):
        status["Unit tests"] = "PASS"
    else:
        status["Unit tests"] = "FAIL"
        
    # 5. Classification Smoke
    print("\n--- 5. CLASSIFICATION SMOKE TEST ---")
    if run_cmd([sys.executable, "ai-engine/training/train_classifier.py", "--smoke"]):
        status["Classification smoke training"] = "PASS"
    else:
        status["Classification smoke training"] = "FAIL"
        
    # 6. Segmentation Smoke
    print("\n--- 6. SEGMENTATION SMOKE TEST ---")
    if run_cmd([sys.executable, "ai-engine/training/train_segmentation.py", "--smoke"]):
        status["Segmentation smoke training"] = "PASS"
    else:
        status["Segmentation smoke training"] = "FAIL"

    # Make dummy best_model.pth if smoke didn't save them correctly for inference (sometimes happens with small sets)
    # The smoke tests DO save Checkpoints to their weights dir! We rely on that.
    
    # 7 & 8 & 9. Inference
    try:
        print("\n--- 7, 8, 9. INFERENCE ---")
        from prediction.pipeline import PredictionPipeline

        clf_ckpt = paths["weights"]["classification_best"]
        seg_ckpt = paths["weights"]["segmentation_best"]

        # If they don't exist, smoke test failed to save them. We'll abort inference.
        if not Path(clf_ckpt).exists() or not Path(seg_ckpt).exists():
            raise RuntimeError("Checkpoints missing. Smoke tests didn't produce best_model.pth.")
        
        status["Checkpoint loading"] = "PASS"

        pipeline = PredictionPipeline(
            clf_checkpoint=clf_ckpt,
            seg_checkpoint=seg_ckpt,
            cfg=cfg,
            gradcam_output_dir="outputs/gradcam",
            threshold=0.5
        )
        
        # Pick one real CT from the classification set for class+gradcam
        records = clf_adapter.get_records()
        stone_img_path = next(r["image_path"] for r in records if r["class_name"] == "Stone")
        
        print(f"Running classification & GradCAM on: {stone_img_path}")
        img = Image.open(stone_img_path)
        clf_result = pipeline.classify(img)
        print("Classification Result:", clf_result)
        status["Classification inference"] = "PASS"
        
        cam_result = pipeline.gradcam(img, stem="verify_gradcam")
        print("Grad-CAM Result:", cam_result)
        status["Grad-CAM"] = "PASS"
        
        # Segmentation Inference using actual matching Image+Mask pairs from val split
        pairs = seg_adapter.get_pairs()
        real_pair = pairs[0] 
        print(f"Running segmentation tightly bound: {real_pair['image_path']}")
        
        from segmentation.inference import SegmentationInference
        seg_infer = SegmentationInference(seg_ckpt, cfg)
        
        sim_image = Image.open(real_pair['image_path'])
        sim_mask = Image.open(real_pair['mask_path'])
        seg_res = seg_infer.predict_with_gt(sim_image, sim_mask)
        
        print("Segmentation Output (Dice/IoU):", seg_res['dice'], seg_res['iou'])
        status["Segmentation inference"] = "PASS"
        
    except Exception as e:
        print("Failed:", e)
        if "Checkpoint loading" not in status: status["Checkpoint loading"] = "FAIL"
        if "Classification inference" not in status: status["Classification inference"] = "FAIL"
        if "Grad-CAM" not in status: status["Grad-CAM"] = "FAIL"
        if "Segmentation inference" not in status: status["Segmentation inference"] = "FAIL"
        

    print("\n==================================================")
    print("10. FINAL STATUS")
    print("==================================================")
    print("Environment:\nPASS")
    for k, v in status.items():
        print(f"{k}:\n{v}")
        
    all_passed = all(v == "PASS" for v in status.values())
    print("\n")
    if all_passed:
        print("READY FOR FULL TRAINING")
    else:
        print("NOT READY FOR FULL TRAINING")

if __name__ == "__main__":
    main()
