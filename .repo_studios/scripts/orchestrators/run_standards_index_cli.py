#!/usr/bin/env python3
"""CLI helper for querying `repo_standards_index.yaml` with structured outputs."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/orchestrator_runs/standards_index_cli")
DEFAULT_INDEX_PATH = Path(".repo_studios/repo_standards_index.yaml")
DEFAULT_ARTIFACTS_TO_KEEP = 5
RUN_STEM = "standards_index_cli"
SCHEMA_VERSION = 1

CANONICAL_SEVERITIES = {"info", "warn", "error", "critical"}
ALIAS_SEVERITY_MAP = {"low": "info", "medium": "warn", "high": "error"}

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:  # pragma: no cover - prefer import when packaged
    from libraries import (  # type: ignore
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised in environments without dependency
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )

logger = logging.getLogger("run_standards_index_cli")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    index_path: Path


@dataclass
class Options:
    artifacts_to_keep: int
    log_level: str = "INFO"


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True, within_repo=True),
        "index_path": PathSpec(field="index_path", default=DEFAULT_INDEX_PATH, within_repo=True),
    },
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


class StandardsCliError(Exception):
    """Exception carrying an exit code suitable for CLI propagation."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s", force=True)


def _norm(value: str) -> str:
    return value.lower().strip()


def _canonical_severity(severity: str | None) -> str | None:
    if not severity:
        return None
    sev = _norm(severity)
    if sev in ALIAS_SEVERITY_MAP:
        canonical = ALIAS_SEVERITY_MAP[sev]
        logger.warning("severity alias '%s' mapped to '%s' (prefer canonical names)", sev, canonical)
        sev = canonical
    return sev


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_standards_index_cli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument("--repo-root", help="Repository root override (defaults to auto-detect)")
    parser.add_argument("--output-dir", help="Directory for structured bundle outputs")
    parser.add_argument("--index-path", help="Override path to repo_standards_index.yaml")
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention count for run bundles",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--severity", help="Filter on canonical severity (info|warn|error|critical)")
        sp.add_argument("--category", help="Filter to rules containing this category id")
        sp.add_argument(
            "--category-multi",
            dest="category_multi",
            action="append",
            default=[],
            help="Require ALL of these category ids (repeatable)",
        )
        sp.add_argument("--applies", help="Substring match against applies_to entries")
        sp.add_argument("--source-frag", help="Substring match against the source path")

    sp_list = sub.add_parser("list", help="List rule IDs with optional filters")
    add_common(sp_list)

    sp_search = sub.add_parser("search", help="Search rule summaries with optional filters")
    add_common(sp_search)
    sp_search.add_argument("--text", required=True, help="Case-insensitive substring over id+summary+rationale")

    sp_show = sub.add_parser("show", help="Show a single rule in detail")
    sp_show.add_argument("--id", required=True)

    sub.add_parser("stats", help="Print counts and integrity hash")

    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.command in {"list", "search"} and args.severity:
        sev = _norm(args.severity)
        sev = ALIAS_SEVERITY_MAP.get(sev, sev)
        if sev not in CANONICAL_SEVERITIES:
            raise StandardsCliError(f"invalid severity: {args.severity}", exit_code=1)


def load_index(index_path: Path) -> dict[str, Any]:
    if not index_path.exists():
        raise StandardsCliError(f"index file not found: {index_path}", exit_code=2)
    try:
        data = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover - coarse error boundary
        raise StandardsCliError(f"failed to parse index: {exc}", exit_code=2) from exc
    return data


