#!/usr/bin/env python
"""Generate condensed prompt seed from standards index.

Purpose: Provide a small, high-signal payload of critical & error-level rules to
bootstrap AI prompting contexts without overloading token budgets.

Selection logic:
  * Include rules with severity in {critical, error}
  * Optionally include 'warn' if --include-warn provided
  * Group by category and output in chosen format

Formats:
  - text (default): human readable bullet list
  - yaml: structured mapping {categories: {cat_id: {title, rules: [ {id, summary, severity} ] }}, integrity_hash}
  - json: same structure as yaml but JSON

CLI:
  standards_prompt_seed.py --format text|yaml|json [--include-warn] [--out path]
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "repo_standards_index.yaml"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():  # pragma: no cover
        raise SystemExit(f"index not found: {INDEX_PATH}")
    return yaml.safe_load(INDEX_PATH.read_text(encoding="utf-8")) or {}


def build_seed(include_warn: bool, index: dict[str, Any]) -> dict[str, Any]:
    categories = index.get("categories", {}) or {}
    rules = index.get("rules", []) or []
    keep_levels = {"critical", "error"} | ({"warn"} if include_warn else set())
    grouped: dict[str, dict[str, Any]] = {}
    for r in rules:
        if r.get("severity") not in keep_levels:
            continue
        for cat in r.get("category_ids", []) or []:
            grp = grouped.setdefault(
                cat, {"title": categories.get(cat, {}).get("title", cat), "rules": []}
            )
            grp["rules"].append(
                {"id": r.get("id"), "summary": r.get("summary"), "severity": r.get("severity")}
            )
    # Sort rules within groups for determinism
    for g in grouped.values():
        g["rules"].sort(key=lambda x: x["id"])
    return {"integrity_hash": index.get("integrity_hash"), "categories": grouped}


def format_text(seed: dict[str, Any]) -> str:
    lines = [f"Integrity: {seed.get('integrity_hash')}", ""]
    for cat, data in sorted(seed["categories"].items()):
        lines.append(f"Category: {data['title']} ({cat})")
        for r in data["rules"]:
            lines.append(f"  - [{r['severity'].upper()}] {r['id']}: {r['summary']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_seed(seed: dict[str, Any], fmt: str, out_path: str | None) -> None:
    if fmt == "text":
        data = format_text(seed)
    elif fmt == "yaml":  # pragma: no cover - simple serialization
        data = yaml.safe_dump(seed, sort_keys=True)
    elif fmt == "json":
        data = json.dumps(seed, indent=2) + "\n"
    else:  # pragma: no cover
        raise SystemExit(f"unknown format: {fmt}")
    if out_path:
        Path(out_path).write_text(data, encoding="utf-8")
        logging.info("Wrote seed to %s", out_path)
    else:
        print(data, end="")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="standards_prompt_seed",
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--format", default="text", choices=["text", "yaml", "json"], help="Output format"
    )
    p.add_argument("--include-warn", action="store_true", help="Include warn severity rules")
    p.add_argument("--out", dest="out", help="Write to file instead of stdout")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    index = load_index()
    seed = build_seed(args.include_warn, index)
    write_seed(seed, args.format, args.out)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
