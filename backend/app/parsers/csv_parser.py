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
        raw_lines = content.splitlines()

        # Find header line (first non-empty line)
        header_idx = -1
        for idx, line in enumerate(raw_lines):
            if line.strip():
                header_idx = idx
                break

        if header_idx == -1:
            return []

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
                # Schema error: every non-empty data row is rejected with SCHEMA_ERROR
                # preserving exact raw line without loss for complete 1-to-1 reconciliation
                err_msg = f"Incompatible schema: missing required column(s) {sorted(list(missing_cols))}"
                for line in raw_lines[header_idx + 1:]:
                    if not line.strip():
                        continue
                    results.append(
                        ParsedRecordResult(
                            raw_record=line,
                            parse_error=err_msg,
                            reject_type="SCHEMA_ERROR"
                        )
                    )
                # If there were no data lines at all (header only), record header as schema error
                if not results:
                    results.append(
                        ParsedRecordResult(
                            raw_record=raw_lines[header_idx],
                            parse_error=err_msg,
                            reject_type="SCHEMA_ERROR"
                        )
                    )
                return results

            for row_idx, row in enumerate(reader, start=2):
                # Skip empty lines
                if not row or all(c.strip() == "" for c in row):
                    continue

                # Preserve exact raw line from raw_lines using reader.line_num
                raw_line = None
                if 1 <= reader.line_num <= len(raw_lines):
                    raw_line = raw_lines[reader.line_num - 1]
                if not raw_line or not raw_line.strip():
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
