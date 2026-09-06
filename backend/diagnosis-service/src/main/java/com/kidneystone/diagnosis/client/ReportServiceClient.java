package com.kidneystone.diagnosis.client;

import com.kidneystone.diagnosis.dto.external.ReportRequest;
import com.kidneystone.diagnosis.dto.external.ReportResponse;
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
public class ReportServiceClient {

    private final RestTemplate restTemplate;

    @Value("${report-service.base-url:http://localhost:8087}")
    private String baseUrl;

    public ReportServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public ReportResponse generateReport(ReportRequest request, String authHeader) {
        String url = baseUrl.stripTrailing() + "/api/v1/reports/generate";
        
        HttpHeaders headers = new HttpHeaders();
        if (authHeader != null) {
            headers.set(HttpHeaders.AUTHORIZATION, authHeader);
        }
        
        HttpEntity<ReportRequest> entity = new HttpEntity<>(request, headers);

        try {
            ResponseEntity<ReportResponse> response = restTemplate.exchange(
                    url, HttpMethod.POST, entity, ReportResponse.class);
            return response.getBody();
        } catch (Exception e) {
            log.error("Failed to call Report Service: {}", e.getMessage());
            throw new RuntimeException("Report Service unavailable or failed", e);
        }
    }
}
