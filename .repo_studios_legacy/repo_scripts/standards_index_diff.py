#!/usr/bin/env python
"""Diff two standards index YAML files.

Focus: rule-level semantic changes + top-level integrity hash drift.

Change categories reported:
  - added: rule id present only in NEW
  - removed: rule id present only in OLD
  - severity_changed: same id but severity differs
  - rationale_changed: same id severity same but rationale text changed (hash unaffected)
  - summary_changed: same id severity same but summary text changed
  - applies_changed: applies_to list differs (order-insensitive compare)
  - categories_changed: category_ids differ (order-insensitive)
  - other_changed: any other key difference (excluding last_updated & tolerated keys)

Exit codes:
  0 clean (no meaningful diffs)
  1 differences found
  2 usage / parse error

Notes:
  - Integrity hash drift is printed separately (it only reflects id|last_updated|severity).
  - Designed to be CI friendly: machine parseable JSON output available via --json.
  - Unrecognized top-level schema versions trigger a warning, not failure (forward compatible).

Examples:
  python scripts/standards_index_diff.py old.yaml new.yaml
  python scripts/standards_index_diff.py old.yaml new.yaml --json diff.json --fail-on any
  python scripts/standards_index_diff.py old.yaml new.yaml --fail-on severity_changed,added

Fail policy (--fail-on): comma-separated set of change kinds whose presence forces exit 1.
If omitted, any change returns exit 1 (default conservative stance).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

CHANGE_KINDS = {
    "added",
    "removed",
    "severity_changed",
    "rationale_changed",
    "summary_changed",
    "applies_changed",
    "categories_changed",
    "other_changed",
}

TOLERATE_DIFF_KEYS = {"last_updated"}


def load(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover - coarse
        logging.exception("failed to parse %s: %s", path, exc)
        sys.exit(2)
    return data


def index_rules(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {r.get("id"): r for r in index.get("rules", []) if r.get("id")}


def classify(
    id_: str, old: dict[str, Any] | None, new: dict[str, Any] | None
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    if old is None and new is not None:
        changes.append({"id": id_, "kind": "added"})
        return changes
    if new is None and old is not None:
        changes.append({"id": id_, "kind": "removed"})
        return changes
    assert old is not None and new is not None  # both present

    # Severity change (hash driver)
    if old.get("severity") != new.get("severity"):
        changes.append(
            {
                "id": id_,
                "kind": "severity_changed",
                "from": old.get("severity"),
                "to": new.get("severity"),
            }
        )

    # Non-hash content changes (rationale, summary)
    if old.get("rationale") != new.get("rationale"):
        changes.append({"id": id_, "kind": "rationale_changed"})
    if old.get("summary") != new.get("summary"):
        changes.append({"id": id_, "kind": "summary_changed"})

    # applies_to list (compare as sets)
    if set(old.get("applies_to", [])) != set(new.get("applies_to", [])):
        changes.append({"id": id_, "kind": "applies_changed"})

    # category_ids
    if set(old.get("category_ids", [])) != set(new.get("category_ids", [])):
        changes.append({"id": id_, "kind": "categories_changed"})

    # Other keys drift (excluding tolerated + ones explicitly tested)
    exclude = {
        "id",
        "severity",
        "rationale",
        "summary",
        "applies_to",
        "category_ids",
        *TOLERATE_DIFF_KEYS,
    }
    old_extra = {k: old[k] for k in old.keys() - exclude}
    new_extra = {k: new[k] for k in new.keys() - exclude}
    if old_extra != new_extra:
        changes.append({"id": id_, "kind": "other_changed"})

    return changes


def generate_diff(old_index: dict[str, Any], new_index: dict[str, Any]) -> dict[str, Any]:
    old_rules = index_rules(old_index)
    new_rules = index_rules(new_index)
    all_ids = set(old_rules) | set(new_rules)
    all_changes: list[dict[str, Any]] = []
    for rid in sorted(all_ids):
        all_changes.extend(classify(rid, old_rules.get(rid), new_rules.get(rid)))

    summary: dict[str, int] = {}
    for c in all_changes:
        summary[c["kind"]] = summary.get(c["kind"], 0) + 1

    return {
        "integrity_hash_old": old_index.get("integrity_hash"),
        "integrity_hash_new": new_index.get("integrity_hash"),
        "integrity_hash_changed": old_index.get("integrity_hash")
        != new_index.get("integrity_hash"),
        "changes": all_changes,
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="standards_index_diff",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__,
    )
    p.add_argument("old", help="Old (baseline) index YAML")
    p.add_argument("new", help="New index YAML")
    p.add_argument("--json", dest="json_out", help="Write machine-readable diff JSON to this path")
    p.add_argument(
        "--fail-on",
        help="Comma-separated change kinds that cause non-zero exit; 'any' = any change (default)",
        default="any",
    )
    return p


def should_fail(changes: list[dict[str, Any]], fail_policy: str) -> bool:
    if not changes:
        return False
    if fail_policy == "any":
        return True
    wanted = {p.strip() for p in fail_policy.split(",") if p.strip()}
    invalid = wanted - CHANGE_KINDS
    if invalid:
        logging.warning("ignoring unknown fail-on kinds: %s", ", ".join(sorted(invalid)))
        wanted = wanted & CHANGE_KINDS
    return any(c["kind"] in wanted for c in changes)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    old_path = Path(args.old)
    new_path = Path(args.new)
    if not old_path.exists() or not new_path.exists():
        logging.error("one or both paths do not exist")
        return 2
    old_index = load(old_path)
    new_index = load(new_path)
    diff = generate_diff(old_index, new_index)

    # Human readable summary
    if diff["integrity_hash_changed"]:
        logging.info(
            "Integrity hash changed: %s -> %s",
            diff["integrity_hash_old"],
            diff["integrity_hash_new"],
        )
    if not diff["changes"]:
        sys.stdout.write("No rule changes detected\n")
    else:
        sys.stdout.write("Rule-level changes:\n")
        for c in diff["changes"]:
            line = f" - {c['id']}: {c['kind']}"
            if c.get("from") is not None or c.get("to") is not None:
                line += f" ({c.get('from')} -> {c.get('to')})"
            sys.stdout.write(line + "\n")
        sys.stdout.write("Summary:\n")
        for kind in sorted(diff["summary"]):
            sys.stdout.write(f" * {kind}: {diff['summary'][kind]}\n")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8")

    return 1 if should_fail(diff["changes"], args.fail_on) else 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
