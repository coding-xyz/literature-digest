#!/usr/bin/env python3
"""Attach full-text AI reviews to the curated article list.

Reviews live in data/<date>/reviews/. A review file can use any stable filename;
the article is matched by, in order:
  - review.article_id, if present;
  - review.id (article id or legacy arXiv id), if present;
  - the filename stem, if it matches the article id or its sanitized form.
No source filename/ID prefix is required, so arXiv, PRX, Nature, Quantum,
Science Advances, ePrint, etc. are treated the same way.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REQUIRED = ("verdict", "confidence", "correctness", "weaknesses", "overclaim", "citations", "questions", "basis")
VERDICTS = {"拒稿", "弱拒", "大修", "小修", "接受"}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-")
    return value or "article"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    run_dir = DATA_DIR / args.date
    report_path = run_dir / "report.json"
    reviews_dir = run_dir / "reviews"
    if not report_path.exists():
        fail(f"report not found: {report_path}")
    if not reviews_dir.exists():
        fail(f"reviews directory not found: {reviews_dir}")

    data = json.loads(report_path.read_text(encoding="utf-8"))
    reviews = {}
    for path in sorted(reviews_dir.glob("*.json")):
        review = json.loads(path.read_text(encoding="utf-8"))
        keys = [path.stem]
        if review.get("article_id"):
            keys.append(str(review["article_id"]))
        if review.get("id"):
            keys.append(str(review["id"]))
        for key in keys:
            reviews[key] = (path, review)

    missing = []
    for article in data["articles"]:
        article_id = str(article["id"])
        candidates = [
            article.get("review_file", ""),
            article_id,
            article_id.removeprefix("arxiv-"),
            slug(article_id),
            Path(article_id).name,
        ]
        found = None
        for key in candidates:
            if key and key in reviews:
                found = reviews[key]
                break
        if not found:
            # last resort: match the review's id/article_id after slug normalization
            for key, value in reviews.items():
                if slug(key) in {slug(c) for c in candidates if c}:
                    found = value
                    break
        if not found:
            missing.append(article_id)
            continue
        path, review = found
        for field in REQUIRED:
            if not review.get(field):
                fail(f"{path.name} missing review field {field!r}")
        if review["verdict"] not in VERDICTS:
            fail(f"{path.name} has invalid verdict {review['verdict']!r}")
        article["review"] = {field: review[field] for field in REQUIRED}

    if missing:
        fail(f"missing reviews for: {', '.join(missing)}")

    report_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Attached {len(data['articles'])} reviews to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
