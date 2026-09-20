package com.kidneystone.auth.service;

import com.kidneystone.auth.dto.UserResponse;
import com.kidneystone.auth.entity.User;
import com.kidneystone.auth.mapper.UserMapper;
import com.kidneystone.auth.repository.UserRepository;
import com.kidneystone.shared.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final UserMapper userMapper;
    private final com.kidneystone.auth.repository.RoleRepository roleRepository;
    private final org.springframework.security.crypto.password.PasswordEncoder passwordEncoder;

    @Transactional(readOnly = true)
    public UserResponse getProfile(String emailOrUsername) {
        User user = userRepository.findByEmailAndIsDeletedFalse(emailOrUsername)
                .orElseGet(() -> userRepository.findByUsernameAndIsDeletedFalse(emailOrUsername)
                        .orElseThrow(() -> new NotFoundException("User not found")));
        return userMapper.toDto(user);
    }

    @Transactional(readOnly = true)
    public List<UserResponse> getAllUsers() {
        return userRepository.findAll().stream()
                .filter(u -> !u.isDeleted())
                .map(userMapper::toDto)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public UserResponse getUserById(UUID id) {
        User user = userRepository.findById(id)
                .filter(u -> !u.isDeleted())
                .orElseThrow(() -> new NotFoundException("User not found"));
        return userMapper.toDto(user);
    }

    @Transactional
    public UserResponse createUser(com.kidneystone.auth.dto.RegisterRequest request) {
        if (userRepository.existsByEmailAndIsDeletedFalse(request.getEmail())) {
            throw new com.kidneystone.shared.exception.ValidationException("Email is already registered");
        }
        if (userRepository.existsByUsernameAndIsDeletedFalse(request.getUsername())) {
             throw new com.kidneystone.shared.exception.ValidationException("Username is already taken");
        }

        com.kidneystone.auth.entity.Role role = roleRepository.findByNameAndIsDeletedFalse(request.getRole().toUpperCase())
                .orElseThrow(() -> new com.kidneystone.shared.exception.ValidationException("Invalid role specified"));

        User user = new User();
        user.setEmail(request.getEmail());
        user.setUsername(request.getUsername());
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setFirstName(request.getFirstName());
        user.setLastName(request.getLastName());
        user.setPhone(request.getPhone());
        user.setRole(role);
        user.setVerified(true);
        user.setStatus("ACTIVE");

        return userMapper.toDto(userRepository.save(user));
    }

    @Transactional
    public void deleteUser(UUID id) {
        User user = userRepository.findById(id)
                .filter(u -> !u.isDeleted())
                .orElseThrow(() -> new NotFoundException("User not found"));
        user.setDeleted(true);
        user.setStatus("INACTIVE");
        userRepository.save(user);
    }
}
