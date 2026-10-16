"""
Unit tests for configuration loading, saving, and defaults.
"""

import os
from pathlib import Path
from app.config import Config, DEFAULT_INTERVAL_MINUTES


def test_config_defaults(tmp_path: Path):
    test_file = tmp_path / "settings_test.json"
    cfg = Config(settings_path=test_file)

    assert cfg.refresh_interval_minutes == DEFAULT_INTERVAL_MINUTES
    assert cfg.always_on_top is True
    assert cfg.privacy_mode is False
    assert cfg.start_with_windows is False
    assert cfg.selected_account_suffix is None


def test_config_persistence(tmp_path: Path):
    test_file = tmp_path / "settings_test.json"
    cfg1 = Config(settings_path=test_file)

    cfg1.refresh_interval_minutes = 30
    cfg1.always_on_top = False
    cfg1.privacy_mode = True
    cfg1.selected_account_suffix = "••••4521"
    cfg1.set_window_position(350, 200)
    cfg1.set_cached_balance("₹ 24,582.37", "18:42")

    # Reload from disk in a fresh Config instance
    cfg2 = Config(settings_path=test_file)
    assert cfg2.refresh_interval_minutes == 30
    assert cfg2.always_on_top is False
    assert cfg2.privacy_mode is True
    assert cfg2.selected_account_suffix == "••••4521"
    assert cfg2.window_position == (350, 200)
    assert cfg2.last_known_balance == "₹ 24,582.37"
    assert cfg2.last_balance_timestamp == "18:42"


def test_invalid_interval_fallback(tmp_path: Path):
    test_file = tmp_path / "settings_test.json"
    cfg = Config(settings_path=test_file)

    # Attempt to assign an unsupported interval
    cfg.refresh_interval_minutes = 999
    # Must fallback or retain valid interval
    assert cfg.refresh_interval_minutes == DEFAULT_INTERVAL_MINUTES
