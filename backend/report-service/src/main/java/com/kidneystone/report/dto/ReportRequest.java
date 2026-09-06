package com.kidneystone.report.dto;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class ReportRequest {
    private String patientId;
    private String imageId;
    
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
    private LocalDateTime timestamp;
}
