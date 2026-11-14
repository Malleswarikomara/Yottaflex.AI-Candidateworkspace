import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database.connection import Base
from app.models import models
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
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    db = TestingSessionLocal()
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
    # Create test run so test does not depend on external or prior state
    PipelineService.process_log_file(
        "timestamp,severity,message\n2026-11-14T10:00:00Z,INFO,Listing test",
        "listing_test.csv",
        db=db_session
    )
    runs = list_pipeline_runs(limit=10, db=db_session)
    assert isinstance(runs, list)
    assert len(runs) > 0
    assert "run_id" in runs[0]
    assert "reconciled" in str(runs[0].keys()).lower() or "valid_records" in runs[0]


def test_route_pipeline_run_details(db_session):
    res = PipelineService.process_log_file(
        "timestamp,severity,message\n2026-11-14T10:00:00Z,INFO,Detail test",
        "detail_test.csv",
        db=db_session
    )
    run_id = res["run_id"]
    details = get_pipeline_run_details(run_id=run_id, db=db_session)
    assert details["run"]["run_id"] == run_id
    assert details["reconciliation"]["is_reconciled"] is True


def test_route_logs_listing_and_filtering(db_session):
    PipelineService.process_log_file(
        "timestamp,severity,message\n2026-11-14T10:00:00Z,INFO,Log listing test",
        "listing_logs.csv",
        db=db_session
    )
    res = list_logs(page=1, limit=20, severity="INFO", db=db_session)
    assert res["page"] == 1
    assert "items" in res
    assert len(res["items"]) > 0
    for item in res["items"]:
        assert item["severity"] == "INFO"


def test_route_logs_stats(db_session):
    # Ingest test records to guarantee deterministic isolated calculation
    PipelineService.process_log_file(
        "timestamp,severity,message,response_ms\n2026-11-14T10:00:00Z,INFO,Stats test,150",
        "stats_test.csv",
        db=db_session
    )
    stats = get_log_stats(db=db_session)
    assert stats["total_logs"] > 0
    assert stats["error_rate_pct"] >= 0.0
    assert "severity_counts" in stats
    assert "latency" in stats


def test_route_latency_distribution(db_session):
    PipelineService.process_log_file(
        "timestamp,severity,message,response_ms\n2026-11-14T10:00:00Z,INFO,Lat test,250",
        "lat_test.csv",
        db=db_session
    )
    dist = get_latency_distribution(db=db_session)
    assert "buckets" in dist
    assert dist["total_samples"] >= 0


def test_route_rejected_logs(db_session):
    # Ingest negative latency to generate a quarantined rejection
    PipelineService.process_log_file(
        "timestamp,severity,message,response_ms\n2026-11-14T10:00:00Z,INFO,Rej test,-100",
        "rej_test.csv",
        db=db_session
    )
    rejected = list_rejected_logs(page=1, limit=10, db=db_session)
    assert "items" in rejected
    assert rejected["total_records"] > 0

    stats = get_rejected_stats(db=db_session)
    assert "reasons_breakdown" in stats


def test_route_metrics_listing(db_session):
    PipelineService.process_log_file(
        "timestamp,severity,message\n2026-11-14T10:00:00Z,INFO,Metric test",
        "metric_test.csv",
        db=db_session
    )
    metrics = list_metrics(limit=10, db=db_session)
    assert isinstance(metrics, list)
    assert len(metrics) > 0


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


def test_route_run_sample_datasets():
    """Verify that all 4 starter sample files execute via API, reconcile, and satisfy idempotent rerun."""
    for sample in ["sample_logs.csv", "sample_logs.json", "sample_logs.log", "quick_starter.json"]:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

        @event.listens_for(engine, "connect")
        def enable_fk(conn, rec):
            c = conn.cursor()
            c.execute("PRAGMA foreign_keys=ON")
            c.close()

        Base.metadata.create_all(bind=engine)
        TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        db = TestingSession()

        try:
            # Run 1: Fresh execution
            res1 = run_sample_file(sample_name=sample, db=db)
            assert res1["status"] in ("SUCCESS", "PARTIAL_SUCCESS")
            assert res1["run_id"] is not None
            assert res1["reconciliation"]["is_reconciled"] is True
            assert res1["reconciliation"]["total_input_records"] > 0
            assert res1["reconciliation"]["newly_inserted_records"] > 0
            assert res1["reconciliation"]["previously_skipped_records"] == 0

            # Verify records are queryable in logs API
            logs_res = list_logs(run_id=res1["run_id"], limit=5, db=db)
            assert logs_res["total_records"] == res1["reconciliation"]["newly_inserted_records"]
            assert len(logs_res["items"]) > 0

            # Run 2: Idempotent rerun on same DB session must NOT create duplicate target records
            res2 = run_sample_file(sample_name=sample, db=db)
            assert res2["status"] in ("SUCCESS", "PARTIAL_SUCCESS")
            assert res2["reconciliation"]["is_reconciled"] is True
            assert res2["reconciliation"]["newly_inserted_records"] == 0
            assert res2["reconciliation"]["previously_skipped_records"] == res1["reconciliation"]["newly_inserted_records"]
        finally:
            db.close()
