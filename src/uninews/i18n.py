"""Interface text in English and Greek.

Every string the user sees goes through tr(key). No Qt here, so it can be
tested on its own, and no build step: adding a language means adding one
dict to CATALOGS and one entry to LANGUAGES.

Publisher, source and article text come from the sites and are never translated.
"""

import os

ENGLISH = "en"
GREEK = "el"
SYSTEM = ""                         # settings value: follow the desktop's language

# Native names: a user who can't read the current language can still find theirs.
LANGUAGES = {ENGLISH: "English", GREEK: "Ελληνικά"}

# A value is a string, or a (one, other) pair for text with a {count}.
EN = {
    "app.subtitle": "University news in one clean place",
    "header.sources": "Sources",
    "header.settings": "Settings",
    "header.refresh": "Refresh news",
    "header.refreshing": "Refreshing...",

    "list.empty_first_run": "No articles yet.\nPress “Refresh news” to fetch them.",
    "list.empty": "No articles found.\nTry refreshing or changing the filter.",

    "card.untitled": "Untitled",
    "card.open": "Open article →",

    "sidebar.title": "Sources",
    "sidebar.search": "Search articles...",
    "sidebar.all": "All sources",

    "pagination.previous": "‹ Previous",
    "pagination.next": "Next ›",
    "pagination.summary": "Showing {first}-{last} of {total}",
    "pagination.per_page": "{size} / page",

    "fetch.load_error": "Could not load sources",
    "fetch.progress": "Fetching {done}/{total}: {label}",
    "fetch.new": ("{count} new article", "{count} new articles"),
    "fetch.removed": ("{count} old removed", "{count} old removed"),
    "fetch.failed": ("{count} source failed", "{count} sources failed"),

    "status.title": "Sources",
    "status.no_refresh": "No refresh yet in this session.",
    "status.worked": "{working} of {total} sources worked.",
    "status.failed": "Failed:",

    "error.timeout": "the site did not respond in time",
    "error.connection": "could not connect (site down, or no internet)",
    "error.http": "the site returned HTTP {status}",

    "settings.title": "Settings",
    "settings.saved": "Settings saved.",
    "settings.save": "Save",
    "settings.cancel": "Cancel",
    "settings.language": "Language",
    "settings.language_system": "Same as system",
    "settings.theme": "Theme",
    "settings.theme_light": "Light",
    "settings.theme_dark": "Dark",
    "settings.open_with": "Open with",
    "settings.open_with_profile": "From UniOS profile",
    "settings.per_page": "Articles per page",
    "settings.refresh_on_startup": "Refresh when the app opens",
    "settings.interval": "Auto-refresh every",
    "settings.interval_off": "Off",
    "settings.minutes_suffix": " min",
    "settings.keep_at_most": "Keep at most",
    "settings.note": (
        "Auto-refresh runs at most every {minutes} minutes, "
        "to avoid overloading university servers."
    ),
}

EL = {
    "app.subtitle": "Τα νέα των πανεπιστημίων σε ένα σημείο",
    "header.sources": "Πηγές",
    "header.settings": "Ρυθμίσεις",
    "header.refresh": "Ανανέωση",
    "header.refreshing": "Ανανέωση...",

    "list.empty_first_run": "Δεν υπάρχουν άρθρα ακόμα.\nΠατήστε «Ανανέωση» για να τα φέρετε.",
    "list.empty": "Δεν βρέθηκαν άρθρα.\nΔοκιμάστε ανανέωση ή άλλο φίλτρο.",

    "card.untitled": "Χωρίς τίτλο",
    "card.open": "Άνοιγμα άρθρου →",

    "sidebar.title": "Πηγές",
    "sidebar.search": "Αναζήτηση άρθρων...",
    "sidebar.all": "Όλες οι πηγές",

    "pagination.previous": "‹ Προηγούμενη",
    "pagination.next": "Επόμενη ›",
    "pagination.summary": "{first}-{last} από {total}",
    "pagination.per_page": "{size} / σελίδα",

    "fetch.load_error": "Δεν ήταν δυνατή η φόρτωση των πηγών",
    "fetch.progress": "Λήψη {done}/{total}: {label}",
    "fetch.new": ("{count} νέο άρθρο", "{count} νέα άρθρα"),
    "fetch.removed": ("{count} παλιό αφαιρέθηκε", "{count} παλιά αφαιρέθηκαν"),
    "fetch.failed": ("απέτυχε {count} πηγή", "απέτυχαν {count} πηγές"),

    "status.title": "Πηγές",
    "status.no_refresh": "Δεν έχει γίνει ανανέωση σε αυτή τη συνεδρία.",
    "status.worked": "Λειτούργησαν {working} από {total} πηγές.",
    "status.failed": "Απέτυχαν:",

    "error.timeout": "ο ιστότοπος δεν απάντησε εγκαίρως",
    "error.connection": "αδυναμία σύνδεσης (ο ιστότοπος είναι εκτός ή δεν υπάρχει internet)",
    "error.http": "ο ιστότοπος επέστρεψε HTTP {status}",

    "settings.title": "Ρυθμίσεις",
    "settings.saved": "Οι ρυθμίσεις αποθηκεύτηκαν.",
    "settings.save": "Αποθήκευση",
    "settings.cancel": "Ακύρωση",
    "settings.language": "Γλώσσα",
    "settings.language_system": "Όπως το σύστημα",
    "settings.theme": "Θέμα",
    "settings.theme_light": "Φωτεινό",
    "settings.theme_dark": "Σκούρο",
    "settings.open_with": "Άνοιγμα με",
    "settings.open_with_profile": "Από το προφίλ UniOS",
    "settings.per_page": "Άρθρα ανά σελίδα",
    "settings.refresh_on_startup": "Ανανέωση με το άνοιγμα της εφαρμογής",
    "settings.interval": "Αυτόματη ανανέωση κάθε",
    "settings.interval_off": "Ανενεργή",
    "settings.minutes_suffix": " λεπτά",
    "settings.keep_at_most": "Διατήρηση έως",
    "settings.note": (
        "Η αυτόματη ανανέωση γίνεται το πολύ κάθε {minutes} λεπτά, "
        "για να μην επιβαρύνονται οι διακομιστές των πανεπιστημίων."
    ),
}

CATALOGS = {ENGLISH: EN, GREEK: EL}

_current = ENGLISH


def system_language() -> str:
    """The desktop's language if we have it, else English. Reads the POSIX locale variables."""
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable, "")

        if not value:
            continue

        # LANGUAGE can be a list ("el:en"); LANG looks like "el_GR.UTF-8".
        for entry in value.split(":"):
            code = entry.split("_")[0].split(".")[0].lower()

            if code in CATALOGS:
                return code

        return ENGLISH          # the first variable that is set decides, like gettext

    return ENGLISH


def resolve(choice: str | None) -> str:
    """Settings value ("", "en", "el", or something unknown) -> a supported language."""
    choice = (choice or "").strip().lower()
    return choice if choice in CATALOGS else system_language()


def set_language(choice: str | None) -> str:
    """Switch the interface language; returns the one now in use."""
    global _current  # pylint: disable=global-statement
    _current = resolve(choice)
    return _current


def current_language() -> str:
    return _current


def tr(key: str, count: int | None = None, **values) -> str:
    """Text for key in the current language, falling back to English, then to the key.

    tr("fetch.new", count=3) picks the plural form and fills {count}.
    """
    text = CATALOGS[_current].get(key, EN.get(key, key))

    if isinstance(text, tuple):
        text = text[0] if count == 1 else text[1]

    if count is not None:
        values["count"] = count

    return text.format(**values) if values else text
