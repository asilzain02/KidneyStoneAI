package com.kidneystone.patient.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;

@Slf4j
@Component
public class JwtProvider {

    @Value("${security.jwt.secret}")
    private String jwtSecret;

    private SecretKey key() {
        return Keys.hmacShaKeyFor(Decoders.BASE64.decode(jwtSecret));
    }

    public String getSubjectFromToken(String token) {
        return Jwts.parser().verifyWith(key()).build()
                .parseSignedClaims(token).getPayload().getSubject();
    }

    public String getClaimAsString(String token, String claim) {
        Object value = Jwts.parser().verifyWith(key()).build()
                .parseSignedClaims(token).getPayload().get(claim);
        return value != null ? value.toString() : null;
    }

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
