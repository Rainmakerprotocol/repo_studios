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
from typing import List, Sequence

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/test_hardening_reports")
RUN_PREFIX = "test_hardening"
DEFAULT_ARTIFACTS_TO_KEEP = 10
SCHEMA_VERSION = 1
TEST_PATTERNS = ("test_*.py", "*_test.py", "test*.py")
IGNORED_PARTS = {".git", ".repo_studios", ".venv", "__pycache__"}

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
except ModuleNotFoundError:  # pragma: no cover - fallback when package path isn't configured
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int
    log_level: str = "INFO"


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(
            field="output_dir",
            default=DEFAULT_OUTPUT_DIR,
            ensure_dir=True,
            within_repo=False,
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
    severity: str
    category: str
    message: str
    line_number: int | None = None


@dataclass
class TestFileAnalysis:
    filepath: Path
    total_lines: int = 0
    test_count: int = 0
    issues: List[TestIssue] = field(default_factory=list)
    long_tests: List[dict[str, int | str]] = field(default_factory=list)
    imports: set[str] = field(default_factory=set)

    @property
    def severity_counts(self) -> dict[str, int]:
        return {
            "high": sum(1 for issue in self.issues if issue.severity == "high"),
            "medium": sum(1 for issue in self.issues if issue.severity == "medium"),
            "low": sum(1 for issue in self.issues if issue.severity == "low"),
        }

    @property
    def priority_score(self) -> int:
        counts = self.severity_counts
        return counts["high"] * 10 + counts["medium"] * 3 + counts["low"]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="analyze_test_hardening",
        description=__doc__ or "",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", help="Repository root directory")
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
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace) -> Options:
    options = build_standard_options(args, OPTIONS_CONFIG)
    return replace(options, log_level=str(args.log_level))


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def discover_test_files(repo_root: Path) -> list[Path]:
    results: set[Path] = set()
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
    if node.name.startswith("test_"):
        return True
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and "test" in decorator.id.lower():
            return True
        if isinstance(decorator, ast.Attribute) and "test" in decorator.attr.lower():
            return True
    return False


def _has_assertions(node: ast.FunctionDef) -> bool:
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
    for child in ast.walk(node):
        if isinstance(child, ast.Global):
            return True
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            if child.id.isupper() or child.id.startswith("_"):
                return True
    return False


def _has_sleep_calls(node: ast.FunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute) and func.attr == "sleep":
                return True
            if isinstance(func, ast.Name) and func.id == "sleep":
                return True
    return False


def _check_content_patterns(content: str, analysis: TestFileAnalysis) -> None:
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


def analyze_all(paths: Paths) -> list[TestFileAnalysis]:
    files = discover_test_files(paths.repo_root)
    logging.info("Discovered %d candidate test files", len(files))
    results: list[TestFileAnalysis] = []
    for file_path in files:
        rel = file_path.relative_to(paths.repo_root)
        logging.debug("Analyzing %s", rel)
        results.append(analyze_file(file_path, paths.repo_root))
    results.sort(key=lambda item: item.priority_score, reverse=True)
    return results


def compose_payload(paths: Paths, options: Options, results: list[TestFileAnalysis], timestamp: dt.datetime) -> dict:
    severity_totals = Counter()
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


def render_markdown_report(payload: dict) -> str:
    summary = payload.get("summary", {})
    severities = summary.get("severity_totals", {})
    lines: list[str] = []

    lines.append("# Test Hardening Report")
    lines.append("")

    summary_list = [
        f"* Status: **{payload.get('status', 'unknown')}**",
        f"* Timestamp: {payload.get('timestamp', '')}",
        f"* Test files analyzed: {summary.get('total_files', 0)}",
        f"* Test functions: {summary.get('total_test_functions', 0)}",
        f"* Total issues: {summary.get('total_issues', 0)}",
        f"* High severity issues: {severities.get('high', 0)}",
        f"* High-priority files: {summary.get('high_priority_files', 0)}",
        f"* Clean files: {summary.get('clean_files', 0)}",
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
                f"* Priority score: {item['priority_score']}",
                (
                    f"* Issues by severity: high={sev.get('high', 0)}, "
                    f"medium={sev.get('medium', 0)}, low={sev.get('low', 0)}"
                ),
            ]
            lines.extend(details)
            if item.get("issues"):
                lines.append("* Key findings:")
                for issue in item["issues"][:5]:
                    line_info = f" (line {issue['line_number']})" if issue.get("line_number") else ""
                    lines.append(f"  * [{issue['severity'].upper()}] {issue['message']}{line_info}")
            if item.get("long_tests"):
                lines.append("* Long tests:")
                for test in item["long_tests"][:3]:
                    lines.append(f"  * `{test['name']}` — {test['lines']} lines (starts at {test['start_line']})")
            lines.append("")

    clean_files = payload.get("clean_files", [])
    if clean_files:
        lines.append("## Clean Files")
        lines.append("")
        for entry in clean_files[:10]:
            lines.append(f"* `{entry['path']}` ({entry['test_count']} tests)")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.extend(
        [
            "1. Address high severity issues before medium/low findings.",
            "2. Decompose long tests into focused units.",
            "3. Mock external dependencies and remove global state.",
            "4. Replace time.sleep() with deterministic waits.",
            "5. Use descriptive names following given-when-then style.",
        ]
    )

    lines.append("")
    return "\n".join(lines)


def render_log(payload: dict) -> str:
    summary = payload.get("summary", {})
    severities = summary.get("severity_totals", {})
    entries = [
        f"status={payload.get('status', 'unknown')}",
        f"exit_code={payload.get('exit_code', 0)}",
        f"total_files={summary.get('total_files', 0)}",
        f"total_tests={summary.get('total_test_functions', 0)}",
        f"issues_total={summary.get('total_issues', 0)}",
        f"issues_high={severities.get('high', 0)}",
        f"issues_medium={severities.get('medium', 0)}",
        f"issues_low={severities.get('low', 0)}",
    ]
    return "\n".join(entries) + "\n"


def write_artifacts(paths: Paths, payload: dict, timestamp: dt.datetime) -> Path:
    run_dir = paths.output_dir / f"{RUN_PREFIX}-{timestamp.strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "report.md").write_text(render_markdown_report(payload), encoding="utf-8")
    (run_dir / "log.txt").write_text(render_log(payload), encoding="utf-8")
    latest_dir = paths.output_dir / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    for src_name, latest_name in {
        "report.json": "latest_report.json",
        "report.md": "latest_report.md",
        "log.txt": "latest_log.txt",
    }.items():
        src = run_dir / src_name
        dest = latest_dir / latest_name
        try:
            if dest.exists():
                dest.unlink()
            dest.hardlink_to(src)
        except OSError:
            dest.write_bytes(src.read_bytes())
    return run_dir


def prune_history(output_dir: Path, keep: int) -> None:
    if not output_dir.exists():
        return
    candidates = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith(RUN_PREFIX)]
    candidates.sort(key=lambda node: node.name, reverse=True)
    for stale in candidates[keep:]:
        for child in sorted(stale.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if child.is_file():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                child.rmdir()
        stale.rmdir()


def _relativize(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def run(argv: Sequence[str] | None = None) -> dict:
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc)
    results = analyze_all(paths)
    payload = compose_payload(paths, options, results, timestamp)
    write_artifacts(paths, payload, timestamp)
    prune_history(paths.output_dir, options.artifacts_to_keep)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    payload = run(argv)
    return int(payload.get("exit_code", 0))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
