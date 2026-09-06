package com.kidneystone.severity.controller;

import com.kidneystone.severity.dto.SeverityRequest;
import com.kidneystone.severity.dto.SeverityResponse;
import com.kidneystone.severity.service.SeverityService;
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
@RequestMapping("/api/v1/severity")
@RequiredArgsConstructor
@Tag(name = "Severity", description = "AI-Assisted Severity Assessment APIs")
@SecurityRequirement(name = "bearerAuth")
public class SeverityController {

    private final SeverityService severityService;

    @PostMapping("/assess")
    @Operation(summary = "Calculate severity based on AI Engine observations")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<SeverityResponse> assessSeverity(@Valid @RequestBody SeverityRequest request) {
        log.info("Assessing severity for prediction: {}", request.getPredictedClass());
        SeverityResponse response = severityService.assess(request);
        return ResponseEntity.ok(response);
    }
}
