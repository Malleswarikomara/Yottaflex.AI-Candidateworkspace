import math
import statistics
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_, case

from app.database.connection import get_db
from app.models.models import ApplicationLog
from app.services.metrics import calculate_percentile

router = APIRouter(prefix="/api/logs", tags=["Application Logs"])


@router.get("")
def list_logs(
    page: int = 1,
    limit: int = 50,
    severity: Optional[str] = None,
    service: Optional[str] = None,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    is_failure: Optional[bool] = None,
    min_response_ms: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    run_id: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_dir: str = "desc",
    db: Session = Depends(get_db)
):
    """Query cleaned, normalized application logs with comprehensive filtering."""
    query = db.query(ApplicationLog)

    if severity and isinstance(severity, str):
        sev_list = [s.strip().upper() for s in severity.split(",") if s.strip()]
        if sev_list:
            query = query.filter(ApplicationLog.severity.in_(sev_list))

    if service and isinstance(service, str):
        svc_list = [s.strip().lower() for s in service.split(",") if s.strip()]
        if svc_list:
            query = query.filter(ApplicationLog.service.in_(svc_list))

    if user_id and isinstance(user_id, str):
        query = query.filter(ApplicationLog.user_id.ilike(f"%{user_id}%"))

    if is_failure is not None and isinstance(is_failure, bool):
        query = query.filter(ApplicationLog.is_failure == is_failure)

    if min_response_ms is not None and isinstance(min_response_ms, (int, float)):
        query = query.filter(ApplicationLog.response_ms >= min_response_ms)

    if run_id and isinstance(run_id, str):
        query = query.filter(ApplicationLog.run_id == run_id)

    if start_date and isinstance(start_date, str):
        try:
            from dateutil import parser as dt_p
            s_dt = dt_p.parse(start_date)
            query = query.filter(ApplicationLog.timestamp >= s_dt)
        except Exception:
            pass

    if end_date and isinstance(end_date, str):
        try:
            from dateutil import parser as dt_p
            e_dt = dt_p.parse(end_date)
            query = query.filter(ApplicationLog.timestamp <= e_dt)
        except Exception:
            pass

    if search and isinstance(search, str):
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                ApplicationLog.message.ilike(search_pattern),
                ApplicationLog.event_id.ilike(search_pattern),
                ApplicationLog.user_id.ilike(search_pattern),
                ApplicationLog.endpoint.ilike(search_pattern),
            )
        )

    total_count = query.count()

    # Sorting
    sort_col = getattr(ApplicationLog, sort_by, ApplicationLog.timestamp)
    if str(sort_dir).lower() == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    offset = (page - 1) * limit
    logs = query.offset(offset).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total_records": total_count,
        "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1,
        "items": [log.to_dict() for log in logs]
    }


