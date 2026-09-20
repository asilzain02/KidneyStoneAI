package com.kidneystone.report.service;

import com.kidneystone.report.dto.ReportRequest;
import com.kidneystone.report.dto.ReportResponse;
import com.kidneystone.report.client.DiagnosisServiceClient;
import org.springframework.stereotype.Service;
import lombok.RequiredArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ReportService {

    private final DiagnosisServiceClient diagnosisServiceClient;

    public List<Map<String, Object>> getReportMetadata(String authHeader) {
        List<Map<String, Object>> completedDiagnoses = diagnosisServiceClient.getCompletedDiagnoses(authHeader);
        return completedDiagnoses.stream()
                .map(d -> {
                        Map<String, Object> map = new java.util.HashMap<>();
                        map.put("id", d.get("id"));
                        map.put("patientId", d.get("patientId"));
                        map.put("diagnosisId", d.get("id"));
                        map.put("format", "PDF");
                        map.put("status", "READY");
                        map.put("generatedAt", d.getOrDefault("createdAt", LocalDateTime.now().toString()));
                        return map;
                })
                .collect(Collectors.toList());
    }

    public ReportResponse generateReport(ReportRequest request) {
        StringBuilder sb = new StringBuilder();
        
        sb.append("------------------------------------------------\n");
        sb.append("KIDNEYSTONEAI CLINICAL AI REPORT\n");
        sb.append("------------------------------------------------\n\n");
        
        sb.append("Patient Information\n");
        sb.append("Patient ID: ").append(request.getPatientId() != null ? request.getPatientId() : "N/A").append("\n\n");
        
        sb.append("Image Information\n");
        sb.append("Image ID: ").append(request.getImageId() != null ? request.getImageId() : "N/A").append("\n\n");
        
        sb.append("AI Diagnosis\n");
        sb.append("Prediction: ").append(request.getPredictedClass() != null ? request.getPredictedClass() : "UNKNOWN").append("\n");
        
        String conf = "N/A";
        if (request.getConfidence() != null) {
            conf = String.format("%.2f%%", request.getConfidence() * 100);
        }
        sb.append("Confidence: ").append(conf).append("\n");
        sb.append("Stone Detected: ").append(Boolean.TRUE.equals(request.getStoneDetected()) ? "Yes" : "No").append("\n\n");
        
        sb.append("Severity Assessment\n");
        sb.append("Severity: ").append(request.getSeverityLevel() != null ? request.getSeverityLevel() : "N/A").append("\n");
        sb.append("Reason: ").append(request.getSeverityReason() != null ? request.getSeverityReason() : "N/A").append("\n\n");
        
        sb.append("Treatment / Clinical Guidance\n");
        sb.append("Recommendation: ").append(request.getTreatmentRecommendation() != null ? request.getTreatmentRecommendation() : "N/A").append("\n\n");
        
        sb.append("Explainability\n");
        if (request.getXaiMethod() != null) {
            sb.append("Method: ").append(request.getXaiMethod()).append("\n");
            sb.append("Visual Data Available. Use Heatmap/Overlay URLs provided in the response metadata.\n\n");
        } else {
            sb.append("No Grad-CAM / explanation information available.\n\n");
        }
        
        sb.append("Clinical Disclaimer\n");
        sb.append("\"AI-generated decision support. Results require confirmation by a qualified healthcare professional.\"\n");
        sb.append("------------------------------------------------\n");
        
        return new ReportResponse(sb.toString());
    }
}
