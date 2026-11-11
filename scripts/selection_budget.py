#!/usr/bin/env python3
"""Derive a dynamic daily selection budget from past high-importance papers.

The budget is guidance, not a hard quota:
- history gives a median total / must-read count;
- the current candidate pool gives a relevance signal;
- the ratio of candidates overlapping past important-paper topics adjusts the
  target up or down.

Writes data/<date>/selection_budget.json.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = ROOT / "config" / "scope.json"
TERMS = (
    "quantum error correction", "fault-tolerant", "surface code", "qldpc",
    "logical qubit", "magic state", "lattice surgery", "decoder", "decoding",
    "threshold", "transpilation", "compilation", "rydberg", "transmon",
    "fluxonium", "circuit quantization", "pauli propagation", "pauli frame",
    "pauli truncation", "stabilizer", "circuit-level", "detector error",
    "large-scale", "crosstalk", "leakage", "master equation", "lindblad",
    "input-output", "measurement backaction", "tensor network", "dmrg",
)


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def text(article: dict) -> str:
    return " ".join(str(article.get(k, "")) for k in ("title", "abstract", "summary", "problem", "method", "result", "contribution")).lower()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    target = args.date
    run = DATA / target
    candidates_path = run / "candidates.json"
    if not candidates_path.exists():
        raise SystemExit(f"missing {candidates_path}")
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))

    history = []
    important_topics: dict[str, int] = {}
    for path in sorted(DATA.glob("*/report.json")):
        if path.parent.name == target:
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        articles = report.get("articles", [])
        if not articles:
            continue
        totals = len(articles)
        must = sum(1 for a in articles if a.get("importance") == 5)
        history.append((path.parent.name, totals, must))
        for a in articles:
            if a.get("importance") != 5:
                continue
            for topic in a.get("topics", []):
                important_topics[topic] = important_topics.get(topic, 0) + 1
            for term in TERMS:
                if term in text(a):
                    important_topics[term] = important_topics.get(term, 0) + 1

    hist_totals = [h[1] for h in history]
    hist_must = [h[2] for h in history]
    median_total = int(statistics.median(hist_totals)) if hist_totals else 10
    median_must = int(statistics.median(hist_must)) if hist_must else 4

    signal = []
    topic_hits = 0
    for r in candidates:
        body = text(r)
        if not any(term in body for term in TERMS):
            continue
        signal.append(r)
        if any(term in body for term in important_topics):
            topic_hits += 1

    quality = (topic_hits + 1) / (len(signal) + 2)
    target_articles = clamp(round(median_total * (0.75 + 0.5 * quality)), 6, 18)
    target_must = clamp(round(median_must * (0.70 + 0.60 * quality)), 2, 8)
    target_articles = min(target_articles, max(6, len(signal)))

    payload = {
        "date": target,
        "history": [{"date": d, "articles": t, "must_read": m} for d, t, m in history],
        "history_median_articles": median_total,
        "history_median_must_read": median_must,
        "candidate_count": len(candidates),
        "signal_pool": len(signal),
        "important_topic_overlap": topic_hits,
        "quality_ratio": round(quality, 4),
        "target_articles": target_articles,
        "target_must_read": target_must,
        "note": "Guidance, not a quota. Adjust after reading if the pool is unusually strong or weak.",
    }
    (run / "selection_budget.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Budget: {target_articles} articles, {target_must} must-read (quality={quality:.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
