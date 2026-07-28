package com.kidneystone.shared.exception;

public class ValidationException extends ApplicationException {
    public ValidationException(String message) {
        super(message, "VALIDATION_FAILED");
    }
}
