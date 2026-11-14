import math
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


def calculate_percentile(sorted_values: List[float], p: float) -> Optional[float]:
    """Calculate the p-th percentile of a sorted list of numbers (linear interpolation)."""
    if not sorted_values:
        return None
    n = len(sorted_values)
    if n == 1:
        return round(sorted_values[0], 2)
    k = (n - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(sorted_values[int(k)], 2)
    d = k - f
    val = sorted_values[f] + d * (sorted_values[c] - sorted_values[f])
    return round(val, 2)


def compute_metrics_for_records(
    valid_records: List[Dict[str, Any]],
    run_id: str
) -> List[Dict[str, Any]]:
    """
    Compute error rate and latency statistics overall and per-service.
    Returns a list of metric dictionaries ready for LogMetric model insertion.
    """
    if not valid_records:
        return []

    # Group valid records by service
    by_service: Dict[str, List[Dict[str, Any]]] = {}
    for r in valid_records:
        svc = r.get("service") or "app"
        by_service.setdefault(svc, []).append(r)

    metrics_list: List[Dict[str, Any]] = []

    # Compute for each service
    for svc, records in by_service.items():
        total_logs = len(records)
        info_count = sum(1 for r in records if r["severity"] == "INFO")
        warning_count = sum(1 for r in records if r["severity"] == "WARNING")
        error_count = sum(1 for r in records if r["severity"] == "ERROR")
        critical_count = sum(1 for r in records if r["severity"] == "CRITICAL")

        failed_requests = sum(1 for r in records if r.get("is_failure"))
        error_rate_pct = ((error_count + critical_count) / total_logs * 100.0) if total_logs > 0 else 0.0

        # Latencies
        latencies = [
            float(r["response_ms"])
            for r in records
            if r.get("response_ms") is not None
        ]

        if latencies:
            latencies.sort()
            avg_lat = round(statistics.mean(latencies), 2)
            p50_lat = calculate_percentile(latencies, 50)
            p95_lat = calculate_percentile(latencies, 95)
            p99_lat = calculate_percentile(latencies, 99)
            max_lat = round(latencies[-1], 2)
        else:
            avg_lat = p50_lat = p95_lat = p99_lat = max_lat = None

        metrics_list.append({
            "run_id": run_id,
            "service": svc,
            "total_logs": total_logs,
            "info_count": info_count,
            "warning_count": warning_count,
            "error_count": error_count,
            "critical_count": critical_count,
            "failed_requests": failed_requests,
            "error_rate_pct": round(error_rate_pct, 2),
            "avg_latency_ms": avg_lat,
            "p50_latency_ms": p50_lat,
            "p95_latency_ms": p95_lat,
            "p99_latency_ms": p99_lat,
            "max_latency_ms": max_lat,
            "calculated_at": datetime.now(timezone.utc),
        })

    return metrics_list
