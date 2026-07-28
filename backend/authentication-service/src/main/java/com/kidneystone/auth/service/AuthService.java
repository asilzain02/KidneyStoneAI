package com.kidneystone.auth.service;

import com.kidneystone.auth.dto.*;
import com.kidneystone.auth.entity.RefreshToken;
import com.kidneystone.auth.entity.Role;
import com.kidneystone.auth.entity.User;
import com.kidneystone.auth.mapper.UserMapper;
import com.kidneystone.auth.repository.RefreshTokenRepository;
import com.kidneystone.auth.repository.RoleRepository;
import com.kidneystone.auth.repository.UserRepository;
import com.kidneystone.auth.security.CustomUserDetails;
import com.kidneystone.auth.security.JwtProvider;
import com.kidneystone.shared.exception.NotFoundException;
import com.kidneystone.shared.exception.UnauthorizedException;
import com.kidneystone.shared.exception.ValidationException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final JwtProvider jwtProvider;
    private final UserMapper userMapper;

    @Transactional
    public AuthResponse login(LoginRequest request) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword()));

        SecurityContextHolder.getContext().setAuthentication(authentication);
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        
        User user = userRepository.findById(userDetails.getId())
                .orElseThrow(() -> new NotFoundException("User not found"));
        
        user.setLastLogin(LocalDateTime.now());
        userRepository.save(user);

        String jwt = jwtProvider.generateToken(authentication);
        RefreshToken refreshToken = createRefreshToken(user);

        return AuthResponse.builder()
                .accessToken(jwt)
                .refreshToken(refreshToken.getToken())
                .tokenType("Bearer")
                .user(userMapper.toDto(user))
                .build();
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmailAndIsDeletedFalse(request.getEmail())) {
            throw new ValidationException("Email is already registered");
        }
        if (userRepository.existsByUsernameAndIsDeletedFalse(request.getUsername())) {
            throw new ValidationException("Username is already taken");
        }

        Role role = roleRepository.findByNameAndIsDeletedFalse(request.getRole().toUpperCase())
                .orElseThrow(() -> new ValidationException("Invalid role specified"));

        User user = new User();
        user.setEmail(request.getEmail());
        user.setUsername(request.getUsername());
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setFirstName(request.getFirstName());
        user.setLastName(request.getLastName());
        user.setPhone(request.getPhone());
        user.setRole(role);
        user.setVerified(false);
        user.setStatus("ACTIVE");

        user = userRepository.save(user);

        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword()));

        String jwt = jwtProvider.generateToken(authentication);
        RefreshToken refreshToken = createRefreshToken(user);

        return AuthResponse.builder()
                .accessToken(jwt)
                .refreshToken(refreshToken.getToken())
                .tokenType("Bearer")
                .user(userMapper.toDto(user))
                .build();
    }

    @Transactional
    public void logout(String userEmail) {
        User user = userRepository.findByEmailAndIsDeletedFalse(userEmail)
                .orElseThrow(() -> new NotFoundException("User not found"));
        refreshTokenRepository.revokeAllUserTokens(user);
    }

    @Transactional
    public AuthResponse refreshToken(TokenRefreshRequest request) {
        RefreshToken refreshToken = refreshTokenRepository.findByToken(request.getRefreshToken())
                .orElseThrow(() -> new UnauthorizedException("Refresh token not found"));

        if (refreshToken.isRevoked() || refreshToken.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw new UnauthorizedException("Refresh token expired or revoked");
        }

        User user = refreshToken.getUser();
        String jwt = jwtProvider.generateTokenFromEmail(user.getEmail(), user.getId().toString());
        
        // Rotate refresh token
        refreshToken.setRevoked(true);
        refreshTokenRepository.save(refreshToken);
        RefreshToken newRefreshToken = createRefreshToken(user);

        return AuthResponse.builder()
                .accessToken(jwt)
                .refreshToken(newRefreshToken.getToken())
                .tokenType("Bearer")
                .user(userMapper.toDto(user))
                .build();
    }

    @Transactional
    public void changePassword(String email, ChangePasswordRequest request) {
        User user = userRepository.findByEmailAndIsDeletedFalse(email)
                .orElseThrow(() -> new NotFoundException("User not found"));

        if (!passwordEncoder.matches(request.getOldPassword(), user.getPasswordHash())) {
            throw new ValidationException("Incorrect old password");
        }

        user.setPasswordHash(passwordEncoder.encode(request.getNewPassword()));
        userRepository.save(user);
    }

    @Transactional
    public void forgotPassword(ForgotPasswordRequest request) {
        // Typically generate a reset token and email it. For this implementation we'll mock successfully.
        if (!userRepository.existsByEmailAndIsDeletedFalse(request.getEmail())) {
            throw new NotFoundException("User not found with provided email");
        }
    }

    @Transactional
    public void resetPassword(ResetPasswordRequest request) {
        // Implement token verification here.
        throw new UnsupportedOperationException("Reset password requires email infrastructure");
    }

    private RefreshToken createRefreshToken(User user) {
        RefreshToken refreshToken = new RefreshToken();
        refreshToken.setUser(user);
        refreshToken.setToken(UUID.randomUUID().toString());
        refreshToken.setExpiresAt(LocalDateTime.now().plusDays(7));
        return refreshTokenRepository.save(refreshToken);
    }
}
