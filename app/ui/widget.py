"""
Main desktop floating widget UI for SBI Balance Widget.
Draggable, borderless card with privacy mode, live status dot,
refresh action, and system tray minimization.
"""

import tkinter as tk
from datetime import datetime
from typing import Callable, Optional

from app.config import Config
from app.state import AuthState, StateManager
from app.ui import theme
from app.ui.settings_dialog import SettingsDialog


class BalanceWidget(tk.Tk):
    """Polished floating desktop card displaying the user's available SBI balance."""

    def __init__(
        self,
        config: Config,
        state_manager: StateManager,
        on_refresh_requested: Callable[[], None],
        on_reauth_requested: Callable[[], None],
        on_minimize_to_tray: Callable[[], None],
        on_exit_requested: Callable[[], None],
    ):
        super().__init__()
        self.config = config
        self.state_manager = state_manager
        self.on_refresh_requested = on_refresh_requested
        self.on_reauth_requested = on_reauth_requested
        self.on_minimize_to_tray = on_minimize_to_tray
        self.on_exit_requested = on_exit_requested

        # Dragging state
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Privacy mode & balance memory
        self._raw_balance_str: Optional[str] = self.config.last_known_balance
        self._privacy_mode: bool = self.config.privacy_mode
        self._is_cached: bool = False

        self._init_window()
        self._build_ui()
        self._apply_initial_state()

        # Listen for state changes
        self.state_manager.add_listener(self._on_state_changed)

    def _init_window(self) -> None:
        self.overrideredirect(True)  # Frameless card
        self.configure(bg=theme.BG_COLOR)
        self.attributes("-topmost", self.config.always_on_top)

        # Restore window position if saved, else default to top-right
        width = 270
        height = 145
        saved_x, saved_y = self.config.window_position

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        if saved_x is not None and saved_y is not None:
            x = max(0, min(saved_x, screen_w - width))
            y = max(0, min(saved_y, screen_h - height))
        else:
            x = screen_w - width - 30
            y = 50

        self.geometry(f"{width}x{height}+{x}+{y}")

        # Dragging bindings
        self.bind("<Button-1>", self._start_drag)
        self.bind("<B1-Motion>", self._do_drag)
        self.bind("<ButtonRelease-1>", self._end_drag)

    def _build_ui(self) -> None:
        # Outer border container
        self.card = tk.Frame(
            self,
            bg=theme.CARD_BG,
            highlightbackground=theme.CARD_BORDER,
            highlightthickness=1,
        )
        self.card.pack(fill="both", expand=True, padx=2, pady=2)

        # ----------------- HEADER -----------------
        header = tk.Frame(self.card, bg=theme.HEADER_BG, height=30)
        header.pack(fill="x", side="top")

        title_lbl = tk.Label(
            header,
            text="🏦 SBI BALANCE",
            font=theme.FONT_TITLE,
            fg=theme.TEXT_PRIMARY,
            bg=theme.HEADER_BG,
            padx=8,
            pady=4,
        )
        title_lbl.pack(side="left")

        # Header controls
        close_btn = tk.Button(
            header,
            text="✕",
            font=theme.FONT_TIMESTAMP,
            fg=theme.TEXT_MUTED,
            bg=theme.HEADER_BG,
            activeforeground=theme.TEXT_PRIMARY,
            activebackground=theme.BUTTON_HOVER,
            relief="flat",
            bd=0,
            padx=8,
            pady=2,
            command=self.on_minimize_to_tray,
        )
        close_btn.pack(side="right")

        settings_btn = tk.Button(
            header,
            text="⚙",
            font=theme.FONT_STATUS,
            fg=theme.TEXT_MUTED,
            bg=theme.HEADER_BG,
            activeforeground=theme.TEXT_PRIMARY,
            activebackground=theme.BUTTON_HOVER,
            relief="flat",
            bd=0,
            padx=6,
            pady=2,
            command=self._open_settings,
        )
        settings_btn.pack(side="right")

        # Bind dragging to header labels too
        title_lbl.bind("<Button-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._do_drag)
        title_lbl.bind("<ButtonRelease-1>", self._end_drag)
        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._do_drag)
        header.bind("<ButtonRelease-1>", self._end_drag)

        # ----------------- BODY / BALANCE -----------------
        body = tk.Frame(self.card, bg=theme.CARD_BG, padx=12, pady=10)
        body.pack(fill="both", expand=True)

        self.balance_lbl = tk.Label(
            body,
            text="Loading...",
            font=theme.FONT_BALANCE,
            fg=theme.ACCENT_GREEN,
            bg=theme.CARD_BG,
            cursor="hand2",
        )
        self.balance_lbl.pack(anchor="center", pady=(4, 0))
        self.balance_lbl.bind("<Button-1>", lambda e: self.toggle_privacy_mode())

        # Account suffix or prompt
        self.acc_lbl = tk.Label(
            body,
            text=self.config.selected_account_suffix or "Savings Account",
            font=theme.FONT_TIMESTAMP,
            fg=theme.TEXT_MUTED,
            bg=theme.CARD_BG,
        )
        self.acc_lbl.pack(anchor="center")

        # ----------------- FOOTER / STATUS BAR -----------------
        footer = tk.Frame(self.card, bg=theme.CARD_BG, padx=10, pady=4)
        footer.pack(fill="x", side="bottom")

        # Status Dot and Text
        status_frame = tk.Frame(footer, bg=theme.CARD_BG)
        status_frame.pack(side="left")

        self.status_dot = tk.Label(
            status_frame,
            text="●",
            font=theme.FONT_STATUS,
            fg=theme.ACCENT_AMBER,
            bg=theme.CARD_BG,
        )
        self.status_dot.pack(side="left", padx=(0, 4))

        self.status_text = tk.Label(
            status_frame,
            text="Connecting...",
            font=theme.FONT_TIMESTAMP,
            fg=theme.TEXT_SECONDARY,
            bg=theme.CARD_BG,
        )
        self.status_text.pack(side="left")

        # Refresh button
        self.refresh_btn = tk.Button(
            footer,
            text="↻ Refresh",
            font=theme.FONT_TIMESTAMP,
            fg=theme.TEXT_PRIMARY,
            bg=theme.BUTTON_BG,
            activeforeground=theme.TEXT_PRIMARY,
            activebackground=theme.BUTTON_HOVER,
            relief="flat",
            bd=0,
            padx=6,
            pady=1,
            cursor="hand2",
            command=self._on_refresh_clicked,
        )
        self.refresh_btn.pack(side="right")

    def _apply_initial_state(self) -> None:
        if self._raw_balance_str:
            self._render_balance_display()
            ts = self.config.last_balance_timestamp or ""
            self.set_status(theme.ACCENT_GREEN, f"Updated {ts}" if ts else "Cached")
        else:
            self.balance_lbl.config(text="--", fg=theme.TEXT_MUTED)
            self.set_status(theme.ACCENT_AMBER, "Initializing...")

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _do_drag(self, event: tk.Event) -> None:
        x = self.winfo_x() + (event.x - self._drag_start_x)
        y = self.winfo_y() + (event.y - self._drag_start_y)
        self.geometry(f"+{x}+{y}")

    def _end_drag(self, event: tk.Event) -> None:
        self.config.set_window_position(self.winfo_x(), self.winfo_y())

    def toggle_privacy_mode(self) -> None:
        """Toggle privacy masking (₹ 24,582.37 <-> ₹ ••••••••)."""
        self._privacy_mode = not self._privacy_mode
        self.config.privacy_mode = self._privacy_mode
        self._render_balance_display()

    def set_balance(self, balance_str: str, account_suffix: Optional[str] = None, is_cached: bool = False) -> None:
        """Update the displayed balance safely on the UI thread."""
        self.after(0, self._set_balance_impl, balance_str, account_suffix, is_cached)

    def _set_balance_impl(self, balance_str: str, account_suffix: Optional[str], is_cached: bool) -> None:
        self._raw_balance_str = balance_str
        self._is_cached = is_cached
        if account_suffix:
            self.acc_lbl.config(text=f"Savings Account {account_suffix}")
        self._render_balance_display()

    def _render_balance_display(self) -> None:
        if not self._raw_balance_str:
            self.balance_lbl.config(text="--", fg=theme.TEXT_MUTED)
            return

        if self._privacy_mode:
            self.balance_lbl.config(text="₹ ••••••••", fg=theme.TEXT_PRIMARY)
        else:
            color = theme.TEXT_SECONDARY if self._is_cached else theme.ACCENT_GREEN
            self.balance_lbl.config(text=self._raw_balance_str, fg=color)

    def set_status(self, dot_color: str, text: str) -> None:
        """Update status dot color and label."""
        self.after(0, self._set_status_impl, dot_color, text)

    def _set_status_impl(self, dot_color: str, text: str) -> None:
        self.status_dot.config(fg=dot_color)
        self.status_text.config(text=text)

    def _on_refresh_clicked(self) -> None:
        self.set_status(theme.ACCENT_AMBER, "Refreshing...")
        self.on_refresh_requested()

    def _open_settings(self) -> None:
        SettingsDialog(
            self,
            self.config,
            on_reauth_requested=self.on_reauth_requested,
            on_settings_saved=self._on_settings_saved,
        )

    def _on_settings_saved(self) -> None:
        self.attributes("-topmost", self.config.always_on_top)

    def _on_state_changed(self, old_state: AuthState, new_state: AuthState, msg: Optional[str]) -> None:
        """Handle state machine events and update UI accordingly."""
        self.after(0, self._handle_state_update, new_state, msg)

    def _handle_state_update(self, state: AuthState, msg: Optional[str]) -> None:
        if state == AuthState.STARTING or state == AuthState.CHECKING_SESSION:
            self.set_status(theme.ACCENT_AMBER, "Checking session...")
        elif state == AuthState.AUTHENTICATED or state == AuthState.READING_BALANCE:
            self.set_status(theme.ACCENT_AMBER, "Reading balance...")
        elif state == AuthState.MONITORING:
            now_str = datetime.now().strftime("%H:%M")
            self.set_status(theme.ACCENT_GREEN, f"Updated {now_str}")
        elif state == AuthState.AUTHENTICATION_REQUIRED or state == AuthState.SBI_LOGIN:
            self.set_status(theme.ACCENT_RED, "Login required")
        elif state == AuthState.CAPTCHA_REQUIRED:
            self.set_status(theme.ACCENT_AMBER, "Solve CAPTCHA on SBI")
        elif state == AuthState.OTP_REQUIRED:
            self.set_status(theme.ACCENT_AMBER, "Enter OTP on SBI")
        elif state == AuthState.SESSION_EXPIRED:
            self.set_status(theme.ACCENT_RED, "Session expired")
        elif state == AuthState.NETWORK_ERROR:
            ts = self.config.last_balance_timestamp or ""
            status_lbl = f"{ts} (cached)" if ts else "Unavailable"
            self.set_status(theme.TEXT_MUTED, status_lbl)
            self._is_cached = True
            self._render_balance_display()
        elif state == AuthState.UNEXPECTED_REDIRECT:
            self.set_status(theme.ACCENT_RED, "Blocked redirect")
        elif state == AuthState.BROWSER_ERROR:
            self.set_status(theme.ACCENT_RED, "Browser error")
