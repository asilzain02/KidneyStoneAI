package com.kidneystone.patient.controller;

import com.kidneystone.patient.dto.CreatePatientRequest;
import com.kidneystone.patient.dto.PatientResponse;
import com.kidneystone.patient.dto.UpdatePatientRequest;
import com.kidneystone.patient.service.PatientService;
import com.kidneystone.shared.dto.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/patients")
@RequiredArgsConstructor
@Tag(name = "Patient", description = "Patient Management APIs")
@SecurityRequirement(name = "bearerAuth")
public class PatientController {

    private final PatientService patientService;

    @PostMapping
    @Operation(summary = "Register a new patient")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<ApiResponse<PatientResponse>> create(
            @Valid @RequestBody CreatePatientRequest request,
            Principal principal) {
        UUID registeredBy = UUID.fromString(principal.getName());
        PatientResponse response = patientService.createPatient(request, registeredBy);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success(response, "Patient registered successfully"));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get patient by ID")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<ApiResponse<PatientResponse>> getById(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(patientService.getPatient(id), "Patient retrieved"));
    }

    @GetMapping("/code/{code}")
    @Operation(summary = "Get patient by patient code")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<ApiResponse<PatientResponse>> getByCode(@PathVariable String code) {
        return ResponseEntity.ok(ApiResponse.success(patientService.getPatientByCode(code), "Patient retrieved"));
    }

    @GetMapping
    @Operation(summary = "List all patients with pagination and search")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<ApiResponse<Page<PatientResponse>>> list(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "createdAt") String sortBy,
            @RequestParam(defaultValue = "desc") String direction,
            @RequestParam(required = false) String search) {

        Sort sort = direction.equalsIgnoreCase("asc") ? Sort.by(sortBy).ascending() : Sort.by(sortBy).descending();
        Pageable pageable = PageRequest.of(page, size, sort);

        Page<PatientResponse> result = (search != null && !search.isBlank())
                ? patientService.searchPatients(search, pageable)
                : patientService.getAllPatients(pageable);

        return ResponseEntity.ok(ApiResponse.success(result, "Patients retrieved"));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update patient")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<ApiResponse<PatientResponse>> update(
            @PathVariable UUID id,
            @Valid @RequestBody UpdatePatientRequest request) {
        return ResponseEntity.ok(ApiResponse.success(patientService.updatePatient(id, request), "Patient updated"));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Soft-delete a patient")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    public ResponseEntity<ApiResponse<Void>> delete(@PathVariable UUID id) {
        patientService.deletePatient(id);
        return ResponseEntity.ok(ApiResponse.success(null, "Patient deleted"));
    }
}
