package com.kidneystone.image.storage;

import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.UUID;

/**
 * Local-disk implementation of {@link FileStorageService}.
 * Files are stored at:  {storage.upload-dir}/{patientId}/{uniqueFileName}
 */
@Slf4j
@Service
public class LocalFileStorageService implements FileStorageService {

    @Value("${storage.upload-dir:uploads}")
    private String uploadDir;

    private Path uploadRoot;

    @PostConstruct
    public void init() {
        uploadRoot = Paths.get(uploadDir).toAbsolutePath().normalize();
        try {
            Files.createDirectories(uploadRoot);
            log.info("File storage root initialised at: {}", uploadRoot);
        } catch (IOException e) {
            throw new IllegalStateException("Cannot create upload root directory: " + uploadRoot, e);
        }
    }

    @Override
    public String store(UUID patientId, MultipartFile file) throws IOException {
        Path patientDir = uploadRoot.resolve(patientId.toString());
        Files.createDirectories(patientDir);

        String originalName = file.getOriginalFilename() != null
                ? file.getOriginalFilename().replaceAll("[^a-zA-Z0-9._-]", "_")
                : "upload";

        String uniqueName = UUID.randomUUID() + "_" + originalName;
        Path destination = patientDir.resolve(uniqueName).normalize();

        // Security: prevent path traversal
        if (!destination.startsWith(patientDir)) {
            throw new IOException("Illegal file path: " + uniqueName);
        }

        Files.copy(file.getInputStream(), destination, StandardCopyOption.REPLACE_EXISTING);
        log.info("Stored file {} for patient {}", uniqueName, patientId);

        // Return relative path: {patientId}/{uniqueName}
        return patientId + "/" + uniqueName;
    }

    @Override
    public Path resolve(String storagePath) {
        return uploadRoot.resolve(storagePath).normalize();
    }

    @Override
    public void delete(String storagePath) {
        try {
            Path target = resolve(storagePath);
            Files.deleteIfExists(target);
            log.info("Deleted file at {}", target);
        } catch (IOException e) {
            log.warn("Could not delete file at {}: {}", storagePath, e.getMessage());
        }
    }
}
