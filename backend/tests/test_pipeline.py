import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.database.connection import SessionLocal
from app.models.models import ApplicationLog, RejectedLog, PipelineRun
from app.services.pipeline import PipelineService
from app.parsers.factory import ParserFactory
from app.validators.normalizers import (
    normalize_timestamp,
    normalize_severity,
    normalize_response_ms,
    validate_and_normalize_record,
    LogValidationError,
    LogSchemaError,
)
from app.services.metrics import calculate_percentile, compute_metrics_for_records


# -----------------------------------------------------------------------------
# 1. HAPPY PATH TESTS
# -----------------------------------------------------------------------------

def test_happy_path_csv():
    uid = uuid.uuid4().hex[:6]
    csv_content = f"""event_id,timestamp,severity,service,message,response_ms,user_id
EVT_HP_{uid}_1,2026-11-14T10:00:00Z,INFO,auth,User login successful,120,USR_101
EVT_HP_{uid}_2,2026-11-14T10:01:00Z,ERROR,payment,Payment gateway timeout,4500,USR_102
EVT_HP_{uid}_3,2026-11-14T10:02:00Z,WARNING,api,High memory usage,800,USR_103
"""
    result = PipelineService.process_log_file(csv_content, "test_happy.csv")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["total_input_records"] == 3
    assert result["reconciliation"]["newly_inserted_records"] == 3
    assert result["reconciliation"]["rejected_records"] == 0
    assert result["metrics_summary"]["severity_error_rate_pct"] == round((1 / 3) * 100.0, 2)


def test_happy_path_json():
    uid = uuid.uuid4().hex[:6]
    json_content = f"""[
        {{"event_id": "J_HP_{uid}_1", "timestamp": "2026-11-14 10:15:20", "severity": "INFO", "service": "auth", "message": "Login ok", "response_ms": 100}},
        {{"event_id": "J_HP_{uid}_2", "timestamp": "2026-11-14 10:16:20", "severity": "CRITICAL", "service": "db", "message": "Cluster failover", "response_ms": 3200}}
    ]"""
    result = PipelineService.process_log_file(json_content, "test_happy.json")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["newly_inserted_records"] == 2
    assert result["reconciliation"]["rejected_records"] == 0


def test_happy_path_text_logs():
    uid = uuid.uuid4().hex[:6]
    text_content = f"""2026-11-14 10:15:20 INFO User login successful user_id=101 service=auth response_ms=120 event_id=EVT_TXT_{uid}_1
2026-11-14 10:16:10 ERROR Database connection failed user_id=102 service=db response_ms=500 event_id=EVT_TXT_{uid}_2
2026-11-14 10:17:30 WARNING API response time exceeded 3000ms user_id=103 service=api response_ms=3000 event_id=EVT_TXT_{uid}_3
"""
    result = PipelineService.process_log_file(text_content, "test_happy.log")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["total_input_records"] == 3
    assert result["reconciliation"]["newly_inserted_records"] == 3
    assert result["reconciliation"]["rejected_records"] == 0


# -----------------------------------------------------------------------------
# 2. EMPTY INPUT TEST
# -----------------------------------------------------------------------------

def test_empty_input_handling():
    result = PipelineService.process_log_file("", "empty_file.csv")
    assert result["status"] == "SUCCESS"
    assert result["reconciliation"]["total_input_records"] == 0
    assert result["reconciliation"]["newly_inserted_records"] == 0
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
    assert result["reconciliation"]["newly_inserted_records"] == 0
    assert result["reconciliation"]["rejected_records"] == 1


def test_malformed_csv_column_mismatch():
    uid = uuid.uuid4().hex[:6]
    csv_with_mismatch = f"""event_id,timestamp,severity,service,message,response_ms
MISMATCH_{uid},2026-11-14T10:00:00Z,INFO,auth,Valid row,150
2026-11-14T10:01:00Z,INFO,auth,Too,Many,Columns,In,This,Row,999,Extra
"""
    result = PipelineService.process_log_file(csv_with_mismatch, "mismatch.csv")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["total_input_records"] == 2
    assert result["reconciliation"]["newly_inserted_records"] == 1
    assert result["reconciliation"]["rejected_records"] == 1


