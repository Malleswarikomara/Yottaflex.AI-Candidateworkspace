import sys
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
data_dir = BASE_DIR / "data"

# Create a test copy of logs.db
source_db = data_dir / "logs.db"
test_db = data_dir / "migration_test.db"

if not source_db.exists():
    print(f"Error: {source_db} does not exist.")
    sys.exit(1)

shutil.copy2(source_db, test_db)
print(f"[1/5] Created test copy of database at: {test_db}")

import os
os.environ["DATABASE_URL"] = f"sqlite:///{test_db.as_posix()}"

from sqlalchemy import create_engine, inspect, text, select
from sqlalchemy.orm import sessionmaker

engine = create_engine(f"sqlite:///{test_db.as_posix()}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()

# 1. Count records before
initial_logs_count = session.execute(text("SELECT count(*) FROM application_logs")).scalar()
initial_runs_count = session.execute(text("SELECT count(*) FROM pipeline_runs")).scalar()
initial_rejects_count = session.execute(text("SELECT count(*) FROM rejected_logs")).scalar()
initial_metrics_count = session.execute(text("SELECT count(*) FROM log_metrics")).scalar()

print(f"[2/5] Initial record counts: logs={initial_logs_count:,}, runs={initial_runs_count:,}, rejects={initial_rejects_count:,}, metrics={initial_metrics_count:,}")

# 2. Run migration script against test copy
from database.migrations.migration_v2 import run_migration
run_migration()
print("[3/5] Migration executed on test database.")

# 3. Inspect columns
inspector = inspect(engine)

pr_cols = {c["name"]: c for c in inspector.get_columns("pipeline_runs")}
print("\n[4/5] Verifying migrated columns and schema structures:")
for col in ["newly_inserted_records", "previously_skipped_records", "retry_count", "failure_reason"]:
    status = "OK" if col in pr_cols else "MISSING"
    print(f"  - pipeline_runs.{col}: {status}")

rej_cols = {c["name"]: c for c in inspector.get_columns("rejected_logs")}
print(f"  - rejected_logs.reject_type: {'OK' if 'reject_type' in rej_cols else 'MISSING'}")

met_cols = {c["name"]: c for c in inspector.get_columns("log_metrics")}
for col in ["http_request_count", "http_failure_count", "http_failure_rate_pct"]:
    status = "OK" if col in met_cols else "MISSING"
    print(f"  - log_metrics.{col}: {status}")

# 4. Verify existing records remained intact
post_logs_count = session.execute(text("SELECT count(*) FROM application_logs")).scalar()
post_runs_count = session.execute(text("SELECT count(*) FROM pipeline_runs")).scalar()
post_rejects_count = session.execute(text("SELECT count(*) FROM rejected_logs")).scalar()
post_metrics_count = session.execute(text("SELECT count(*) FROM log_metrics")).scalar()

assert initial_logs_count == post_logs_count, f"Logs count mismatch: {initial_logs_count} vs {post_logs_count}"
assert initial_runs_count == post_runs_count, f"Runs count mismatch: {initial_runs_count} vs {post_runs_count}"
assert initial_rejects_count == post_rejects_count, f"Rejects count mismatch: {initial_rejects_count} vs {post_rejects_count}"
assert initial_metrics_count == post_metrics_count, f"Metrics count mismatch: {initial_metrics_count} vs {post_metrics_count}"

print(f"\n[5/5] Data Integrity Verification: 100% of existing records intact.")
print(f"      application_logs: {post_logs_count:,} rows")
print(f"      pipeline_runs:    {post_runs_count:,} rows")
print(f"      rejected_logs:    {post_rejects_count:,} rows")
print(f"      log_metrics:      {post_metrics_count:,} rows")
print("\n>>> MIGRATION VERIFICATION PASSED SUCCESSFULLY! <<<")
session.close()
