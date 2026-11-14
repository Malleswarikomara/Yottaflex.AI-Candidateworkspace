import csv
import io
from typing import List
from app.parsers.base import BaseLogParser, ParsedRecordResult


class CsvLogParser(BaseLogParser):
    """
    Parses CSV log files.
    Extracts headers and creates dictionary records.
    Captures malformed CSV lines with row-level error reporting.
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
            num_cols = len(cleaned_headers)

            for row_idx, row in enumerate(reader, start=2):
                # Skip empty lines
                if not row or all(c.strip() == "" for c in row):
                    continue

                raw_line = ",".join(row)
                if len(row) != num_cols:
                    results.append(ParsedRecordResult(
                        raw_record=raw_line,
                        parse_error=f"Malformed CSV: expected {num_cols} columns but got {len(row)} at row {row_idx}"
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
                parse_error=f"Fatal CSV parsing error: {str(e)}"
            ))

        return results
