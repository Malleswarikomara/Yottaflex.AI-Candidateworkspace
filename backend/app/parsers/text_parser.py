import re
from typing import List, Dict, Any, Optional
from app.parsers.base import BaseLogParser, ParsedRecordResult

# Regex to match ISO timestamp or standard SQL timestamp:
# e.g., 2026-11-14 10:15:20, 2026-11-14T10:15:20.123Z, [2026-11-14 10:15:20], etc.
TS_REGEX = re.compile(
    r"^\[?(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\]?"
)

# Alternative timestamp: 14/Nov/2026:10:15:20 (+0000)
APACHE_TS_REGEX = re.compile(
    r"^\[?(?P<timestamp>\d{1,2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}(?:\s+[+-]\d{4})?)\]?"
)

# Regex to match severity in brackets or bare: [INFO], INFO, [ERROR], etc.
SEV_REGEX = re.compile(
    r"^\[?(?P<severity>INFO|WARN|WARNING|ERR|ERROR|CRIT|CRITICAL|FATAL)\]?",
    re.IGNORECASE
)

# Regex to extract key=value pairs: user_id=101, service="auth", latency=3000ms, etc.
KV_REGEX = re.compile(
    r'(?P<key>[a-zA-Z_][a-zA-Z0-9_]*)=(?:"(?P<val1>[^"]*)"|\'(?P<val2>[^\']*)\'|(?P<val3>[^\s,]+))'
)

# Bracketed tag extractor, e.g. [auth] or [api-gateway]
TAG_REGEX = re.compile(r"^\[(?P<tag>[a-zA-Z0-9_\-\.]+)\]")


class TextLogParser(BaseLogParser):
    """
    Parses semi-structured text log lines.
    Extracts timestamp, severity, bracketed services, message, and key-value pairs.
    """

    def parse_line(self, line: str) -> Optional[ParsedRecordResult]:
        line_to_parse = line.strip()
        if not line_to_parse:
            return None

        # 1. Extract Timestamp
        ts_match = TS_REGEX.match(line_to_parse)
        if ts_match:
            timestamp_str = ts_match.group("timestamp")
            remainder = line_to_parse[ts_match.end():].strip()
        else:
            ts_match2 = APACHE_TS_REGEX.match(line_to_parse)
            if ts_match2:
                timestamp_str = ts_match2.group("timestamp")
                remainder = line_to_parse[ts_match2.end():].strip()
            else:
                return ParsedRecordResult(
                    raw_record=line,
                    parse_error="Failed to extract timestamp from log line",
                    reject_type="MALFORMED"
                )

        # 2. Extract Severity
        service_candidate = None
        sev_match = SEV_REGEX.match(remainder)
        if sev_match:
            severity_str = sev_match.group("severity")
            remainder = remainder[sev_match.end():].strip()
        else:
            # Check if severity is preceded by a bracketed service: e.g. [service] [INFO]
            tag_match = TAG_REGEX.match(remainder)
            if tag_match:
                service_candidate = tag_match.group("tag")
                remainder = remainder[tag_match.end():].strip()
                sev_match = SEV_REGEX.match(remainder)
                if sev_match:
                    severity_str = sev_match.group("severity")
                    remainder = remainder[sev_match.end():].strip()
                else:
                    return ParsedRecordResult(
                        raw_record=line,
                        parse_error="Failed to extract severity level from log line",
                        reject_type="MALFORMED"
                    )
            else:
                return ParsedRecordResult(
                    raw_record=line,
                    parse_error="Failed to extract severity level from log line",
                    reject_type="MALFORMED"
                )

        # Check for bracketed service tag after severity if not found earlier: e.g. INFO [payment]
        service = service_candidate
        tag_match2 = TAG_REGEX.match(remainder)
        if tag_match2:
            if not service:
                service = tag_match2.group("tag")
            remainder = remainder[tag_match2.end():].strip()

        # 3. Extract key-value pairs (e.g. user_id=101, latency=3000ms, service=auth)
        kv_data = {}
        for m in KV_REGEX.finditer(remainder):
            k = m.group("key").lower()
            v = m.group("val1") or m.group("val2") or m.group("val3")
            kv_data[k] = v

        # If latency is in text message like 'response time exceeded 3000ms'
        latency_text_match = re.search(r"(\d+(?:\.\d+)?)\s*ms\b", remainder, re.IGNORECASE)
        if "response_ms" not in kv_data and "latency" not in kv_data and latency_text_match:
            kv_data["response_ms"] = float(latency_text_match.group(1))

        # 4. Clean message: remove explicit key=value pairs from the natural text message
        cleaned_msg = KV_REGEX.sub("", remainder).strip()
        cleaned_msg = re.sub(r"\s+", " ", cleaned_msg)
        cleaned_msg = cleaned_msg.strip(" -:;,")
        if not cleaned_msg:
            cleaned_msg = remainder

        # Build final record dict
        record: Dict[str, Any] = {
            "timestamp": timestamp_str,
            "severity": severity_str,
            "message": cleaned_msg,
            "service": kv_data.get("service") or service or "app",
            "user_id": kv_data.get("user_id") or kv_data.get("userid") or kv_data.get("user"),
            "event_id": kv_data.get("event_id") or kv_data.get("id"),
            "response_ms": kv_data.get("response_ms") or kv_data.get("latency") or kv_data.get("duration"),
            "endpoint": kv_data.get("endpoint") or kv_data.get("path"),
            "http_status": kv_data.get("status") or kv_data.get("status_code") or kv_data.get("http_status"),
        }

        return ParsedRecordResult(raw_record=line, data=record)

    def parse_content(self, content: str) -> List[ParsedRecordResult]:
        content_stripped = content.strip()
        if not content_stripped:
            return []

        results: List[ParsedRecordResult] = []
        for line in content.splitlines():
            res = self.parse_line(line)
            if res:
                results.append(res)
        return results
