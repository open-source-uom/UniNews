"""Fetch worker: grouping, error messages, and one-request-at-a-time per site."""

import os
import threading

import pytest
import requests

pytest.importorskip("PyQt6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from uninews.ui.fetch_worker import (  # noqa: E402
    FetchWorker,
    describe_error,
    group_by_site,
)


class FakeSource:
    """Stands in for a Fetcher: only .url, .label and .fetch() are used."""

    def __init__(self, label, url, articles=None, error=None, tracker=None):
        self.label = label
        self.url = url
        self.publisher = "Test"
        self.articles = articles or []
        self.error = error
        self.tracker = tracker

    def fetch(self):
        if self.tracker is not None:
            self.tracker.enter(self.url)

        try:
            if self.error:
                raise self.error
            return list(self.articles)
        finally:
            if self.tracker is not None:
                self.tracker.leave(self.url)


class ConcurrencyTracker:
    """Records the most simultaneous fetches seen per site."""

    def __init__(self):
        self.lock = threading.Lock()
        self.active = {}
        self.peak = {}

    def enter(self, url):
        with self.lock:
            self.active[url] = self.active.get(url, 0) + 1
            self.peak[url] = max(self.peak.get(url, 0), self.active[url])

    def leave(self, url):
        with self.lock:
            self.active[url] -= 1


def run_worker(sources):
    worker = FetchWorker(sources)
    worker.run()          # run() directly: no Qt event loop needed
    return worker.results


def test_groups_sources_by_host():
    sources = [
        FakeSource("a", "https://uom.gr/1"),
        FakeSource("b", "https://uom.gr/2"),
        FakeSource("c", "https://mit.edu/feed"),
    ]
    groups = group_by_site(sources)

    assert sorted(len(group) for group in groups) == [1, 2]


def test_one_request_at_a_time_per_site():
    tracker = ConcurrencyTracker()
    sources = [
        FakeSource(f"uom {i}", "https://uom.gr/x", tracker=tracker) for i in range(4)
    ] + [
        FakeSource(f"mit {i}", "https://mit.edu/x", tracker=tracker) for i in range(4)
    ]

    run_worker(sources)

    assert tracker.peak == {"https://uom.gr/x": 1, "https://mit.edu/x": 1}


def test_one_failure_does_not_stop_the_others():
    results = run_worker([
        FakeSource("good", "https://a.gr", articles=["x", "y"]),
        FakeSource("bad", "https://b.gr", error=requests.Timeout()),
        FakeSource("also good", "https://c.gr", articles=["z"]),
    ])

    by_label = {result.fetcher.label: result for result in results}

    assert len(results) == 3
    assert by_label["good"].ok and len(by_label["good"].articles) == 2
    assert not by_label["bad"].ok
    assert by_label["bad"].error == "the site did not respond in time"


def test_progress_is_reported_for_every_source():
    worker = FetchWorker([FakeSource(str(i), f"https://{i}.gr") for i in range(3)])
    seen = []
    worker.progress.connect(lambda done, total, label: seen.append((done, total)))

    worker.run()

    assert seen == [(1, 3), (2, 3), (3, 3)]


def test_stop_ends_early():
    worker = FetchWorker([FakeSource(str(i), "https://same.gr") for i in range(5)])
    worker.stop()
    worker.run()

    assert worker.results == []


class FakeResponse:
    status_code = 503


def test_error_messages_are_readable():
    http_error = requests.HTTPError()
    http_error.response = FakeResponse()

    assert describe_error(requests.ConnectionError()).startswith("could not connect")
    assert describe_error(http_error) == "the site returned HTTP 503"
    assert describe_error(ValueError("bot-check page")) == "bot-check page"
