"""
schemas.py — Pydantic response models for KidneyStoneAI AI Engine API v1.

Purpose:
    Defines the stable external API contract between the Python AI Engine
    and the Spring Boot services.  Changing internal ML implementation must
    not break these schemas.

Design decisions:
    - Grad-CAM image bytes are NOT included in JSON.  Instead, relative file
      paths (within the controlled output directory) are returned.  Spring
      fetches them via a dedicated /api/v1/files/ endpoint.
    - All probabilities are plain floats 0..1.
    - device and processingTimeMs aid observability without leaking internals.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


# ── Individual result blocks ──────────────────────────────────────────────────


class ClassificationResult(BaseModel):
    """
    Purpose:
        Carries the 4-class classification output from EfficientNet-B0.
    """
    predictedClass: str = Field(..., description="Predicted class name (Normal/Cyst/Stone/Tumor)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Softmax probability of predicted class")
    probabilities: Dict[str, float] = Field(
        ..., description="Softmax probabilities for all 4 classes"
    )


class BoundingBox(BaseModel):
    """
    Purpose:
        Pixel-space bounding box of detected stone region.
        Physical mm measurements intentionally omitted — DICOM pixel spacing
        is not available and fabricating medical measurements is prohibited.
    """
    x: int
    y: int
    width: int
    height: int


class SegmentationResult(BaseModel):
    """
    Purpose:
        Carries U-Net EXP02_LOSS_TVERSKY segmentation output.
        'detected' is False when no pixels exceed the threshold —
        Stone may still be present if classification predicts Stone.
    """
    detected: bool
    stoneAreaPixels: int
    totalPixels: int
    coverageRatio: float = Field(..., ge=0.0, le=1.0)
    numComponents: Optional[int] = None
    boundingBox: Optional[BoundingBox] = None
    maskPath: Optional[str] = None
    overlayPath: Optional[str] = None


class ExplainabilityResult(BaseModel):
    """
    Purpose:
        Grad-CAM model-attention visualization metadata.
        heatmapPath and overlayPath are paths relative to the AI Engine
        output root — Spring fetches these via /api/v1/files/{inferenceId}/*.
    """
    method: str = Field(default="Grad-CAM")
    description: str = Field(
        default=(
            "Model-influential region visualization computed via Grad-CAM. "
            "This shows which image regions most influenced the classification decision. "
            "This is NOT a diagnostic proof and must not be interpreted as a definitive "
            "localization of pathology."
        )
    )
    targetClass: str
    targetLayer: str
    heatmapPath: Optional[str] = None
    overlayPath: Optional[str] = None


class ConsistencyResult(BaseModel):
    """
    Purpose:
        Cross-validates classification and segmentation agreement so
        downstream services understand when the two models disagree.
    """
    status: str  # CONSISTENT | PARTIAL_DISAGREEMENT | DISAGREEMENT
    message: str


class ModelInfo(BaseModel):
    """
    Purpose:
        Model version metadata for audit/observability.
        Lets Spring log which model version produced a given diagnosis.
    """
    classificationCheckpoint: str
    segmentationCheckpoint: str
    segmentationExperiment: str = "EXP02_LOSS_TVERSKY"


class InferenceMetadata(BaseModel):
    """
    Purpose:
        Request-level observability fields.
    """
    device: str
    processingTimeMs: int
    timestamp: str


# ── Top-level response ────────────────────────────────────────────────────────


class AIAnalysisResponse(BaseModel):
    """
    Purpose:
        The complete, versioned response returned by POST /api/v1/ai/analyze.
        This is the stable contract between Python AI Engine and Spring Boot.

    Spring Boot must depend only on this contract, not on internal Python
    implementation details.
    """
    inferenceId: str = Field(..., description="Unique UUID for this inference request")
    classification: ClassificationResult
    segmentation: SegmentationResult
    explainability: ExplainabilityResult
    consistency: ConsistencyResult
    models: ModelInfo
    metadata: InferenceMetadata


# ── Error response ────────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """
    Purpose:
        Structured error response — never expose raw stack traces externally.
    """
    inferenceId: Optional[str] = None
    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
