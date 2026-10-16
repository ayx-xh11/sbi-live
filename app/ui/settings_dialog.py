"""
Settings dialog for SBI Balance Desktop Widget.
Allows configuration of Windows Credential Manager, refresh intervals,
startup settings, and manual re-authentication.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

from app.config import Config
from app.security.credentials import (
    delete_credentials,
    get_saved_credentials,
    has_credentials,
    save_credentials,
)
from app.ui import theme


class SettingsDialog(tk.Toplevel):
    """Modal dialog for application preferences and credential management."""

    def __init__(
        self,
        parent: tk.Tk,
        config: Config,
        on_reauth_requested: Callable[[], None],
        on_settings_saved: Callable[[], None],
    ):
        super().__init__(parent)
        self.title("SBI Widget Settings")
        self.configure(bg=theme.BG_COLOR)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.config = config
        self.on_reauth_requested = on_reauth_requested
        self.on_settings_saved = on_settings_saved

        self._build_ui()
        self._center_window(parent)

    def _build_ui(self) -> None:
        container = tk.Frame(
            self,
            bg=theme.CARD_BG,
            padx=20,
            pady=20,
            highlightbackground=theme.CARD_BORDER,
            highlightthickness=1,
        )
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # ----------------- SECTION 1: CREDENTIALS -----------------
        sec1_title = tk.Label(
            container,
            text="SBI Internet Banking Credentials",
            font=theme.FONT_TITLE,
            fg=theme.TEXT_PRIMARY,
            bg=theme.CARD_BG,
        )
        sec1_title.pack(anchor="w", pady=(0, 2))

        sec1_desc = tk.Label(
            container,
            text="Credentials are encrypted directly inside Windows Credential Manager.",
            font=theme.FONT_TIMESTAMP,
            fg=theme.TEXT_SECONDARY,
            bg=theme.CARD_BG,
        )
        sec1_desc.pack(anchor="w", pady=(0, 10))

        # Username
        u_frame = tk.Frame(container, bg=theme.CARD_BG)
        u_frame.pack(fill="x", pady=2)
        tk.Label(u_frame, text="Username:", font=theme.FONT_STATUS, fg=theme.TEXT_SECONDARY, bg=theme.CARD_BG, width=12, anchor="w").pack(side="left")
        self.username_entry = tk.Entry(u_frame, font=theme.FONT_STATUS, bg=theme.BG_COLOR, fg=theme.TEXT_PRIMARY, insertbackground=theme.TEXT_PRIMARY, relief="flat", highlightbackground=theme.CARD_BORDER, highlightthickness=1)
        self.username_entry.pack(side="left", fill="x", expand=True)

        # Password
        p_frame = tk.Frame(container, bg=theme.CARD_BG)
        p_frame.pack(fill="x", pady=4)
        tk.Label(p_frame, text="Password:", font=theme.FONT_STATUS, fg=theme.TEXT_SECONDARY, bg=theme.CARD_BG, width=12, anchor="w").pack(side="left")
        self.password_entry = tk.Entry(p_frame, show="•", font=theme.FONT_STATUS, bg=theme.BG_COLOR, fg=theme.TEXT_PRIMARY, insertbackground=theme.TEXT_PRIMARY, relief="flat", highlightbackground=theme.CARD_BORDER, highlightthickness=1)
        self.password_entry.pack(side="left", fill="x", expand=True)

        # Pre-fill username if exists
        saved_creds = get_saved_credentials()
        if saved_creds:
            self.username_entry.insert(0, saved_creds[0])

        # Credential status & action buttons
        cred_btn_frame = tk.Frame(container, bg=theme.CARD_BG)
        cred_btn_frame.pack(fill="x", pady=(8, 15))

        self.cred_status_lbl = tk.Label(
            cred_btn_frame,
            text="● Saved in Windows Vault" if has_credentials() else "○ No credentials stored",
            font=theme.FONT_TIMESTAMP,
            fg=theme.ACCENT_GREEN if has_credentials() else theme.TEXT_MUTED,
            bg=theme.CARD_BG,
        )
        self.cred_status_lbl.pack(side="left")

        save_cred_btn = tk.Button(
            cred_btn_frame,
            text="Save to Windows",
            font=theme.FONT_STATUS,
            bg=theme.BUTTON_BG,
            fg=theme.TEXT_PRIMARY,
            relief="flat",
            padx=8,
            pady=2,
            command=self._on_save_credentials,
        )
        save_cred_btn.pack(side="right", padx=(4, 0))

        del_cred_btn = tk.Button(
            cred_btn_frame,
            text="Remove",
            font=theme.FONT_STATUS,
            bg=theme.BUTTON_BG,
            fg=theme.ACCENT_RED,
            relief="flat",
            padx=8,
            pady=2,
            command=self._on_delete_credentials,
        )
        del_cred_btn.pack(side="right")

        # ----------------- SECTION 2: REFRESH INTERVAL -----------------
        sep1 = tk.Frame(container, height=1, bg=theme.CARD_BORDER)
        sep1.pack(fill="x", pady=(0, 12))

        sec2_title = tk.Label(
            container,
            text="Automatic Balance Refresh",
            font=theme.FONT_TITLE,
            fg=theme.TEXT_PRIMARY,
            bg=theme.CARD_BG,
        )
        sec2_title.pack(anchor="w", pady=(0, 4))

        self.interval_var = tk.IntVar(value=self.config.refresh_interval_minutes)
        intervals_frame = tk.Frame(container, bg=theme.CARD_BG)
        intervals_frame.pack(fill="x", pady=(0, 15))

        options = [
            ("5 min", 5),
            ("10 min", 10),
            ("15 min", 15),
            ("30 min", 30),
            ("Manual only", 0),
        ]
        for lbl, val in options:
            rb = tk.Radiobutton(
                intervals_frame,
                text=lbl,
                variable=self.interval_var,
                value=val,
                font=theme.FONT_STATUS,
                fg=theme.TEXT_PRIMARY,
                bg=theme.CARD_BG,
                activebackground=theme.CARD_BG,
                activeforeground=theme.ACCENT_GREEN,
                selectcolor=theme.HEADER_BG,
            )
            rb.pack(side="left", padx=(0, 10))

        # ----------------- SECTION 3: PREFERENCES -----------------
        sep2 = tk.Frame(container, height=1, bg=theme.CARD_BORDER)
        sep2.pack(fill="x", pady=(0, 12))

        sec3_title = tk.Label(
            container,
            text="Preferences",
            font=theme.FONT_TITLE,
            fg=theme.TEXT_PRIMARY,
            bg=theme.CARD_BG,
        )
        sec3_title.pack(anchor="w", pady=(0, 6))

        self.topmost_var = tk.BooleanVar(value=self.config.always_on_top)
        topmost_cb = tk.Checkbutton(
            container,
            text="Always on Top (keep widget floating over other windows)",
            variable=self.topmost_var,
            font=theme.FONT_STATUS,
            fg=theme.TEXT_PRIMARY,
            bg=theme.CARD_BG,
            activebackground=theme.CARD_BG,
            activeforeground=theme.ACCENT_GREEN,
            selectcolor=theme.HEADER_BG,
        )
        topmost_cb.pack(anchor="w", pady=2)

        self.startup_var = tk.BooleanVar(value=self.config.start_with_windows)
        startup_cb = tk.Checkbutton(
            container,
            text="Start with Windows automatically (HKCU Run)",
            variable=self.startup_var,
            font=theme.FONT_STATUS,
            fg=theme.TEXT_PRIMARY,
            bg=theme.CARD_BG,
            activebackground=theme.CARD_BG,
            activeforeground=theme.ACCENT_GREEN,
            selectcolor=theme.HEADER_BG,
        )
        startup_cb.pack(anchor="w", pady=2)

        # ----------------- ACTIONS BAR -----------------
        sep3 = tk.Frame(container, height=1, bg=theme.CARD_BORDER)
        sep3.pack(fill="x", pady=(15, 15))

        action_frame = tk.Frame(container, bg=theme.CARD_BG)
        action_frame.pack(fill="x")

        reauth_btn = tk.Button(
            action_frame,
            text="🔐 Re-authenticate Now",
            font=theme.FONT_STATUS,
            bg=theme.BUTTON_BG,
            fg=theme.ACCENT_AMBER,
            relief="flat",
            padx=10,
            pady=4,
            command=self._on_reauth,
        )
        reauth_btn.pack(side="left")

        save_close_btn = tk.Button(
            action_frame,
            text="Save & Close",
            font=theme.FONT_BTN,
            bg=theme.ACCENT_BLUE,
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=4,
            command=self._on_save_all,
        )
        save_close_btn.pack(side="right")

    def _on_save_credentials(self) -> None:
        user = self.username_entry.get().strip()
        pwd = self.password_entry.get()
        if not user or not pwd:
            messagebox.showwarning("Missing Fields", "Please enter both Username and Password to store.", parent=self)
            return

        success = save_credentials(user, pwd)
        if success:
            self.cred_status_lbl.config(text="● Saved in Windows Vault", fg=theme.ACCENT_GREEN)
            messagebox.showinfo("Saved", "Credentials stored securely in Windows Credential Manager.", parent=self)
        else:
            messagebox.showerror("Error", "Failed to save credentials to Windows Credential Manager.", parent=self)

    def _on_delete_credentials(self) -> None:
        if delete_credentials():
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.cred_status_lbl.config(text="○ No credentials stored", fg=theme.TEXT_MUTED)
            messagebox.showinfo("Removed", "Credentials removed from Windows Credential Manager.", parent=self)

    def _on_reauth(self) -> None:
        self.destroy()
        self.on_reauth_requested()

    def _on_save_all(self) -> None:
        # Save interval
        self.config.refresh_interval_minutes = self.interval_var.get()
        # Save always on top
        self.config.always_on_top = self.topmost_var.get()
        # Save start with windows
        self.config.start_with_windows = self.startup_var.get()

        self.on_settings_saved()
        self.destroy()

    def _center_window(self, parent: tk.Tk) -> None:
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - (w // 2)
        py = parent.winfo_y() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"+{max(0, px)}+{max(0, py)}")
