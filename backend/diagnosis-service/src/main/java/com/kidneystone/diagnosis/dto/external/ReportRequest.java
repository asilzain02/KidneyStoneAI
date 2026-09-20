package com.kidneystone.diagnosis.dto.external;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ReportRequest {
    private String patientId;
    private String imageId;
    private String diagnosisId;
    
    // AI Output
    private String predictedClass;
    private Double confidence;
    private Boolean stoneDetected;
    
    // Severity Output
    private String severityLevel;
    private String severityReason;
    
    // Treatment Output
    private String treatmentCategory;
    private String treatmentRecommendation;
    
    // Explainability
    private String xaiMethod;
    private String heatmapUrl;
    private String overlayUrl;
    
    private String status;
    private String timestamp;
}
