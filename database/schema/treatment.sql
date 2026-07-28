-- treatment.sql — Treatment Service Schema
CREATE SCHEMA IF NOT EXISTS treatment;

CREATE TABLE IF NOT EXISTS treatment.recommendations (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id   UUID         NOT NULL UNIQUE,
    severity_id     UUID         NOT NULL,
    recommendation  VARCHAR(50)  NOT NULL,  -- HYDRATION, ESWL, URS, PCNL, MEDICATION
    description     TEXT,
    urgency         VARCHAR(20),
    doctor_override BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS treatment.treatment_history (
    id                 UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id         UUID      NOT NULL,
    recommendation_id  UUID      NOT NULL REFERENCES treatment.recommendations(id),
    recorded_at        TIMESTAMP NOT NULL DEFAULT NOW()
);
