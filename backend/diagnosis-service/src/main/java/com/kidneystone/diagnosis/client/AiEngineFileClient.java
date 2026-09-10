package com.kidneystone.diagnosis.client;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

/**
 * Purpose:
 *   Fetches binary artefact files (Grad-CAM heatmap, overlay) from the AI Engine
 *   using the existing endpoint:
 *
 *     GET /api/v1/ai/files/{inferenceId}/{filename}
 *
 *   Used exclusively by DiagnosisComparisonGenerator to obtain the actual
 *   Grad-CAM PNG bytes so they can be composited into the comparison image.
 *
 *   This client does NOT perform inference — it only retrieves files that
 *   the AI Engine has already generated.
 */
@Slf4j
@Component
public class AiEngineFileClient {

    private static final String FILES_PATH = "/api/v1/ai/files/{inferenceId}/{filename}";

    private final RestTemplate restTemplate;

    @Value("${ai-engine.base-url:http://localhost:8000}")
    private String aiEngineBaseUrl;

    @Value("${ai-engine.secret:}")
    private String aiEngineSecret;

    public AiEngineFileClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Purpose:
     *   Download a binary file from the AI Engine output directory.
     *
     * @param inferenceId  ID of the inference run (from AiAnalysisResult)
     * @param filename     e.g. "overlay.png", "heatmap.png"
     * @return             raw bytes of the file, or null if unavailable
     */
    public byte[] fetchFile(String inferenceId, String filename) {
        if (inferenceId == null || filename == null) return null;

        String url = aiEngineBaseUrl.stripTrailing()
                + "/api/v1/ai/files/" + inferenceId + "/" + filename;

        HttpHeaders headers = new HttpHeaders();
        if (aiEngineSecret != null && !aiEngineSecret.isBlank()) {
            headers.set("X-AI-Secret", aiEngineSecret);
        }

        try {
            ResponseEntity<byte[]> resp = restTemplate.exchange(
                    url, HttpMethod.GET, new HttpEntity<>(headers), byte[].class);

            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                log.debug("Fetched AI Engine file: inferenceId={}, filename={}, size={}B",
                        inferenceId, filename, resp.getBody().length);
                return resp.getBody();
            }

            log.warn("AI Engine file not found or empty: url={}, status={}", url, resp.getStatusCode());
            return null;

        } catch (Exception e) {
            log.warn("Could not fetch AI Engine file (non-fatal): url={}, error={}", url, e.getMessage());
            return null;
        }
    }
}
