package com.kidneystone.diagnosis.client;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.kidneystone.diagnosis.dto.AiAnalysisResult;
import com.kidneystone.diagnosis.exception.AiEngineException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

/**
 * Purpose:
 *   HTTP client for the Python AI Engine's POST /api/v1/ai/analyze endpoint.
 *
 *   Responsibilities:
 *     - Send a CT image as multipart/form-data to the AI Engine.
 *     - Parse the JSON response into AiAnalysisResult.
 *     - Map all HTTP/network failures to typed AiEngineException.
 *     - Add the shared secret header when configured.
 *
 *   Boundaries:
 *     - Does NOT contain ML logic.
 *     - Does NOT know about patients or diagnoses.
 *     - Does NOT retry — caller (DiagnosisService) decides retry policy.
 *
 *   Configuration (application.yml):
 *     ai-engine.base-url: http://localhost:8000
 *     ai-engine.secret:   (optional)
 */
@Slf4j
@Component
public class AiEngineClient {

    private static final String ANALYZE_PATH = "/api/v1/ai/analyze";
    private static final String SECRET_HEADER = "X-AI-Secret";

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    /** Base URL of the Python AI Engine (e.g. http://ai-engine:8000). */
    @Value("${ai-engine.base-url:http://localhost:8000}")
    private String aiEngineBaseUrl;

    /**
     * Optional shared secret.  If set, added to every request as X-AI-Secret.
     * The AI Engine validates this when AI_ENGINE_SECRET env var is configured.
     */
    @Value("${ai-engine.secret:}")
    private String aiEngineSecret;

    public AiEngineClient(RestTemplate restTemplate, ObjectMapper objectMapper) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
    }

    /**
     * Purpose:
     *   Send a CT image to the AI Engine and return the parsed analysis result.
     *
     * @param imageBytes   raw bytes of the CT image file
     * @param filename     original filename (used by AI Engine for stem naming)
     * @param contentType  MIME type of the image (e.g. "image/jpeg")
     * @return             parsed AiAnalysisResult
     * @throws AiEngineException on any connection, timeout, or server error
     */
    public AiAnalysisResult analyze(byte[] imageBytes, String filename, String contentType) {
        String url = aiEngineBaseUrl.stripTrailing() + ANALYZE_PATH;

        log.info("Sending image to AI Engine: url={}, filename={}, size={}B",
                url, filename, imageBytes.length);

        // ── Build multipart request ────────────────────────────────────────

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        // Purpose:
        // Add shared secret header if configured — prevents direct external access
        // to the AI Engine inference endpoint.
        if (aiEngineSecret != null && !aiEngineSecret.isBlank()) {
            headers.set(SECRET_HEADER, aiEngineSecret);
        }

        // Wrap image bytes as a named multipart part "file"
        ByteArrayResource fileResource = new ByteArrayResource(imageBytes) {
            @Override
            public String getFilename() {
                return filename != null ? filename : "ct_image.jpg";
            }
        };

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        HttpHeaders fileHeaders = new HttpHeaders();
        fileHeaders.setContentType(
                contentType != null
                        ? MediaType.parseMediaType(contentType)
                        : MediaType.IMAGE_JPEG
        );
        body.add("file", new HttpEntity<>(fileResource, fileHeaders));

        HttpEntity<MultiValueMap<String, Object>> requestEntity =
                new HttpEntity<>(body, headers);

        // ── Execute and handle errors ──────────────────────────────────────

        try {
            ResponseEntity<String> response = restTemplate.exchange(
                    url,
                    HttpMethod.POST,
                    requestEntity,
                    String.class
            );

            if (!response.getStatusCode().is2xxSuccessful()) {
                throw new AiEngineException(
                        "AI Engine returned HTTP " + response.getStatusCode()
                                + ": " + response.getBody()
                );
            }

            String responseBody = response.getBody();
            if (responseBody == null || responseBody.isBlank()) {
                throw new AiEngineException("AI Engine returned an empty response body.");
            }

            AiAnalysisResult result = objectMapper.readValue(responseBody, AiAnalysisResult.class);
            log.info("AI Engine response received: inferenceId={}, class={}, confidence={}",
                    result.getInferenceId(),
                    result.getClassification() != null ? result.getClassification().getPredictedClass() : "?",
                    result.getClassification() != null ? result.getClassification().getConfidence() : "?");

            return result;

        } catch (ResourceAccessException e) {
            // Covers connection refused, read timeout, etc.
            log.error("AI Engine unreachable: url={}, error={}", url, e.getMessage());
            throw new AiEngineException(
                    "AI Engine is unavailable at " + url + ". "
                            + "Please verify the service is running.", e
            );
        } catch (RestClientException e) {
            log.error("AI Engine HTTP error: url={}, error={}", url, e.getMessage());
            throw new AiEngineException("AI Engine HTTP error: " + e.getMessage(), e);
        } catch (AiEngineException e) {
            throw e;
        } catch (Exception e) {
            log.error("Failed to parse AI Engine response: {}", e.getMessage());
            throw new AiEngineException("Failed to parse AI Engine response: " + e.getMessage(), e);
        }
    }
}
