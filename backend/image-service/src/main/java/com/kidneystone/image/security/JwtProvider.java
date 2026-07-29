package com.kidneystone.image.security;

import com.kidneystone.shared.security.BaseJwtProvider;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;

@Slf4j
@Component
public class JwtProvider extends BaseJwtProvider {

    @Value("${security.jwt.secret}")
    private String jwtSecret;

    @Override
    protected SecretKey key() {
        return Keys.hmacShaKeyFor(Decoders.BASE64.decode(jwtSecret));
    }
}
