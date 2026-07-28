-- diagnosis.sql — Diagnosis Service Schema
CREATE SCHEMA IF NOT EXISTS diagnosis;

CREATE TABLE IF NOT EXISTS diagnosis.predictions (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID         NOT NULL,
    image_id        UUID         NOT NULL,
    stone_detected  BOOLEAN      NOT NULL,
    stone_count     INTEGER,
    confidence      NUMERIC(5,4),
    ai_version      VARCHAR(50),
    status          VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_prediction_patient ON diagnosis.predictions(patient_id);
CREATE INDEX idx_prediction_status  ON diagnosis.predictions(status);

CREATE TABLE IF NOT EXISTS diagnosis.detections (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID         NOT NULL REFERENCES diagnosis.predictions(id) ON DELETE CASCADE,
    bbox_x        NUMERIC(8,2),
    bbox_y        NUMERIC(8,2),
    bbox_width    NUMERIC(8,2),
    bbox_height   NUMERIC(8,2),
    confidence    NUMERIC(5,4),
    stone_size_mm NUMERIC(6,2),
    location      VARCHAR(100),
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);
