#!/usr/bin/env python3
"""Generate a function coverage inventory from a coverage XML report.

The producer inspects a Coverage.py XML payload, correlates executed lines with
Python functions inside the repository, and emits structured artifacts under
`.repo_studios/reports/producer_reports/test_coverage_reports/<timestamp>/`:

- `report.json`: per-file function coverage metrics and uncovered function names.
- `report.md`: human-oriented summary highlighting modules with the weakest
  coverage.
- `report.csv`: spreadsheet-friendly table mirroring the JSON payload.
- `log.txt`: key/value digest suitable for automation hooks.

Artifacts are pruned to the configured retention window and mirrored into the
root directory via `latest_*` pointers for quick access.
"""

from __future__ import annotations

import argparse
import ast
import logging
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARIES_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:  # pragma: no cover - import is validated in tests via module load
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when executed directly
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

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/test_coverage_reports")
DEFAULT_COVERAGE_XML = Path(".repo_studios/reports/producer_reports/test_run_coverage/coverage.xml")
RUN_PREFIX = "test_coverage"
DEFAULT_ARTIFACTS_TO_KEEP = 10
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    coverage_xml: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "coverage_xml": PathSpec(
            field="coverage_xml",
            default=DEFAULT_COVERAGE_XML,
            ensure_dir=False,
        ),
        "output_dir": PathSpec(
            field="output_dir",
            default=DEFAULT_OUTPUT_DIR,
            ensure_dir=True,
        ),
    },
)

OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(
            field="artifacts_to_keep",
            minimum=1,
        )
    },
)


@dataclass(frozen=True)
class FunctionStat:
    name: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class FileCoverage:
    path: Path
    functions: list[FunctionStat]
    line_hits: dict[int, int]


def _current_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return _current_utc()
    parsed = datetime.fromisoformat(raw)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarise function-level test coverage from Coverage.py XML outputs.")
    parser.add_argument("--repo-root", help="Override repository root resolution")
    parser.add_argument(
        "--coverage-xml",
        help="Path to Coverage.py XML report",
        default=str(DEFAULT_COVERAGE_XML),
    )
    parser.add_argument(
        "--output-dir",
        help="Destination for timestamped artifacts",
        default=str(DEFAULT_OUTPUT_DIR),
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Historical runs to retain (minimum 1)",
    )
    parser.add_argument(
        "--timestamp",
        help="Override run timestamp (ISO 8601)",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        help="Minimum overall coverage percentage required (0-100)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Include files with zero functions in the final report",
    )
    return parser.parse_args(argv)


def _within_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.relative_to(repo_root)
    except ValueError:
        return False
    return True


def _resolve_filename(
    filename: str,
    *,
    repo_root: Path,
    sources: list[Path],
) -> Path:
    candidate = Path(filename)
    if candidate.is_absolute():
        return candidate.resolve()
    for source in sources:
        joined = (source / candidate).resolve()
        if joined.exists():
            return joined
    return (repo_root / candidate).resolve()


def _load_coverage_lines(
    coverage_xml: Path,
    *,
    repo_root: Path,
) -> dict[Path, dict[int, int]]:
    tree = ET.parse(coverage_xml)
    root = tree.getroot()
    sources = [
        Path(node.text or "").expanduser() for node in root.findall("./sources/source") if (node.text or "").strip()
    ]

    coverage: dict[Path, dict[int, int]] = {}
    for class_node in root.findall(".//class"):
        filename = class_node.get("filename")
        if not filename:
            continue
        resolved = _resolve_filename(filename, repo_root=repo_root, sources=sources)
        file_hits = coverage.setdefault(resolved, {})
        for line_node in class_node.findall("./lines/line"):
            number_raw = line_node.get("number")
            hits_raw = line_node.get("hits")
            if not number_raw:
                continue
            try:
                number = int(number_raw)
            except ValueError:
                continue
            try:
                hits = int(hits_raw) if hits_raw is not None else 0
            except ValueError:
                hits = 0
            file_hits[number] = max(file_hits.get(number, 0), hits)
    return coverage


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self._scopes: list[str] = []
        self.functions: list[FunctionStat] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._scopes.append(node.name)
        self.generic_visit(node)
        self._scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._add_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._add_function(node)
        self.generic_visit(node)

    def _add_function(self, node: ast.AST) -> None:
        name = getattr(node, "name", "<anonymous>")
        parts = [*self._scopes, str(name)]
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)
        if end < start:
            end = start
        self.functions.append(FunctionStat(name=".".join(parts), start_line=start, end_line=end))


