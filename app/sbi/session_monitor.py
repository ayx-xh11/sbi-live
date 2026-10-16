"""
Session monitor and balance retrieval coordinator.
Periodically checks the SBI session, keeps the session alive,
retrieves the Available Balance, and updates application state.
"""

import threading
import time
from datetime import datetime
from typing import Callable, List, Optional

from app.config import Config
from app.state import AuthState, StateManager
from app.browser.browser_manager import BrowserManager
from app.sbi.auth_flow import AuthFlow
from app.sbi.balance_parser import AccountInfo, extract_accounts_from_text, select_account_balance
from app.security.safe_logger import logger


class SessionMonitor:
    """Coordinates background balance polling, session keep-alive, and notifications."""

    def __init__(
        self,
        config: Config,
        state_manager: StateManager,
        browser_manager: BrowserManager,
        on_balance_updated: Optional[Callable[[AccountInfo, List[AccountInfo]], None]] = None,
    ):
        self.config = config
        self.state_manager = state_manager
        self.browser_manager = browser_manager
        self.auth_flow = AuthFlow(browser_manager, state_manager)
        self.on_balance_updated = on_balance_updated

        self._stop_event = threading.Event()
        self._refresh_trigger = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._is_paused = False

    def start(self) -> None:
        """Start the background monitor worker thread."""
        with self._lock:
            if self._worker_thread and self._worker_thread.is_alive():
                return
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="SBISessionMonitor")
            self._worker_thread.start()
            logger.info("SessionMonitor worker thread started.")

    def stop(self) -> None:
        """Stop the background monitor worker thread."""
        self._stop_event.set()
        self._refresh_trigger.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        self.browser_manager.close()
        logger.info("SessionMonitor worker thread stopped.")

    def trigger_manual_refresh(self) -> None:
        """Request an immediate refresh."""
        logger.info("Manual refresh requested.")
        self._refresh_trigger.set()

    def set_paused(self, paused: bool) -> None:
        with self._lock:
            self._is_paused = paused
        logger.info(f"Session monitoring paused={paused}")

    def is_paused(self) -> bool:
        with self._lock:
            return self._is_paused

    def refresh_balance_now(self) -> Optional[AccountInfo]:
        """Perform a single synchronous balance refresh cycle."""
        try:
            page = self.browser_manager.start()

            # Ensure authenticated
            if not self.auth_flow.check_is_authenticated(page):
                logger.info("Session check: Authentication required before balance refresh.")
                success = self.auth_flow.execute_auth_flow()
                if not success:
                    return None

            self.state_manager.set_state(AuthState.READING_BALANCE, "Retrieving current Available Balance...")

            # Reveal hidden balances if required
            self.auth_flow.trigger_balance_toggles_if_present(page)
            page.wait_for_timeout(2000)

            # Extract page text
            page_text = page.inner_text("body")
            accounts = extract_accounts_from_text(page_text)

            if not accounts:
                logger.warning("No savings accounts parsed from page text. Checking if structure changed.")
                self.state_manager.set_state(AuthState.SITE_CHANGED, "Unable to find account balance on page.")
                return None

            selected = select_account_balance(accounts, self.config.selected_account_suffix)
            if selected:
                now_str = datetime.now().strftime("%H:%M")
                self.config.set_cached_balance(selected.formatted_balance, now_str)
                logger.info("Available Balance successfully retrieved.")

                if self.on_balance_updated:
                    try:
                        self.on_balance_updated(selected, accounts)
                    except Exception as e:
                        logger.error(f"Error in on_balance_updated callback: {e}")

                self.state_manager.set_state(AuthState.MONITORING, f"Updated at {now_str}")
                return selected

        except Exception as e:
            logger.error(f"Error during balance refresh: {e}")
            self.state_manager.set_state(AuthState.NETWORK_ERROR, f"Balance check error: {e}")

        return None

    def _monitor_loop(self) -> None:
        """Main worker loop handling periodic refresh and keep-alive."""
        logger.info("Entering session monitor loop.")

        # Initial check upon launch
        if not self._stop_event.is_set():
            self.refresh_balance_now()

        while not self._stop_event.is_set():
            interval_mins = self.config.refresh_interval_minutes
            if interval_mins > 0:
                sleep_seconds = interval_mins * 60
            else:
                sleep_seconds = 86400  # Manual only: wait for trigger or stop

            # Wait for either the interval to elapse or a manual refresh trigger
            triggered = self._refresh_trigger.wait(timeout=sleep_seconds)
            self._refresh_trigger.clear()

            if self._stop_event.is_set():
                break

            if self.is_paused() and not triggered:
                continue

            # Execute balance refresh
            self.refresh_balance_now()
