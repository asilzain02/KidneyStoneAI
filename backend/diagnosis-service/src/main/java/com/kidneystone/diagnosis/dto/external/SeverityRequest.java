package com.kidneystone.diagnosis.dto.external;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class SeverityRequest {
    private String predictedClass;
    private Double confidence;
    private Boolean stoneDetected;
    private Integer stoneAreaPixels;
    private Double coverageRatio;
}