def _collect_functions(path: Path) -> list[FunctionStat]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []
    collector = _FunctionCollector()
    collector.visit(tree)
    return collector.functions


def _is_function_covered(function: FunctionStat, hits: dict[int, int]) -> bool:
    for line in range(function.start_line, function.end_line + 1):
        if hits.get(line, 0) > 0:
            return True
    return False


def _round_pct(covered: int, total: int) -> float:
    if total == 0:
        return 0.0
    pct = (covered / total) * 100
    return round(pct, 2)


def _summarize_file(
    report: FileCoverage,
    *,
    repo_root: Path,
    include_empty: bool,
) -> dict[str, object] | None:
    functions = report.functions
    if not functions and not include_empty:
        return None
    total = len(functions)
    covered = 0
    uncovered: list[str] = []
    for function in functions:
        if _is_function_covered(function, report.line_hits):
            covered += 1
        else:
            uncovered.append(function.name)
    pct = _round_pct(covered, total)
    return {
        "absolute_path": report.path,
        "path": _relative_path(report.path, repo_root),
        "function_count": total,
        "functions_covered": covered,
        "coverage_pct": pct,
        "uncovered_functions": uncovered,
    }


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _build_payload(
    files: Iterable[dict[str, object]],
    *,
    repo_root: Path,
    coverage_source: Path,
    generated_at: datetime,
    include_empty: bool,
    min_coverage: float | None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    file_entries = [entry for entry in files if entry is not None]
    file_entries.sort(key=lambda item: (item["coverage_pct"], item["path"]))  # type: ignore[index]
    total_functions = sum(int(item["function_count"]) for item in file_entries)
    covered_functions = sum(int(item["functions_covered"]) for item in file_entries)
    overall_pct = _round_pct(covered_functions, total_functions)

    threshold = None if min_coverage is None else max(min(min_coverage, 100.0), 0.0)
    below_threshold = []
    for item in file_entries:
        if threshold is not None and item["coverage_pct"] < threshold:  # type: ignore[index]
            below_threshold.append(item)

    if total_functions == 0:
        status = "no_functions"
    elif threshold is not None and overall_pct < threshold:
        status = "threshold_failed"
    else:
        status = "ok"

    summary = {
        "status": status,
        "total_files": len(file_entries),
        "total_functions": total_functions,
        "covered_functions": covered_functions,
        "overall_coverage_pct": overall_pct,
        "files_below_threshold": [item["path"] for item in below_threshold],
        "threshold": threshold,
        "include_empty": include_empty,
    }

    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at.isoformat(),
        "coverage_source": _relative_path(coverage_source, repo_root),
        "repo_root": str(repo_root),
        "summary": summary,
        "files": [
            {
                "path": item["path"],
                "absolute_path": str(item.get("absolute_path", "")),
                "function_count": item["function_count"],
                "functions_covered": item["functions_covered"],
                "coverage_pct": item["coverage_pct"],
                "uncovered_functions": item["uncovered_functions"],
            }
            for item in file_entries
        ],
    }
    return payload, file_entries


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload.get("summary", {})
    files = payload.get("files", [])
    lines = [
        "# Test Coverage Inventory",
        "",
        f"- generated_utc: {payload.get('generated_utc', '')}",
        f"- coverage_source: {payload.get('coverage_source', '')}",
        f"- status: {summary.get('status', '')}",
        f"- total_files: {summary.get('total_files', 0)}",
        f"- total_functions: {summary.get('total_functions', 0)}",
        f"- covered_functions: {summary.get('covered_functions', 0)}",
        f"- overall_coverage_pct: {summary.get('overall_coverage_pct', 0.0)}",
        "",
        "## Files by Coverage",
        "",
    ]
    if not files:
        lines.append("(no functions detected)")
        lines.append("")
        return "\n".join(lines)

    lines.append("| File | Functions | Covered | Coverage % | Uncovered Functions |")
    lines.append("| --- | ---:| ---:| ---:| --- |")
    for entry in files:
        uncovered = entry.get("uncovered_functions", [])
        uncovered_display = ", ".join(uncovered) if uncovered else "(none)"
        lines.append(
            "| `{path}` | {total} | {covered} | {pct:.2f} | {uncovered} |".format(
                path=entry.get("path", ""),
                total=entry.get("function_count", 0),
                covered=entry.get("functions_covered", 0),
                pct=float(entry.get("coverage_pct", 0.0)),
                uncovered=uncovered_display,
            )
        )
    lines.append("")
    return "\n".join(lines)


