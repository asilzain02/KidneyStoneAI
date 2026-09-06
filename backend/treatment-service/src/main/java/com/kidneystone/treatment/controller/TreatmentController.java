package com.kidneystone.treatment.controller;

import com.kidneystone.treatment.dto.TreatmentRequest;
import com.kidneystone.treatment.dto.TreatmentResponse;
import com.kidneystone.treatment.service.TreatmentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/api/v1/treatment")
@RequiredArgsConstructor
@Tag(name = "Treatment", description = "AI-Assisted Treatment Recommendation APIs")
@SecurityRequirement(name = "bearerAuth")
public class TreatmentController {

    private final TreatmentService treatmentService;

    @PostMapping("/recommend")
    @Operation(summary = "Generate treatment guidance based on severity")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<TreatmentResponse> recommendTreatment(@Valid @RequestBody TreatmentRequest request) {
        log.info("Generating treatment recommendation for severity: {}", request.getSeverityLevel());
        TreatmentResponse response = treatmentService.recommend(request);
        return ResponseEntity.ok(response);
    }
}
