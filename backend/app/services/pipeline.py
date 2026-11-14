import uuid
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.models import PipelineRun, ApplicationLog, RejectedLog, LogMetric
from app.parsers.factory import ParserFactory
from app.validators.normalizers import (
    validate_and_normalize_record,
    LogValidationError,
)
from app.services.metrics import compute_metrics_for_records


class PipelineService:
    """Core orchestration service for log ingestion, validation, publishing, and reconciliation."""

    @staticmethod
    def generate_run_id() -> str:
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:6].upper()
        return f"RUN_{now_str}_{uid}"

    @classmethod
    def process_log_file(
        cls,
        content: str,
        filename: str,
        run_id: Optional[str] = None,
        db: Optional[Session] = None,
        batch_size: int = 5000,
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end ingestion pipeline:
        1. Initialize Run record
        2. Detect format & parse content
        3. Validate, cleanse, and normalize
        4. Detect intra-batch duplicates and quarantine invalid records
        5. Idempotent target publishing to database
        6. Compute error rate & latency metrics
        7. Audit reconciliation check
        """
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True

        if not run_id:
            run_id = cls.generate_run_id()

        start_time = datetime.now(timezone.utc)
        parser, detected_format = ParserFactory.get_parser(filename, content)

        # 1. Initialize PipelineRun record
        pipeline_run = PipelineRun(
            run_id=run_id,
            source_file=filename,
            file_format=detected_format,
            status="RUNNING",
            start_time=start_time,
            total_input_records=0,
            valid_records=0,
            rejected_records=0,
            duplicate_records=0,
        )
        db.add(pipeline_run)
        db.commit()

        try:
            # 2. Parse Raw Records
            parse_results = parser.parse_content(content)
            total_input_count = len(parse_results)

            valid_records: List[Dict[str, Any]] = []
            rejected_records: List[Dict[str, Any]] = []
            seen_event_ids: set = set()
            intra_batch_duplicates = 0

            # 3. Validation & Quarantine Loop
            for res in parse_results:
                if not res.is_parse_ok:
                    rejected_records.append({
                        "run_id": run_id,
                        "source_file": filename,
                        "raw_record": res.raw_record[:1000],
                        "reason": res.parse_error or "Parse error",
                        "rejected_at": datetime.now(timezone.utc),
                    })
                    continue

                try:
                    cleaned = validate_and_normalize_record(res.data, filename, run_id)
                    event_id = cleaned["event_id"]

                    if event_id in seen_event_ids:
                        intra_batch_duplicates += 1
                        rejected_records.append({
                            "run_id": run_id,
                            "source_file": filename,
                            "raw_record": res.raw_record[:1000],
                            "reason": f"Duplicate event_id within batch: {event_id}",
                            "rejected_at": datetime.now(timezone.utc),
                        })
                    else:
                        seen_event_ids.add(event_id)
                        valid_records.append(cleaned)

                except LogValidationError as e:
                    rejected_records.append({
                        "run_id": run_id,
                        "source_file": filename,
                        "raw_record": res.raw_record[:1000],
                        "reason": str(e),
                        "rejected_at": datetime.now(timezone.utc),
                    })

            # 4. Target Publishing & Idempotency
            # Query existing event_ids in DB to prevent unique constraint crash on rerun
            db_duplicate_count = 0
            records_to_insert: List[Dict[str, Any]] = []

            if valid_records:
                incoming_ids = [r["event_id"] for r in valid_records]
                
                # Check in chunks to prevent SQLite variable limit
                existing_ids = set()
                chunk_size = 900
                for i in range(0, len(incoming_ids), chunk_size):
                    chunk = incoming_ids[i : i + chunk_size]
                    stmt = select(ApplicationLog.event_id).where(ApplicationLog.event_id.in_(chunk))
                    chunk_existing = db.execute(stmt).scalars().all()
                    existing_ids.update(chunk_existing)

                for r in valid_records:
                    if r["event_id"] in existing_ids:
                        db_duplicate_count += 1
                        # Safe idempotent handling: record already present from previous run
                    else:
                        records_to_insert.append(r)

                # Batch insert into application_logs
                if records_to_insert:
                    db.bulk_insert_mappings(ApplicationLog, records_to_insert)

            # Insert rejected records
            if rejected_records:
                db.bulk_insert_mappings(RejectedLog, rejected_records)

            # 5. Compute Error Rate & Latency Metrics
            metric_entries = compute_metrics_for_records(valid_records, run_id)
            if metric_entries:
                db.bulk_insert_mappings(LogMetric, metric_entries)

            # 6. Audit Reconciliation
            end_time = datetime.now(timezone.utc)
            duration_sec = round((end_time - start_time).total_seconds(), 3)
            valid_count = len(valid_records)
            rejected_count = len(rejected_records)
            total_duplicate_count = intra_batch_duplicates + db_duplicate_count

            is_reconciled = (valid_count + rejected_count) == total_input_count

            # Determine final status
            if total_input_count == 0:
                final_status = "SUCCESS"
            elif rejected_count == 0 and db_duplicate_count == 0:
                final_status = "SUCCESS"
            elif valid_count > 0:
                final_status = "PARTIAL_SUCCESS"
            else:
                final_status = "FAILED"

            # 7. Update PipelineRun record
            pipeline_run.status = final_status
            pipeline_run.end_time = end_time
            pipeline_run.duration_seconds = duration_sec
            pipeline_run.total_input_records = total_input_count
            pipeline_run.valid_records = valid_count
            pipeline_run.rejected_records = rejected_count
            pipeline_run.duplicate_records = total_duplicate_count

            db.commit()

            # Global metrics rollup for summary
            total_errors = sum(1 for r in valid_records if r["severity"] in ("ERROR", "CRITICAL"))
            error_rate_pct = round((total_errors / valid_count * 100.0), 2) if valid_count > 0 else 0.0

            valid_latencies = [r["response_ms"] for r in valid_records if r.get("response_ms") is not None]
            avg_latency = round(sum(valid_latencies) / len(valid_latencies), 2) if valid_latencies else None

            return {
                "run_id": run_id,
                "status": final_status,
                "source_file": filename,
                "file_format": detected_format,
                "duration_seconds": duration_sec,
                "reconciliation": {
                    "total_input_records": total_input_count,
                    "valid_records": valid_count,
                    "rejected_records": rejected_count,
                    "accounted_for": valid_count + rejected_count,
                    "is_reconciled": is_reconciled,
                    "intra_batch_duplicates": intra_batch_duplicates,
                    "db_duplicates_skipped": db_duplicate_count,
                    "newly_inserted_logs": len(records_to_insert),
                },
                "metrics_summary": {
                    "valid_records": valid_count,
                    "total_errors": total_errors,
                    "error_rate_pct": error_rate_pct,
                    "avg_latency_ms": avg_latency,
                },
            }

        except Exception as exc:
            db.rollback()
            end_time = datetime.now(timezone.utc)
            pipeline_run.status = "FAILED"
            pipeline_run.end_time = end_time
            pipeline_run.duration_seconds = round((end_time - start_time).total_seconds(), 3)
            pipeline_run.error_message = str(exc)
            db.commit()
            raise exc

        finally:
            if should_close_db:
                db.close()
