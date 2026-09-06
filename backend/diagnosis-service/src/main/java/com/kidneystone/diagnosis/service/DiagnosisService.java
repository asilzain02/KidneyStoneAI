package com.kidneystone.diagnosis.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.kidneystone.diagnosis.client.AiEngineClient;
import com.kidneystone.diagnosis.dto.AiAnalysisResult;
import com.kidneystone.diagnosis.dto.DiagnosisResponse;
import com.kidneystone.diagnosis.entity.Diagnosis;
import com.kidneystone.diagnosis.exception.AiEngineException;
import com.kidneystone.diagnosis.mapper.DiagnosisMapper;
import com.kidneystone.diagnosis.repository.DiagnosisRepository;
import com.kidneystone.diagnosis.client.ImageServiceClient;
import com.kidneystone.diagnosis.client.ImageServiceClient.DownloadedImage;
import com.kidneystone.diagnosis.client.SeverityServiceClient;
import com.kidneystone.diagnosis.client.TreatmentServiceClient;
import com.kidneystone.diagnosis.client.ReportServiceClient;
import com.kidneystone.diagnosis.dto.external.SeverityRequest;
import com.kidneystone.diagnosis.dto.external.SeverityResponse;
import com.kidneystone.diagnosis.dto.external.TreatmentRequest;
import com.kidneystone.diagnosis.dto.external.TreatmentResponse;
import com.kidneystone.diagnosis.dto.external.ReportRequest;
import com.kidneystone.diagnosis.dto.external.ReportResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Purpose:
 *   Business logic layer for the diagnosis workflow.
 *
 *   Responsibilities:
 *     1. Receive a CT image (as bytes) from the controller.
 *     2. Call AiEngineClient to run AI inference.
 *     3. Persist the result to the Diagnosis table.
 *     4. Return the mapped DiagnosisResponse to the controller.
 *     5. Provide read operations for fetching past diagnoses.
 *
 *   Boundaries:
 *     - Does NOT perform any ML computation.
 *     - Does NOT access the filesystem directly.
 *     - Does NOT communicate with patient-service (patient context is passed
 *       in from the controller which resolves it via JWT claims).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DiagnosisService {

    private final DiagnosisRepository diagnosisRepository;
    private final AiEngineClient aiEngineClient;
    private final ImageServiceClient imageServiceClient;
    private final SeverityServiceClient severityServiceClient;
    private final TreatmentServiceClient treatmentServiceClient;
    private final ReportServiceClient reportServiceClient;
    private final DiagnosisMapper diagnosisMapper;
    private final ObjectMapper objectMapper;

    /** AI Engine base URL — used to construct heatmap/overlay download URLs. */
    @Value("${ai-engine.base-url:http://localhost:8000}")
    private String aiEngineBaseUrl;

    // ── Trigger diagnosis ─────────────────────────────────────────────────────

    /**
     * Purpose:
     *   Main entry point for running AI diagnosis on a CT image.
     *   Calls the AI Engine, persists the result, and returns the response.
     *
     * @param imageId      UUID of the medical image (from image-service)
     * @param patientId    UUID of the patient who owns the image
     * @param requestedBy  UUID of the authenticated user triggering the diagnosis
     * @param imageBytes   raw bytes of the CT image
     * @param filename     original filename for the AI Engine
     * @param contentType  MIME type (e.g. "image/jpeg")
     * @return             DiagnosisResponse with AI results and XAI links
     */
    @Transactional
    public DiagnosisResponse runDiagnosis(
            UUID imageId,
            UUID patientId,
            UUID requestedBy,
            String authHeader
    ) {
        log.info("Starting AI diagnosis: imageId={}, patientId={}, requestedBy={}",
                imageId, patientId, requestedBy);

        // ── 0. Fetch image from Image Service ──────────────────────────────
        DownloadedImage image;
        try {
            image = imageServiceClient.downloadImage(imageId, authHeader);
        } catch (Exception e) {
            log.error("Failed to retrieve image for diagnosis: {}", e.getMessage());
            throw new AiEngineException("Failed to retrieve image from Image Service. Ensure the image exists.");
        }

        // ── 1. Create pending diagnosis record ─────────────────────────────
        // Purpose:
        // Save a PENDING record before calling the AI Engine so that if the
        // service crashes mid-inference, there is an audit trail showing
        // that a diagnosis was attempted.
        Diagnosis diagnosis = new Diagnosis();
        diagnosis.setImageId(imageId);
        diagnosis.setPatientId(patientId);
        diagnosis.setRequestedBy(requestedBy);
        diagnosis.setStatus("PENDING");
        diagnosis = diagnosisRepository.save(diagnosis);

        log.info("Diagnosis record created: id={}", diagnosis.getId());

        // ── 2. Call AI Engine ──────────────────────────────────────────────
        AiAnalysisResult aiResult;
        try {
            aiResult = aiEngineClient.analyze(image.getBytes(), image.getFilename(), image.getContentType());
        } catch (AiEngineException e) {
            // Purpose:
            // Mark the diagnosis as FAILED — do not silently swallow the error.
            diagnosis.setStatus("FAILED");
            diagnosis.setErrorMessage(truncate(e.getMessage(), 1000));
            diagnosisRepository.save(diagnosis);

            log.error("AI Engine call failed: diagnosisId={}, error={}",
                    diagnosis.getId(), e.getMessage());
            throw e;
        }

        // ── 3. Persist AI result columns ───────────────────────────────────
        diagnosisMapper.applyAiResult(aiResult, diagnosis);

        // ── 4. Assess Severity ─────────────────────────────────────────────
        try {
            SeverityRequest sevReq = SeverityRequest.builder()
                    .predictedClass(diagnosis.getPredictedClass())
                    .confidence(diagnosis.getConfidence())
                    .stoneDetected(diagnosis.getStoneDetected())
                    .stoneAreaPixels(diagnosis.getStoneAreaPixels())
                    .coverageRatio(diagnosis.getCoverageRatio())
                    .build();
            SeverityResponse sevResp = severityServiceClient.assessSeverity(sevReq, authHeader);
            diagnosis.setSeverityLevel(sevResp.getSeverityLevel());
            diagnosis.setSeverityReason(sevResp.getSeverityReason());
        } catch (Exception e) {
            log.warn("Severity assessment failed. Continuing without severity data: {}", e.getMessage());
        }

        // ── 5. Recommend Treatment ─────────────────────────────────────────
        try {
            TreatmentRequest treatReq = TreatmentRequest.builder()
                    .predictedClass(diagnosis.getPredictedClass())
                    .severityLevel(diagnosis.getSeverityLevel())
                    .build();
            TreatmentResponse treatResp = treatmentServiceClient.recommendTreatment(treatReq, authHeader);
            diagnosis.setTreatmentCategory(treatResp.getTreatmentCategory());
            diagnosis.setTreatmentRecommendation(treatResp.getTreatmentRecommendation());
        } catch (Exception e) {
            log.warn("Treatment recommendation failed. Continuing without treatment data: {}", e.getMessage());
        }

        diagnosis.setStatus("COMPLETED");

        // Purpose:
        // Store the full JSON blob for audit and forward-compatibility.
        // If we add new AI Engine fields later, they are captured here
        // even before the entity schema is updated.
        try {
            diagnosis.setFullResultJson(objectMapper.writeValueAsString(aiResult));
        } catch (JsonProcessingException e) {
            log.warn("Could not serialise AI result to JSON blob: {}", e.getMessage());
            // Non-fatal — columns still have the structured data.
        }

        diagnosis = diagnosisRepository.save(diagnosis);

        log.info(
                "Diagnosis completed: id={}, inferenceId={}, class={}, confidence={}, processingMs={}",
                diagnosis.getId(),
                diagnosis.getInferenceId(),
                diagnosis.getPredictedClass(),
                diagnosis.getConfidence(),
                diagnosis.getProcessingTimeMs()
        );

        return diagnosisMapper.toResponse(diagnosis, aiEngineBaseUrl);
    }

    // ── Read operations ───────────────────────────────────────────────────────

    /**
     * Purpose:
     *   Return all diagnosis records for a specific image.
     *   Ordered by most recent first.
     */
    @Transactional(readOnly = true)
    public List<DiagnosisResponse> getDiagnosesByImage(UUID imageId) {
        return diagnosisRepository
                .findAllByImageIdOrderByCreatedAtDesc(imageId)
                .stream()
                .map(d -> diagnosisMapper.toResponse(d, aiEngineBaseUrl))
                .collect(Collectors.toList());
    }

    /**
     * Purpose:
     *   Return paginated diagnosis records for a patient across all their images.
     */
    @Transactional(readOnly = true)
    public Page<DiagnosisResponse> getDiagnosesByPatient(UUID patientId, Pageable pageable) {
        return diagnosisRepository
                .findAllByPatientIdOrderByCreatedAtDesc(patientId, pageable)
                .map(d -> diagnosisMapper.toResponse(d, aiEngineBaseUrl));
    }

    /**
     * Purpose:
     *   Fetch a single diagnosis by its ID.
     *   Throws IllegalArgumentException if not found (controller maps to 404).
     */
    @Transactional(readOnly = true)
    public DiagnosisResponse getDiagnosisById(UUID diagnosisId) {
        Diagnosis diagnosis = diagnosisRepository
                .findById(diagnosisId)
                .orElseThrow(() -> new IllegalArgumentException(
                        "Diagnosis not found: " + diagnosisId
                ));
        return diagnosisMapper.toResponse(diagnosis, aiEngineBaseUrl);
    }

    /**
     * Purpose:
     *   Generate a full clinical report by calling the downstream Report Service.
     */
    @Transactional(readOnly = true)
    public ReportResponse generateReport(UUID diagnosisId, String authHeader) {
        Diagnosis diagnosis = diagnosisRepository
                .findById(diagnosisId)
                .orElseThrow(() -> new IllegalArgumentException("Diagnosis not found: " + diagnosisId));

        ReportRequest req = ReportRequest.builder()
                .patientId(diagnosis.getPatientId() != null ? diagnosis.getPatientId().toString() : null)
                .imageId(diagnosis.getImageId() != null ? diagnosis.getImageId().toString() : null)
                .predictedClass(diagnosis.getPredictedClass())
                .confidence(diagnosis.getConfidence())
                .stoneDetected(diagnosis.getStoneDetected())
                .severityLevel(diagnosis.getSeverityLevel())
                .severityReason(diagnosis.getSeverityReason())
                .treatmentCategory(diagnosis.getTreatmentCategory())
                .treatmentRecommendation(diagnosis.getTreatmentRecommendation())
                .xaiMethod(diagnosis.getXaiMethod())
                .status(diagnosis.getStatus())
                .timestamp(diagnosis.getCreatedAt() != null ? diagnosis.getCreatedAt().toString() : null)
                .build();

        return reportServiceClient.generateReport(req, authHeader);
    }

    // ── Utility ────────────────────────────────────────────────────────────────

    /** Truncate a string to max length to prevent DB column overflows. */
    private String truncate(String value, int maxLength) {
        if (value == null) return null;
        return value.length() <= maxLength ? value : value.substring(0, maxLength);
    }
}
