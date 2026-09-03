package com.kidneystone.diagnosis.exception;

/**
 * Purpose:
 *   Typed exception for all AI Engine communication failures.
 *   Separates AI Engine errors from general application errors so that
 *   the controller can return a semantically meaningful HTTP 502/503
 *   response rather than a generic 500.
 *
 *   Examples:
 *     - AI Engine unreachable (connection timeout)
 *     - AI Engine returns 5xx (inference failed)
 *     - AI Engine returns invalid/unparseable response
 *     - Read timeout during long inference
 */
public class AiEngineException extends RuntimeException {

    public AiEngineException(String message) {
        super(message);
    }

    public AiEngineException(String message, Throwable cause) {
        super(message, cause);
    }
}
