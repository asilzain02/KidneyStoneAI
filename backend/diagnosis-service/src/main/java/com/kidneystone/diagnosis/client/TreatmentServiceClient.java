package com.kidneystone.diagnosis.client;

import com.kidneystone.diagnosis.dto.external.TreatmentRequest;
import com.kidneystone.diagnosis.dto.external.TreatmentResponse;
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
public class TreatmentServiceClient {

    private final RestTemplate restTemplate;

    @Value("${treatment-service.base-url:http://localhost:8086}")
    private String baseUrl;

    public TreatmentServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public TreatmentResponse recommendTreatment(TreatmentRequest request, String authHeader) {
        String url = baseUrl.stripTrailing() + "/api/v1/treatment/recommend";
        
        HttpHeaders headers = new HttpHeaders();
        if (authHeader != null) {
            headers.set(HttpHeaders.AUTHORIZATION, authHeader);
        }
        
        HttpEntity<TreatmentRequest> entity = new HttpEntity<>(request, headers);

        try {
            ResponseEntity<TreatmentResponse> response = restTemplate.exchange(
                    url, HttpMethod.POST, entity, TreatmentResponse.class);
            return response.getBody();
        } catch (Exception e) {
            log.error("Failed to call Treatment Service: {}", e.getMessage());
            throw new RuntimeException("Treatment Service unavailable or failed", e);
        }
    }
}
