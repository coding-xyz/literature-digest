#!/usr/bin/env python3
"""Validate a curated FTQC / superconducting-simulation digest and inject it
into the self-contained HTML template.

The template owns presentation and the local reading workflow; this script only
checks the curated JSON and replaces the <script id="report-data"> block.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "report-template.html"
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"

REQUIRED_ARTICLE_FIELDS = [
    "id", "no", "topics", "source", "venue", "published", "title", "title_zh",
    "authors", "abstract", "importance", "importance_reason", "summary",
    "problem", "method", "result", "contribution", "limitation", "key_numbers",
    "url",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def has_math(article: dict) -> bool:
    text = "".join(str(article.get(field, "")) for field in ("summary", "problem", "method", "result", "contribution"))
    return "\\(" in text or "$$" in text


SCREEN_TERMS = [
    "quantum error correction", "fault-tolerant", "fault tolerant", "surface code",
    "qldpc", "quantum ldpc", "logical qubit", "magic state", "lattice surgery",
    "transpilation", "compilation", "decoder", "decoding", "syndrome",
    "crosstalk", "leakage", "tomography", "superconducting", "transmon",
    "fluxonium", "tunable coupler", "circuit quantization", "circuit qed",
    "normal mode", "capacitance matrix", "master equation", "lindblad",
    "magnus", "1/f noise", "control pulse", "pauli propagation", "pauli frame",
    "pauli truncation", "stabilizer simulation", "circuit-level",
    "detector error", "large-scale simulation", "erasure", "surface-code",
    "quantum expander", "belief propagation",
]


def keyword_hit(record: dict) -> bool:
    text = (record.get("title", "") + " " + record.get("abstract", "")).lower()
    return any(term in text for term in SCREEN_TERMS)


def _included_for(article: dict, source_key: str, journal: str | None = None) -> bool:
    source = article.get("source", "")
    if source_key == "arxiv":
        return source == "arXiv"
    if source_key == "eprint":
        return source == "Cryptology ePrint Archive"
    if source_key == "pr":
        aliases = {
            "Physical Review Letters": "PRL",
            "Physical Review A": "PRA",
            "Physical Review Applied": "PRApplied",
            "Physical Review X": "PRX",
            "PRX Quantum": "PRX Quantum",
            "Physical Review Research": "PRResearch",
            "Reviews of Modern Physics": "RMP",
        }
        key = aliases.get(journal or "", "")
        return source == key or (source == "PR 系列" and article.get("venue") == journal)
    if source_key == "nature":
        return source == "Nature 系列" and article.get("venue") == journal
    if source_key == "quantum":
        return source == "Quantum"
    return source == source_key or source == journal


def compute_coverage(config: dict, candidates: list[dict], articles: list[dict], manifest: dict) -> tuple[list[dict], dict]:
    sources = config["sources"]
    rows: list[dict] = []
    statuses = {s.get("key"): s.get("status", "ok") for s in manifest.get("sources", [])}

    def add(group: str, label: str, kind: str, source_key: str, journal: str | None = None):
        subset = [r for r in candidates if r.get("source") == source_key and (journal is None or r.get("venue") == journal)]
        inc = sum(1 for a in articles if _included_for(a, source_key, journal))
        rows.append({
            "group": group, "label": label, "kind": kind,
            "raw": len(subset), "screened": sum(1 for r in subset if keyword_hit(r)),
            "included": inc,
            "status": statuses.get(source_key, "ok"),
        })

    pre_rows_start = len(rows)
    pre_status = "ok"
    if any(statuses.get(k) == "error" for k in ("arxiv", "eprint")):
        pre_status = "partial"
    rows.append({"group": "预印本", "label": "预印本", "kind": "group", "raw": 0, "screened": 0, "included": 0, "status": pre_status})
    add("预印本", "arXiv", "journal", "arxiv")
    add("预印本", "Cryptology ePrint Archive", "journal", "eprint")
    pre_group = rows[pre_rows_start]
    pre_group["raw"] = sum(r["raw"] for r in rows[pre_rows_start + 1:])
    pre_group["screened"] = sum(r["screened"] for r in rows[pre_rows_start + 1:])
    pre_group["included"] = sum(r["included"] for r in rows[pre_rows_start + 1:])

    pr_cfg = sources["pr"]
    pr_rows_start = len(rows)
    rows.append({"group": "PR 系列", "label": "PR 系列", "kind": "group", "raw": 0, "screened": 0, "included": 0, "status": statuses.get("pr", "ok")})
    for journal in pr_cfg["journals"]:
        add("PR 系列", journal, "journal", "pr", journal)
    pr_group = rows[pr_rows_start]
    pr_group["raw"] = sum(r["raw"] for r in rows[pr_rows_start + 1:])
    pr_group["screened"] = sum(r["screened"] for r in rows[pr_rows_start + 1:])
    pr_group["included"] = sum(r["included"] for r in rows[pr_rows_start + 1:])

    nature_cfg = sources["nature"]
    nat_rows_start = len(rows)
    rows.append({"group": "Nature 系列", "label": "Nature 系列", "kind": "group", "raw": 0, "screened": 0, "included": 0, "status": statuses.get("nature", "ok")})
    for journal in nature_cfg["feeds"]:
        add("Nature 系列", journal, "journal", "nature", journal)
    nat_group = rows[nat_rows_start]
    nat_group["raw"] = sum(r["raw"] for r in rows[nat_rows_start + 1:])
    nat_group["screened"] = sum(r["screened"] for r in rows[nat_rows_start + 1:])
    nat_group["included"] = sum(r["included"] for r in rows[nat_rows_start + 1:])

    add("Quantum", "Quantum", "single", "quantum")
    for key, cfg in sources.get("extra_journals", {}).items():
        add(cfg["label"], cfg["label"], "single", key, cfg["label"])

    included = sum(1 for a in articles)
    raw = sum(int(row.get("fetched", 0)) for row in manifest.get("sources", []))
    totals = {
        "raw": raw,
        "deduped": len(candidates),
        "screened": sum(r["screened"] for r in rows if r["kind"] != "group"),
        "included": included,
        "errors": [s.get("key") for s in manifest.get("sources", []) if s.get("status") == "error"],
    }
    if sum(r["included"] for r in rows if r["kind"] != "group") != included:
        fail("coverage included counts do not match article count")
    return rows, totals


def validate(data: dict, issue_date: str) -> None:
    meta = data.get("meta")
    if not isinstance(meta, dict):
        fail("meta is missing")
    if meta.get("issue_date") != issue_date:
        fail(f"meta.issue_date={meta.get('issue_date')!r} does not match --date {issue_date!r}")
    for key in ("title", "subtitle", "as_of", "window", "generated_at", "scope_href"):
        if not meta.get(key):
            fail(f"meta.{key} is empty")
    if meta.get("is_template") is True:
        fail("refusing to build a report from template demo data (meta.is_template=true)")
    articles = data.get("articles")
    if not isinstance(articles, list) or not articles:
        fail("articles must be a non-empty list")

    ids: set[str] = set()
    numbers: set[int] = set()
    for index, article in enumerate(articles, start=1):
        for field in REQUIRED_ARTICLE_FIELDS:
            if field not in article or article[field] in ("", None, []):
                fail(f"articles[{index}] missing required field {field!r}")
        if article["id"] in ids:
            fail(f"duplicate article id: {article['id']}")
        ids.add(article["id"])
        if not isinstance(article["no"], int) or article["no"] in numbers:
            fail(f"duplicate or non-integer no at {article['id']}")
        numbers.add(article["no"])
        if not isinstance(article["importance"], int) or not 1 <= article["importance"] <= 5:
            fail(f"importance must be an integer 1..5 at {article['id']}")
        if not isinstance(article["topics"], list) or not article["topics"]:
            fail(f"topics must be a non-empty list at {article['id']}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(article["published"])):
            fail(f"invalid published date at {article['id']}")
        if str(article["published"]) > issue_date:
            fail(f"published date is after issue date at {article['id']}")
        parsed = urlparse(article["url"])
        if parsed.scheme != "https" or not parsed.netloc:
            fail(f"article URL must be https at {article['id']}: {article['url']}")
        if not isinstance(article["authors"], list) or not article["authors"]:
            fail(f"authors must be non-empty at {article['id']}")
        if not isinstance(article["key_numbers"], list) or not article["key_numbers"]:
            fail(f"key_numbers must be non-empty at {article['id']}")
        review = article.get("review")
        if not isinstance(review, dict):
            fail(f"review is missing at {article['id']}")
        for field in ("verdict", "confidence", "correctness", "weaknesses", "overclaim", "citations", "questions", "basis"):
            if not review.get(field):
                fail(f"review.{field} is missing at {article['id']}")
        if len(article["summary"]) > 280:
            fail(f"summary is too long at {article['id']} ({len(article['summary'])} chars)")
        for field in ("abstract", "problem", "method", "result", "contribution", "limitation"):
            if len(article[field]) < 10:
                fail(f"{field} is too short at {article['id']}")

    expected_numbers = set(range(1, len(articles) + 1))
    if numbers != expected_numbers:
        fail(f"article numbers must be 1..{len(articles)}, got {sorted(numbers)}")
    if not any(has_math(a) for a in articles):
        fail("at least one article should contain inline/display LaTeX")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=date.today().isoformat(), help="issue date (YYYY-MM-DD)")
    parser.add_argument("--data", help="path to curated report.json")
    parser.add_argument("--out", help="output HTML path")
    args = parser.parse_args()

    issue_date = args.date
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", issue_date):
        fail("--date must be YYYY-MM-DD")
    data_path = Path(args.data) if args.data else DATA_DIR / issue_date / "report.json"
    if not data_path.exists():
        fail(f"curated report not found: {data_path}")
    if not TEMPLATE.exists():
        fail(f"template not found: {TEMPLATE}")

    data = json.loads(data_path.read_text(encoding="utf-8"))
    validate(data, issue_date)

    run_dir = data_path.parent
    candidates_path = run_dir / "candidates.json"
    manifest_path = run_dir / "manifest.json"
    if not candidates_path.exists() or not manifest_path.exists():
        fail(f"candidates.json / manifest.json not found next to {data_path}")
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = json.loads((ROOT / "config" / "scope.json").read_text(encoding="utf-8"))
    journals, totals = compute_coverage(config, candidates, data["articles"], manifest)
    data["meta"]["journals"] = journals
    data["meta"]["coverage_totals"] = totals
    (run_dir / "coverage.json").write_text(json.dumps({"journals": journals, "totals": totals}, ensure_ascii=False, indent=2), encoding="utf-8")

    template = TEMPLATE.read_text(encoding="utf-8").replace("__REPORT_DATE__", issue_date)
    pattern = re.compile(
        r'(<script id="report-data" type="application/json">)(.*?)(</script>)',
        re.S,
    )
    if len(pattern.findall(template)) != 1:
        fail("template must contain exactly one report-data script block")

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = pattern.sub(lambda match: match.group(1) + payload + match.group(3), template, count=1)

    out_path = Path(args.out) if args.out else REPORT_DIR / f"{issue_date}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    topic_counts: dict[str, int] = {}
    for article in data["articles"]:
        for topic in article["topics"]:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    must_read = sum(1 for a in data["articles"] if a["importance"] >= 5)
    print(f"Built {out_path}")
    print(f"  issue:     {issue_date}")
    print(f"  articles:  {len(data['articles'])} ({must_read} must-read)")
    print("  topics:    " + " · ".join(f"{k} {v}" for k, v in sorted(topic_counts.items(), key=lambda x: (-x[1], x[0]))))
    print(f"  math:      {sum(1 for a in data['articles'] if has_math(a))} articles with LaTeX")
    print(f"  size:      {out_path.stat().st_size / 1024:.1f} KiB")
    try:
        from build_index import build_index
        index_path = build_index(ROOT / "index.html", REPORT_DIR, DATA_DIR)
        print(f"  index:     {index_path}")
    except Exception as exc:
        fail(f"could not build index.html: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
