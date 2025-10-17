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
* logs_dir: <cwd>/.repo_studios/pytest_logs
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
import logging
import os
import re
import signal
import subprocess
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
# Use defusedxml for secure XML parsing
from defusedxml import ElementTree

# Patterns to suppress from console/log output (non-actionable noise)
_SUPPRESS_LINE_SUBSTR = [
    # Python 3.13 + coverage.py/ast: sqlite connection ResourceWarnings during teardown
    "ResourceWarning: unclosed database in <sqlite3.Connection object",
    "ResourceWarning: Enable tracemalloc to get the object allocation traceback",
    # Follow-up context lines emitted with those warnings
    'self.code = compile(text, filename, "exec", dont_inherit=True)',
    "return compile(source, filename, mode, flags",
]


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

        use_select = True
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
                        lines.append(
                            "[pytest_log_runner] Escalating: sent SIGTERM to pytest process.\n"
                        )
                        sys.stdout.write(lines[-1])
                    except Exception:
                        pass
                    try:
                        proc.wait(timeout=10)
                    except Exception:
                        try:
                            proc.kill()
                            lines.append(
                                "[pytest_log_runner] Escalating: sent SIGKILL to pytest process.\n"
                            )
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
            node_left = file_attr or (
                classname.replace(".", "/") + ".py" if classname else "<unknown>"
            )
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


