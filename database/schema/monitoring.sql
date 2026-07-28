-- monitoring.sql — Monitoring Service Schema
CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE TABLE IF NOT EXISTS monitoring.service_metrics (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name    VARCHAR(100) NOT NULL,
    cpu_usage       NUMERIC(5,2),
    memory_usage    NUMERIC(5,2),
    latency_ms      NUMERIC(10,2),
    error_rate      NUMERIC(5,4),
    response_time   NUMERIC(10,2),
    status          VARCHAR(20)  NOT NULL DEFAULT 'UP',
    recorded_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_metric_service  ON monitoring.service_metrics(service_name);
CREATE INDEX idx_metric_time     ON monitoring.service_metrics(recorded_at DESC);
