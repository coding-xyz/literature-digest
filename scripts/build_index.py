#!/usr/bin/env python3
"""Build the reports index page by scanning reports/*.html.

The index embeds a small JSON manifest and displays each daily report in an
iframe, so the daily report is shown exactly as generated. No network and no
directory listing at runtime.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"
TEMPLATE = ROOT / "templates" / "index-template.html"
OUT = ROOT / "index.html"
DATE_META = re.compile(r'<meta\s+name=["\']report-date["\']\s+content=["\'](\d{4}-\d{2}-\d{2})["\']', re.I)


def iso_week(d: dt.date) -> tuple[int, int]:
    cal = d.isocalendar()
    return cal.year, cal.week


def scan_reports(reports_dir: Path, data_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in reports_dir.glob("*.html"):
        if path.name == "index.html":
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")[:20000]
        except OSError:
            continue
        match = DATE_META.search(raw)
        date = match.group(1) if match else ""
        if not date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.stem):
            date = path.stem
        if not date:
            continue
        try:
            d = dt.date.fromisoformat(date)
        except ValueError:
            continue
        title = "文献速递"
        count = None
        must_read = None
        data_path = data_dir / date / "report.json"
        if data_path.exists():
            try:
                payload = json.loads(data_path.read_text(encoding="utf-8"))
                meta = payload.get("meta", {})
                title = meta.get("subtitle") or meta.get("title") or title
                articles = payload.get("articles", [])
                count = len(articles)
                must_read = sum(1 for a in articles if a.get("importance") == 5)
            except (json.JSONDecodeError, OSError):
                pass
        y, w = iso_week(d)
        rows.append({
            "date": date,
            "file": f"reports/{path.name}",
            "title": title,
            "count": count,
            "mustRead": must_read,
            "week": f"{y}-W{w:02d}",
            "weekStart": (d - dt.timedelta(days=d.isoweekday() - 1)).isoformat(),
            "weekEnd": (d - dt.timedelta(days=d.isoweekday() - 1) + dt.timedelta(days=6)).isoformat(),
        })
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def build_index(out: Path = OUT, reports_dir: Path = REPORTS_DIR, data_dir: Path = DATA_DIR) -> Path:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"index template not found: {TEMPLATE}")
    reports = scan_reports(reports_dir, data_dir)
    payload = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "reports": reports,
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(<script id="reports-data" type="application/json">)(.*?)(</script>)',
        re.S,
    )
    if len(pattern.findall(template)) != 1:
        raise ValueError("index template must contain exactly one reports-data block")
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = pattern.sub(lambda m: m.group(1) + blob + m.group(3), template, count=1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--reports", type=Path, default=REPORTS_DIR)
    ap.add_argument("--data", type=Path, default=DATA_DIR)
    args = ap.parse_args()
    path = build_index(args.out, args.reports, args.data)
    print(f"Built {path}")
    print(f"  reports: {len(scan_reports(args.reports, args.data))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
