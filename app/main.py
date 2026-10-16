"""
Application entry point and lifecycle coordinator for SBI Balance Desktop Widget.
Integrates the floating widget UI, system tray, browser session, and background monitor.
"""

import sys
from typing import List, Optional

from app.config import Config
from app.state import AuthState, StateManager
from app.browser.browser_manager import BrowserManager
from app.sbi.balance_parser import AccountInfo
from app.sbi.session_monitor import SessionMonitor
from app.ui.widget import BalanceWidget
from app.ui.account_dialog import AccountDialog
from app.ui.tray_icon import SystemTrayManager
from app.security.safe_logger import logger


class Application:
    """Coordinates UI, background monitor, browser session, and system tray."""

    def __init__(self):
        self.config = Config()
        self.state_manager = StateManager()
        self.browser_manager = BrowserManager()

        # Build Widget UI
        self.widget = BalanceWidget(
            config=self.config,
            state_manager=self.state_manager,
            on_refresh_requested=self.on_refresh_requested,
            on_reauth_requested=self.on_reauth_requested,
            on_minimize_to_tray=self.on_minimize_to_tray,
            on_exit_requested=self.on_exit,
        )

        # Background Session Monitor
        self.monitor = SessionMonitor(
            config=self.config,
            state_manager=self.state_manager,
            browser_manager=self.browser_manager,
            on_balance_updated=self.on_balance_updated,
        )

        # System Tray Icon
        self.tray = SystemTrayManager(
            on_show_widget=self.on_show_widget,
            on_refresh=self.on_refresh_requested,
            on_reauth=self.on_reauth_requested,
            on_settings=self.on_open_settings,
            on_toggle_pause=self.on_toggle_pause,
            on_exit=self.on_exit,
        )

    def on_balance_updated(self, selected: AccountInfo, all_accounts: List[AccountInfo]) -> None:
        """Called by background monitor when a new balance is read."""
        self.widget.set_balance(selected.formatted_balance, selected.masked_number, is_cached=False)

        # If user has multiple accounts and none explicitly selected yet, prompt them
        if len(all_accounts) > 1 and not self.config.selected_account_suffix:
            self.widget.after(500, self._show_account_selection_dialog, all_accounts)

    def _show_account_selection_dialog(self, all_accounts: List[AccountInfo]) -> None:
        def on_selected(suffix: str) -> None:
            self.config.selected_account_suffix = suffix
            self.monitor.trigger_manual_refresh()

        AccountDialog(
            parent=self.widget,
            accounts=all_accounts,
            current_suffix=self.config.selected_account_suffix,
            on_selected=on_selected,
        )

    def on_refresh_requested(self) -> None:
        self.monitor.trigger_manual_refresh()

    def on_reauth_requested(self) -> None:
        """Trigger interactive authentication flow."""
        def reauth_task():
            self.browser_manager.show_browser()
            self.monitor.auth_flow.execute_auth_flow()
            self.monitor.trigger_manual_refresh()

        import threading
        t = threading.Thread(target=reauth_task, daemon=True)
        t.start()

    def on_minimize_to_tray(self) -> None:
        """Hide widget window and keep running in system tray."""
        self.widget.withdraw()
        logger.info("Widget minimized to system tray.")

    def on_show_widget(self) -> None:
        """Restore widget from system tray."""
        def _restore():
            self.widget.deiconify()
            self.widget.lift()
            self.widget.attributes("-topmost", self.config.always_on_top)
        self.widget.after(0, _restore)

    def on_open_settings(self) -> None:
        self.widget.after(0, self.widget._open_settings)

    def on_toggle_pause(self) -> None:
        paused = not self.monitor.is_paused()
        self.monitor.set_paused(paused)

    def on_exit(self) -> None:
        """Clean shutdown of background threads and UI."""
        logger.info("Exiting application...")
        try:
            self.monitor.stop()
        except Exception:
            pass

        try:
            self.widget.quit()
        except Exception:
            pass

    def run(self) -> None:
        """Start background services and Tkinter event loop."""
        logger.info("Starting SBI Balance Widget application...")
        self.monitor.start()
        self.tray.start()
        self.widget.mainloop()


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
