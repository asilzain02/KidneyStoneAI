"""
verify_segmentation_visualizer.py

This script hits the AI engine endpoints (locally spinning up pipeline.py manually)
to simulate classification outputs directly, bypassing uvicorn, yielding immediate
analysis on dimensional matches and overlay existence between GradCAM and Seg outputs.
"""
from pathlib import Path
import sys
import numpy as np
from PIL import Image

_ENGINE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

from prediction.pipeline import PredictionPipeline
from config.settings import get_training_cfg, get_paths_cfg

def run_checks():
    cfg = get_training_cfg()
    paths = get_paths_cfg()
    
    clf_ckpt = paths["weights"]["classification_best"]
    seg_ckpt = paths["weights"]["segmentation_best"]
    
    # Needs a real image
    manifest = Path(paths["manifests"]["classification"])
    if not manifest.exists():
        print("Manifest missing")
        return
        
    line = open(manifest).readlines()[3].strip().split(",")
    img_path = line[0] # assuming path is col 0
    img = Image.open(img_path).convert("RGB")
    
    print(f"Testing on image: {img_path}")
    
    pipeline = PredictionPipeline(
        clf_checkpoint=clf_ckpt,
        seg_checkpoint=seg_ckpt,
        cfg=cfg,
        gradcam_output_dir="outputs/gradcam",
        threshold=0.5
    )
    
    # ── CASE 1: Stone (Happy Path) ──
    print("\n--- CASE 1: STONE & SEGMENT DETECTED ---")
    result = pipeline.predict(img, stem="test_stone", run_segmentation=True, run_gradcam=True)
    
    seg = result["segmentation"]["saved_files"]
    gc = result["gradcam"]["saved_files"]
    
    seg_overlay = Path("outputs/gradcam") / Path(seg["overlayPath"]).name
    seg_mask = Path("outputs/gradcam") / Path(seg["maskPath"]).name
    gc_overlay = Path(gc["overlay"])
    
    assert seg_overlay.exists(), "Seg overlay missing"
    assert seg_mask.exists(),    "Seg mask missing"
    assert gc_overlay.exists(),  "GC overlay missing"
    
    img_o = Image.open(seg_overlay)
    img_g = Image.open(gc_overlay)
    
    print(f"Original CT dimensions: {img.size}")
    print(f"Seg Overlay dimensions: {img_o.size}")
    print(f"GradCAM Overlay dimensions: {img_g.size}")
    
    assert img_o.size == img.size, "Seg overlay size mismatch"
    assert img_g.size[0] in [224, 320], "GC overlay should match model feature space"
    
    # Check pixels
    arr_mask = np.array(Image.open(seg_mask))
    print(f"Seg Mask positive pixels: {np.sum(arr_mask > 0)}")
    
    # Ensure Seg is NOT GradCAM
    import cv2
    arr_o = np.array(img_o)
    arr_g = np.array(img_g)
    arr_g_resized = cv2.resize(arr_g, (img.size[0], img.size[1]))
    diff = np.sum(np.abs(arr_o.astype(float) - arr_g_resized.astype(float)))
    print(f"Difference between Seg and GC Overlays: {diff}")
    assert diff > 0, "Seg overlay and GradCAM overlay are identical!"
    
    # ── CASE 2: Force Normal ──
    print("\n--- CASE 2: NORMAL CLASSIFICATION & STONE DETECTED ---")
    # We will hijack the classifier to output Normal
    pipeline.classify = lambda *args: {
        "predicted_class": "Normal", "confidence": 0.99, "class_probabilities": {"Normal": 0.99, "Stone": 0.0}
    }
    # And hijack segmentation to find stone
    pipeline.segment = lambda *args: {
        "stone_area_pixels": 500,
        "mask_statistics": {"total_pixels": 1000},
        "binary_mask_cleaned": np.ones((img.size[1], img.size[0]), dtype=np.uint8)
    }
    
    result2 = pipeline.predict(img, stem="test_disagreement", run_segmentation=True, run_gradcam=True)
    print("MOCKED: Classification ->", result2["classification"]["predicted_class"])
    print("MOCKED: Seg Pixels ->", result2["segmentation"]["stone_area_pixels"])
    
    print("\nAll independent validations triggered properly.")

if __name__ == "__main__":
    run_checks()
