-- report.sql — Report Service Schema
CREATE SCHEMA IF NOT EXISTS report;

CREATE TABLE IF NOT EXISTS report.reports (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID         NOT NULL,
    prediction_id   UUID         NOT NULL,
    report_type     VARCHAR(20)  NOT NULL,  -- PDF, JSON, HTML
    file_path       TEXT,
    generated_by    UUID         NOT NULL,
    is_archived     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_report_patient ON report.reports(patient_id);

CREATE TABLE IF NOT EXISTS report.audit_logs (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    entity       VARCHAR(100) NOT NULL,
    entity_id    UUID         NOT NULL,
    action       VARCHAR(50)  NOT NULL,
    performed_by UUID         NOT NULL,
    details      JSONB,
    performed_at TIMESTAMP    NOT NULL DEFAULT NOW()
);
