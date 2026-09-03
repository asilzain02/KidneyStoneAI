"""
analyze.py — Versioned unified AI inference endpoint.

Purpose:
    Exposes POST /api/v1/ai/analyze as the single stable entry point for
    all AI inference.  Spring Boot calls this endpoint — it must never
    need to know whether classification, segmentation or Grad-CAM run
    internally or who runs them.

Design:
    - Delegates ALL ML work to the existing PredictionPipeline.
    - Assigns a unique inferenceId per request for traceability.
    - Maps the pipeline's internal dict to the versioned Pydantic schema.
    - Never leaks internal paths, stack traces or model internals.
    - Grad-CAM images are saved to a controlled output directory;
      their relative paths are returned for Spring to optionally fetch.

Security:
    - 'AI_ENGINE_SECRET' header can optionally guard this endpoint
      so only the Spring backend can call it (set AI_ENGINE_SECRET env var).
"""

from __future__ import annotations

import io
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import torch
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.schemas import (
    AIAnalysisResponse,
    BoundingBox,
    ClassificationResult,
    ConsistencyResult,
    ErrorResponse,
    ExplainabilityResult,
    InferenceMetadata,
    ModelInfo,
    SegmentationResult,
)
from config.settings import get_paths_cfg, get_training_cfg
from utils.logger import get_logger

log = get_logger("api.v1.analyze")

# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Inference v1"],
)

# ── Pipeline singleton ────────────────────────────────────────────────────────

# Purpose:
# Load models once at startup and reuse for all requests.
# Loading 48MB + 94MB on every request would be unacceptable.
_pipeline = None


