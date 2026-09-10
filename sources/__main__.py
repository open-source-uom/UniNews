"""Check source configs without starting the app.

Usage:
    python -m sources data/sources
    python -m sources data/sources/universities/uom.json
"""

import sys
from pathlib import Path

from sources import load_sources


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    failed = 0
    links = set()

    for source in load_sources(Path(sys.argv[1])):
        try:
            articles = source.fetch()
        except Exception as error:
            failed += 1
            print(f"FAIL   {source.publisher} / {source.label}: {error}")
            continue

        status = "OK   " if articles else "EMPTY"
        print(f"{status}  {source.publisher} / {source.label}: {len(articles)} articles")

        for article in articles[:3]:
            print(f"         {article.published or '-':<22} {article.title[:60]}")

        links.update(article.link for article in articles)

    print(f"\n{len(links)} unique articles, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
