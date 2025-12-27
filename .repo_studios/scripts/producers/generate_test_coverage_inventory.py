#!/usr/bin/env python3
"""Generate a function coverage inventory from a coverage XML report.

This producer ingests a Coverage.py XML payload, correlates executed lines with
Python functions inside the repository, and emits a positional-encoded bundle
under:

`<reports_root>/<viewer_slug>/<topic>/<YYYYMMDD-HHMM>/`

Artifacts:
- `manifest.json`: run metadata + inputs/provenance.
- `summary.md`: human-readable coverage summary.
- `telemetry.json`: extracted metrics + payload for downstream ingestion.

Legacy `latest_*` pointer outputs are not generated.
"""

from __future__ import annotations

import argparse
import ast
import logging
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from typing import Any, cast
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARIES_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"
REPO_STUDIOS_ROOT = REPO_ROOT / ".repo_studios"

try:  # pragma: no cover - import is validated in tests via module load
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.database_integration import create_storage
except ModuleNotFoundError:  # pragma: no cover - fallback when executed directly
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    if str(REPO_STUDIOS_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_STUDIOS_ROOT))
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.database_integration import create_storage

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/healthview")
DEFAULT_COVERAGE_XML = Path(".repo_studios/tests/fixtures/test_run_coverage/coverage.xml")
DEFAULT_ARTIFACTS_TO_KEEP = 5
SCHEMA_VERSION = 1
VIEWER_SLUG = "producer_reports"
TOPIC_SLUG = "test_coverage_inventory"


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    coverage_xml: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int


@dataclass(frozen=True)
class RefreshResult:
    exit_code: int
    suite_results: list[dict[str, Any]]


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


