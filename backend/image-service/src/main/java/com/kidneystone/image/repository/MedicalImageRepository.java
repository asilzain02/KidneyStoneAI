package com.kidneystone.image.repository;

import com.kidneystone.image.entity.MedicalImage;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface MedicalImageRepository extends JpaRepository<MedicalImage, UUID> {

    Optional<MedicalImage> findByIdAndIsDeletedFalse(UUID id);

    Page<MedicalImage> findAllByPatientIdAndIsDeletedFalse(UUID patientId, Pageable pageable);

    Page<MedicalImage> findAllByIsDeletedFalse(Pageable pageable);
}
