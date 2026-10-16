"""
Unit tests for SafeLogger credential and financial data redaction.
"""

from app.security.safe_logger import sanitize_text


def test_password_redaction():
    text = "User submitted form with password=MySecretPass123&action=login"
    sanitized = sanitize_text(text)
    assert "MySecretPass123" not in sanitized
    assert "[REDACTED]" in sanitized


def test_otp_redaction():
    text = "SMS received with OTP: 948201 for transaction verification"
    sanitized = sanitize_text(text)
    assert "948201" not in sanitized
    assert "[REDACTED_OTP]" in sanitized or "[REDACTED_CODE]" in sanitized


def test_standalone_numeric_token_redaction():
    text = "Received numeric token 582194 in message payload"
    sanitized = sanitize_text(text)
    assert "582194" not in sanitized
    assert "[REDACTED_CODE]" in sanitized


def test_account_number_masking():
    text = "Retrieved details for account 102938475612 from SBI core banking"
    sanitized = sanitize_text(text)
    assert "102938475612" not in sanitized
    assert "••••5612" in sanitized


def test_session_token_redaction():
    text = "Session established with token=abcd1234efgh5678"
    sanitized = sanitize_text(text)
    assert "abcd1234efgh5678" not in sanitized
    assert "[REDACTED_TOKEN]" in sanitized
