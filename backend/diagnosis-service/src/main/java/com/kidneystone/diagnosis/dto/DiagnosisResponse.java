package com.kidneystone.diagnosis.dto;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Purpose:
 *   API response DTO returned to frontend/API gateway for a completed diagnosis.
 *   Contains all information a frontend needs to display the diagnosis result,
 *   including AI predictions, segmentation data, and XAI explanation links.
 *
 *   Deliberately separate from the Diagnosis entity so that internal JPA fields
 *   are never accidentally exposed to external callers.
 */
@Data
public class DiagnosisResponse {

    private UUID id;
    private UUID imageId;
    private UUID patientId;
    private String inferenceId;

    // ── Classification ────────────────────────────────────────────────────────

    /**
     * AI-predicted class.
     * Terminology: "AI prediction" — NOT a confirmed medical diagnosis.
     */
    private String predictedClass;
    private Double confidence;

    // ── Segmentation ──────────────────────────────────────────────────────────

    private Boolean stoneDetected;
    private Integer stoneAreaPixels;
    private Double coverageRatio;

    // ── Explainability ────────────────────────────────────────────────────────

    /**
     * URL where the frontend can fetch the Grad-CAM heatmap image.
     * Points back through the gateway to the AI Engine files endpoint.
     */
    private String heatmapUrl;

    /**
     * URL where the frontend can fetch the Grad-CAM overlay image.
     */
    private String overlayUrl;

    private String xaiMethod;

    // ── Consistency ───────────────────────────────────────────────────────────

    /**
     * Cross-validation result between classification and segmentation.
     * Values: CONSISTENT | PARTIAL_DISAGREEMENT | DISAGREEMENT
     */
    private String consistencyStatus;
    private String consistencyMessage;

    // ── Model info ────────────────────────────────────────────────────────────

    private String classificationModel;
    private String segmentationModel;
    private Integer processingTimeMs;
    private String device;

    // ── Clinical Decision Support ─────────────────────────────────────────────

    private String severityLevel;
    private String severityReason;
    
    private String treatmentCategory;
    private String treatmentRecommendation;

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    private String status;
    private LocalDateTime createdAt;
}
