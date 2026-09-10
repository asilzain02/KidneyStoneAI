package com.kidneystone.diagnosis.controller;

import com.kidneystone.diagnosis.dto.DiagnosisResponse;
import com.kidneystone.diagnosis.dto.external.ReportResponse;
import com.kidneystone.diagnosis.dto.external.SeverityResponse;
import com.kidneystone.diagnosis.dto.external.TreatmentResponse;
import com.kidneystone.diagnosis.exception.AiEngineException;
import com.kidneystone.diagnosis.service.DiagnosisService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.*;
import jakarta.validation.Valid;

import java.io.IOException;
import java.security.Principal;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Purpose:
 *   REST controller for the AI Diagnosis API.
 *
 *   Responsibilities:
 *     - Authenticate the caller via JWT (handled by Spring Security filter).
 *     - Accept a CT image file and trigger AI analysis.
 *     - Delegate all business logic to DiagnosisService.
 *     - Return structured HTTP responses (never raw exceptions).
 *
 *   Endpoints:
 *     POST /api/v1/diagnoses/{imageId}                 — trigger AI diagnosis
 *     GET  /api/v1/diagnoses/{id}                      — get one diagnosis
 *     GET  /api/v1/diagnoses/image/{imageId}           — all diagnoses for an image
 *     GET  /api/v1/diagnoses/patient/{patientId}       — paginated patient history
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/diagnoses")
@RequiredArgsConstructor
@Tag(name = "Diagnosis", description = "AI-powered CT kidney diagnosis APIs")
@SecurityRequirement(name = "bearerAuth")
public class DiagnosisController {

    private final DiagnosisService diagnosisService;

    // ── Trigger diagnosis ─────────────────────────────────────────────────────

