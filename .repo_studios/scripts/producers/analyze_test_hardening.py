#!/usr/bin/env python3
"""Structured test hardening analyzer producer."""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import logging
import re
import sys
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, List, Sequence, cast

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback when package path isn't configured
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep

try:  # pragma: no cover - prefer import when packaged
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories
except ModuleNotFoundError:  # pragma: no cover - fallback when running in isolation
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories

TOPIC_SLUG = "test_hardening"
DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("analyze_test_hardening")
SCHEMA_VERSION = 1
TEST_PATTERNS = ("test_*.py", "*_test.py", "test*.py")
IGNORED_PARTS = {".git", ".repo_studios", ".venv", "__pycache__"}


@dataclass(frozen=True)
class Paths:
    """Path configuration for test hardening analysis.

    Attributes:
        repo_root: Repository root directory.
        output_dir: Output directory for generated report bundles.
    """

    repo_root: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    """Runtime options for test hardening analysis.

    Attributes:
        artifacts_to_keep: Number of historical run directories to retain.
        log_level: Logging verbosity level.
    """

    artifacts_to_keep: int
    log_level: str = "INFO"


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(
            field="output_dir",
            default=DEFAULT_OUTPUT_DIR,
            ensure_dir=True,
            within_repo=True,
        ),
    },
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
    },
)


@dataclass
class TestIssue:
    """A single issue detected in a test file.

    Attributes:
        severity: Issue severity level (high, medium, low).
        category: Issue category (e.g., missing_mocks, long_test, no_assertions).
        message: Human-readable description of the issue.
        line_number: Source line where the issue was detected, if applicable.
    """

    severity: str
    category: str
    message: str
    line_number: int | None = None


@dataclass
class TestFileAnalysis:
    """Analysis results for a single test file.

    Attributes:
        filepath: Path to the analyzed test file.
        total_lines: Total line count of the file.
        test_count: Number of test functions detected.
        issues: List of issues found during analysis.
        long_tests: Details of tests exceeding length thresholds.
        imports: Set of imported module names.
    """

    filepath: Path
    total_lines: int = 0
    test_count: int = 0
    issues: List[TestIssue] = field(default_factory=list)
    long_tests: List[dict[str, int | str]] = field(default_factory=list)
    imports: set[str] = field(default_factory=set)

    @property
    def severity_counts(self) -> dict[str, int]:
        """Return counts of issues by severity level.

        Returns:
            Dictionary with high, medium, and low severity counts.
        """
        return {
            "high": sum(1 for issue in self.issues if issue.severity == "high"),
            "medium": sum(1 for issue in self.issues if issue.severity == "medium"),
            "low": sum(1 for issue in self.issues if issue.severity == "low"),
        }

    @property
    def priority_score(self) -> int:
        """Calculate a weighted priority score based on issue severities.

        Returns:
            Score weighted as: high*10 + medium*3 + low*1.
        """
        counts = self.severity_counts
        return counts["high"] * 10 + counts["medium"] * 3 + counts["low"]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for test hardening analysis.

    Args:
        argv: Command-line arguments. Uses sys.argv if None.

    Returns:
        Parsed argument namespace with all CLI options.
    """
    parser = argparse.ArgumentParser(
        prog="analyze_test_hardening",
        description=__doc__ or "",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for structured artifacts",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical run directories to retain",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--timestamp",
        help="Override run timestamp (ISO 8601) for deterministic runs",
    )
    parser.add_argument(
        "--tests-dir",
        action="append",
        default=[],
        help=(
            "Explicit test directory to scan (bypasses IGNORED_PARTS for that subtree). "
            "Repeat to specify multiple directories. When omitted, discovers tests from repo root "
            "excluding .repo_studios/, .venv/, .git/, __pycache__/."
        ),
    )
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    """Build path configuration from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Paths configuration dataclass.
    """
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    """Build runtime options from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Options configuration dataclass.
    """
    options = cast(Options, build_standard_options(args, OPTIONS_CONFIG))
    return replace(options, log_level=str(args.log_level))


def configure_logging(level: str) -> None:
    """Configure logging with the specified verbosity level.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def _timestamp_slug(moment: dt.datetime) -> str:
    """Convert a datetime to a YYYYMMDD-HHMM format slug.

    Args:
        moment: Datetime to convert (will be normalized to UTC).

    Returns:
        Timestamp string in YYYYMMDD-HHMM format.
    """
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=dt.timezone.utc)
    return moment.astimezone(dt.timezone.utc).strftime("%Y%m%d-%H%M")


