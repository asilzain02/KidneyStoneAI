package com.kidneystone.image.dto;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
public class ImageResponse {

    private UUID id;
    private UUID patientId;
    private String fileName;
    private String originalFileName;
    private String storagePath;
    private Long fileSize;
    private String contentType;
    private String modality;
    private LocalDateTime uploadDate;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private UUID createdBy;
    private UUID updatedBy;
    private Integer version;
}
