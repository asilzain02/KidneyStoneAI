package com.kidneystone.image.mapper;

import com.kidneystone.image.dto.ImageResponse;
import com.kidneystone.image.entity.MedicalImage;
import org.mapstruct.Mapper;
import org.mapstruct.NullValuePropertyMappingStrategy;

@Mapper(componentModel = "spring", nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
public interface ImageMapper {

    ImageResponse toDto(MedicalImage image);
}
