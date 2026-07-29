package com.kidneystone.image.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtProvider jwtProvider;

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path.startsWith("/v3/api-docs") ||
                path.startsWith("/swagger-ui") ||
                path.startsWith("/actuator/health") ||
                path.equals("/error");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        try {
            String jwt = parseJwt(request);
            if (jwt != null && jwtProvider.validateToken(jwt)) {
                String subject = jwtProvider.getSubjectFromToken(jwt);
                java.util.UUID userId = jwtProvider.getUserId(jwt);
                List<String> roleStrings = jwtProvider.getAuthorities(jwt);

                // DEBUG LOGS
                log.info("======================================");
                log.info("JWT Subject      : {}", subject);
                log.info("JWT UserId       : {}", userId);
                log.info("JWT Authorities  : {}", roleStrings);
                log.info("======================================");

                String principalName = (userId != null) ? userId.toString() : subject;

                List<SimpleGrantedAuthority> authorities = roleStrings.stream()
                        .map(SimpleGrantedAuthority::new)
                        .toList();

                UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                        principalName, null, authorities);
                SecurityContextHolder.getContext().setAuthentication(authentication);

                // DEBUG LOGS
                log.info("Spring Authentication: {}",
                        SecurityContextHolder.getContext().getAuthentication());

                log.info("Spring Authorities: {}",
                        SecurityContextHolder.getContext()
                                .getAuthentication()
                                .getAuthorities());

                log.info("======================================");
            }
        } catch (Exception e) {
            log.error("Cannot set user authentication: {}", e.getMessage());
        }

        filterChain.doFilter(request, response);
    }

    private String parseJwt(HttpServletRequest request) {
        String headerAuth = request.getHeader("Authorization");
        if (StringUtils.hasText(headerAuth) && headerAuth.startsWith("Bearer ")) {
            return headerAuth.substring(7);
        }
        return null;
    }
}
