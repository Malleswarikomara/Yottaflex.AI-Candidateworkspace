import csv
import io
from typing import List, Tuple, Optional
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


def read_record(reader: csv.reader, raw_lines: List[str]) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Reads one complete logical CSV record while preserving its original text.
    Handles multiline quoted values across multiple physical lines.
    """
    start_line = reader.line_num
    try:
        row = next(reader)
    except StopIteration:
        return None, None
    end_line = reader.line_num
    raw_record = "\n".join(raw_lines[start_line:end_line])
    return row, raw_record


class CsvLogParser(BaseLogParser):
    """
    Parses CSV log files.
    Tracks logical records and their physical line ranges.
    Handles UTF-8 BOM, leading blank lines, and multiline quoted records.
    Validates required column schema and column count.
    """

    def parse_content(self, content: str) -> List[ParsedRecordResult]:
        content_stripped = content.strip()
        if not content_stripped:
            return []

        # 1. Normalize UTF-8 BOM and prepare reader
        content = content.removeprefix("\ufeff")
        stream = io.StringIO(content, newline="")
        reader = csv.reader(stream)
        raw_lines = content.splitlines()

        results: List[ParsedRecordResult] = []

        try:
            # 2. Skip leading blank rows to select the header record
            headers: Optional[List[str]] = None
            header_raw: Optional[str] = None
            while True:
                row, raw_rec = read_record(reader, raw_lines)
                if row is None:
                    return []
                if not row or all(c.strip() == "" for c in row):
                    continue
                headers = row
                header_raw = raw_rec
                break

            cleaned_headers = [h.strip().lower() for h in headers]
            mapped_headers = [ACCEPTABLE_VARIANTS.get(h, h) for h in cleaned_headers]
            num_cols = len(cleaned_headers)

            # 3. Check if required schema columns are present
            present_canonical = set(mapped_headers)
            missing_cols = REQUIRED_COLUMNS - present_canonical
            if missing_cols:
                # Schema error: quarantine each logical data record individually
                err_msg = f"Incompatible schema: missing required column(s) {sorted(list(missing_cols))}"
                while True:
                    row, raw_rec = read_record(reader, raw_lines)
                    if row is None:
                        break
                    if not row or all(c.strip() == "" for c in row):
                        continue
                    results.append(
                        ParsedRecordResult(
                            raw_record=raw_rec,
                            parse_error=err_msg,
                            reject_type="SCHEMA_ERROR"
                        )
                    )
                # If there were no data records at all (header only), quarantine header
                if not results:
                    results.append(
                        ParsedRecordResult(
                            raw_record=header_raw or ",".join(headers),
                            parse_error=err_msg,
                            reject_type="SCHEMA_ERROR"
                        )
                    )
                return results

            # 4. Process data records
            while True:
                row, raw_rec = read_record(reader, raw_lines)
                if row is None:
                    break

                # Skip empty lines between records
                if not row or all(c.strip() == "" for c in row):
                    continue

                if len(row) != num_cols:
                    results.append(ParsedRecordResult(
                        raw_record=raw_rec,
                        parse_error=f"Malformed CSV: expected {num_cols} columns but got {len(row)}",
                        reject_type="MALFORMED"
                    ))
                    continue

                record = {}
                for col_name, col_val in zip(cleaned_headers, row):
                    val = col_val.strip()
                    record[col_name] = val if val != "" else None

                results.append(ParsedRecordResult(raw_record=raw_rec, data=record))

        except Exception as e:
            results.append(ParsedRecordResult(
                raw_record=content[:200],
                parse_error=f"Fatal CSV parsing error: {str(e)}",
                reject_type="MALFORMED"
            ))

        return results
