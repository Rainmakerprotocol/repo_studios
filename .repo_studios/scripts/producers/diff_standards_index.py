#!/usr/bin/env python3
"""Diff two standards index YAML files and emit a canonical report bundle.

This producer writes positional-encoded artifacts under the configured reports root:

<reports_root>/<viewer_slug>/<topic>/<YYYYMMDD-HHMM>/

Artifacts:
- manifest.json
- summary.md
- telemetry.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
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

DEFAULT_OUTPUT_DIR = Path(".repo_studios/command_center/reports")
VIEWER_SLUG = "rawview"
TOPIC_SLUG = "standards_index_diff"
DEFAULT_ARTIFACTS_TO_KEEP = 10

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARIES_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import prune_run_directories
    from libraries.database_integration import create_storage
except ModuleNotFoundError:  # pragma: no cover - fallback when run as script
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import prune_run_directories
    from libraries.database_integration import create_storage


class DiffError(Exception):
    """Raised when diff generation fails."""


def _current_utc() -> datetime:
    return datetime.now(timezone.utc)


def _format_run_slug(moment: datetime) -> str:
    return moment.strftime("%Y%m%d-%H%M")


def _resolve_timestamp(raw: str | None) -> tuple[str, datetime]:
    if not raw:
        now = _current_utc()
        return _format_run_slug(now), now
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return _format_run_slug(parsed), parsed
    except ValueError:
        logging.warning("--timestamp value was not ISO-8601; falling back to current time")
        now = _current_utc()
        return _format_run_slug(now), now


def _resolve_timestamp_slug(explicit: str | None) -> str:
    if explicit is None:
        return _current_utc().strftime("%Y%m%d-%H%M")

    cleaned = explicit.strip()
    if len(cleaned) != 13 or cleaned[8] != "-":
        raise ValueError("run timestamp must be in YYYYMMDD-HHMM format")
    if not (cleaned[:8] + cleaned[9:]).isdigit():
        raise ValueError("run timestamp must be in YYYYMMDD-HHMM format")
    return cleaned


def _ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve_output_dir(output_value: str | None, repo_root: Path) -> Path:
    value = output_value or str(DEFAULT_OUTPUT_DIR)
    out_dir = Path(value)
    if not out_dir.is_absolute():
        out_dir = (repo_root / out_dir).resolve()
    return out_dir


def _resolve_input(path_str: str, repo_root: Path) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    return path


def _rel_to_repo(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path.resolve())


def _bundle_dir(output_dir: Path, *, timestamp: str) -> Path:
    return output_dir / VIEWER_SLUG / TOPIC_SLUG / timestamp


def load(path: Path) -> dict[str, Any]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:  # pragma: no cover - validated upstream
        raise DiffError(f"Input file not found: {path}") from exc
    except Exception as exc:  # pragma: no cover - malformed yaml
        raise DiffError(f"Failed to parse {path}: {exc}") from exc


def index_rules(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {r.get("id"): r for r in index.get("rules", []) if r.get("id")}


def classify(id_: str, old: dict[str, Any] | None, new: dict[str, Any] | None) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    if old is None and new is not None:
        changes.append({"id": id_, "kind": "added"})
        return changes
    if new is None and old is not None:
        changes.append({"id": id_, "kind": "removed"})
        return changes
    assert old is not None and new is not None

    if old.get("severity") != new.get("severity"):
        changes.append(
            {
                "id": id_,
                "kind": "severity_changed",
                "from": old.get("severity"),
                "to": new.get("severity"),
            }
        )

    if old.get("rationale") != new.get("rationale"):
        changes.append({"id": id_, "kind": "rationale_changed"})
    if old.get("summary") != new.get("summary"):
        changes.append({"id": id_, "kind": "summary_changed"})

    if set(old.get("applies_to", [])) != set(new.get("applies_to", [])):
        changes.append({"id": id_, "kind": "applies_changed"})

    if set(old.get("category_ids", [])) != set(new.get("category_ids", [])):
        changes.append({"id": id_, "kind": "categories_changed"})

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
    for change in all_changes:
        summary[change["kind"]] = summary.get(change["kind"], 0) + 1

    return {
        "integrity_hash_old": old_index.get("integrity_hash"),
        "integrity_hash_new": new_index.get("integrity_hash"),
        "integrity_hash_changed": old_index.get("integrity_hash") != new_index.get("integrity_hash"),
        "changes": all_changes,
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diff standards index files and emit structured artifacts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("old", help="Old (baseline) index YAML")
    parser.add_argument("new", help="New index YAML")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve relative paths",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Reports root directory used to write positional artifacts",
    )
    parser.add_argument(
        "--timestamp",
        help="DEPRECATED: ISO8601 timestamp seed; use --run-timestamp for deterministic runs.",
    )
    parser.add_argument(
        "--run-timestamp",
        default=None,
        help="Override run timestamp slug (UTC, YYYYMMDD-HHMM). Useful for deterministic tests.",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="How many historical runs to retain",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR)",
    )
    parser.add_argument(
        "--json",
        dest="json_out",
        help="Optional path to write the raw diff JSON",
    )
    parser.add_argument(
        "--fail-on",
        default="any",
        help="Comma-separated kinds that trigger exit 1; 'any' means every change",
    )
    return parser


def should_fail(changes: list[dict[str, Any]], fail_policy: str) -> bool:
    if not changes:
        return False
    cleaned = fail_policy.strip().lower()
    if cleaned in {"", "none", "never"}:
        return False
    if cleaned == "any":
        return True
    wanted = {part.strip().lower() for part in fail_policy.split(",") if part.strip()}
    invalid = wanted - CHANGE_KINDS
    if invalid:
        logging.warning("Ignoring unknown fail-on kinds: %s", ", ".join(sorted(invalid)))
        wanted &= CHANGE_KINDS
    return any(change["kind"] in wanted for change in changes)


def _compose_report_payload(
    *,
    run_slug: str,
    generated_at: datetime,
    repo_root: Path,
    old_path: Path,
    new_path: Path,
    fail_policy: str,
    diff: dict[str, Any] | None,
    status: str,
    should_fail_flag: bool,
    notes: str,
) -> dict[str, Any]:
    summary = diff["summary"] if diff else {}
    changes = diff["changes"] if diff else []
    return {
        "status": status,
        "run_timestamp": run_slug,
        "generated_at": generated_at.isoformat(),
        "repo_root": str(repo_root),
        "old_index": _rel_to_repo(old_path, repo_root),
        "new_index": _rel_to_repo(new_path, repo_root),
        "fail_policy": fail_policy,
        "should_fail": should_fail_flag,
        "change_count": len(changes),
        "summary": summary,
        "changes": changes,
        "integrity_hash_old": diff.get("integrity_hash_old") if diff else None,
        "integrity_hash_new": diff.get("integrity_hash_new") if diff else None,
        "integrity_hash_changed": diff.get("integrity_hash_changed") if diff else None,
        "notes": notes,
    }


def _format_change_row(change: dict[str, Any]) -> str:
    details: list[str] = []
    if change.get("from") is not None or change.get("to") is not None:
        details.append(f"{change.get('from')} → {change.get('to')}")
    return "; ".join(details) if details else ""


def _write_summary_md(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Standards Index Diff Report\n\n")
    lines.append(f"- generated_at: {payload['generated_at']}\n")
    lines.append(f"- run_timestamp: {payload['run_timestamp']}\n")
    lines.append(f"- status: {payload['status']}\n")
    lines.append(f"- old_index: {payload['old_index']}\n")
    lines.append(f"- new_index: {payload['new_index']}\n")
    lines.append(f"- fail_policy: {payload['fail_policy']}\n")
    lines.append(f"- change_count: {payload['change_count']}\n")
    lines.append(f"- should_fail: {str(payload['should_fail']).lower()}\n")
    if payload.get("integrity_hash_changed") is not None:
        lines.append(f"- integrity_hash_changed: {str(payload['integrity_hash_changed']).lower()}\n")
    if payload.get("notes"):
        lines.append(f"- notes: {payload['notes']}\n")
    lines.append("\n")

    lines.append("## Summary\n\n")
    summary = payload.get("summary") or {}
    if summary:
        lines.append("| Change Kind | Count |\n")
        lines.append("|---|---:|\n")
        for kind in sorted(summary):
            lines.append(f"| {kind} | {summary[kind]} |\n")
        lines.append("\n")
    else:
        lines.append("No rule changes detected.\n\n")

    changes = payload.get("changes") or []
    if changes:
        lines.append("## Changes\n\n")
        lines.append("| Rule ID | Kind | Details |\n")
        lines.append("|---|---|---|\n")
        for change in changes:
            lines.append(f"| {change['id']} | {change['kind']} | {_format_change_row(change)} |\n")
        lines.append("\n")

    lines.append("## How to Reproduce\n\n")
    command = (
        f"python {Path(__file__).resolve()} "
        f"{payload['old_index']} {payload['new_index']} --fail-on {payload['fail_policy']}"
    )
    lines.append("```bash\n")
    lines.append(f"{command}\n")
    lines.append("```\n")
    return "".join(lines)


def write_artifacts(
    payload: dict[str, Any],
    *,
    diff: dict[str, Any] | None,
    output_dir: Path,
    timestamp: str,
    keep: int,
    logger: logging.Logger,
) -> Path:
    bundle_dir = _bundle_dir(output_dir, timestamp=timestamp)
    storage = create_storage(output_dir, VIEWER_SLUG, TOPIC_SLUG, timestamp=timestamp)

    now_iso = payload["generated_at"]
    repo_root = Path(payload["repo_root"]).resolve()

    manifest_path = bundle_dir / "manifest.json"
    summary_path = bundle_dir / "summary.md"
    telemetry_path = bundle_dir / "telemetry.json"

    manifest: dict[str, object] = {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp,
        "generated_at": now_iso,
        "status": "ok" if payload["status"] != "error" else "error",
        "git_sha": None,
        "repo_root": str(repo_root),
        "inputs": {
            "old_index": payload["old_index"],
            "new_index": payload["new_index"],
            "fail_policy": payload["fail_policy"],
            "artifacts_to_keep": max(1, keep),
            "run_timestamp": timestamp,
        },
        "catalog": [
            {"artifact": "manifest.json", "path": _rel_to_repo(manifest_path, repo_root)},
            {"artifact": "summary.md", "path": _rel_to_repo(summary_path, repo_root)},
            {"artifact": "telemetry.json", "path": _rel_to_repo(telemetry_path, repo_root)},
        ],
        "provenance": {
            "script": "diff_standards_index.py",
            "trigger": "cli",
        },
    }

    summary_md = _write_summary_md(payload)

    summary_counts = payload.get("summary") or {}
    change_count = int(payload.get("change_count", 0) or 0)
    telemetry_metrics: dict[str, object] = {"change_count": change_count}
    for kind in CHANGE_KINDS:
        telemetry_metrics[kind] = int(summary_counts.get(kind, 0) or 0)
    telemetry_metrics["integrity_hash_changed"] = bool(payload.get("integrity_hash_changed"))
    telemetry_metrics["should_fail"] = bool(payload.get("should_fail"))

    telemetry: dict[str, object] = {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp,
        "generated_at": now_iso,
        "status": payload["status"],
        "metrics": telemetry_metrics,
        "inputs": {
            "old_index": payload["old_index"],
            "new_index": payload["new_index"],
            "fail_policy": payload["fail_policy"],
        },
        "payload": {
            "summary": payload.get("summary") or {},
            "changes": payload.get("changes") or [],
            "integrity_hash_old": payload.get("integrity_hash_old"),
            "integrity_hash_new": payload.get("integrity_hash_new"),
            "integrity_hash_changed": payload.get("integrity_hash_changed"),
            "notes": payload.get("notes") or "",
        },
    }

    # DB_INTEGRATION_MARKER: standards index diff manifest write
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: standards index diff summary markdown write
    storage.write_summary({"markdown": summary_md}, format="md")
    # DB_INTEGRATION_MARKER: standards index diff telemetry write
    storage.write_telemetry(telemetry)

    base_dir = output_dir / VIEWER_SLUG / TOPIC_SLUG
    prune_run_directories(
        base_dir,
        keep=max(1, keep),
        current_run=bundle_dir,
        logger=logger,
    )

    return bundle_dir


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)
    log = logging.getLogger("standards_index_diff")

    repo_root = Path(args.repo_root).resolve()
    output_dir = _resolve_output_dir(args.output_dir, repo_root)
    _ensure_directory(output_dir)
    timestamp_slug = _resolve_timestamp_slug(args.run_timestamp)
    run_slug, generated_at = _resolve_timestamp(args.timestamp)
    if args.timestamp and not args.run_timestamp:
        timestamp_slug = run_slug

    old_path = _resolve_input(args.old, repo_root)
    new_path = _resolve_input(args.new, repo_root)

    if not old_path.exists() or not new_path.exists():
        missing = [str(path) for path in (old_path, new_path) if not path.exists()]
        payload = _compose_report_payload(
            run_slug=timestamp_slug,
            generated_at=generated_at,
            repo_root=repo_root,
            old_path=old_path,
            new_path=new_path,
            fail_policy=args.fail_on,
            diff=None,
            status="error",
            should_fail_flag=False,
            notes=f"Missing input files: {', '.join(missing)}",
        )
        write_artifacts(
            payload,
            diff=None,
            output_dir=output_dir,
            timestamp=timestamp_slug,
            keep=args.artifacts_to_keep,
            logger=log,
        )
        return 2

    diff_data: dict[str, Any] | None = None
    notes = ""

    try:
        old_index = load(old_path)
        new_index = load(new_path)
        diff_data = generate_diff(old_index, new_index)
    except DiffError as exc:
        notes = str(exc)
        payload = _compose_report_payload(
            run_slug=timestamp_slug,
            generated_at=generated_at,
            repo_root=repo_root,
            old_path=old_path,
            new_path=new_path,
            fail_policy=args.fail_on,
            diff=None,
            status="error",
            should_fail_flag=False,
            notes=notes,
        )
        write_artifacts(
            payload,
            diff=None,
            output_dir=output_dir,
            timestamp=timestamp_slug,
            keep=args.artifacts_to_keep,
            logger=log,
        )
        return 2

    status = "changes" if diff_data["changes"] else "no_changes"
    should_fail_flag = should_fail(diff_data["changes"], args.fail_on)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(diff_data, indent=2) + "\n", encoding="utf-8")

    payload = _compose_report_payload(
        run_slug=timestamp_slug,
        generated_at=generated_at,
        repo_root=repo_root,
        old_path=old_path,
        new_path=new_path,
        fail_policy=args.fail_on,
        diff=diff_data,
        status=status,
        should_fail_flag=should_fail_flag,
        notes=notes,
    )

    bundle_dir = write_artifacts(
        payload,
        diff=diff_data,
        output_dir=output_dir,
        timestamp=timestamp_slug,
        keep=args.artifacts_to_keep,
        logger=log,
    )

    if diff_data["integrity_hash_changed"]:
        logging.info(
            "Integrity hash changed: %s -> %s",
            diff_data["integrity_hash_old"],
            diff_data["integrity_hash_new"],
        )
    logging.info("Standards index diff bundle written to %s", bundle_dir)
    return 1 if should_fail_flag else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
