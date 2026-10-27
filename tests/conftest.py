"""Shared test setup."""

import pytest

from uninews import i18n


@pytest.fixture(autouse=True)
def english_interface():
    """Tests assert English text, whatever the developer's desktop language is."""
    i18n.set_language(i18n.ENGLISH)
    yield
    i18n.set_language(i18n.ENGLISH)