def write_summary(path: Path, title: str, entries: list[tuple[str, str | None]]) -> None:
    # Group by file and sort by descending count, then filename asc
    groups = group_by_file(entries)
    counts = Counter({k: len(v) for k, v in groups.items()})
    sorted_groups = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    with path.open("w", encoding="utf-8") as f:
        f.write(f"{title}\n")
        f.write(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Total: {len(entries)}\n\n")
        if not entries:
            f.write("<none>\n")
            return
        f.write("Grouped by file (count desc):\n")
        for file_name, cnt in sorted_groups:
            f.write(f"  {cnt:4d}  {file_name}\n")
        f.write("\nItems:\n")
        for nodeid, msg in entries:
            if msg:
                f.write(f"- {nodeid}  # {msg}\n")
            else:
                f.write(f"- {nodeid}\n")


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run pytest, capture logs, and write failed/skip summaries.",
    )
    parser.add_argument(
        "--cwd",
        default=os.environ.get("PYTEST_RUNNER_CWD")
        or os.environ.get("GITHUB_WORKSPACE")
        or str(Path.cwd()),
        help="Working directory to run pytest from",
    )
    parser.add_argument(
        "--logs-dir",
        default=os.environ.get("PYTEST_LOGS_DIR")
        or str(Path(os.environ.get("GITHUB_WORKSPACE") or Path.cwd())
                / ".repo_studios/pytest_logs"),
        help="Directory to store logs",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Additional pytest args after --",
    )
    parser.add_argument(
        "--from-log",
        dest="from_log",
        default=None,
        help="Summarize from an existing full pytest log (no test run)",
    )
    parser.add_argument(
        "--from-junit",
        dest="from_junit",
        default=None,
        help="Summarize from an existing JUnit XML (no test run)",
    )
    args = parser.parse_args(argv)

    # Extract pass-through args after "--"
    passthrough = []
    if args.pytest_args:
        # argparse includes the leading --; strip it if present
        passthrough = [a for a in args.pytest_args if a != "--"]

    cwd = Path(args.cwd)
    logs_dir, failed_dir, skip_dir = ensure_dirs(Path(args.logs_dir))
    ts = timestamp()

    full_log_path = logs_dir / f"pytest_{ts}.txt"
    failed_log_path = failed_dir / f"pytest_failed_{ts}.txt"
    skip_log_path = skip_dir / f"pytest_skip_{ts}.txt"

    junit_path = logs_dir / f"junit_{ts}.xml"
    reportlog_path = logs_dir / f"reportlog_{ts}.jsonl"
    html_report_path = logs_dir / f"report_{ts}.html"
    cov_xml_path = logs_dir / f"coverage_{ts}.xml"
    cov_html_dir = logs_dir / f"coverage_html_{ts}"
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
    # Optional plugin outputs (detected via pytest --help in the same interpreter)
    optional_opts = ["--report-log", "-n", "--cov", "--reruns", "--html", "--timeout"]
    supports = _pytest_help_supports(optional_opts, cwd)
    xdist_used = False
    cov_enabled = False
    reruns_enabled = False
    if supports.get("--report-log", False):
        base_cmd += ["--report-log", str(reportlog_path)]
    # Allow disabling xdist via env if it causes instability/hangs
    if (
        supports.get("-n", False)
        and _env_flag("PYTEST_RUNNER_DISABLE_XDIST", default=False) is False
    ):
        base_cmd += ["-n", "auto"]
        xdist_used = True
    if supports.get("--cov", False):
        if _env_flag("PYTEST_RUNNER_DISABLE_COV", default=False) is False:
            base_cmd += [
                "--cov=.",
                "--cov-report",
                f"xml:{cov_xml_path}",
                "--cov-report",
                f"html:{cov_html_dir}",
            ]
            cov_enabled = True
    if supports.get("--reruns", False):
        if _env_flag("PYTEST_RUNNER_DISABLE_RERUNS", default=False) is False:
            base_cmd += ["--reruns", "1", "--reruns-delay", "2"]
            reruns_enabled = True
    if supports.get("--html", False):
        base_cmd += ["--html", str(html_report_path), "--self-contained-html"]
    # pytest-timeout plugin support (if available via --help)
    if supports.get("--timeout", False) and _env_flag("PYTEST_RUNNER_ENABLE_TIMEOUT", default=True):
        per_test_sec = os.environ.get("PYTEST_RUNNER_TIMEOUT_PER_TEST", "120")
        method = os.environ.get("PYTEST_RUNNER_TIMEOUT_METHOD", "thread")
        base_cmd += ["--timeout", str(per_test_sec), "--timeout-method", method]

    # If no selectors provided, let pytest.ini testpaths control discovery
    # Summarize-only mode: from existing log/junit without running pytest
    if args.from_log or args.from_junit:
        # Determine timestamp from provided filenames when possible
        if args.from_log:
            m_ts = re.search(r"pytest_(\d{4}-\d{2}-\d{2}_\d{4})\.txt$", args.from_log)
            if m_ts:
                ts = m_ts.group(1)
        if args.from_junit:
            m_ts2 = re.search(r"junit_(\d{4}-\d{2}-\d{2}_\d{4})\.xml$", args.from_junit)
            if m_ts2:
                ts = m_ts2.group(1)
        full_log_path = Path(args.from_log) if args.from_log else full_log_path
        junit_path = Path(args.from_junit) if args.from_junit else junit_path
        # Read sources
        output = ""
        if args.from_log:
            output = Path(args.from_log).read_text(encoding="utf-8", errors="ignore")
        failed, skipped = ([], [])
        if output:
            f1, s1 = parse_failed_and_skipped(output)
            failed.extend(f1)
            skipped.extend(s1)
        if args.from_junit and Path(junit_path).exists():
            f2, s2 = parse_junit_failed_and_skipped(Path(junit_path))
            # Merge, avoid duplicates
            seen = set(failed)
            for item in f2:
                if item not in seen:
                    failed.append(item)
            seen = set(skipped)
            for item in s2:
                if item not in seen:
                    skipped.append(item)
        # Write summaries
        write_summary(failed_dir / f"pytest_failed_{ts}.txt", "FAILED tests", failed)
        write_summary(skip_dir / f"pytest_skip_{ts}.txt", "SKIPPED tests", skipped)
        logging.info("Summaries written for timestamp %s (from existing artifacts)", ts)
        return 1 if failed else 0

    cmd = base_cmd + (passthrough or [])

    logging.info("Running: %s (cwd=%s)", " ".join(cmd), cwd)
    output, rc, terminated = run_pytest_and_capture(cmd, cwd)

    # Save full output
    with full_log_path.open("w", encoding="utf-8") as f:
        f.write(output)
    logging.info("Saved full log: %s", full_log_path)

    # Parse and write summaries
    failed, skipped = parse_failed_and_skipped(output)
    write_summary(failed_log_path, "FAILED tests", failed)
    write_summary(skip_log_path, "SKIPPED tests", skipped)
    logging.info("Saved failed summary: %s", failed_log_path)
    logging.info("Saved skipped summary: %s", skip_log_path)
    logging.info("Saved JUnit XML: %s", junit_path)

    # If we detected a hang and terminated OR pytest exited due to a signal while using xdist,
    # optionally retry serially (common mitigation for xdist end-of-suite stalls).
    exited_by_signal = isinstance(rc, int) and rc < 0
    if (
        (terminated or exited_by_signal)
        and xdist_used
        and _env_flag("PYTEST_RUNNER_FALLBACK_SERIAL", default=True)
    ):
        try:
            logging.warning(
                "Detected hang/termination%s with xdist; retrying in serial mode without -n",
                " (signal)" if exited_by_signal else "",
            )
            cmd_serial = [c for c in cmd if c != "-n"]

            # Remove the automatic value following -n if present
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

            cmd_serial = _strip_after_flag(cmd_serial, "-n")
            out2, rc2, _ = run_pytest_and_capture(cmd_serial, cwd)
            # Append retry output to the same log for continuity
            with full_log_path.open("a", encoding="utf-8") as f:
                f.write("\n[pytest_log_runner] Retried serial run output begins below:\n\n")
                f.write(out2)
            output += "\n[pytest_log_runner] Retried serial run appended above.\n"
            rc = rc2
        except Exception as e:
            logging.exception("Serial fallback failed: %s", e)

    # Write a manifest for longitudinal comparisons
    try:
        import json as _json
        import platform as _platform

        manifest = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "cwd": str(cwd),
            "python": sys.version.split()[0],
            "platform": _platform.platform(),
            "pytest_cmd": cmd,
            "artifacts": {
                "full_log": str(full_log_path),
                "junit_xml": str(junit_path),
                "reportlog": str(reportlog_path) if plugin_available("pytest_reportlog") else None,
                "html_report": str(html_report_path) if supports.get("--html", False) else None,
                "coverage_xml": str(cov_xml_path) if cov_enabled else None,
                "coverage_html": str(cov_html_dir) if cov_enabled else None,
            },
            "plugins": {
                "xdist": xdist_used,
                "cov": cov_enabled,
                "reruns": reruns_enabled,
                "reportlog": supports.get("--report-log", False),
                "html": supports.get("--html", False),
            },
            "exit_code": rc,
            "terminated": terminated,
        }
        # Annotate signal termination info if applicable
        if isinstance(rc, int) and rc < 0:
            manifest["signal"] = abs(rc)
        try:
            suite = ElementTree.parse(junit_path).getroot().find("testsuite")
            if suite is not None:
                manifest["junit"] = {
                    "tests": int(suite.get("tests", "0")),
                    "failures": int(suite.get("failures", "0")),
                    "errors": int(suite.get("errors", "0")),
                    "skipped": int(suite.get("skipped", "0")),
                    "time": float(suite.get("time", "0")),
                }
        except Exception as e:
            logging.warning("Failed to parse JUnit XML: %s", e)

        manifest_path = logs_dir / f"manifest_{ts}.json"
        with manifest_path.open("w", encoding="utf-8") as mf:
            _json.dump(manifest, mf, indent=2)
        logging.info("Saved manifest: %s", manifest_path)
    except Exception as e:
        logging.warning("Failed to write manifest: %s", e)

    # Return the actual pytest exit code
    return rc


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    raise SystemExit(main())