# -----------------------------------------------------------------------------
# 4. DUPLICATES & IDEMPOTENCY
# -----------------------------------------------------------------------------

def test_intra_batch_duplicates_quarantined():
    uid = uuid.uuid4().hex[:6]
    dupe_id = f"DUPE_{uid}"
    csv_with_dupes = f"""event_id,timestamp,severity,service,message,response_ms
{dupe_id},2026-11-14T10:00:00Z,INFO,auth,Initial event,120
{dupe_id},2026-11-14T10:00:05Z,INFO,auth,Duplicate event_id within batch,125
"""
    result = PipelineService.process_log_file(csv_with_dupes, "dupes.csv")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["newly_inserted_records"] == 1
    assert result["reconciliation"]["rejected_records"] == 1
    assert result["reconciliation"]["intra_batch_duplicates"] == 1


def test_idempotent_rerun_behavior():
    unique_evt = f"IDEMP_{uuid.uuid4().hex[:8]}"
    csv_content = f"""event_id,timestamp,severity,service,message,response_ms
{unique_evt},2026-11-14T11:00:00Z,INFO,auth,Idempotency test log,200
"""
    # First execution
    res1 = PipelineService.process_log_file(csv_content, "idempotent.csv")
    assert res1["reconciliation"]["newly_inserted_records"] == 1

    # Second execution of identical data
    res2 = PipelineService.process_log_file(csv_content, "idempotent.csv")
    assert res2["reconciliation"]["newly_inserted_records"] == 0
    assert res2["reconciliation"]["previously_skipped_records"] == 1
    assert res2["reconciliation"]["is_reconciled"] is True


# -----------------------------------------------------------------------------
# 5. NULLS & MISSING REQUIRED FIELDS
# -----------------------------------------------------------------------------

def test_missing_timestamp_rejected():
    with pytest.raises(LogSchemaError, match="Missing required field: timestamp") as exc:
        validate_and_normalize_record({"severity": "INFO", "message": "Test"}, "test.csv", "RUN_1")
    assert exc.value.reject_type == "SCHEMA_ERROR"


def test_missing_severity_rejected():
    with pytest.raises(LogSchemaError, match="Missing required field: severity") as exc:
        validate_and_normalize_record({"timestamp": "2026-11-14T10:00:00Z", "message": "Test"}, "test.csv", "RUN_1")
    assert exc.value.reject_type == "SCHEMA_ERROR"


def test_missing_message_rejected():
    with pytest.raises(LogSchemaError, match="Missing required field: message") as exc:
        validate_and_normalize_record({"timestamp": "2026-11-14T10:00:00Z", "severity": "INFO", "message": ""}, "test.csv", "RUN_1")
    assert exc.value.reject_type == "SCHEMA_ERROR"


# -----------------------------------------------------------------------------
# 6. DOMAIN EDGE CASES: LATENCY & ERROR RATES
# -----------------------------------------------------------------------------

def test_domain_edge_case_negative_latency_rejected():
    with pytest.raises(LogValidationError, match="Negative response time"):
        normalize_response_ms("-50")

    with pytest.raises(LogValidationError, match="Negative response time"):
        normalize_response_ms(-12.5)


def test_domain_edge_case_p95_and_average_latency_calculation():
    latencies = [100.0, 200.0, 300.0, 500.0, 900.0]
    avg = sum(latencies) / len(latencies)
    assert avg == 400.0

    p50 = calculate_percentile(latencies, 50)
    p95 = calculate_percentile(latencies, 95)
    assert p50 == 300.0
    assert p95 == 820.0


def test_domain_edge_case_error_rate_calculation():
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
    dt1 = normalize_timestamp("2026-11-14T10:15:20Z")
    assert dt1.tzinfo == timezone.utc

    dt2 = normalize_timestamp("2026-11-14 10:15:20")
    assert dt2.year == 2026 and dt2.month == 11 and dt2.day == 14

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


# -----------------------------------------------------------------------------
# 8. REQUIRED EDGE CASES & NEGATIVE SCENARIOS (NEW TESTS)
# -----------------------------------------------------------------------------

