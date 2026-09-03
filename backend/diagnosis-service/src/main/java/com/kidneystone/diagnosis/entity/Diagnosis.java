package com.kidneystone.diagnosis.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Purpose:
 *   JPA entity that persists the result of one AI diagnosis request.
 *   One Diagnosis record corresponds to one AI Engine inference call
 *   for a specific medical image owned by a patient.
 *
 *   Stores both individual structured columns (for querying/reporting)
 *   and the full AI JSON result blob (for audit and future schema evolution).
 */
@Entity
@Table(name = "diagnoses", indexes = {
    @Index(name = "idx_diagnosis_image_id",   columnList = "image_id"),
    @Index(name = "idx_diagnosis_patient_id",  columnList = "patient_id"),
    @Index(name = "idx_diagnosis_created_at",  columnList = "created_at")
})
@Getter
@Setter
public class Diagnosis {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    // ── Ownership ──────────────────────────────────────────────────────────

    /** The medical image that was analysed. */
    @Column(name = "image_id", nullable = false)
    private UUID imageId;

    /** The patient the image belongs to (denormalised for fast queries). */
    @Column(name = "patient_id", nullable = false)
    private UUID patientId;

    /** The authenticated user (doctor/admin) who triggered the diagnosis. */
    @Column(name = "requested_by", nullable = false)
    private UUID requestedBy;

    // ── AI Inference tracking ──────────────────────────────────────────────

    /** Unique ID returned by the AI Engine for this inference run. */
    @Column(name = "inference_id", length = 36)
    private String inferenceId;

    // ── Classification result ──────────────────────────────────────────────

    /** Predicted class: Normal, Cyst, Stone, Tumor */
    @Column(name = "predicted_class", length = 20)
    private String predictedClass;

    /** Softmax confidence (0.0 - 1.0) of the predicted class. */
    @Column(name = "confidence")
    private Double confidence;

    // ── Segmentation result ────────────────────────────────────────────────

    /** Whether the segmentation model detected a stone-like region. */
    @Column(name = "stone_detected")
    private Boolean stoneDetected;

    /** Number of pixels classified as stone by the segmentation model. */
    @Column(name = "stone_area_pixels")
    private Integer stoneAreaPixels;

    /** Fraction of image occupied by stone region (0.0 - 1.0). */
    @Column(name = "coverage_ratio")
    private Double coverageRatio;

    // ── Explainability ─────────────────────────────────────────────────────

    /** XAI method used (always "Grad-CAM" in this version). */
    @Column(name = "xai_method", length = 30)
    private String xaiMethod;

    /**
     * Path (relative to AI Engine output root) where the Grad-CAM
     * heatmap PNG is stored.  Serves as a reference for later retrieval
     * — Spring should not embed absolute local OS paths here.
     */
    @Column(name = "heatmap_path", length = 512)
    private String heatmapPath;

    /**
     * Path (relative to AI Engine output root) where the Grad-CAM
     * overlay PNG is stored.
     */
    @Column(name = "overlay_path", length = 512)
    private String overlayPath;

    // ── Consistency ────────────────────────────────────────────────────────

    /** Cross-validation status: CONSISTENT | PARTIAL_DISAGREEMENT | DISAGREEMENT */
    @Column(name = "consistency_status", length = 30)
    private String consistencyStatus;

    @Column(name = "consistency_message", length = 512)
    private String consistencyMessage;

    // ── Model metadata ─────────────────────────────────────────────────────

    @Column(name = "classification_model", length = 100)
    private String classificationModel;

    @Column(name = "segmentation_model", length = 100)
    private String segmentationModel;

    /** Processing time in milliseconds reported by the AI Engine. */
    @Column(name = "processing_time_ms")
    private Integer processingTimeMs;

    @Column(name = "device", length = 10)
    private String device;

    // ── Full result audit blob ─────────────────────────────────────────────

    /**
     * Purpose:
     *   The complete JSON response from the AI Engine, stored verbatim.
     *   This ensures we never lose information even if the entity columns
     *   do not capture every field (forward compatibility).
     */
    @Column(name = "full_result_json", columnDefinition = "TEXT")
    private String fullResultJson;

    // ── Lifecycle ──────────────────────────────────────────────────────────

    @Column(name = "status", length = 20, nullable = false)
    private String status = "COMPLETED";

    @Column(name = "error_message", length = 1024)
    private String errorMessage;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
