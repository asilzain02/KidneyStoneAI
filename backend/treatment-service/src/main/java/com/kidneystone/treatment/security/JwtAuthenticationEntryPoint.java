// package com.kidneystone.treatment.security;

// import com.fasterxml.jackson.databind.ObjectMapper;
// import com.kidneystone.shared.dto.ApiResponse;
// import jakarta.servlet.ServletException;
// import jakarta.servlet.http.HttpServletRequest;
// import jakarta.servlet.http.HttpServletResponse;
// import lombok.extern.slf4j.Slf4j;
// import org.springframework.http.HttpStatus;
// import org.springframework.http.MediaType;
// import org.springframework.security.core.AuthenticationException;
// import org.springframework.security.web.AuthenticationEntryPoint;
// import org.springframework.stereotype.Component;

// import java.io.IOException;

// @Slf4j
// @Component
// public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {

//     @Override
//     public void commence(HttpServletRequest request, HttpServletResponse response,
//                          AuthenticationException authException) throws IOException, ServletException {
//         log.error("Unauthorized error: {}", authException.getMessage());

//         response.setContentType(MediaType.APPLICATION_JSON_VALUE);
//         response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);

//         ApiResponse<Void> apiResponse = ApiResponse.error("Unauthorized: " + authException.getMessage(),
//                 HttpStatus.UNAUTHORIZED.value());

//         ObjectMapper mapper = new ObjectMapper();
//         mapper.writeValue(response.getOutputStream(), apiResponse);
//     }
// }

package com.kidneystone.treatment.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.kidneystone.shared.dto.ApiResponse;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import java.io.IOException;

/**
 * Handles authentication failures for protected Diagnosis Service endpoints.
 *
 * PURPOSE:
 * When a request reaches a protected endpoint without valid authentication,
 * Spring Security invokes this class. It returns a standardized JSON error
 * response instead of Spring's default error page.
 */
@Slf4j
@Component
public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {

    /**
     * Handles an unauthenticated request.
     *
     * @param request       the incoming HTTP request
     * @param response      the HTTP response
     * @param authException the authentication failure exception
     * @throws IOException      if the JSON response cannot be written
     * @throws ServletException if servlet processing fails
     */
    @Override
    public void commence(
            HttpServletRequest request,
            HttpServletResponse response,
            AuthenticationException authException) throws IOException, ServletException {

        // Log the authentication failure for debugging and server-side monitoring.
        log.error("Unauthorized error: {}", authException.getMessage());

        // Tell the client that the response body contains JSON.
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);

        // Return HTTP 401 Unauthorized.
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);

        /*
         * Build the standard shared API error response.
         *
         * ApiResponse.error() expects:
         * 1. message
         * 2. String error code
         * 3. error details
         *
         * The HTTP status is already set separately above, so we should not
         * pass HttpStatus.UNAUTHORIZED.value() as the second argument.
         */
        ApiResponse<Void> apiResponse = ApiResponse.error(
                "Unauthorized: " + authException.getMessage(),
                "UNAUTHORIZED",
                "Authentication is required to access this resource.");

        // Convert the ApiResponse object into JSON and send it to the client.
        ObjectMapper mapper = new ObjectMapper();
        mapper.writeValue(response.getOutputStream(), apiResponse);
    }
}
