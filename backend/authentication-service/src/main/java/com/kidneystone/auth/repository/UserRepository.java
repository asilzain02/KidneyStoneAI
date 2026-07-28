package com.kidneystone.auth.repository;

import com.kidneystone.auth.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {
    Optional<User> findByEmailAndIsDeletedFalse(String email);
    Optional<User> findByUsernameAndIsDeletedFalse(String username);
    boolean existsByEmailAndIsDeletedFalse(String email);
    boolean existsByUsernameAndIsDeletedFalse(String username);
}
