from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any


class ParsedRecordResult:
    """Container for parsed output of a single raw log entry."""
    def __init__(self, raw_record: str, data: Dict[str, Any] = None, parse_error: str = None):
        self.raw_record = raw_record
        self.data = data or {}
        self.parse_error = parse_error

    @property
    def is_parse_ok(self) -> bool:
        return self.parse_error is None and bool(self.data)


class BaseLogParser(ABC):
    """Abstract base class for all log format parsers."""

    @abstractmethod
    def parse_content(self, content: str) -> List[ParsedRecordResult]:
        """
        Parse raw file/text content into a list of ParsedRecordResult objects.
        Every single incoming record/line is preserved either with .data or with .parse_error.
        """
        pass
