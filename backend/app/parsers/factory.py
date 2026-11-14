import os
from typing import Tuple
from app.parsers.base import BaseLogParser
from app.parsers.json_parser import JsonLogParser
from app.parsers.csv_parser import CsvLogParser
from app.parsers.text_parser import TextLogParser


class ParserFactory:
    """Detects format and returns appropriate BaseLogParser instance."""

    @staticmethod
    def get_parser(filename: str, sample_content: str = "") -> Tuple[BaseLogParser, str]:
        """
        Returns (parser_instance, detected_format_name).
        Format names: 'JSON', 'CSV', 'TEXT'.
        """
        ext = os.path.splitext(filename)[1].lower()

        if ext in (".json", ".jsonl", ".ndjson"):
            return JsonLogParser(), "JSON"
        elif ext in (".csv",):
            return CsvLogParser(), "CSV"
        elif ext in (".log", ".txt"):
            # Sniff content to differentiate structured JSON/CSV disguised as .log/.txt
            sample = sample_content.strip()
            if sample.startswith("[") or sample.startswith("{"):
                return JsonLogParser(), "JSON"
            first_line = sample.splitlines()[0] if sample else ""
            if "," in first_line and any(
                hdr in first_line.lower() for hdr in ("timestamp", "severity", "level", "service", "message")
            ):
                return CsvLogParser(), "CSV"
            return TextLogParser(), "TEXT"

        # Default fallback: check content
        sample = sample_content.strip()
        if sample.startswith("[") or sample.startswith("{"):
            return JsonLogParser(), "JSON"
        first_line = sample.splitlines()[0] if sample else ""
        if "," in first_line and any(
            hdr in first_line.lower() for hdr in ("timestamp", "severity", "level", "service", "message")
        ):
            return CsvLogParser(), "CSV"

        return TextLogParser(), "TEXT"