def test_unexpected_schema_change():
    """Verify input with incompatible or missing required columns is rejected under SCHEMA_ERROR."""
    incompatible_csv = """col_x,col_y,col_z
val1,val2,val3
val4,val5,val6
"""
    result = PipelineService.process_log_file(incompatible_csv, "schema_change.csv")
    assert result["reconciliation"]["is_reconciled"] is True
    # Both data rows are accounted for and quarantined as SCHEMA_ERROR
    assert result["reconciliation"]["total_input_records"] == 2
    assert result["reconciliation"]["rejected_records"] == 2
    assert result["reconciliation"]["newly_inserted_records"] == 0

    # Verify reject type in database
    db = SessionLocal()
    try:
        rejections = db.query(RejectedLog).filter(RejectedLog.run_id == result["run_id"]).all()
        assert len(rejections) == 2
        for rej in rejections:
            assert rej.reject_type == "SCHEMA_ERROR"
            assert "Incompatible schema" in rej.reason
    finally:
        db.close()


def test_partial_success_and_manual_rerun():
    """
    Verify partial success handling and manual rerun idempotency.
    In this architecture, retries are manual re-submissions of batches.
    Duplicate prevention via deterministic event IDs ensures already inserted rows
    are safely skipped without double-insertion upon rerun.
    """
    unique_a = f"EVT_PART_{uuid.uuid4().hex[:6]}"
    unique_b = f"EVT_PART_{uuid.uuid4().hex[:6]}"
    # Batch with 2 valid records and 1 malformed record (negative latency)
    csv_content = f"""event_id,timestamp,severity,service,message,response_ms
{unique_a},2026-11-14T10:00:00Z,INFO,auth,Valid event A,120
{unique_b},2026-11-14T10:01:00Z,INFO,auth,Valid event B,150
EVT_BAD,2026-11-14T10:02:00Z,INFO,auth,Bad latency record,-999
"""
    # 1. Initial run: Partial Success
    res1 = PipelineService.process_log_file(csv_content, "batch_partial.csv", retry_count=0)
    assert res1["status"] == "PARTIAL_SUCCESS"
    assert res1["reconciliation"]["newly_inserted_records"] == 2
    assert res1["reconciliation"]["rejected_records"] == 1
    assert res1["reconciliation"]["is_reconciled"] is True

    # 2. Manual rerun execution: should NOT duplicate the 2 successfully inserted records
    res2 = PipelineService.process_log_file(csv_content, "batch_partial.csv", retry_count=1)
    assert res2["reconciliation"]["newly_inserted_records"] == 0
    assert res2["reconciliation"]["previously_skipped_records"] == 2
    assert res2["reconciliation"]["rejected_records"] == 1
    assert res2["reconciliation"]["is_reconciled"] is True


def test_missing_required_field_quarantined_as_schema_error():
    """
    End-to-end pipeline verification: records missing a required core field
    (timestamp, severity, or message) are quarantined in rejected_logs with reject_type == 'SCHEMA_ERROR'.
    """
    unique_tag = uuid.uuid4().hex[:6]
    csv_payload = f"""timestamp,severity,service,message,response_ms
,INFO,auth,Missing timestamp record,100
2026-11-14T10:00:00Z,,auth,Missing severity record,100
2026-11-14T10:01:00Z,INFO,auth,,100
2026-11-14T10:02:00Z,INFO,auth,Fully valid record {unique_tag},100
"""
    result = PipelineService.process_log_file(csv_payload, "test_schema_errors.csv")
    assert result["reconciliation"]["total_input_records"] == 4
    assert result["reconciliation"]["newly_inserted_records"] == 1
    assert result["reconciliation"]["rejected_records"] == 3
    assert result["reconciliation"]["is_reconciled"] is True

    db = SessionLocal()
    try:
        rejections = db.query(RejectedLog).filter(RejectedLog.run_id == result["run_id"]).all()
        assert len(rejections) == 3
        for rej in rejections:
            assert rej.reject_type == "SCHEMA_ERROR"
            assert "Missing required field" in rej.reason
    finally:
        db.close()


