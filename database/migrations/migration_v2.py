import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from sqlalchemy import text, inspect
from app.database.connection import engine, Base


def run_migration():
    """Migrate database schema to v2 by adding new tracking columns and constraints."""
    print("Running database schema migration to v2...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.begin() as conn:
        # 1. Pipeline Runs columns
        if "pipeline_runs" in existing_tables:
            pr_cols = [c["name"] for c in inspector.get_columns("pipeline_runs")]
            if "newly_inserted_records" not in pr_cols:
                conn.execute(text("ALTER TABLE pipeline_runs ADD COLUMN newly_inserted_records INTEGER DEFAULT 0"))
            if "previously_skipped_records" not in pr_cols:
                conn.execute(text("ALTER TABLE pipeline_runs ADD COLUMN previously_skipped_records INTEGER DEFAULT 0"))
            if "retry_count" not in pr_cols:
                conn.execute(text("ALTER TABLE pipeline_runs ADD COLUMN retry_count INTEGER DEFAULT 0"))
            if "failure_reason" not in pr_cols:
                conn.execute(text("ALTER TABLE pipeline_runs ADD COLUMN failure_reason TEXT"))

        # 2. Rejected Logs columns
        if "rejected_logs" in existing_tables:
            rej_cols = [c["name"] for c in inspector.get_columns("rejected_logs")]
            if "reject_type" not in rej_cols:
                conn.execute(text("ALTER TABLE rejected_logs ADD COLUMN reject_type VARCHAR(50) DEFAULT 'VALIDATION_ERROR'"))

        # 3. Log Metrics columns
        if "log_metrics" in existing_tables:
            met_cols = [c["name"] for c in inspector.get_columns("log_metrics")]
            if "http_request_count" not in met_cols:
                conn.execute(text("ALTER TABLE log_metrics ADD COLUMN http_request_count INTEGER DEFAULT 0"))
            if "http_failure_count" not in met_cols:
                conn.execute(text("ALTER TABLE log_metrics ADD COLUMN http_failure_count INTEGER DEFAULT 0"))
            if "http_failure_rate_pct" not in met_cols:
                conn.execute(text("ALTER TABLE log_metrics ADD COLUMN http_failure_rate_pct FLOAT DEFAULT 0.0"))

    # Create any missing tables defined in models
    Base.metadata.create_all(bind=engine)
    print("Database migration v2 completed successfully.")


def reset_and_recreate_db():
    """Drops and recreates all tables cleanly according to the updated schema."""
    print("Dropping and recreating all tables cleanly...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Fresh database schema created successfully.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_and_recreate_db()
    else:
        run_migration()
