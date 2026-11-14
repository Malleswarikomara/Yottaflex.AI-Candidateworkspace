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
                decoder = json.JSONDecoder()
                idx = content.find("[") + 1
                while idx < len(content):
                    while idx < len(content) and content[idx] in " \t\r\n,":
                        idx += 1
                    if idx >= len(content) or content[idx] == "]":
                        break
                    try:
                        item, end_idx = decoder.raw_decode(content, idx)
                        raw_slice = content[idx:end_idx]
                        if isinstance(item, dict):
                            results.append(ParsedRecordResult(raw_record=raw_slice, data=item))
                        else:
                            results.append(ParsedRecordResult(
                                raw_record=raw_slice,
                                parse_error=f"JSON array item is not an object: {type(item).__name__}",
                                reject_type="MALFORMED",
                            ))
                        idx = end_idx
                    except json.JSONDecodeError as e:
                        next_comma = content.find(",", idx)
                        next_bracket = content.find("]", idx)
                        if next_comma != -1 and (next_bracket == -1 or next_comma < next_bracket):
                            end_idx = next_comma
                        elif next_bracket != -1:
                            end_idx = next_bracket
                        else:
                            end_idx = len(content)
                        raw_slice = content[idx:end_idx].strip()
                        results.append(ParsedRecordResult(
                            raw_record=raw_slice,
                            parse_error=f"Malformed JSON syntax: {e.msg}",
                            reject_type="MALFORMED",
                        ))
                        idx = end_idx
                return results
            except Exception:
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
                    results.append(ParsedRecordResult(raw_record=line, data=parsed))
                else:
                    results.append(ParsedRecordResult(
                        raw_record=line,
                        parse_error=f"JSON line is not an object: {type(parsed).__name__}",
                        reject_type="MALFORMED"
                    ))
            except json.JSONDecodeError as e:
                results.append(ParsedRecordResult(
                    raw_record=line,
                    parse_error=f"Malformed JSON syntax: {e.msg} at line {idx + 1}",
                    reject_type="MALFORMED"
                ))

        return results
