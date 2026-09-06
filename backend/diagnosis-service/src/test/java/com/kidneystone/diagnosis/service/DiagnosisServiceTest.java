package com.kidneystone.diagnosis.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.kidneystone.diagnosis.client.AiEngineClient;
import com.kidneystone.diagnosis.dto.AiAnalysisResult;
import com.kidneystone.diagnosis.dto.DiagnosisResponse;
import com.kidneystone.diagnosis.entity.Diagnosis;
import com.kidneystone.diagnosis.exception.AiEngineException;
import com.kidneystone.diagnosis.mapper.DiagnosisMapper;
import com.kidneystone.diagnosis.repository.DiagnosisRepository;
import com.kidneystone.diagnosis.client.ImageServiceClient;
import com.kidneystone.diagnosis.client.ImageServiceClient.DownloadedImage;
import com.kidneystone.diagnosis.client.SeverityServiceClient;
import com.kidneystone.diagnosis.client.TreatmentServiceClient;
import com.kidneystone.diagnosis.client.ReportServiceClient;
import com.kidneystone.diagnosis.dto.external.SeverityResponse;
import com.kidneystone.diagnosis.dto.external.TreatmentResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DiagnosisServiceTest {

    @Mock
    private DiagnosisRepository diagnosisRepository;

    @Mock
    private AiEngineClient aiEngineClient;

    @Mock
    private ImageServiceClient imageServiceClient;

    @Mock
    private DiagnosisMapper diagnosisMapper;

    @Mock
    private ObjectMapper objectMapper;

    @Mock
    private SeverityServiceClient severityServiceClient;

    @Mock
    private TreatmentServiceClient treatmentServiceClient;

    @Mock
    private ReportServiceClient reportServiceClient;

    @InjectMocks
    private DiagnosisService diagnosisService;

    private UUID imageId;
    private UUID patientId;
    private UUID requestedBy;
    private String authHeader;
    private byte[] imageBytes;
    private String filename;
    private String contentType;

    @BeforeEach
    void setUp() {
        imageId = UUID.randomUUID();
        patientId = UUID.randomUUID();
        requestedBy = UUID.randomUUID();
        authHeader = "Bearer dummy-token";
        imageBytes = "mockImageBytes".getBytes();
        filename = "test.jpg";
        contentType = "image/jpeg";

        ReflectionTestUtils.setField(diagnosisService, "aiEngineBaseUrl", "http://ai-engine:8000");
    }

    @Test
    void runDiagnosis_Success() throws Exception {
        // Arrange
        Diagnosis pendingDiagnosis = new Diagnosis();
        pendingDiagnosis.setId(UUID.randomUUID());
        pendingDiagnosis.setStatus("PENDING");

        AiAnalysisResult aiResult = new AiAnalysisResult();
        aiResult.setInferenceId("inf-123");

        Diagnosis completedDiagnosis = new Diagnosis();
        completedDiagnosis.setId(pendingDiagnosis.getId());
        completedDiagnosis.setStatus("COMPLETED");
        completedDiagnosis.setInferenceId("inf-123");

        DiagnosisResponse expectedResponse = new DiagnosisResponse();
        expectedResponse.setInferenceId("inf-123");

        // Mock saving PENDING record
        when(diagnosisRepository.save(any(Diagnosis.class))).thenReturn(pendingDiagnosis).thenReturn(completedDiagnosis);
        // Mock image fetch
        DownloadedImage downloadedImage = new DownloadedImage(imageBytes, filename, contentType);
        when(imageServiceClient.downloadImage(imageId, authHeader)).thenReturn(downloadedImage);

        // Mock AI Engine call
        when(aiEngineClient.analyze(imageBytes, filename, contentType)).thenReturn(aiResult);
        
        // Mock JSON serialization
        when(objectMapper.writeValueAsString(aiResult)).thenReturn("{}");

        // Mock Mapper
        when(diagnosisMapper.toResponse(completedDiagnosis, "http://ai-engine:8000")).thenReturn(expectedResponse);

        // Mock external clients
        when(severityServiceClient.assessSeverity(any(), eq(authHeader))).thenReturn(new SeverityResponse());
        when(treatmentServiceClient.recommendTreatment(any(), eq(authHeader))).thenReturn(new TreatmentResponse());

        // Act
        DiagnosisResponse response = diagnosisService.runDiagnosis(imageId, patientId, requestedBy, authHeader);

        // Assert
        assertNotNull(response);
        assertEquals("inf-123", response.getInferenceId());

        verify(imageServiceClient, times(1)).downloadImage(imageId, authHeader);
        verify(diagnosisRepository, times(2)).save(any(Diagnosis.class));
        verify(aiEngineClient, times(1)).analyze(imageBytes, filename, contentType);
        verify(diagnosisMapper, times(1)).applyAiResult(aiResult, pendingDiagnosis);
    }

    @Test
    void runDiagnosis_AiEngineFails_UpdatesStatusToFailed() {
        // Arrange
        Diagnosis pendingDiagnosis = new Diagnosis();
        pendingDiagnosis.setId(UUID.randomUUID());

        when(diagnosisRepository.save(any(Diagnosis.class))).thenReturn(pendingDiagnosis);
        
        DownloadedImage downloadedImage = new DownloadedImage(imageBytes, filename, contentType);
        when(imageServiceClient.downloadImage(imageId, authHeader)).thenReturn(downloadedImage);
        when(aiEngineClient.analyze(any(), any(), any())).thenThrow(new AiEngineException("Timeout"));

        // Act & Assert
        Exception ex = assertThrows(AiEngineException.class, () ->
                diagnosisService.runDiagnosis(imageId, patientId, requestedBy, authHeader));

        assertEquals("Timeout", ex.getMessage());

        verify(diagnosisRepository, times(2)).save(any(Diagnosis.class));
        // Verify the second save was for a FAILED status
        verify(diagnosisRepository).save(argThat(d -> "FAILED".equals(d.getStatus())));
    }
}
