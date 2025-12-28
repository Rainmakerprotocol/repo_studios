"""Shared helpers for analyzing pytest log bundles."""

from __future__ import annotations

import importlib
import importlib.util
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

__all__ = [
    "TestHealth",
    "TestLogAnalysisResult",
    "select_junit_artifact",
    "select_full_log",
    "build_test_log_report",
    "render_markdown",
]

WARNINGS_HDR = re.compile(r"^=+\s+warnings summary\s+=+$", re.IGNORECASE)
SLOWEST_HDR = re.compile(r"^=+\s+slowest\s+\d+\s+durations\s+=+$", re.IGNORECASE)
_WARN_LINE_RE = re.compile(r"^(?P<path>[^:]+):\d+:\s*(?P<type>[A-Za-z]+Warning):\s*(?P<msg>.*)$")
_SLOW_LINE_RE = re.compile(r"^(?P<secs>\d+\.\d+)s\s+call\s+(?P<node>\S+)\s*$")


@dataclass
class TestHealth:
    total: int = 0
    passed: int = 0
    skipped: int = 0
    xfailed: int = 0
    failed: int = 0
    errors: int = 0


@dataclass
class TestLogAnalysisResult:
    report: dict[str, Any]
    markdown: str


def _latest(path: Path, prefix: str, suffix: str) -> Path | None:
    candidates = sorted(p for p in path.glob(f"{prefix}_*.{suffix}") if p.is_file())
    return candidates[-1] if candidates else None


def _latest_by_prefix(path: Path, prefix: str) -> Path | None:
    candidates = sorted(p for p in path.glob(f"{prefix}_*.*") if p.is_file())
    return candidates[-1] if candidates else None


