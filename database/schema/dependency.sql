-- dependency.sql — Dependency Analyzer Service Schema
CREATE SCHEMA IF NOT EXISTS dependency;

CREATE TABLE IF NOT EXISTS dependency.dependency_graph (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    source_service  VARCHAR(100) NOT NULL,
    target_service  VARCHAR(100) NOT NULL,
    weight          NUMERIC(5,4),
    last_seen       TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE (source_service, target_service)
);

CREATE TABLE IF NOT EXISTS dependency.failure_predictions (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name    VARCHAR(100) NOT NULL,
    risk_score      NUMERIC(5,4) NOT NULL,
    predicted_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    root_cause      TEXT,
    recommendation  TEXT
);
CREATE INDEX idx_failure_service ON dependency.failure_predictions(service_name);
