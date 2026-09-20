package com.kidneystone.image.dto;

import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class ImageUploadRequest {

    @Size(max = 50, message = "Modality must be at most 50 characters")
    private String modality;

    @Size(max = 255, message = "File name must be at most 255 characters")
    private String fileName;
}
