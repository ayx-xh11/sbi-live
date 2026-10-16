"""
Configuration management for SBI Balance Desktop Widget.
Handles persistent settings, directories in %APPDATA%, and Windows Startup registry.
"""

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional

# Base Application Directories
_app_data_env = os.environ.get("APPDATA")
if _app_data_env:
    APP_DIR = Path(_app_data_env) / "SBIBalanceWidget"
else:
    APP_DIR = Path.home() / ".sbi_balance_widget"

PROFILE_DIR = APP_DIR / "profile"
LOGS_DIR = APP_DIR / "logs"
SETTINGS_FILE = APP_DIR / "settings.json"

# Ensure directories exist
APP_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Allowed refresh intervals in minutes (0 represents manual-only)
ALLOWED_INTERVALS = [5, 10, 15, 30, 0]
DEFAULT_INTERVAL_MINUTES = 15

REGISTRY_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
REGISTRY_APP_NAME = "SBIBalanceWidget"


class Config:
    """Manages application settings with JSON persistence and Windows startup integration."""

    def __init__(self, settings_path: Optional[Path] = None):
        self._path = settings_path or SETTINGS_FILE
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {
            "refresh_interval_minutes": DEFAULT_INTERVAL_MINUTES,
            "always_on_top": True,
            "privacy_mode": False,
            "start_with_windows": False,
            "selected_account_suffix": None,
            "window_x": None,
            "window_y": None,
            "last_known_balance": None,
            "last_balance_timestamp": None,
        }
        self.load()

    def load(self) -> None:
        with self._lock:
            if self._path.exists():
                try:
                    with open(self._path, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                        if isinstance(saved, dict):
                            self._data.update(saved)
                except Exception:
                    # If corrupt, keep defaults
                    pass

    def save(self) -> None:
        with self._lock:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2)
            except Exception:
                pass

    @property
    def refresh_interval_minutes(self) -> int:
        with self._lock:
            val = self._data.get("refresh_interval_minutes", DEFAULT_INTERVAL_MINUTES)
            return val if val in ALLOWED_INTERVALS else DEFAULT_INTERVAL_MINUTES

    @refresh_interval_minutes.setter
    def refresh_interval_minutes(self, val: int) -> None:
        if val in ALLOWED_INTERVALS:
            with self._lock:
                self._data["refresh_interval_minutes"] = val
            self.save()

    @property
    def always_on_top(self) -> bool:
        with self._lock:
            return bool(self._data.get("always_on_top", True))

    @always_on_top.setter
    def always_on_top(self, val: bool) -> None:
        with self._lock:
            self._data["always_on_top"] = bool(val)
        self.save()

    @property
    def privacy_mode(self) -> bool:
        with self._lock:
            return bool(self._data.get("privacy_mode", False))

    @privacy_mode.setter
    def privacy_mode(self, val: bool) -> None:
        with self._lock:
            self._data["privacy_mode"] = bool(val)
        self.save()

    @property
    def start_with_windows(self) -> bool:
        with self._lock:
            return bool(self._data.get("start_with_windows", False))

    @start_with_windows.setter
    def start_with_windows(self, enable: bool) -> None:
        success = set_windows_startup(enable)
        with self._lock:
            self._data["start_with_windows"] = enable if success else is_windows_startup_enabled()
        self.save()

    @property
    def selected_account_suffix(self) -> Optional[str]:
        with self._lock:
            return self._data.get("selected_account_suffix")

    @selected_account_suffix.setter
    def selected_account_suffix(self, suffix: Optional[str]) -> None:
        with self._lock:
            self._data["selected_account_suffix"] = suffix
        self.save()

    @property
    def window_position(self) -> tuple[Optional[int], Optional[int]]:
        with self._lock:
            return self._data.get("window_x"), self._data.get("window_y")

    def set_window_position(self, x: int, y: int) -> None:
        with self._lock:
            self._data["window_x"] = x
            self._data["window_y"] = y
        self.save()

    @property
    def last_known_balance(self) -> Optional[str]:
        with self._lock:
            return self._data.get("last_known_balance")

    @property
    def last_balance_timestamp(self) -> Optional[str]:
        with self._lock:
            return self._data.get("last_balance_timestamp")

    def set_cached_balance(self, balance_str: str, timestamp_str: str) -> None:
        with self._lock:
            self._data["last_known_balance"] = balance_str
            self._data["last_balance_timestamp"] = timestamp_str
        self.save()


def get_launch_command() -> str:
    """Determine the exact command string for Windows startup."""
    if getattr(sys, "frozen", False):
        # Running as compiled PyInstaller executable
        return f'"{sys.executable}"'
    else:
        # Running as Python script; use pythonw.exe if available to avoid opening console
        python_exe = sys.executable
        if "python.exe" in python_exe.lower():
            pythonw = python_exe.lower().replace("python.exe", "pythonw.exe")
            if os.path.exists(pythonw):
                python_exe = pythonw
        entry_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "run_widget.py"))
        return f'"{python_exe}" "{entry_script}"'


def is_windows_startup_enabled() -> bool:
    """Check if the app is registered in HKCU Run registry."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_RUN_KEY, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, REGISTRY_APP_NAME)
            return bool(val)
    except Exception:
        return False


def set_windows_startup(enable: bool) -> bool:
    """Register or unregister app in HKCU Run registry."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_RUN_KEY, 0, winreg.KEY_ALL_ACCESS) as key:
            if enable:
                cmd = get_launch_command()
                winreg.SetValueEx(key, REGISTRY_APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, REGISTRY_APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False