def test_json_and_text_parser_raw_record_whitespace_preservation():
    """Verify raw unstripped indentation and whitespace is preserved in raw_record."""
    from app.parsers.json_parser import JsonLogParser
    from app.parsers.text_parser import TextLogParser

    json_parser = JsonLogParser()
    ndjson_content = '   {"event_id": "INDENT_1", "timestamp": "2026-11-14T10:00:00Z", "severity": "INFO", "message": "Indented JSON"}\n   CORRUPT JSON LINE   '
    res_json = json_parser.parse_content(ndjson_content)
    assert len(res_json) == 2
    assert res_json[0].raw_record.startswith("   {")
    assert res_json[1].raw_record == "   CORRUPT JSON LINE   "
    assert res_json[1].reject_type == "MALFORMED"

    text_parser = TextLogParser()
    text_content = "   2026-11-14 10:00:00 [INFO] [auth] Leading whitespace text line\n   NOT A VALID LOG LINE   "
    res_text = text_parser.parse_content(text_content)
    assert len(res_text) == 2
    assert res_text[0].raw_record.startswith("   2026-11-14")
    assert res_text[1].raw_record == "   NOT A VALID LOG LINE   "
    assert res_text[1].reject_type == "MALFORMED"


def test_timestamp_boundary_enforcement_all_input_types():
    """Verify allowable date bounds (1970–2100) are strictly enforced for all timestamp formats."""
    # 1. Valid boundary: Epoch 0 (1970-01-01)
    dt0 = normalize_timestamp(0)
    assert dt0.year == 1970
    dt0_str = normalize_timestamp("0")
    assert dt0_str.year == 1970

    # 2. Numeric epoch before 1970 (e.g. -100 seconds)
    with pytest.raises(LogValidationError, match="Timestamp year out of allowable bounds"):
        normalize_timestamp(-100)

    # 3. Numeric epoch after 2100 (e.g. year 2105: 4260000000)
    with pytest.raises(LogValidationError, match="Timestamp year out of allowable bounds"):
        normalize_timestamp(4260000000)

    # 4. Digit-string epoch outside allowable range (before 1970 or after 2100)
    with pytest.raises(LogValidationError, match="Timestamp year out of allowable bounds"):
        normalize_timestamp("-1000000")

    with pytest.raises(LogValidationError, match="Timestamp year out of allowable bounds"):
        normalize_timestamp("5000000000")

    # 5. Datetime object outside allowable range
    with pytest.raises(LogValidationError, match="Timestamp year out of allowable bounds"):
        normalize_timestamp(datetime(1965, 5, 20))

    with pytest.raises(LogValidationError, match="Timestamp year out of allowable bounds"):
        normalize_timestamp(datetime(2150, 1, 1))

    # 6. Valid numeric epoch in milliseconds
    dt_ms = normalize_timestamp(1700000000000)
    assert dt_ms.year == 2023


def test_json_array_raw_record_preservation():
    """Verify that JSON array elements preserve their exact original raw text slice upon quarantine."""
    unique_tag = uuid.uuid4().hex[:6]
    json_array_content = f"""[
  {{
    "timestamp": "",
    "severity": "INFO",
    "message": "Quarantined record in JSON array {unique_tag}"
  }},
  {{
    "timestamp": "2026-11-14T10:00:00Z",
    "severity": "INFO",
    "message": "Valid array record {unique_tag}"
  }}
]"""
    result = PipelineService.process_log_file(json_array_content, "array_quarantine.json")
    assert result["reconciliation"]["total_input_records"] == 2
    assert result["reconciliation"]["newly_inserted_records"] == 1
    assert result["reconciliation"]["rejected_records"] == 1
    assert result["reconciliation"]["is_reconciled"] is True

    db = SessionLocal()
    try:
        rej = db.query(RejectedLog).filter(RejectedLog.run_id == result["run_id"]).first()
        assert rej is not None
        assert rej.reject_type == "SCHEMA_ERROR"
        # Assert that the exact original multiline string formatting with indentation was preserved
        assert f'"message": "Quarantined record in JSON array {unique_tag}"' in rej.raw_record
        assert '{\n    "timestamp": ""' in rej.raw_record
    finally:
        db.close()


