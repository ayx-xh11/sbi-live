"""
Safe, redacting logger for SBI Balance Desktop Widget.
Ensures no credentials, OTPs, full account numbers, or session cookies are ever logged.
"""

import logging
import re
from logging.handlers import RotatingFileHandler
from typing import Optional
from app.config import LOGS_DIR

# Redaction patterns
_PATTERNS = [
    # Passwords in query parameters or text: password=..., pwd=...
    (re.compile(r'(?i)(password|passwd|pwd|secret)\s*[:=]\s*([^\s,;&"\']+)', re.IGNORECASE), r'\1=[REDACTED]'),
    # OTP patterns: 4-8 digit numbers explicitly labeled as OTP / code
    (re.compile(r'(?i)(otp|one[-\s]?time[-\s]?password|code|verification)\s*[:=]?\s*(\b\d{4,8}\b)', re.IGNORECASE), r'\1=[REDACTED_OTP]'),
    # Standalone 6-8 digit OTP tokens when passed in messages
    (re.compile(r'\b(?<![.\d])\d{6}(?![.\d])\b'), '[REDACTED_CODE]'),
    # Bank Account numbers (10 to 18 digits) -> masked to last 4 digits: ••••1234
    (re.compile(r'\b\d{6,14}(\d{4})\b'), r'••••\1'),
    # Cookie headers, tokens
    (re.compile(r'(?i)(sessionid|token|auth|cookie)\s*[:=]\s*([^\s,;&"\']+)', re.IGNORECASE), r'\1=[REDACTED_TOKEN]'),
]


class RedactingFormatter(logging.Formatter):
    """Custom formatter that scrubs sensitive data from log records."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = original
        for pattern, replacement in _PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted


def sanitize_text(text: str) -> str:
    """Helper to redact sensitive data from strings directly."""
    if not text:
        return text
    result = text
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def setup_logger(name: str = "sbi_widget", log_level: int = logging.INFO) -> logging.Logger:
    """Initialize and configure the safe application logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(log_level)
    formatter = RedactingFormatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # File Handler (max 5 MB, up to 3 backups)
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / "widget.log"
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not initialize file log handler: {e}")

    return logger


# Global logger instance
logger = setup_logger()