@router.get("/stats")
def get_log_stats(
    run_id: Optional[str] = None,
    service: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns core operational KPIs:
    - Total log records
    - Breakdown by severity (INFO, WARNING, ERROR, CRITICAL)
    - Severity Error rate % = ((ERROR + CRITICAL) / Total) * 100
    - HTTP Failure rate % = (HTTP status >= 500 / Total HTTP requests) * 100
    - Total failed requests (severity error or HTTP failure)
    - Latency statistics (Average, Min, Max, P50, P95, P99)
    - Breakdown by service
    """
    query = db.query(ApplicationLog)
    if run_id and isinstance(run_id, str):
        query = query.filter(ApplicationLog.run_id == run_id)
    if service and isinstance(service, str):
        query = query.filter(ApplicationLog.service == service.lower())

    total_logs = query.count()
    if total_logs == 0:
        return {
            "total_logs": 0,
            "error_rate_pct": 0.0,
            "http_request_count": 0,
            "http_failure_count": 0,
            "http_failure_rate_pct": 0.0,
            "failed_requests": 0,
            "severity_counts": {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0},
            "latency": {
                "avg_ms": None,
                "min_ms": None,
                "max_ms": None,
                "p50_ms": None,
                "p95_ms": None,
                "p99_ms": None,
            },
            "services_breakdown": [],
        }

    # Severity counts
    sev_filter = (ApplicationLog.run_id == run_id) if (run_id and isinstance(run_id, str)) else True
    sev_counts = dict(
        db.query(ApplicationLog.severity, func.count(ApplicationLog.event_id))
        .filter(sev_filter)
        .group_by(ApplicationLog.severity)
        .all()
    )

    info_c = sev_counts.get("INFO", 0)
    warn_c = sev_counts.get("WARNING", 0)
    err_c = sev_counts.get("ERROR", 0)
    crit_c = sev_counts.get("CRITICAL", 0)

    # Severity-based error rate = (ERROR + CRITICAL) / Total * 100
    error_rate_pct = round(((err_c + crit_c) / total_logs) * 100.0, 2)

    # HTTP request counts & failures
    http_req_query = query.filter(ApplicationLog.http_status.isnot(None))
    http_request_count = http_req_query.count()
    http_failure_count = http_req_query.filter(ApplicationLog.http_status >= 500).count()
    http_failure_rate_pct = (
        round((http_failure_count / http_request_count * 100.0), 2)
        if http_request_count > 0 else 0.0
    )

    # Total combined failed requests
    failed_c = query.filter(ApplicationLog.is_failure == True).count()

    # Latencies array for percentiles
    latencies = [
        float(val[0])
        for val in query.filter(ApplicationLog.response_ms.isnot(None))
        .with_entities(ApplicationLog.response_ms)
        .all()
    ]

    if latencies:
        latencies.sort()
        avg_lat = round(statistics.mean(latencies), 2)
        min_lat = round(latencies[0], 2)
        max_lat = round(latencies[-1], 2)
        p50_lat = calculate_percentile(latencies, 50)
        p95_lat = calculate_percentile(latencies, 95)
        p99_lat = calculate_percentile(latencies, 99)
    else:
        avg_lat = min_lat = max_lat = p50_lat = p95_lat = p99_lat = None

    # Service breakdown
    svc_groups = (
        db.query(
            ApplicationLog.service,
            func.count(ApplicationLog.event_id).label("total"),
            func.sum(case((ApplicationLog.severity == 'INFO', 1), else_=0)).label("info"),
            func.sum(case((ApplicationLog.severity == 'WARNING', 1), else_=0)).label("warn"),
            func.sum(case((ApplicationLog.severity == 'ERROR', 1), else_=0)).label("error"),
            func.sum(case((ApplicationLog.severity == 'CRITICAL', 1), else_=0)).label("crit"),
            func.sum(case((ApplicationLog.http_status.isnot(None), 1), else_=0)).label("http_total"),
            func.sum(case((ApplicationLog.http_status >= 500, 1), else_=0)).label("http_fail"),
            func.avg(ApplicationLog.response_ms).label("avg_resp"),
            func.max(ApplicationLog.response_ms).label("max_resp"),
        )
        .filter(sev_filter)
        .group_by(ApplicationLog.service)
        .all()
    )

    services_summary = []
    for s in svc_groups:
        s_tot = s.total or 0
        s_err = (s.error or 0) + (s.crit or 0)
        s_rate = round((s_err / s_tot * 100.0), 2) if s_tot > 0 else 0.0
        h_tot = s.http_total or 0
        h_fail = s.http_fail or 0
        h_rate = round((h_fail / h_tot * 100.0), 2) if h_tot > 0 else 0.0
        services_summary.append({
            "service": s.service,
            "total_logs": s_tot,
            "info_count": s.info or 0,
            "warning_count": s.warn or 0,
            "error_count": s.error or 0,
            "critical_count": s.crit or 0,
            "error_rate_pct": s_rate,
            "http_request_count": h_tot,
            "http_failure_count": h_fail,
            "http_failure_rate_pct": h_rate,
            "avg_latency_ms": round(float(s.avg_resp), 2) if s.avg_resp is not None else None,
            "max_latency_ms": round(float(s.max_resp), 2) if s.max_resp is not None else None,
        })

    return {
        "total_logs": total_logs,
        "error_rate_pct": error_rate_pct,
        "http_request_count": http_request_count,
        "http_failure_count": http_failure_count,
        "http_failure_rate_pct": http_failure_rate_pct,
        "failed_requests": failed_c,
        "severity_counts": {
            "INFO": info_c,
            "WARNING": warn_c,
            "ERROR": err_c,
            "CRITICAL": crit_c,
        },
        "latency": {
            "avg_ms": avg_lat,
            "min_ms": min_lat,
            "max_ms": max_lat,
            "p50_ms": p50_lat,
            "p95_ms": p95_lat,
            "p99_ms": p99_lat,
        },
        "services_breakdown": services_summary,
    }


@router.get("/latency-distribution")
def get_latency_distribution(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Returns histogram buckets of latencies for performance distribution charts."""
    query = db.query(ApplicationLog.response_ms).filter(ApplicationLog.response_ms.isnot(None))
    if run_id and isinstance(run_id, str):
        query = query.filter(ApplicationLog.run_id == run_id)

    latencies = [val[0] for val in query.all()]
    if not latencies:
        return {"buckets": [], "total_samples": 0}

    brackets = [
        ("0-100ms", 0, 100),
        ("100-300ms", 100, 300),
        ("300-500ms", 300, 500),
        ("500-1000ms", 500, 1000),
        ("1000-3000ms", 1000, 3000),
        (">3000ms", 3000, float("inf")),
    ]

    counts = {b[0]: 0 for b in brackets}
    for l in latencies:
        for label, low, high in brackets:
            if low <= l < high:
                counts[label] += 1
                break

    buckets = [{"range": k, "count": v, "percentage": round(v / len(latencies) * 100, 1)} for k, v in counts.items()]
    return {
        "buckets": buckets,
        "total_samples": len(latencies)
    }
