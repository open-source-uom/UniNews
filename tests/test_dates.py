"""Every date format seen on the configured sites so far."""

import pytest

from uninews.dates import parse_date


@pytest.mark.parametrize(
    "text, expected",
    [
        ("2026-09-10 14:51:30", "2026-09-10 14:51:30"),                # UoM
        ("Wed, 09 Sep 2026 16:40:00 -0400", "2026-09-09 20:40:00"),    # MIT RSS, to UTC
        ("25 June 2026", "2026-06-25 00:00:00"),                       # UoWM English
        ("10 Σεπτεμβρίου, 2026", "2026-09-10 00:00:00"),               # Greek, comma
        ("10 Σεπτεμβρίου 2026", "2026-09-10 00:00:00"),                # Greek, no comma
        ("8 Ιουλίου, 2026", "2026-07-08 00:00:00"),
        ("12 Μαΐου 2026", "2026-05-12 00:00:00"),                      # diaeresis
        ("3 Ιουνίου 2026", "2026-06-03 00:00:00"),                     # June vs July
        ("06/10/2025", "2025-10-06 00:00:00"),                         # day first
        ("10.09.2026", "2026-09-10 00:00:00"),
        ("September 10, 2026", "2026-09-10 00:00:00"),
        ("10 Sep 2026 09:30", "2026-09-10 09:30:00"),
    ],
)
def test_known_formats(text, expected):
    assert parse_date(text) == expected


@pytest.mark.parametrize("text", [None, "", "-", "News", "31/02/2026", "Under Construction"])
def test_unrecognised_returns_none(text):
    assert parse_date(text) is None
