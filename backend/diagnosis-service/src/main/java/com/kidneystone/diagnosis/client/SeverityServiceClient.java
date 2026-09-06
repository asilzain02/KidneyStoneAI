package com.kidneystone.diagnosis.client;

import com.kidneystone.diagnosis.dto.external.SeverityRequest;
import com.kidneystone.diagnosis.dto.external.SeverityResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Slf4j
@Component
public class SeverityServiceClient {

    private final RestTemplate restTemplate;

    @Value("${severity-service.base-url:http://localhost:8085}")
    private String baseUrl;

    public SeverityServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public SeverityResponse assessSeverity(SeverityRequest request, String authHeader) {
        String url = baseUrl.stripTrailing() + "/api/v1/severity/assess";
        
        HttpHeaders headers = new HttpHeaders();
        if (authHeader != null) {
            headers.set(HttpHeaders.AUTHORIZATION, authHeader);
        }
        
        HttpEntity<SeverityRequest> entity = new HttpEntity<>(request, headers);

        try {
            ResponseEntity<SeverityResponse> response = restTemplate.exchange(
                    url, HttpMethod.POST, entity, SeverityResponse.class);
            return response.getBody();
        } catch (Exception e) {
            log.error("Failed to call Severity Service: {}", e.getMessage());
            throw new RuntimeException("Severity Service unavailable or failed", e);
        }
    }
}
