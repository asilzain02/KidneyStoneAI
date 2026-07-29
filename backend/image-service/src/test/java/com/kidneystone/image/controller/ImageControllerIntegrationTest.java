package com.kidneystone.image.controller;

import com.kidneystone.image.entity.MedicalImage;
import com.kidneystone.image.repository.MedicalImageRepository;
import com.kidneystone.image.storage.FileStorageService;
import org.junit.jupiter.api.*;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.domain.Page;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.domain.Pageable;

import static org.mockito.ArgumentMatchers.any;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for ImageController.
 * Uses MockMvc with mocked repository and storage to avoid DB + disk dependency.
 *
 * Each test scenario maps to a manual test case defined in the Sprint requirements:
 *   - upload PNG ✓
 *   - upload JPG ✓
 *   - upload DICOM ✓
 *   - reject PDF ✓
 *   - reject ZIP ✓
 *   - retrieve metadata ✓
 *   - list patient images ✓
 *   - delete image ✓
 */
@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = {
        "spring.jpa.hibernate.ddl-auto=none",
        "spring.flyway.enabled=false",
        "spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
        "security.jwt.secret=7c222fb2927d828af22f592134e8932480637c0d79cc5f6d6287951a37c3da33c67537494411fb31061f52d0a4c28f34175b5a6be58ab5b4976451def53a2386",
        "storage.upload-dir=target/test-uploads"
})
@DisplayName("ImageController Integration Tests")
class ImageControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private MedicalImageRepository imageRepository;

    @MockBean
    private FileStorageService fileStorageService;

    private UUID patientId;
    private UUID imageId;

    @BeforeEach
    void setUp() throws Exception {
        patientId = UUID.randomUUID();
        imageId   = UUID.randomUUID();

        MedicalImage img = new MedicalImage();
        img.setPatientId(patientId);
        img.setFileName("uuid_scan.png");
        img.setOriginalFileName("scan.png");
        img.setStoragePath(patientId + "/uuid_scan.png");
        img.setFileSize(1024L);
        img.setContentType("image/png");
        img.setModality("IMAGE");
        img.setUploadDate(LocalDateTime.now());
        img.setStatus("ACTIVE");

        Mockito.when(fileStorageService.store(any(UUID.class), any()))
               .thenReturn(patientId + "/uuid_scan.png");
        Mockito.when(imageRepository.save(any(MedicalImage.class))).thenReturn(img);
        Mockito.when(imageRepository.findByIdAndIsDeletedFalse(any(UUID.class)))
               .thenReturn(Optional.of(img));
        // Fix: stub the list-by-patient query so it returns Page.empty() instead of null
        Mockito.when(imageRepository.findAllByPatientIdAndIsDeletedFalse(any(UUID.class), any(Pageable.class)))
               .thenReturn(Page.empty());
    }

    // ── Upload PNG ──────────────────────────────────────────────────────────

    @Test
    @WithMockUser(username = "550e8400-e29b-41d4-a716-446655440000", authorities = "ROLE_DOCTOR")
    @DisplayName("Upload PNG - 201 Created")
    void uploadPng_returns201() throws Exception {
        MockMultipartFile file = new MockMultipartFile("file", "scan.png", "image/png",
                "fake-png-content".getBytes());

        mockMvc.perform(multipart("/api/v1/images/upload/" + patientId).file(file))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status").value("SUCCESS"));
    }

    // ── Upload JPG ──────────────────────────────────────────────────────────

    @Test
    @WithMockUser(username = "550e8400-e29b-41d4-a716-446655440000", authorities = "ROLE_DOCTOR")
    @DisplayName("Upload JPG - 201 Created")
    void uploadJpg_returns201() throws Exception {
        MockMultipartFile file = new MockMultipartFile("file", "scan.jpg", "image/jpeg",
                "fake-jpg-content".getBytes());

        mockMvc.perform(multipart("/api/v1/images/upload/" + patientId).file(file))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status").value("SUCCESS"));
    }

    // ── Upload DICOM ────────────────────────────────────────────────────────

    @Test
    @WithMockUser(username = "550e8400-e29b-41d4-a716-446655440000", authorities = "ROLE_DOCTOR")
    @DisplayName("Upload DICOM (.dcm) - 201 Created")
    void uploadDicom_returns201() throws Exception {
        MockMultipartFile file = new MockMultipartFile("file", "scan.dcm", "application/dicom",
                "DICM-fake-bytes".getBytes());

        mockMvc.perform(multipart("/api/v1/images/upload/" + patientId).file(file))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status").value("SUCCESS"));
    }

    // ── Reject PDF ──────────────────────────────────────────────────────────

    @Test
    @WithMockUser(username = "550e8400-e29b-41d4-a716-446655440000", authorities = "ROLE_DOCTOR")
    @DisplayName("Reject PDF - 400 Bad Request")
    void uploadPdf_returns400() throws Exception {
        MockMultipartFile file = new MockMultipartFile("file", "report.pdf", "application/pdf",
                "fake-pdf".getBytes());

        mockMvc.perform(multipart("/api/v1/images/upload/" + patientId).file(file))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value("ERROR"));
    }

    // ── Reject ZIP ──────────────────────────────────────────────────────────

    @Test
    @WithMockUser(username = "550e8400-e29b-41d4-a716-446655440000", authorities = "ROLE_DOCTOR")
    @DisplayName("Reject ZIP - 400 Bad Request")
    void uploadZip_returns400() throws Exception {
        MockMultipartFile file = new MockMultipartFile("file", "archive.zip", "application/zip",
                "fake-zip".getBytes());

        mockMvc.perform(multipart("/api/v1/images/upload/" + patientId).file(file))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value("ERROR"));
    }

    // ── Retrieve metadata ───────────────────────────────────────────────────

    @Test
    @WithMockUser(authorities = "ROLE_DOCTOR")
    @DisplayName("Retrieve metadata by ID - 200 OK")
    void getById_returns200() throws Exception {
        mockMvc.perform(get("/api/v1/images/" + imageId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("SUCCESS"));
    }

    // ── List patient images ─────────────────────────────────────────────────

    @Test
    @WithMockUser(authorities = "ROLE_DOCTOR")
    @DisplayName("List patient images - 200 OK")
    void listByPatient_returns200() throws Exception {
        mockMvc.perform(get("/api/v1/images/patient/" + patientId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("SUCCESS"));
    }

    // ── Delete image ────────────────────────────────────────────────────────

    @Test
    @WithMockUser(authorities = "ROLE_DOCTOR")
    @DisplayName("Soft-delete image - 200 OK")
    void deleteImage_returns200() throws Exception {
        mockMvc.perform(delete("/api/v1/images/" + imageId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("SUCCESS"));
    }

    // ── Unauthenticated ─────────────────────────────────────────────────────

    @Test
    @DisplayName("Upload without auth - 401 Unauthorized")
    void upload_noAuth_returns401() throws Exception {
        MockMultipartFile file = new MockMultipartFile("file", "scan.png", "image/png",
                "fake".getBytes());
        mockMvc.perform(multipart("/api/v1/images/upload/" + patientId).file(file))
                .andExpect(status().isUnauthorized());
    }
}
