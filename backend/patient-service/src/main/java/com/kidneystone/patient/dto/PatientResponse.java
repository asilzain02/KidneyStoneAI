package com.kidneystone.patient.dto;

import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Data
public class PatientResponse {

    private UUID id;
    private String patientCode;
    private String firstName;
    private String lastName;
    private LocalDate dateOfBirth;
    private String gender;
    private String bloodGroup;
    private String phone;
    private String email;
    private String address;
    private String status;
    private UUID registeredBy;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