def _timestamp_slug(timestamp: datetime) -> str:
    return timestamp.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarise function-level test coverage from Coverage.py XML outputs.")
    parser.add_argument("--repo-root", help="Override repository root resolution")
    parser.add_argument(
        "--coverage-xml",
        help="Path to Coverage.py XML report",
        default=str(DEFAULT_COVERAGE_XML),
    )
    parser.add_argument(
        "--refresh-coverage-xml",
        action="store_true",
        help=(
            "Regenerate the coverage XML by running pytest with coverage before building the inventory report. "
            "This is intended for agent-friendly one-shot execution; it requires pytest-cov to be installed."
        ),
    )
    parser.add_argument(
        "--refresh-tests",
        nargs="*",
        default=[".repo_studios/tests"],
        help=(
            "Test paths passed to pytest when --refresh-coverage-xml is enabled. "
            "Defaults to .repo_studios/tests."
        ),
    )
    parser.add_argument(
        "--refresh-continue-on-error",
        action="store_true",
        help=(
            "When --refresh-coverage-xml is enabled, continue generating coverage even if pytest exits non-zero. "
            "This is useful when some suites are known to fail but we still want a repo-health coverage snapshot."
        ),
    )
    parser.add_argument(
        "--refresh-omit-tests",
        action="store_true",
        help=(
            "When --refresh-coverage-xml is enabled, omit */tests/* paths from coverage measurement. "
            "This does not change which tests are executed; it only changes what is counted in coverage."
        ),
    )
    parser.add_argument(
        "--refresh-cov-target",
        action="append",
        default=[],
        help=(
            "Coverage targets passed to pytest-cov via --cov=<target> when --refresh-coverage-xml is enabled. "
            "Repeat to specify multiple targets. Defaults to .repo_studios when omitted."
        ),
    )
    parser.add_argument(
        "--output-dir",
        help="Reports root for positional bundle outputs",
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
    parser.add_argument(
        "--refresh-pytest-args",
        nargs=argparse.REMAINDER,
        help=(
            "Additional args passed to pytest when --refresh-coverage-xml is enabled. "
            "This option must appear last on the command line."
        ),
    )
    return parser.parse_args(argv)


def _refresh_coverage_xml(
    *,
    repo_root: Path,
    coverage_xml: Path,
    tests: Sequence[str],
    cov_targets: Sequence[str],
    extra_pytest_args: Sequence[str] | None,
    omit_tests: bool,
) -> RefreshResult:
    coverage_xml.parent.mkdir(parents=True, exist_ok=True)

    resolved_cov_targets = list(cov_targets) if cov_targets else [".repo_studios"]

    cov_config_path: str | None = None
    if omit_tests:
        with NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".ini") as cov_config_file:
            cov_config_path = cov_config_file.name
            cov_config_file.write("[run]\n")
            cov_config_file.write("omit =\n")
            cov_config_file.write("    */tests/*\n")
            cov_config_file.flush()

    suite_results: list[dict[str, Any]] = []

    def _run_pytest_suite(*, suite: str, append: bool, coverage_file: Path) -> int:
        command = [sys.executable, "-m", "pytest", "-q", suite]
        command.extend([f"--cov={target}" for target in resolved_cov_targets])
        if cov_config_path:
            command.append(f"--cov-config={cov_config_path}")
        if append:
            command.append("--cov-append")
        # Disable pytest-cov report generation; we will render XML once at the end.
        command.append("--cov-report=")
        if extra_pytest_args:
            command.extend(list(extra_pytest_args))

        env = dict(os.environ)
        env["COVERAGE_FILE"] = str(coverage_file)

        logging.debug("coverage refresh suite=%s append=%s", suite, append)
        logging.debug("coverage refresh command=%s", " ".join(command))
        result = subprocess.run(command, cwd=str(repo_root), check=False, env=env)
        return int(result.returncode)

    def _render_final_xml(*, coverage_file: Path) -> None:
        try:
            from coverage import Coverage
            from coverage.exceptions import NoDataError
        except ModuleNotFoundError as exc:
            raise RuntimeError("coverage package is required to render combined coverage XML") from exc

        cov = Coverage(config_file=cov_config_path or False, data_file=str(coverage_file))
        cov.load()
        try:
            cov.xml_report(outfile=str(coverage_xml))
        except NoDataError:
            raise RuntimeError("No coverage data collected; cannot render coverage XML")

    overall_exit = 0
    try:
        logging.info("Refreshing coverage data via pytest-cov")
        logging.debug("coverage refresh cwd=%s", repo_root)

        # Run each supplied test entry as its own invocation so callers can pass a
        # mixture of directories and individual test modules.
        with TemporaryDirectory(prefix="repo_studios_cov_") as tmpdir:
            coverage_file = Path(tmpdir) / ".coverage"
            for index, suite in enumerate(tests):
                exit_code = _run_pytest_suite(suite=str(suite), append=index > 0, coverage_file=coverage_file)
                suite_results.append({"suite": str(suite), "exit_code": exit_code})
                if exit_code != 0:
                    overall_exit = exit_code

            # Always attempt to render a final XML from whatever coverage data was collected.
            _render_final_xml(coverage_file=coverage_file)

        return RefreshResult(exit_code=overall_exit, suite_results=suite_results)
    finally:
        if cov_config_path:
            try:
                Path(cov_config_path).unlink(missing_ok=True)
            except OSError:
                pass


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
) -> dict[str, Any] | None:
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
    files: Iterable[dict[str, Any] | None],
    *,
    repo_root: Path,
    coverage_source: Path,
    generated_at: datetime,
    include_empty: bool,
    min_coverage: float | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    file_entries: list[dict[str, Any]] = [entry for entry in files if entry is not None]
    file_entries.sort(key=lambda item: (float(item.get("coverage_pct", 0.0)), str(item.get("path", ""))))
    total_functions = sum(int(item.get("function_count", 0) or 0) for item in file_entries)
    covered_functions = sum(int(item.get("functions_covered", 0) or 0) for item in file_entries)
    overall_pct = _round_pct(covered_functions, total_functions)

    threshold = None if min_coverage is None else max(min(min_coverage, 100.0), 0.0)
    below_threshold = []
    for item in file_entries:
        if threshold is not None and float(item.get("coverage_pct", 0.0) or 0.0) < threshold:
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

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at.isoformat(),
        "coverage_source": _relative_path(coverage_source, repo_root),
        "repo_root": str(repo_root),
        "summary": summary,
        "files": [
            {
                "path": item.get("path", ""),
                "absolute_path": str(item.get("absolute_path", "")),
                "function_count": int(item.get("function_count", 0) or 0),
                "functions_covered": int(item.get("functions_covered", 0) or 0),
                "coverage_pct": float(item.get("coverage_pct", 0.0) or 0.0),
                "uncovered_functions": list(item.get("uncovered_functions", []) or []),
            }
            for item in file_entries
        ],
    }
    return payload, file_entries