def _render_csv(files: Iterable[dict[str, object]]) -> str:
    rows = ["path,function_count,functions_covered,coverage_pct,uncovered_functions"]
    for entry in files:
        uncovered = ";".join(entry.get("uncovered_functions", [])) if entry.get("uncovered_functions") else ""
        rows.append(
            "{path},{total},{covered},{pct:.2f},{uncovered}".format(
                path=entry.get("path", ""),
                total=entry.get("function_count", 0),
                covered=entry.get("functions_covered", 0),
                pct=float(entry.get("coverage_pct", 0.0)),
                uncovered=uncovered,
            )
        )
    return "\n".join(rows) + "\n"


def _render_log(payload: dict[str, object]) -> str:
    summary = payload.get("summary", {})
    parts = [
        f"status={summary.get('status', '')}",
        f"total_files={summary.get('total_files', 0)}",
        f"total_functions={summary.get('total_functions', 0)}",
        f"covered_functions={summary.get('covered_functions', 0)}",
        f"overall_coverage_pct={summary.get('overall_coverage_pct', 0.0):.2f}",
    ]
    threshold = summary.get("threshold")
    if threshold is not None:
        parts.append(f"threshold={float(threshold):.2f}")
    below = summary.get("files_below_threshold", [])
    if below:
        parts.append(f"files_below_threshold={len(below)}")
        preview = ",".join(str(item) for item in list(below)[:5])
        parts.append(f"below_preview={preview}")
    return "\n".join(parts) + "\n"


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )

    paths = build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))
    options = build_standard_options(args, OPTIONS_CONFIG)

    if args.min_coverage is not None and (args.min_coverage < 0 or args.min_coverage > 100):
        logging.error("--min-coverage must be between 0 and 100")
        return 2

    if not paths.coverage_xml.exists():
        logging.error("Coverage XML not found: %s", paths.coverage_xml)
        return 1

    coverage_map = _load_coverage_lines(paths.coverage_xml, repo_root=paths.repo_root)
    file_reports: list[FileCoverage] = []
    for file_path, line_hits in coverage_map.items():
        if not _within_repo(file_path, paths.repo_root):
            continue
        if not file_path.exists():
            continue
        functions = _collect_functions(file_path)
        file_reports.append(FileCoverage(path=file_path, functions=functions, line_hits=line_hits))

    if args.include_empty:
        # Include files that appear in coverage but have zero functions.
        for file_path, line_hits in coverage_map.items():
            if not _within_repo(file_path, paths.repo_root):
                continue
            if not file_path.exists():
                continue
            if any(report.path == file_path for report in file_reports):
                continue
            file_reports.append(FileCoverage(path=file_path, functions=[], line_hits=line_hits))

    generated_at = _parse_timestamp(args.timestamp)

    file_reports.sort(key=lambda report: str(report.path))

    file_entries = [
        _summarize_file(
            report,
            repo_root=paths.repo_root,
            include_empty=args.include_empty,
        )
        for report in file_reports
    ]

    payload, ordered_files = _build_payload(
        file_entries,
        repo_root=paths.repo_root,
        coverage_source=paths.coverage_xml,
        generated_at=generated_at,
        include_empty=args.include_empty,
        min_coverage=args.min_coverage,
    )

    artifacts = [
        ReportArtifact(
            filename="report.json",
            pointer="latest_report.json",
            kind="json",
            content=lambda: payload,
        ),
        ReportArtifact(
            filename="report.md",
            pointer="latest_report.md",
            kind="text",
            content=lambda: _render_markdown(payload),
        ),
        ReportArtifact(
            filename="report.csv",
            pointer="latest_report.csv",
            kind="text",
            content=lambda: _render_csv(payload["files"]),
        ),
        ReportArtifact(
            filename="log.txt",
            pointer="latest_report.log",
            kind="text",
            content=lambda: _render_log(payload),
        ),
    ]

    write_report_artifacts(
        stem=RUN_PREFIX,
        timestamp=generated_at,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    status = payload["summary"]["status"]  # type: ignore[index]
    logging.info(
        "coverage status=%s files=%d overall=%.2f",
        status,
        payload["summary"]["total_files"],  # type: ignore[index]
        payload["summary"]["overall_coverage_pct"],  # type: ignore[index]
    )
    if status == "threshold_failed":
        logging.error(
            "Coverage %.2f%% below threshold %.2f%%",
            payload["summary"]["overall_coverage_pct"],
            payload["summary"]["threshold"],
        )
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
