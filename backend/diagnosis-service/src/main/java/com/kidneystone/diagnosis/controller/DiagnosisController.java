package com.kidneystone.diagnosis.controller;

import com.kidneystone.diagnosis.dto.DiagnosisResponse;
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
import org.springframework.web.multipart.MultipartFile;

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
    @PostMapping(
            value = "/{imageId}",
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE
    )
    @Operation(summary = "Run AI diagnosis on a CT image")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<?> runDiagnosis(
            @PathVariable UUID imageId,
            @RequestParam("file") MultipartFile file,
            @RequestParam("patientId") UUID patientId,
            Principal principal
    ) {
        UUID requestedBy = UUID.fromString(principal.getName());

        log.info("Diagnosis request: imageId={}, patientId={}, requestedBy={}, file={}",
                imageId, patientId, requestedBy, file.getOriginalFilename());

        // ── Validate upload ────────────────────────────────────────────────
        if (file.isEmpty()) {
            return ResponseEntity
                    .badRequest()
                    .body(errorBody("File is empty."));
        }

        byte[] imageBytes;
        try {
            imageBytes = file.getBytes();
        } catch (IOException e) {
            log.error("Failed to read uploaded file: {}", e.getMessage());
            return ResponseEntity
                    .badRequest()
                    .body(errorBody("Failed to read uploaded file: " + e.getMessage()));
        }

        // ── Run diagnosis ──────────────────────────────────────────────────
        try {
            DiagnosisResponse response = diagnosisService.runDiagnosis(
                    imageId,
                    patientId,
                    requestedBy,
                    imageBytes,
                    file.getOriginalFilename(),
                    file.getContentType()
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
