package com.kidneystone.diagnosis.dto.external;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class TreatmentRequest {
    private String predictedClass;
    private String severityLevel;
}
