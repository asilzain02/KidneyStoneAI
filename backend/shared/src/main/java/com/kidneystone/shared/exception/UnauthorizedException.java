package com.kidneystone.shared.exception;

public class UnauthorizedException extends ApplicationException {
    public UnauthorizedException(String message) {
        super(message, "UNAUTHORIZED");
    }
}