def test_database_failure_injection_rollback_and_retry():
    """
    Simulate an unexpected database insertion failure during pipeline execution.
    Verify that:
    1. The transaction is rolled back and no uncommitted application logs remain.
    2. The pipeline_runs record is marked FAILED with diagnostic failure_reason.
    3. Retrying the batch succeeds without duplicate records.
    4. Subsequent reruns are idempotent.
    """
    from unittest.mock import patch
    from sqlalchemy.orm import Session as SqlASession

    unique_tag = uuid.uuid4().hex[:6]
    csv_payload = f"""timestamp,severity,service,message,response_ms
2026-11-14T10:00:00Z,INFO,auth,Retry test record 1 {unique_tag},100
2026-11-14T10:01:00Z,INFO,auth,Retry test record 2 {unique_tag},200
2026-11-14T10:02:00Z,INFO,auth,Retry test record 3 {unique_tag},300
"""
    fail_run_id = f"RUN_FAIL_{unique_tag}"

    # 1. Inject failure during bulk_insert_mappings
    with patch.object(SqlASession, "bulk_insert_mappings", side_effect=RuntimeError("Simulated DB connection dropped")):
        with pytest.raises(RuntimeError, match="Simulated DB connection dropped"):
            PipelineService.process_log_file(csv_payload, "failure_test.csv", run_id=fail_run_id)

    # 2. Verify rollback: zero ApplicationLog rows with unique_tag exist
    db = SessionLocal()
    try:
        inserted = db.query(ApplicationLog).filter(ApplicationLog.message.contains(unique_tag)).all()
        assert len(inserted) == 0

        # Verify pipeline_runs recorded FAILED status with failure_reason
        failed_run = db.query(PipelineRun).filter(PipelineRun.run_id == fail_run_id).first()
        assert failed_run is not None
        assert failed_run.status == "FAILED"
        assert "Simulated DB connection dropped" in (failed_run.failure_reason or "")
    finally:
        db.close()

    # 3. Retry the exact same batch without failure injection
    retry_run_id = f"RUN_RETRY_{unique_tag}"
    retry_res = PipelineService.process_log_file(
        csv_payload,
        "failure_test.csv",
        run_id=retry_run_id,
        retry_count=1
    )
    assert retry_res["status"] == "SUCCESS"
    assert retry_res["reconciliation"]["newly_inserted_records"] == 3
    assert retry_res["reconciliation"]["rejected_records"] == 0
    assert retry_res["reconciliation"]["previously_skipped_records"] == 0
    assert retry_res["reconciliation"]["is_reconciled"] is True

    # 4. Subsequent rerun: verify idempotency
    rerun_run_id = f"RUN_RERUN_{unique_tag}"
    rerun_res = PipelineService.process_log_file(
        csv_payload,
        "failure_test.csv",
        run_id=rerun_run_id,
        retry_count=2
    )
    assert rerun_res["reconciliation"]["newly_inserted_records"] == 0
    assert rerun_res["reconciliation"]["previously_skipped_records"] == 3
    assert rerun_res["reconciliation"]["is_reconciled"] is True


def test_late_arriving_logs():
    """Verify older historical event timestamps are accepted and processed correctly."""
    unique_evt = f"LATE_{uuid.uuid4().hex[:8]}"
    csv_content = f"""event_id,timestamp,severity,service,message,response_ms
{unique_evt},2020-05-12T04:30:00Z,INFO,auth,Historical log from 2020,110
"""
    result = PipelineService.process_log_file(csv_content, "late_arriving.csv")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["newly_inserted_records"] == 1
    assert result["reconciliation"]["rejected_records"] == 0


def test_out_of_order_timestamps():
    """Verify non-chronological / out-of-order events within the same batch are handled properly."""
    u1, u2, u3 = f"OOO_{uuid.uuid4().hex[:6]}", f"OOO_{uuid.uuid4().hex[:6]}", f"OOO_{uuid.uuid4().hex[:6]}"
    csv_content = f"""event_id,timestamp,severity,service,message,response_ms
{u1},2026-11-14T12:00:00Z,INFO,auth,Event at noon,100
{u2},2026-11-14T08:00:00Z,INFO,auth,Event earlier at 8 AM,200
{u3},2026-11-14T10:00:00Z,INFO,auth,Event at 10 AM,150
"""
    result = PipelineService.process_log_file(csv_content, "out_of_order.csv")
    assert result["reconciliation"]["is_reconciled"] is True
    assert result["reconciliation"]["newly_inserted_records"] == 3
    assert result["reconciliation"]["rejected_records"] == 0


