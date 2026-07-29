package com.kidneystone.image.exception;

import com.kidneystone.shared.dto.ApiResponse;
import com.kidneystone.shared.exception.ApplicationException;
import com.kidneystone.shared.exception.NotFoundException;
import com.kidneystone.shared.exception.ValidationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.security.access.AccessDeniedException;

import java.util.stream.Collectors;

/**
 * Image-service specific exception handler.
 * Handles multipart and image-specific cases in addition to shared exceptions.
 */
@Slf4j
@RestControllerAdvice
public class ImageExceptionHandler {

        @ExceptionHandler(NotFoundException.class)
        public ResponseEntity<ApiResponse<Void>> handleNotFound(NotFoundException ex) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                                .body(ApiResponse.error(ex.getMessage(), "NOT_FOUND", null));
        }

        @ExceptionHandler(ValidationException.class)
        public ResponseEntity<ApiResponse<Void>> handleValidation(ValidationException ex) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                                .body(ApiResponse.error(ex.getMessage(), "VALIDATION_FAILED", null));
        }

        @ExceptionHandler(AccessDeniedException.class)
        public ResponseEntity<ApiResponse<Void>> handleAccessDenied(AccessDeniedException ex) {

                ApiResponse<Void> response = ApiResponse.error(
                                "Access Denied",
                                "FORBIDDEN",
                                ex.getMessage());

                return ResponseEntity
                                .status(HttpStatus.FORBIDDEN)
                                .body(response);
        }

        @ExceptionHandler(ApplicationException.class)
        public ResponseEntity<ApiResponse<Void>> handleApplication(ApplicationException ex) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                                .body(ApiResponse.error(ex.getMessage(), ex.getErrorCode(), null));
        }

        @ExceptionHandler(MaxUploadSizeExceededException.class)
        public ResponseEntity<ApiResponse<Void>> handleMaxSize(MaxUploadSizeExceededException ex) {
                return ResponseEntity.status(HttpStatus.PAYLOAD_TOO_LARGE)
                                .body(ApiResponse.error("File exceeds maximum upload size of 50 MB",
                                                "FILE_TOO_LARGE", ex.getMessage()));
        }

        @ExceptionHandler(MethodArgumentNotValidException.class)
        public ResponseEntity<ApiResponse<Void>> handleMethodArgumentNotValid(MethodArgumentNotValidException ex) {
                String details = ex.getBindingResult().getAllErrors().stream()
                                .map(e -> ((FieldError) e).getField() + ": " + e.getDefaultMessage())
                                .collect(Collectors.joining(", "));
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                                .body(ApiResponse.error("Validation Failed", "VALIDATION_ERROR", details));
        }

        @ExceptionHandler(Exception.class)
        public ResponseEntity<ApiResponse<Void>> handleGeneric(Exception ex) {
                log.error("Unhandled exception in image-service", ex);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                                .body(ApiResponse.error("Internal Server Error", "INTERNAL_ERROR", ex.getMessage()));
        }
}
