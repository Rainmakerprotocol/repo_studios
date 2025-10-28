#!/usr/bin/env python3
"""Diff two standards index YAML files and emit structured artifacts."""

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
DEFAULT_OUTPUT_DIR = Path(
    ".repo_studios/reports/producer_reports/standards_index_diff_reports"
)
RUN_PREFIX = "standards_index_diff"
DEFAULT_ARTIFACTS_TO_KEEP = 10

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARIES_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import copy_latest_artifact
except ModuleNotFoundError:  # pragma: no cover - fallback when run as script
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import copy_latest_artifact


class DiffError(Exception):
    """Raised when diff generation fails."""


def _current_utc() -> datetime:
    return datetime.now(timezone.utc)


def _format_run_slug(moment: datetime) -> str:
    return moment.strftime("%Y%m%d_%H%M%S")


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
        return raw, _current_utc()


def _ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_slug(slug: str) -> str:
    """Make a filesystem-safe slug across platforms."""

    sanitized = slug.replace("/", "_").replace("\\", "_")
    if os.sep not in {"/", "\\"}:
        sanitized = sanitized.replace(os.sep, "_")
    return sanitized


def _prepare_run_dir(output_dir: Path, run_slug: str) -> Path:
    safe_slug = _sanitize_slug(run_slug)
    run_dir = output_dir / f"{RUN_PREFIX}-{safe_slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:
    keep = max(keep, 1)
    if not output_dir.exists():
        return
    dirs = [
        path
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(f"{RUN_PREFIX}-")
    ]
    dirs.sort(key=lambda item: item.name, reverse=True)
    for index, path in enumerate(dirs):
        if index < keep or path == current_run:
            continue
        for child in path.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)
        path.rmdir()


_copy_latest = copy_latest_artifact


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


