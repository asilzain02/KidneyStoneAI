-- V1__init_patient_schema.sql
-- Patient Service - Flyway Migration
-- Timezone: UTC

CREATE SCHEMA IF NOT EXISTS patient;

-- PATIENTS table (core demographic record)
CREATE TABLE IF NOT EXISTS patient.patients (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_code    VARCHAR(20)  NOT NULL UNIQUE,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    date_of_birth   DATE         NOT NULL,
    gender          VARCHAR(10)  NOT NULL,
    blood_group     VARCHAR(5),
    phone           VARCHAR(20),
    email           VARCHAR(255),
    address         TEXT,
    registered_by   UUID         NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_by      UUID,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE,
    version         INTEGER      NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_patient_code     ON patient.patients(patient_code);
CREATE INDEX        IF NOT EXISTS idx_patient_email    ON patient.patients(email)    WHERE is_deleted = FALSE;
CREATE INDEX        IF NOT EXISTS idx_patient_active   ON patient.patients(is_deleted);

-- EMERGENCY CONTACTS
CREATE TABLE IF NOT EXISTS patient.emergency_contacts (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID         NOT NULL REFERENCES patient.patients(id) ON DELETE CASCADE,
    name            VARCHAR(200) NOT NULL,
    relationship    VARCHAR(50)  NOT NULL,
    phone           VARCHAR(20)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE,
    version         INTEGER      NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_ec_patient ON patient.emergency_contacts(patient_id);
