"""Settings storage."""

import json

import pytest

from uninews import config


@pytest.fixture(autouse=True)
def temporary_home(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(config, "ACADEMIC_CONFIG_FILE", tmp_path / "academicConfig.json")


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



def write_unios_profile(university):
    config.ACADEMIC_CONFIG_FILE.write_text(
        json.dumps({"universityName": university, "departmentName": "Informatics"}),
        encoding="utf-8",
    )


def test_unios_university_from_unidesk():
    write_unios_profile("University of Macedonia")
    assert config.load_unios_university() == "University of Macedonia"


@pytest.mark.parametrize("content", [None, "{not json", "[]", '{"universityName": ""}'])
def test_unios_university_empty_when_unset_or_broken(content):
    if content is not None:
        config.ACADEMIC_CONFIG_FILE.write_text(content, encoding="utf-8")
    assert config.load_unios_university() == ""


def test_home_university_defaults_to_all_sources():
    assert config.home_university(config.DEFAULT_SETTINGS) == ""


def test_home_university_follows_unios_profile():
    write_unios_profile("University of Macedonia")
    assert config.home_university(config.DEFAULT_SETTINGS) == "University of Macedonia"


@pytest.mark.parametrize(
    ("setting", "expected"),
    [("University of Western Macedonia", "University of Western Macedonia"), ("all", "")],
)
def test_uninews_setting_wins_over_unios_profile(setting, expected):
    write_unios_profile("University of Macedonia")
    assert config.home_university({"home_university": setting}) == expected
