import json
from typing import List
from app.parsers.base import BaseLogParser, ParsedRecordResult


class JsonLogParser(BaseLogParser):
    """
    Parses structured JSON logs.
    Supports either:
    1. A single JSON Array of objects: `[ {...}, {...} ]`
    2. JSON Lines (NDJSON): each line is an independent JSON object.
    """

    def parse_content(self, content: str) -> List[ParsedRecordResult]:
        content_stripped = content.strip()
        if not content_stripped:
            return []

        results: List[ParsedRecordResult] = []

        # Check if entire content is a JSON Array
        if content_stripped.startswith("[") and content_stripped.endswith("]"):
            try:
                array_data = json.loads(content_stripped)
                if not isinstance(array_data, list):
                    return [ParsedRecordResult(
                        raw_record=content_stripped[:200],
                        parse_error="Expected JSON array at root level",
                        reject_type="MALFORMED"
                    )]

                for item in array_data:
                    raw_str = json.dumps(item)
                    if isinstance(item, dict):
                        results.append(ParsedRecordResult(raw_record=raw_str, data=item))
                    else:
                        results.append(ParsedRecordResult(
                            raw_record=raw_str,
                            parse_error=f"JSON array item is not an object: {type(item).__name__}",
                            reject_type="MALFORMED"
                        ))
                return results
            except json.JSONDecodeError:
                # If array parsing fails, fall back to line-by-line parsing
                pass

        # Parse line-by-line (NDJSON / JSON Lines format)
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            try:
                parsed = json.loads(line_str)
                if isinstance(parsed, dict):
                    results.append(ParsedRecordResult(raw_record=line_str, data=parsed))
                else:
                    results.append(ParsedRecordResult(
                        raw_record=line_str,
                        parse_error=f"JSON line is not an object: {type(parsed).__name__}",
                        reject_type="MALFORMED"
                    ))
            except json.JSONDecodeError as e:
                results.append(ParsedRecordResult(
                    raw_record=line_str,
                    parse_error=f"Malformed JSON syntax: {e.msg} at line {idx + 1}",
                    reject_type="MALFORMED"
                ))

        return results
