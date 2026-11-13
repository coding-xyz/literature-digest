#!/usr/bin/env python3
"""Assemble data/<date>/report.json from small per-article JSON files.

This avoids asking a model to write one very long JSON document in a single
tool call. Expected layout:

  data/<date>/meta.json          # the report "meta" object
  data/<date>/articles/01.json   # one article object per file
  data/<date>/articles/02.json
  ...

Each article file must contain "no" so the final order is deterministic.
If articles/ is absent, the existing report.json is left untouched.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from atomic_io import atomic_write_json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    run = DATA / args.date
    articles_dir = run / "articles"
    if not articles_dir.exists():
        print(f"No articles/ directory for {args.date}; leaving report.json untouched.")
        return 0

    meta_path = run / "meta.json"
    if not meta_path.exists():
        meta_path = run / "report.meta.json"
    if not meta_path.exists():
        fail(f"missing {run / 'meta.json'} (or report.meta.json)")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        fail("meta.json must contain an object")

    articles = []
    seen = set()
    for path in sorted(articles_dir.glob("*.json")):
        if path.name.startswith("_"):
            continue
        article = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(article, dict):
            fail(f"{path.name}: article must be an object")
        if "no" not in article:
            fail(f"{path.name}: missing article.no")
        no = int(article["no"])
        if no in seen:
            fail(f"duplicate article.no {no} in {path.name}")
        seen.add(no)
        articles.append(article)

    if not articles:
        fail(f"no article JSON files in {articles_dir}")

    articles.sort(key=lambda a: int(a["no"]))
    expected = list(range(1, len(articles) + 1))
    actual = [int(a["no"]) for a in articles]
    if actual != expected:
        fail(f"article.no must be contiguous 1..{len(articles)}, got {actual}")

    payload = {"meta": meta, "articles": articles}
    atomic_write_json(run / "report.json", payload)
    print(f"Assembled {len(articles)} articles into {run / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
