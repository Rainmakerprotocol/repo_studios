#!/usr/bin/env python
"""CLI helper for querying `repo_standards_index.yaml`.

Usage examples:
    python scripts/standards_index_cli.py list --severity error
  python scripts/standards_index_cli.py search --text "hash" --category python_coding
  python scripts/standards_index_cli.py show --id PY001

Commands:
  list    List rule IDs (with optional filters)
  search  Full rule summaries filtered by free-text (case-insensitive substring)
  show    Display a single rule in detail (YAML)
  stats   Print basic counts and integrity hash

Filtering options (list/search):
    --severity <sev>            One of: info|warn|error|critical (case-insensitive). Legacy aliases low→info, medium→warn, high→error are accepted with a WARN.
  --category <category_id>    Filter to rules containing this category id (repeatable)
  --applies <scope>           Filter where <scope> appears in applies_to (substring match)
  --source-frag <text>        Substring match against source path
  --text <substring>          (search only) case-insensitive substring over id+summary+rationale

Exit codes:
  0 success
  1 usage / validation error
  2 file not found / parse error
  3 rule not found (show)

Design notes:
  - Keeps dependency surface minimal (std lib + PyYAML already present).
  - Preserves deterministic ordering (same as build script: by id asc for output lists).
  - Avoids mutating the index (read-only usage).
  - Intentionally narrow capability; future diff / gap / enforce tools build separately.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "repo_standards_index.yaml"
CANONICAL_SEVERITIES = {"info", "warn", "error", "critical"}
ALIAS_SEVERITY_MAP = {"low": "info", "medium": "warn", "high": "error"}
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        logging.error("index file not found: %s", INDEX_PATH)
        sys.exit(2)
    try:
        data = yaml.safe_load(INDEX_PATH.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover - coarse error boundary
        logging.exception("failed to parse index: %s", exc)
        sys.exit(2)
    return data


def _norm(s: str) -> str:
    return s.lower().strip()


def _canonical_severity(sev: str | None) -> str | None:
    if not sev:
        return None
    s = _norm(sev)
    if s in ALIAS_SEVERITY_MAP:
        logging.warning(
            "severity alias '%s' mapped to '%s' (prefer canonical names)", s, ALIAS_SEVERITY_MAP[s]
        )
        s = ALIAS_SEVERITY_MAP[s]
    return s


def filter_rules(rules: Iterable[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    requested_sev = _canonical_severity(getattr(args, "severity", None))
    for r in rules:
        if requested_sev and _norm(r.get("severity", "")) != requested_sev:
            continue
        if args.category and args.category not in r.get("category_ids", []):
            continue
        if args.category_multi:
            if not all(c in r.get("category_ids", []) for c in args.category_multi):
                continue
        if args.applies and args.applies.lower() not in " ".join(r.get("applies_to", [])).lower():
            continue
        if args.source_frag and args.source_frag.lower() not in r.get("source", "").lower():
            continue
        if getattr(args, "text", None):
            blob = " ".join(
                [
                    r.get("id", ""),
                    r.get("summary", ""),
                    r.get("rationale", ""),
                ]
            ).lower()
            if args.text.lower() not in blob:
                continue
        out.append(r)
    # Deterministic order: by id ascending
    out.sort(key=lambda x: x.get("id", ""))
    return out


def cmd_list(index: dict[str, Any], args: argparse.Namespace) -> int:
    rules = filter_rules(index.get("rules", []), args)
    for r in rules:
        # stdout: intended primary output
        sys.stdout.write(f"{r.get('id')}\n")
    return 0


def cmd_search(index: dict[str, Any], args: argparse.Namespace) -> int:
    rules = filter_rules(index.get("rules", []), args)
    for r in rules:
        sys.stdout.write(f"{r.get('id')}: {r.get('summary')}\n")
    return 0


def cmd_show(index: dict[str, Any], args: argparse.Namespace) -> int:
    rid = args.id
    for r in index.get("rules", []):
        if r.get("id") == rid:
            # Emit YAML for readability
            sys.stdout.write(yaml.safe_dump(r, sort_keys=False, width=100))
            return 0
    logging.error("rule not found: %s", rid)
    return 3


def cmd_stats(index: dict[str, Any], args: argparse.Namespace) -> int:  # noqa: ARG001
    rules = index.get("rules", [])
    per_sev: dict[str, int] = {}
    for r in rules:
        sev = r.get("severity", "unknown")
        per_sev[sev] = per_sev.get(sev, 0) + 1
    sys.stdout.write(f"rules_total: {len(rules)}\n")
    for sev in sorted(per_sev):
        sys.stdout.write(f"rules_{sev}: {per_sev[sev]}\n")
    sys.stdout.write(f"integrity_hash: {index.get('integrity_hash', '')}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="standards_index_cli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    sub = p.add_subparsers(dest="command", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--severity")
        sp.add_argument("--category", help="Single category id filter")
        sp.add_argument(
            "--category-multi",
            dest="category_multi",
            action="append",
            help="Require ALL of these category ids (repeatable)",
        )
        sp.add_argument("--applies", help="Substring match in applies_to list")
        sp.add_argument("--source-frag", help="Substring match in source path")

    sp_list = sub.add_parser("list", help="List rule IDs with optional filters")
    add_common(sp_list)

    sp_search = sub.add_parser("search", help="Search rule summaries with optional filters")
    add_common(sp_search)
    sp_search.add_argument(
        "--text", required=True, help="Case-insensitive substring over id+summary+rationale"
    )

    sp_show = sub.add_parser("show", help="Show a single rule in detail")
    sp_show.add_argument("--id", required=True)

    sub.add_parser("stats", help="Show counts and integrity hash")

    return p


def validate_args(args: argparse.Namespace) -> None:
    if args.command in {"list", "search"} and args.severity:
        sev = _norm(args.severity)
        sev = ALIAS_SEVERITY_MAP.get(sev, sev)
        if sev not in CANONICAL_SEVERITIES:
            logging.error("invalid severity: %s", args.severity)
            raise SystemExit(f"invalid severity: {args.severity}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_args(args)
    except SystemExit as exc:  # propagate with exit code 1
        if exc.code != 0:
            return 1
        return 0
    index = load_index()
    if args.command == "list":
        return cmd_list(index, args)
    if args.command == "search":
        return cmd_search(index, args)
    if args.command == "show":
        return cmd_show(index, args)
    if args.command == "stats":
        return cmd_stats(index, args)
    logging.error("unknown command: %s", args.command)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
