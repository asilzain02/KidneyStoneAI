package com.kidneystone.treatment.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class TreatmentResponse {
    private String treatmentCategory;
    private String treatmentRecommendation;
    private String disclaimer;
}
