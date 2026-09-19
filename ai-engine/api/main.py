"""
main.py — FastAPI application entry point for KidneyStoneAI AI Engine.

Purpose:
    Wires together all route groups and configures the FastAPI application.

Endpoints available:
    Versioned (production / Spring integration):
        POST /api/v1/ai/analyze         — full pipeline (class + seg + XAI)
        GET  /api/v1/ai/files/{id}/{f}  — serve Grad-CAM output files

    Legacy (backward compatible — keep for CLI / dev testing):
        GET  /health                    — model status + device info
        POST /predict/classify          — classification only
        POST /predict/segment           — segmentation only
        POST /predict/full              — classification + segmentation + Grad-CAM

Run locally:
    cd ai-engine
    uvicorn api.main:app --reload --port 8000

Run in KindeyStoneAI (ROOT)
    .\.venv-ai\Scripts\Activate.ps1
    python -m uvicorn api.main:app --app-dir .\ai-engine --host 0.0.0.0 --port 8000

Environment variables:
    KIDNEY_AI_CLF_CHECKPOINT   — path to classification .pth checkpoint
    KIDNEY_AI_SEG_CHECKPOINT   — path to segmentation .pth checkpoint
    KIDNEY_AI_GRADCAM_DIR      — output directory for Grad-CAM images
    AI_ENGINE_SECRET           — optional shared secret for /api/v1/* endpoints
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import numpy as np
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

_ENGINE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

from config.settings import get_training_cfg, get_paths_cfg
from utils.logger import get_logger

# Purpose:
# Import the versioned v1 router so all /api/v1/ai/* endpoints are registered.
from api.v1.analyze import router as v1_router

log = get_logger("api")

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="KidneyStoneAI Inference API",
    description=(
        "CT kidney classification (EfficientNet-B0), stone segmentation (U-Net EXP02), "
        "and Grad-CAM explainability. "
        "Use POST /api/v1/ai/analyze for Spring Boot integration."
    ),
    version="0.4.0",
)

# Purpose:
# Register the versioned v1 router.  All Spring Boot -> Python calls use these.
app.include_router(v1_router)


# ── Shared lazy pipeline (reused by legacy endpoints below) ──────────────────

_pipeline = None


def _get_pipeline():
    """
    Purpose:
        Return the shared PredictionPipeline singleton.
        Models are loaded once on first call and stay in memory.
    """
    global _pipeline
    if _pipeline is None:
        from prediction.pipeline import PredictionPipeline

        cfg = get_training_cfg()
        paths = get_paths_cfg()

        clf_ckpt = os.environ.get(
            "KIDNEY_AI_CLF_CHECKPOINT",
            paths["weights"]["classification_best"],
        )
        seg_ckpt = os.environ.get(
            "KIDNEY_AI_SEG_CHECKPOINT",
            paths["weights"]["segmentation_best"],
        )
        gradcam_dir = os.environ.get(
            "KIDNEY_AI_GRADCAM_DIR",
            paths["outputs"]["gradcam"],
        )

        if not Path(clf_ckpt).exists():
            raise RuntimeError(
                f"Classification checkpoint not found: {clf_ckpt}. "
                "Train the model first: python training/train_classifier.py"
            )

        _pipeline = PredictionPipeline(
            clf_checkpoint=clf_ckpt,
            cfg=cfg,
            seg_checkpoint=seg_ckpt if Path(seg_ckpt).exists() else None,
            gradcam_output_dir=gradcam_dir,
        )
        log.info("Pipeline initialised")
    return _pipeline


def _read_image(file: UploadFile) -> Image.Image:
    """Read and decode an uploaded image file."""
    try:
        contents = file.file.read()
        return Image.open(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read image: {e}")


# ── Legacy routes (backward compatible) ──────────────────────────────────────

@app.get("/health")
def health():
    """Health check — returns model readiness and device info."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    clf_ready = Path(
        get_paths_cfg()["weights"]["classification_best"]
    ).exists()
    seg_ready = Path(
        get_paths_cfg()["weights"]["segmentation_best"]
    ).exists()
    return {
        "status": "ok",
        "device": device,
        "classification_model_ready": clf_ready,
        "segmentation_model_ready": seg_ready,
        "version": "0.4.0",
        "v1_endpoint": "/api/v1/ai/analyze",
    }


@app.post("/predict/classify")
async def predict_classify(file: UploadFile = File(...)):
    """Classify a CT image -> Normal / Cyst / Stone / Tumor."""
    try:
        image = _read_image(file)
        pipeline = _get_pipeline()
        result = pipeline.classify(image)
        return JSONResponse(content=result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/predict/segment")
async def predict_segment(file: UploadFile = File(...)):
    """Run stone segmentation on a CT image. Returns mask statistics."""
    try:
        image = _read_image(file)
        pipeline = _get_pipeline()
        result = pipeline.segment(image)
        # Remove numpy arrays before JSON serialisation
        serialisable = {
            k: v for k, v in result.items()
            if not isinstance(v, np.ndarray)
        }
        return JSONResponse(content=serialisable)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/predict/full")
async def predict_full(file: UploadFile = File(...)):
    """
    Full pipeline: classify -> segment -> Grad-CAM.
    Returns combined structured result.
    """
    try:
        image = _read_image(file)
        pipeline = _get_pipeline()
        stem = Path(file.filename or "upload").stem
        result = pipeline.predict(image, stem=stem)
        serialisable = {
            k: v for k, v in result.items()
            if not isinstance(v, np.ndarray)
        }
        return JSONResponse(content=serialisable)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
