package com.kidneystone.patient.repository;

import com.kidneystone.patient.entity.Patient;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface PatientRepository extends JpaRepository<Patient, UUID> {

    Optional<Patient> findByIdAndIsDeletedFalse(UUID id);

    Optional<Patient> findByPatientCodeAndIsDeletedFalse(String patientCode);

    boolean existsByPatientCodeAndIsDeletedFalse(String patientCode);

    boolean existsByEmailAndIsDeletedFalse(String email);

    Page<Patient> findAllByIsDeletedFalse(Pageable pageable);

    @Query("""
        SELECT p FROM Patient p
        WHERE p.isDeleted = false
        AND (
            LOWER(p.firstName) LIKE LOWER(CONCAT('%', :query, '%')) OR
            LOWER(p.lastName)  LIKE LOWER(CONCAT('%', :query, '%')) OR
            LOWER(p.email)     LIKE LOWER(CONCAT('%', :query, '%')) OR
            LOWER(p.patientCode) LIKE LOWER(CONCAT('%', :query, '%'))
        )
        """)
    Page<Patient> searchPatients(@Param("query") String query, Pageable pageable);
}
