package com.kidneystone.auth.security;

import com.kidneystone.auth.entity.User;
import com.kidneystone.auth.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    @Override
    @Transactional(readOnly = true)
    public UserDetails loadUserByUsername(String emailOrUsername) throws UsernameNotFoundException {
        User user = userRepository.findByEmailAndIsDeletedFalse(emailOrUsername)
                .orElseGet(() -> userRepository.findByUsernameAndIsDeletedFalse(emailOrUsername)
                        .orElseThrow(() -> new UsernameNotFoundException("User not found with email or username: " + emailOrUsername)));

        return new CustomUserDetails(user);
    }
}
