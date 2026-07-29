package com.kidneystone.image.service;

import com.kidneystone.image.dto.ImageResponse;
import com.kidneystone.image.entity.MedicalImage;
import com.kidneystone.image.mapper.ImageMapper;
import com.kidneystone.image.repository.MedicalImageRepository;
import com.kidneystone.image.storage.FileStorageService;
import com.kidneystone.image.validation.ImageFileValidator;
import com.kidneystone.shared.exception.NotFoundException;
import com.kidneystone.shared.exception.ValidationException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("ImageService Unit Tests")
class ImageServiceTest {

    @Mock private MedicalImageRepository imageRepository;
    @Mock private ImageMapper imageMapper;
    @Mock private FileStorageService fileStorageService;
    @Mock private ImageFileValidator fileValidator;

    @InjectMocks
    private ImageService imageService;

    private UUID patientId;
    private UUID imageId;
    private UUID uploadedBy;

    @BeforeEach
    void setUp() {
        patientId  = UUID.randomUUID();
        imageId    = UUID.randomUUID();
        uploadedBy = UUID.randomUUID();
    }

    // ── upload ─────────────────────────────────────────────────────────────

    @Test
    @DisplayName("upload PNG - happy path")
    void upload_png_success() throws IOException {
        MockMultipartFile file = new MockMultipartFile(
                "file", "scan.png", "image/png", "fake-png-bytes".getBytes());

        MedicalImage saved = buildImage();
        ImageResponse expected = new ImageResponse();
        expected.setId(saved.getId());

        doNothing().when(fileValidator).validate(file);
        when(fileStorageService.store(patientId, file)).thenReturn(patientId + "/uuid_scan.png");
        when(fileValidator.detectModality("scan.png")).thenReturn("IMAGE");
        when(imageRepository.save(any(MedicalImage.class))).thenReturn(saved);
        when(imageMapper.toDto(saved)).thenReturn(expected);

        ImageResponse result = imageService.upload(patientId, file, null, uploadedBy);

        assertThat(result.getId()).isEqualTo(saved.getId());
        verify(fileValidator).validate(file);
        verify(fileStorageService).store(patientId, file);
        verify(imageRepository).save(any(MedicalImage.class));
    }

    @Test
    @DisplayName("upload - validation failure throws ValidationException")
    void upload_invalidFile_throws() {
        MultipartFile file = new MockMultipartFile("file", "hack.exe", "application/octet-stream", new byte[0]);
        doThrow(new ValidationException("Unsupported file type")).when(fileValidator).validate(file);

        assertThatThrownBy(() -> imageService.upload(patientId, file, null, uploadedBy))
                .isInstanceOf(ValidationException.class)
                .hasMessageContaining("Unsupported");
    }

    @Test
    @DisplayName("upload - storage IO failure wraps in RuntimeException")
    void upload_storageFailure_throws() throws IOException {
        MockMultipartFile file = new MockMultipartFile("file", "scan.dcm", "application/dicom", "bytes".getBytes());
        doNothing().when(fileValidator).validate(file);
        when(fileStorageService.store(patientId, file)).thenThrow(new IOException("disk full"));

        assertThatThrownBy(() -> imageService.upload(patientId, file, null, uploadedBy))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("File storage failed");
    }

    // ── getById ────────────────────────────────────────────────────────────

    @Test
    @DisplayName("getById - existing image returns response")
    void getById_found() {
        MedicalImage image = buildImage();
        ImageResponse expected = new ImageResponse();
        expected.setId(imageId);

        when(imageRepository.findByIdAndIsDeletedFalse(imageId)).thenReturn(Optional.of(image));
        when(imageMapper.toDto(image)).thenReturn(expected);

        ImageResponse result = imageService.getById(imageId);
        assertThat(result.getId()).isEqualTo(imageId);
    }

    @Test
    @DisplayName("getById - missing image throws NotFoundException")
    void getById_notFound() {
        when(imageRepository.findByIdAndIsDeletedFalse(imageId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> imageService.getById(imageId))
                .isInstanceOf(NotFoundException.class)
                .hasMessageContaining(imageId.toString());
    }

    // ── delete ─────────────────────────────────────────────────────────────

    @Test
    @DisplayName("delete - soft-deletes and saves")
    void delete_setsDeletedTrue() {
        MedicalImage image = buildImage();
        when(imageRepository.findByIdAndIsDeletedFalse(imageId)).thenReturn(Optional.of(image));
        when(imageRepository.save(image)).thenReturn(image);

        imageService.delete(imageId);

        assertThat(image.isDeleted()).isTrue();
        assertThat(image.getStatus()).isEqualTo("DELETED");
        verify(imageRepository).save(image);
    }

    @Test
    @DisplayName("delete - not found throws NotFoundException")
    void delete_notFound() {
        when(imageRepository.findByIdAndIsDeletedFalse(imageId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> imageService.delete(imageId))
                .isInstanceOf(NotFoundException.class);
    }

    // ── helpers ────────────────────────────────────────────────────────────

    private MedicalImage buildImage() {
        MedicalImage img = new MedicalImage();
        img.setId(imageId);
        img.setPatientId(patientId);
        img.setFileName("uuid_scan.png");
        img.setOriginalFileName("scan.png");
        img.setStoragePath(patientId + "/uuid_scan.png");
        img.setFileSize(1024L);
        img.setContentType("image/png");
        img.setModality("IMAGE");
        img.setUploadDate(LocalDateTime.now());
        img.setStatus("ACTIVE");
        return img;
    }
}
