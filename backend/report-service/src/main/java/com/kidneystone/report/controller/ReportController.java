package com.kidneystone.report.controller;

import com.kidneystone.report.dto.ReportRequest;
import com.kidneystone.report.dto.ReportResponse;
import com.kidneystone.report.service.ReportService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/api/v1/reports")
@RequiredArgsConstructor
@Tag(name = "Report", description = "AI-Assisted Clinical Report APIs")
@SecurityRequirement(name = "bearerAuth")
public class ReportController {

    private final ReportService reportService;

    @PostMapping("/generate")
    @Operation(summary = "Generate a consolidated structured clinical report")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<ReportResponse> generateReport(@RequestBody ReportRequest request) {
        log.info("Generating report for patientId={}, imageId={}", request.getPatientId(), request.getImageId());
        ReportResponse response = reportService.generateReport(request);
        return ResponseEntity.ok(response);
    }
}
