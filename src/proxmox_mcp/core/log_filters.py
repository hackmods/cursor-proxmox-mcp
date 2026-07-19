"""Log filters that redact secrets from log records."""
from __future__ import annotations

import logging
import re

_REDACT_PATTERNS = [
    (re.compile(r"(token[_-]?value\s*[=:]\s*)(\S+)", re.I), r"\1***"),
    (re.compile(r"(password\s*[=:]\s*)(\S+)", re.I), r"\1***"),
    (re.compile(r"(PVEAPIToken=)([^\s,]+)", re.I), r"\1***"),
    (re.compile(r"(secret\s*[=:]\s*)(\S+)", re.I), r"\1***"),
    (re.compile(r"(out-data|err-data)\s*[=:]\s*.+", re.I), r"\1=***"),
]


class RedactingFilter(logging.Filter):
    """Redact known-sensitive substrings from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        redacted = msg
        for pattern, repl in _REDACT_PATTERNS:
            redacted = pattern.sub(repl, redacted)
        if redacted != msg:
            record.msg = redacted
            record.args = ()
        return True
