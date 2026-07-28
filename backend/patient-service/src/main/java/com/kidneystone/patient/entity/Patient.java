package com.kidneystone.patient.entity;

import com.kidneystone.shared.BaseEntity;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "patients", schema = "patient")
@Getter
@Setter
@NoArgsConstructor
public class Patient extends BaseEntity {

    @Column(name = "patient_code", nullable = false, unique = true, length = 20)
    private String patientCode;

    @Column(name = "first_name", nullable = false, length = 100)
    private String firstName;

    @Column(name = "last_name", nullable = false, length = 100)
    private String lastName;

    @Column(name = "date_of_birth", nullable = false)
    private LocalDate dateOfBirth;

    @Column(name = "gender", nullable = false, length = 10)
    private String gender;

    @Column(name = "blood_group", length = 5)
    private String bloodGroup;

    @Column(name = "phone", length = 20)
    private String phone;

    @Column(name = "email", length = 255)
    private String email;

    @Column(name = "address", columnDefinition = "TEXT")
    private String address;

    @Column(name = "registered_by", nullable = false)
    private UUID registeredBy;

    @Column(name = "status", nullable = false, length = 20)
    private String status = "ACTIVE";

    @OneToMany(mappedBy = "patient", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<EmergencyContact> emergencyContacts = new ArrayList<>();
}
