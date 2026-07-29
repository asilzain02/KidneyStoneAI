package com.kidneystone.image.validation;

import com.kidneystone.shared.exception.ValidationException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * Centralised file validation component.
 * Reused by the service layer; not tied to HTTP.
 */
@Component
public class ImageFileValidator {

    private static final List<String> ALLOWED_EXTENSIONS = List.of("png", "jpg", "jpeg", "dcm");
    private static final List<String> ALLOWED_CONTENT_TYPES = List.of(
            "image/png",
            "image/jpeg",
            "image/jpg",
            "application/dicom",
            "application/octet-stream"   // many DICOM clients send this
    );

    @Value("${storage.max-file-size-bytes:52428800}")   // 50 MB default
    private long maxFileSizeBytes;

    public void validate(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new ValidationException("File must not be null or empty");
        }

        String originalName = file.getOriginalFilename();
        if (originalName == null || originalName.isBlank()) {
            throw new ValidationException("Original filename is missing");
        }

        String extension = extractExtension(originalName);
        if (!ALLOWED_EXTENSIONS.contains(extension.toLowerCase())) {
            throw new ValidationException(
                    "Unsupported file type '" + extension + "'. Allowed: " +
                    String.join(", ", ALLOWED_EXTENSIONS));
        }

        String contentType = file.getContentType();
        if (contentType == null || ALLOWED_CONTENT_TYPES.stream()
                .noneMatch(allowed -> allowed.equalsIgnoreCase(contentType))) {
            throw new ValidationException(
                    "Unsupported content type '" + contentType + "'");
        }

        if (file.getSize() > maxFileSizeBytes) {
            long maxMb = maxFileSizeBytes / (1024 * 1024);
            throw new ValidationException(
                    "File size " + (file.getSize() / (1024 * 1024)) + " MB exceeds maximum of " + maxMb + " MB");
        }
    }

    private String extractExtension(String filename) {
        int dot = filename.lastIndexOf('.');
        return (dot >= 0 && dot < filename.length() - 1)
                ? filename.substring(dot + 1)
                : "";
    }

    /**
     * Derive modality from extension.
     */
    public String detectModality(String originalFileName) {
        if (originalFileName == null) return "UNKNOWN";
        String ext = extractExtension(originalFileName).toLowerCase();
        return switch (ext) {
            case "dcm" -> "DICOM";
            case "png", "jpg", "jpeg" -> "IMAGE";
            default -> "UNKNOWN";
        };
    }
}
