import re

import pytest

from uninews import i18n
from uninews.i18n import tr

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def placeholders(text) -> set[str]:
    texts = text if isinstance(text, tuple) else (text,)
    return {name for t in texts for name in PLACEHOLDER.findall(t)}


@pytest.mark.parametrize("code", sorted(i18n.CATALOGS))
def test_every_language_has_every_key(code):
    assert set(i18n.CATALOGS[code]) == set(i18n.EN)


@pytest.mark.parametrize("code", sorted(i18n.CATALOGS))
def test_translations_keep_placeholders_and_plural_shape(code):
    for key, english in i18n.EN.items():
        translated = i18n.CATALOGS[code][key]
        assert isinstance(translated, tuple) == isinstance(english, tuple), key
        assert placeholders(translated) == placeholders(english), key


def test_languages_match_catalogs():
    assert set(i18n.LANGUAGES) == set(i18n.CATALOGS)


def test_tr_switches_language():
    assert tr("header.settings") == "Settings"
    i18n.set_language("el")
    assert tr("header.settings") == "Ρυθμίσεις"


def test_tr_plural_and_values():
    assert tr("fetch.new", count=1) == "1 new article"
    assert tr("fetch.new", count=0) == "0 new articles"
    i18n.set_language("el")
    assert tr("fetch.new", count=1) == "1 νέο άρθρο"
    assert tr("fetch.new", count=5) == "5 νέα άρθρα"
    assert tr("pagination.summary", first=1, last=12, total=40) == "1-12 από 40"


def test_unknown_key_falls_back_to_key():
    assert tr("no.such.key") == "no.such.key"


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({"LANG": "el_GR.UTF-8"}, "el"),
        ({"LANG": "en_US.UTF-8"}, "en"),
        ({"LANG": "de_DE.UTF-8"}, "en"),
        ({"LANGUAGE": "el:en", "LANG": "en_US.UTF-8"}, "el"),
        ({"LC_ALL": "C"}, "en"),
        ({}, "en"),
    ],
)
def test_system_language(monkeypatch, env, expected):
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(variable, raising=False)
    for variable, value in env.items():
        monkeypatch.setenv(variable, value)

    assert i18n.system_language() == expected


def test_resolve_settings_value(monkeypatch):
    monkeypatch.setenv("LANGUAGE", "el")
    assert i18n.resolve("") == "el"            # follow the desktop
    assert i18n.resolve("en") == "en"          # explicit choice wins
    assert i18n.resolve("fr") == "el"          # unknown -> desktop
