#!/usr/bin/env python3
"""Apply the machine-readable SCOPE_CONFIG block in SCOPE.md.

SCOPE.md is the human-editable source of truth. The JSON block between
<!-- SCOPE_CONFIG and --> controls categories, keywords, feeds and journal
lists. collect.py calls apply_scope() automatically at startup.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "SCOPE.md"
CONFIG = ROOT / "config" / "scope.json"


def read_block() -> dict:
    text = SCOPE.read_text(encoding="utf-8")
    match = re.search(r"<!--\s*SCOPE_CONFIG\s*\n(.*?)\n\s*-->", text, re.S)
    if not match:
        raise ValueError("SCOPE.md is missing <!-- SCOPE_CONFIG ... -->")
    return json.loads(match.group(1))


def apply_scope(config: dict | None = None) -> dict:
    config = json.loads(json.dumps(config)) if config is not None else json.loads(CONFIG.read_text(encoding="utf-8"))
    block = read_block()
    required = ("arxiv_categories", "include_keywords", "exclude_keywords", "nature_feeds",
                "pr_journals", "extra_journals", "quantum_feed", "eprint_feed", "lookback_days")
    for key in required:
        if key not in block:
            raise ValueError(f"SCOPE_CONFIG missing {key}")
    config["sources"]["arxiv"]["categories"] = list(block["arxiv_categories"])
    config["topic"]["include_keywords"] = list(block["include_keywords"])
    config["topic"]["exclude_keywords"] = list(block["exclude_keywords"])
    config["sources"]["nature"]["feeds"] = dict(block["nature_feeds"])
    config["sources"]["pr"]["journals"] = dict(block["pr_journals"])
    config["sources"]["extra_journals"] = dict(block["extra_journals"])
    config["sources"]["quantum"]["feed"] = str(block["quantum_feed"])
    config["sources"]["eprint"]["feed"] = str(block["eprint_feed"])
    config["sources"]["eprint"]["enabled"] = bool(block.get("eprint_enabled", True))
    config["time"]["lookback_days"] = int(block["lookback_days"])
    return config


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="validate without writing")
    args = ap.parse_args()
    config = apply_scope()
    if not args.check:
        CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SCOPE.md -> config/scope.json synced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
