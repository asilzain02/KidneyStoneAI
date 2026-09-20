package com.kidneystone.report.client;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Map;
import java.util.List;

@Slf4j
@Component
public class DiagnosisServiceClient {

    private final RestTemplate restTemplate;

    @Value("${diagnosis-service.base-url:http://localhost:8084}")
    private String baseUrl;

    public DiagnosisServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public List<Map<String, Object>> getCompletedDiagnoses(String authHeader) {
        String url = baseUrl.stripTrailing() + "/api/v1/diagnoses?size=1000";
        
        HttpHeaders headers = new HttpHeaders();
        if (authHeader != null) {
            headers.set(HttpHeaders.AUTHORIZATION, authHeader);
        }
        
        HttpEntity<?> entity = new HttpEntity<>(headers);

        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                    url, HttpMethod.GET, entity, Map.class);
            
            Map<String, Object> body = response.getBody();
            if (body != null) {
                // Handle ApiResponse wrapper: { status: "SUCCESS", data: { content: [...] } }
                Object dataObj = body.get("data");
                if (dataObj instanceof Map) {
                    Map<String, Object> dataMap = (Map<String, Object>) dataObj;
                    if (dataMap.containsKey("content")) {
                        List<Map<String, Object>> diagnoses = (List<Map<String, Object>>) dataMap.get("content");
                        return diagnoses.stream()
                                .filter(d -> "COMPLETED".equals(d.get("status")))
                                .toList();
                    }
                }
                // Fallback: direct content at root level
                if (body.containsKey("content")) {
                    List<Map<String, Object>> diagnoses = (List<Map<String, Object>>) body.get("content");
                    return diagnoses.stream()
                            .filter(d -> "COMPLETED".equals(d.get("status")))
                            .toList();
                }
            }
            return List.of();
        } catch (Exception e) {
            log.error("Failed to fetch from Diagnosis Service: {}", e.getMessage());
            throw new RuntimeException("Diagnosis Service unavailable or failed", e);
        }
    }

    public Map<String, Object> getDiagnosisById(String diagnosisId, String authHeader) {
        String url = baseUrl.stripTrailing() + "/api/v1/diagnoses/" + diagnosisId;
        HttpHeaders headers = new HttpHeaders();
        if (authHeader != null) {
            headers.set(HttpHeaders.AUTHORIZATION, authHeader);
        }
        HttpEntity<?> entity = new HttpEntity<>(headers);

        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                    url, HttpMethod.GET, entity, Map.class);
            return response.getBody();
        } catch (Exception e) {
            log.error("Failed to fetch diagnosis {} from Diagnosis Service: {}", diagnosisId, e.getMessage());
            throw new RuntimeException("Failed to fetch diagnosis details", e);
        }
    }
}
