package com.kidneystone.report.controller;

import com.kidneystone.report.dto.ReportRequest;
import com.kidneystone.report.dto.ReportResponse;
import com.kidneystone.report.service.ReportService;
import com.kidneystone.report.service.PdfGeneratorService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
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
    private final PdfGeneratorService pdfGeneratorService;

    @GetMapping
    @Operation(summary = "Get list of available reports based on completed diagnoses")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<?> getReports(
            @RequestHeader(value = org.springframework.http.HttpHeaders.AUTHORIZATION, required = false) String authHeader) {
        return ResponseEntity.ok(reportService.getReportMetadata(authHeader));
    }

    @PostMapping("/generate")
    @Operation(summary = "Generate a consolidated structured clinical report")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<ReportResponse> generateReport(@RequestBody ReportRequest request) {
        log.info("Generating report for patientId={}, imageId={}", request.getPatientId(), request.getImageId());
        ReportResponse response = reportService.generateReport(request);
        return ResponseEntity.ok(response);
    }

    @GetMapping(value = "/{diagnosisId}/pdf", produces = MediaType.APPLICATION_PDF_VALUE)
    @Operation(summary = "Generate and download a PDF format clinical report")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<byte[]> getPdfReport(
            @PathVariable String diagnosisId,
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String authHeader) {
        
        log.info("Generating PDF report for diagnosisId={}", diagnosisId);
        
        // Temporarily, we can either re-fetch diagnosis data from DiagnosisServiceClient
        // or just have ReportService do it. 
        ReportRequest request = reportService.generateReportRequest(diagnosisId, authHeader);
        
        byte[] pdfBytes = pdfGeneratorService.generatePdfReport(request, authHeader);

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"KidneyStoneAI_Report_" + diagnosisId + ".pdf\"")
                .body(pdfBytes);
    }
}
