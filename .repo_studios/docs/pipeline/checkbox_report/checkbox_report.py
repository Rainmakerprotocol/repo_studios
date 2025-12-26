#!/usr/bin/env python3
"""Generate a repo-wide inventory of unchecked Markdown checkboxes.

This script scans Markdown files under ``.repo_studios/docs/pipeline``
(configurable via ``--search-dir``), collects the unchecked checklist
entries, and
emits two artifacts:

* ``checkbox_report.csv`` – machine-readable table (file, line number,
  heading hierarchy, text)
* ``checkbox_report.md`` – doc-index-friendly summary that explains the
  report and highlights notable outstanding work

Both artifacts live beneath ``docs/pipeline/checkbox_report/outputs`` by
default so humans and agents can easily find them.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import re
import sys
import textwrap
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

CHECKBOX_PATTERN = re.compile(r"^\s*(?:[-*+]|(?:\d+[.)]))\s+\[\s\]\s*(.*)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
SETEXT_PATTERN = re.compile(r"^[=-]{3,}\s*$")
CODE_FENCE_PATTERN = re.compile(r"^([`~]{3,})(.*)$")

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


ROOT = Path(__file__).resolve().parents[4]
LIBRARIES_ROOT = ROOT / ".repo_studios" / "command_center" / "scripts"
if str(LIBRARIES_ROOT) not in sys.path:
    sys.path.insert(0, str(LIBRARIES_ROOT))

from libraries.cli import resolve_repo_root  # noqa: E402

LINE_WIDTH = 100


def configure_logging(verbose: bool) -> None:
    """Initialize root logging once per process."""

    if logging.getLogger().handlers:
        return
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(message)s")


def format_relative(path: Path, base: Path) -> str:
    """Return path relative to base when possible for nicer display."""

    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()

@dataclass(frozen=True)
class CheckboxRecord:
    """Represents a single unchecked checklist entry."""

    relative_path: Path
    line_number: int
    heading_h1: str
    heading_h2: str
    heading_h3: str
    heading_h4: str
    text: str

    def to_csv_row(self) -> list[str]:
        return [
            self.relative_path.as_posix(),
            str(self.line_number),
            self.heading_h1,
            self.heading_h2,
            self.heading_h3,
            self.heading_h4,
            self.text,
        ]


@dataclass
class ParseState:
    headings: list[str] = field(default_factory=lambda: ["", "", "", ""])
    previous_line_for_setext: str | None = None
    in_front_matter: bool = False
    in_code_fence: bool = False
    current_fence: str | None = None


def _handle_front_matter(state: ParseState, stripped_line: str, lineno: int) -> bool:
    if lineno == 1 and stripped_line == "---":
        state.in_front_matter = True
        return True
    if state.in_front_matter:
        if stripped_line == "---":
            state.in_front_matter = False
        return True
    return False


def _toggle_code_fence(state: ParseState, stripped_line: str) -> bool:
    fence_match = CODE_FENCE_PATTERN.match(stripped_line)
    if not fence_match:
        return False
    fence, _ = fence_match.groups()
    if not state.in_code_fence:
        state.in_code_fence = True
        state.current_fence = fence
    elif fence == state.current_fence:
        state.in_code_fence = False
        state.current_fence = None
    return True


def _assign_heading(headings: list[str], level: int, title: str) -> None:
    headings[level - 1] = title.strip()
    for idx in range(level, len(headings)):
        headings[idx] = ""


def _apply_atx_heading(state: ParseState, line: str) -> bool:
    heading_match = HEADING_PATTERN.match(line)
    if not heading_match:
        return False
    hashes, title = heading_match.groups()
    _assign_heading(state.headings, min(len(hashes), 4), title)
    state.previous_line_for_setext = None
    return True


def _apply_setext_heading(state: ParseState, line: str) -> bool:
    if not state.previous_line_for_setext:
        return False
    if not SETEXT_PATTERN.match(line):
        return False
    setext_level = 1 if line.lstrip().startswith("=") else 2
    _assign_heading(state.headings, min(setext_level, 4), state.previous_line_for_setext)
    state.previous_line_for_setext = None
    return True


def _build_record(
    path: Path,
    repo_root: Path,
    lineno: int,
    checkbox_text: str,
    headings: list[str],
) -> CheckboxRecord:
    try:
        rel_path = path.relative_to(repo_root)
    except ValueError:
        rel_path = path.resolve()
    return CheckboxRecord(
        relative_path=rel_path,
        line_number=lineno,
        heading_h1=headings[0],
        heading_h2=headings[1],
        heading_h3=headings[2],
        heading_h4=headings[3],
        text=checkbox_text,
    )


def _should_skip_line(state: ParseState, line: str, stripped_line: str, lineno: int) -> bool:
    if _handle_front_matter(state, stripped_line, lineno):
        return True
    if _toggle_code_fence(state, stripped_line):
        return True
    if state.in_code_fence:
        return True
    if _apply_atx_heading(state, line):
        return True
    if _apply_setext_heading(state, line):
        return True
    return False

def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a CSV + Markdown report of unchecked Markdown checkboxes."
    )
    default_output_dir = Path(".repo_studios/docs/pipeline/checkbox_report/outputs")
    default_search_dir = Path(".repo_studios/docs/pipeline")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir,
        help="Directory to hold generated artifacts (default: %(default)s)",
    )
    parser.add_argument(
        "--csv-name",
        default="checkbox_report.csv",
        help="Name of the CSV artifact (default: %(default)s)",
    )
    parser.add_argument(
        "--markdown-name",
        default="checkbox_report.md",
        help="Name of the Markdown summary (default: %(default)s)",
    )
    parser.add_argument(
        "--search-dir",
        type=Path,
        default=default_search_dir,
        help="Directory to scan for Markdown files (default: %(default)s)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information while scanning files.",
    )
    return parser.parse_args(argv)

def discover_markdown_files(search_root: Path) -> list[Path]:
    """Return every Markdown file under the provided search root."""

    if not search_root.exists():
        return []
    files = sorted(search_root.rglob("*.md"))
    return [path for path in files if path.is_file()]
def scan_file(path: Path, repo_root: Path) -> list[CheckboxRecord]:
    """Scan a Markdown file for unchecked checkboxes."""

    records: list[CheckboxRecord] = []
    state = ParseState()

    with path.open("r", encoding="utf-8") as handle:
        for lineno, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if _should_skip_line(state, line, stripped, lineno):
                continue

            checkbox_match = CHECKBOX_PATTERN.match(line)
            if checkbox_match:
                text = checkbox_match.group(1).strip()
                records.append(
                    _build_record(
                        path=path,
                        repo_root=repo_root,
                        lineno=lineno,
                        checkbox_text=text,
                        headings=state.headings,
                    )
                )

            state.previous_line_for_setext = line if stripped else None

    return records

def gather_records(markdown_files: Iterable[Path], repo_root: Path, verbose: bool = False) -> list[CheckboxRecord]:
    records: list[CheckboxRecord] = []
    for path in markdown_files:
        file_records = scan_file(path, repo_root)
        if file_records:
            records.extend(file_records)
            if verbose:
                LOG.info("%s: %d unchecked", path.relative_to(repo_root), len(file_records))
    return sorted(records, key=lambda rec: (rec.relative_path.as_posix(), rec.line_number))


def write_csv(records: Sequence[CheckboxRecord], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "file_path",
                "line_number",
                "heading_h1",
                "heading_h2",
                "heading_h3",
                "heading_h4",
                "checkbox_text",
            ]
        )
        for record in records:
            writer.writerow(record.to_csv_row())

def summarize_counts(records: Sequence[CheckboxRecord]) -> dict[str, Counter]:
    per_file = Counter(record.relative_path.as_posix() for record in records)
    per_h1 = Counter(record.heading_h1 or "(no H1)" for record in records)
    return {"per_file": per_file, "per_h1": per_h1}


GOAL_LINES = [
    "Provide a single discoverable index of unchecked Markdown tasks across the repository.",
    "Help Copilot and contributors jump directly to unfinished work with heading context.",
    "Offer a CSV artifact for automation plus a Markdown digest the doc index can surface.",
]


SUMMARY_TEMPLATE = """---
title: Checkbox Report Summary
tier: tooling
audience:
    - Copilot
    - Repo_Studios
