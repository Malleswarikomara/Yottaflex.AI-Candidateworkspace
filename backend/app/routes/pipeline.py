import os
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.models import PipelineRun, ApplicationLog, RejectedLog
from app.services.pipeline import PipelineService
from app.services.generator import SyntheticLogGenerator

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline Operations"])


class GenerateRequest(BaseModel):
    count: int = 1000
    format: str = "json"  # "json", "csv", "text"
    anomaly_ratio: float = 0.03
    auto_ingest: bool = True


@router.post("/upload")
async def upload_log_file(
    file: UploadFile = File(...),
    run_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Ingest a log file (CSV, JSON, JSONL, or Semi-structured TEXT/LOG).
    Executes parsing, schema validation, quarantine, deduplication, and reconciliation.
    """
    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file content: {str(e)}")

    if not content.strip():
        # Handle empty file edge case
        result = PipelineService.process_log_file(
            content="",
            filename=file.filename,
            run_id=run_id,
            db=db
        )
        return result

    result = PipelineService.process_log_file(
        content=content,
        filename=file.filename,
        run_id=run_id,
        db=db
    )
    return result


@router.post("/run-sample")
def run_sample_file(
    sample_name: str = Query("sample_logs.csv", enum=["sample_logs.csv", "sample_logs.json", "sample_logs.log", "quick_starter.json"]),
    db: Session = Depends(get_db)
):
    """Executes the ingestion pipeline on one of the pre-generated sample files. Auto-generates if missing."""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    sample_dir = base_dir / "data" / "sample"
    sample_path = sample_dir / sample_name

    if not sample_path.exists():
        sample_dir.mkdir(parents=True, exist_ok=True)
        gen = SyntheticLogGenerator(seed=42)
        count = 100 if sample_name == "quick_starter.json" else 1000
        records = gen.generate_dataset(count=count, anomaly_ratio=0.03)
        if sample_name.endswith(".csv"):
            sample_content = gen.to_csv(records)
        elif sample_name.endswith(".log"):
            sample_content = gen.to_text_log(records)
        else:
            sample_content = gen.to_json(records, lines=False)
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write(sample_content)

    with open(sample_path, "r", encoding="utf-8") as f:
        content = f.read()

    result = PipelineService.process_log_file(
        content=content,
        filename=sample_name,
        db=db
    )
    return result


@router.post("/generate")
def generate_synthetic_data(
    payload: GenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generates synthetic log records with configurable volume and controlled anomalies.
    If auto_ingest is True, immediately processes the generated data through the pipeline.
    """
    if payload.count < 1 or payload.count > 200000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 200,000")

    gen = SyntheticLogGenerator(seed=42)
    records = gen.generate_dataset(count=payload.count, anomaly_ratio=payload.anomaly_ratio)

    fmt = payload.format.lower()
    if fmt == "csv":
        content = gen.to_csv(records)
        ext = "csv"
    elif fmt == "text":
        content = gen.to_text_log(records)
        ext = "log"
    else:
        content = gen.to_json(records, lines=False)
        ext = "json"

    filename = f"synthetic_{payload.count}_records.{ext}"

    # Save to data/input
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    input_dir = base_dir / "data" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    with open(input_dir / filename, "w", encoding="utf-8") as f:
        f.write(content)

    if payload.auto_ingest:
        result = PipelineService.process_log_file(
            content=content,
            filename=filename,
            db=db
        )
        return {
            "message": f"Generated and ingested {payload.count} records ({fmt.upper()})",
            "file_saved_at": str(input_dir / filename),
            "pipeline_result": result
        }

    return {
        "message": f"Generated {payload.count} records ({fmt.upper()}) without ingestion",
        "file_saved_at": str(input_dir / filename),
        "total_generated": len(records),
    }


@router.get("/runs")
def list_pipeline_runs(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists all pipeline execution runs, ordered by most recent."""
    runs = db.query(PipelineRun).order_by(desc(PipelineRun.start_time)).limit(limit).all()
    return [r.to_dict() for r in runs]


@router.get("/runs/{run_id}")
def get_pipeline_run_details(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve detailed execution status, reconciliation audit, and failure breakdown for a run."""
    run = db.query(PipelineRun).filter(PipelineRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    accounted = run.newly_inserted_records + run.rejected_records + run.previously_skipped_records
    reconciliation = {
        "total_input_records": run.total_input_records,
        "valid_records": run.valid_records,
        "newly_inserted_records": run.newly_inserted_records,
        "rejected_records": run.rejected_records,
        "duplicate_records": run.duplicate_records,
        "previously_skipped_records": run.previously_skipped_records,
        "accounted_for": accounted,
        "is_reconciled": (accounted == run.total_input_records),
    }

    return {
        "run": run.to_dict(),
        "reconciliation": reconciliation,
        "metrics": [m.to_dict() for m in run.metrics],
    }
