package com.kidneystone.diagnosis.mapper;

import com.kidneystone.diagnosis.dto.AiAnalysisResult;
import com.kidneystone.diagnosis.dto.DiagnosisResponse;
import com.kidneystone.diagnosis.entity.Diagnosis;
import org.springframework.stereotype.Component;

/**
 * Purpose:
 *   Maps between the Diagnosis JPA entity and its DTOs.
 *
 *   Responsibilities:
 *     - AiAnalysisResult (AI Engine JSON response) -> Diagnosis entity columns
 *     - Diagnosis entity -> DiagnosisResponse (outbound API response)
 *
 *   Design: Manual mapper (no MapStruct) to avoid annotation processor
 *   complexity and remain explicit about which fields are mapped.
 */
@Component
public class DiagnosisMapper {

    /**
     * Purpose:
     *   Populate a Diagnosis entity from the AI Engine analysis result.
     *   The entity's ownership fields (imageId, patientId, requestedBy)
     *   must be set by the caller before saving — this method only handles
     *   the AI result fields.
     *
     * @param result  parsed AI Engine response
     * @param entity  pre-created entity with ownership fields already set
     */
    public void applyAiResult(AiAnalysisResult result, Diagnosis entity) {
        if (result == null) return;

        entity.setInferenceId(result.getInferenceId());

        // ── Classification ────────────────────────────────────────────────
        if (result.getClassification() != null) {
            entity.setPredictedClass(result.getClassification().getPredictedClass());
            entity.setConfidence(result.getClassification().getConfidence());
        }

        // ── Segmentation ──────────────────────────────────────────────────
        if (result.getSegmentation() != null) {
            entity.setStoneDetected(result.getSegmentation().getDetected());
            entity.setStoneAreaPixels(result.getSegmentation().getStoneAreaPixels());
            entity.setCoverageRatio(result.getSegmentation().getCoverageRatio());
        }

        // ── Explainability ─────────────────────────────────────────────────
        if (result.getExplainability() != null) {
            entity.setXaiMethod(result.getExplainability().getMethod());
            entity.setHeatmapPath(result.getExplainability().getHeatmapPath());
            entity.setOverlayPath(result.getExplainability().getOverlayPath());
        }

        // ── Consistency ────────────────────────────────────────────────────
        if (result.getConsistency() != null) {
            entity.setConsistencyStatus(result.getConsistency().getStatus());
            entity.setConsistencyMessage(result.getConsistency().getMessage());
        }

        // ── Models ─────────────────────────────────────────────────────────
        if (result.getModels() != null) {
            entity.setClassificationModel(result.getModels().getClassificationCheckpoint());
            entity.setSegmentationModel(result.getModels().getSegmentationCheckpoint());
        }

        // ── Metadata ───────────────────────────────────────────────────────
        if (result.getMetadata() != null) {
            entity.setProcessingTimeMs(result.getMetadata().getProcessingTimeMs());
            entity.setDevice(result.getMetadata().getDevice());
        }
    }

    /**
     * Purpose:
     *   Map a saved Diagnosis entity to the outbound API response DTO,
     *   constructing heatmap/overlay URLs from the AI Engine inference ID
     *   so the frontend does not need to know internal AI Engine paths.
     *
     * @param entity     saved Diagnosis entity
     * @param aiEngineUrl base URL of the AI Engine (e.g. http://ai-engine:8000)
     * @return           DiagnosisResponse ready to return to caller
     */
    public DiagnosisResponse toResponse(Diagnosis entity, String aiEngineUrl) {
        DiagnosisResponse resp = new DiagnosisResponse();

        resp.setId(entity.getId());
        resp.setImageId(entity.getImageId());
        resp.setPatientId(entity.getPatientId());
        resp.setInferenceId(entity.getInferenceId());

        resp.setPredictedClass(entity.getPredictedClass());
        resp.setConfidence(entity.getConfidence());

        resp.setStoneDetected(entity.getStoneDetected());
        resp.setStoneAreaPixels(entity.getStoneAreaPixels());
        resp.setCoverageRatio(entity.getCoverageRatio());

        resp.setXaiMethod(entity.getXaiMethod());
        resp.setConsistencyStatus(entity.getConsistencyStatus());
        resp.setConsistencyMessage(entity.getConsistencyMessage());

        resp.setClassificationModel(entity.getClassificationModel());
        resp.setSegmentationModel(entity.getSegmentationModel());
        resp.setProcessingTimeMs(entity.getProcessingTimeMs());
        resp.setDevice(entity.getDevice());

        resp.setStatus(entity.getStatus());
        resp.setCreatedAt(entity.getCreatedAt());

        // Purpose:
        // Build publicly-accessible URLs for heatmap and overlay images.
        // The AI Engine /api/v1/ai/files/{inferenceId}/{filename} endpoint
        // serves the files; we route through the AI Engine base URL.
        if (entity.getInferenceId() != null && aiEngineUrl != null) {
            String base = aiEngineUrl.stripTrailing() + "/api/v1/ai/files/" + entity.getInferenceId();
            if (entity.getHeatmapPath() != null) {
                String filename = extractFilename(entity.getHeatmapPath());
                resp.setHeatmapUrl(base + "/" + filename);
            }
            if (entity.getOverlayPath() != null) {
                String filename = extractFilename(entity.getOverlayPath());
                resp.setOverlayUrl(base + "/" + filename);
            }
        }

        return resp;
    }

    /** Extract the filename from a path string. */
    private String extractFilename(String path) {
        if (path == null) return null;
        String normalized = path.replace("\\", "/");
        int idx = normalized.lastIndexOf('/');
        return idx >= 0 ? normalized.substring(idx + 1) : normalized;
    }
}
