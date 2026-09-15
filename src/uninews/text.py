"""Small text helpers shared by sources and the database."""

import unicodedata


def clean_text(text: str | None) -> str:
    """Collapse all whitespace to single spaces."""
    return " ".join((text or "").split())


def fold(text: str | None) -> str:
    """Lowercase and remove accents, so "Υποτροφία" and "υποτροφια" match."""
    decomposed = unicodedata.normalize("NFD", text or "")
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return stripped.casefold()
