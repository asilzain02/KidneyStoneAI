package com.kidneystone.image.storage;

import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Path;
import java.util.UUID;

/**
 * File storage abstraction.
 * Implementations can target local disk, MinIO, AWS S3, etc.
 * Business logic never touches the implementation directly.
 */
public interface FileStorageService {

    /**
     * Store a file under a patient-scoped directory.
     *
     * @param patientId the patient UUID (used as sub-directory)
     * @param file      the uploaded multipart file
     * @return relative storage path (relative to upload root)
     * @throws IOException if writing fails
     */
    String store(UUID patientId, MultipartFile file) throws IOException;

    /**
     * Resolve an absolute {@link Path} from a relative storage path.
     *
     * @param storagePath relative path returned by {@link #store}
     * @return absolute path on the filesystem
     */
    Path resolve(String storagePath);

    /**
     * Permanently delete a stored file.
     *
     * @param storagePath relative path returned by {@link #store}
     */
    void delete(String storagePath);
}