    /**
     * POST /api/v1/diagnoses/{imageId}
     *
     * Purpose:
     *   Accept a CT image upload and trigger the full AI pipeline:
     *   EfficientNet-B0 classification + U-Net segmentation + Grad-CAM XAI.
     *   Persists the result and returns the structured DiagnosisResponse.
     *
     * Authorization: ROLE_ADMIN or ROLE_DOCTOR only.
     *
     * @param imageId    UUID of the image record in image-service
     * @param file       the actual CT image bytes (multipart/form-data)
     * @param patientId  UUID of the patient (query param — supplied by gateway/caller)
     * @param principal  JWT principal — provides the requesting user's UUID
     */
    /**
     * POST /api/v1/diagnoses
     *
     * Purpose:
     *   Trigger the full AI pipeline on an already uploaded image.
     *   Fetches the image automatically from Image Service.
     *
     * Authorization: ROLE_ADMIN or ROLE_DOCTOR only.
     *
     * @param request    JSON DTO containing patientId and imageId
     * @param authHeader Bearer token passed intact to Image Service
     * @param principal  JWT principal — provides the requesting user's UUID
     */
    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "Run AI diagnosis on an existing CT image")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<?> runDiagnosis(
            @Valid @RequestBody com.kidneystone.diagnosis.dto.DiagnosisRequest request,
            @RequestHeader(org.springframework.http.HttpHeaders.AUTHORIZATION) String authHeader,
            Principal principal
    ) {
        UUID requestedBy = UUID.fromString(principal.getName());
        UUID imageId = request.getImageId();
        UUID patientId = request.getPatientId();

        log.info("Diagnosis request: imageId={}, patientId={}, requestedBy={}",
                imageId, patientId, requestedBy);

        try {
            DiagnosisResponse response = diagnosisService.runDiagnosis(
                    imageId,
                    patientId,
                    requestedBy,
                    authHeader
            );
            return ResponseEntity.status(HttpStatus.CREATED).body(response);

        } catch (AiEngineException e) {
            log.error("AI Engine unavailable: imageId={}, error={}", imageId, e.getMessage());
            return ResponseEntity
                    .status(HttpStatus.BAD_GATEWAY)
                    .body(errorBody("AI Engine error: " + e.getMessage()));

        } catch (Exception e) {
            log.error("Unexpected error during diagnosis: imageId={}, error={}",
                    imageId, e.getMessage(), e);
            return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(errorBody("Internal error during diagnosis. Check logs."));
        }
    }

    // ── Read endpoints ────────────────────────────────────────────────────────

    /**
     * GET /api/v1/diagnoses/{id}
     * Purpose: Retrieve a single diagnosis by its UUID.
     */
    @GetMapping("/{id}")
    @Operation(summary = "Get a diagnosis by ID")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<?> getDiagnosis(@PathVariable UUID id) {
        try {
            DiagnosisResponse response = diagnosisService.getDiagnosisById(id);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * GET /api/v1/diagnoses/image/{imageId}
     * Purpose: List all diagnoses for a specific image (most recent first).
     */
    @GetMapping("/image/{imageId}")
    @Operation(summary = "List all diagnoses for an image")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<List<DiagnosisResponse>> getDiagnosesByImage(
            @PathVariable UUID imageId
    ) {
        return ResponseEntity.ok(diagnosisService.getDiagnosesByImage(imageId));
    }

    /**
     * GET /api/v1/diagnoses/patient/{patientId}
     * Purpose: Paginated diagnosis history for a patient.
     */
    @GetMapping("/patient/{patientId}")
    @Operation(summary = "List paginated diagnoses for a patient")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<Page<DiagnosisResponse>> getDiagnosesByPatient(
            @PathVariable UUID patientId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        Pageable pageable = PageRequest.of(page, size);
        return ResponseEntity.ok(diagnosisService.getDiagnosesByPatient(patientId, pageable));
    }

    // ── Helper ────────────────────────────────────────────────────────────────

    @GetMapping("/{id}/severity")
    @Operation(summary = "Get the computed severity assessment for a diagnosis")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<SeverityResponse> getSeverity(@PathVariable UUID id) {
        DiagnosisResponse diagnosis = diagnosisService.getDiagnosisById(id);
        SeverityResponse response = new SeverityResponse();
        response.setSeverityLevel(diagnosis.getSeverityLevel());
        response.setSeverityReason(diagnosis.getSeverityReason());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}/treatment")
    @Operation(summary = "Get the computed treatment recommendation for a diagnosis")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<TreatmentResponse> getTreatment(@PathVariable UUID id) {
        DiagnosisResponse diagnosis = diagnosisService.getDiagnosisById(id);
        TreatmentResponse response = new TreatmentResponse();
        response.setTreatmentCategory(diagnosis.getTreatmentCategory());
        response.setTreatmentRecommendation(diagnosis.getTreatmentRecommendation());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}/report")
    @Operation(summary = "Generate a structured clinical report for a diagnosis")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<ReportResponse> getReport(
            @PathVariable UUID id,
            @RequestHeader(value = org.springframework.http.HttpHeaders.AUTHORIZATION, required = false) String authHeader) {
        return ResponseEntity.ok(diagnosisService.generateReport(id, authHeader));
    }

    /**
     * GET /api/v1/diagnoses/{id}/comparison
     * Purpose: Retrieve the generated deterministic clinical comparison PNG.
     */
    @GetMapping(value = "/{id}/comparison", produces = MediaType.IMAGE_PNG_VALUE)
    @Operation(summary = "Get the generated clinical comparison visual (PNG)")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<?> getComparisonImage(
            @PathVariable UUID id,
            @RequestHeader(value = org.springframework.http.HttpHeaders.AUTHORIZATION, required = false) String authHeader) {
        try {
            byte[] imageBytes = diagnosisService.getComparisonImage(id, authHeader);
            return ResponseEntity
                    .ok()
                    .contentType(MediaType.IMAGE_PNG)
                    .body(imageBytes);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            log.error("Failed to fetch comparison image for diagnosis {}: {}", id, e.getMessage());
            return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(errorBody("Comparison image generation failed."));
        }
    }

    /**
     * Purpose:
     *   Build a simple error body map so callers get a JSON object instead
     *   of an empty response on error.
     *   Never exposes internal stack traces.
     */
    private Map<String, String> errorBody(String message) {
        return Map.of("error", message);
    }
}
