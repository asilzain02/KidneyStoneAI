package com.kidneystone.severity.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class SeverityRequest {
    @NotNull(message = "Predicted class is required")
    private String predictedClass;
    private Double confidence;

    private Boolean stoneDetected;
    private Integer stoneAreaPixels;
    private Double coverageRatio;
}