def load(path: Path) -> dict[str, Any]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:  # pragma: no cover - validated upstream
        raise DiffError(f"Input file not found: {path}") from exc
    except Exception as exc:  # pragma: no cover - malformed yaml
        raise DiffError(f"Failed to parse {path}: {exc}") from exc


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
        "integrity_hash_changed": old_index.get("integrity_hash")
        != new_index.get("integrity_hash"),
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
        help="Directory to write structured artifacts",
    )
    parser.add_argument(
        "--timestamp",
        help="ISO8601 timestamp for the run directory",
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
    if fail_policy == "any":
        return True
    wanted = {part.strip() for part in fail_policy.split(",") if part.strip()}
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
        "schema_version": 1,
        "status": status,
        "timestamp": run_slug,
        "generated_utc": generated_at.isoformat(),
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


def _write_report_json(run_dir: Path, payload: dict[str, Any]) -> Path:
    path = run_dir / "report.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _format_change_row(change: dict[str, Any]) -> str:
    details: list[str] = []
    if change.get("from") is not None or change.get("to") is not None:
        details.append(f"{change.get('from')} → {change.get('to')}")
    return "; ".join(details) if details else ""


def _write_report_md(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Standards Index Diff Report\n\n")
    lines.append(f"- generated_utc: {payload['generated_utc']}\n")
    lines.append(f"- status: {payload['status']}\n")
    lines.append(f"- old_index: {payload['old_index']}\n")
    lines.append(f"- new_index: {payload['new_index']}\n")
    lines.append(f"- fail_policy: {payload['fail_policy']}\n")
    lines.append(f"- change_count: {payload['change_count']}\n")
    lines.append(f"- should_fail: {str(payload['should_fail']).lower()}\n")
    if payload.get("integrity_hash_changed") is not None:
        lines.append(
            f"- integrity_hash_changed: {str(payload['integrity_hash_changed']).lower()}\n"
        )
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
            lines.append(
                f"| {change['id']} | {change['kind']} | {_format_change_row(change)} |\n"
            )
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


def _write_report_log(payload: dict[str, Any]) -> str:
    lines = [
        f"status={payload['status']}",
        f"change_count={payload['change_count']}",
        f"should_fail={str(payload['should_fail']).lower()}",
        f"fail_policy={payload['fail_policy']}",
        f"old_index={payload['old_index']}",
        f"new_index={payload['new_index']}",
        f"integrity_hash_old={payload.get('integrity_hash_old')}",
        f"integrity_hash_new={payload.get('integrity_hash_new')}",
        f"integrity_hash_changed={payload.get('integrity_hash_changed')}",
    ]
    if payload.get("notes"):
        lines.append(f"notes={payload['notes']}")
    lines.append("summary:")
    for kind, count in sorted((payload.get("summary") or {}).items()):
        lines.append(f"  {kind}={count}")
    return "\n".join(lines) + "\n"


def _write_raw_artifacts(
    *,
    run_dir: Path,
    diff: dict[str, Any] | None,
    notes: str,
) -> tuple[Path | None, Path]:
    raw_json_path: Path | None = None
    raw_txt_path = run_dir / "raw.txt"
    raw_chunks: list[str] = []

    if diff is not None:
        raw_json_path = run_dir / "raw.json"
        raw_json_path.write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8")
        raw_chunks.append(json.dumps(diff, indent=2))

    if notes:
        raw_chunks.append(f"Notes: {notes}")

    if not raw_chunks:
        raw_chunks.append("[]")

    raw_txt_path.write_text("\n\n".join(raw_chunks) + "\n", encoding="utf-8")
    return raw_json_path, raw_txt_path


def write_artifacts(
    payload: dict[str, Any],
    *,
    diff: dict[str, Any] | None,
    run_dir: Path,
    output_dir: Path,
    keep: int,
) -> None:
    report_json_path = _write_report_json(run_dir, payload)
    report_md_path = run_dir / "report.md"
    report_md_path.write_text(_write_report_md(payload), encoding="utf-8")
    report_log_path = run_dir / "log.txt"
    report_log_path.write_text(_write_report_log(payload), encoding="utf-8")

    raw_json_path, raw_txt_path = _write_raw_artifacts(
        run_dir=run_dir, diff=diff, notes=payload.get("notes", "")
    )

    latest_pairs = [
        (report_json_path, output_dir / "latest_report.json"),
        (report_md_path, output_dir / "latest_report.md"),
        (report_log_path, output_dir / "latest_report.log"),
        (raw_txt_path, output_dir / "latest_raw.txt"),
    ]
    if raw_json_path is not None:
        latest_pairs.append((raw_json_path, output_dir / "latest_raw.json"))

    for src, dest in latest_pairs:
        _copy_latest(src, dest)

    prune_old_runs(output_dir, keep=keep, current_run=run_dir)


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)

    repo_root = Path(args.repo_root).resolve()
    output_dir = _resolve_output_dir(args.output_dir, repo_root)
    _ensure_directory(output_dir)
    run_slug, generated_at = _resolve_timestamp(args.timestamp)
    run_dir = _prepare_run_dir(output_dir, run_slug)

    old_path = _resolve_input(args.old, repo_root)
    new_path = _resolve_input(args.new, repo_root)

    if not old_path.exists() or not new_path.exists():
        missing = [str(path) for path in (old_path, new_path) if not path.exists()]
        payload = _compose_report_payload(
            run_slug=run_slug,
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
            run_dir=run_dir,
            output_dir=output_dir,
            keep=args.artifacts_to_keep,
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
            run_slug=run_slug,
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
            run_dir=run_dir,
            output_dir=output_dir,
            keep=args.artifacts_to_keep,
        )
        return 2

    status = "changes" if diff_data["changes"] else "no_changes"
    should_fail_flag = should_fail(diff_data["changes"], args.fail_on)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(diff_data, indent=2) + "\n", encoding="utf-8")

    payload = _compose_report_payload(
        run_slug=run_slug,
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

    write_artifacts(
        payload,
        diff=diff_data,
        run_dir=run_dir,
        output_dir=output_dir,
        keep=args.artifacts_to_keep,
    )

    if diff_data["integrity_hash_changed"]:
        logging.info(
            "Integrity hash changed: %s -> %s",
            diff_data["integrity_hash_old"],
            diff_data["integrity_hash_new"],
        )
    logging.info("Standards index diff written to %s", run_dir)
    return 1 if should_fail_flag else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
