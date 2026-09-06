package com.kidneystone.diagnosis.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.UUID;

/**
 * Purpose:
 *   Data Transfer Object for initiating an AI Diagnosis.
 *   This avoids sending multipart file payloads, relying instead
 *   on the image ID to retrieve already-uploaded data from the Image Service.
 */
@Data
public class DiagnosisRequest {

    @NotNull(message = "Patient ID is required")
    private UUID patientId;

    @NotNull(message = "Image ID is required")
    private UUID imageId;
}
