-- severity.sql — Severity Service Schema
CREATE SCHEMA IF NOT EXISTS severity;

CREATE TYPE severity.severity_level AS ENUM ('LOW', 'MODERATE', 'HIGH', 'CRITICAL');

CREATE TABLE IF NOT EXISTS severity.severities (
    id              UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id   UUID                    NOT NULL UNIQUE,
    severity_level  severity.severity_level NOT NULL,
    confidence      NUMERIC(5,4),
    features        JSONB,
    created_at      TIMESTAMP               NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS severity.severity_histories (
    id              UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID      NOT NULL,
    severity_id     UUID      NOT NULL REFERENCES severity.severities(id),
    recorded_at     TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_severity_history_patient ON severity.severity_histories(patient_id);
