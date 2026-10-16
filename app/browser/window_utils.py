"""
Windows OS-level window management utilities using ctypes/user32.
Minimizes or brings the SBI browser window to foreground reliably.
"""

import sys
from typing import List
from app.security.safe_logger import logger

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    # Window Show Constants
    SW_HIDE = 0
    SW_SHOWNORMAL = 1
    SW_SHOWMINIMIZED = 2
    SW_MAXIMIZE = 3
    SW_SHOWNOACTIVATE = 4
    SW_SHOW = 5
    SW_MINIMIZE = 6
    SW_SHOWMINNOACTIVE = 7
    SW_SHOWNA = 8
    SW_RESTORE = 9

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


    def find_sbi_browser_hwnds() -> List[int]:
        """Find window HWNDs that match SBI browser titles."""
        hwnds: List[int] = []

        def enum_windows_callback(hwnd: wintypes.HWND, lParam: wintypes.LPARAM) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value

            # Match YONO SBI, State Bank of India, or SBI banking window titles
            keywords = ["YONO SBI", "State Bank of India", "SBI", "onlinesbi"]
            for kw in keywords:
                if kw.lower() in title.lower():
                    hwnds.append(hwnd)
                    break
            return True

        cb = WNDENUMPROC(enum_windows_callback)
        user32.EnumWindows(cb, 0)
        return hwnds


    def minimize_sbi_browser() -> None:
        """Minimize all detected SBI browser windows to keep them hidden during normal operation."""
        try:
            hwnds = find_sbi_browser_hwnds()
            for hwnd in hwnds:
                user32.ShowWindow(hwnd, SW_MINIMIZE)
            if hwnds:
                logger.debug(f"Minimized {len(hwnds)} SBI browser window(s)")
        except Exception as e:
            logger.debug(f"Error minimizing SBI browser window: {e}")


    def restore_and_focus_sbi_browser() -> None:
        """Restore the SBI browser window and bring it to the foreground for user interaction."""
        try:
            hwnds = find_sbi_browser_hwnds()
            for hwnd in hwnds:
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
            if hwnds:
                logger.info("Restored SBI browser window to foreground for user verification")
        except Exception as e:
            logger.debug(f"Error restoring SBI browser window: {e}")

else:
    # Non-Windows stub
    def find_sbi_browser_hwnds() -> List[int]:
        return []

    def minimize_sbi_browser() -> None:
        pass

    def restore_and_focus_sbi_browser() -> None:
        pass
