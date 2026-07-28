package com.kidneystone.auth.service;

import com.kidneystone.auth.dto.AuthResponse;
import com.kidneystone.auth.dto.LoginRequest;
import com.kidneystone.auth.dto.UserResponse;
import com.kidneystone.auth.entity.RefreshToken;
import com.kidneystone.auth.entity.Role;
import com.kidneystone.auth.entity.User;
import com.kidneystone.auth.mapper.UserMapper;
import com.kidneystone.auth.repository.RefreshTokenRepository;
import com.kidneystone.auth.repository.RoleRepository;
import com.kidneystone.auth.repository.UserRepository;
import com.kidneystone.auth.security.CustomUserDetails;
import com.kidneystone.auth.security.JwtProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserRepository userRepository;
    @Mock
    private RoleRepository roleRepository;
    @Mock
    private RefreshTokenRepository refreshTokenRepository;
    @Mock
    private PasswordEncoder passwordEncoder;
    @Mock
    private AuthenticationManager authenticationManager;
    @Mock
    private JwtProvider jwtProvider;
    @Mock
    private UserMapper userMapper;
    @Mock
    private Authentication authentication;

    @InjectMocks
    private AuthService authService;

    private User mockUser;
    private Role mockRole;

    @BeforeEach
    void setUp() {
        mockRole = new Role();
        mockRole.setName("DOCTOR");

        mockUser = new User();
        mockUser.setId(UUID.randomUUID());
        mockUser.setEmail("doctor@test.com");
        mockUser.setPasswordHash("hashedpassword");
        mockUser.setRole(mockRole);
        mockUser.setStatus("ACTIVE");
    }

    @Test
    void testLoginSuccess() {
        LoginRequest req = new LoginRequest();
        req.setEmail("doctor@test.com");
        req.setPassword("password");

        CustomUserDetails cud = new CustomUserDetails(mockUser);
        
        when(authenticationManager.authenticate(any(UsernamePasswordAuthenticationToken.class))).thenReturn(authentication);
        when(authentication.getPrincipal()).thenReturn(cud);
        when(userRepository.findById(cud.getId())).thenReturn(Optional.of(mockUser));
        when(jwtProvider.generateToken(authentication)).thenReturn("mock-jwt-token");
        when(userMapper.toDto(any(User.class))).thenReturn(new UserResponse());

        RefreshToken refreshToken = new RefreshToken();
        refreshToken.setToken("mock-refresh-token");
        when(refreshTokenRepository.save(any())).thenReturn(refreshToken);

        AuthResponse res = authService.login(req);

        assertNotNull(res);
        assertNotNull(res.getAccessToken());
        verify(userRepository, times(1)).save(any(User.class));
        verify(refreshTokenRepository, times(1)).save(any());
    }
}
