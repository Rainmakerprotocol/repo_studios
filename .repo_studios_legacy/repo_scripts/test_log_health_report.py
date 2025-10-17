#!/usr/bin/env python3
"""
Test Log Health Report — Warning/Exception Census + Slowest Tests

Scans the latest pytest artifacts under .repo_studios/pytest_logs and
produces a timestamped report with:
- Warnings by type and by file
- Exception/traceback count
- Slowest tests (from pytest durations block)
- Basic pass/skip/xfail summary (from JUnit)

Outputs (under --output-base/<ts>/):
- report.json
- report.md
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

LOGS_DIR_DEFAULT = ".repo_studios/pytest_logs"


def _latest(path: Path, prefix: str, suffix: str) -> Path | None:
    candidates = sorted(p for p in path.glob(f"{prefix}_*.{suffix}") if p.is_file())
    return candidates[-1] if candidates else None


def _latest_by_prefix(path: Path, prefix: str) -> Path | None:
    candidates = sorted(p for p in path.glob(f"{prefix}_*.*") if p.is_file())
    return candidates[-1] if candidates else None


def _ensure_out(base: Path) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_dir = base / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


WARNINGS_HDR = re.compile(r"^=+\s+warnings summary\s+=+$", re.IGNORECASE)
SLOWEST_HDR = re.compile(r"^=+\s+slowest\s+\d+\s+durations\s+=+$", re.IGNORECASE)
SUMMARY_HDR = re.compile(r"^=+\s+short test summary info\s+=+$", re.IGNORECASE)


def _extract_block(lines: list[str], start_re: re.Pattern[str]) -> list[str]:
    start = None
    for i, line in enumerate(lines):
        if start_re.match(line.strip()):
            start = i + 1
            break
    if start is None:
        return []
    # collect until next header (====) or EOF
    out: list[str] = []
    for line in lines[start:]:
        if line.strip().startswith("=") and (
            "summary" in line or "coverage" in line or "slowest" in line or "short test" in line
        ):
            break
        out.append(line.rstrip("\n"))
    return out


_WARN_LINE_RE = re.compile(r"^(?P<path>[^:]+):\d+:\s*(?P<type>[A-Za-z]+Warning):\s*(?P<msg>.*)$")


@dataclass
class TestHealth:
    total: int = 0
    passed: int = 0
    skipped: int = 0
    xfailed: int = 0
    failed: int = 0
    errors: int = 0


def _parse_junit(path: Path) -> TestHealth:
    # Use defusedxml for secure XML parsing (avoid XXE and entity expansion attacks)
    from defusedxml import ElementTree

    th = TestHealth()
    try:
        root = ElementTree.parse(path).getroot()
    except Exception:
        return th
    # aggregate across suites
    for suite in root.findall("testsuite"):
        th.total += int(suite.get("tests") or 0)
        th.failed += int(suite.get("failures") or 0)
        th.errors += int(suite.get("errors") or 0)
        th.skipped += int(suite.get("skipped") or 0)
    # xfailed isn’t directly in JUnit; approximate from testcase/skipped message
    for tc in root.iterfind(".//testcase"):
        sk = tc.find("skipped")
        if sk is not None:
            msg = (sk.get("message") or "").lower()
            if "xfailed" in msg or "xfail" in msg:
                th.xfailed += 1
    th.passed = max(th.total - (th.failed + th.errors + th.skipped), 0)
    return th


def _pick_best_junit(logs_dir: Path) -> Path | None:
    """Select the most representative JUnit XML artifact.

    Heuristic:
    - Prefer files matching junit_*.xml
    - Parse each and compute total test count across suites
    - Skip incidental internal-only artifacts (pytest internal error shim):
        tests == 1 and a single testcase with classname="pytest" and name="internal"
    - Choose the file with the highest total tests; tie-breaker: latest mtime
    - Fallback: if all were skipped/unparseable, choose the max-tests among all candidates;
      if still none, use the latest by name as last resort.
    """
    # Use defusedxml for secure XML parsing when inspecting JUnit artifacts
    from defusedxml import ElementTree

    candidates = sorted(p for p in logs_dir.glob("junit_*.xml") if p.is_file())
    if not candidates:
        # broaden slightly as a fallback
        candidates = sorted(p for p in logs_dir.glob("junit*.*") if p.is_file())

    def _totals_and_internal_only(path: Path) -> tuple[int, bool]:
        try:
            root = ElementTree.parse(path).getroot()
        except Exception:
            return 0, False
        total = 0
        for suite in root.findall("testsuite"):
            total += int(suite.get("tests") or 0)
        internal_only = False
        if total == 1:
            for tc in root.iterfind(".//testcase"):
                name = (tc.get("name") or "")
                classname = (tc.get("classname") or "")
                if name == "internal" and classname == "pytest":
                    internal_only = True
                    break
        return total, internal_only

    best: Path | None = None
    best_total = -1

    # First pass: skip internal-only artifacts
    for p in candidates:
        total, internal_only = _totals_and_internal_only(p)
        if internal_only:
            continue
        if total > best_total or (total == best_total and (best is None or p.stat().st_mtime > best.stat().st_mtime)):
            best = p
            best_total = total

    if best is not None:
        return best

    # Second pass: include all, pick max tests
    for p in candidates:
        total, _ = _totals_and_internal_only(p)
        if total > best_total or (total == best_total and (best is None or p.stat().st_mtime > best.stat().st_mtime)):
            best = p
            best_total = total

    # Final fallback: latest by prefix
    return best or _latest_by_prefix(logs_dir, "junit")


def _parse_warnings(block: list[str]) -> tuple[Counter[str], Counter[str]]:
    by_type: Counter[str] = Counter()
    by_file: Counter[str] = Counter()
    for line in block:
        m = _WARN_LINE_RE.match(line.strip())
        if not m:
            continue
        wtype = m.group("type")
        path = m.group("path")
        by_type[wtype] += 1
        by_file[path] += 1
    return by_type, by_file


_SLOW_LINE_RE = re.compile(r"^(?P<secs>\d+\.\d+)s\s+call\s+(?P<node>\S+)\s*$")


def _parse_slowest(block: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in block:
        m = _SLOW_LINE_RE.match(line.strip())
        if m:
            out.append({"seconds": float(m.group("secs")), "nodeid": m.group("node")})
    return out


def _count_tracebacks(text: str) -> int:
    return text.count("Traceback (most recent call last):")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate test log health report")
    ap.add_argument("--logs-dir", default=LOGS_DIR_DEFAULT)
    ap.add_argument("--output-base", default=".repo_studios/test_health")
    args = ap.parse_args()

    repo_root = Path(".").resolve()
    logs_dir = (Path(args.logs_dir) if Path(args.logs_dir).is_absolute() else (repo_root / args.logs_dir)).resolve()
    out_base = (Path(args.output_base) if Path(args.output_base).is_absolute() else (repo_root / args.output_base)).resolve()
    out_dir = _ensure_out(out_base)

    # Choose the most representative JUnit file to avoid incidental internal artifacts
    junit = _pick_best_junit(logs_dir) or _latest(logs_dir, "junit", "xml") or _latest_by_prefix(logs_dir, "junit")
    full_log = _latest(logs_dir, "pytest", "txt") or _latest_by_prefix(logs_dir, "pytest")

    junit_health = _parse_junit(junit) if junit else TestHealth()
    log_text = _read(full_log) if full_log else ""
    lines = log_text.splitlines()
    warn_block = _extract_block(lines, WARNINGS_HDR)
    slow_block = _extract_block(lines, SLOWEST_HDR)

    warn_by_type, warn_by_file = _parse_warnings(warn_block)
    slow_tests = _parse_slowest(slow_block)
    traceback_count = _count_tracebacks(log_text)

    data = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "logs_dir": str(logs_dir),
            "junit": str(junit) if junit else None,
            "full_log": str(full_log) if full_log else None,
        },
        "summary": {
            "total": junit_health.total,
            "passed": junit_health.passed,
            "skipped": junit_health.skipped,
            "xfailed": junit_health.xfailed,
            "failed": junit_health.failed,
            "errors": junit_health.errors,
            "warnings_total": int(sum(warn_by_type.values())),
            "tracebacks": traceback_count,
        },
        "warnings": {
            "by_type": warn_by_type,
            "by_file": warn_by_file,
        },
        "slow_tests": slow_tests,
    }

    # JSON (convert Counters)
    json_ready = json.loads(json.dumps(data, default=lambda o: dict(o)))
    (out_dir / "report.json").write_text(json.dumps(json_ready, indent=2), encoding="utf-8")

    # Markdown
    md: list[str] = []
    md.append("# Test Log Health Report\n")
    md.append(f"Generated: {data['meta']['generated_at']}\n")
    md.append("\n## Summary\n")
    s = data["summary"]
    md.append(
        f"- total: {s['total']}, passed: {s['passed']}, skipped: {s['skipped']}, xfailed: {s['xfailed']}, failed: {s['failed']}, errors: {s['errors']}\n"
    )
    md.append(f"- warnings_total: {s['warnings_total']}, tracebacks: {s['tracebacks']}\n")

    md.append("\n## Warnings by Type\n")
    if warn_by_type:
        md.append("| Type | Count |\n|---|---:|\n")
        for wtype, cnt in warn_by_type.most_common():
            md.append(f"| {wtype} | {cnt} |\n")
    else:
        md.append("(none)\n")

    md.append("\n## Top Warning Files\n")
    if warn_by_file:
        md.append("| File | Count |\n|---|---:|\n")
        for path, cnt in warn_by_file.most_common(15):
            md.append(f"| {path} | {cnt} |\n")
    else:
        md.append("(none)\n")

    md.append("\n## Slowest Tests\n")
    if slow_tests:
        md.append("| Seconds | Test |\n|---:|---|\n")
        for item in slow_tests:
            md.append(f"| {item['seconds']:.2f} | {item['nodeid']} |\n")
    else:
        md.append("(none)\n")

    (out_dir / "report.md").write_text("\n".join(md), encoding="utf-8")

    logging.info("Test log health report written to %s", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