def read_text(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _load_element_tree():
    try:
        spec = importlib.util.find_spec("defusedxml.ElementTree")
    except ModuleNotFoundError:
        spec = None
    if spec is not None:
        return importlib.import_module("defusedxml.ElementTree")

    import xml.etree.ElementTree as _ElementTree

    return _ElementTree


def parse_junit(path: Path | None) -> TestHealth:
    """Parse a JUnit XML file into :class:`TestHealth`."""

    ElementTree = _load_element_tree()
    th = TestHealth()
    if path is None or not path.exists():
        return th
    try:
        root = ElementTree.parse(path).getroot()
    except Exception:
        return th
    suites = list(root.findall("testsuite"))
    if root.tag == "testsuite":
        suites.insert(0, root)
    for suite in suites:
        th.total += int(suite.get("tests") or 0)
        th.failed += int(suite.get("failures") or 0)
        th.errors += int(suite.get("errors") or 0)
        th.skipped += int(suite.get("skipped") or 0)
    for tc in root.iterfind(".//testcase"):
        skipped = tc.find("skipped")
        if skipped is None:
            continue
        message = (skipped.get("message") or "").lower()
        if "xfailed" in message or "xfail" in message:
            th.xfailed += 1
    th.passed = max(th.total - (th.failed + th.errors + th.skipped), 0)
    return th


def select_junit_artifact(logs_dir: Path) -> Path | None:
    ElementTree = _load_element_tree()
    candidates = sorted(p for p in logs_dir.glob("junit_*.xml") if p.is_file())
    if not candidates:
        candidates = sorted(p for p in logs_dir.glob("junit*.*") if p.is_file())

    def _totals_and_internal_only(path: Path) -> tuple[int, bool]:
        try:
            root = ElementTree.parse(path).getroot()
        except Exception:
            return 0, False
        suites = list(root.findall("testsuite"))
        if root.tag == "testsuite":
            suites.insert(0, root)
        total = 0
        for suite in suites:
            total += int(suite.get("tests") or 0)
        internal_only = False
        if total <= 1:
            for tc in root.iterfind(".//testcase"):
                name = tc.get("name") or ""
                classname = tc.get("classname") or ""
                if name == "internal" and classname == "pytest":
                    internal_only = True
                    break
        return total, internal_only

    best: Path | None = None
    best_total = -1
    for candidate in candidates:
        total, internal_only = _totals_and_internal_only(candidate)
        if internal_only:
            continue
        if total > best_total or (
            total == best_total and (best is None or candidate.stat().st_mtime > best.stat().st_mtime)
        ):
            best = candidate
            best_total = total
    if best is not None:
        return best
    for candidate in candidates:
        total, _ = _totals_and_internal_only(candidate)
        if total > best_total or (
            total == best_total and (best is None or candidate.stat().st_mtime > best.stat().st_mtime)
        ):
            best = candidate
            best_total = total
    return best or _latest_by_prefix(logs_dir, "junit")


def select_full_log(logs_dir: Path) -> Path | None:
    return _latest(logs_dir, "pytest", "txt") or _latest_by_prefix(logs_dir, "pytest")


def _extract_block(lines: Sequence[str], start_re: re.Pattern[str]) -> list[str]:
    start = None
    for idx, line in enumerate(lines):
        if start_re.match(line.strip()):
            start = idx + 1
            break
    if start is None:
        return []
    collected: list[str] = []
    for line in lines[start:]:
        if line.strip().startswith("=") and (
            "summary" in line or "coverage" in line or "slowest" in line or "short test" in line
        ):
            break
        collected.append(line)
    return collected


def _parse_warnings(block: Iterable[str]) -> tuple[Counter[str], Counter[str]]:
    by_type: Counter[str] = Counter()
    by_file: Counter[str] = Counter()
    for line in block:
        match = _WARN_LINE_RE.match(line.strip())
        if not match:
            continue
        by_type[match.group("type")] += 1
        by_file[match.group("path")] += 1
    return by_type, by_file


def _parse_slowest(block: Iterable[str]) -> list[dict[str, Any]]:
    slow: list[dict[str, Any]] = []
    for line in block:
        match = _SLOW_LINE_RE.match(line.strip())
        if match:
            slow.append({"seconds": float(match.group("secs")), "nodeid": match.group("node")})
    return slow


def _count_tracebacks(text: str) -> int:
    return text.count("Traceback (most recent call last):")


def build_test_log_report(
    logs_dir: Path,
    *,
    junit_path: Path | None = None,
    full_log_path: Path | None = None,
    generated: datetime | None = None,
) -> TestLogAnalysisResult:
    logs_dir = logs_dir.resolve()
    junit = junit_path or select_junit_artifact(logs_dir)
    full_log = full_log_path or select_full_log(logs_dir)
    test_health = parse_junit(junit)
    log_text = read_text(full_log)
    lines = log_text.splitlines()
    warnings_block = _extract_block(lines, WARNINGS_HDR)
    slow_block = _extract_block(lines, SLOWEST_HDR)

    warn_by_type, warn_by_file = _parse_warnings(warnings_block)
    slow_tests = _parse_slowest(slow_block)
    traceback_count = _count_tracebacks(log_text)

    generated = generated or datetime.now()
    report = {
        "schema_version": 1,
        "meta": {
            "generated_at": generated.isoformat(),
            "logs_dir": str(logs_dir),
            "junit": str(junit) if junit else None,
            "full_log": str(full_log) if full_log else None,
        },
        "summary": {
            "total": test_health.total,
            "passed": test_health.passed,
            "skipped": test_health.skipped,
            "xfailed": test_health.xfailed,
            "failed": test_health.failed,
            "errors": test_health.errors,
            "warnings_total": int(sum(warn_by_type.values())),
            "tracebacks": traceback_count,
        },
        "warnings": {
            "by_type": dict(warn_by_type),
            "by_file": dict(warn_by_file),
        },
        "slow_tests": slow_tests,
    }
    markdown = render_markdown(report)
    return TestLogAnalysisResult(report=report, markdown=markdown)


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("## Test Log Health Report")
    lines.append("")
    meta = report.get("meta", {})
    lines.append(f"Generated: {meta.get('generated_at', 'unknown')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    summary = report.get("summary", {})
    lines.append(
        "- total: {total}, passed: {passed}, skipped: {skipped}, xfailed: {xfailed}, failed: {failed}, errors: {errors}".format(
            total=summary.get("total", 0),
            passed=summary.get("passed", 0),
            skipped=summary.get("skipped", 0),
            xfailed=summary.get("xfailed", 0),
            failed=summary.get("failed", 0),
            errors=summary.get("errors", 0),
        )
    )
    lines.append(
        "- warnings_total: {warnings_total}, tracebacks: {tracebacks}".format(
            warnings_total=summary.get("warnings_total", 0),
            tracebacks=summary.get("tracebacks", 0),
        )
    )
    lines.append("")
    lines.append("## Warnings by Type")
    lines.append("")
    by_type = report.get("warnings", {}).get("by_type", {})
    if by_type:
        lines.append("| Type | Count |")
        lines.append("|---|---:|")
        for wtype, count in sorted(by_type.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| {wtype} | {count} |")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Top Warning Files")
    lines.append("")
    by_file = report.get("warnings", {}).get("by_file", {})
    if by_file:
        lines.append("| File | Count |")
        lines.append("|---|---:|")
        for path, count in sorted(by_file.items(), key=lambda item: (-item[1], item[0]))[:15]:
            lines.append(f"| {path} | {count} |")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Slowest Tests")
    lines.append("")
    slow_tests = report.get("slow_tests", [])
    if slow_tests:
        lines.append("| Seconds | Test |")
        lines.append("|---:|---|")
        for item in slow_tests:
            lines.append(f"| {item.get('seconds', 0):.2f} | {item.get('nodeid', '?')} |")
    else:
        lines.append("(none)")
    lines.append("")
    return "\n".join(lines)
