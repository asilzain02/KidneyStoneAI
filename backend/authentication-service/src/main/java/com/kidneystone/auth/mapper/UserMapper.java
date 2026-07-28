package com.kidneystone.auth.mapper;

import com.kidneystone.auth.dto.UserResponse;
import com.kidneystone.auth.entity.Permission;
import com.kidneystone.auth.entity.User;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;

import java.util.Collections;
import java.util.Set;
import java.util.stream.Collectors;

@Mapper(componentModel = "spring")
public interface UserMapper {

    @Mapping(target = "role", source = "role.name")
    @Mapping(target = "permissions", source = "role.permissions", qualifiedByName = "mapPermissions")
    UserResponse toDto(User user);

    @Named("mapPermissions")
    default Set<String> mapPermissions(Set<Permission> permissions) {
        if (permissions == null) {
            return Collections.emptySet();
        }
        return permissions.stream()
                .map(Permission::getCode)
                .collect(Collectors.toSet());
    }
}
