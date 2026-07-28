-- image.sql — Image Service Schema
CREATE SCHEMA IF NOT EXISTS image;

CREATE TABLE IF NOT EXISTS image.image_metadata (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID         NOT NULL,
    original_name   VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL UNIQUE,
    file_path       TEXT         NOT NULL,
    file_size       BIGINT       NOT NULL,
    content_type    VARCHAR(100) NOT NULL,
    uploaded_by     UUID         NOT NULL,
    is_valid        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMP
);
CREATE INDEX idx_image_patient ON image.image_metadata(patient_id);

CREATE TABLE IF NOT EXISTS image.image_audit (
    id          UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id    UUID      NOT NULL REFERENCES image.image_metadata(id),
    action      VARCHAR(50) NOT NULL,
    performed_by UUID     NOT NULL,
    performed_at TIMESTAMP NOT NULL DEFAULT NOW()
);
