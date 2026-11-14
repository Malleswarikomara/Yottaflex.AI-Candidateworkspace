-- =============================================================================
-- Application Log Analytics & Monitoring Platform
-- Database Schema: PostgreSQL 14+
-- =============================================================================

-- 1. Pipeline Execution Runs
-- Grain: One record per pipeline execution (file upload or batch process)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    file_format VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING' 
        CHECK (status IN ('PENDING', 'RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED')),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds DOUBLE PRECISION,
    total_input_records INTEGER NOT NULL DEFAULT 0,
    valid_records INTEGER NOT NULL DEFAULT 0,
    rejected_records INTEGER NOT NULL DEFAULT 0,
    duplicate_records INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_start_time ON pipeline_runs(start_time DESC);

-- 2. Valid Cleaned Application Logs
-- Grain: One record per unique application event
CREATE TABLE IF NOT EXISTS application_logs (
    event_id VARCHAR(64) PRIMARY KEY,
    run_id VARCHAR(64) REFERENCES pipeline_runs(run_id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    severity VARCHAR(16) NOT NULL 
        CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    service VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    response_ms DOUBLE PRECISION CHECK (response_ms IS NULL OR response_ms >= 0),
    user_id VARCHAR(64),
    endpoint VARCHAR(255),
    http_status INTEGER,
    is_failure BOOLEAN NOT NULL DEFAULT FALSE,
    source_file VARCHAR(255) NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_app_logs_timestamp ON application_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_app_logs_severity ON application_logs(severity);
CREATE INDEX IF NOT EXISTS idx_app_logs_service ON application_logs(service);
CREATE INDEX IF NOT EXISTS idx_app_logs_run_id ON application_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_app_logs_response_ms ON application_logs(response_ms);
CREATE INDEX IF NOT EXISTS idx_app_logs_is_failure ON application_logs(is_failure);
CREATE INDEX IF NOT EXISTS idx_app_logs_composite ON application_logs(service, severity, timestamp DESC);

-- 3. Quarantined Rejected Logs
-- Grain: One record per invalid / unparseable / malformed raw log event
CREATE TABLE IF NOT EXISTS rejected_logs (
    reject_id SERIAL PRIMARY KEY,
    run_id VARCHAR(64) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    source_file VARCHAR(255) NOT NULL,
    raw_record TEXT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    rejected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rejected_logs_run_id ON rejected_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_rejected_logs_reason ON rejected_logs(reason);
CREATE INDEX IF NOT EXISTS idx_rejected_logs_rejected_at ON rejected_logs(rejected_at DESC);

-- 4. Pre-aggregated Error Rate & Latency Metrics
-- Grain: Aggregated summary per service and pipeline run
CREATE TABLE IF NOT EXISTS log_metrics (
    metric_id SERIAL PRIMARY KEY,
    run_id VARCHAR(64) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    service VARCHAR(64) NOT NULL,
    total_logs INTEGER NOT NULL DEFAULT 0,
    info_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    critical_count INTEGER NOT NULL DEFAULT 0,
    failed_requests INTEGER NOT NULL DEFAULT 0,
    error_rate_pct DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    avg_latency_ms DOUBLE PRECISION,
    p50_latency_ms DOUBLE PRECISION,
    p95_latency_ms DOUBLE PRECISION,
    p99_latency_ms DOUBLE PRECISION,
    max_latency_ms DOUBLE PRECISION,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_log_metrics_run_id ON log_metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_log_metrics_service ON log_metrics(service);

-- 5. Analytical Views for Reporting & Reconciliation
CREATE OR REPLACE VIEW v_reconciliation_summary AS
SELECT 
    pr.run_id,
    pr.source_file,
    pr.status,
    pr.total_input_records,
    pr.valid_records,
    pr.rejected_records,
    (pr.valid_records + pr.rejected_records) AS accounted_for_records,
    CASE 
        WHEN pr.total_input_records = (pr.valid_records + pr.rejected_records) THEN TRUE 
        ELSE FALSE 
    END AS is_reconciled,
    pr.duration_seconds,
    pr.start_time
FROM pipeline_runs pr;

CREATE OR REPLACE VIEW v_service_kpis AS
SELECT 
    service,
    COUNT(*) AS total_logs,
    SUM(CASE WHEN severity = 'INFO' THEN 1 ELSE 0 END) AS info_count,
    SUM(CASE WHEN severity = 'WARNING' THEN 1 ELSE 0 END) AS warning_count,
    SUM(CASE WHEN severity = 'ERROR' THEN 1 ELSE 0 END) AS error_count,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count,
    ROUND(
        (SUM(CASE WHEN severity IN ('ERROR', 'CRITICAL') THEN 1 ELSE 0 END)::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100), 2
    ) AS error_rate_pct,
    ROUND(AVG(response_ms)::NUMERIC, 2) AS avg_latency_ms,
    ROUND(MAX(response_ms)::NUMERIC, 2) AS max_latency_ms
FROM application_logs
GROUP BY service;
