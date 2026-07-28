package com.kidneystone.patient.service;

import com.kidneystone.patient.dto.CreatePatientRequest;
import com.kidneystone.patient.dto.PatientResponse;
import com.kidneystone.patient.dto.UpdatePatientRequest;
import com.kidneystone.patient.entity.Patient;
import com.kidneystone.patient.mapper.PatientMapper;
import com.kidneystone.patient.repository.PatientRepository;
import com.kidneystone.shared.exception.NotFoundException;
import com.kidneystone.shared.exception.ValidationException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class PatientService {

    private final PatientRepository patientRepository;
    private final PatientMapper patientMapper;
    private final PatientCodeGenerator codeGenerator;

    @Transactional
    public PatientResponse createPatient(CreatePatientRequest request, UUID registeredBy) {
        if (StringUtils.hasText(request.getEmail())
                && patientRepository.existsByEmailAndIsDeletedFalse(request.getEmail())) {
            throw new ValidationException("A patient with this email already exists");
        }

        Patient patient = patientMapper.toEntity(request);
        patient.setPatientCode(codeGenerator.generate());
        patient.setRegisteredBy(registeredBy);
        patient.setStatus("ACTIVE");

        patient = patientRepository.save(patient);
        log.info("Created patient {} with code {}", patient.getId(), patient.getPatientCode());
        return patientMapper.toDto(patient);
    }

    @Transactional(readOnly = true)
    public PatientResponse getPatient(UUID id) {
        Patient patient = patientRepository.findByIdAndIsDeletedFalse(id)
                .orElseThrow(() -> new NotFoundException("Patient not found: " + id));
        return patientMapper.toDto(patient);
    }

    @Transactional(readOnly = true)
    public PatientResponse getPatientByCode(String code) {
        Patient patient = patientRepository.findByPatientCodeAndIsDeletedFalse(code)
                .orElseThrow(() -> new NotFoundException("Patient not found with code: " + code));
        return patientMapper.toDto(patient);
    }

    @Transactional(readOnly = true)
    public Page<PatientResponse> getAllPatients(Pageable pageable) {
        return patientRepository.findAllByIsDeletedFalse(pageable)
                .map(patientMapper::toDto);
    }

    @Transactional(readOnly = true)
    public Page<PatientResponse> searchPatients(String query, Pageable pageable) {
        if (!StringUtils.hasText(query)) {
            return getAllPatients(pageable);
        }
        return patientRepository.searchPatients(query.trim(), pageable)
                .map(patientMapper::toDto);
    }

    @Transactional
    public PatientResponse updatePatient(UUID id, UpdatePatientRequest request) {
        Patient patient = patientRepository.findByIdAndIsDeletedFalse(id)
                .orElseThrow(() -> new NotFoundException("Patient not found: " + id));

        patientMapper.updateEntity(request, patient);
        patient = patientRepository.save(patient);
        return patientMapper.toDto(patient);
    }

    @Transactional
    public void deletePatient(UUID id) {
        Patient patient = patientRepository.findByIdAndIsDeletedFalse(id)
                .orElseThrow(() -> new NotFoundException("Patient not found: " + id));
        patient.setDeleted(true);
        patientRepository.save(patient);
        log.info("Soft-deleted patient {}", id);
    }
}