def test_invalid_reference_key():
    """Verify foreign key constraint integrity: log with non-existent run_id is safely prevented."""
    db = SessionLocal()
    try:
        bogus_log = ApplicationLog(
            event_id=f"BOGUS_{uuid.uuid4().hex[:8]}",
            run_id="NON_EXISTENT_RUN_KEY_12345",
            timestamp=datetime.now(timezone.utc),
            severity="INFO",
            service="auth",
            message="Foreign key violation test",
            source_file="test.csv"
        )
        db.add(bogus_log)
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_null_optional_fields():
    """Verify optional fields (user_id, endpoint, http_status, response_ms) can be null without rejection."""
    unique_evt = f"NULL_OPT_{uuid.uuid4().hex[:8]}"
    rec = {
        "event_id": unique_evt,
        "timestamp": "2026-11-14T10:00:00Z",
        "severity": "INFO",
        "service": "auth",
        "message": "Valid record with null optionals",
        "user_id": None,
        "endpoint": None,
        "http_status": None,
        "response_ms": None,
    }
    cleaned = validate_and_normalize_record(rec, "test.json", "RUN_NULL")
    assert cleaned["event_id"] == unique_evt
    assert cleaned["user_id"] is None
    assert cleaned["response_ms"] is None
    assert cleaned["http_status"] is None


def test_http_failure_rate():
    """Verify INFO severity with HTTP 503 is accurately counted as HTTP failure and not severity error."""
    records = [
        {"service": "api", "severity": "INFO", "http_status": 200, "response_ms": 100, "is_failure": False},
        {"service": "api", "severity": "INFO", "http_status": 200, "response_ms": 110, "is_failure": False},
        {"service": "api", "severity": "INFO", "http_status": 503, "response_ms": 450, "is_failure": True},
    ]
    metrics = compute_metrics_for_records(records, "RUN_HTTP_TEST")
    assert len(metrics) == 1
    m = metrics[0]
    assert m["total_logs"] == 3
    assert m["error_count"] == 0
    assert m["critical_count"] == 0
    assert m["error_rate_pct"] == 0.0  # Severity error rate is 0%
    assert m["http_request_count"] == 3
    assert m["http_failure_count"] == 1
    assert m["http_failure_rate_pct"] == round((1 / 3 * 100.0), 2)  # HTTP failure rate is 33.33%


def test_rerun_reconciliation():
    """Verify reconciliation accounting when re-ingesting duplicate file: Input = Inserted + Rejects + Skipped."""
    u1 = f"RERUN_{uuid.uuid4().hex[:6]}"
    u2 = f"RERUN_{uuid.uuid4().hex[:6]}"
    csv_payload = f"""event_id,timestamp,severity,service,message,response_ms
{u1},2026-11-14T10:00:00Z,INFO,auth,Event 1,100
{u2},2026-11-14T10:01:00Z,INFO,auth,Event 2,120
BAD_EVT,2026-11-14T10:02:00Z,INFO,auth,Negative latency,-500
"""
    # Run 1: 2 inserted, 1 rejected, 0 skipped -> Total 3
    res1 = PipelineService.process_log_file(csv_payload, "rerun_audit.csv")
    assert res1["reconciliation"]["newly_inserted_records"] == 2
    assert res1["reconciliation"]["rejected_records"] == 1
    assert res1["reconciliation"]["previously_skipped_records"] == 0
    assert res1["reconciliation"]["accounted_for"] == 3
    assert res1["reconciliation"]["is_reconciled"] is True

    # Run 2: 0 newly inserted, 1 rejected, 2 previously skipped -> Total 3
    res2 = PipelineService.process_log_file(csv_payload, "rerun_audit.csv")
    assert res2["reconciliation"]["newly_inserted_records"] == 0
    assert res2["reconciliation"]["rejected_records"] == 1
    assert res2["reconciliation"]["previously_skipped_records"] == 2
    assert res2["reconciliation"]["accounted_for"] == 3
    assert res2["reconciliation"]["is_reconciled"] is True


