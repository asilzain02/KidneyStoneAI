package com.kidneystone.patient.mapper;

import com.kidneystone.patient.dto.PatientResponse;
import com.kidneystone.patient.entity.Patient;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

import com.kidneystone.patient.dto.CreatePatientRequest;
import com.kidneystone.patient.dto.UpdatePatientRequest;

@Mapper(componentModel = "spring", nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
public interface PatientMapper {

    PatientResponse toDto(Patient patient);

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "patientCode", ignore = true)
    @Mapping(target = "registeredBy", ignore = true)
    @Mapping(target = "status", ignore = true)
    @Mapping(target = "emergencyContacts", ignore = true)
    @Mapping(target = "deleted", ignore = true)
    @Mapping(target = "version", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "updatedBy", ignore = true)
    Patient toEntity(CreatePatientRequest request);

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "patientCode", ignore = true)
    @Mapping(target = "registeredBy", ignore = true)
    @Mapping(target = "emergencyContacts", ignore = true)
    @Mapping(target = "deleted", ignore = true)
    @Mapping(target = "version", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "updatedBy", ignore = true)
    void updateEntity(UpdatePatientRequest request, @MappingTarget Patient patient);
}