def _render_summary_markdown(*, timestamp_slug: str, payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary", {}), dict) else {}
    files = payload.get("files", []) if isinstance(payload.get("files", []), list) else []
    lines: list[str] = [
        "# Test Coverage Inventory",
        "",
        f"- run_timestamp: {timestamp_slug}",
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
    for entry in (item for item in files if isinstance(item, dict)):
        uncovered = entry.get("uncovered_functions", [])
        uncovered_values = uncovered if isinstance(uncovered, list) else []
        uncovered_display = ", ".join(str(value) for value in uncovered_values) if uncovered_values else "(none)"
        lines.append(
            "| `{path}` | {total} | {covered} | {pct:.2f} | {uncovered} |".format(
                path=entry.get("path", ""),
                total=entry.get("function_count", 0),
                covered=entry.get("functions_covered", 0),
                pct=float(entry.get("coverage_pct", 0.0) or 0.0),
                uncovered=uncovered_display,
            )
        )
    lines.append("")
    return "\n".join(lines)


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

    refresh_exit_code: int | None = None
    refresh_suite_results: list[dict[str, Any]] | None = None
    if args.refresh_coverage_xml:
        fixtures_root = paths.repo_root / ".repo_studios" / "tests" / "fixtures"
        if _within_repo(paths.coverage_xml, paths.repo_root) and fixtures_root in paths.coverage_xml.parents:
            logging.warning(
                "Refreshing coverage XML will overwrite fixture data: %s",
                _relative_path(paths.coverage_xml, paths.repo_root),
            )
        refresh_result = _refresh_coverage_xml(
            repo_root=paths.repo_root,
            coverage_xml=paths.coverage_xml,
            tests=cast(list[str], args.refresh_tests),
            cov_targets=cast(list[str], args.refresh_cov_target),
            extra_pytest_args=cast(list[str] | None, args.refresh_pytest_args),
            omit_tests=bool(args.refresh_omit_tests),
        )
        refresh_exit_code = refresh_result.exit_code
        refresh_suite_results = refresh_result.suite_results
        if refresh_exit_code != 0:
            if bool(getattr(args, "refresh_continue_on_error", False)):
                logging.warning("Coverage refresh had failures (exit=%s); continuing", refresh_exit_code)
            else:
                logging.error("Coverage refresh failed (exit=%s)", refresh_exit_code)
                return refresh_exit_code

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

    timestamp_slug = _timestamp_slug(generated_at)
    now_iso = _current_utc().isoformat()

    summary = payload.get("summary", {})
    status = str(summary.get("status", "error"))

    output_dir = paths.output_dir
    storage = create_storage(output_dir, VIEWER_SLUG, TOPIC_SLUG, timestamp=timestamp_slug)
    bundle_dir = output_dir / VIEWER_SLUG / TOPIC_SLUG / timestamp_slug

    manifest_path = bundle_dir / "manifest.json"
    summary_path = bundle_dir / "summary.md"
    telemetry_path = bundle_dir / "telemetry.json"

    files_below_threshold = summary.get("files_below_threshold", [])
    below_count = len(files_below_threshold) if isinstance(files_below_threshold, list) else 0

    coverage_values = [float(item.get("coverage_pct", 0.0)) for item in ordered_files]
    min_file_coverage = min(coverage_values) if coverage_values else 0.0

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp_slug,
        "generated_at": now_iso,
        "status": status,
        "git_sha": None,
        "repo_root": str(paths.repo_root),
        "inputs": {
            "coverage_xml": _relative_path(paths.coverage_xml, paths.repo_root),
            "output_dir": _relative_path(output_dir, paths.repo_root),
            "min_coverage": summary.get("threshold"),
            "include_empty": bool(summary.get("include_empty", False)),
            "artifacts_to_keep": max(1, options.artifacts_to_keep),
            "timestamp": generated_at.isoformat(),
            "refresh_coverage_xml": bool(args.refresh_coverage_xml),
            "refresh_tests": cast(list[str], args.refresh_tests),
            "refresh_continue_on_error": bool(getattr(args, "refresh_continue_on_error", False)),
            "refresh_omit_tests": bool(getattr(args, "refresh_omit_tests", False)),
            "refresh_cov_target": cast(list[str], args.refresh_cov_target),
            "refresh_pytest_args": cast(list[str] | None, args.refresh_pytest_args),
            "refresh_exit_code": refresh_exit_code,
            "refresh_suite_results": refresh_suite_results,
        },
        "catalog": [
            {"artifact": "manifest.json", "path": _relative_path(manifest_path, paths.repo_root)},
            {"artifact": "summary.md", "path": _relative_path(summary_path, paths.repo_root)},
            {"artifact": "telemetry.json", "path": _relative_path(telemetry_path, paths.repo_root)},
        ],
        "provenance": {
            "script": "generate_test_coverage_inventory.py",
            "trigger": "cli",
        },
    }

    telemetry: dict[str, Any] = {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp_slug,
        "generated_at": now_iso,
        "status": status,
        "metrics": {
            "total_files": int(summary.get("total_files", 0) or 0),
            "total_functions": int(summary.get("total_functions", 0) or 0),
            "covered_functions": int(summary.get("covered_functions", 0) or 0),
            "overall_coverage_pct": float(summary.get("overall_coverage_pct", 0.0) or 0.0),
            "threshold": summary.get("threshold"),
            "files_below_threshold_count": below_count,
            "min_file_coverage_pct": float(min_file_coverage),
        },
        "inputs": {
            "coverage_source": _relative_path(paths.coverage_xml, paths.repo_root),
            "include_empty": bool(summary.get("include_empty", False)),
            "min_coverage": summary.get("threshold"),
        },
        "payload": payload,
    }

    summary_markdown = _render_summary_markdown(timestamp_slug=timestamp_slug, payload=payload)

    # DB_INTEGRATION_MARKER: Persist manifest bundle (report_runs + report_artifacts)
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: Persist human-readable report summary (report_artifacts)
    storage.write_summary({"markdown": summary_markdown}, format="md")
    # DB_INTEGRATION_MARKER: Persist telemetry payload + extracted metrics (report_artifacts + test_metrics)
    storage.write_telemetry(telemetry)

    base_dir = output_dir / VIEWER_SLUG / TOPIC_SLUG
    prune_run_directories(
        base_dir,
        keep=max(1, options.artifacts_to_keep),
        current_run=bundle_dir,
        logger=logging.getLogger(__name__),
    )

    logging.info(
        "coverage status=%s files=%d overall=%.2f",
        status,
        telemetry["metrics"]["total_files"],
        telemetry["metrics"]["overall_coverage_pct"],
    )

    if status == "threshold_failed":
        logging.error(
            "Coverage %.2f%% below threshold %.2f%%",
            telemetry["metrics"]["overall_coverage_pct"],
            float(telemetry["metrics"].get("threshold") or 0.0),
        )
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