def test_valid_zero_latency_preserved():
    """Ensure that legitimate 0 and 0.0 response times are not dropped or converted to NULL."""
    u_zero = f"ZERO_{uuid.uuid4().hex[:6]}"
    csv_payload = f"""event_id,timestamp,severity,service,message,response_ms
{u_zero},2026-11-14T10:00:00Z,INFO,cache,Cache instant hit,0
"""
    res = PipelineService.process_log_file(csv_payload, "zero_latency.csv")
    assert res["status"] == "SUCCESS"
    assert res["reconciliation"]["newly_inserted_records"] == 1

    db = SessionLocal()
    try:
        log = db.query(ApplicationLog).filter(ApplicationLog.event_id == u_zero).first()
        assert log is not None
        assert log.response_ms == 0.0
        assert log.to_dict()["response_ms"] == 0.0
    finally:
        db.close()


def test_deterministic_event_id_includes_endpoint_and_status():
    """Ensure events at identical timestamp/service/message but distinct endpoints/statuses don't collide."""
    unique_tag = uuid.uuid4().hex[:6]
    ts = "2026-11-14T12:00:00Z"
    csv_payload = f"""timestamp,severity,service,message,endpoint,http_status
{ts},INFO,gateway,Gateway request {unique_tag},/api/v1/users,200
{ts},INFO,gateway,Gateway request {unique_tag},/api/v1/orders,200
{ts},INFO,gateway,Gateway request {unique_tag},/api/v1/users,500
"""
    res = PipelineService.process_log_file(csv_payload, "endpoints.csv")
    assert res["status"] == "SUCCESS"
    # All 3 records should have unique generated event IDs and be inserted
    assert res["reconciliation"]["newly_inserted_records"] == 3
    assert res["reconciliation"]["rejected_records"] == 0


def test_csv_raw_record_quoting_preserved():
    """Ensure CSV lines with quoted commas retain exact raw source text."""
    csv_content = """timestamp,severity,message,response_ms
2026-11-14T10:00:00Z,INFO,"Payment processed, authorized by bank",-100
"""
    res = PipelineService.process_log_file(csv_content, "quoted.csv")
    assert res["reconciliation"]["rejected_records"] == 1
    db = SessionLocal()
    try:
        rej = db.query(RejectedLog).filter(RejectedLog.run_id == res["run_id"]).first()
        assert rej is not None
        # Must retain original quotes, not stripped/re-joined
        assert '"Payment processed, authorized by bank"' in rej.raw_record
    finally:
        db.close()


def test_epoch_zero_timestamp_normalized():
    """Ensure epoch 0 is normalized to 1970 UTC without being treated as falsy/missing."""
    raw = {"timestamp": 0, "severity": "INFO", "message": "Epoch zero test"}
    cleaned = validate_and_normalize_record(raw, "epoch_zero.json", "RUN_TEST")
    assert cleaned["timestamp"].year == 1970
    assert cleaned["timestamp"].month == 1
    assert cleaned["timestamp"].day == 1


def test_timestamps_serialized_with_utc_z():
    """Ensure database to_dict() returns timestamps with explicit UTC 'Z'."""
    u_tz = f"TZ_{uuid.uuid4().hex[:6]}"
    csv_payload = f"""event_id,timestamp,severity,service,message
{u_tz},2026-11-14T10:00:00Z,INFO,auth,Timezone test
"""
    res = PipelineService.process_log_file(csv_payload, "tz_test.csv")
    db = SessionLocal()
    try:
        log = db.query(ApplicationLog).filter(ApplicationLog.event_id == u_tz).first()
        d = log.to_dict()
        assert d["timestamp"].endswith("Z")
        assert d["ingested_at"].endswith("Z")

        run = db.query(PipelineRun).filter(PipelineRun.run_id == res["run_id"]).first()
        rd = run.to_dict()
        assert rd["start_time"].endswith("Z")
        assert rd["created_at"].endswith("Z")
    finally:
        db.close()


def test_csv_with_leading_blank_lines():
    """Ensure CSV with leading blank lines is not rejected."""
    unique_msg = f"Hello {uuid.uuid4().hex[:6]}"
    content = f"""

timestamp,severity,message
2026-11-14T10:00:00Z,INFO,{unique_msg}"""
    res = PipelineService.process_log_file(content, "leading_blank.csv")
    assert res["status"] == "SUCCESS"
    assert res["reconciliation"]["newly_inserted_records"] == 1
    assert res["reconciliation"]["rejected_records"] == 0
    assert res["reconciliation"]["is_reconciled"] is True


