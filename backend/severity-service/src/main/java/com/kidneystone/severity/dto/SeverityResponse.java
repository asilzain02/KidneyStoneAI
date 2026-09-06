package com.kidneystone.severity.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class SeverityResponse {
    private String severityLevel;
    private String severityReason;
}
