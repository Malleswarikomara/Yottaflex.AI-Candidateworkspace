import csv
import io
from typing import List
from app.parsers.base import BaseLogParser, ParsedRecordResult

REQUIRED_COLUMNS = {"timestamp", "severity", "message"}
ACCEPTABLE_VARIANTS = {
    "time": "timestamp",
    "@timestamp": "timestamp",
    "datetime": "timestamp",
    "level": "severity",
    "log_level": "severity",
    "msg": "message",
    "log": "message",
}


class CsvLogParser(BaseLogParser):
    """
    Parses CSV log files.
    Extracts headers and creates dictionary records.
    Captures malformed CSV lines with row-level error reporting.
    Validates required column schema.
    """

    def parse_content(self, content: str) -> List[ParsedRecordResult]:
        content_stripped = content.strip()
        if not content_stripped:
            return []

        results: List[ParsedRecordResult] = []
        stream = io.StringIO(content)

        try:
            reader = csv.reader(stream)
            try:
                headers = next(reader)
            except StopIteration:
                return []

            cleaned_headers = [h.strip().lower() for h in headers]
            mapped_headers = [ACCEPTABLE_VARIANTS.get(h, h) for h in cleaned_headers]
            num_cols = len(cleaned_headers)

            # Check if required schema columns are present
            present_canonical = set(mapped_headers)
            missing_cols = REQUIRED_COLUMNS - present_canonical
            if missing_cols:
                # Schema error across the file: reject header row or reject records as schema error
                return [
                    ParsedRecordResult(
                        raw_record=",".join(headers),
                        parse_error=f"Incompatible schema: missing required column(s) {sorted(list(missing_cols))}",
                        reject_type="SCHEMA_ERROR"
                    )
                ]

            for row_idx, row in enumerate(reader, start=2):
                # Skip empty lines
                if not row or all(c.strip() == "" for c in row):
                    continue

                raw_line = ",".join(row)
                if len(row) != num_cols:
                    results.append(ParsedRecordResult(
                        raw_record=raw_line,
                        parse_error=f"Malformed CSV: expected {num_cols} columns but got {len(row)} at row {row_idx}",
                        reject_type="MALFORMED"
                    ))
                    continue

                record = {}
                for col_name, col_val in zip(cleaned_headers, row):
                    val = col_val.strip()
                    record[col_name] = val if val != "" else None

                results.append(ParsedRecordResult(raw_record=raw_line, data=record))

        except Exception as e:
            results.append(ParsedRecordResult(
                raw_record=content[:200],
                parse_error=f"Fatal CSV parsing error: {str(e)}",
                reject_type="MALFORMED"
            ))

        return results
