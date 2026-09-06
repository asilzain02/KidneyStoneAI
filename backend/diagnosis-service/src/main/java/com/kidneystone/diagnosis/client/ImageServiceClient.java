package com.kidneystone.diagnosis.client;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.UUID;

/**
 * Purpose:
 *   HTTP client for communicating with the Image Service.
 *   This prevents Diagnosis Service from illegally reading image files
 *   direct from the filesystem, adhering to microservice boundaries.
 */
@Slf4j
@Component
public class ImageServiceClient {

    private final RestTemplate restTemplate;

    @Value("${image-service.base-url:http://localhost:8083}")
    private String imageServiceBaseUrl;

    public ImageServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @Data
    @AllArgsConstructor
    public static class DownloadedImage {
        private byte[] bytes;
        private String filename;
        private String contentType;
    }

    /**
     * Purpose:
     *   Retrieves the binary image resource from the Image Service.
     *   Extracts the content type and filename from the response headers.
     *
     * @param imageId UUID of the image
     * @param authHeader The Bearer JWT token from the original incoming request
     * @return DownloadedImage containing bytes and metadata
     */
    public DownloadedImage downloadImage(UUID imageId, String authHeader) {
        String url = imageServiceBaseUrl.stripTrailing() + "/api/v1/images/download/" + imageId;

        HttpHeaders headers = new HttpHeaders();
        // Purpose: Forward the authentication context to Image Service.
        if (authHeader != null) {
            headers.set(HttpHeaders.AUTHORIZATION, authHeader);
        }

        HttpEntity<?> entity = new HttpEntity<>(headers);

        log.info("Fetching image bytes from Image Service: url={}", url);

        try {
            ResponseEntity<byte[]> response = restTemplate.exchange(
                    url,
                    HttpMethod.GET,
                    entity,
                    byte[].class
            );

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new RuntimeException("Image Service returned unsuccessful status or empty body: " + response.getStatusCode());
            }

            // Extract content-type
            String contentType = response.getHeaders().getContentType() != null ? 
                    response.getHeaders().getContentType().toString() : "image/jpeg";

            // Extract filename from "attachment; filename=\"xyz.jpg\""
            String filename = "image.jpg"; // Default
            String disp = response.getHeaders().getFirst(HttpHeaders.CONTENT_DISPOSITION);
            if (disp != null && disp.contains("filename=\"")) {
                int start = disp.indexOf("filename=\"") + 10;
                int end = disp.lastIndexOf("\"");
                if (end > start) {
                    filename = disp.substring(start, end);
                }
            }

            return new DownloadedImage(response.getBody(), filename, contentType);

        } catch (RestClientException e) {
            log.error("Failed to download image from Image Service: url={}, error={}", url, e.getMessage());
            throw new RuntimeException("Failed to fetch image from Image Service: " + e.getMessage(), e);
        }
    }
}
