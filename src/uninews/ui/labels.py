"""Turning long publisher and source names into short display labels."""


def initialism(name: str) -> str:
    """"University of Western Macedonia" -> "UoWM" (as the sources name themselves)."""
    return "".join(
        word[0].upper() if word[0].isupper() else word[0] for word in name.split()
    )


def initials(name: str) -> str:
    """Letters for the card's image box: "University of Macedonia" -> "UM"."""
    words = [word for word in name.split() if word[:1].isupper()] or name.split()

    if not words:
        return "UN"

    if len(words) == 1:
        return words[0][:3].upper()

    return "".join(word[0] for word in words[:3]).upper()


def shorten_source(source: str, publisher: str) -> str:
    """Drop the publisher's own prefix from a source name.

    Next to "University of Western Macedonia", "UoWM Midwifery" reads as
    "Midwifery": the publisher is already shown.
    """
    prefix = initialism(publisher)

    if prefix and source.startswith(f"{prefix} "):
        return source[len(prefix) + 1:]

    return source
