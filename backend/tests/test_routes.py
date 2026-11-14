import pytest
from app.database.connection import SessionLocal
from app.routes.pipeline import list_pipeline_runs, get_pipeline_run_details, generate_synthetic_data, GenerateRequest
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
