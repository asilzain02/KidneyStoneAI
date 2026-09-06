package com.kidneystone.diagnosis.dto.external;

import lombok.Data;

@Data
public class TreatmentResponse {
    private String treatmentCategory;
    private String treatmentRecommendation;
    private String disclaimer;
}