def filter_rules(rules: Iterable[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    requested_sev = _canonical_severity(getattr(args, "severity", None))
    category = getattr(args, "category", None)
    category_multi = getattr(args, "category_multi", []) or []
    applies = getattr(args, "applies", None)
    source_frag = getattr(args, "source_frag", None)
    text = getattr(args, "text", None)

    for rule in rules:
        if requested_sev and _norm(rule.get("severity", "")) != requested_sev:
            continue
        if category and category not in rule.get("category_ids", []):
            continue
        if category_multi and not all(cat in rule.get("category_ids", []) for cat in category_multi):
            continue
        if applies and applies.lower() not in " ".join(rule.get("applies_to", [])).lower():
            continue
        if source_frag and source_frag.lower() not in rule.get("source", "").lower():
            continue
        if text:
            haystack = " ".join(
                [
                    rule.get("id", ""),
                    rule.get("summary", ""),
                    rule.get("rationale", ""),
                ]
            ).lower()
            if text.lower() not in haystack:
                continue
        filtered.append(rule)
    filtered.sort(key=lambda item: item.get("id", ""))
    return filtered


def _count_by_severity(rules: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rule in rules:
        sev = rule.get("severity", "unknown")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _collect_filters(args: argparse.Namespace) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    if args.command in {"list", "search"}:
        if args.severity:
            filters["severity"] = _canonical_severity(args.severity) or args.severity
        if args.category:
            filters["category"] = args.category
        if args.category_multi:
            filters["category_multi"] = list(args.category_multi)
        if args.applies:
            filters["applies"] = args.applies
        if args.source_frag:
            filters["source_frag"] = args.source_frag
    if args.command == "search" and args.text:
        filters["text"] = args.text
    if args.command == "show":
        filters["id"] = args.id
    return filters


def _yaml_lines(payload: dict[str, Any]) -> list[str]:
    dumped = yaml.safe_dump(payload, sort_keys=False, width=100).rstrip("\n")
    return dumped.splitlines()


def _execute_command(index: dict[str, Any], args: argparse.Namespace) -> tuple[int, dict[str, Any] | None, list[str], str | None, int]:
    rules = index.get("rules", [])
    stdout_lines: list[str] = []
    error_message: str | None = None
    items_returned = 0
    results: dict[str, Any] | None = None
    exit_code = 0

    if args.command == "list":
        matches = filter_rules(rules, args)
        stdout_lines = [rule.get("id", "") for rule in matches]
        results = {"rule_ids": stdout_lines}
        items_returned = len(stdout_lines)
    elif args.command == "search":
        matches = filter_rules(rules, args)
        stdout_lines = [f"{rule.get('id')}: {rule.get('summary')}" for rule in matches]
        results = {
            "matches": [
                {
                    "id": rule.get("id"),
                    "summary": rule.get("summary"),
                    "severity": rule.get("severity"),
                }
                for rule in matches
            ]
        }
        items_returned = len(matches)
    elif args.command == "show":
        target = next((rule for rule in rules if rule.get("id") == args.id), None)
        if target is None:
            error_message = f"rule not found: {args.id}"
            exit_code = 3
        else:
            stdout_lines = _yaml_lines(target)
            results = {"rule": target}
            items_returned = 1
    elif args.command == "stats":
        counts = _count_by_severity(rules)
        stdout_lines = [f"rules_total: {len(rules)}"]
        stdout_lines.extend(f"rules_{sev}: {count}" for sev, count in sorted(counts.items()))
        stdout_lines.append(f"integrity_hash: {index.get('integrity_hash', '')}")
        results = {
            "stats": {
                "rules_total": len(rules),
                "severity_counts": counts,
                "integrity_hash": index.get("integrity_hash", ""),
            }
        }
        items_returned = len(stdout_lines)
    else:  # pragma: no cover - defensive guard
        error_message = f"unknown command: {args.command}"
        exit_code = 1

    if error_message:
        logger.error(error_message)

    return exit_code, results, stdout_lines, error_message, items_returned


def _overall_status(exit_code: int) -> str:
    return "passed" if exit_code == 0 else "failed"


def _render_markdown_report(
    *,
    timestamp_utc: datetime,
    command: str,
    summary: dict[str, Any],
    filters: dict[str, Any],
    stdout_lines: list[str],
    error_message: str | None,
) -> str:
    lines: list[str] = ["# Standards Index CLI", ""]
    lines.append(f"Generated (UTC): {timestamp_utc.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Command: {command}")
    lines.append(f"- Exit code: {summary['exit_code']}")
    lines.append(f"- Status: {summary['overall_status']}")
    lines.append(f"- Items returned: {summary['items_returned']}")
    total_rules = summary.get("total_rules")
    lines.append(f"- Total rules: {total_rules if total_rules is not None else '<unknown>'}")
    if filters:
        lines.append("- Filters:")
        for key, value in filters.items():
            lines.append(f"  - {key}: {value}")
    lines.append("")

    if error_message:
        lines.append("## Error")
        lines.append("")
        lines.append(error_message)
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    if stdout_lines:
        lines.append("## Output")
        lines.append("")
        lines.append("```text")
        lines.extend(stdout_lines)
        lines.append("```")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    try:
        validate_args(args)
    except StandardsCliError as exc:
        logger.error(exc.message)
        summary_payload = {
            "exit_code": exc.exit_code,
            "overall_status": _overall_status(exc.exit_code),
            "items_returned": 0,
            "total_rules": None,
            "severity_counts": {},
            "error": exc.message,
        }
        timestamp_utc = datetime.now(timezone.utc)
        stdout_lines: list[str] = []
        report_payload = {
            "schema_version": SCHEMA_VERSION,
            "generated_utc": timestamp_utc.isoformat(timespec="seconds"),
            "command": args.command,
            "filters": _collect_filters(args),
            "summary": summary_payload,
            "results": None,
            "stdout": stdout_lines,
            "error": exc.message,
        }
        markdown_payload = _render_markdown_report(
            timestamp_utc=timestamp_utc,
            command=args.command,
            summary=summary_payload,
            filters=report_payload["filters"],
            stdout_lines=stdout_lines,
            error_message=exc.message,
        )
        bundle_summary = {
            "command": args.command,
            "overall_status": summary_payload["overall_status"],
            "items_returned": 0,
            "exit_code": exc.exit_code,
        }
        # Without resolved paths/options we cannot write structured artifacts; bubble up early failure.
        return {
            "exit_code": exc.exit_code,
            "stdout_lines": stdout_lines,
            "summary": summary_payload,
            "results": None,
            "error": exc.message,
            "report_json": None,
            "bundle_summary": None,
            "run_dir": None,
            "report_md": markdown_payload,
        }

    paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
    options = build_standard_options(args, OPTIONS_CONFIG)
    options = replace(options, log_level=args.log_level)
    _configure_logging(options.log_level)

    timestamp_utc = datetime.now(timezone.utc)
    stdout_lines: list[str] = []
    error_message: str | None = None
    results_payload: dict[str, Any] | None = None
    items_returned = 0
    exit_code = 0
    severity_counts: dict[str, int] = {}
    total_rules: int | None = None

    try:
        index = load_index(paths.index_path)
        rules = index.get("rules", [])
        severity_counts = _count_by_severity(rules)
        total_rules = len(rules)
        exit_code, results_payload, stdout_lines, error_message, items_returned = _execute_command(index, args)
    except StandardsCliError as exc:
        exit_code = exc.exit_code
        error_message = exc.message
        logger.error(exc.message)

    summary_payload = {
        "exit_code": exit_code,
        "overall_status": _overall_status(exit_code),
        "items_returned": items_returned,
        "total_rules": total_rules,
        "severity_counts": severity_counts,
    }
    if error_message:
        summary_payload["error"] = error_message

    filters = _collect_filters(args)
    report_payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": timestamp_utc.isoformat(timespec="seconds"),
        "command": args.command,
        "filters": filters,
        "summary": summary_payload,
        "results": results_payload,
        "stdout": stdout_lines,
        "error": error_message,
        "paths": {
            "index_path": str(paths.index_path),
            "output_dir": str(paths.output_dir),
        },
        "options": {
            "artifacts_to_keep": options.artifacts_to_keep,
            "log_level": options.log_level,
        },
    }

    markdown_payload = _render_markdown_report(
        timestamp_utc=timestamp_utc,
        command=args.command,
        summary=summary_payload,
        filters=filters,
        stdout_lines=stdout_lines,
        error_message=error_message,
    )

    bundle_summary = {
        "command": args.command,
        "overall_status": summary_payload["overall_status"],
        "items_returned": items_returned,
        "exit_code": exit_code,
    }

    stdout_text = "".join(f"{line}\n" for line in stdout_lines) if stdout_lines else ""

    artifacts = [
        ReportArtifact("report.json", "latest_report.json", "json", report_payload),
        ReportArtifact("report.md", "latest_report.md", "text", markdown_payload),
        ReportArtifact("bundle_summary.json", "latest_bundle_summary.json", "json", bundle_summary),
        ReportArtifact("stdout.txt", "latest_stdout.txt", "text", stdout_text),
    ]

    write_result = write_report_artifacts(
        stem=RUN_STEM,
        timestamp=timestamp_utc,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    return {
        "exit_code": exit_code,
        "stdout_lines": stdout_lines,
        "summary": summary_payload,
        "results": results_payload,
        "error": error_message,
        "run_dir": str(write_result.run_dir),
        "report_json": str(write_result.artifacts["report.json"]),
        "bundle_summary": str(write_result.artifacts["bundle_summary.json"]),
        "report_md": str(write_result.artifacts["report.md"]),
    }


def main(argv: Sequence[str] | None = None) -> int:
    result = run(argv)
    for line in result.get("stdout_lines", []) or []:
        sys.stdout.write(f"{line}\n")
    return int(result.get("exit_code", 1))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
