package com.kidneystone.auth.security;

import com.kidneystone.auth.entity.User;
import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

@Getter
public class CustomUserDetails implements UserDetails {

    private final UUID id;
    private final String username;
    private final String email;
    private final String password;
    private final Collection<? extends GrantedAuthority> authorities;
    private final boolean isVerified;
    private final String status;

    public CustomUserDetails(User user) {
        this.id = user.getId();
        this.username = user.getUsername();
        this.email = user.getEmail();
        this.password = user.getPasswordHash();
        this.isVerified = user.isVerified();
        this.status = user.getStatus();
        
        Set<GrantedAuthority> auths = new HashSet<>();
        if (user.getRole() != null) {
            auths.add(new SimpleGrantedAuthority("ROLE_" + user.getRole().getName()));
            if (user.getRole().getPermissions() != null) {
                auths.addAll(user.getRole().getPermissions().stream()
                        .map(p -> new SimpleGrantedAuthority(p.getCode()))
                        .collect(Collectors.toSet()));
            }
        }
        this.authorities = auths;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return "ACTIVE".equalsIgnoreCase(this.status);
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return "ACTIVE".equalsIgnoreCase(this.status);
    }
}
