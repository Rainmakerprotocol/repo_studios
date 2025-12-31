#!/usr/bin/env python
"""Markdown Anchor & Link Checker

Scans selected markdown files for:
  * Internal document anchors: [text](#anchor)
  * Cross-file relative links: [text](path/to/file.md#optional-anchor)

Validates that:
  * Target files exist
  * Target anchors exist (heading-derived slug)

Slug generation follows GitHub-style simplification (lowercase, spaces -> dashes,
strip non-alphanumeric except dashes) and collapses consecutive dashes.

Exit codes:
  0 - success, no issues
  1 - issues found (printed)

Usage:
  python scripts/check_markdown_anchors.py [--root .] [--glob docs/**/*.md]

Defaults choose a curated file set (README + docs/agents/*quickstart* + step5 plan).

Artifacts:
        * Canonical bundle artifacts under
            `.repo_studios/reports/producer_reports/healthview/markdown_anchor_validation/<YYYYMMDD-HHMM>/`
        * Files: `manifest.json`, `summary.md`, `telemetry.json`
        * Timestamped run folders with automatic pruning (keep last 10 by default)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple, cast

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback during standalone execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep

try:
    from libraries.database_integration import create_storage
except ModuleNotFoundError:  # pragma: no cover - fallback during standalone execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries.database_integration import create_storage

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")  # capture link target

TOPIC_SLUG = "markdown_anchor_validation"
DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("validate_markdown_anchors")
DEFAULT_PATTERNS = [
    "docs/**/*.md",
    ".repo_studios/docs/**/*.md",
]


class Issue(NamedTuple):
    file: Path
    line: int
    kind: str
    target: str
    message: str


class Paths(NamedTuple):
    repo_root: Path
    scan_root: Path
    output_dir: Path


class Options(NamedTuple):
    artifacts_to_keep: int
    patterns: tuple[str, ...] = ()
    timestamp: str | None = None
    log_level: str = "INFO"


PATH_SPECS: dict[str, PathSpec] = {
    "scan_root": PathSpec(field="root", default=Path("."), within_repo=False),
    "output_dir": PathSpec(
        field="output_dir",
        default=DEFAULT_OUTPUT_DIR,
        ensure_dir=True,
        within_repo=False,
    ),
}


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs=PATH_SPECS,
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
    },
)


def _relativize(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:  # pragma: no cover - defensive
        return path.as_posix()


def build_report(
    *,
    root: Path,
    patterns: Iterable[str],
    issues: list[Issue],
    scanned_files: list[Path],
    ts: datetime,
) -> dict:
    issue_payload = [
        {
            "file": _relativize(issue.file, root),
            "line": issue.line,
            "kind": issue.kind,
            "target": issue.target,
            "message": issue.message,
        }
        for issue in issues
    ]
    return {
        "schema_version": 1,
        "generated_utc": ts.isoformat(),
        "status": "fail" if issue_payload else "ok",
        "root": str(root),
        "patterns": list(patterns),
        "issue_count": len(issue_payload),
        "issues": issue_payload,
        "scanned_files": sorted(_relativize(path, root) for path in scanned_files),
    }


def _format_run_slug(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")


def _parse_timestamp(raw: str | None) -> datetime:
    if raw is None:
        return datetime.now(timezone.utc)

    if re.fullmatch(r"\d{8}-\d{4}", raw):
        return datetime.strptime(raw, "%Y%m%d-%H%M").replace(tzinfo=timezone.utc)

    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - argparse already guards tests
        raise SystemExit(f"Invalid --timestamp value: {exc}")

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def compose_manifest(*, report: dict, run_timestamp: str, inputs: dict) -> dict:
    status = report.get("status", "ok")
    return {
        "schema_version": 1,
        "viewer_slug": "producer_reports",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_timestamp,
        "generated_utc": report.get("generated_utc"),
        "status": "fail" if status == "fail" else "ok",
        "inputs": inputs,
        "summary": {
            "files_scanned": len(report.get("scanned_files", [])),
            "issue_count": report.get("issue_count", 0),
        },
        "catalog": ["scripts.utilities.check_markdown_anchors"],
        "provenance": {
            "requested_by": "cli",
            "trigger_type": "manual",
        },
    }


def compose_telemetry(*, report: dict, links_checked: int) -> dict:
    issues = report.get("issues", [])
    missing_file_count = sum(1 for issue in issues if issue.get("kind") == "file")
    missing_anchor_count = sum(1 for issue in issues if issue.get("kind") == "anchor")
    return {
        "schema_version": 1,
        "generated_utc": report.get("generated_utc"),
        "status": report.get("status"),
        "metrics": {
            "files_scanned": len(report.get("scanned_files", [])),
            "links_checked": links_checked,
            "issue_count": report.get("issue_count", 0),
            "missing_file_count": missing_file_count,
            "missing_anchor_count": missing_anchor_count,
        },
        "payload": {
            "report": report,
        },
    }


def render_summary_markdown(*, report: dict) -> str:
    lines = [
        "# Markdown Anchor Validation Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Root: {report['root']}",
        "Patterns: " + (", ".join(report["patterns"]) or "<none>"),
        f"Issue Count: {report['issue_count']}",
    ]
    if report["issues"]:
        lines.append("")
        lines.append("## Issues")
        lines.append("")
        for issue in report["issues"]:
            lines.append(
                f"- `{issue['file']}`:{issue['line']} [{issue['kind']}] {issue['target']} — {issue['message']}"
            )
    else:
        lines.append("")
        lines.append("All checks passed without anchor or link errors.")
    return "\n".join(lines) + "\n"


def slugify(raw: str) -> str:
    s = raw.strip().lower()
    # remove code spans/backticks
    s = re.sub(r"`+", "", s)
    # remove anything not alphanumeric/space/-
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def collect_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        anchors.add(slugify(m.group(2)))
    return anchors


def iter_files(patterns: Iterable[str], root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for pat in patterns:
        for path in root.glob(pat):
            if path.is_file() and path.suffix == ".md" and path not in seen:
                seen.add(path)
                yield path


def parse_links(text: str) -> Iterable[tuple[int, str]]:
    for idx, line in enumerate(text.splitlines(), start=1):
        for m in LINK_RE.finditer(line):
            yield idx, m.group(1)


def check_file(path: Path, root: Path, anchors_cache: dict[Path, set[str]]) -> tuple[list[Issue], int]:
    issues: list[Issue] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    links_checked = 0
    for line_no, target in parse_links(text):
        links_checked += 1
        if target.startswith(("http://", "https://", "mailto:")):
            continue  # external
        if target.startswith("#"):
            # intra-file anchor
            anchor = target[1:]
            anchor_slug = slugify(anchor)
            anchors = anchors_cache.setdefault(path, collect_anchors(text))
            if anchor_slug not in anchors:
                issues.append(
                    Issue(
                        path,
                        line_no,
                        "anchor",
                        target,
                        f"Missing anchor slug '{anchor_slug}' in same file",
                    )
                )
            continue
        # file or file#anchor
        file_part, _, anchor_part = target.partition("#")
        # normalize relative path
        target_path = (path.parent / file_part).resolve()
        try:
            target_path.relative_to(root.resolve())
        except ValueError:
            # outside root; skip for safety
            continue
        if not target_path.exists():
            issues.append(Issue(path, line_no, "file", target, "Target file does not exist"))
            continue
        if anchor_part:
            tgt_text = target_path.read_text(encoding="utf-8", errors="replace")
            anchors = anchors_cache.setdefault(target_path, collect_anchors(tgt_text))
            slug = slugify(anchor_part)
            if slug not in anchors:
                issues.append(
                    Issue(
                        path,
                        line_no,
                        "anchor",
                        target,
                        f"Missing anchor slug '{slug}' in target file",
                    )
                )
    return issues, links_checked


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    patterns = list(args.globs) if args.globs else list(DEFAULT_PATTERNS)
    base_options = build_standard_options(args, OPTIONS_CONFIG)
    return Options(
        artifacts_to_keep=base_options.artifacts_to_keep,
        patterns=tuple(patterns),
        timestamp=getattr(args, "timestamp", None),
        log_level=str(getattr(args, "log_level", "INFO")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check markdown internal links & anchors")
    parser.add_argument("--repo-root", help="Repository root (defaults to project root)")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--glob",
        action="append",
        help="Glob pattern (repeatable)",
        dest="globs",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Destination for report artifacts",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical artifact folders to retain (min 1)",
    )
    parser.add_argument(
        "--timestamp",
        help="Override run timestamp (ISO 8601). Primarily for tests.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )

    args = parser.parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)

    logging.basicConfig(level=getattr(logging, options.log_level.upper()), format="%(levelname)s %(message)s")
    logger = logging.getLogger(__name__)

    root = paths.scan_root
    output_dir = paths.output_dir
    patterns = options.patterns
    ts = _parse_timestamp(options.timestamp)
    run_timestamp = _format_run_slug(ts)

    anchors_cache: dict[Path, set[str]] = {}
    all_issues: list[Issue] = []
    scanned_files: list[Path] = []
    links_checked_total = 0
    for md_file in iter_files(patterns, root):
        scanned_files.append(md_file)
        issues, links_checked = check_file(md_file, root, anchors_cache)
        all_issues.extend(issues)
        links_checked_total += links_checked

    report = build_report(
        root=root,
        patterns=patterns,
        issues=all_issues,
        scanned_files=scanned_files,
        ts=ts,
    )
    # output_dir already contains full topic path - pass empty viewer/topic
    storage = create_storage(output_dir, "", "", timestamp=run_timestamp)

    inputs = {
        "root": str(root),
        "patterns": list(patterns),
        "artifacts_to_keep": options.artifacts_to_keep,
    }
    manifest = compose_manifest(report=report, run_timestamp=run_timestamp, inputs=inputs)
    telemetry = compose_telemetry(report=report, links_checked=links_checked_total)
    summary_md = render_summary_markdown(report=report)

    # DB_INTEGRATION_MARKER: markdown anchor validation manifest
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: markdown anchor validation summary markdown
    storage.write_summary({"markdown": summary_md}, format="markdown")
    # DB_INTEGRATION_MARKER: markdown anchor validation telemetry
    storage.write_telemetry(telemetry)

    # output_dir already contains full topic path
    run_dir = output_dir / run_timestamp
    prune_result = prune_run_directories(
        output_dir,
        keep=options.artifacts_to_keep,
        current_run=run_dir,
        logger=logger,
    )
    if prune_result.removed:
        logger.info("Pruned %d old report folder(s)", len(prune_result.removed))

    if all_issues:
        logging.error("Markdown anchor/link issues detected (%d)", len(all_issues))
        for issue in all_issues:
            logging.error(
                "%s:%d: [%s] %s -> %s",
                _relativize(issue.file, root),
                issue.line,
                issue.kind,
                issue.target,
                issue.message,
            )
        logging.error("Artifacts written to %s", run_dir)
        return 1

    if scanned_files:
        rel_files = ", ".join(sorted(_relativize(path, root) for path in scanned_files))
        logging.info("All checked markdown anchors OK (files: %s)", rel_files)
    else:  # pragma: no cover - internal guardrail
        logging.info("No markdown files matched the provided patterns")
    logging.info("Artifacts written to %s", run_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
