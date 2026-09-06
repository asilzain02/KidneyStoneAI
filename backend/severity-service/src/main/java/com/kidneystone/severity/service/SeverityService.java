package com.kidneystone.severity.service;

import com.kidneystone.severity.dto.SeverityRequest;
import com.kidneystone.severity.dto.SeverityResponse;
import org.springframework.stereotype.Service;

@Service
public class SeverityService {

    public SeverityResponse assess(SeverityRequest request) {
        String pClass = request.getPredictedClass();
        Boolean detected = request.getStoneDetected();
        Double coverage = request.getCoverageRatio();

        if (pClass == null) {
            return new SeverityResponse("LOW", "Insufficient clinical data to determine severity.");
        }

        pClass = pClass.trim().toUpperCase();

        if (pClass.equals("NORMAL")) {
            return new SeverityResponse("LOW", "No obvious abnormalities detected.");
        }

        if (pClass.equals("TUMOR")) {
            return new SeverityResponse("HIGH", "Suspected tumor mass detected. Requires urgent attention.");
        }

        if (pClass.equals("CYST")) {
            return new SeverityResponse("MODERATE", "Cyst detected. Usually benign but requires clinical correlation.");
        }

        if (pClass.equals("STONE")) {
            if (detected != null && detected && coverage != null) {
                if (coverage > 0.05) {
                    return new SeverityResponse("HIGH", "Large stone burden detected (" + 
                            String.format("%.1f", coverage * 100) + "% coverage). High risk of obstruction.");
                } else if (coverage > 0.01) {
                    return new SeverityResponse("MODERATE", "Moderate stone burden detected.");
                } else {
                    return new SeverityResponse("LOW", "Small stone detected. Likely asymptomatic.");
                }
            } else {
                return new SeverityResponse("MODERATE", "Stone predicted but spatial bounds are unclear.");
            }
        }

        return new SeverityResponse("LOW", "Unknown classification. Defaulting to baseline severity.");
    }
}