def _resolve_timestamp(raw: str | None) -> dt.datetime:
    """Resolve or generate a UTC timestamp for the run.

    Args:
        raw: ISO 8601 timestamp string, or None for current time.

    Returns:
        Datetime object normalized to UTC.

    Raises:
        RuntimeError: If the timestamp string is invalid.
    """
    if not raw:
        return dt.datetime.now(dt.timezone.utc)
    try:
        moment = dt.datetime.fromisoformat(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid --timestamp value: {exc}") from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=dt.timezone.utc)
    return moment.astimezone(dt.timezone.utc)


def _detect_trigger_type() -> str:
    """Detect the execution trigger type from environment.

    Returns:
        One of 'make', 'ci', or 'cli' based on environment variables.
    """
    import os

    if os.getenv("MAKELEVEL"):
        return "make"
    if os.getenv("GITHUB_ACTIONS"):
        return "ci"
    return "cli"


def _detect_requested_by() -> str | None:
    """Detect the user or actor who triggered the run.

    Returns:
        Username from GITHUB_ACTOR, USERNAME, or USER environment variables.
    """
    import os

    return os.getenv("GITHUB_ACTOR") or os.getenv("USERNAME") or os.getenv("USER")


def _detect_git_sha(repo_root: Path) -> str | None:
    """Detect the current git commit SHA.

    Args:
        repo_root: Repository root directory.

    Returns:
        Git SHA string, or None if not in a git repository.
    """
    import os
    import subprocess

    env_sha = os.getenv("GITHUB_SHA")
    if env_sha:
        return env_sha
    if not (repo_root / ".git").exists():
        return None
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:  # pragma: no cover - best effort
        return None
    value = value.strip()
    return value or None


def discover_test_files(repo_root: Path, tests_dirs: list[Path] | None = None) -> list[Path]:
    """Discover test files in the repository.

    Searches for files matching test patterns (test_*.py, *_test.py).
    When explicit directories are provided, only those are scanned.
    Otherwise, scans from repo root excluding standard ignored paths.

    Args:
        repo_root: Repository root directory.
        tests_dirs: Explicit test directories to scan, or None for auto-discovery.

    Returns:
        Sorted list of discovered test file paths.
    """
    results: set[Path] = set()

    # If explicit test directories are provided, scan them without IGNORED_PARTS filtering
    if tests_dirs:
        for tests_dir in tests_dirs:
            if not tests_dir.is_absolute():
                tests_dir = repo_root / tests_dir
            if not tests_dir.exists():
                logging.warning("Tests directory not found: %s", tests_dir)
                continue
            for pattern in TEST_PATTERNS:
                for candidate in tests_dir.rglob(pattern):
                    if not candidate.is_file():
                        continue
                    # Only filter __pycache__ when using explicit dirs
                    rel_parts = set(candidate.relative_to(repo_root).parts) if candidate.is_relative_to(repo_root) else set()
                    if "__pycache__" in rel_parts:
                        continue
                    results.add(candidate)
        return sorted(results)

    # Default: discover from repo root with full IGNORED_PARTS filtering
    for pattern in TEST_PATTERNS:
        for candidate in repo_root.rglob(pattern):
            if not candidate.is_file():
                continue
            rel_parts = set(candidate.relative_to(repo_root).parts)
            if rel_parts & IGNORED_PARTS:
                continue
            results.add(candidate)
    return sorted(results)


def analyze_file(path: Path, repo_root: Path) -> TestFileAnalysis:
    """Analyze a single test file for hardening issues.

    Parses the file, extracts imports, and checks for common test quality
    issues like missing mocks, long tests, and lack of assertions.

    Args:
        path: Path to the test file.
        repo_root: Repository root for relative path computation.

    Returns:
        Analysis results containing detected issues.
    """
    analysis = TestFileAnalysis(filepath=path)
    try:
        content = path.read_text(encoding="utf-8")
        analysis.total_lines = len(content.splitlines())
        tree = ast.parse(content, filename=str(path))
        _check_imports(tree, analysis)
        _check_test_functions(tree, analysis, content)
        _check_content_patterns(content, analysis)
    except Exception as exc:  # pragma: no cover - defensive guard
        logging.exception("Failed to analyze %s", path)
        rel = path.relative_to(repo_root) if path.is_relative_to(repo_root) else path
        analysis.issues.append(
            TestIssue(
                severity="high",
                category="parse_error",
                message=f"Failed to parse {rel}: {exc}",
            )
        )
    return analysis


def _check_imports(tree: ast.AST, analysis: TestFileAnalysis) -> None:
    """Check imports for risky external dependencies without mocks.

    Args:
        tree: Parsed AST of the test file.
        analysis: Analysis object to update with findings.
    """
    has_mock = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                analysis.imports.add(alias.name)
                if "pytest" in alias.name:
                    has_mock = has_mock or "pytest" in alias.name
                if "mock" in alias.name or "unittest.mock" in alias.name:
                    has_mock = True
        elif isinstance(node, ast.ImportFrom) and node.module:
            analysis.imports.add(node.module)
            if "mock" in node.module:
                has_mock = True
    risky_imports = {
        "requests",
        "urllib",
        "http.client",
        "httpx",
        "sqlite3",
        "psycopg2",
        "pymongo",
        "sqlalchemy",
        "boto3",
        "google.cloud",
        "azure",
        "smtplib",
        "email",
    }
    found = analysis.imports & risky_imports
    if found and not has_mock:
        analysis.issues.append(
            TestIssue(
                severity="high",
                category="missing_mocks",
                message=f"External dependencies detected ({', '.join(sorted(found))}) but no mock library imported.",
            )
        )


def _check_test_functions(tree: ast.AST, analysis: TestFileAnalysis, content: str) -> None:
    """Check test functions for quality issues.

    Detects long tests, vague naming, missing assertions, global state
    mutation, and flaky patterns like time.sleep().

    Args:
        tree: Parsed AST of the test file.
        analysis: Analysis object to update with findings.
        content: Raw file content for pattern matching.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not _is_test_function(node):
            continue
        analysis.test_count += 1
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", node.lineno)
        length = end_line - start_line + 1
        if length > 50:
            analysis.issues.append(
                TestIssue(
                    severity="high",
                    category="long_test",
                    message=f"Test '{node.name}' is {length} lines long. Consider decomposing.",
                    line_number=start_line,
                )
            )
            analysis.long_tests.append({"name": node.name, "lines": length, "start_line": start_line})
        elif length > 30:
            analysis.issues.append(
                TestIssue(
                    severity="medium",
                    category="long_test",
                    message=f"Test '{node.name}' is {length} lines. Consider splitting for clarity.",
                    line_number=start_line,
                )
            )
        if len(node.name) < 10 or node.name.count("_") < 2:
            analysis.issues.append(
                TestIssue(
                    severity="low",
                    category="naming",
                    message=f"Test '{node.name}' has a vague name. Prefer given_when_then style.",
                    line_number=start_line,
                )
            )
        if not _has_assertions(node):
            analysis.issues.append(
                TestIssue(
                    severity="high",
                    category="no_assertions",
                    message=f"Test '{node.name}' has no assertions.",
                    line_number=start_line,
                )
            )
        if _uses_global_state(node):
            analysis.issues.append(
                TestIssue(
                    severity="high",
                    category="global_state",
                    message=f"Test '{node.name}' mutates module-level state.",
                    line_number=start_line,
                )
            )
        if _has_sleep_calls(node):
            analysis.issues.append(
                TestIssue(
                    severity="medium",
                    category="flaky",
                    message=f"Test '{node.name}' uses time.sleep(); prefer deterministic waits.",
                    line_number=start_line,
                )
            )


def _is_test_function(node: ast.FunctionDef) -> bool:
    """Determine whether an AST function node represents a test function.

    Check for test_ prefix in name or test-related decorators.

    Args:
        node: AST function definition node to inspect.

    Returns:
        True if the function is a test function, False otherwise.
    """
    if node.name.startswith("test_"):
        return True
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and "test" in decorator.id.lower():
            return True
        if isinstance(decorator, ast.Attribute) and "test" in decorator.attr.lower():
            return True
    return False


def _has_assertions(node: ast.FunctionDef) -> bool:
    """Check whether a function contains any assertion statements.

    Scan the AST for assert statements or pytest-style assert calls.

    Args:
        node: AST function definition node to inspect.

    Returns:
        True if any assertions are found, False otherwise.
    """
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            return True
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Attribute) and child.func.attr.startswith("assert"):
                return True
            if isinstance(child.func, ast.Name) and child.func.id.startswith("assert"):
                return True
    return False


def _uses_global_state(node: ast.FunctionDef) -> bool:
    """Check whether a function mutates module-level state.

    Scan for global statements or writes to uppercase/underscore-prefixed names.

    Args:
        node: AST function definition node to inspect.

    Returns:
        True if global state mutation is detected, False otherwise.
    """
    for child in ast.walk(node):
        if isinstance(child, ast.Global):
            return True
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            if child.id.isupper() or child.id.startswith("_"):
                return True
    return False


def _has_sleep_calls(node: ast.FunctionDef) -> bool:
    """Check whether a function contains time.sleep() calls.

    Detect calls that may introduce flakiness through non-deterministic waits.

    Args:
        node: AST function definition node to inspect.

    Returns:
        True if sleep calls are found, False otherwise.
    """
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute) and func.attr == "sleep":
                return True
            if isinstance(func, ast.Name) and func.id == "sleep":
                return True
    return False


def _check_content_patterns(content: str, analysis: TestFileAnalysis) -> None:
    """Scan file content for hardcoded paths, URLs, and debug artifacts.

    Add issues to analysis when problematic patterns are detected.

    Args:
        content: Raw file content as string.
        analysis: TestFileAnalysis object to populate with issues.
    """
    lines = content.splitlines()
    path_patterns = [
        r"[\"\']/(home|Users|tmp|var|etc)/[^\"\']+[\"\']",
        r"[\"\'][A-Z]:\\[^\"\']+[\"\']",
    ]
    for idx, line in enumerate(lines, 1):
        for pattern in path_patterns:
            if re.search(pattern, line):
                analysis.issues.append(
                    TestIssue(
                        severity="medium",
                        category="hardcoded_path",
                        message="Hard-coded filesystem path detected; prefer tmp_path fixtures.",
                        line_number=idx,
                    )
                )
                break
    url_regex = r"https?://(?!localhost|127\\.0\\.0\\.1|example\\.com)[^\s\"\')]+"
    for idx, line in enumerate(lines, 1):
        if re.search(url_regex, line) and "mock" not in line.lower():
            analysis.issues.append(
                TestIssue(
                    severity="high",
                    category="external_dependency",
                    message="Real URL detected without mocks; tests may hit external services.",
                    line_number=idx,
                )
            )
    print_count = sum(1 for line in lines if re.search(r"\bprint\s*\(", line))
    if print_count > 2:
        analysis.issues.append(
            TestIssue(
                severity="low",
                category="debug_code",
                message=f"Found {print_count} print statements; remove debug output.",
            )
        )
    commented = [idx for idx, line in enumerate(lines, 1) if line.strip().startswith("#") and len(line.strip()) > 2]
    if len(commented) > 10:
        analysis.issues.append(
            TestIssue(
                severity="low",
                category="commented_code",
                message=f"File has {len(commented)} commented lines; consider cleanup.",
            )
        )


def analyze_all(paths: Paths, tests_dirs: list[Path] | None = None) -> list[TestFileAnalysis]:
    """Analyze all discovered test files for hardening issues.

    Discover test files, analyze each for issues, and return sorted results.

    Args:
        paths: Paths configuration containing repo_root.
        tests_dirs: Optional list of specific test directories to analyze.

    Returns:
        List of TestFileAnalysis objects sorted by priority score descending.
    """
    files = discover_test_files(paths.repo_root, tests_dirs=tests_dirs)
    logging.info("Discovered %d candidate test files", len(files))
    results: list[TestFileAnalysis] = []
    for file_path in files:
        rel = file_path.relative_to(paths.repo_root)
        logging.debug("Analyzing %s", rel)
        results.append(analyze_file(file_path, paths.repo_root))
    results.sort(key=lambda item: item.priority_score, reverse=True)
    return results


def compose_payload(paths: Paths, options: Options, results: list[TestFileAnalysis], timestamp: dt.datetime) -> dict[str, Any]:
    """Build the main JSON payload from analysis results.

    Aggregate severity totals, identify clean and priority files, and structure output.

    Args:
        paths: Paths configuration with repo_root and output_dir.
        options: Options configuration with artifacts_to_keep and log_level.
        results: List of TestFileAnalysis objects from analyze_all.
        timestamp: Timestamp for the report.

    Returns:
        Dictionary containing structured report payload.
    """
    severity_totals: Counter[str] = Counter()
    total_issues = 0
    for item in results:
        for level, count in item.severity_counts.items():
            severity_totals[level] += count
        total_issues += len(item.issues)
    clean_files = [item for item in results if item.priority_score == 0]
    highest_priority = [item for item in results if item.priority_score > 0][:20]
    payload_results = []
    for item in results:
        payload_results.append(
            {
                "path": _relativize(item.filepath, paths.repo_root),
                "priority_score": item.priority_score,
                "total_lines": item.total_lines,
                "test_count": item.test_count,
                "severity": item.severity_counts,
                "issues": [
                    {
                        "severity": issue.severity,
                        "category": issue.category,
                        "message": issue.message,
                        "line_number": issue.line_number,
                    }
                    for issue in item.issues
                ],
                "long_tests": item.long_tests,
            }
        )
    status = "ok" if total_issues == 0 else "issues-found"
    exit_code = 0 if severity_totals["high"] == 0 else 1
    summary = {
        "total_files": len(results),
        "total_test_functions": sum(item.test_count for item in results),
        "total_issues": total_issues,
        "severity_totals": dict(severity_totals),
        "high_priority_files": sum(1 for item in results if item.severity_counts["high"] > 0),
        "clean_files": len(clean_files),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "timestamp": timestamp.isoformat(),
        "status": status,
        "exit_code": exit_code,
        "message": "Issues detected." if status != "ok" else "All analyzed tests passed hardening checks.",
        "paths": {
            "repo_root": str(paths.repo_root),
            "output_dir": str(paths.output_dir),
        },
        "options": {
            "artifacts_to_keep": options.artifacts_to_keep,
            "log_level": options.log_level,
        },
        "summary": summary,
        "top_priority": [
            {
                "path": _relativize(item.filepath, paths.repo_root),
                "priority_score": item.priority_score,
                "severity": item.severity_counts,
                "issues": [
                    {
                        "severity": issue.severity,
                        "category": issue.category,
                        "message": issue.message,
                        "line_number": issue.line_number,
                    }
                    for issue in item.issues
                    if issue.severity in {"high", "medium"}
                ],
                "long_tests": item.long_tests,
            }
            for item in highest_priority
        ],
        "clean_files": [
            {
                "path": _relativize(item.filepath, paths.repo_root),
                "test_count": item.test_count,
            }
            for item in clean_files
        ],
        "results": payload_results,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    """Render the analysis payload as a Markdown summary report.

    Format summary statistics, top priority files, clean files, and recommendations.

    Args:
        payload: Dictionary containing structured report data from compose_payload.

    Returns:
        Markdown-formatted report as a single string.
    """
    summary = payload.get("summary", {})
    severities = summary.get("severity_totals", {})
    lines: list[str] = []

    lines.append("# Test Hardening Report")
    lines.append("")

    summary_list = [
        f"- Status: **{payload.get('status', 'unknown')}**",
        f"- Timestamp: {payload.get('timestamp', '')}",
        f"- Test files analyzed: {summary.get('total_files', 0)}",
        f"- Test functions: {summary.get('total_test_functions', 0)}",
        f"- Total issues: {summary.get('total_issues', 0)}",
        f"- High severity issues: {severities.get('high', 0)}",
        f"- High-priority files: {summary.get('high_priority_files', 0)}",
        f"- Clean files: {summary.get('clean_files', 0)}",
    ]
    lines.extend(summary_list)
    lines.append("")

    top_priority = payload.get("top_priority", [])
    if top_priority:
        lines.append("## Top Priority Files")
        lines.append("")
        for item in top_priority[:10]:
            lines.append(f"### `{item['path']}`")
            lines.append("")
            sev = item.get("severity", {})
            details = [
                f"- Priority score: {item['priority_score']}",
                (
                    f"- Issues by severity: high={sev.get('high', 0)}, "
                    f"medium={sev.get('medium', 0)}, low={sev.get('low', 0)}"
                ),
            ]
            lines.extend(details)
            if item.get("issues"):
                lines.append("- Key findings:")
                for issue in item["issues"][:5]:
                    line_info = f" (line {issue['line_number']})" if issue.get("line_number") else ""
                    lines.append(f"  - [{issue['severity'].upper()}] {issue['message']}{line_info}")
            if item.get("long_tests"):
                lines.append("- Long tests:")
                for test in item["long_tests"][:3]:
                    lines.append(f"  - `{test['name']}` — {test['lines']} lines (starts at {test['start_line']})")
            lines.append("")

    clean_files = payload.get("clean_files", [])
    if clean_files:
        lines.append("## Clean Files")
        lines.append("")
        for entry in clean_files[:10]:
            lines.append(f"- `{entry['path']}` ({entry['test_count']} tests)")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.extend(
        [
            "1. Address high severity issues before medium/low findings.",
            "1. Decompose long tests into focused units.",
            "1. Mock external dependencies and remove global state.",
            "1. Replace time.sleep() with deterministic waits.",
            "1. Use descriptive names following given-when-then style.",
        ]
    )

    lines.append("")
    return "\n".join(lines)


def build_manifest(
    *,
    paths: Paths,
    options: Options,
    timestamp: dt.datetime,
    timestamp_slug: str,
    status: str,
    exit_code: int,
    tests_dirs: list[Path] | None = None,
) -> dict[str, Any]:
    """Build the manifest metadata for this analysis run.

    Create provenance and configuration metadata for artifact tracking.

    Args:
        paths: Paths configuration with repo_root and output_dir.
        options: Options configuration with runtime settings.
        timestamp: Timestamp for the report.
        timestamp_slug: Formatted timestamp string for directory naming.
        status: Report status string (ok or issues-found).
        exit_code: Exit code for the run (0 or 1).
        tests_dirs: Optional list of specific test directories analyzed.

    Returns:
        Dictionary containing manifest metadata.
    """
    bundle_dir = paths.output_dir / timestamp_slug
    return {
        "schema_version": SCHEMA_VERSION,
        "viewer_slug": "producer_reports",
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp_slug,
        "generated_at": timestamp.astimezone(dt.timezone.utc).isoformat(),
        "git_sha": _detect_git_sha(paths.repo_root),
        "status": status,
        "exit_code": exit_code,
        "catalog": [
            {
                "script_path": str(Path(".repo_studios/scripts/producers/analyze_test_hardening.py")),
                "role": "producer",
            }
        ],
        "paths": {
            "repo_root": str(paths.repo_root),
            "reports_root": str(paths.output_dir),
            "bundle_dir": str(bundle_dir),
        },
        "inputs": {
            "test_patterns": list(TEST_PATTERNS),
            "ignored_parts": sorted(IGNORED_PARTS),
            "tests_dirs": [str(d) for d in tests_dirs] if tests_dirs else None,
            "artifacts_to_keep": options.artifacts_to_keep,
            "log_level": options.log_level,
        },
        "provenance": {
            "trigger_type": _detect_trigger_type(),
            "requested_by": _detect_requested_by(),
        },
    }


def build_telemetry(payload: dict[str, Any], *, timestamp_slug: str) -> dict[str, Any]:
    """Build telemetry data structure from the analysis payload.

    Extract metrics and component data for downstream telemetry consumers.

    Args:
        payload: Dictionary containing structured report data.
        timestamp_slug: Formatted timestamp string for run identification.

    Returns:
        Dictionary containing telemetry metrics and components.
    """
    summary = payload.get("summary", {})
    severities = summary.get("severity_totals", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "viewer_slug": "producer_reports",
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp_slug,
        "timestamp": payload.get("timestamp"),
        "status": payload.get("status"),
        "exit_code": payload.get("exit_code"),
        "metrics": {
            "total_files": summary.get("total_files", 0),
            "total_test_functions": summary.get("total_test_functions", 0),
            "total_issues": summary.get("total_issues", 0),
            "severity": {
                "high": severities.get("high", 0),
                "medium": severities.get("medium", 0),
                "low": severities.get("low", 0),
            },
            "high_priority_files": summary.get("high_priority_files", 0),
            "clean_files": summary.get("clean_files", 0),
        },
        "components": {
            "hardening": {
                "summary": summary,
                "top_priority": payload.get("top_priority", []),
                "clean_files": payload.get("clean_files", []),
                "results": payload.get("results", []),
            }
        },
    }


def prune_history(
    topic_dir: Path,
    keep: int,
    *,
    current_run: Path | None,
    logger: logging.Logger | None,
) -> list[Path]:
    """Remove old run directories beyond the retention threshold.

    Delegate to prune_run_directories utility for timestamp-based cleanup.

    Args:
        topic_dir: Directory containing timestamped run subdirectories.
        keep: Number of recent runs to retain (minimum 1).
        current_run: Current run directory to preserve regardless of age.
        logger: Logger for debug output.

    Returns:
        List of paths that were removed.
    """
    result = prune_run_directories(
        topic_dir,
        keep=max(keep, 1),
        current_run=current_run,
        logger=logger,
    )
    return result.removed


def _relativize(path: Path, repo_root: Path) -> str:
    """Convert a path to a repo-relative POSIX string.

    Fall back to absolute POSIX path if path is outside repo_root.

    Args:
        path: Path to convert.
        repo_root: Repository root for relative calculation.

    Returns:
        POSIX-formatted relative or absolute path string.
    """
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    """Execute the test hardening analysis pipeline.

    Parse arguments, analyze test files, compose payload, and write artifacts.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Dictionary containing the full analysis payload with output paths.
    """
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)
    logger = logging.getLogger(__name__)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _resolve_timestamp(getattr(args, "timestamp", None))
    timestamp_slug = _timestamp_slug(timestamp)

    # Resolve tests_dirs from CLI args
    tests_dirs: list[Path] | None = None
    if getattr(args, "tests_dir", None):
        tests_dirs = [Path(d) for d in args.tests_dir]

    results = analyze_all(paths, tests_dirs=tests_dirs)
    payload = compose_payload(paths, options, results, timestamp)
    bundle_dir = (paths.output_dir / timestamp_slug).resolve()
    storage = create_storage(paths.output_dir, "", "", timestamp=timestamp_slug)
    manifest = build_manifest(
        paths=paths,
        options=options,
        timestamp=timestamp,
        timestamp_slug=timestamp_slug,
        status=str(payload.get("status", "unknown")),
        exit_code=int(payload.get("exit_code", 0)),
        tests_dirs=tests_dirs,
    )
    summary_md = render_markdown_report(payload)
    telemetry = build_telemetry(payload, timestamp_slug=timestamp_slug)

    # DB_INTEGRATION_MARKER: test hardening manifest write
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: test hardening summary markdown write
    storage.write_summary({"markdown": summary_md}, format="md")
    # DB_INTEGRATION_MARKER: test hardening telemetry write
    storage.write_telemetry(telemetry)

    removed = prune_history(
        paths.output_dir,
        options.artifacts_to_keep,
        current_run=bundle_dir,
        logger=logger,
    )
    if removed:
        logger.debug("Pruned test hardening runs: %s", ", ".join(sorted(path.name for path in removed)))

    payload["viewer_slug"] = "producer_reports"
    payload["topic"] = TOPIC_SLUG
    payload["run_timestamp"] = timestamp_slug
    payload["output_dir"] = str(bundle_dir)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the test hardening analysis script.

    Execute run() and return the exit code from the payload.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 if high-severity issues found).
    """
    payload = run(argv)
    return int(payload.get("exit_code", 0))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
