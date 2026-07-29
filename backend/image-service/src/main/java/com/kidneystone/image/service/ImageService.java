package com.kidneystone.image.service;

import com.kidneystone.image.dto.ImageResponse;
import com.kidneystone.image.dto.ImageUploadRequest;
import com.kidneystone.image.entity.MedicalImage;
import com.kidneystone.image.mapper.ImageMapper;
import com.kidneystone.image.repository.MedicalImageRepository;
import com.kidneystone.image.storage.FileStorageService;
import com.kidneystone.image.validation.ImageFileValidator;
import com.kidneystone.shared.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class ImageService {

    private final MedicalImageRepository imageRepository;
    private final ImageMapper imageMapper;
    private final FileStorageService fileStorageService;
    private final ImageFileValidator fileValidator;

    // ── Upload ──────────────────────────────────────────────────────────────

    @Transactional
    public ImageResponse upload(UUID patientId, MultipartFile file,
                                ImageUploadRequest request, UUID uploadedBy) {

        fileValidator.validate(file);

        String storagePath;
        try {
            storagePath = fileStorageService.store(patientId, file);
        } catch (IOException e) {
            log.error("Failed to store file for patient {}: {}", patientId, e.getMessage());
            throw new RuntimeException("File storage failed: " + e.getMessage(), e);
        }

        String originalName = file.getOriginalFilename() != null
                ? file.getOriginalFilename() : "upload";

        String modality = (request != null && request.getModality() != null && !request.getModality().isBlank())
                ? request.getModality().toUpperCase()
                : fileValidator.detectModality(originalName);

        MedicalImage image = new MedicalImage();
        image.setPatientId(patientId);
        image.setFileName(storagePath.contains("/") ? storagePath.substring(storagePath.lastIndexOf('/') + 1) : storagePath);
        image.setOriginalFileName(originalName);
        image.setStoragePath(storagePath);
        image.setFileSize(file.getSize());
        image.setContentType(file.getContentType());
        image.setModality(modality);
        image.setUploadDate(LocalDateTime.now());
        image.setStatus("ACTIVE");

        image = imageRepository.save(image);
        log.info("Uploaded image {} for patient {}", image.getId(), patientId);
        return imageMapper.toDto(image);
    }

    // ── Fetch metadata ──────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public ImageResponse getById(UUID id) {
        MedicalImage image = imageRepository.findByIdAndIsDeletedFalse(id)
                .orElseThrow(() -> new NotFoundException("Image not found: " + id));
        return imageMapper.toDto(image);
    }

    @Transactional(readOnly = true)
    public Page<ImageResponse> getByPatient(UUID patientId, Pageable pageable) {
        return imageRepository.findAllByPatientIdAndIsDeletedFalse(patientId, pageable)
                .map(imageMapper::toDto);
    }

    // ── Download ─────────────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public Path resolveFilePath(UUID id) {
        MedicalImage image = imageRepository.findByIdAndIsDeletedFalse(id)
                .orElseThrow(() -> new NotFoundException("Image not found: " + id));
        return fileStorageService.resolve(image.getStoragePath());
    }

    // ── Soft Delete ──────────────────────────────────────────────────────────

    @Transactional
    public void delete(UUID id) {
        MedicalImage image = imageRepository.findByIdAndIsDeletedFalse(id)
                .orElseThrow(() -> new NotFoundException("Image not found: " + id));
        image.setDeleted(true);
        image.setStatus("DELETED");
        imageRepository.save(image);
        log.info("Soft-deleted image {}", id);
    }
}
