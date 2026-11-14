import re
import hashlib
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from typing import Optional, Tuple, Any, Dict

EPOCH_START = datetime(1970, 1, 1, tzinfo=timezone.utc)


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
    Accepts historical and late-arriving timestamps within allowable bounds (1970–2100).
    """
    if raw_val is None:
        raise LogSchemaError("Missing required field: timestamp")

    dt: Optional[datetime] = None

    if isinstance(raw_val, datetime):
        try:
            if raw_val.tzinfo is None:
                dt = raw_val.replace(tzinfo=timezone.utc)
            else:
                dt = raw_val.astimezone(timezone.utc)
        except (OverflowError, ValueError, OSError) as e:
            raise LogValidationError(f"Invalid timestamp datetime conversion: {e}") from e
    elif isinstance(raw_val, (int, float)):
        try:
            val = float(raw_val)
            if abs(val) > 1e11:
                val = val / 1000.0
            dt = EPOCH_START + timedelta(seconds=val)
        except (ValueError, OverflowError, OSError) as e:
            raise LogValidationError(f"Invalid epoch timestamp: {raw_val}") from e
    else:
        raw_str = str(raw_val).strip()
        if not raw_str:
            raise LogSchemaError("Missing required field: timestamp (empty value)")

        # Check for numeric epoch string (positive or negative integer / float)
        if re.match(r"^-?\d+(?:\.\d+)?$", raw_str):
            try:
                val = float(raw_str)
                if abs(val) > 1e11:
                    val = val / 1000.0
                dt = EPOCH_START + timedelta(seconds=val)
            except (ValueError, OverflowError, OSError) as e:
                raise LogValidationError(f"Invalid epoch timestamp: '{raw_str}'") from e
        else:
            try:
                parsed_dt = date_parser.parse(raw_str)
                if parsed_dt.tzinfo is None:
                    dt = parsed_dt.replace(tzinfo=timezone.utc)
                else:
                    dt = parsed_dt.astimezone(timezone.utc)
            except Exception as e:
                raise LogValidationError(f"Invalid timestamp format: '{raw_str}'") from e

    # Universal boundary sanity check: accept logs from 1970 to 2100
    if dt.year < 1970 or dt.year > 2100:
        raise LogValidationError(f"Timestamp year out of allowable bounds (1970-2100): {dt.year}")

    return dt


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


def _get_first_present(record: Dict[str, Any], *keys: str) -> Any:
    """
    Safely retrieves the first non-empty value among multiple key candidates.
    Preserves numerical 0 and 0.0 without treating them as falsy.
    """
    for k in keys:
        if k in record:
            val = record[k]
            if val is not None:
                if isinstance(val, str):
                    if val.strip() != "":
                        return val.strip()
                else:
                    return val
    return None


def generate_deterministic_event_id(
    timestamp: datetime,
    service: str,
    message: str,
    user_id: Optional[str] = None,
    response_ms: Optional[float] = None,
    endpoint: Optional[str] = None,
    http_status: Optional[int] = None,
) -> str:
    """Generate a stable deterministic 16-char hex ID from log contents."""
    key = (
        f"{timestamp.isoformat()}|{service}|{message}|"
        f"{user_id or ''}|{endpoint or ''}|"
        f"{http_status if http_status is not None else ''}|"
        f"{response_ms if response_ms is not None else ''}"
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return f"EVT_{digest[:16].upper()}"


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
    raw_msg = _get_first_present(raw_record, "message", "msg", "log")
    if raw_msg is None or str(raw_msg).strip() == "":
        raise LogSchemaError("Missing required field: message")
    message = str(raw_msg).strip()

    # 2. Timestamp check (Required)
    raw_ts = _get_first_present(raw_record, "timestamp", "time", "@timestamp", "datetime")
    timestamp = normalize_timestamp(raw_ts)

    # 3. Severity check (Required)
    raw_sev = _get_first_present(raw_record, "severity", "level", "log_level", "status_level")
    severity = normalize_severity(raw_sev)

    # 4. Service check (Optional, defaults to 'app')
    raw_service = _get_first_present(raw_record, "service", "service_name", "app")
    service = str(raw_service).strip().lower() if raw_service else "app"
    if not service or service in ("none", "null"):
        service = "app"

    # 5. Response Time check (Optional)
    # Using _get_first_present ensures 0 and 0.0 are preserved and not evaluated as falsy
    raw_resp = _get_first_present(raw_record, "response_ms", "latency", "latency_ms", "duration_ms", "response_time")
    response_ms = normalize_response_ms(raw_resp)

    # 6. User ID (Optional)
    raw_user = _get_first_present(raw_record, "user_id", "userId", "user")
    user_id = str(raw_user).strip() if raw_user is not None and str(raw_user).strip().lower() not in ("", "none", "null") else None

    # 7. Endpoint & HTTP Status (Optional)
    raw_endpoint = _get_first_present(raw_record, "endpoint", "path", "url")
    endpoint = str(raw_endpoint).strip() if raw_endpoint else None

    raw_status = _get_first_present(raw_record, "http_status", "status_code", "status")
    http_status = None
    if raw_status is not None:
        try:
            http_status = int(raw_status)
        except (ValueError, TypeError):
            pass

    # 8. Event ID (Optional, auto-generated if missing)
    raw_event_id = _get_first_present(raw_record, "event_id", "id", "eventId")
    if raw_event_id and str(raw_event_id).strip():
        event_id = str(raw_event_id).strip()
    else:
        event_id = generate_deterministic_event_id(
            timestamp=timestamp,
            service=service,
            message=message,
            user_id=user_id,
            response_ms=response_ms,
            endpoint=endpoint,
            http_status=http_status,
        )

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
