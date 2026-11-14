import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.database.connection import SessionLocal
from app.routes.pipeline import list_pipeline_runs, get_pipeline_run_details
from app.routes.logs import list_logs, get_log_stats, get_latency_distribution
from app.routes.rejected import list_rejected_logs, get_rejected_stats
from app.routes.metrics import list_metrics
from app.main import health_check, system_info

def verify_all_tabs():
    db = SessionLocal()
    try:
        print("=" * 70)
        print("MANUAL VERIFICATION OF DASHBOARD DATA & TAB QUERIES")
        print("=" * 70)

        # Tab 1: Overview Tab
        health = health_check()
        print(f"[Tab 1 - Overview] Health: {health['status']}")
        stats = get_log_stats(run_id=None, service=None, db=db)
        print(f"[Tab 1 - Overview] Total Ingested Logs:  {stats['total_logs']:,}")
        print(f"[Tab 1 - Overview] Severity Error Rate:  {stats['error_rate_pct']}%  ((Error+Crit) / Total)")
        print(f"[Tab 1 - Overview] HTTP Failure Rate:    {stats['http_failure_rate_pct']}%  (HTTP 5xx / HTTP Requests)")
        print(f"[Tab 1 - Overview] HTTP Failures:        {stats['http_failure_count']:,} / {stats['http_request_count']:,} requests")
        print(f"[Tab 1 - Overview] Latency (Avg/P95):    {stats['latency']['avg_ms']} ms / {stats['latency']['p95_ms']} ms")
        assert "error_rate_pct" in stats and "http_failure_rate_pct" in stats

        # Tab 2: Log Explorer Tab
        logs = list_logs(page=1, limit=5, severity=None, service=None, search=None, db=db)
        print(f"\n[Tab 2 - Log Explorer] Retrieved {len(logs['items'])} logs (Total in DB: {logs['total_records']:,})")
        assert len(logs["items"]) > 0

        # Tab 3: Performance Analytics Tab
        lat_dist = get_latency_distribution(run_id=None, db=db)
        print(f"\n[Tab 3 - Performance] Latency distribution: {len(lat_dist['buckets'])} histogram buckets (samples: {lat_dist['total_samples']:,})")
        print(f"[Tab 3 - Performance] P50 / P95 / P99: {stats['latency']['p50_ms']} ms / {stats['latency']['p95_ms']} ms / {stats['latency']['p99_ms']} ms")
        assert len(lat_dist["buckets"]) > 0

        # Tab 4: Data Quality & Quarantine Tab
        rej_stats = get_rejected_stats(run_id=None, db=db)
        print(f"\n[Tab 4 - Data Quality] Total Quarantined: {rej_stats['total_rejected']:,}")
        print("[Tab 4 - Data Quality] Breakdown by reject_type:")
        for t in rej_stats.get("reject_types_breakdown", []):
            print(f"       - {t['type']}: {t['count']:,} records ({t['percentage']}%)")
        assert "reject_types_breakdown" in rej_stats

        # Tab 5: Pipeline Monitoring Tab
        runs = list_pipeline_runs(limit=5, db=db)
        print(f"\n[Tab 5 - Pipeline Monitoring] Historical runs count: {len(runs)}")
        latest = runs[0]
        print(f"[Tab 5 - Pipeline Monitoring] Latest Run {latest['run_id']}:")
        print(f"       - Status:            {latest['status']}")
        print(f"       - Total Input:       {latest['total_input_records']:,}")
        print(f"       - Newly Inserted:    {latest.get('newly_inserted_records', latest.get('valid_records')):,}")
        print(f"       - Quarantined:       {latest['rejected_records']:,}")
        print(f"       - Previously Skipped:{latest.get('previously_skipped_records', 0):,}")
        print(f"       - Retries:           {latest.get('retry_count', 0)}")
        print(f"       - Reconciled:        {latest.get('is_reconciled')}")
        assert latest.get("is_reconciled") is True

        print("=" * 70)
        print("ALL FIVE DASHBOARD TABS AND DATA MODELS VERIFIED WITH ZERO ERRORS!")
        print("=" * 70)
    finally:
        db.close()

if __name__ == "__main__":
    verify_all_tabs()
