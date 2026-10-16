"""
Account selection dialog for users with multiple SBI savings accounts.
Displays only masked account identifiers (e.g. ••••1234) and their balances.
"""

import tkinter as tk
from typing import Callable, List, Optional
from app.sbi.balance_parser import AccountInfo
from app.ui import theme


class AccountDialog(tk.Toplevel):
    """Modal dialog allowing the user to select their primary savings account."""

    def __init__(
        self,
        parent: tk.Tk,
        accounts: List[AccountInfo],
        current_suffix: Optional[str],
        on_selected: Callable[[str], None],
    ):
        super().__init__(parent)
        self.title("Select SBI Account")
        self.configure(bg=theme.BG_COLOR)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.accounts = accounts
        self.on_selected = on_selected
        self.selected_var = tk.StringVar()

        # Pre-select matching suffix or first account
        default_val = accounts[0].masked_number
        if current_suffix:
            clean = current_suffix.replace("•", "").strip()
            for acc in accounts:
                if acc.masked_number.endswith(clean):
                    default_val = acc.masked_number
                    break
        self.selected_var.set(default_val)

        self._build_ui()
        self._center_window(parent)

    def _build_ui(self) -> None:
        frame = tk.Frame(self, bg=theme.CARD_BG, padx=20, pady=20, highlightbackground=theme.CARD_BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        title_lbl = tk.Label(
            frame,
            text="Multiple Accounts Detected",
            font=theme.FONT_TITLE,
            fg=theme.TEXT_PRIMARY,
            bg=theme.CARD_BG,
        )
        title_lbl.pack(anchor="w", pady=(0, 5))

        desc_lbl = tk.Label(
            frame,
            text="Choose which account balance you wish to display on the widget:",
            font=theme.FONT_STATUS,
            fg=theme.TEXT_SECONDARY,
            bg=theme.CARD_BG,
            wraplength=320,
            justify="left",
        )
        desc_lbl.pack(anchor="w", pady=(0, 15))

        # Account radio buttons
        for acc in self.accounts:
            text = f"{acc.account_type} {acc.masked_number}   ({acc.formatted_balance})"
            rb = tk.Radiobutton(
                frame,
                text=text,
                variable=self.selected_var,
                value=acc.masked_number,
                font=theme.FONT_STATUS,
                fg=theme.TEXT_PRIMARY,
                bg=theme.CARD_BG,
                activebackground=theme.CARD_BG,
                activeforeground=theme.ACCENT_GREEN,
                selectcolor=theme.HEADER_BG,
            )
            rb.pack(anchor="w", pady=4)

        btn_frame = tk.Frame(frame, bg=theme.CARD_BG)
        btn_frame.pack(fill="x", pady=(20, 0))

        save_btn = tk.Button(
            btn_frame,
            text="Select Account",
            font=theme.FONT_BTN,
            bg=theme.ACCENT_BLUE,
            fg="#ffffff",
            activebackground=theme.BUTTON_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=4,
            command=self._on_confirm,
        )
        save_btn.pack(side="right")

    def _center_window(self, parent: tk.Tk) -> None:
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - (w // 2)
        py = parent.winfo_y() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

    def _on_confirm(self) -> None:
        selected = self.selected_var.get()
        if selected:
            self.on_selected(selected)
        self.destroy()
