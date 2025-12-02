#!/usr/bin/env python3
"""
Pytest log runner and summarizer.

Runs pytest with the desired flags, saves the full terminal output to a
timestamped log under <logs_dir>/pytest_YYYY-MM-DD_hhmm.txt, and then
parses the output to write two additional summaries:

- <logs_dir>/pytest_failed_logs/pytest_failed_YYYY-MM-DD_hhmm.txt
  Contains only failed tests, grouped by file with a count summary.

- <logs_dir>/pytest_skip_logs/pytest_skip_YYYY-MM-DD_hhmm.txt
  Contains only skipped tests, grouped by file with a count summary.

Defaults (auto-detected workspace):
* cwd: current working directory (or GITHUB_WORKSPACE when set)
* logs_dir: <cwd>/.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs
* pytest command:
    /bin/python -m pytest -vv -ra -rs --color=no \
        --show-capture=all --durations=25 --durations-min=0.50 \
        --junitxml <logs_dir>/junit_YYYY-MM-DD_hhmm.xml

Pass-through extra pytest args after "--".

Examples:
    # Run full suite
    python ./.repo_studios/pytest_log_runner.py

    # Run a subset
    python ./.repo_studios/pytest_log_runner.py -- \
        tests/api/test_events_sse.py::test_sse_burst_delivery_and_stats_update
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import os
import re
import signal
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from command_center.scripts.orchestrators import run_test_execution_telemetry as telemetry_topic_runner

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/orchestrator_runs/pytest_log_capture")
DEFAULT_LOGS_DIR = Path(".repo_studios/reports/orchestrator_logs/pytest_log_capture_logs")
DEFAULT_ARTIFACTS_TO_KEEP = 5
RUN_STEM = "pytest_log_capture"
SCHEMA_VERSION = 1
TOPIC_TARGET = "command_center.scripts.orchestrators.run_test_execution_telemetry"
LEGACY_ENV_FLAG = "PYTEST_LOG_CAPTURE_USE_LEGACY"
_LEGACY_ONLY_FLAGS = ("--from-log", "--from-junit", "--cwd")

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

# Use defusedxml for secure XML parsing; fallback keeps runner usable when missing
try:  # pragma: no cover - import wiring
    from defusedxml import ElementTree  # type: ignore

    _USING_DEFUSEDXML = True
except ModuleNotFoundError:  # pragma: no cover - exercised in environments without dependency
    from xml.etree import ElementTree  # type: ignore

    _USING_DEFUSEDXML = False

# Patterns to suppress from console/log output (non-actionable noise)
_SUPPRESS_LINE_SUBSTR = [
    # Python 3.13 + coverage.py/ast: sqlite connection ResourceWarnings during teardown
    "ResourceWarning: unclosed database in <sqlite3.Connection object",
    "ResourceWarning: Enable tracemalloc to get the object allocation traceback",
    # Follow-up context lines emitted with those warnings
    'self.code = compile(text, filename, "exec", dont_inherit=True)',
    "return compile(source, filename, mode, flags",
]


def _use_legacy_runner(argv: Sequence[str] | None) -> bool:
    flag = os.environ.get(LEGACY_ENV_FLAG)
    if flag is not None and flag.strip().lower() in {"1", "true", "yes", "on"}:
        return True
    raw = list(argv) if argv is not None else []
    if "--" in raw:
        return True
    for option in _LEGACY_ONLY_FLAGS:
        for entry in raw:
            if entry == option or entry.startswith(f"{option}="):
                return True
    return False


def _has_option(args: Sequence[str], option: str) -> bool:
    prefix = f"{option}="
    return any(entry == option or entry.startswith(prefix) for entry in args)


def _collect_option_value(args: Sequence[str], option: str) -> str | None:
    prefix = f"{option}="
    for index, entry in enumerate(args):
        if entry == option:
            if index + 1 < len(args):
                return args[index + 1]
            return None
        if entry.startswith(prefix):
            return entry.split("=", 1)[1]
    return None


def _normalize_topic_args(argv: Sequence[str] | None) -> list[str]:
    raw = list(argv) if argv is not None else []
    normalized: list[str] = []
    skip_next = False
    for index, entry in enumerate(raw):
        if skip_next:
            skip_next = False
            continue
        if entry == "--output-dir":
            normalized.append("--healthview-root")
            if index + 1 < len(raw):
                normalized.append(raw[index + 1])
                skip_next = True
            continue
        if entry.startswith("--output-dir="):
            normalized.append(entry.replace("--output-dir", "--healthview-root", 1))
            continue
        normalized.append(entry)

    keep_value = _collect_option_value(normalized, "--artifacts-to-keep")
    if keep_value is None:
        keep_value = str(DEFAULT_ARTIFACTS_TO_KEEP)
        normalized.extend(["--artifacts-to-keep", keep_value])

    for option in (
        "--collector-artifacts-to-keep",
        "--health-artifacts-to-keep",
        "--coverage-artifacts-to-keep",
        "--heatmap-artifacts-to-keep",
        "--hardening-artifacts-to-keep",
    ):
        if not _has_option(normalized, option):
            normalized.extend([option, keep_value])

    return normalized


def _redirect_to_topic(argv: Sequence[str] | None) -> dict[str, Any]:
    normalized = _normalize_topic_args(argv)
    exit_code = telemetry_topic_runner.run(normalized)
    status = "success" if exit_code == 0 else "failed"
    return {
        "status": status,
        "exit_code": exit_code,
        "redirect": {
            "target": TOPIC_TARGET,
            "argv": normalized,
        },
    }


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    logs_dir: Path


@dataclass
class Options:
    artifacts_to_keep: int
    log_level: str = "INFO"


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True, within_repo=True),
        "logs_dir": PathSpec(field="logs_dir", default=DEFAULT_LOGS_DIR, ensure_dir=True, within_repo=True),
    },
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M")


def plugin_available(mod_name: str) -> bool:
    """Return True if a Python module (pytest plugin) is importable."""
    try:
        import importlib.util as _util

        return _util.find_spec(mod_name) is not None
    except Exception:
        return False


def ensure_dirs(base: Path) -> tuple[Path, Path, Path]:
    logs_dir = base
    failed_dir = base / "pytest_failed_logs"
    skip_dir = base / "pytest_skip_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)
    skip_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir, failed_dir, skip_dir


def _env_flag(name: str, default: bool = True) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    val = val.strip().lower()
    return val not in {"0", "false", "no", "off", ""}


def run_pytest_and_capture(cmd: list[str], cwd: Path) -> tuple[str, int, bool]:
    # Ensure noisy, non-actionable warnings are suppressed at interpreter level.
    env = os.environ.copy()
    warn_entries = [
        "ignore:unclosed database in <sqlite3\\.Connection object:ResourceWarning",
        "ignore:Support for class-based `config` is deprecated:DeprecationWarning",
    ]
    if env.get("PYTHONWARNINGS"):
        env["PYTHONWARNINGS"] = ",".join([env["PYTHONWARNINGS"], *warn_entries])
    else:
        env["PYTHONWARNINGS"] = ",".join(warn_entries)
    # Enable faulthandler in child so SIGUSR1 prints stack traces on hang.
    env.setdefault("PYTHONFAULTHANDLER", "1")
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines: list[str] = []
    suppress_noisy_lines = _env_flag("TEST_LOG_SUPPRESS", default=True)
    assert proc.stdout is not None
    # Watchdog for idle hangs: if no output for N seconds, optionally signal and eventually kill
    idle_timeout = float(os.environ.get("PYTEST_RUNNER_IDLE_TIMEOUT_SEC", "300") or 300)
    escalation_grace = float(os.environ.get("PYTEST_RUNNER_ESCALATION_GRACE_SEC", "30") or 30)
    # Safety: only send SIGUSR1 when explicitly enabled. By default, many processes
    # will terminate on SIGUSR1 unless faulthandler has registered a handler.
    enable_sigusr1 = _env_flag("PYTEST_RUNNER_ENABLE_SIGUSR1", default=False)
    last_output_ts = time.time()
    signaled_dump = False
    terminated = False
    # Use select to avoid blocking indefinitely on readline()
    try:
        import select as _select

        use_select = os.name != "nt"
    except Exception:
        use_select = False
    try:
        while True:
            if use_select:
                ready, _, _ = _select.select([proc.stdout], [], [], 1.0)
                if ready:
                    line = proc.stdout.readline()
                else:
                    line = ""
            else:
                line = proc.stdout.readline()

            if line:
                # Filter out known, non-actionable noise lines before teeing to console
                if not (suppress_noisy_lines and any(s in line for s in _SUPPRESS_LINE_SUBSTR)):
                    sys.stdout.write(line)
                    lines.append(line)
                last_output_ts = time.time()
            else:
                # No new data; check if process exited
                rc = proc.poll()
                if rc is not None:
                    break
                # Check idle timeout
                idle = time.time() - last_output_ts
                if idle >= idle_timeout and not signaled_dump:
                    if enable_sigusr1:
                        # Ask child to dump stacks (if faulthandler registered in child)
                        try:
                            os.kill(proc.pid, signal.SIGUSR1)
                            lines.append(
                                "\n[pytest_log_runner] Idle timeout reached; sent SIGUSR1 to pytest process for stack dump.\n"
                            )
                            sys.stdout.write(lines[-1])
                        except Exception as e:
                            lines.append(f"\n[pytest_log_runner] Failed to signal child: {e}\n")
                            sys.stdout.write(lines[-1])
                    else:
                        # Note idle but avoid sending signals that may terminate pytest
                        note = "\n[pytest_log_runner] Idle timeout reached; SIGUSR1 disabled (set PYTEST_RUNNER_ENABLE_SIGUSR1=1 to enable stack dump).\n"
                        lines.append(note)
                        sys.stdout.write(note)
                    signaled_dump = True
                if signaled_dump and idle >= (idle_timeout + escalation_grace) and not terminated:
                    # Escalate: terminate then kill
                    try:
                        proc.terminate()
                        lines.append("[pytest_log_runner] Escalating: sent SIGTERM to pytest process.\n")
                        sys.stdout.write(lines[-1])
                    except Exception:
                        pass
                    try:
                        proc.wait(timeout=10)
                    except Exception:
                        try:
                            proc.kill()
                            lines.append("[pytest_log_runner] Escalating: sent SIGKILL to pytest process.\n")
                            sys.stdout.write(lines[-1])
                        except Exception:
                            pass
                    terminated = True
                    break
                # Small sleep to avoid tight loop when not using select
                if not use_select:
                    time.sleep(0.1)
        rc = proc.wait()
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
    return "".join(lines), rc, terminated


_SUMMARY_HDR_RE = re.compile(r"short test summary info", re.IGNORECASE)
# Summary-section patterns (appear after 'short test summary info')
_FAILED_LINE_RE = re.compile(r"^FAILED\s+(\S+)(?:\s+-\s+(.*))?$")
_SKIPPED_LINE_RE = re.compile(r"^SKIPPED\s+(\S+)(?:\s+-\s+(.*))?$")
# Live progress-line patterns (while running), e.g. 'tests/foo.py::test_bar FAILED'
_PROG_FAILED_RE = re.compile(r"^(\S+::\S+)\s+FAILED(?:\s|$)")
_PROG_SKIPPED_RE = re.compile(r"^(\S+::\S+)\s+SKIPPED(?:\s*\((.*)\))?(?:\s|$)")


def _iter_summary_lines(all_lines: list[str]) -> Iterable[str]:
    # Find the last occurrence of the summary header and yield subsequent non-empty lines
    start_idx = None
    for i in range(len(all_lines) - 1, -1, -1):
        if _SUMMARY_HDR_RE.search(all_lines[i]):
            start_idx = i + 1
            break
    if start_idx is None:
        return []  # No summary found
    # Skip separators or blank lines after header
    out: list[str] = []
    for line in all_lines[start_idx:]:
        if not line.strip():
            continue
        out.append(line.rstrip("\n"))
    return out


def parse_failed_and_skipped(
    full_output: str,
) -> tuple[list[tuple[str, str | None]], list[tuple[str, str | None]]]:
    """Parse failures/skips from pytest output.

    Strategy:
    1) Prefer the 'short test summary info' section when present.
    2) If absent/empty, fall back to scanning live progress lines.
    """
    lines = full_output.splitlines()
    summary_lines = list(_iter_summary_lines(lines))
    failed: list[tuple[str, str | None]] = []
    skipped: list[tuple[str, str | None]] = []

    for s in summary_lines:
        m_fail = _FAILED_LINE_RE.match(s)
        if m_fail:
            nodeid, msg = m_fail.group(1), m_fail.group(2)
            failed.append((nodeid, msg))
            continue
        m_skip = _SKIPPED_LINE_RE.match(s)
        if m_skip:
            nodeid, msg = m_skip.group(1), m_skip.group(2)
            skipped.append((nodeid, msg))
            continue

    if not failed and not skipped:
        # Fall back to scanning progress lines.
        for s in lines:
            m_pf = _PROG_FAILED_RE.match(s)
            if m_pf:
                nodeid = m_pf.group(1)
                failed.append((nodeid, None))
                continue
            m_ps = _PROG_SKIPPED_RE.match(s)
            if m_ps:
                nodeid = m_ps.group(1)
                reason = m_ps.group(2)
                skipped.append((nodeid, reason))

    return failed, skipped


def parse_junit_failed_and_skipped(
    junit_path: Path,
) -> tuple[list[tuple[str, str | None]], list[tuple[str, str | None]]]:
    """Parse failures/skips from a pytest-generated JUnit XML file.

    Node id built as '<file>::<name>' when 'file' attribute is present; otherwise
    falls back to '<classname>::<name>'.
    """
    failed: list[tuple[str, str | None]] = []
    skipped: list[tuple[str, str | None]] = []
    try:
        root = ElementTree.parse(junit_path).getroot()
    except Exception:
        return failed, skipped
    for suite in root.findall("testsuite"):
        for tc in suite.findall("testcase"):
            file_attr = tc.get("file")
            classname = tc.get("classname")
            name = tc.get("name") or "<unknown>"
            node_left = file_attr or (classname.replace(".", "/") + ".py" if classname else "<unknown>")
            nodeid = f"{node_left}::{name}"
            # Failure or error
            f_el = tc.find("failure")
            if f_el is None:
                f_el = tc.find("error")
            if f_el is not None:
                msg = f_el.get("message") or (f_el.text.strip() if f_el.text else None)
                failed.append((nodeid, msg))
                continue
            s_el = tc.find("skipped")
            if s_el is not None:
                msg = s_el.get("message") or (s_el.text.strip() if s_el.text else None)
                skipped.append((nodeid, msg))
    return failed, skipped


def group_by_file(entries: list[tuple[str, str | None]]) -> dict[str, list[tuple[str, str | None]]]:
    groups: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    for nodeid, msg in entries:
        file_part = nodeid.split("::", 1)[0]
        groups[file_part].append((nodeid, msg))
    return groups


def render_summary_text(title: str, entries: list[tuple[str, str | None]]) -> str:
    # Group by file and sort by descending count, then filename asc
    groups = group_by_file(entries)
    counts = Counter({k: len(v) for k, v in groups.items()})
    sorted_groups = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    lines: list[str] = []
    lines.append(f"{title}")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"Total: {len(entries)}")
    lines.append("")
    if not entries:
        lines.append("<none>")
        return "\n".join(lines) + "\n"
    lines.append("Grouped by file (count desc):")
    for file_name, cnt in sorted_groups:
        lines.append(f"  {cnt:4d}  {file_name}")
    lines.append("")
    lines.append("Items:")
    for nodeid, msg in entries:
        if msg:
            lines.append(f"- {nodeid}  # {msg}")
        else:
            lines.append(f"- {nodeid}")
    return "\n".join(lines) + "\n"


def write_summary(path: Path, title: str, entries: list[tuple[str, str | None]]) -> None:
    path.write_text(render_summary_text(title, entries), encoding="utf-8")


def _build_output_paths(base: Path, ts: str) -> dict[str, Path]:
    return {
        "full_log": base / f"pytest_{ts}.txt",
        "failed_log": base / "pytest_failed_logs" / f"pytest_failed_{ts}.txt",
        "skip_log": base / "pytest_skip_logs" / f"pytest_skip_{ts}.txt",
        "junit": base / f"junit_{ts}.xml",
        "reportlog": base / f"reportlog_{ts}.jsonl",
        "html": base / f"report_{ts}.html",
        "cov_xml": base / f"coverage_{ts}.xml",
        "cov_html_dir": base / f"coverage_html_{ts}",
        "manifest": base / f"manifest_{ts}.json",
    }


def _render_table(entries: list[tuple[str, str | None]], delimiter: str) -> str:
    headers = ["file", "nodeid", "message"]
    rows: list[list[str]] = [headers]
    for nodeid, msg in entries:
        file_part = nodeid.split("::", 1)[0]
        rows.append([file_part, nodeid, msg or ""])
    if delimiter == "\t":
        return "\n".join(delimiter.join(row) for row in rows) + "\n"
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    return buffer.getvalue()


def _collect_junit_metrics(junit_path: Path) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    if not junit_path.exists():
        return metrics
    try:
        root = ElementTree.parse(junit_path).getroot()
    except Exception:
        return metrics
    suite = root.find("testsuite")
    if suite is None:
        return metrics
    metrics.update(
        {
            "tests": int(suite.get("tests", "0")),
            "failures": int(suite.get("failures", "0")),
            "errors": int(suite.get("errors", "0")),
            "skipped": int(suite.get("skipped", "0")),
            "time": float(suite.get("time", "0")),
        }
    )
    return metrics


def _overall_status(exit_code: int, failures: int) -> str:
    if exit_code == 0 and failures == 0:
        return "passed"
    if exit_code == 0 and failures > 0:
        return "unstable"
    return "failed"


def _render_markdown_report(
    *,
    generated_at: datetime,
    run_info: dict[str, Any],
    failures: list[tuple[str, str | None]],
    skips: list[tuple[str, str | None]],
    summary: dict[str, Any],
) -> str:
    lines: list[str] = ["# Pytest Log Capture", ""]
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Run Summary")
    lines.append("")
    lines.append(f"- Overall status: {summary['overall_status']}")
    lines.append(f"- Exit code: {run_info['exit_code']}")
    lines.append(f"- Duration (s): {summary['duration_seconds']:.2f}")
    lines.append(f"- Tests run: {summary['tests_run']}")
    lines.append(f"- Passed: {summary['passed']}")
    lines.append(f"- Errors: {summary['errors']}")
    lines.append(f"- Failures: {summary['failures']}")
    lines.append(f"- Skips: {summary['skips']}")
    lines.append(f"- Command: {' '.join(run_info['command']) if run_info['command'] else '<none>'}")
    lines.append("")

    def _section(title: str, entries: list[tuple[str, str | None]]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not entries:
            lines.append("(none)")
            lines.append("")
            return
        lines.append("<!-- markdownlint-disable MD013 -->")
        for nodeid, message in entries:
            if message:
                lines.append(f"- {nodeid} — {message}")
            else:
                lines.append(f"- {nodeid}")
        lines.append("<!-- markdownlint-enable MD013 -->")
        lines.append("")

    _section("Failures", failures)
    _section("Skips", skips)
    return "\n".join(lines).rstrip() + "\n"


def _pytest_help_supports(options: list[str], cwd: Path) -> dict[str, bool]:
    """Return a map of option -> supported (based on `pytest --help` text)."""
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "--help"],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
        help_text = res.stdout or ""
    except Exception:
        help_text = ""
    support: dict[str, bool] = {}
    for opt in options:
        if opt == "-n":
            # xdist exposes -n/--numprocesses
            support[opt] = ("\n-n " in help_text) or ("--numprocesses" in help_text)
        else:
            support[opt] = opt in help_text
    return support


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run pytest, capture logs, and emit structured artifacts.",
    )
    parser.add_argument("--repo-root", help="Repository root override (defaults to auto-detect)")
    parser.add_argument("--output-dir", help="Directory for structured bundle outputs")
    parser.add_argument("--logs-dir", help="Directory for legacy raw logs and JUnit artifacts")
    parser.add_argument("--cwd", help="Working directory to invoke pytest from")
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention count for structured run directories",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--from-log",
        dest="from_log",
        default=None,
        help="Summarize existing pytest log without executing tests",
    )
    parser.add_argument(
        "--from-junit",
        dest="from_junit",
        default=None,
        help="Summarize existing pytest JUnit XML without executing tests",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Additional pytest args following --",
    )
    return parser.parse_args(argv)


def _strip_after_flag(lst: list[str], flag: str) -> list[str]:
    out: list[str] = []
    skip_next = False
    for item in lst:
        if skip_next:
            skip_next = False
            continue
        if item == flag:
            skip_next = True
            continue
        out.append(item)
    return out


def _legacy_run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    _configure_logging(args.log_level)
    logger = logging.getLogger("run_pytest_log_capture")

    paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
    options = build_standard_options(args, OPTIONS_CONFIG)
    options = replace(options, log_level=args.log_level)

    if not _USING_DEFUSEDXML:
        logger.warning("defusedxml not available; falling back to xml.etree.ElementTree")

    passthrough = [a for a in (args.pytest_args or []) if a != "--"]
    default_cwd = (
        args.cwd
        or os.environ.get("PYTEST_RUNNER_CWD")
        or os.environ.get("GITHUB_WORKSPACE")
        or str(paths.repo_root)
    )
    cwd = Path(default_cwd)

    _logs_dir, _failed_dir, _skip_dir = ensure_dirs(paths.logs_dir)
    ts = timestamp()
    legacy_paths = _build_output_paths(paths.logs_dir, ts)
    junit_path = Path(args.from_junit) if args.from_junit else legacy_paths["junit"]
    reportlog_path = legacy_paths["reportlog"]
    html_report_path = legacy_paths["html"]
    cov_xml_path = legacy_paths["cov_xml"]
    cov_html_dir = legacy_paths["cov_html_dir"]

    summary_mode = bool(args.from_log or args.from_junit)
    idle_timeout = float(os.environ.get("PYTEST_RUNNER_IDLE_TIMEOUT_SEC", "300") or 300)
    escalation_grace = float(os.environ.get("PYTEST_RUNNER_ESCALATION_GRACE_SEC", "30") or 30)
    enable_sigusr1 = _env_flag("PYTEST_RUNNER_ENABLE_SIGUSR1", default=False)

    start_time = datetime.now(timezone.utc)
    end_time = start_time
    output = ""
    rc = 0
    terminated = False
    retried_serial = False
    xdist_used = False
    cov_enabled = False
    reruns_enabled = False
    supports: dict[str, bool] = {}
    junit_metrics: dict[str, Any] = {}
    failures: list[tuple[str, str | None]] = []
    skips: list[tuple[str, str | None]] = []
    full_command: list[str] = passthrough[:]

    junit_path = legacy_paths["junit"]
    reportlog_path = legacy_paths["reportlog"]
    html_report_path = legacy_paths["html"]
    cov_xml_path = legacy_paths["cov_xml"]
    cov_html_dir = legacy_paths["cov_html_dir"]

    if summary_mode:
        if args.from_log:
            match = re.search(r"pytest_(\d{4}-\d{2}-\d{2}_\d{4})\.txt$", args.from_log)
            if match:
                ts = match.group(1)
                legacy_paths = _build_output_paths(paths.logs_dir, ts)
                junit_path = Path(args.from_junit) if args.from_junit else legacy_paths["junit"]
                reportlog_path = legacy_paths["reportlog"]
                html_report_path = legacy_paths["html"]
                cov_xml_path = legacy_paths["cov_xml"]
                cov_html_dir = legacy_paths["cov_html_dir"]
        if args.from_junit:
            match = re.search(r"junit_(\d{4}-\d{2}-\d{2}_\d{4})\.xml$", args.from_junit)
            if match:
                ts = match.group(1)
                legacy_paths = _build_output_paths(paths.logs_dir, ts)
                reportlog_path = legacy_paths["reportlog"]
                html_report_path = legacy_paths["html"]
                cov_xml_path = legacy_paths["cov_xml"]
                cov_html_dir = legacy_paths["cov_html_dir"]
                junit_path = Path(args.from_junit)
        if args.from_log:
            src = Path(args.from_log)
            output = src.read_text(encoding="utf-8", errors="ignore") if src.exists() else ""
            legacy_paths["full_log"] = src
        if output:
            f1, s1 = parse_failed_and_skipped(output)
            failures.extend(f1)
            skips.extend(s1)
        if junit_path.exists():
            f2, s2 = parse_junit_failed_and_skipped(junit_path)
            existing_failures = set(failures)
            for item in f2:
                if item not in existing_failures:
                    failures.append(item)
            existing_skips = set(skips)
            for item in s2:
                if item not in existing_skips:
                    skips.append(item)
            junit_metrics = _collect_junit_metrics(junit_path)
        rc = 1 if failures else 0
    else:
        base_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-vv",
            "-ra",
            "-rs",
            "--color=no",
            "--show-capture=all",
            "--durations=25",
            "--durations-min=0.50",
            f"--junitxml={junit_path}",
        ]
        optional_opts = ["--report-log", "-n", "--cov", "--reruns", "--html", "--timeout"]
        supports = _pytest_help_supports(optional_opts, cwd)
        if supports.get("--report-log", False):
            base_cmd += ["--report-log", str(reportlog_path)]
        if supports.get("-n", False) and _env_flag("PYTEST_RUNNER_DISABLE_XDIST", default=False) is False:
            base_cmd += ["-n", "auto"]
            xdist_used = True
        if supports.get("--cov", False) and _env_flag("PYTEST_RUNNER_DISABLE_COV", default=False) is False:
            base_cmd += [
                "--cov=.",
                "--cov-report",
                f"xml:{cov_xml_path}",
                "--cov-report",
                f"html:{cov_html_dir}",
            ]
            cov_enabled = True
        if supports.get("--reruns", False) and _env_flag("PYTEST_RUNNER_DISABLE_RERUNS", default=False) is False:
            base_cmd += ["--reruns", "1", "--reruns-delay", "2"]
            reruns_enabled = True
        if supports.get("--html", False):
            base_cmd += ["--html", str(html_report_path), "--self-contained-html"]
        if supports.get("--timeout", False) and _env_flag("PYTEST_RUNNER_ENABLE_TIMEOUT", default=True):
            per_test_sec = os.environ.get("PYTEST_RUNNER_TIMEOUT_PER_TEST", "120")
            method = os.environ.get("PYTEST_RUNNER_TIMEOUT_METHOD", "thread")
            base_cmd += ["--timeout", str(per_test_sec), "--timeout-method", method]

        cmd = base_cmd + passthrough
        full_command = cmd
        logger.info("Running: %s (cwd=%s)", " ".join(cmd), cwd)
        output, rc, terminated = run_pytest_and_capture(cmd, cwd)
        end_time = datetime.now(timezone.utc)

        legacy_paths["full_log"].write_text(output, encoding="utf-8")
        logger.info("Saved full log: %s", legacy_paths["full_log"])

        failures, skips = parse_failed_and_skipped(output)
        logger.info("Expected JUnit XML: %s", junit_path)

        exited_by_signal = isinstance(rc, int) and rc < 0
        if (terminated or exited_by_signal) and xdist_used and _env_flag("PYTEST_RUNNER_FALLBACK_SERIAL", default=True):
            try:
                logger.warning(
                    "Detected hang/termination%s with xdist; retrying in serial mode without -n",
                    " (signal)" if exited_by_signal else "",
                )
                cmd_serial = _strip_after_flag(cmd, "-n")
                out2, rc2, _ = run_pytest_and_capture(cmd_serial, cwd)
                with legacy_paths["full_log"].open("a", encoding="utf-8") as fh:
                    fh.write("\n[pytest_log_runner] Retried serial run output begins below:\n\n")
                    fh.write(out2)
                output += "\n[pytest_log_runner] Retried serial run appended above.\n"
                rc = rc2
                retried_serial = True
                end_time = datetime.now(timezone.utc)
                failures, skips = parse_failed_and_skipped(output)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Serial fallback failed: %s", exc)

        junit_metrics = _collect_junit_metrics(junit_path)
    # End execute flow

    generated_at = datetime.now(timezone.utc)
    duration_seconds = max((end_time - start_time).total_seconds(), 0.0)
    junit_tests = int(junit_metrics.get("tests", 0)) if junit_metrics else 0
    junit_errors = int(junit_metrics.get("errors", 0)) if junit_metrics else 0
    inferred_total = max(junit_tests, len(failures) + len(skips))
    total_tests = junit_tests or inferred_total
    passed_tests = max(total_tests - len(failures) - junit_errors - len(skips), 0)

    summary_payload = {
        "overall_status": _overall_status(rc, len(failures)),
        "failures": len(failures),
        "skips": len(skips),
        "errors": junit_errors,
        "passed": passed_tests,
        "tests_run": total_tests,
        "duration_seconds": duration_seconds,
        "junit": junit_metrics,
    }

    run_info = {
        "mode": "summarize" if summary_mode else "execute",
        "timestamp_utc": generated_at.isoformat(timespec="seconds"),
        "command": full_command,
        "exit_code": rc,
        "terminated": terminated,
        "retried_serial": retried_serial,
        "xdist_used": xdist_used,
        "cov_enabled": cov_enabled,
        "reruns_enabled": reruns_enabled,
        "cwd": str(cwd),
        "idle_timeout_seconds": idle_timeout,
        "escalation_grace_seconds": escalation_grace,
        "enable_sigusr1": enable_sigusr1,
    }

    failure_summary_text = render_summary_text("FAILED tests", failures)
    skip_summary_text = render_summary_text("SKIPPED tests", skips)
    failures_tsv = _render_table(failures, "\t")
    skips_tsv = _render_table(skips, "\t")
    failures_csv = _render_table(failures, ",")
    skips_csv = _render_table(skips, ",")
    markdown_payload = _render_markdown_report(
        generated_at=generated_at,
        run_info=run_info,
        failures=failures,
        skips=skips,
        summary=summary_payload,
    )

    bundle_summary = {
        "overall_status": summary_payload["overall_status"],
        "failures": summary_payload["failures"],
        "skips": summary_payload["skips"],
        "errors": summary_payload["errors"],
        "passed": summary_payload["passed"],
        "tests_run": summary_payload["tests_run"],
        "duration_seconds": summary_payload["duration_seconds"],
        "exit_code": rc,
    }

    report_payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at.isoformat(timespec="seconds"),
        "run": run_info,
        "summary": summary_payload,
        "failures": [{"nodeid": nodeid, "message": msg} for nodeid, msg in failures],
        "skips": [{"nodeid": nodeid, "message": msg} for nodeid, msg in skips],
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "using_defusedxml": _USING_DEFUSEDXML,
            "plugins": supports,
        },
        "provenance": {
            "legacy": {
                "full_log": str(legacy_paths["full_log"]),
                "failed_summary": str(legacy_paths["failed_log"]),
                "skip_summary": str(legacy_paths["skip_log"]),
                "junit": str(junit_path),
                "reportlog": str(reportlog_path),
                "html_report": str(html_report_path),
                "coverage_xml": str(cov_xml_path),
                "coverage_html_dir": str(cov_html_dir),
            }
        },
    }

    artifacts: list[ReportArtifact] = [
        ReportArtifact("report.json", "latest_report.json", "json", report_payload),
        ReportArtifact("report.md", "latest_report.md", "text", markdown_payload),
        ReportArtifact("bundle_summary.json", "latest_bundle_summary.json", "json", bundle_summary),
        ReportArtifact("failures.tsv", "latest_failures.tsv", "text", failures_tsv),
        ReportArtifact("failures.csv", "latest_failures.csv", "text", failures_csv),
        ReportArtifact("skips.tsv", "latest_skips.tsv", "text", skips_tsv),
        ReportArtifact("skips.csv", "latest_skips.csv", "text", skips_csv),
        ReportArtifact("failures.txt", "latest_failures.txt", "text", failure_summary_text),
        ReportArtifact("skips.txt", "latest_skips.txt", "text", skip_summary_text),
        ReportArtifact("full_log.txt", "latest_full_log.txt", "text", output),
    ]

    if junit_path.exists():
        artifacts.append(
            ReportArtifact("junit.xml", "latest_junit.xml", "text", junit_path.read_text(encoding="utf-8", errors="ignore"))
        )

    write_result = write_report_artifacts(
        stem=RUN_STEM,
        timestamp=generated_at,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )
    logger.info("Structured artifacts written to %s", write_result.run_dir)

    write_summary(legacy_paths["failed_log"], "FAILED tests", failures)
    write_summary(legacy_paths["skip_log"], "SKIPPED tests", skips)
    logger.info("Saved failed summary: %s", legacy_paths["failed_log"])
    logger.info("Saved skipped summary: %s", legacy_paths["skip_log"])

    return {
        "status": "success" if rc == 0 else "failed",
        "exit_code": rc,
        "run_dir": str(write_result.run_dir),
        "report_json": str(write_result.artifacts["report.json"]),
        "report_md": str(write_result.artifacts["report.md"]),
        "bundle_summary": str(write_result.artifacts["bundle_summary.json"]),
        "failures_tsv": str(write_result.artifacts["failures.tsv"]),
        "skips_tsv": str(write_result.artifacts["skips.tsv"]),
        "summary": summary_payload,
    }


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    if not _use_legacy_runner(argv):
        return _redirect_to_topic(argv)
    return _legacy_run(argv)


def main(argv: Sequence[str] | None = None) -> int:
    result = run(argv)
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
