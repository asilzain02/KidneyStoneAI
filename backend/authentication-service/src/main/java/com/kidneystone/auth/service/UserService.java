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

    @Transactional(readOnly = true)
    public UserResponse getProfile(String email) {
        User user = userRepository.findByEmailAndIsDeletedFalse(email)
                .orElseThrow(() -> new NotFoundException("User not found"));
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
    public void deleteUser(UUID id) {
        User user = userRepository.findById(id)
                .filter(u -> !u.isDeleted())
                .orElseThrow(() -> new NotFoundException("User not found"));
        user.setDeleted(true);
        user.setStatus("INACTIVE");
        userRepository.save(user);
    }
}