def test_csv_with_utf8_bom():
    """Ensure CSV with UTF-8 BOM is recognized and parsed correctly."""
    unique_msg = f"Hello BOM {uuid.uuid4().hex[:6]}"
    content = "\ufefftimestamp,severity,message\n"
    content += f"2026-11-14T10:00:00Z,INFO,{unique_msg}"
    res = PipelineService.process_log_file(content, "bom.csv")
    assert res["status"] == "SUCCESS"
    assert res["reconciliation"]["newly_inserted_records"] == 1
    assert res["reconciliation"]["rejected_records"] == 0
    assert res["reconciliation"]["is_reconciled"] is True


def test_csv_multiline_raw_record():
    """Ensure multiline quoted CSV records preserve complete original raw record."""
    content = (
        'timestamp,severity,message\n'
        '2026-11-14T10:00:00Z,INFO,"Payment\n'
        'processing failed"\n'
    )
    from app.parsers.csv_parser import CsvLogParser
    parser = CsvLogParser()
    parsed = parser.parse_content(content)
    assert len(parsed) == 1
    assert parsed[0].is_parse_ok is True
    assert parsed[0].data["message"] == "Payment\nprocessing failed"
    expected_raw = '2026-11-14T10:00:00Z,INFO,"Payment\nprocessing failed"'
    assert parsed[0].raw_record == expected_raw


def test_csv_multiline_crlf_raw_record():
    """Ensure multiline CSV record with Windows CRLF preserves exact embedded CRLF in raw_record."""
    bad_content = (
        "timestamp,severity,message,response_ms\r\n"
        '2026-11-14T10:00:00Z,ERROR,"First line\r\n'
        'Second line",-50\r\n'
    )
    res = PipelineService.process_log_file(bad_content, "crlf_rej.csv")
    assert res["reconciliation"]["rejected_records"] == 1
    db = SessionLocal()
    try:
        rej = db.query(RejectedLog).filter(RejectedLog.run_id == res["run_id"]).first()
        assert rej is not None
        assert "First line\r\nSecond line" in rej.raw_record
        assert "\r\n" in rej.raw_record
    finally:
        db.close()


def test_valid_records_counts_all_validated_before_duplicate_screening():
    """Verify that valid_records represents all records that passed validation before duplicate screening."""
    ts = "2026-11-14T10:00:00Z"
    unique_tag = uuid.uuid4().hex[:6]
    # 4 records in total:
    # 2 identical records (1 original + 1 intra-batch duplicate)
    # 1 distinct valid record
    # 1 corrupt record (negative latency)
    csv_payload = f"""event_id,timestamp,severity,service,message,response_ms
EVT_DUP_{unique_tag},{ts},INFO,auth,Duplicate message,100
EVT_DUP_{unique_tag},{ts},INFO,auth,Duplicate message,100
EVT_OK_{unique_tag},{ts},INFO,auth,Unique valid message,150
EVT_BAD_{unique_tag},{ts},INFO,auth,Bad latency record,-500
"""
    res = PipelineService.process_log_file(csv_payload, "valid_count_test.csv")
    recon = res["reconciliation"]
    # Total input: 4 records
    assert recon["total_input_records"] == 4
    # Valid records (passed validation): 3 records (EVT_DUP, EVT_DUP, EVT_OK)
    assert recon["valid_records"] == 3
    # Newly inserted: 2 records (EVT_DUP first instance + EVT_OK)
    assert recon["newly_inserted_records"] == 2
    # Rejected records: 2 records (1 duplicate + 1 negative latency)
    assert recon["rejected_records"] == 2
    assert recon["intra_batch_duplicates"] == 1
    # Conservation law holds: 4 == 2 (inserted) + 2 (rejected) + 0 (skipped)
    assert recon["accounted_for"] == 4
    assert recon["is_reconciled"] is True
    # In metrics_summary, unique_valid_records represents unique valid records after deduplication
    assert res["metrics_summary"]["unique_valid_records"] == 2
