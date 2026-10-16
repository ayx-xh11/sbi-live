"""
Browser Manager for SBI Balance Desktop Widget.
Manages persistent Playwright browser profile in %APPDATA%, domain guarding, and window lifecycle.
"""

import os
import shutil
import sys
import threading
from typing import Optional
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright, Route, Request

from app.config import PROFILE_DIR
from app.security.domain_guard import is_url_allowed
from app.security.safe_logger import logger
from app.browser.window_utils import minimize_sbi_browser, restore_and_focus_sbi_browser

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
)


class BrowserManager:
    """Controls the persistent Playwright browser instance and enforces domain guarding."""

    def __init__(self, user_data_dir: Optional[str] = None):
        self._user_data_dir = str(user_data_dir or PROFILE_DIR)
        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._lock = threading.Lock()
        self._is_visible = False

    def _determine_browser_channel(self) -> Optional[str]:
        """Check if Microsoft Edge executable is available on Windows."""
        if sys.platform != "win32":
            return None
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        for p in edge_paths:
            if os.path.exists(p):
                return "msedge"
        return None

    def _route_guard(self, route: Route, request: Request) -> None:
        """Domain guard route interceptor: block unapproved external domains."""
        url = request.url
        if is_url_allowed(url):
            try:
                route.continue_()
            except Exception:
                pass
        else:
            logger.warning(f"DomainGuard blocked unapproved navigation/request: {url[:100]}")
            try:
                route.abort()
            except Exception:
                pass

    def start(self) -> Page:
        """Start the persistent browser context and return the primary page."""
        with self._lock:
            if self._page and not self._page.is_closed():
                return self._page

            logger.info("Initializing persistent browser profile...")
            os.makedirs(self._user_data_dir, exist_ok=True)
            self._playwright = sync_playwright().start()

            channel = self._determine_browser_channel()
            logger.info(f"Launching persistent browser context using channel: {channel or 'chromium'}")

            launch_kwargs = {
                "user_data_dir": self._user_data_dir,
                "headless": False,  # Run headed so it can be shown/minimized cleanly via Windows OS API
                "user_agent": DEFAULT_USER_AGENT,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
            }
            if channel:
                launch_kwargs["channel"] = channel

            self._context = self._playwright.chromium.launch_persistent_context(**launch_kwargs)

            # Register strict domain guard route filter
            self._context.route("**/*", self._route_guard)

            pages = self._context.pages
            self._page = pages[0] if pages else self._context.new_page()

            # Minimize initially to keep background by default
            minimize_sbi_browser()
            return self._page

    def get_page(self) -> Optional[Page]:
        with self._lock:
            if self._page and not self._page.is_closed():
                return self._page
            return None

    def show_browser(self) -> None:
        """Bring the real SBI browser window to foreground for user authentication."""
        with self._lock:
            self._is_visible = True
        restore_and_focus_sbi_browser()

    def hide_browser(self) -> None:
        """Minimize the SBI browser window to background."""
        with self._lock:
            self._is_visible = False
        minimize_sbi_browser()

    def close(self) -> None:
        """Gracefully shut down the browser and persistent context."""
        with self._lock:
            try:
                if self._page and not self._page.is_closed():
                    self._page.close()
            except Exception:
                pass
            finally:
                self._page = None

            try:
                if self._context:
                    self._context.close()
            except Exception:
                pass
            finally:
                self._context = None

            try:
                if self._playwright:
                    self._playwright.stop()
            except Exception:
                pass
            finally:
                self._playwright = None

            logger.info("Browser session closed.")

    def is_running(self) -> bool:
        with self._lock:
            return self._page is not None and not self._page.is_closed()
