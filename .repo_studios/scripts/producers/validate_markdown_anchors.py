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
    * JSON + markdown reports under `.repo_studios/reports/producer_reports/markdown_anchor_validation_reports/`
    * `latest_report.(json|md)` pointers for downstream agents
    * Timestamped run folders with automatic pruning (keep last 10 by default)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")  # capture link target

DEFAULT_OUTPUT_DIR = Path(
        ".repo_studios/reports/producer_reports/markdown_anchor_validation_reports"
)
RUN_PREFIX = "markdown_anchor_validation"


class Issue(NamedTuple):
    file: Path
    line: int
    kind: str
    target: str
    message: str


def _relativize(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:  # pragma: no cover - defensive
        return path.as_posix()


def build_report(
    *,
    root: Path,
    patterns: list[str],
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
        "patterns": patterns,
        "issue_count": len(issue_payload),
        "issues": issue_payload,
        "scanned_files": sorted(_relativize(path, root) for path in scanned_files),
    }


def write_artifacts(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.fromisoformat(report["generated_utc"])
    run_dir = output_dir / f"{RUN_PREFIX}-{ts.strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    json_path = run_dir / "report.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

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
    (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    latest_json = output_dir / "latest_report.json"
    latest_md = output_dir / "latest_report.md"
    for source, dest in [
        (json_path, latest_json),
        (run_dir / "report.md", latest_md),
    ]:
        try:
            if dest.exists():
                dest.unlink()
            dest.hardlink_to(source)
        except Exception:  # pragma: no cover - fallback copy path
            dest.write_bytes(source.read_bytes())

    return run_dir


def prune_old_runs(output_dir: Path, *, keep: int) -> list[Path]:
    keep = max(keep, 1)
    if not output_dir.exists():
        return []
    candidates = [
        path
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(f"{RUN_PREFIX}-")
    ]
    candidates.sort(key=lambda path: path.name, reverse=True)
    removed: list[Path] = []
    for stale in candidates[keep:]:
        shutil.rmtree(stale, ignore_errors=True)
        removed.append(stale)
    return removed


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


def check_file(path: Path, root: Path, anchors_cache: dict[Path, set[str]]) -> list[Issue]:
    issues: list[Issue] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_no, target in parse_links(text):
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
    return issues


def _parse_timestamp(raw: str | None) -> datetime:
    if raw is None:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - argparse already guards tests
        raise SystemExit(f"Invalid --timestamp value: {exc}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check markdown internal links & anchors")
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
        default=10,
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
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(levelname)s %(message)s")

    root = Path(args.root).resolve()
    output_dir = Path(args.output_dir).resolve()
    patterns = args.globs or [
        "README.md",
        "docs/agents/config_quickstart.md",
        "docs/agents/step5_agent_config_system.md",
    ]
    ts = _parse_timestamp(args.timestamp)

    anchors_cache: dict[Path, set[str]] = {}
    all_issues: list[Issue] = []
    scanned_files: list[Path] = []
    for md_file in iter_files(patterns, root):
        scanned_files.append(md_file)
        all_issues.extend(check_file(md_file, root, anchors_cache))

    report = build_report(
        root=root,
        patterns=patterns,
        issues=all_issues,
        scanned_files=scanned_files,
        ts=ts,
    )
    run_dir = write_artifacts(report, output_dir)
    pruned = prune_old_runs(output_dir, keep=args.artifacts_to_keep)
    if pruned:
        logging.info("Pruned %d old report folder(s)", len(pruned))

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
