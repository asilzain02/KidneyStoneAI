package com.kidneystone.diagnosis.repository;

import com.kidneystone.diagnosis.entity.Diagnosis;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

/**
 * Purpose:
 *   Spring Data JPA repository for Diagnosis entities.
 *   Provides standard CRUD plus query methods for listing diagnoses
 *   by image or by patient.
 */
@Repository
public interface DiagnosisRepository extends JpaRepository<Diagnosis, UUID> {

    /**
     * Find all diagnoses for a specific medical image.
     * An image may have been analysed multiple times (re-diagnosis).
     */
    List<Diagnosis> findAllByImageIdOrderByCreatedAtDesc(UUID imageId);

    /**
     * Find paginated diagnoses for a patient (all their images).
     */
    Page<Diagnosis> findAllByPatientIdOrderByCreatedAtDesc(UUID patientId, Pageable pageable);

    /**
     * Check whether any diagnosis already exists for an image.
     */
    boolean existsByImageId(UUID imageId);
}
