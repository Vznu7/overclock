import logging
import re
import sys

# Patterns to sanitize in logs
SENSITIVE_PATTERNS = [
    (re.compile(r"bearer\s+[a-zA-Z0-9\-_.]+", re.IGNORECASE), "Bearer [REDACTED]"),
    (
        re.compile(r"password['\"]?\s*[:=]\s*['\"]?[^'\",\s]+['\"]?", re.IGNORECASE),
        "password=[REDACTED]",
    ),
    (
        re.compile(r"api_key['\"]?\s*[:=]\s*['\"]?[^'\",\s]+['\"]?", re.IGNORECASE),
        "api_key=[REDACTED]",
    ),
    (
        re.compile(r"secret['\"]?\s*[:=]\s*['\"]?[^'\",\s]+['\"]?", re.IGNORECASE),
        "secret=[REDACTED]",
    ),
]


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern, replacement in SENSITIVE_PATTERNS:
            msg = pattern.sub(replacement, msg)
        return msg


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("overclock")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
