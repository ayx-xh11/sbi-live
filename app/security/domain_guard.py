"""
Domain guard and strict URL allowlisting for SBI personal banking flows.
Guards against open redirects, malicious origins, and credential transmission to unapproved domains.
"""

from urllib.parse import urlparse
from typing import Set
from app.security.safe_logger import logger

# Confirmed SBI domains based on live reconnaissance
ALLOWED_DOMAINS: Set[str] = {
    "yonoretail.sbi.bank.in",
    "retail.onlinesbi.sbi",
    "www.onlinesbi.sbi",
    "onlinesbi.sbi",
    "retail.sbi.bank.in",
    "sbi.bank.in",
    "cdn.onlineyono.sbi.bank.in",
    "bba.sbi.bank.in",
}


def is_url_allowed(url: str) -> bool:
    """
    Validates whether a URL strictly belongs to legitimate, approved SBI domains.
    Enforces:
      - HTTPS only (with about:blank permitted only for newly opened initial tabs)
      - No userinfo in authority (prevents phishing like https://attacker@sbi.bank.in)
      - Exact domain or approved subdomain match
    """
    if not url:
        return False

    url_str = url.strip()
    if url_str == "about:blank":
        return True

    try:
        parsed = urlparse(url_str)
    except Exception:
        return False

    # Enforce HTTPS strictly
    if parsed.scheme.lower() != "https":
        logger.warning(f"Rejected non-HTTPS URL: {parsed.scheme}://...")
        return False

    # Block userinfo spoofing (e.g. user:pass@host)
    if parsed.username or parsed.password:
        logger.warning("Rejected URL containing userinfo authority components")
        return False

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False

    # Exact match in allowlist
    if hostname in ALLOWED_DOMAINS:
        return True

    # Must strictly end with .sbi.bank.in or .onlinesbi.sbi
    valid_suffixes = (".sbi.bank.in", ".onlinesbi.sbi")
    for suffix in valid_suffixes:
        if hostname.endswith(suffix):
            # Ensure the character immediately before suffix is a dot or it is the domain itself
            prefix = hostname[:-len(suffix)]
            if prefix and not prefix.endswith("."):
                return False
            return True

    logger.warning(f"Rejected unapproved domain navigation: {hostname}")
    return False


def validate_navigation_or_raise(url: str) -> None:
    """Validate URL and raise SecurityError if disallowed."""
    if not is_url_allowed(url):
        raise PermissionError(f"Navigation to unapproved domain blocked: {url}")
