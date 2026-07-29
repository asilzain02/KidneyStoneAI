package com.kidneystone.shared.security;

import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.UnsupportedJwtException;
import lombok.extern.slf4j.Slf4j;

import javax.crypto.SecretKey;
import java.util.List;
import java.util.UUID;

/**
 * Abstract base class providing common JWT parsing and validation logic
 * strictly conforming to the project's JWT architectural standards.
 * All microservices that consume or emit JWTs should extend this class.
 */
@Slf4j
public abstract class BaseJwtProvider {

    /**
     * Implementing classes must provide the SecretKey, typically parsed from application configuration.
     * @return the HMAC SHA SecretKey used to sign and verify tokens.
     */
    protected abstract SecretKey key();

    /**
     * Extracts the primary Subject (e.g., email address) from the token.
     */
    public String getSubjectFromToken(String token) {
        return Jwts.parser().verifyWith(key()).build()
                .parseSignedClaims(token).getPayload().getSubject();
    }

    /**
     * Extracts the specific "userId" UUID claim from the token.
     */
    public UUID getUserId(String token) {
        Object userIdStr = Jwts.parser().verifyWith(key()).build()
                .parseSignedClaims(token).getPayload().get("userId");
        if (userIdStr != null) {
            return UUID.fromString(userIdStr.toString());
        }
        return null;
    }

    /**
     * Extracts the generic "authorities" claim from the token as a List of Strings.
     */
    @SuppressWarnings("unchecked")
    public List<String> getAuthorities(String token) {
        Object authoritiesObj = Jwts.parser().verifyWith(key()).build()
                .parseSignedClaims(token).getPayload().get("authorities");
        
        if (authoritiesObj instanceof List<?>) {
            return (List<String>) authoritiesObj;
        }
        return List.of();
    }

    /**
     * Helper to gracefully handle token validation logs and verify cryptographic soundness.
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parser().verifyWith(key()).build().parseSignedClaims(token);
            return true;
        } catch (MalformedJwtException e) {
            log.error("Invalid JWT: {}", e.getMessage());
        } catch (ExpiredJwtException e) {
            log.error("Expired JWT: {}", e.getMessage());
        } catch (UnsupportedJwtException e) {
            log.error("Unsupported JWT: {}", e.getMessage());
        } catch (IllegalArgumentException e) {
            log.error("Empty JWT claims: {}", e.getMessage());
        }
        return false;
    }
}