owners:
    - DocumentationOps
status: active
version: 1.0
updated_at: {today}
tags:
    - checkbox-report
    - repo-todo
related_files:
    - {script_rel}
    - {csv_rel}
    - {markdown_rel}
---

# Checkbox Report

## Goals

{goals_section}

## System Context

{system_context_section}

## Stage Narratives

Top files with the highest number of unfinished items:
{top_files_section}

### Sample Outstanding Tasks

{sample_section}

## Signals & Telemetry

{signals_section}

### Unchecked Tasks by H1

{headings_table_section}

## Maintenance Playbook

{maintenance_section}

## Update Log

* {today} — Report regenerated.
"""

def _format_bullet_line(text: str) -> str:
    return textwrap.fill(
        text,
        width=LINE_WIDTH,
        initial_indent="* ",
        subsequent_indent="  ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def _format_bullet_section(lines: Sequence[str]) -> str:
    return "\n".join(_format_bullet_line(line) for line in lines)


def _format_goals_section() -> str:
    return _format_bullet_section(GOAL_LINES)


def _format_system_context_section(
    search_rel: str,
    outputs_rel: str,
    csv_rel: str,
    markdown_rel: str,
) -> str:
    lines = [
        f"Source of truth: Markdown files beneath `{search_rel}`.",
        "Checklist scope: unchecked boxes only (`- [ ]`). Completed entries are omitted to keep the focus on pending work.",
        f"Generated artifacts live in `{outputs_rel}` for easy access.",
        f"CSV artifact: `{csv_rel}`.",
        f"Markdown (this file): `{markdown_rel}`.",
    ]
    return _format_bullet_section(lines)


def _format_top_files_section(top_files: Sequence[tuple[str, int]]) -> str:
    if not top_files:
        return _format_bullet_line("No unchecked items detected.")
    return "\n".join(
        _format_bullet_line(f"`{path}` — {count} unchecked") for path, count in top_files
    )


def _format_headings_table(top_h1: Sequence[tuple[str, int]]) -> str:
    lines = ["| H1 | Unchecked |", "| --- | --- |"]
    if top_h1:
        lines.extend(f"| {title} | {count} |" for title, count in top_h1)
    else:
        lines.append("| none | 0 |")
    return "\n".join(lines)


def _format_sample_section(records: Sequence[CheckboxRecord], limit: int = 10) -> str:
    sample_records = records[:limit]
    lines: list[str] = []
    for record in sample_records:
        headings = [
            record.heading_h1,
            record.heading_h2,
            record.heading_h3,
            record.heading_h4,
        ]
        heading_chain = " > ".join([h for h in headings if h]) or "(no heading context)"
        bullet_text = (
            f"`{record.relative_path.as_posix()}` L{record.line_number} — {heading_chain}: {record.text}"
        )
        lines.append(_format_bullet_line(bullet_text))
    if not lines:
        lines.append(_format_bullet_line("All checklists are currently complete."))
    return "\n".join(lines)


def _format_signals_section(total_records: int, file_count: int) -> str:
    lines = [
        f"Total unchecked tasks: {total_records}.",
        f"Files containing unchecked tasks: {file_count}.",
    ]
    return _format_bullet_section(lines)


def _format_instruction_section(
    script_rel: str,
    csv_rel: str,
    markdown_rel: str,
    search_rel: str,
) -> str:
    lines = [
        f"Run `python {script_rel} --verbose` after checklist edits under `{search_rel}`.",
        f"Commit `{csv_rel}` and `{markdown_rel}` together so doc-index consumers see the refresh.",
        "Use the CSV artifact as the source of truth for automation; this Markdown is optimized for doc-index discovery.",
    ]
    return _format_bullet_section(lines)

def render_markdown_summary(
    records: Sequence[CheckboxRecord],
    csv_path: Path,
    markdown_path: Path,
    repo_root: Path,
    script_path: Path,
    search_root: Path,
) -> str:
    csv_rel = format_relative(csv_path, repo_root)
    markdown_rel = format_relative(markdown_path, repo_root)
    script_rel = format_relative(script_path, repo_root)
    search_rel = format_relative(search_root, repo_root)
    outputs_rel = format_relative(csv_path.parent, repo_root)
    counts = summarize_counts(records)
    today = dt.date.today().isoformat()

    top_files = counts["per_file"].most_common(10)
    top_h1 = counts["per_h1"].most_common(10)
    total_records = len(records)
    file_count = len(counts["per_file"])

    context = {
        "csv_rel": csv_rel,
        "markdown_rel": markdown_rel,
        "script_rel": script_rel,
        "search_rel": search_rel,
        "today": today,
        "goals_section": _format_goals_section(),
        "system_context_section": _format_system_context_section(
            search_rel, outputs_rel, csv_rel, markdown_rel
        ),
        "top_files_section": _format_top_files_section(top_files),
        "sample_section": _format_sample_section(records),
        "headings_table_section": _format_headings_table(top_h1),
        "signals_section": _format_signals_section(total_records, file_count),
        "maintenance_section": _format_instruction_section(
            script_rel, csv_rel, markdown_rel, search_rel
        ),
        "total_records": total_records,
        "total_files": file_count,
    }
    return SUMMARY_TEMPLATE.format(**context)

def write_markdown_summary(content: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    configure_logging(verbose=args.verbose)
    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))
    raw_output_dir = args.output_dir
    output_dir = raw_output_dir.resolve() if raw_output_dir.is_absolute() else (repo_root / raw_output_dir).resolve()
    csv_path = (output_dir / args.csv_name).resolve()
    markdown_path = (output_dir / args.markdown_name).resolve()
    script_path = Path(__file__).resolve()
    allowed_root = (repo_root / ".repo_studios" / "docs" / "pipeline").resolve()
    raw_search_dir = args.search_dir
    if raw_search_dir.is_absolute():
        search_root = raw_search_dir.resolve()
    else:
        search_root = (repo_root / raw_search_dir).resolve()

    try:
        search_root.relative_to(allowed_root)
    except ValueError as exc:
        raise SystemExit(
            f"Search directory '{search_root}' must be within '{allowed_root}'."
        ) from exc
    if not search_root.exists():
        raise SystemExit(f"Search directory '{search_root}' does not exist.")

    markdown_files = discover_markdown_files(search_root)
    if args.verbose:
        LOG.info("Scanning %d Markdown files under %s ...", len(markdown_files), search_root)

    records = gather_records(markdown_files, repo_root, verbose=args.verbose)

    write_csv(records, csv_path)
    summary_content = render_markdown_summary(
        records,
        csv_path,
        markdown_path,
        repo_root,
        script_path,
        search_root,
    )
    write_markdown_summary(summary_content, markdown_path)

    if args.verbose:
        LOG.info("CSV written to %s", csv_path.relative_to(repo_root))
        LOG.info("Markdown summary written to %s", markdown_path.relative_to(repo_root))

if __name__ == "__main__":  # pragma: no cover
    main()
