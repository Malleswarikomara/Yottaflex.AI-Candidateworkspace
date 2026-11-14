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
    LogSchemaError,
)
from app.services.metrics import compute_metrics_for_records, calculate_percentile


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
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end ingestion pipeline:
        1. Initialize PipelineRun record
        2. Detect format & parse content
        3. Validate, cleanse, and normalize
        4. Detect intra-batch duplicates and quarantine invalid records with reject_type
        5. Idempotent target publishing to database (track newly inserted vs previously skipped)
        6. Compute severity error rates, HTTP failure rates, and latency percentiles
        7. Audit reconciliation check: Input = Newly Inserted + Rejected + Previously Skipped
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
            newly_inserted_records=0,
            rejected_records=0,
            duplicate_records=0,
            previously_skipped_records=0,
            retry_count=retry_count,
            failure_reason=None,
            error_message=None,
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
            validated_record_count = 0

            # 3. Validation & Quarantine Loop
            for res in parse_results:
                if not res.is_parse_ok:
                    rejected_records.append({
                        "run_id": run_id,
                        "source_file": filename,
                        "raw_record": res.raw_record,
                        "reason": res.parse_error or "Parse error",
                        "reject_type": getattr(res, "reject_type", "MALFORMED"),
                        "rejected_at": datetime.now(timezone.utc),
                    })
                    continue

                try:
                    cleaned = validate_and_normalize_record(res.data, filename, run_id)
                    validated_record_count += 1
                    event_id = cleaned["event_id"]

                    if event_id in seen_event_ids:
                        intra_batch_duplicates += 1
                        rejected_records.append({
                            "run_id": run_id,
                            "source_file": filename,
                            "raw_record": res.raw_record,
                            "reason": f"Duplicate event_id within batch: {event_id}",
                            "reject_type": "DUPLICATE",
                            "rejected_at": datetime.now(timezone.utc),
                        })
                    else:
                        seen_event_ids.add(event_id)
                        valid_records.append(cleaned)

                except LogValidationError as e:
                    reject_type = getattr(e, "reject_type", "VALIDATION_ERROR")
                    rejected_records.append({
                        "run_id": run_id,
                        "source_file": filename,
                        "raw_record": res.raw_record,
                        "reason": str(e),
                        "reject_type": reject_type,
                        "rejected_at": datetime.now(timezone.utc),
                    })

            # 4. Target Publishing & Idempotent Deduplication
            # Differentiate newly inserted vs previously stored records
            previously_skipped_records = 0
            records_to_insert: List[Dict[str, Any]] = []

            if valid_records:
                incoming_ids = [r["event_id"] for r in valid_records]

                # Check existing event_ids in database using chunking
                existing_ids = set()
                chunk_size = 900
                for i in range(0, len(incoming_ids), chunk_size):
                    chunk = incoming_ids[i : i + chunk_size]
                    stmt = select(ApplicationLog.event_id).where(ApplicationLog.event_id.in_(chunk))
                    chunk_existing = db.execute(stmt).scalars().all()
                    existing_ids.update(chunk_existing)

                for r in valid_records:
                    if r["event_id"] in existing_ids:
                        # Existing event already in database from previous run: safe skip
                        previously_skipped_records += 1
                    else:
                        records_to_insert.append(r)

                # Batch insert newly discovered valid records
                if records_to_insert:
                    db.bulk_insert_mappings(ApplicationLog, records_to_insert)

            # Insert quarantined records
            if rejected_records:
                db.bulk_insert_mappings(RejectedLog, rejected_records)

            # 5. Compute Error Rate, HTTP Failure Rate, and Latency Metrics
            metric_entries = compute_metrics_for_records(valid_records, run_id)
            if metric_entries:
                db.bulk_insert_mappings(LogMetric, metric_entries)

            # 6. Audit Reconciliation Formula:
            # Input = Newly Inserted + Rejected + Previously Skipped
            newly_inserted_count = len(records_to_insert)
            rejected_count = len(rejected_records)
            accounted_for = newly_inserted_count + rejected_count + previously_skipped_records
            is_reconciled = (accounted_for == total_input_count)

            total_duplicates = intra_batch_duplicates + previously_skipped_records

            end_time = datetime.now(timezone.utc)
            duration_sec = round((end_time - start_time).total_seconds(), 3)

            # Determine final status
            if total_input_count == 0:
                final_status = "SUCCESS"
            elif rejected_count == 0 and (newly_inserted_count > 0 or previously_skipped_records > 0):
                final_status = "SUCCESS"
            elif (newly_inserted_count > 0 or previously_skipped_records > 0) and is_reconciled:
                final_status = "PARTIAL_SUCCESS"
            else:
                final_status = "FAILED"

            # 7. Update PipelineRun record
            pipeline_run.status = final_status
            pipeline_run.end_time = end_time
            pipeline_run.duration_seconds = duration_sec
            pipeline_run.total_input_records = total_input_count
            pipeline_run.valid_records = validated_record_count
            pipeline_run.newly_inserted_records = newly_inserted_count
            pipeline_run.rejected_records = rejected_count
            pipeline_run.duplicate_records = total_duplicates
            pipeline_run.previously_skipped_records = previously_skipped_records

            db.commit()

            # Global metrics rollup for response summary
            count_error = sum(1 for r in valid_records if r["severity"] == "ERROR")
            count_critical = sum(1 for r in valid_records if r["severity"] == "CRITICAL")
            total_sev_errors = count_error + count_critical
            sev_error_rate = round((total_sev_errors / len(valid_records) * 100.0), 2) if valid_records else 0.0

            http_reqs = [r for r in valid_records if r.get("http_status") is not None]
            http_fails = [r for r in http_reqs if isinstance(r.get("http_status"), int) and r["http_status"] >= 500]
            http_failure_rate = round((len(http_fails) / len(http_reqs) * 100.0), 2) if http_reqs else 0.0

            valid_latencies = [float(r["response_ms"]) for r in valid_records if r.get("response_ms") is not None]
            valid_with_latency_count = len(valid_latencies)
            null_latency_count = len(valid_records) - valid_with_latency_count
            total_latency_ms = round(sum(valid_latencies), 2) if valid_latencies else 0.0
            avg_latency = round(sum(valid_latencies) / valid_with_latency_count, 2) if valid_with_latency_count > 0 else None

            if valid_latencies:
                valid_latencies.sort()
                p50_latency = calculate_percentile(valid_latencies, 50)
                p95_latency = calculate_percentile(valid_latencies, 95)
                p99_latency = calculate_percentile(valid_latencies, 99)
            else:
                p50_latency = p95_latency = p99_latency = None

            return {
                "run_id": run_id,
                "status": final_status,
                "source_file": filename,
                "file_format": detected_format,
                "duration_seconds": duration_sec,
                "retry_count": retry_count,
                "reconciliation": {
                    "total_input_records": total_input_count,
                    "newly_inserted_records": newly_inserted_count,
                    "valid_records": validated_record_count,
                    "rejected_records": rejected_count,
                    "previously_skipped_records": previously_skipped_records,
                    "intra_batch_duplicates": intra_batch_duplicates,
                    "duplicate_records": total_duplicates,
                    "accounted_for": accounted_for,
                    "is_reconciled": is_reconciled,
                },
                "metrics_summary": {
                    "unique_valid_records": len(valid_records),
                    "valid_records": len(valid_records),
                    "newly_inserted": newly_inserted_count,
                    "previously_skipped": previously_skipped_records,
                    "error_count": count_error,
                    "critical_count": count_critical,
                    "severity_error_count": total_sev_errors,
                    "severity_error_rate_pct": sev_error_rate,
                    "error_rate_pct": sev_error_rate,
                    "http_request_count": len(http_reqs),
                    "http_failure_count": len(http_fails),
                    "http_failure_rate_pct": http_failure_rate,
                    "valid_records_with_latency": valid_with_latency_count,
                    "null_latency_records": null_latency_count,
                    "total_latency_ms": total_latency_ms,
                    "avg_latency_ms": avg_latency,
                    "p50_latency_ms": p50_latency,
                    "p95_latency_ms": p95_latency,
                    "p99_latency_ms": p99_latency,
                },
            }

        except Exception as exc:
            db.rollback()
            end_time = datetime.now(timezone.utc)
            pipeline_run.status = "FAILED"
            pipeline_run.end_time = end_time
            pipeline_run.duration_seconds = round((end_time - start_time).total_seconds(), 3)
            pipeline_run.failure_reason = str(exc)
            pipeline_run.error_message = str(exc)
            db.commit()
            raise exc

        finally:
            if should_close_db:
                db.close()
