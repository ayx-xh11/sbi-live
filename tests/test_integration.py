"""
Integration tests for cached balance handling and session monitor state transitions.
"""

from unittest.mock import MagicMock, patch
from app.config import Config
from app.state import AuthState, StateManager
from app.sbi.balance_parser import AccountInfo
from app.sbi.session_monitor import SessionMonitor


def test_offline_cached_balance_behavior(tmp_path):
    test_settings = tmp_path / "settings_offline.json"
    cfg = Config(settings_path=test_settings)
    cfg.set_cached_balance("₹ 24,582.37", "18:42")

    sm = StateManager()
    browser_mock = MagicMock()

    # Simulate network failure during balance check
    browser_mock.start.side_effect = Exception("Connection refused / Offline")

    monitor = SessionMonitor(config=cfg, state_manager=sm, browser_manager=browser_mock)
    res = monitor.refresh_balance_now()

    # Must return None, state must become NETWORK_ERROR, but cached balance remains safe in config
    assert res is None
    assert sm.current_state == AuthState.NETWORK_ERROR
    assert cfg.last_known_balance == "₹ 24,582.37"
    assert cfg.last_balance_timestamp == "18:42"


def test_session_monitor_pause_and_resume():
    cfg = MagicMock()
    sm = StateManager()
    browser_mock = MagicMock()

    monitor = SessionMonitor(config=cfg, state_manager=sm, browser_manager=browser_mock)
    assert monitor.is_paused() is False

    monitor.set_paused(True)
    assert monitor.is_paused() is True

    monitor.set_paused(False)
    assert monitor.is_paused() is False