def _get_pipeline():
    """
    Purpose:
        Lazily initialise PredictionPipeline on first request.
        After first call, the same instance is returned for all subsequent
        requests — models stay loaded in memory (CPU or CUDA).
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline

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
            "Set KIDNEY_AI_CLF_CHECKPOINT or train the model first."
        )

    seg_path = Path(seg_ckpt) if seg_ckpt else None
    _pipeline = PredictionPipeline(
        clf_checkpoint=clf_ckpt,
        cfg=cfg,
        seg_checkpoint=str(seg_path) if (seg_path and seg_path.exists()) else None,
        gradcam_output_dir=gradcam_dir,
    )
    log.info(
        "PredictionPipeline ready",
        clf=clf_ckpt,
        seg=seg_ckpt,
        device=str(_pipeline.device),
    )
    return _pipeline


# ── Optional secret-header guard ─────────────────────────────────────────────

def _check_secret(x_ai_secret: Optional[str] = Header(default=None)):
    """
    Purpose:
        If AI_ENGINE_SECRET env var is set, callers must pass the matching
        value in the X-AI-Secret header.  This prevents arbitrary external
        clients from hitting the AI Engine directly.
        If AI_ENGINE_SECRET is not configured, the check is skipped (dev mode).
    """
    expected = os.environ.get("AI_ENGINE_SECRET", "")
    if expected and x_ai_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid AI Engine secret.")


# ── Image helpers ─────────────────────────────────────────────────────────────

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/tiff", "image/webp"}
_MAX_FILE_SIZE_MB = 50


def _validate_and_read(file: UploadFile) -> Image.Image:
    """
    Purpose:
        Validate uploaded file type and readability before passing to ML pipeline.
        Prevents path traversal, hidden binary files and corrupted uploads.

    Returns:
        PIL Image in verification-ready state.
    """
    # Content-type check (not solely trusted — user-supplied, but useful)
    if file.content_type and file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Accepted: {sorted(_ALLOWED_CONTENT_TYPES)}",
        )

    contents = file.file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(contents) > _MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {_MAX_FILE_SIZE_MB} MB."
        )

    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()  # Raises on corrupted files
        # Re-open after verify (verify() closes the file)
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        return image
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot read image: {exc}"
        )


# ── Result mapping ────────────────────────────────────────────────────────────

def _build_response(
    inference_id: str,
    raw: dict,
    paths: dict,
    processing_ms: int,
    device: str,
) -> AIAnalysisResponse:
    """
    Purpose:
        Maps the internal PredictionPipeline result dict to the versioned
        Pydantic response schema.  This is the ONLY place where internal
        dict keys are mapped to external field names — changing internal
        pipeline internals only requires updating this function.

    Parameters:
        inference_id    : the UUID assigned to this request
        raw             : dict returned by PredictionPipeline.predict()
        paths           : paths config dict (for checkpoint names)
        processing_ms   : wall-clock time in milliseconds
        device          : 'cuda' or 'cpu'
    """
    clf = raw["classification"]

    # ── Classification ────────────────────────────────────────────────────────
    classification = ClassificationResult(
        predictedClass=clf["predicted_class"],
        confidence=clf["confidence"],
        probabilities=clf["class_probabilities"],
    )

    # ── Segmentation ──────────────────────────────────────────────────────────
    seg_raw = raw.get("segmentation", {})
    seg_stats = seg_raw.get("mask_statistics", {})

    bbox_raw = seg_stats.get("bounding_box")
    bbox = None
    if bbox_raw and isinstance(bbox_raw, (list, tuple)) and len(bbox_raw) == 4:
        bbox = BoundingBox(
            x=int(bbox_raw[0]),
            y=int(bbox_raw[1]),
            width=int(bbox_raw[2]),
            height=int(bbox_raw[3]),
        )

    stone_pixels = seg_stats.get("stone_area_pixels", seg_raw.get("stone_area_pixels", 0))
    total_pixels = seg_stats.get("total_pixels", 0)
    coverage = seg_stats.get("coverage_ratio", 0.0)
    detected = stone_pixels > 0

    segmentation = SegmentationResult(
        detected=detected,
        stoneAreaPixels=int(stone_pixels),
        totalPixels=int(total_pixels),
        coverageRatio=float(coverage),
        numComponents=seg_stats.get("num_components"),
        boundingBox=bbox,
    )

    # ── Explainability ────────────────────────────────────────────────────────
    gradcam_raw = raw.get("gradcam", {})
    saved_files = gradcam_raw.get("saved_files", {})

    explainability = ExplainabilityResult(
        targetClass=gradcam_raw.get("predicted_class", clf["predicted_class"]),
        targetLayer="backbone.conv_head",   # EfficientNet-B0 — verified in classifier.py
        heatmapPath=saved_files.get("heatmap"),
        overlayPath=saved_files.get("overlay"),
    )

    # ── Consistency ───────────────────────────────────────────────────────────
    predicted = clf["predicted_class"]
    if predicted == "Stone":
        if detected:
            c_status, c_msg = "CONSISTENT", (
                "Classification predicts kidney stone and segmentation "
                "detected a corresponding region."
            )
        else:
            c_status, c_msg = "PARTIAL_DISAGREEMENT", (
                "Classification predicts kidney stone, but segmentation "
                "did not detect a stone region above the threshold."
            )
    else:
        if detected:
            c_status, c_msg = "DISAGREEMENT", (
                f"Classification predicts {predicted}, but segmentation "
                "detected a region that resembles stone. Review recommended."
            )
        else:
            c_status, c_msg = "CONSISTENT", (
                f"Classification predicts {predicted} and segmentation "
                "did not detect a stone region."
            )

    consistency = ConsistencyResult(status=c_status, message=c_msg)

    # ── Model info ────────────────────────────────────────────────────────────
    clf_ckpt = os.environ.get(
        "KIDNEY_AI_CLF_CHECKPOINT",
        paths["weights"]["classification_best"],
    )
    seg_ckpt = os.environ.get(
        "KIDNEY_AI_SEG_CHECKPOINT",
        paths["weights"]["segmentation_best"],
    )

    model_info = ModelInfo(
        classificationCheckpoint=Path(clf_ckpt).name,
        segmentationCheckpoint=Path(seg_ckpt).name,
    )

    # ── Metadata ─────────────────────────────────────────────────────────────
    metadata = InferenceMetadata(
        device=device,
        processingTimeMs=processing_ms,
        timestamp=datetime.utcnow().isoformat(),
    )

    return AIAnalysisResponse(
        inferenceId=inference_id,
        classification=classification,
        segmentation=segmentation,
        explainability=explainability,
        consistency=consistency,
        models=model_info,
        metadata=metadata,
    )


# ── Main endpoint ─────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=AIAnalysisResponse,
    summary="Full AI analysis: classification + segmentation + Grad-CAM",
    description=(
        "Accepts a CT image and runs the complete KidneyStoneAI pipeline: "
        "EfficientNet-B0 classification → U-Net EXP02 segmentation → "
        "Grad-CAM explainability. Returns a structured result with an "
        "inference ID that can be used to fetch Grad-CAM image files."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid image"},
        401: {"description": "Invalid AI Engine secret"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Internal inference error"},
        503: {"model": ErrorResponse, "description": "Models not loaded"},
    },
)
async def analyze(
    file: UploadFile = File(..., description="CT image (JPEG/PNG/TIFF)"),
    _: None = Depends(_check_secret),
):
    """
    Run the full KidneyStoneAI inference pipeline on a single CT image.

    Returns:
        AIAnalysisResponse with classification, segmentation, explainability,
        consistency check, model metadata, and timing information.
    """
    inference_id = str(uuid.uuid4())

    log.info(
        "Inference request received",
        inference_id=inference_id,
        filename=file.filename,
        content_type=file.content_type,
    )

    t_start = time.perf_counter()

    # ── 1. Validate image ────────────────────────────────────────────────────
    try:
        image = _validate_and_read(file)
    except HTTPException:
        raise
    except Exception as exc:
        log.error("Image validation failed", inference_id=inference_id, error=str(exc))
        raise HTTPException(status_code=400, detail=f"Image validation failed: {exc}")

    # ── 2. Load pipeline (lazy — models stay in memory) ──────────────────────
    try:
        pipeline = _get_pipeline()
    except RuntimeError as exc:
        log.error("Pipeline initialisation failed", error=str(exc))
        raise HTTPException(status_code=503, detail=str(exc))

    paths = get_paths_cfg()
    device_str = str(pipeline.device)

    # ── 3. Run unified inference ─────────────────────────────────────────────
    try:
        raw = pipeline.predict(
            image=image,
            stem=inference_id,          # Grad-CAM files named by inference_id
            run_segmentation=True,
            run_gradcam=True,
        )
    except Exception as exc:
        log.error(
            "Inference failed",
            inference_id=inference_id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"Inference failed (inferenceId={inference_id}). "
                "Check AI Engine logs for details."
            ),
        )

    processing_ms = int((time.perf_counter() - t_start) * 1000)

    # ── 4. Build structured response ─────────────────────────────────────────
    try:
        response = _build_response(
            inference_id=inference_id,
            raw=raw,
            paths=paths,
            processing_ms=processing_ms,
            device=device_str,
        )
    except Exception as exc:
        log.error(
            "Response mapping failed",
            inference_id=inference_id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Response mapping failed: {exc}",
        )

    log.info(
        "Inference complete",
        inference_id=inference_id,
        predicted_class=response.classification.predictedClass,
        confidence=round(response.classification.confidence, 4),
        segmentation_detected=response.segmentation.detected,
        processing_ms=processing_ms,
        device=device_str,
    )

    return response


# ── File serving endpoint ─────────────────────────────────────────────────────

@router.get(
    "/files/{inference_id}/{filename}",
    summary="Retrieve a Grad-CAM output file by inference ID",
    description=(
        "Serves heatmap, overlay, or original PNG files generated during "
        "an analyze request.  The filename is typically "
        "{inferenceId}_heatmap.png or {inferenceId}_overlay.png."
    ),
)
async def get_file(
    inference_id: str,
    filename: str,
    _: None = Depends(_check_secret),
):
    """
    Purpose:
        Allows Spring Boot (or any authorised caller) to fetch Grad-CAM
        output images without direct filesystem access.

    Security:
        - inference_id is validated as UUID format.
        - filename is path-sanitised — directory traversal is blocked.
    """
    # Validate inference_id looks like a UUID
    try:
        uuid.UUID(inference_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid inference ID format.")

    # Sanitise filename — prevent path traversal
    safe_name = Path(filename).name
    if safe_name != filename or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    paths = get_paths_cfg()
    gradcam_dir = os.environ.get(
        "KIDNEY_AI_GRADCAM_DIR",
        paths["outputs"]["gradcam"],
    )

    file_path = Path(gradcam_dir) / safe_name
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {safe_name}"
        )

    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=safe_name,
    )
