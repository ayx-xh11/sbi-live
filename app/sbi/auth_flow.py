"""
Authentication workflow manager for SBI Personal Banking.
Coordinates session checks, pre-filling credentials, user CAPTCHA/OTP challenges,
and transitions to background monitoring.
"""

import time
from typing import Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from app.state import AuthState, StateManager
from app.browser.selectors import (
    SBI_YONO_WELCOME_URL,
    SBI_CLASSIC_LOGIN_URL,
    USERNAME_SELECTORS,
    PASSWORD_SELECTORS,
    CAPTCHA_INPUT_SELECTORS,
    CAPTCHA_IMAGE_SELECTORS,
    LOGIN_BUTTON_SELECTORS,
    OTP_INDICATOR_SELECTORS,
    AUTHENTICATED_INDICATORS,
    BALANCE_VIEW_TOGGLES,
)
from app.browser.browser_manager import BrowserManager
from app.security.credentials import get_saved_credentials
from app.security.domain_guard import is_url_allowed
from app.security.safe_logger import logger


class AuthFlow:
    """Handles the live interactions with SBI portal during authentication."""

    def __init__(self, browser_manager: BrowserManager, state_manager: StateManager):
        self.browser_manager = browser_manager
        self.state_manager = state_manager

    def check_is_authenticated(self, page: Page) -> bool:
        """Check if the browser is currently on an authenticated SBI page."""
        if not is_url_allowed(page.url):
            return False

        # Look for authenticated signals
        for selector in AUTHENTICATED_INDICATORS:
            try:
                if page.locator(selector).first.is_visible(timeout=1000):
                    return True
            except Exception:
                continue

        return False

    def is_otp_required(self, page: Page) -> bool:
        """Check if page is currently prompting for OTP."""
        for selector in OTP_INDICATOR_SELECTORS:
            try:
                if page.locator(selector).first.is_visible(timeout=1000):
                    return True
            except Exception:
                continue
        return False

    def is_login_page(self, page: Page) -> bool:
        """Check if page currently displays the username/password/captcha login form."""
        try:
            for u_sel in USERNAME_SELECTORS:
                if page.locator(u_sel).first.is_visible(timeout=1000):
                    return True
        except Exception:
            pass
        return False

    def prefill_credentials_if_available(self, page: Page) -> bool:
        """
        Pre-fill username and password from Windows Credential Manager if present.
        Only executed on strictly verified SBI domains.
        """
        if not is_url_allowed(page.url):
            logger.error("Refusing to fill credentials on unverified domain")
            return False

        creds = get_saved_credentials()
        if not creds:
            logger.info("No saved credentials found in Windows Credential Manager.")
            return False

        username, password = creds
        try:
            # Fill username
            filled_user = False
            for u_sel in USERNAME_SELECTORS:
                loc = page.locator(u_sel).first
                if loc.is_visible(timeout=1000):
                    loc.fill(username)
                    filled_user = True
                    break

            # Fill password
            filled_pass = False
            for p_sel in PASSWORD_SELECTORS:
                loc = page.locator(p_sel).first
                if loc.is_visible(timeout=1000):
                    loc.fill(password)
                    filled_pass = True
                    break

            if filled_user and filled_pass:
                logger.info("Credentials pre-filled from Windows Credential Manager into official SBI form.")
                return True
        except Exception as e:
            logger.warning(f"Could not prefill credentials: {e}")

        return False

    def trigger_balance_toggles_if_present(self, page: Page) -> None:
        """If balances are hidden behind 'View Balance' eye buttons, click them."""
        for toggle_sel in BALANCE_VIEW_TOGGLES:
            try:
                buttons = page.locator(toggle_sel).all()
                for btn in buttons:
                    if btn.is_visible():
                        btn.click()
                        time.sleep(1)
            except Exception:
                continue

    def execute_auth_flow(self, max_wait_seconds: int = 180) -> bool:
        """
        Runs the full authentication flow:
        1. Checks existing session.
        2. If unauthenticated, navigates to official SBI portal.
        3. Pre-fills saved credentials and brings browser forward for CAPTCHA/OTP.
        4. Waits for user to complete CAPTCHA & OTP on official SBI page.
        5. Detects authenticated dashboard and hides browser.
        """
        page = self.browser_manager.start()
        self.state_manager.set_state(AuthState.CHECKING_SESSION, "Checking SBI session status...")

        # Step 1: Check existing page state
        try:
            if self.check_is_authenticated(page):
                logger.info("Existing valid SBI session detected.")
                self.state_manager.set_state(AuthState.AUTHENTICATED, "Session is active and valid.")
                self.browser_manager.hide_browser()
                return True
        except Exception as e:
            logger.warning(f"Session pre-check error: {e}")

        # Step 2: Navigate to official login if not already there
        logger.info("Session not active. Navigating to official login...")
        self.state_manager.set_state(AuthState.AUTHENTICATION_REQUIRED, "SBI authentication required.")

        try:
            page.goto(SBI_YONO_WELCOME_URL, wait_until="commit", timeout=45000)
            page.wait_for_timeout(4000)
        except Exception as e:
            logger.warning(f"Welcome URL commit failed, attempting fallback: {e}")
            try:
                page.goto(SBI_CLASSIC_LOGIN_URL, wait_until="commit", timeout=30000)
                page.wait_for_timeout(4000)
            except Exception as e2:
                self.state_manager.set_state(AuthState.NETWORK_ERROR, f"Unable to reach SBI: {e2}")
                return False

        # Verify domain before proceeding
        if not is_url_allowed(page.url):
            self.state_manager.set_state(AuthState.UNEXPECTED_REDIRECT, f"Redirected to unapproved URL: {page.url}")
            return False

        # Step 3: Fill credentials and bring browser forward for CAPTCHA
        self.state_manager.set_state(AuthState.SBI_LOGIN, "Official SBI login page loaded.")
        self.prefill_credentials_if_available(page)

        self.state_manager.set_state(AuthState.CAPTCHA_REQUIRED, "Please complete the CAPTCHA in the SBI browser.")
        self.browser_manager.show_browser()

        # Step 4: User interaction polling loop
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                if page.is_closed():
                    self.state_manager.set_state(AuthState.BROWSER_ERROR, "Browser was closed.")
                    return False

                # Check if authenticated
                if self.check_is_authenticated(page):
                    logger.info("Authentication successful! Dashboard detected.")
                    self.state_manager.set_state(AuthState.AUTHENTICATED, "Authentication successful.")
                    self.browser_manager.hide_browser()
                    return True

                # Check if OTP screen is active
                if self.is_otp_required(page):
                    if self.state_manager.current_state != AuthState.OTP_REQUIRED:
                        self.state_manager.set_state(AuthState.OTP_REQUIRED, "Please enter the OTP in the SBI browser.")
                        self.browser_manager.show_browser()

                time.sleep(2)
            except Exception as e:
                logger.debug(f"Waiting for authentication: {e}")
                time.sleep(2)

        # Timeout reached
        self.state_manager.set_state(AuthState.SESSION_EXPIRED, "Authentication timed out. Please try again.")
        return False
