"""
Unit tests for domain allowlisting and URL validation.
"""

import pytest
from app.security.domain_guard import is_url_allowed, validate_navigation_or_raise


def test_approved_sbi_domains():
    valid_urls = [
        "https://yonoretail.sbi.bank.in/registration/welcome?srcChn=RINB",
        "https://retail.onlinesbi.sbi/retail/login.htm",
        "https://www.onlinesbi.sbi/",
        "https://onlinesbi.sbi/personal",
        "https://retail.sbi.bank.in/npersonal/sbi_home.html",
        "https://sbi.bank.in/web/personal-banking",
        "https://cdn.onlineyono.sbi.bank.in/assets/js/bundle.js",
        "https://bba.sbi.bank.in/v1/deviceService/config",
        "about:blank",
    ]
    for url in valid_urls:
        assert is_url_allowed(url) is True, f"Failed on valid URL: {url}"


def test_rejected_non_https_schemes():
    disallowed_urls = [
        "http://yonoretail.sbi.bank.in/",
        "ftp://sbi.bank.in/files",
        "javascript:alert(1)",
        "data:text/html,<div>test</div>",
        "file:///C:/passwords.txt",
    ]
    for url in disallowed_urls:
        assert is_url_allowed(url) is False, f"Allowed insecure scheme: {url}"


def test_rejected_spoofed_or_external_domains():
    malicious_urls = [
        "https://google.com",
        "https://attacker.com/sbi",
        "https://sbi.bank.in.attacker.com/login",
        "https://onlinesbi.sbi.evilcorp.org",
        "https://fake-sbi.bank.in.phishing.net",
        "https://user:pass@sbi.bank.in/login",
        "https://attacker.com?sbi.bank.in",
    ]
    for url in malicious_urls:
        assert is_url_allowed(url) is False, f"Allowed malicious/external URL: {url}"


def test_validate_navigation_or_raise():
    # Should not raise for valid domain
    validate_navigation_or_raise("https://yonoretail.sbi.bank.in/dashboard")

    # Should raise PermissionError for unapproved domain
    with pytest.raises(PermissionError):
        validate_navigation_or_raise("https://unapproved-site.com")
