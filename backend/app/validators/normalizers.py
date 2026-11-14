import re
import hashlib
from datetime import datetime, timezone
from dateutil import parser as date_parser
from typing import Optional, Tuple, Any, Dict


class LogValidationError(Exception):
    """Custom exception raised when a log record fails validation."""
    def __init__(self, message: str, reject_type: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.message = message
        self.reject_type = reject_type


class LogSchemaError(LogValidationError):
    """Custom exception raised when a log record fails schema requirements."""
    def __init__(self, message: str):
        super().__init__(message, reject_type="SCHEMA_ERROR")


# Severity mapping dictionary
SEVERITY_MAP = {
    "INFO": "INFO",
    "INF": "INFO",
    "I": "INFO",
    "INFORMATION": "INFO",
    "WARN": "WARNING",
    "WARNING": "WARNING",
    "W": "WARNING",
    "ERR": "ERROR",
    "ERROR": "ERROR",
    "E": "ERROR",
    "CRIT": "CRITICAL",
    "CRITICAL": "CRITICAL",
    "FATAL": "CRITICAL",
    "C": "CRITICAL",
    "F": "CRITICAL",
}


def normalize_timestamp(raw_val: Any) -> datetime:
    """
    Parse and normalize any timestamp into a timezone-aware UTC datetime.
    Supports ISO-8601, Common Log format, RFC 2822, and numeric Unix epochs.
    Older (late-arriving) timestamps are accepted as valid.
    """
    if raw_val is None:
        raise LogSchemaError("Missing required field: timestamp")

    if isinstance(raw_val, datetime):
        if raw_val.tzinfo is None:
            return raw_val.replace(tzinfo=timezone.utc)
        return raw_val.astimezone(timezone.utc)

    # Check for numeric epoch (seconds or milliseconds)
    if isinstance(raw_val, (int, float)):
        try:
            if raw_val > 1e11:
                return datetime.fromtimestamp(raw_val / 1000.0, tz=timezone.utc)
            return datetime.fromtimestamp(float(raw_val), tz=timezone.utc)
        except Exception as e:
            raise LogValidationError(f"Invalid epoch timestamp: {raw_val}") from e

    raw_str = str(raw_val).strip()
    if not raw_str:
        raise LogSchemaError("Missing required field: timestamp (empty value)")

    if raw_str.isdigit():
        val = int(raw_str)
        if val > 1e11:
            return datetime.fromtimestamp(val / 1000.0, tz=timezone.utc)
        return datetime.fromtimestamp(float(val), tz=timezone.utc)

    try:
        dt = date_parser.parse(raw_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        # Boundary sanity check: accept historical logs from 1970 to 2100
        if dt.year < 1970 or dt.year > 2100:
            raise LogValidationError(f"Timestamp year out of allowable bounds (1970-2100): {dt.year}")

        return dt
    except Exception as e:
        if isinstance(e, LogValidationError):
            raise
        raise LogValidationError(f"Invalid timestamp format: '{raw_str}'") from e


def normalize_severity(raw_val: Any) -> str:
    """Normalize severity level to INFO, WARNING, ERROR, or CRITICAL."""
    if raw_val is None:
        raise LogSchemaError("Missing required field: severity")

    raw_str = str(raw_val).strip().upper()
    if not raw_str:
        raise LogSchemaError("Missing required field: severity (empty value)")

    cleaned = re.sub(r"[\[\]\(\)\-\:\s]", "", raw_str)

    if cleaned in SEVERITY_MAP:
        return SEVERITY_MAP[cleaned]

    raise LogValidationError(f"Invalid severity: '{raw_val}'. Allowed values: INFO, WARNING, ERROR, CRITICAL.")


def normalize_response_ms(raw_val: Any) -> Optional[float]:
    """
    Validate and extract latency in milliseconds.
    Returns float or None. Rejects negative values or non-numeric strings.
    """
    if raw_val is None:
        return None

    if isinstance(raw_val, str):
        cleaned = raw_val.strip().lower()
        if not cleaned or cleaned in ("none", "null", "n/a", "-"):
            return None
        if cleaned.endswith("ms"):
            cleaned = cleaned[:-2].strip()
            mult = 1.0
        elif cleaned.endswith("s"):
            cleaned = cleaned[:-1].strip()
            mult = 1000.0
        else:
            mult = 1.0

        try:
            val = float(cleaned) * mult
        except ValueError:
            raise LogValidationError(f"Invalid response time format: '{raw_val}'")
    elif isinstance(raw_val, (int, float)):
        val = float(raw_val)
    else:
        raise LogValidationError(f"Invalid response time type: {type(raw_val)}")

    if val < 0:
        raise LogValidationError(f"Negative response time: {val}ms. Latency must be non-negative.")

    return round(val, 2)


def generate_deterministic_event_id(
    timestamp: datetime,
    service: str,
    message: str,
    user_id: Optional[str] = None,
    response_ms: Optional[float] = None
) -> str:
    """Generate a stable deterministic 16-char hex ID from log contents."""
    key = f"{timestamp.isoformat()}|{service}|{message}|{user_id or ''}|{response_ms or ''}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return f"EVT_{digest[:12].upper()}"


def validate_and_normalize_record(
    raw_record: Dict[str, Any],
    source_file: str,
    run_id: str
) -> Dict[str, Any]:
    """
    Validate all fields of an extracted log record dictionary.
    Returns cleaned normalized dictionary ready for ApplicationLog insertion.
    Optional fields (user_id, endpoint, http_status, response_ms) are allowed to be None.
    Raises LogSchemaError or LogValidationError on invalid records.
    """
    # 1. Message check (Required)
    raw_msg = raw_record.get("message") or raw_record.get("msg") or raw_record.get("log")
    if raw_msg is None or str(raw_msg).strip() == "":
        raise LogSchemaError("Missing required field: message")
    message = str(raw_msg).strip()

    # 2. Timestamp check (Required)
    raw_ts = (
        raw_record.get("timestamp")
        or raw_record.get("time")
        or raw_record.get("@timestamp")
        or raw_record.get("datetime")
    )
    timestamp = normalize_timestamp(raw_ts)

    # 3. Severity check (Required)
    raw_sev = (
        raw_record.get("severity")
        or raw_record.get("level")
        or raw_record.get("log_level")
        or raw_record.get("status_level")
    )
    severity = normalize_severity(raw_sev)

    # 4. Service check (Optional, defaults to 'app')
    raw_service = raw_record.get("service") or raw_record.get("service_name") or raw_record.get("app")
    service = str(raw_service).strip().lower() if raw_service else "app"
    if not service or service in ("none", "null"):
        service = "app"

    # 5. Response Time check (Optional)
    raw_resp = (
        raw_record.get("response_ms")
        or raw_record.get("latency")
        or raw_record.get("latency_ms")
        or raw_record.get("duration_ms")
        or raw_record.get("response_time")
    )
    response_ms = normalize_response_ms(raw_resp)

    # 6. User ID (Optional)
    raw_user = raw_record.get("user_id") or raw_record.get("userId") or raw_record.get("user")
    user_id = str(raw_user).strip() if raw_user is not None and str(raw_user).strip() not in ("", "none", "null") else None

    # 7. Endpoint & HTTP Status (Optional)
    raw_endpoint = raw_record.get("endpoint") or raw_record.get("path") or raw_record.get("url")
    endpoint = str(raw_endpoint).strip() if raw_endpoint else None

    raw_status = raw_record.get("http_status") or raw_record.get("status_code") or raw_record.get("status")
    http_status = None
    if raw_status is not None:
        try:
            http_status = int(raw_status)
        except (ValueError, TypeError):
            pass

    # 8. Event ID (Optional, auto-generated if missing)
    raw_event_id = raw_record.get("event_id") or raw_record.get("id") or raw_record.get("eventId")
    if raw_event_id and str(raw_event_id).strip():
        event_id = str(raw_event_id).strip()
    else:
        event_id = generate_deterministic_event_id(timestamp, service, message, user_id, response_ms)

    # 9. Failure determination: Severity ERROR/CRITICAL or HTTP status >= 500
    is_failure = (severity in ("ERROR", "CRITICAL")) or (http_status is not None and http_status >= 500)

    return {
        "event_id": event_id,
        "run_id": run_id,
        "timestamp": timestamp,
        "severity": severity,
        "service": service,
        "message": message,
        "response_ms": response_ms,
        "user_id": user_id,
        "endpoint": endpoint,
        "http_status": http_status,
        "is_failure": is_failure,
        "source_file": source_file,
    }
