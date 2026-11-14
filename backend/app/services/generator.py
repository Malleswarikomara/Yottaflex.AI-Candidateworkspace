import random
import json
import csv
import io
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional


class SyntheticLogGenerator:
    """
    Generates realistic application log datasets with configurable volume,
    controlled error rates, and intentional edge-case anomalies for quality testing.
    Supports fixed random seeds for deterministic reproducibility.
    """

    SERVICES = ["auth", "payment", "api-gateway", "order-service", "inventory", "notification"]
    ENDPOINTS = {
        "auth": ["/api/v1/login", "/api/v1/refresh", "/api/v1/logout"],
        "payment": ["/api/v1/charge", "/api/v1/refund", "/api/v1/methods"],
        "api-gateway": ["/health", "/v1/proxy", "/metrics"],
        "order-service": ["/orders/checkout", "/orders/history", "/orders/cancel"],
        "inventory": ["/items/check", "/items/reserve", "/items/update"],
        "notification": ["/notify/email", "/notify/sms", "/notify/push"],
    }

    INFO_MESSAGES = [
        "User authenticated successfully",
        "Token refreshed for session",
        "Order placed with ID",
        "Inventory reserved for SKU",
        "Email receipt dispatched",
        "Health check probe passed",
        "Payment tokenized via provider",
    ]

    WARN_MESSAGES = [
        "Database pool connection threshold 85% reached",
        "API response time degraded above SLA",
        "Cache miss rate exceeded expected variance",
        "Rate limit quota nearing threshold",
        "Retry attempt 2 for external supplier gateway",
    ]

    ERROR_MESSAGES = [
        "Database query timeout after 5000ms",
        "Payment authorization declined by upstream processor",
        "Deadlock detected in inventory transaction lock",
        "Authentication token signature validation failed",
        "Connection reset by peer on microservice client",
    ]

    CRITICAL_MESSAGES = [
        "Database cluster primary node unreachable",
        "Payment vault encryption key unavailable",
        "Circuit breaker opened: all downstream calls rejected",
        "Fatal out of memory condition in worker pool",
    ]

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_record(
        self,
        base_time: datetime,
        idx: int,
        inject_anomaly: bool = False,
        scenario: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a single raw record dict with optional anomaly or specific scenario injection."""
        service = self.rng.choice(self.SERVICES)
        endpoint = self.rng.choice(self.ENDPOINTS[service])
        user_id = f"USR_{self.rng.randint(100, 999)}"
        event_id = f"EVT_{idx:06d}"
        
        # Default timestamp progression with natural variance
        timestamp = base_time + timedelta(seconds=self.rng.randint(0, 3600))

        # Explicit scenario override or randomized anomaly selection
        if scenario or inject_anomaly:
            chosen = scenario or self.rng.choice([
                "missing_timestamp",
                "invalid_timestamp",
                "invalid_severity",
                "missing_message",
                "missing_service",
                "negative_latency",
                "duplicate_id",
                "boundary_zero_latency",
                "boundary_high_latency",
                "late_arriving",
                "out_of_order",
                "null_optional_fields"
            ])

            if chosen == "missing_timestamp":
                return {
                    "event_id": event_id,
                    "timestamp": None,
                    "severity": "INFO",
                    "service": service,
                    "message": "Malformed record missing timestamp",
                    "response_ms": 120,
                    "user_id": user_id,
                }
            elif chosen == "invalid_timestamp":
                return {
                    "event_id": event_id,
                    "timestamp": "2026-99-99 99:99:99",
                    "severity": "ERROR",
                    "service": service,
                    "message": "Malformed record with garbage timestamp",
                    "response_ms": 500,
                    "user_id": user_id,
                }
            elif chosen == "invalid_severity":
                return {
                    "event_id": event_id,
                    "timestamp": timestamp.isoformat(),
                    "severity": "UNKNOWN_SEV_LEVEL",
                    "service": service,
                    "message": "Record with non-standard severity",
                    "response_ms": 200,
                    "user_id": user_id,
                }
            elif chosen == "missing_message":
                return {
                    "event_id": event_id,
                    "timestamp": timestamp.isoformat(),
                    "severity": "INFO",
                    "service": service,
                    "message": "",
                    "response_ms": 150,
                    "user_id": user_id,
                }
            elif chosen == "missing_service":
                return {
                    "event_id": event_id,
                    "timestamp": timestamp.isoformat(),
                    "severity": "INFO",
                    "service": "",
                    "message": "Record missing required service entity",
                    "response_ms": 110,
                    "user_id": user_id,
                }
            elif chosen == "negative_latency":
                return {
                    "event_id": event_id,
                    "timestamp": timestamp.isoformat(),
                    "severity": "INFO",
                    "service": service,
                    "message": "Invalid negative latency record",
                    "response_ms": -350.0,
                    "user_id": user_id,
                }
            elif chosen == "duplicate_id":
                # Injects deliberate duplicate keys to verify quarantine / skip handling
                dupe_idx = self.rng.randint(1, 5)
                return {
                    "event_id": f"EVT_DUPLICATE_KEY_{dupe_idx:03d}",
                    "timestamp": timestamp.isoformat(),
                    "severity": "WARNING",
                    "service": service,
                    "message": f"Duplicate key injection test {dupe_idx}",
                    "response_ms": 300,
                    "user_id": user_id,
                }
            elif chosen == "boundary_zero_latency":
                # Valid boundary value: exactly 0.0 ms
                return {
                    "event_id": event_id,
                    "timestamp": timestamp.isoformat(),
                    "severity": "INFO",
                    "service": service,
                    "message": "Sub-millisecond instant cached response",
                    "response_ms": 0.0,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "http_status": 200,
                }
            elif chosen == "boundary_high_latency":
                # Valid boundary value: high SLA breach latency (60,000 ms)
                return {
                    "event_id": event_id,
                    "timestamp": timestamp.isoformat(),
                    "severity": "ERROR",
                    "service": service,
                    "message": "Upstream gateway gateway timeout at boundary SLA limit",
                    "response_ms": 60000.0,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "http_status": 504,
                }
            elif chosen == "late_arriving":
                # Valid late-arriving log from 14 days ago
                late_time = base_time - timedelta(days=14, seconds=self.rng.randint(0, 3600))
                return {
                    "event_id": event_id,
                    "timestamp": late_time.isoformat(),
                    "severity": "INFO",
                    "service": service,
                    "message": "Late arriving event from mobile client cache",
                    "response_ms": 140.0,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "http_status": 200,
                }
            elif chosen == "out_of_order":
                # Valid event with timestamp jittered backwards by 2 hours
                jittered_time = base_time - timedelta(minutes=self.rng.randint(10, 120))
                return {
                    "event_id": event_id,
                    "timestamp": jittered_time.isoformat(),
                    "severity": "WARNING",
                    "service": service,
                    "message": "Out-of-order event arriving after buffer reordering",
                    "response_ms": 220.0,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "http_status": 200,
                }
            elif chosen == "null_optional_fields":
                # Valid event where optional fields (response_ms, user_id, endpoint, http_status) are null
                return {
                    "event_id": event_id,
                    "timestamp": timestamp.isoformat(),
                    "severity": "INFO",
                    "service": service,
                    "message": "Background cron worker execution with null optional fields",
                    "response_ms": None,
                    "user_id": None,
                    "endpoint": None,
                    "http_status": None,
                }

        # Normal record generation
        # Distribution: 75% INFO, 15% WARNING, 8% ERROR, 2% CRITICAL (Severity Error Rate ~ 10%)
        roll = self.rng.random()
        if roll < 0.75:
            severity = "INFO"
            message = self.rng.choice(self.INFO_MESSAGES)
            response_ms = round(self.rng.normalvariate(120, 30), 2)
            http_status = 200
        elif roll < 0.90:
            severity = "WARNING"
            message = self.rng.choice(self.WARN_MESSAGES)
            response_ms = round(self.rng.normalvariate(800, 150), 2)
            http_status = self.rng.choice([200, 429])
        elif roll < 0.98:
            severity = "ERROR"
            message = self.rng.choice(self.ERROR_MESSAGES)
            response_ms = round(self.rng.normalvariate(2500, 600), 2)
            http_status = self.rng.choice([500, 502, 504])
        else:
            severity = "CRITICAL"
            message = self.rng.choice(self.CRITICAL_MESSAGES)
            response_ms = round(self.rng.normalvariate(4500, 1000), 2)
            http_status = 503

        # Clamp response_ms >= 10ms for regular traffic
        response_ms = max(10.0, response_ms)

        # Occasional non-request log without latency (10% of records)
        if self.rng.random() < 0.10:
            response_ms = None
            endpoint = None
            http_status = None

        return {
            "event_id": event_id,
            "timestamp": timestamp.isoformat(),
            "severity": severity,
            "service": service,
            "message": message,
            "response_ms": response_ms,
            "user_id": user_id,
            "endpoint": endpoint,
            "http_status": http_status,
        }

    def generate_dataset(
        self,
        count: int = 1000,
        anomaly_ratio: float = 0.03
    ) -> List[Dict[str, Any]]:
        """
        Generate a list of raw record dictionaries.
        Includes normal data, boundary values, duplicate records, missing values,
        late or out-of-order data, and deliberately labelled invalid records.
        """
        base_time = datetime(2026, 11, 14, 10, 0, 0, tzinfo=timezone.utc)
        records = []
        anomaly_count = int(count * anomaly_ratio)

        for i in range(1, count + 1):
            is_anomaly = (i <= anomaly_count)
            rec = self.generate_record(base_time, i, inject_anomaly=is_anomaly)
            records.append(rec)

        # Shuffle to intersperse anomalies and out-of-order timestamps naturally
        self.rng.shuffle(records)
        return records

    def to_csv(self, records: List[Dict[str, Any]]) -> str:
        """Serialize records to CSV string."""
        if not records:
            return ""
        output = io.StringIO()
        fieldnames = ["event_id", "timestamp", "severity", "service", "message", "response_ms", "user_id", "endpoint", "http_status"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({k: (r.get(k) if r.get(k) is not None else "") for k in fieldnames})
        return output.getvalue()

    def to_json(self, records: List[Dict[str, Any]], lines: bool = False) -> str:
        """Serialize records to JSON array or JSON Lines."""
        if lines:
            return "\n".join(json.dumps(r) for r in records)
        return json.dumps(records, indent=2)

    def to_text_log(self, records: List[Dict[str, Any]]) -> str:
        """
        Serialize records to semi-structured application log lines:
        e.g., 2026-11-14 10:15:20 INFO User login successful user_id=101 service=auth response_ms=120
        """
        lines = []
        for r in records:
            ts = r.get("timestamp") or "MISSING_TS"
            if "T" in str(ts):
                ts = str(ts).replace("T", " ")[:19]
            sev = r.get("severity") or "UNKNOWN"
            msg = r.get("message") or ""
            service = r.get("service") or "app"
            uid = r.get("user_id")
            resp = r.get("response_ms")
            evt = r.get("event_id")

            parts = [f"{ts} {sev} {msg}"]
            if uid:
                parts.append(f"user_id={uid}")
            if service:
                parts.append(f"service={service}")
            if resp is not None:
                parts.append(f"response_ms={resp}")
            if evt:
                parts.append(f"event_id={evt}")

            lines.append(" ".join(parts))
        return "\n".join(lines)


def generate_logs(count: int = 100000, seed: int = 42, anomaly_ratio: float = 0.03) -> List[Dict[str, Any]]:
    """
    Convenience function to generate reproducible log datasets with a fixed seed.
    Supports small starter batches (e.g., 100) or high-volume scalability runs (100,000+).
    """
    gen = SyntheticLogGenerator(seed=seed)
    return gen.generate_dataset(count=count, anomaly_ratio=anomaly_ratio)
