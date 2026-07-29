-- V1__init_image_schema.sql
-- Image Service - Flyway Migration
-- Timezone: UTC

CREATE SCHEMA IF NOT EXISTS image;

-- MEDICAL IMAGES table (metadata only – no binary data)
CREATE TABLE IF NOT EXISTS image.medical_images (
    id                 UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id         UUID          NOT NULL,
    file_name          VARCHAR(255)  NOT NULL,
    original_file_name VARCHAR(255)  NOT NULL,
    storage_path       VARCHAR(1024) NOT NULL,
    file_size          BIGINT        NOT NULL,
    content_type       VARCHAR(100)  NOT NULL,
    modality           VARCHAR(50)   NOT NULL DEFAULT 'UNKNOWN',
    upload_date        TIMESTAMP     NOT NULL DEFAULT NOW(),
    status             VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE',
    created_at         TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by         UUID,
    updated_by         UUID,
    is_deleted         BOOLEAN       NOT NULL DEFAULT FALSE,
    version            INTEGER       NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_image_patient_id ON image.medical_images(patient_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_image_status     ON image.medical_images(status)     WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_image_active     ON image.medical_images(is_deleted);
