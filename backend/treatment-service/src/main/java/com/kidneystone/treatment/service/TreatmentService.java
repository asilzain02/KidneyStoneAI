package com.kidneystone.treatment.service;

import com.kidneystone.treatment.dto.TreatmentRequest;
import com.kidneystone.treatment.dto.TreatmentResponse;
import org.springframework.stereotype.Service;

@Service
public class TreatmentService {

    private static final String DISCLAIMER = "AI-generated clinical decision support. Results require confirmation by a qualified healthcare professional.";

    public TreatmentResponse recommend(TreatmentRequest request) {
        String severity = request.getSeverityLevel();
        if (severity == null) {
            severity = "UNKNOWN";
        }
        severity = severity.trim().toUpperCase();

        if ("HIGH".equals(severity)) {
            return new TreatmentResponse(
                    "URGENT_EVALUATION",
                    "Immediate urological consultation recommended due to high severity finding. Consider surgical intervention assessment.",
                    DISCLAIMER
            );
        }

        if ("MODERATE".equals(severity)) {
            return new TreatmentResponse(
                    "CLINICAL_EVALUATION",
                    "Routine clinical evaluation recommended. Monitor patient symptoms and consider outpatient urology referral.",
                    DISCLAIMER
            );
        }

        if ("LOW".equals(severity)) {
            return new TreatmentResponse(
                    "CONSERVATIVE_MANAGEMENT",
                    "Conservative management may be considered based on clinical assessment. Encourage hydration and monitor.",
                    DISCLAIMER
            );
        }

        return new TreatmentResponse(
                "UNKNOWN",
                "Insufficient severity data to provide a recommendation. Further clinical evaluation required.",
                DISCLAIMER
        );
    }
}
