package com.kidneystone.auth.controller;

import com.kidneystone.auth.dto.UserResponse;
import com.kidneystone.auth.service.UserService;
import com.kidneystone.shared.dto.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/auth/users")
@RequiredArgsConstructor
@Tag(name = "User Management", description = "Admin User Management APIs")
public class UserController {

    private final UserService userService;

    @GetMapping
    @Operation(summary = "List all users")
    @PreAuthorize("hasAuthority('USER_READ') or hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<List<UserResponse>>> getAllUsers() {
        return ResponseEntity.ok(ApiResponse.success(userService.getAllUsers(), "Users retrieved"));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get user by ID")
    @PreAuthorize("hasAuthority('USER_READ') or hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<UserResponse>> getUserById(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(userService.getUserById(id), "User retrieved"));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Soft delete user")
    @PreAuthorize("hasAuthority('USER_DELETE') or hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<Void>> deleteUser(@PathVariable UUID id) {
        userService.deleteUser(id);
        return ResponseEntity.ok(ApiResponse.success(null, "User deleted successfully"));
    }
}
