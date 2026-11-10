#!/usr/bin/env python3
"""Collect recent papers for the quantum-information / cryptology monitor.

Standard library only. The collector is deliberately conservative:
- every source keeps a raw response snapshot;
- every normalized record keeps a stable id and its source date;
- a source failure is reported as an error, never silently converted to "no update";
- the 7-day lookback absorbs weekends and Crossref lag.
"""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "scope.json"
DATA_DIR = ROOT / "data"
USER_AGENT = "QC-Literature-Radar/1.0 (+local research workflow; mailto:research@example.org)"
HTTP_TIMEOUT = 75


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact_title(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", (value or "").lower())


def doi_key(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    return value


def parse_iso_date(value: str) -> dt.date | None:
    if not value:
        return None
    raw = value.strip()
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return dt.datetime.fromisoformat(raw).date()
    except ValueError:
        return None


def parse_rfc822(value: str) -> dt.datetime | None:
    if not value:
        return None
    try:
        return email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def date_key(value: dt.datetime | dt.date | None) -> str:
    if value is None:
        return ""
    return value.date().isoformat() if isinstance(value, dt.datetime) else value.isoformat()


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def http_get(url: str, retries: int = 2) -> bytes:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/atom+xml, application/rss+xml, application/xml, application/json, text/xml, */*",
    }
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
                return response.read()
        except Exception as exc:  # network and HTTP errors are reported, not hidden
            last_error = exc
            if attempt < retries:
                time.sleep(2 + attempt * 3)
    raise RuntimeError(f"{type(last_error).__name__}: {last_error}")


def get_json(url: str) -> dict:
    return json.loads(http_get(url).decode("utf-8", "replace"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(value, fh, ensure_ascii=False, indent=2)
    tmp.replace(path)


def item_id(prefix: str, stable: str) -> str:
    digest = hashlib.sha1(stable.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"


# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------

def collect_arxiv(cfg: dict, start: dt.date, end: dt.date) -> list[dict]:
    categories = cfg["categories"]
    query = "(" + " OR ".join(f"cat:{c}" for c in categories) + ")"
    query += f" AND submittedDate:[{start:%Y%m%d}0000 TO {end:%Y%m%d}2359]"
    page_size = int(cfg.get("page_size", 200))
    max_results = int(cfg.get("max_results", 1200))
    records: list[dict] = []
    seen: set[str] = set()

    for offset in range(0, max_results, page_size):
        params = {
            "search_query": query,
            "start": offset,
            "max_results": min(page_size, max_results - offset),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
        root = ET.fromstring(http_get(url))
        ns = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}
        entries = root.findall("a:entry", ns)
        total = int(root.findtext("o:totalResults", default="0", namespaces=ns) or 0)
        if not entries:
            break

        for entry in entries:
            arxiv_url = entry.findtext("a:id", default="", namespaces=ns).strip()
            arxiv_id = re.sub(r"v\d+$", "", arxiv_url.rsplit("/", 1)[-1])
            if not arxiv_id or arxiv_id in seen:
                continue
            seen.add(arxiv_id)
            published_raw = entry.findtext("a:published", default="", namespaces=ns)
            updated_raw = entry.findtext("a:updated", default="", namespaces=ns)
            pub_date = parse_iso_date(published_raw)
            if pub_date is None or pub_date < start or pub_date > end:
                continue
            categories_found = [c.get("term", "") for c in entry.findall("a:category", ns)]
            authors = [
                clean_text(a.findtext("a:name", default="", namespaces=ns))
                for a in entry.findall("a:author", ns)
            ]
            title = " ".join(entry.findtext("a:title", default="", namespaces=ns).split())
            abstract = " ".join(entry.findtext("a:summary", default="", namespaces=ns).split())
            pdf_url = ""
            for link in entry.findall("a:link", ns):
                if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                    pdf_url = link.get("href", "")
                    break
            primary_el = entry.find("{http://arxiv.org/schemas/atom}primary_category")
            primary = primary_el.get("term", "") if primary_el is not None else ""
            records.append({
                "id": f"arxiv-{arxiv_id}",
                "source": "arxiv",
                "source_label": "arXiv",
                "venue": "arXiv",
                "primary_category": primary or (categories_found[0] if categories_found else ""),
                "title": title,
                "authors": [a for a in authors if a],
                "abstract": abstract,
                "published": pub_date.isoformat(),
                "updated": parse_iso_date(updated_raw).isoformat() if parse_iso_date(updated_raw) else pub_date.isoformat(),
                "doi": "",
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": pdf_url or f"https://arxiv.org/pdf/{arxiv_id}",
                "type": "preprint",
                "categories": categories_found,
                "source_date": pub_date.isoformat(),
            })
        if offset + len(entries) >= total:
            break
        time.sleep(3)  # arXiv API etiquette

    return records


# ---------------------------------------------------------------------------
# ePrint
# ---------------------------------------------------------------------------

def collect_eprint(cfg: dict, start: dt.date, end: dt.date) -> list[dict]:
    root = ET.fromstring(http_get(cfg["feed"]))
    records: list[dict] = []
    for item in root.iter("item"):
        fields: dict[str, list[str]] = {}
        for child in item:
            name = local_name(child.tag)
            fields.setdefault(name, []).append(child.text or "")
        title = clean_text(" ".join(fields.get("title", [])))
        link = clean_text(" ".join(fields.get("link", [])))
        if not title or not link:
            continue
        pub = parse_rfc822(" ".join(fields.get("pubDate", [])))
        if pub is None:
            continue
        pub_date = pub.astimezone(dt.timezone.utc).date()
        if pub_date < start or pub_date > end:
            continue
        paper_no = link.rstrip("/").rsplit("/", 1)[-1]
        year = link.rstrip("/").rsplit("/", 2)[-2]
        pdf_url = ""
        for enclosure in item.iter():
            if local_name(enclosure.tag) == "enclosure":
                pdf_url = enclosure.get("url", "")
                break
        records.append({
            "id": f"eprint-{year}-{paper_no}",
            "source": "eprint",
            "source_label": "Cryptology ePrint Archive",
            "venue": "Cryptology ePrint Archive",
            "title": title,
            "authors": [clean_text(x) for x in fields.get("creator", []) if clean_text(x)],
            "abstract": clean_text(" ".join(fields.get("description", []))),
            "published": pub_date.isoformat(),
            "updated": pub_date.isoformat(),
            "doi": "",
            "url": link,
            "pdf_url": pdf_url or (link + ".pdf"),
            "type": "preprint",
            "categories": [clean_text(x) for x in fields.get("category", []) if clean_text(x)],
            "source_date": pub_date.isoformat(),
        })
    return records


# ---------------------------------------------------------------------------
# Nature portfolio
# ---------------------------------------------------------------------------

def collect_nature(cfg: dict, start: dt.date, end: dt.date) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    errors: list[str] = []
    prefixes = tuple(cfg.get("research_doi_prefixes", ["10.1038/s415", "10.1038/s414", "10.1038/s419"]))

    for journal, feed in cfg["feeds"].items():
        try:
            root = ET.fromstring(http_get(feed))
        except Exception as exc:
            errors.append(f"{journal}: {exc}")
            continue
        for item in root.iter():
            if local_name(item.tag) != "item":
                continue
            fields: dict[str, list[str]] = {}
            for child in item:
                fields.setdefault(local_name(child.tag), []).append(child.text or "")
            doi = doi_key(clean_text(" ".join(fields.get("doi", []))))
            if not doi.startswith(prefixes):
                continue  # news, comment, careers, podcasts
            title_candidates = [clean_text(x) for x in fields.get("title", []) if clean_text(x)]
            title = title_candidates[0] if title_candidates else ""
            pub_raw = clean_text(" ".join(fields.get("date", [])))[:10]
            pub_date = parse_iso_date(pub_raw)
            if not title or pub_date is None or pub_date < start or pub_date > end:
                continue
            link = clean_text(" ".join(fields.get("link", []))) or f"https://doi.org/{doi}"
            abstract = clean_text(" ".join(fields.get("encoded", [])))
            abstract = re.sub(
                r"^.*?Published online:\s*\d{1,2}\s+\w+\s+\d{4};\s*(?:doi:\s*10\.\d{4,9}/[^\s]+\s*)?",
                "",
                abstract,
                flags=re.I,
            )
            abstract = re.sub(r"^doi:\s*10\.\d{4,9}/[^\s]+\s*", "", abstract, flags=re.I)
            records.append({
                "id": f"nature-{doi}",
                "source": "nature",
                "source_label": "Nature 系列",
                "venue": journal,
                "title": title,
                "authors": [clean_text(x) for x in fields.get("creator", []) if clean_text(x)],
                "abstract": abstract,
                "published": pub_date.isoformat(),
                "updated": pub_date.isoformat(),
                "doi": doi,
                "url": link,
                "pdf_url": "",
                "type": "journal-article",
                "categories": [journal],
                "source_date": pub_date.isoformat(),
            })
    return records, errors


# ---------------------------------------------------------------------------
# Physical Review via Crossref
# ---------------------------------------------------------------------------

def collect_pr(cfg: dict, start: dt.date, end: dt.date) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    errors: list[str] = []
    rows = int(cfg.get("rows_per_journal", 100))

    for journal, issn in cfg["journals"].items():
        try:
            params = {
                "filter": f"from-pub-date:{start.isoformat()},until-pub-date:{end.isoformat()}",
                "rows": rows,
                "select": "DOI,title,author,published,published-online,URL,container-title,abstract,type,volume,page,issue",
                "sort": "published",
                "order": "desc",
            }
            url = f"https://api.crossref.org/journals/{issn}/works?" + urllib.parse.urlencode(params)
            payload = get_json(url)
            items = payload.get("message", {}).get("items", [])
        except Exception as exc:
            errors.append(f"{journal}: {exc}")
            continue

        for it in items:
            doi = doi_key(it.get("DOI", ""))
            title = clean_text(" ".join(it.get("title", []) or []))
            if not doi or not title:
                continue
            pub_parts = (
                it.get("published", {}).get("date-parts")
                or it.get("published-online", {}).get("date-parts")
                or [[None]]
            )[0]
            if not pub_parts or not pub_parts[0]:
                continue
            try:
                pub_date = dt.date(int(pub_parts[0]), int(pub_parts[1]), int(pub_parts[2]))
            except (ValueError, IndexError):
                continue
            if pub_date < start or pub_date > end:
                continue
            authors = []
            for a in it.get("author", []) or []:
                name = " ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip()
                if name:
                    authors.append(name)
            venue = clean_text(" ".join(it.get("container-title", []) or [])) or journal
            abstract = clean_text(it.get("abstract", ""))
            records.append({
                "id": f"pr-{doi}",
                "source": "pr",
                "source_label": "PR 系列",
                "venue": venue,
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "published": pub_date.isoformat(),
                "updated": pub_date.isoformat(),
                "doi": doi,
                "url": f"https://doi.org/{doi}",
                "pdf_url": "",
                "type": "journal-article",
                "categories": [venue],
                "volume": it.get("volume", ""),
                "page": it.get("page", ""),
                "issue": it.get("issue", ""),
                "source_date": pub_date.isoformat(),
            })
    return records, errors


def collect_journal_crossref(
    key: str,
    label: str,
    journal: str,
    issn: str,
    start: dt.date,
    end: dt.date,
    rows: int = 100,
) -> list[dict]:
    """Collect one journal through the Crossref journal-works endpoint.

    Used for open-access / hybrid journals that do not expose a stable RSS feed:
    Science Advances, SciPost Physics, AVS Quantum Science, QST.
    """
    params = {
        "filter": f"from-pub-date:{start.isoformat()},until-pub-date:{end.isoformat()}",
        "rows": rows,
        "select": "DOI,title,author,published,published-online,URL,container-title,abstract,type,volume,page,issue",
        "sort": "published",
        "order": "desc",
    }
    url = f"https://api.crossref.org/journals/{issn}/works?" + urllib.parse.urlencode(params)
    payload = get_json(url)
    records: list[dict] = []
    for it in payload.get("message", {}).get("items", []):
        doi = doi_key(it.get("DOI", ""))
        title = clean_text(" ".join(it.get("title", []) or []))
        if not doi or not title:
            continue
        pub_parts = (
            it.get("published", {}).get("date-parts")
            or it.get("published-online", {}).get("date-parts")
            or [[None]]
        )[0]
        if not pub_parts or not pub_parts[0]:
            continue
        try:
            pub_date = dt.date(int(pub_parts[0]), int(pub_parts[1]), int(pub_parts[2]))
        except (ValueError, IndexError):
            continue
        if pub_date < start or pub_date > end:
            continue
        authors = []
        for a in it.get("author", []) or []:
            name = " ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip()
            if name:
                authors.append(name)
        venue = clean_text(" ".join(it.get("container-title", []) or [])) or journal
        records.append({
            "id": f"{key}-{doi}",
            "source": key,
            "source_label": label,
            "venue": venue,
            "title": title,
            "authors": authors,
            "abstract": clean_text(it.get("abstract", "")),
            "published": pub_date.isoformat(),
            "updated": pub_date.isoformat(),
            "doi": doi,
            "url": f"https://doi.org/{doi}",
            "pdf_url": "",
            "type": "journal-article",
            "categories": [venue],
            "volume": it.get("volume", ""),
            "page": it.get("page", ""),
            "issue": it.get("issue", ""),
            "source_date": pub_date.isoformat(),
        })
    return records


# ---------------------------------------------------------------------------
# Quantum
# ---------------------------------------------------------------------------

def collect_quantum(cfg: dict, start: dt.date, end: dt.date) -> list[dict]:
    root = ET.fromstring(http_get(cfg["feed"]))
    records: list[dict] = []
    for item in root.iter("item"):
        fields: dict[str, list[str]] = {}
        for child in item:
            fields.setdefault(local_name(child.tag), []).append(child.text or "")
        title = clean_text(" ".join(fields.get("title", [])))
        link = clean_text(" ".join(fields.get("link", [])))
        if not title or not link.startswith("http"):
            continue
        pub = parse_rfc822(" ".join(fields.get("pubDate", [])))
        if pub is None:
            continue
        pub_date = pub.astimezone(dt.timezone.utc).date()
        if pub_date < start or pub_date > end:
            continue
        doi = "10.22331/" + link.rstrip("/").rsplit("/", 1)[-1]
        abstract = clean_text(" ".join(fields.get("description", [])))
        abstract = re.sub(
            r"^Quantum\s+\d+,\s*\d+\s*\(2026\)\.\s*https?://doi\.org/\S+\s*",
            "",
            abstract,
            flags=re.I,
        )
        records.append({
            "id": f"quantum-{doi}",
            "source": "quantum",
            "source_label": "Quantum",
            "venue": "Quantum",
            "title": title,
            "authors": [clean_text(x) for x in fields.get("creator", []) if clean_text(x)],
            "abstract": abstract,
            "published": pub_date.isoformat(),
            "updated": pub_date.isoformat(),
            "doi": doi,
            "url": link,
            "pdf_url": link.rstrip("/") + "/pdf/",
            "type": "journal-article",
            "categories": ["Quantum"],
            "source_date": pub_date.isoformat(),
        })
    return records


# ---------------------------------------------------------------------------
# normalization, state, manifest
# ---------------------------------------------------------------------------

def enrich(record: dict, topic: dict) -> dict:
    text = f"{record.get('title', '')} {record.get('abstract', '')}".lower()
    record["matched_keywords"] = [k for k in topic.get("include_keywords", []) if k.lower() in text][:12]
    record["excluded"] = any(k.lower() in text for k in topic.get("exclude_keywords", []))
    return record


def dedupe(records: list[dict]) -> list[dict]:
    out: list[dict] = []
    by_doi: dict[str, dict] = {}
    by_arxiv: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    priority = {"pr": 5, "nature": 5, "quantum": 4, "eprint": 3, "arxiv": 2}

    for rec in records:
        doi = doi_key(rec.get("doi", ""))
        arxiv_id = rec["id"][len("arxiv-"):] if rec["id"].startswith("arxiv-") else ""
        tkey = compact_title(rec.get("title", ""))
        existing = by_doi.get(doi) if doi else None
        if existing is None and arxiv_id:
            existing = by_arxiv.get(arxiv_id)
        if existing is None and tkey:
            existing = by_title.get(tkey)
        if existing is None:
            out.append(rec)
            if doi:
                by_doi[doi] = rec
            if arxiv_id:
                by_arxiv[arxiv_id] = rec
            if tkey:
                by_title[tkey] = rec
            continue
        # Keep the higher-priority record, attach the other as an alternate link.
        if priority.get(rec.get("source"), 0) > priority.get(existing.get("source"), 0):
            rec.setdefault("alt_urls", [])
            if existing.get("url") and existing["url"] != rec.get("url"):
                rec["alt_urls"].append(existing["url"])
            idx = out.index(existing)
            out[idx] = rec
            existing = rec
        else:
            existing.setdefault("alt_urls", [])
            if rec.get("url") and rec["url"] != existing.get("url"):
                existing["alt_urls"].append(rec["url"])
        if rec.get("doi"):
            by_doi[doi_key(rec["doi"])] = existing
        if arxiv_id:
            by_arxiv[arxiv_id] = existing
        if tkey:
            by_title[tkey] = existing
    return out


def load_state() -> dict:
    path = DATA_DIR / "state.json"
    if not path.exists():
        return {"schema_version": 1, "sources": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema_version": 1, "sources": {}}


def update_state(state: dict, records: list[dict], now: str) -> dict:
    by_source: dict[str, set[str]] = {}
    for rec in records:
        by_source.setdefault(rec["source"], set()).add(rec["id"])
    for source, ids in by_source.items():
        entry = state.setdefault("sources", {}).setdefault(source, {"seen_ids": []})
        seen = set(entry.get("seen_ids", []))
        seen.update(ids)
        entry["seen_ids"] = sorted(seen)[-8000:]
        entry["last_run"] = now
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="issue date in Asia/Shanghai (YYYY-MM-DD); default: today")
    parser.add_argument("--days", type=int, help="lookback days; default from config")
    args = parser.parse_args()

    config = load_config()
    tz = ZoneInfo(config["time"]["timezone"])
    now = dt.datetime.now(tz)
    target = dt.date.fromisoformat(args.date) if args.date else now.date()
    days = args.days if args.days is not None else int(config["time"]["lookback_days"])
    start = target - dt.timedelta(days=max(0, days - 1))
    end = target
    run_dir = DATA_DIR / target.isoformat()
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []
    coverage: list[dict] = []
    state = load_state()
    source_cfg = config["sources"]

    def run_source(key: str, label: str, url: str, fn):
        started = dt.datetime.now(tz)
        try:
            result = fn()
            if isinstance(result, tuple):
                records, errors = result
            else:
                records, errors = result, []
            status = "ok" if not errors else "partial"
            error_text = " | ".join(errors)
        except Exception as exc:
            records, status, error_text = [], "error", f"{type(exc).__name__}: {exc}"
        records = [enrich(r, config["topic"]) for r in records]
        records = [r for r in records if not r.get("excluded", False)]
        write_json(raw_dir / f"{key}.json", records)
        all_records.extend(records)
        unique_today = {r["id"] for r in records if r.get("source_date") == target.isoformat()}
        latest = max((r.get("source_date", "") for r in records), default="")
        coverage.append({
            "key": key,
            "label": label,
            "status": status,
            "url": url,
            "fetched": len(records),
            "today": len(unique_today),
            "latest": latest,
            "error": error_text,
            "elapsed_ms": int((dt.datetime.now(tz) - started).total_seconds() * 1000),
        })
        print(f"[{key}] status={status} records={len(records)} today={len(unique_today)} latest={latest or '-'}", flush=True)
        if error_text:
            print(f"  ! {error_text}", file=sys.stderr, flush=True)

    if source_cfg["arxiv"].get("enabled", True):
        run_source("arxiv", source_cfg["arxiv"]["label"], "https://export.arxiv.org/api/query", lambda: collect_arxiv(source_cfg["arxiv"], start, end))
    if source_cfg["eprint"].get("enabled", True):
        run_source("eprint", source_cfg["eprint"]["label"], source_cfg["eprint"]["feed"], lambda: collect_eprint(source_cfg["eprint"], start, end))
    if source_cfg["nature"].get("enabled", True):
        run_source("nature", source_cfg["nature"]["label"], "https://www.nature.com/", lambda: collect_nature(source_cfg["nature"], start, end))
    if source_cfg["pr"].get("enabled", True):
        run_source("pr", source_cfg["pr"]["label"], "https://api.crossref.org/", lambda: collect_pr(source_cfg["pr"], start, end))
    for key, journal_cfg in source_cfg.get("extra_journals", {}).items():
        if journal_cfg.get("enabled", True):
            run_source(
                key,
                journal_cfg["label"],
                f"https://api.crossref.org/journals/{journal_cfg['issn']}/works",
                lambda key=key, cfg=journal_cfg: collect_journal_crossref(
                    key, cfg["label"], cfg["label"], cfg["issn"], start, end
                ),
            )
    if source_cfg["quantum"].get("enabled", True):
        run_source("quantum", source_cfg["quantum"]["label"], source_cfg["quantum"]["feed"], lambda: collect_quantum(source_cfg["quantum"], start, end))

    all_records = dedupe(all_records)
    # Stable display order: newest first, then source priority.
    source_order = {"pr": 0, "nature": 1, "quantum": 2, "eprint": 3, "arxiv": 4,
                    "scienceadv": 5, "scipost": 6, "avs": 7, "qst": 8}
    all_records.sort(key=lambda r: (r.get("source_date", ""), -source_order.get(r.get("source", ""), 9)), reverse=True)

    write_json(run_dir / "candidates.json", all_records)
    state = update_state(state, all_records, now.isoformat(timespec="seconds"))
    state["last_target_date"] = target.isoformat()
    write_json(DATA_DIR / "state.json", state)

    manifest = {
        "target_date": target.isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat(), "days": days},
        "timezone": config["time"]["timezone"],
        "generated_at": now.isoformat(timespec="seconds"),
        "topic": config["topic"]["name"],
        "total_candidates": len(all_records),
        "today_candidates": len({r["id"] for r in all_records if r.get("source_date") == target.isoformat()}),
        "sources": coverage,
    }
    write_json(run_dir / "manifest.json", manifest)
    print(f"\nSaved {len(all_records)} unique candidates to {run_dir}")
    print(f"Today ({target}): {manifest['today_candidates']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
