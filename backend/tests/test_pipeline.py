import pytest
from datetime import datetime, timezone
from app.services.pipeline import PipelineService
from app.parsers.factory import ParserFactory
from app.validators.normalizers import (
    normalize_timestamp,
    normalize_severity,
    normalize_response_ms,
    validate_and_normalize_record,
    LogValidationError,
)
from app.services.metrics import calculate_percentile, compute_metrics_for_records


# -----------------------------------------------------------------------------
# 1. HAPPY PATH TESTS
# -----------------------------------------------------------------------------

def test_happy_path_csv():
    csv_content = """event_id,timestamp,severity,service,message,response_ms,user_id
EVT_001,2026-11-14T10:00:00Z,INFO,auth,User login successful,120,USR_101
EVT_002,2026-11-14T10:01:00Z,ERROR,payment,Payment gateway timeout,4500,USR_102
EVT_003,2026-11-14T10:02:00Z,WARNING,api,High memory usage,800,USR_103
"""
    result = PipelineService.process_log_file(csv_content, "test_happy.csv")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["total_input_records"] == 3
    assert result["reconciliation"]["valid_records"] == 3
    assert result["reconciliation"]["rejected_records"] == 0
    assert result["metrics_summary"]["error_rate_pct"] == round((1 / 3) * 100.0, 2)


def test_happy_path_json():
    json_content = """[
        {"event_id": "J1", "timestamp": "2026-11-14 10:15:20", "severity": "INFO", "service": "auth", "message": "Login ok", "response_ms": 100},
        {"event_id": "J2", "timestamp": "2026-11-14 10:16:20", "severity": "CRITICAL", "service": "db", "message": "Cluster failover", "response_ms": 3200}
    ]"""
    result = PipelineService.process_log_file(json_content, "test_happy.json")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["valid_records"] == 2
    assert result["reconciliation"]["rejected_records"] == 0


def test_happy_path_text_logs():
    text_content = """2026-11-14 10:15:20 INFO User login successful user_id=101 service=auth response_ms=120
2026-11-14 10:16:10 ERROR Database connection failed user_id=102 service=db response_ms=500
2026-11-14 10:17:30 WARNING API response time exceeded 3000ms user_id=103 service=api response_ms=3000
"""
    result = PipelineService.process_log_file(text_content, "test_happy.log")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["total_input_records"] == 3
    assert result["reconciliation"]["valid_records"] == 3
    assert result["reconciliation"]["rejected_records"] == 0


# -----------------------------------------------------------------------------
# 2. EMPTY INPUT TEST
# -----------------------------------------------------------------------------

def test_empty_input_handling():
    result = PipelineService.process_log_file("", "empty_file.csv")
    assert result["status"] == "SUCCESS"
    assert result["reconciliation"]["total_input_records"] == 0
    assert result["reconciliation"]["valid_records"] == 0
    assert result["reconciliation"]["rejected_records"] == 0
    assert result["reconciliation"]["is_reconciled"] is True


# -----------------------------------------------------------------------------
# 3. MALFORMED RECORDS & SYNTAX ERRORS
# -----------------------------------------------------------------------------

def test_malformed_json_syntax():
    corrupted_json = """{"event_id": "BAD_JSON", "timestamp": "2026-11-14T10:00:00Z", "severity": "INFO", "message": "Unclosed quote}"""
    result = PipelineService.process_log_file(corrupted_json, "broken.json")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["total_input_records"] == 1
    assert result["reconciliation"]["valid_records"] == 0
    assert result["reconciliation"]["rejected_records"] == 1


def test_malformed_csv_column_mismatch():
    csv_with_mismatch = """timestamp,severity,service,message,response_ms
2026-11-14T10:00:00Z,INFO,auth,Valid row,150
2026-11-14T10:01:00Z,INFO,auth,Too,Many,Columns,In,This,Row,999,Extra
"""
    result = PipelineService.process_log_file(csv_with_mismatch, "mismatch.csv")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["total_input_records"] == 2
    assert result["reconciliation"]["valid_records"] == 1
    assert result["reconciliation"]["rejected_records"] == 1


# -----------------------------------------------------------------------------
# 4. DUPLICATES & IDEMPOTENCY
# -----------------------------------------------------------------------------

def test_intra_batch_duplicates_quarantined():
    csv_with_dupes = """event_id,timestamp,severity,service,message,response_ms
DUPE_01,2026-11-14T10:00:00Z,INFO,auth,Initial event,120
DUPE_01,2026-11-14T10:00:05Z,INFO,auth,Duplicate event_id within batch,125
"""
    result = PipelineService.process_log_file(csv_with_dupes, "dupes.csv")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["valid_records"] == 1
    assert result["reconciliation"]["rejected_records"] == 1
    assert result["reconciliation"]["intra_batch_duplicates"] == 1


