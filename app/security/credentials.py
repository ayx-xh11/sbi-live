"""
Windows Credential Manager integration for SBI Balance Desktop Widget.
Uses the OS-level secure credential vault via keyring.
Strictly stores only username and password. Never stores OTP, PINs, or tokens.
"""

from typing import Optional, Tuple
import keyring
from app.security.safe_logger import logger

SERVICE_NAME = "SBIBalanceWidget"
META_SERVICE = "SBIBalanceWidget_Meta"
META_USER_KEY = "active_username"


def save_credentials(username: str, password: str) -> bool:
    """
    Save SBI username and password securely into Windows Credential Manager.
    Returns True on success, False on failure.
    """
    if not username or not password:
        logger.error("Attempted to save empty username or password")
        return False

    try:
        username_clean = username.strip()
        # Save active username pointer
        keyring.set_password(META_SERVICE, META_USER_KEY, username_clean)
        # Save password under username
        keyring.set_password(SERVICE_NAME, username_clean, password)
        logger.info("Credentials successfully saved to Windows Credential Manager")
        return True
    except Exception as e:
        logger.error(f"Failed to store credentials in Windows Credential Manager: {e}")
        return False


def get_saved_credentials() -> Optional[Tuple[str, str]]:
    """
    Retrieve stored (username, password) from Windows Credential Manager.
    Returns (username, password) or None if not found or on error.
    """
    try:
        username = keyring.get_password(META_SERVICE, META_USER_KEY)
        if not username:
            return None

        password = keyring.get_password(SERVICE_NAME, username)
        if not password:
            return None

        return (username, password)
    except Exception as e:
        logger.error(f"Failed to retrieve credentials from Windows Credential Manager: {e}")
        return None


def delete_credentials() -> bool:
    """
    Remove stored credentials from Windows Credential Manager.
    Returns True if removed, False otherwise.
    """
    try:
        username = keyring.get_password(META_SERVICE, META_USER_KEY)
        deleted = False
        if username:
            try:
                keyring.delete_password(SERVICE_NAME, username)
                deleted = True
            except keyring.errors.PasswordDeleteError:
                pass

        try:
            keyring.delete_password(META_SERVICE, META_USER_KEY)
            deleted = True
        except keyring.errors.PasswordDeleteError:
            pass

        logger.info("Credentials removed from Windows Credential Manager")
        return deleted
    except Exception as e:
        logger.error(f"Error while removing credentials: {e}")
        return False


def has_credentials() -> bool:
    """Check if valid credentials currently exist in the Windows Credential Manager."""
    creds = get_saved_credentials()
    return creds is not None and bool(creds[0]) and bool(creds[1])
