import pytest
from app.database.connection import SessionLocal
from app.routes.pipeline import (
    list_pipeline_runs,
    get_pipeline_run_details,
    generate_synthetic_data,
    run_sample_file,
    GenerateRequest,
)
from app.services.pipeline import PipelineService
from app.routes.logs import list_logs, get_log_stats, get_latency_distribution
from app.routes.rejected import list_rejected_logs, get_rejected_stats
from app.routes.metrics import list_metrics
from app.main import health_check, system_info


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_route_health_and_info():
    health = health_check()
    assert health["status"] == "healthy"
    info = system_info()
    assert "Three-Tier Architecture" in info["architecture"]


def test_route_pipeline_runs_listing(db_session):
    runs = list_pipeline_runs(limit=10, db=db_session)
    assert isinstance(runs, list)
    assert len(runs) > 0
    assert "run_id" in runs[0]
    assert "reconciled" in str(runs[0].keys()).lower() or "valid_records" in runs[0]


def test_route_pipeline_run_details(db_session):
    runs = list_pipeline_runs(limit=1, db=db_session)
    if runs:
        run_id = runs[0]["run_id"]
        details = get_pipeline_run_details(run_id=run_id, db=db_session)
        assert details["run"]["run_id"] == run_id
        assert details["reconciliation"]["is_reconciled"] is True


def test_route_logs_listing_and_filtering(db_session):
    res = list_logs(page=1, limit=20, severity="INFO", db=db_session)
    assert res["page"] == 1
    assert "items" in res
    for item in res["items"]:
        assert item["severity"] == "INFO"


def test_route_logs_stats(db_session):
    stats = get_log_stats(db=db_session)
    assert stats["total_logs"] > 0
    assert stats["error_rate_pct"] >= 0.0
    assert "severity_counts" in stats
    assert "latency" in stats


def test_route_latency_distribution(db_session):
    dist = get_latency_distribution(db=db_session)
    assert "buckets" in dist
    assert dist["total_samples"] >= 0


def test_route_rejected_logs(db_session):
    rejected = list_rejected_logs(page=1, limit=10, db=db_session)
    assert "items" in rejected
    assert rejected["total_records"] >= 0

    stats = get_rejected_stats(db=db_session)
    assert "reasons_breakdown" in stats


def test_route_metrics_listing(db_session):
    metrics = list_metrics(limit=10, db=db_session)
    assert isinstance(metrics, list)


def test_route_synthetic_data_generation(db_session):
    req = GenerateRequest(count=50, format="json", anomaly_ratio=0.04, auto_ingest=True)
    res = generate_synthetic_data(payload=req, db=db_session)
    assert "Generated and ingested 50 records" in res["message"]
    assert res["pipeline_result"]["reconciliation"]["is_reconciled"] is True


def test_route_logs_stats_service_filtering(db_session):
    """Verify service filter strictly isolates errors and metrics to the queried service."""
    import uuid
    run_id = f"RUN_FILTER_{uuid.uuid4().hex[:6]}"
    tag = uuid.uuid4().hex[:6]
    csv_payload = f"""timestamp,severity,service,message,response_ms
2026-11-14T10:00:00Z,ERROR,auth,Auth failed {tag},100
2026-11-14T10:01:00Z,INFO,auth,Auth success {tag},110
2026-11-14T10:02:00Z,INFO,payment,Payment success {tag},200
2026-11-14T10:03:00Z,INFO,payment,Payment refunded {tag},210
"""
    PipelineService.process_log_file(csv_payload, "filter_test.csv", run_id=run_id, db=db_session)

    # 1. Stats filtered for payment: must have 0% error rate and 0 errors
    payment_stats = get_log_stats(run_id=run_id, service="payment", db=db_session)
    assert payment_stats["total_logs"] == 2
    assert payment_stats["error_rate_pct"] == 0.0
    assert payment_stats["severity_counts"]["ERROR"] == 0
    assert payment_stats["severity_counts"]["CRITICAL"] == 0
    assert payment_stats["severity_counts"]["INFO"] == 2

    # 2. Stats filtered for auth: must have 50% error rate and 1 error
    auth_stats = get_log_stats(run_id=run_id, service="auth", db=db_session)
    assert auth_stats["total_logs"] == 2
    assert auth_stats["error_rate_pct"] == 50.0
    assert auth_stats["severity_counts"]["ERROR"] == 1
    assert auth_stats["severity_counts"]["INFO"] == 1


def test_route_run_sample_datasets(db_session):
    """Verify that all 4 starter sample files execute via the API and reconcile."""
    for sample in ["sample_logs.csv", "sample_logs.json", "sample_logs.log", "quick_starter.json"]:
        res = run_sample_file(sample_name=sample, db=db_session)
        assert res["status"] in ("SUCCESS", "PARTIAL_SUCCESS")
        assert res["reconciliation"]["is_reconciled"] is True
        assert res["reconciliation"]["total_input_records"] > 0
