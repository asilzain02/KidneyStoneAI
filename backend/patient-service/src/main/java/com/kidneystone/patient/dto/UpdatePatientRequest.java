package com.kidneystone.patient.dto;

import jakarta.validation.constraints.*;
import lombok.Data;

import java.time.LocalDate;

@Data
public class UpdatePatientRequest {

    @Size(max = 100)
    private String firstName;

    @Size(max = 100)
    private String lastName;

    @Past(message = "Date of birth must be in the past")
    private LocalDate dateOfBirth;

    @Pattern(regexp = "MALE|FEMALE|OTHER", message = "Gender must be MALE, FEMALE, or OTHER")
    private String gender;

    @Size(max = 5)
    private String bloodGroup;

    @Size(max = 20)
    private String phone;

    @Email(message = "Invalid email format")
    @Size(max = 255)
    private String email;

    private String address;

    @Pattern(regexp = "ACTIVE|INACTIVE|DECEASED", message = "Status must be ACTIVE, INACTIVE, or DECEASED")
    private String status;
}
