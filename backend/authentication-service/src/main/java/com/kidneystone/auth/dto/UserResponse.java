package com.kidneystone.auth.dto;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.UUID;
import java.util.Set;

@Data
public class UserResponse {
    private UUID id;
    private String email;
    private String username;
    private String firstName;
    private String lastName;
    private String phone;
    private String role;
    private Set<String> permissions;
    private String status;
    private LocalDateTime lastLogin;
    private boolean isVerified;
    private LocalDateTime createdAt;
}
