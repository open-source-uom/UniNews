"""Settings storage."""

import json

import pytest

from uninews import config


@pytest.fixture(autouse=True)
def temporary_home(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "settings.json")


def test_defaults_when_nothing_saved():
    assert config.load_settings() == config.DEFAULT_SETTINGS


def test_saved_settings_win_and_new_defaults_appear():
    config.save_settings({"theme": "dark", "page_size": 30})
    settings = config.load_settings()

    assert settings["theme"] == "dark"
    assert settings["max_cached_articles"] == 500      # default filled in


def test_greek_keywords_survive_a_round_trip():
    config.save_settings({"notification_keywords": ["υποτροφ", "εξετ"]})
    assert config.load_settings()["notification_keywords"] == ["υποτροφ", "εξετ"]


def test_broken_file_is_kept_not_wiped():
    config.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.SETTINGS_FILE.write_text("{not json", encoding="utf-8")

    assert config.load_settings() == config.DEFAULT_SETTINGS
    assert config.SETTINGS_FILE.with_suffix(".json.broken").exists()


def test_refresh_interval_has_a_floor():
    assert config.refresh_interval_ms({"refresh_interval_minutes": 0}) == 0
    assert config.refresh_interval_ms({"refresh_interval_minutes": 60}) == 60 * 60_000
    assert config.refresh_interval_ms({"refresh_interval_minutes": 1}) == (
        config.MIN_REFRESH_INTERVAL_MINUTES * 60_000
    )
