package com.kidneystone.patient.service;

import com.kidneystone.patient.dto.CreatePatientRequest;
import com.kidneystone.patient.dto.PatientResponse;
import com.kidneystone.patient.entity.Patient;
import com.kidneystone.patient.mapper.PatientMapper;
import com.kidneystone.patient.repository.PatientRepository;
import com.kidneystone.shared.exception.NotFoundException;
import com.kidneystone.shared.exception.ValidationException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDate;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PatientServiceTest {

    @Mock private PatientRepository patientRepository;
    @Mock private PatientMapper patientMapper;
    @Mock private PatientCodeGenerator codeGenerator;

    @InjectMocks private PatientService patientService;

    private Patient mockPatient;
    private PatientResponse mockResponse;

    @BeforeEach
    void setUp() {
        mockPatient = new Patient();
        mockPatient.setId(UUID.randomUUID());
        mockPatient.setPatientCode("PAT-26-01001");
        mockPatient.setFirstName("John");
        mockPatient.setLastName("Doe");
        mockPatient.setStatus("ACTIVE");

        mockResponse = new PatientResponse();
        mockResponse.setId(mockPatient.getId());
        mockResponse.setPatientCode("PAT-26-01001");
        mockResponse.setFirstName("John");
        mockResponse.setLastName("Doe");
    }

    @Test
    void createPatient_Success() {
        CreatePatientRequest req = new CreatePatientRequest();
        req.setFirstName("John");
        req.setLastName("Doe");
        req.setDateOfBirth(LocalDate.of(1990, 1, 1));
        req.setGender("MALE");

        when(patientMapper.toEntity(req)).thenReturn(mockPatient);
        when(codeGenerator.generate()).thenReturn("PAT-26-01001");
        when(patientRepository.save(any(Patient.class))).thenReturn(mockPatient);
        when(patientMapper.toDto(mockPatient)).thenReturn(mockResponse);

        PatientResponse result = patientService.createPatient(req, UUID.randomUUID());

        assertNotNull(result);
        assertEquals("PAT-26-01001", result.getPatientCode());
        verify(patientRepository).save(any(Patient.class));
    }

    @Test
    void createPatient_DuplicateEmail_ThrowsValidationException() {
        CreatePatientRequest req = new CreatePatientRequest();
        req.setEmail("existing@test.com");
        req.setFirstName("Jane");
        req.setLastName("Doe");
        req.setDateOfBirth(LocalDate.of(1985, 5, 15));
        req.setGender("FEMALE");

        when(patientRepository.existsByEmailAndIsDeletedFalse("existing@test.com")).thenReturn(true);

        assertThrows(ValidationException.class, () -> patientService.createPatient(req, UUID.randomUUID()));
        verify(patientRepository, never()).save(any());
    }

    @Test
    void getPatient_NotFound_ThrowsNotFoundException() {
        UUID id = UUID.randomUUID();
        when(patientRepository.findByIdAndIsDeletedFalse(id)).thenReturn(Optional.empty());

        assertThrows(NotFoundException.class, () -> patientService.getPatient(id));
    }

    @Test
    void getPatient_Found_ReturnsResponse() {
        when(patientRepository.findByIdAndIsDeletedFalse(mockPatient.getId())).thenReturn(Optional.of(mockPatient));
        when(patientMapper.toDto(mockPatient)).thenReturn(mockResponse);

        PatientResponse result = patientService.getPatient(mockPatient.getId());

        assertNotNull(result);
        assertEquals(mockPatient.getId(), result.getId());
    }

    @Test
    void deletePatient_SoftDeletes() {
        when(patientRepository.findByIdAndIsDeletedFalse(mockPatient.getId())).thenReturn(Optional.of(mockPatient));

        patientService.deletePatient(mockPatient.getId());

        assertTrue(mockPatient.isDeleted());
        verify(patientRepository).save(mockPatient);
    }
}
