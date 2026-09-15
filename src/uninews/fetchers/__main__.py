"""Check publisher configs without starting the app.

    python3 -m uninews.fetchers                                   # everything
    python3 -m uninews.fetchers src/uninews/resources/publishers/uom.json
"""

import sys
from pathlib import Path

from uninews.config import PUBLISHERS_DIR
from uninews.fetchers import load_fetchers


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else PUBLISHERS_DIR

    failed = 0
    links = set()

    for fetcher in load_fetchers(path):
        try:
            articles = fetcher.fetch()
        except Exception as error:
            failed += 1
            print(f"FAIL   {fetcher.publisher} / {fetcher.label}: {error}")
            continue

        status = "OK   " if articles else "EMPTY"
        print(f"{status}  {fetcher.publisher} / {fetcher.label}: {len(articles)} articles")

        for article in articles[:3]:
            print(f"         {article.published_at or '-':<22} {article.title[:60]}")

        links.update(article.link for article in articles)

    print(f"\n{len(links)} unique articles, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
