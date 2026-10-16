"""
System tray integration for SBI Balance Desktop Widget using pystray.
Provides a background tray icon with menu actions to open, refresh, authenticate, or exit.
"""

import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item
from app.security.safe_logger import logger


def create_tray_icon_image() -> Image.Image:
    """Generate a clean 64x64 tray icon image."""
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer circle
    draw.ellipse((4, 4, 60, 60), fill="#27272a", outline="#10b981", width=3)

    # Inner Rupee symbol '₹'
    try:
        # Draw Rupee text
        font = ImageFont.truetype("arial.ttf", 32)
        draw.text((22, 14), "₹", fill="#10b981", font=font)
    except Exception:
        # Fallback simple lines
        draw.line((20, 22, 44, 22), fill="#10b981", width=3)
        draw.line((20, 30, 40, 30), fill="#10b981", width=3)
        draw.line((26, 22, 26, 44), fill="#10b981", width=3)

    return img


class SystemTrayManager:
    """Controls the Windows notification area tray icon."""

    def __init__(
        self,
        on_show_widget: Callable[[], None],
        on_refresh: Callable[[], None],
        on_reauth: Callable[[], None],
        on_settings: Callable[[], None],
        on_toggle_pause: Callable[[], None],
        on_exit: Callable[[], None],
    ):
        self.on_show_widget = on_show_widget
        self.on_refresh = on_refresh
        self.on_reauth = on_reauth
        self.on_settings = on_settings
        self.on_toggle_pause = on_toggle_pause
        self.on_exit = on_exit

        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the system tray icon in a dedicated daemon thread."""
        image = create_tray_icon_image()
        menu = pystray.Menu(
            item("Open Widget", lambda: self.on_show_widget(), default=True),
            item("Refresh Balance", lambda: self.on_refresh()),
            item("Authenticate SBI", lambda: self.on_reauth()),
            item("Settings", lambda: self.on_settings()),
            item("Pause / Resume", lambda: self.on_toggle_pause()),
            pystray.Menu.SEPARATOR,
            item("Exit", lambda: self.stop()),
        )

        self._icon = pystray.Icon("SBIBalanceWidget", image, "SBI Balance Widget", menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True, name="SBITrayThread")
        self._thread.start()
        logger.info("System tray icon initialized.")

    def stop(self) -> None:
        """Stop and remove tray icon, and trigger app exit."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
        self.on_exit()
