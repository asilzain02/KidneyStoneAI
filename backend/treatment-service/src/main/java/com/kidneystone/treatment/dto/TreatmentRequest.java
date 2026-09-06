package com.kidneystone.treatment.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class TreatmentRequest {
    @NotNull(message = "Predicted class is required")
    private String predictedClass;
    
    @NotNull(message = "Severity level is required")
    private String severityLevel;
}
