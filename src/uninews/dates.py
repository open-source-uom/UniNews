"""Turn the date text found on sites into one sortable format.

Output is "YYYY-MM-DD HH:MM:SS". Dates with a timezone are converted to UTC;
dates without one are kept as written.
"""

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from uninews.text import fold

SORTABLE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Start of each month name, lowercase and without accents.
# Greek prefixes match both "Σεπτέμβριος" and "Σεπτεμβρίου".
MONTH_PREFIXES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "ιαν": 1, "φεβ": 2, "μαρ": 3, "απρ": 4, "μαι": 5, "ιουν": 6,
    "ιουλ": 7, "αυγ": 8, "σεπ": 9, "οκτ": 10, "νοε": 11, "δεκ": 12,
}

NUMERIC_DATE = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b")        # 06/10/2025
DAY_MONTH_YEAR = re.compile(r"\b(\d{1,2})\s+([^\W\d_]{3,})\.?,?\s+(\d{4})\b")  # 10 Σεπτεμβρίου, 2026
MONTH_DAY_YEAR = re.compile(r"\b([^\W\d_]{3,})\.?\s+(\d{1,2}),?\s+(\d{4})\b")  # September 10, 2026
TIME = re.compile(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b")


def parse_date(text: str | None) -> str | None:
    """Return a sortable date string, or None if the text isn't recognised."""
    text = (text or "").strip()

    if not text:
        return None

    for parser in (_parse_iso, _parse_rfc822, _parse_numeric, _parse_words):
        parsed = parser(text)

        if parsed is not None:
            return to_sortable(parsed)

    return None


def now_sortable() -> str:
    return to_sortable(datetime.now(timezone.utc))


def to_sortable(value: datetime) -> str:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.strftime(SORTABLE_FORMAT)


def _parse_iso(text: str) -> datetime | None:
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_rfc822(text: str) -> datetime | None:
    try:
        return parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError):
        return None


def _parse_numeric(text: str) -> datetime | None:
    match = NUMERIC_DATE.search(text)

    if not match:
        return None

    day, month, year = (int(group) for group in match.groups())
    return _build(year, month, day, text)


def _parse_words(text: str) -> datetime | None:
    folded = fold(text)

    match = DAY_MONTH_YEAR.search(folded)
    if match:
        day, month_name, year = match.groups()
    else:
        match = MONTH_DAY_YEAR.search(folded)
        if not match:
            return None
        month_name, day, year = match.groups()

    month = _month_number(month_name)

    if month is None:
        return None

    return _build(int(year), month, int(day), text)


def _month_number(name: str) -> int | None:
    for prefix, number in MONTH_PREFIXES.items():
        if name.startswith(prefix):
            return number
    return None


def _build(year: int, month: int, day: int, text: str) -> datetime | None:
    hour = minute = second = 0
    time_match = TIME.search(text)

    if time_match:
        hour, minute = int(time_match[1]), int(time_match[2])
        second = int(time_match[3] or 0)

    try:
        return datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None
