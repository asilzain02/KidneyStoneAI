-- patient.sql — Patient Service Schema
CREATE SCHEMA IF NOT EXISTS patient;

CREATE TABLE IF NOT EXISTS patient.patients (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_code     VARCHAR(20)  NOT NULL UNIQUE,
    first_name       VARCHAR(100) NOT NULL,
    last_name        VARCHAR(100) NOT NULL,
    date_of_birth    DATE         NOT NULL,
    gender           VARCHAR(10)  NOT NULL,
    blood_group      VARCHAR(5),
    phone            VARCHAR(20),
    email            VARCHAR(255),
    address          TEXT,
    created_by       UUID         NOT NULL,  -- auth.users.id
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP    NOT NULL DEFAULT NOW(),
    deleted_at       TIMESTAMP
);
CREATE INDEX idx_patient_code    ON patient.patients(patient_code);
CREATE INDEX idx_patient_active  ON patient.patients(is_active) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS patient.clinical_histories (
    id              UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID      NOT NULL REFERENCES patient.patients(id),
    condition       VARCHAR(255),
    notes           TEXT,
    recorded_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patient.medical_records (
    id          UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID      NOT NULL REFERENCES patient.patients(id),
    record_type VARCHAR(50),
    content     JSONB,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patient.emergency_contacts (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id   UUID         NOT NULL REFERENCES patient.patients(id) ON DELETE CASCADE,
    name         VARCHAR(200) NOT NULL,
    relationship VARCHAR(50)  NOT NULL,
    phone        VARCHAR(20)  NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);
