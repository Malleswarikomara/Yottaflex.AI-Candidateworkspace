from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.connection import get_db
from app.models.models import LogMetric

router = APIRouter(prefix="/api/metrics", tags=["Aggregated Metrics"])


@router.get("")
def list_metrics(
    run_id: Optional[str] = None,
    service: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Query pre-aggregated service metrics recorded across pipeline executions."""
    query = db.query(LogMetric)

    if run_id and isinstance(run_id, str):
        query = query.filter(LogMetric.run_id == run_id)
    if service and isinstance(service, str):
        query = query.filter(LogMetric.service == service.lower())

    results = query.order_by(desc(LogMetric.calculated_at)).limit(limit).all()
    return [m.to_dict() for m in results]
