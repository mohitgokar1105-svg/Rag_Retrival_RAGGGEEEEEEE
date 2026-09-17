"""
Download the evaluation corpus.

Pulls 25 pages of FastAPI documentation into corpus/. The docs are MIT licensed
(https://github.com/fastapi/fastapi) and are fetched rather than committed, so
this repo carries no third-party content.

    python fetch_corpus.py

Roughly 35,000 words across 25 documents. Swap PAGES for any other source, or
just drop your own .txt / .md files into corpus/ and skip this entirely.
"""

import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs"

PAGES = [
    "async",
    "deployment/concepts", "deployment/docker", "deployment/https",
    "tutorial/background-tasks", "tutorial/bigger-applications",
    "tutorial/body", "tutorial/body-nested-models", "tutorial/cookie-params",
    "tutorial/cors", "tutorial/debugging", "tutorial/dependencies/index",
    "tutorial/handling-errors", "tutorial/header-params", "tutorial/metadata",
    "tutorial/middleware", "tutorial/path-operation-configuration",
    "tutorial/path-params", "tutorial/query-params", "tutorial/request-files",
    "tutorial/response-model", "tutorial/security/first-steps",
    "tutorial/sql-databases", "tutorial/static-files", "tutorial/testing",
]


def main():
    out = Path("corpus")
    out.mkdir(exist_ok=True)

    ok = failed = 0
    for page in PAGES:
        name = page.replace("/", "_") + ".md"
        try:
            with urllib.request.urlopen(f"{BASE}/{page}.md", timeout=20) as r:
                (out / name).write_bytes(r.read())
            ok += 1
        except Exception as exc:
            print(f"  failed {page}: {type(exc).__name__}")
            failed += 1

    words = sum(len(p.read_text(encoding="utf-8", errors="ignore").split())
                for p in out.glob("*.md"))
    print(f"\n{ok} documents in corpus/ ({failed} failed), {words:,} words")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
