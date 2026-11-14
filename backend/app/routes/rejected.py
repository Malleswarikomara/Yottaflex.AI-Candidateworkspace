from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database.connection import get_db
from app.models.models import RejectedLog

router = APIRouter(prefix="/api/rejected", tags=["Quarantined Records"])


@router.get("")
def list_rejected_logs(
    page: int = 1,
    limit: int = 50,
    run_id: Optional[str] = None,
    reason: Optional[str] = None,
    reject_type: Optional[str] = None,
    source_file: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve quarantined rejected records with source traceability and reason inspection."""
    query = db.query(RejectedLog)

    if run_id and isinstance(run_id, str):
        query = query.filter(RejectedLog.run_id == run_id)

    if reason and isinstance(reason, str):
        query = query.filter(RejectedLog.reason.ilike(f"%{reason}%"))

    if reject_type and isinstance(reject_type, str):
        query = query.filter(RejectedLog.reject_type == reject_type.upper())

    if source_file and isinstance(source_file, str):
        query = query.filter(RejectedLog.source_file.ilike(f"%{source_file}%"))

    total_count = query.count()
    offset = (page - 1) * limit
    logs = query.order_by(desc(RejectedLog.rejected_at)).offset(offset).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total_records": total_count,
        "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1,
        "items": [log.to_dict() for log in logs]
    }


@router.get("/stats")
def get_rejected_stats(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Returns frequency distribution of rejection reasons and reject types for data quality analytics."""
    query = db.query(RejectedLog)
    if run_id and isinstance(run_id, str):
        query = query.filter(RejectedLog.run_id == run_id)

    total_rejected = query.count()

    reason_filter = (RejectedLog.run_id == run_id) if (run_id and isinstance(run_id, str)) else True

    # Rejection Reasons Breakdown
    reason_groups = (
        db.query(RejectedLog.reason, func.count(RejectedLog.reject_id).label("count"))
        .filter(reason_filter)
        .group_by(RejectedLog.reason)
        .order_by(desc("count"))
        .all()
    )

    # Rejection Types Breakdown (MALFORMED, VALIDATION_ERROR, DUPLICATE, SCHEMA_ERROR)
    type_groups = (
        db.query(RejectedLog.reject_type, func.count(RejectedLog.reject_id).label("count"))
        .filter(reason_filter)
        .group_by(RejectedLog.reject_type)
        .order_by(desc("count"))
        .all()
    )

    reasons_breakdown = [
        {
            "reason": r.reason,
            "count": r.count,
            "percentage": round((r.count / total_rejected * 100.0), 1) if total_rejected > 0 else 0.0
        }
        for r in reason_groups
    ]

    types_breakdown = [
        {
            "type": t.reject_type or "VALIDATION_ERROR",
            "count": t.count,
            "percentage": round((t.count / total_rejected * 100.0), 1) if total_rejected > 0 else 0.0
        }
        for t in type_groups
    ]

    return {
        "total_rejected": total_rejected,
        "reasons_breakdown": reasons_breakdown,
        "types_breakdown": types_breakdown,
    }
