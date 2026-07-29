package com.kidneystone.image.controller;

import com.kidneystone.image.dto.ImageResponse;
import com.kidneystone.image.dto.ImageUploadRequest;
import com.kidneystone.image.service.ImageService;
import com.kidneystone.shared.dto.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.PathResource;
import org.springframework.core.io.Resource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.nio.file.Path;
import java.security.Principal;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/images")
@RequiredArgsConstructor
@Tag(name = "Image", description = "Medical Image Management APIs")
@SecurityRequirement(name = "bearerAuth")
public class ImageController {

    private final ImageService imageService;

    // POST /api/v1/images/upload/{patientId}
    @PostMapping(value = "/upload/{patientId}", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "Upload a medical image for a patient")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<ApiResponse<ImageResponse>> upload(
            @PathVariable UUID patientId,
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "modality", required = false) String modality,
            Principal principal) {

        UUID uploadedBy = UUID.fromString(principal.getName());
        ImageUploadRequest request = new ImageUploadRequest();
        request.setModality(modality);

        ImageResponse response = imageService.upload(patientId, file, request, uploadedBy);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success(response, "Image uploaded successfully"));
    }

    // GET /api/v1/images/{id}
    @GetMapping("/{id}")
    @Operation(summary = "Get image metadata by ID")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<ApiResponse<ImageResponse>> getById(@PathVariable UUID id) {
        return ResponseEntity.ok(
                ApiResponse.success(imageService.getById(id), "Image retrieved"));
    }

    // GET /api/v1/images/patient/{patientId}
    @GetMapping("/patient/{patientId}")
    @Operation(summary = "List all images for a patient")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<ApiResponse<Page<ImageResponse>>> getByPatient(
            @PathVariable UUID patientId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "uploadDate") String sortBy,
            @RequestParam(defaultValue = "desc") String direction) {

        Sort sort = direction.equalsIgnoreCase("asc")
                ? Sort.by(sortBy).ascending()
                : Sort.by(sortBy).descending();
        Pageable pageable = PageRequest.of(page, size, sort);

        return ResponseEntity.ok(
                ApiResponse.success(imageService.getByPatient(patientId, pageable), "Images retrieved"));
    }

    // GET /api/v1/images/download/{id}
    @GetMapping("/download/{id}")
    @Operation(summary = "Download the binary file of an image")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<Resource> download(@PathVariable UUID id) {
        ImageResponse meta = imageService.getById(id);
        Path filePath = imageService.resolveFilePath(id);

        Resource resource = new PathResource(filePath);
        if (!resource.exists() || !resource.isReadable()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }

        String contentType = meta.getContentType() != null
                ? meta.getContentType()
                : MediaType.APPLICATION_OCTET_STREAM_VALUE;

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"" + meta.getOriginalFileName() + "\"")
                .body(resource);
    }

    // DELETE /api/v1/images/{id}
    @DeleteMapping("/{id}")
    @Operation(summary = "Soft-delete an image")
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_DOCTOR')")
    public ResponseEntity<ApiResponse<Void>> delete(@PathVariable UUID id) {
        imageService.delete(id);
        return ResponseEntity.ok(ApiResponse.success(null, "Image deleted"));
    }
}
