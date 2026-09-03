"""
visualizer.py — Save Grad-CAM results to disk.

Saves:
  {output_dir}/{stem}_original.png
  {output_dir}/{stem}_heatmap.png
  {output_dir}/{stem}_overlay.png
  {output_dir}/{stem}_result.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import numpy as np
from PIL import Image


def save_gradcam_result(
    result: Dict,
    output_dir: str | Path,
    stem: str = "gradcam",
) -> Dict[str, str]:
    """
    Save Grad-CAM outputs from GradCAMGenerator.generate().

    Parameters
    ----------
    result     : dict returned by GradCAMGenerator.generate()
    output_dir : directory to write files into
    stem       : filename stem (e.g. image name without extension)

    Returns
    -------
    dict mapping keys to saved file paths
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    saved = {}

    # Original image
    orig = result["original_rgb"]
    orig_path = out / f"{stem}_original.png"
    Image.fromarray(orig.astype(np.uint8)).save(orig_path)
    saved["original"] = str(orig_path)

    # Heatmap (grayscale, normalised to uint8)
    heatmap = (result["heatmap"] * 255).astype(np.uint8)
    hm_path = out / f"{stem}_heatmap.png"
    Image.fromarray(heatmap).save(hm_path)
    saved["heatmap"] = str(hm_path)

    # Overlay
    overlay_path = out / f"{stem}_overlay.png"
    Image.fromarray(result["overlay"].astype(np.uint8)).save(overlay_path)
    saved["overlay"] = str(overlay_path)

    # JSON metadata
    meta = {
        "predicted_class": result["predicted_class"],
        "predicted_class_id": result["predicted_class_id"],
        "confidence": result["confidence"],
        "class_probabilities": result["class_probabilities"],
        "files": saved,
    }
    json_path = out / f"{stem}_result.json"
    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)
    saved["result_json"] = str(json_path)

    return saved
