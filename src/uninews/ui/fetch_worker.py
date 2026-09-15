"""Fetching, off the UI thread.

The worker only does network work and returns Articles. It never touches the
database, because a SQLite connection belongs to the thread that opened it.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from urllib.parse import urlsplit

from PyQt6.QtCore import QThread, pyqtSignal

from uninews.fetchers.base import Fetcher
from uninews.article import Article

MAX_PARALLEL_SITES = 6


@dataclass(frozen=True)
class FetchResult:
    fetcher: Fetcher
    articles: list[Article]
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error


class FetchWorker(QThread):
    """Fetches every fetcher, then emits finished_fetching(results).

    Different sites are fetched in parallel, but one site is never asked for
    two pages at once, so we stay polite to servers like uom.gr.
    """

    progress = pyqtSignal(int, int, str)          # done, total, label
    finished_fetching = pyqtSignal(list)          # list[FetchResult]

    def __init__(self, fetchers: list[Fetcher], parent=None):
        super().__init__(parent)

        self.fetchers = fetchers
        self.results: list[FetchResult] = []
        self._stop = False

    def stop(self) -> None:
        """Ask the worker to finish early; checked between fetchers."""
        self._stop = True

    def run(self) -> None:
        groups = group_by_site(self.fetchers)
        done = 0

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_SITES) as pool:
            for group_results in pool.map(self.fetch_group, groups):
                for result in group_results:
                    done += 1
                    self.results.append(result)
                    self.progress.emit(done, len(self.fetchers), result.fetcher.label)

        self.finished_fetching.emit(self.results)

    def fetch_group(self, fetchers: list[Fetcher]) -> list[FetchResult]:
        """One site's fetchers, one after another."""
        results = []

        for fetcher in fetchers:
            if self._stop:
                break

            results.append(self.fetch_one(fetcher))

        return results

    def fetch_one(self, fetcher: Fetcher) -> FetchResult:
        try:
            return FetchResult(fetcher, fetcher.fetch())
        except Exception as error:
            return FetchResult(fetcher, [], describe_error(error))


def group_by_site(fetchers: list[Fetcher]) -> list[list[Fetcher]]:
    groups: dict[str, list[Fetcher]] = {}

    for fetcher in fetchers:
        groups.setdefault(urlsplit(fetcher.url).netloc, []).append(fetcher)

    return list(groups.values())


def describe_error(error: Exception) -> str:
    import requests

    if isinstance(error, requests.Timeout):
        return "the site did not respond in time"

    if isinstance(error, requests.ConnectionError):
        return "could not connect (site down, or no internet)"

    if isinstance(error, requests.HTTPError) and error.response is not None:
        return f"the site returned HTTP {error.response.status_code}"

    return str(error) or type(error).__name__