def test_idempotent_rerun_behavior():
    import uuid
    unique_evt = f"IDEMP_{uuid.uuid4().hex[:8]}"
    csv_content = f"""event_id,timestamp,severity,service,message,response_ms
{unique_evt},2026-11-14T11:00:00Z,INFO,auth,Idempotency test log,200
"""
    # First execution
    res1 = PipelineService.process_log_file(csv_content, "idempotent.csv")
    assert res1["reconciliation"]["newly_inserted_logs"] == 1

    # Second execution of identical data
    res2 = PipelineService.process_log_file(csv_content, "idempotent.csv")
    assert res2["reconciliation"]["newly_inserted_logs"] == 0
    assert res2["reconciliation"]["db_duplicates_skipped"] == 1
    assert res2["reconciliation"]["is_reconciled"] is True


# -----------------------------------------------------------------------------
# 5. NULLS & MISSING REQUIRED FIELDS
# -----------------------------------------------------------------------------

def test_missing_timestamp_rejected():
    with pytest.raises(LogValidationError, match="Missing required field: timestamp"):
        validate_and_normalize_record({"severity": "INFO", "message": "Test"}, "test.csv", "RUN_1")


def test_missing_severity_rejected():
    with pytest.raises(LogValidationError, match="Missing required field: severity"):
        validate_and_normalize_record({"timestamp": "2026-11-14T10:00:00Z", "message": "Test"}, "test.csv", "RUN_1")


def test_missing_message_rejected():
    with pytest.raises(LogValidationError, match="Missing required field: message"):
        validate_and_normalize_record({"timestamp": "2026-11-14T10:00:00Z", "severity": "INFO", "message": ""}, "test.csv", "RUN_1")


# -----------------------------------------------------------------------------
# 6. DOMAIN EDGE CASES: LATENCY & ERROR RATES
# -----------------------------------------------------------------------------

def test_domain_edge_case_negative_latency_rejected():
    with pytest.raises(LogValidationError, match="Negative response time"):
        normalize_response_ms("-50")

    with pytest.raises(LogValidationError, match="Negative response time"):
        normalize_response_ms(-12.5)


def test_domain_edge_case_p95_and_average_latency_calculation():
    # Prompt business calculation example: 100ms, 200ms, 300ms, 500ms, 900ms
    # Sum = 2000, Count = 5 -> Average = 400ms
    latencies = [100.0, 200.0, 300.0, 500.0, 900.0]
    avg = sum(latencies) / len(latencies)
    assert avg == 400.0

    p50 = calculate_percentile(latencies, 50)
    p95 = calculate_percentile(latencies, 95)
    assert p50 == 300.0
    assert p95 == 820.0  # Linear interpolation between 500 and 900


def test_domain_edge_case_error_rate_calculation():
    # Prompt example: 750 INFO, 150 WARNING, 80 ERROR, 20 CRITICAL -> Total = 1000
    # Error rate = (80 + 20) / 1000 * 100 = 10%
    sample_records = (
        [{"service": "test", "severity": "INFO", "response_ms": 100, "is_failure": False}] * 750
        + [{"service": "test", "severity": "WARNING", "response_ms": 150, "is_failure": False}] * 150
        + [{"service": "test", "severity": "ERROR", "response_ms": 500, "is_failure": True}] * 80
        + [{"service": "test", "severity": "CRITICAL", "response_ms": 1200, "is_failure": True}] * 20
    )
    metrics = compute_metrics_for_records(sample_records, "RUN_TEST_ERR_RATE")
    assert len(metrics) == 1
    m = metrics[0]
    assert m["total_logs"] == 1000
    assert m["error_count"] == 80
    assert m["critical_count"] == 20
    assert m["error_rate_pct"] == 10.0


# -----------------------------------------------------------------------------
# 7. NORMALIZATION EDGE CASES: TIMESTAMP & SEVERITY
# -----------------------------------------------------------------------------

def test_timestamp_normalizations():
    # ISO-8601 with Z
    dt1 = normalize_timestamp("2026-11-14T10:15:20Z")
    assert dt1.tzinfo == timezone.utc

    # Standard space-delimited
    dt2 = normalize_timestamp("2026-11-14 10:15:20")
    assert dt2.year == 2026 and dt2.month == 11 and dt2.day == 14

    # Epoch in milliseconds
    dt3 = normalize_timestamp(1763115320000)
    assert dt3.year == 2025 or dt3.year == 2026


def test_severity_case_and_alias_normalization():
    assert normalize_severity("info") == "INFO"
    assert normalize_severity("[warning]") == "WARNING"
    assert normalize_severity("warn") == "WARNING"
    assert normalize_severity("ERR") == "ERROR"
    assert normalize_severity("error") == "ERROR"
    assert normalize_severity("CRIT") == "CRITICAL"
    assert normalize_severity("fatal") == "CRITICAL"

    with pytest.raises(LogValidationError, match="Invalid severity"):
        normalize_severity("INVALID_SEV_123")
