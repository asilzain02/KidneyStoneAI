package com.kidneystone.shared.dto;

import lombok.Builder;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Builder
public class ApiResponse<T> {
    private String status;
    private String message;
    private LocalDateTime timestamp;
    private T data;
    private ApiError error;

    @Data
    @Builder
    public static class ApiError {
        private String code;
        private String details;
    }

    public static <T> ApiResponse<T> success(T data, String message) {
        return ApiResponse.<T>builder()
                .status("SUCCESS")
                .message(message)
                .timestamp(LocalDateTime.now())
                .data(data)
                .build();
    }

    public static <T> ApiResponse<T> error(String message, String code, String details) {
        return ApiResponse.<T>builder()
                .status("ERROR")
                .message(message)
                .timestamp(LocalDateTime.now())
                .error(ApiError.builder().code(code).details(details).build())
                .build();
    }
}
