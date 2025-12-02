#!/usr/bin/env python3
"""
Health Suite Orchestrator

Runs repo health scripts sequentially, always continuing to the next step.
Each step is considered complete whether it succeeds or fails; failures are
logged to per-step error logs and included in a final status summary.

Requested order (with tolerant filename matching for historical typos):
    1) batch_clean.py
    2) run_pytest_log_capture.py (alias pytest_log_runner.py)
    3) collect_test_log_reports.py
    4) scan_monkey_patches.py
    5) generate_dependency_hygiene_report.py (alias dep_hygiene_report.py)
    6) analyze_monkey_patch_trends.py (alias compare_monkey_patch_trends.py)
    7) validate_import_boundaries.py (alias check_import_boundaries.py)
    8) generate_test_log_health_report.py
    9) generate_typecheck_report.py (alias typecheck_report.py)
 10) refresh_mypy_baselines.py
 11) generate_import_graph_report.py (alias import_graph_report.py)
 12) churn_complexity_heatmap.py
 13) generate_lizard_report.py
 14) dump_faulthandler_once.py (best-effort)
 15) generate_fault_artifacts.py (best-effort)
 16) scripts/health/faulthandler_aggregate.py (best-effort)
 17) scripts/ci_faulthandler_gate.py (best-effort, report-only)
 18) anchor_health_report.py
 19) health_suite_summary.py

Outputs:
- Per-step logs under .repo_studios/reports/orchestrator_logs/health_suite_logs/<timestamp>/
- A machine-readable status.json and a brief status.md under the same folder

Exit code: always 0 (so the suite never aborts mid-chain). Inspect status for
per-step results.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT = REPO_ROOT / ".repo_studios"
repo_DIR = ROOT
REPORTS_ROOT = repo_DIR / "reports"
LOG_BASE = REPORTS_ROOT / "orchestrator_logs" / "health_suite_logs"
PYTEST_LOGS_DIR = REPORTS_ROOT / "orchestrator_logs" / "pytest_log_capture_logs"
LEGACY_LOG_BASE = repo_DIR / "health_suite" / "logs"
FAULT_RUN_ROOT = REPORTS_ROOT / "orchestrator_logs" / "faulthandler_logs"
LEGACY_FAULT_ROOT = repo_DIR / "faulthandler"
SUMMARY_BASE = REPORTS_ROOT / "summarizer_reports" / "health_suite_summary_reports"
LEGACY_SUMMARY_BASE = repo_DIR / "health_suite"

SCRIPT_ALIASES: dict[str, str] = {
    "batch_clean.py": "scripts/orchestrators/run_batch_cleanup.py",
    "pytest_log_runner.py": "scripts/orchestrators/run_pytest_log_capture.py",
    "scan_monkey_patches.py": "scripts/producers/scan_monkey_patches.py",
    "dep_hygiene_report.py": "scripts/producers/generate_dependency_hygiene_report.py",
    "compare_monkey_patch_trends.py": "scripts/aggregators/analyze_monkey_patch_trends.py",
    "check_import_boundaries.py": "scripts/producers/validate_import_boundaries.py",
    "check_import_boundries.py": "scripts/producers/validate_import_boundaries.py",
    "import_graph_report.py": "scripts/producers/generate_import_graph_report.py",
    "churn_complexity_heatmap.py": "scripts/aggregators/generate_churn_complexity_heatmap.py",
    "typecheck_report.py": "scripts/producers/generate_typecheck_report.py",
    "lizard_report.py": "scripts/producers/generate_lizard_report.py",
    "dump_faulthandler_once.py": "scripts/utilities/dump_faulthandler_snapshot.py",
    "generate_fault_artifacts.py": "scripts/consumers/generate_fault_artifacts.py",
    "health_suite_summary.py": "scripts/summarizers/summarize_health_suite.py",
    "heath_suite_summary.py": "scripts/summarizers/summarize_health_suite.py",
    "anchor_health_report.py": "scripts/consumers/generate_anchor_health_report.py",
    "refresh_mypy_baselines.py": "scripts/utilities/refresh_mypy_baselines.py",
}

USING_LEGACY = False


def _use_legacy_pipeline() -> bool:
    raw = os.getenv("HEALTH_SUITE_USE_LEGACY")
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _ts_to_iso(ts: str) -> str | None:
    try:
        parsed = datetime.strptime(ts, "%Y-%m-%d_%H%M")
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc).isoformat()


def _make_topic_steps(ts: str) -> list["Step"]:
    py = exe()
    repo_root = str(REPO_ROOT)
    log_level = os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO")
    orchestrators_root = ROOT / "command_center" / "scripts" / "orchestrators"
    iso_ts = _ts_to_iso(ts)

    def _build_step(name: str, relative_path: str, extra_args: Sequence[str] | None = None) -> "Step":
        script_path = orchestrators_root / relative_path
        if not script_path.exists():
            return Step(
                name=f"{name}(MISSING)",
                argv=[
                    py,
                    "-c",
                    (
                        f"import sys; print('missing {relative_path}', file=sys.stderr); sys.exit(1)"
                    ),
                ],
                optional=True,
            )
        argv = [
            py,
            str(script_path),
            "--repo-root",
            repo_root,
            "--log-level",
            log_level,
        ]
        if iso_ts:
            argv.extend(["--timestamp", iso_ts])
        if extra_args:
            argv.extend(extra_args)
        return Step(name=name, argv=argv)

    steps: list[Step] = []
    steps.append(
        _build_step(
            "dependency_import_hygiene",
            "run_dependency_import_hygiene.py",
            ["--trigger-batch-cleanup", "--refresh-mypy-baselines"],
        )
    )
    steps.append(_build_step("test_execution_telemetry", "run_test_execution_telemetry.py"))
    steps.append(_build_step("docs_health_overview", "run_docs_health_overview.py"))
    steps.append(_build_step("fault_diagnostics_overview", "run_fault_diagnostics_overview.py"))
    steps.append(_build_step("monkey_patch_oversight", "run_monkey_patch_oversight.py"))
    steps.append(_build_step("standards_integrity", "run_standards_integrity.py"))
    return steps


def _ts_default() -> str:
    return time.strftime("%Y-%m-%d_%H%M")


def exe() -> str:
    return sys.executable or "python"


def _candidate_paths(name: str) -> list[Path]:
    parts = [name]
    alias = SCRIPT_ALIASES.get(name)
    if alias:
        parts.append(alias)
    seen: set[Path] = set()
    resolved: list[Path] = []
    for part in parts:
        option = Path(part)
        candidates: list[Path]
        if option.is_absolute():
            candidates = [option]
        else:
            candidates = [repo_DIR / option, REPO_ROOT / option]
        for candidate in candidates:
            try:
                real = candidate.resolve()
            except FileNotFoundError:
                real = candidate
            if real in seen:
                continue
            seen.add(real)
            resolved.append(real)
    return resolved


def find_script(*candidates: str) -> Path | None:
    for name in candidates:
        for candidate in _candidate_paths(name):
            if candidate.exists():
                return candidate
    return None


@dataclass
class Step:
    name: str
    argv: list[str]
    optional: bool = False  # if missing script, mark as skipped (not error)
    env: dict[str, str] | None = None  # optional env overrides for this step
    timeout_sec: float | None = None  # liberal per-step timeout; None means use global default
    heartbeat_sec: float | None = None  # emit periodic heartbeat while running


def make_steps(ts: str) -> list[Step]:
    global USING_LEGACY
    if not _use_legacy_pipeline():
        USING_LEGACY = False
        return _make_topic_steps(ts)
    USING_LEGACY = True
    py = exe()
    steps: list[Step] = []
    # Prepare a shared FAULT_OUTDIR for fault steps so all child processes
    # write into a deterministic run folder for this orchestrator execution.
    fault_base = FAULT_RUN_ROOT / ts
    try:
        fault_base.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    legacy_fault_base = LEGACY_FAULT_ROOT / ts
    try:
        legacy_fault_base.mkdir(parents=True, exist_ok=True)
        marker = legacy_fault_base / "MOVED.txt"
        if not marker.exists():
            marker.write_text(f"Fault artifacts now live at {fault_base.resolve()}\n", encoding="utf-8")
    except Exception:
        pass
    fault_env = {
        "FAULT_ENABLE": "1",
        "FAULT_OUTDIR": str(fault_base),
        "FAULT_LEGACY_OUTDIR": str(legacy_fault_base),
        # Avoid background repeating timers during the suite run
        "FAULT_DUMP_LATER": os.getenv("FAULT_DUMP_LATER", "0"),
    }

    # 1) batch_clean.py
    script = find_script("batch_clean.py")
    if script:
        steps.append(
            Step(
                name="batch_clean",
                argv=[py, str(script), "-t", "agents", "-t", "api", "-t", "scripts", "--no-pytest"],
            )
        )
    else:
        steps.append(
            Step(
                name="batch_clean(MISSING)",
                argv=[py, "-c", "print('missing batch_clean.py')"],
                optional=True,
            )
        )

    # 2) pytest log capture orchestrator
    script = find_script("scripts/orchestrators/run_pytest_log_capture.py", "pytest_log_runner.py")
    steps.append(
        Step(
            name="pytest_logs",
            argv=[py, str(script)] if script else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 3) collect_test_log_reports.py
    producer_script = ROOT / "scripts/producers/collect_test_log_reports.py"
    steps.append(
        Step(
            name="collect_test_log_reports",
            argv=[
                py,
                str(producer_script) if producer_script.exists() else "-c",
                *(
                    [
                        "--logs-dir",
                        str(PYTEST_LOGS_DIR),
                        "--output-dir",
                        str(repo_DIR / "reports/producer_reports/test_log_reports"),
                        "--artifacts-to-keep",
                        "10",
                        "--log-level",
                        os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO"),
                    ]
                    if producer_script.exists()
                    else [
                        "import sys; print('missing collect_test_log_reports.py', file=sys.stderr); sys.exit(1)",
                    ]
                ),
            ],
            optional=not producer_script.exists(),
        )
    )

    # 4) scan_monkey_patches.py
    script = find_script("scan_monkey_patches.py")
    steps.append(
        Step(
            name="scan_monkey_patches",
            argv=[
                py,
                str(script),
                "--repo-root",
                ".",
                "--output-dir",
                str(repo_DIR / "reports/producer_reports/monkey_patch_scans"),
                "--log-level",
                os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO"),
                "--with-git",
                "--strict",
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 5) generate_dependency_hygiene_report.py
    script = find_script("dep_hygiene_report.py")
    steps.append(
        Step(
            name="dep_health",
            argv=[
                py,
                str(script),
                "--repo-root",
                ".",
                "--output-dir",
                str(repo_DIR / "reports/producer_reports/dependency_hygiene_reports"),
                "--log-level",
                os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO"),
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 6) analyze_monkey_patch_trends.py
    script = find_script("compare_monkey_patch_trends.py")
    steps.append(
        Step(
            name="compare_monkey_patch_trends",
            argv=[
                py,
                str(script),
                "--base-dir",
                str(repo_DIR / "reports/producer_reports/monkey_patch_scans"),
                *(["--verbose"] if os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO").upper() == "DEBUG" else []),
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 7) validate_import_boundaries.py (typo-tolerant)
    script = find_script("check_import_boundaries.py", "check_import_boundries.py")
    steps.append(
        Step(
            name="check_import_boundaries",
            argv=[
                py,
                str(script),
                "--repo-root",
                ".",
                "--log-level",
                os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO"),
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 8) generate_test_log_health_report.py (consumer)
    consumer_script = ROOT / "scripts/consumers/generate_test_log_health_report.py"
    steps.append(
        Step(
            name="test_log_health_report",
            argv=[
                py,
                str(consumer_script) if consumer_script.exists() else "-c",
                "--logs-dir",
                str(PYTEST_LOGS_DIR),
                "--output-base",
                str(repo_DIR / "reports/consumer_reports/test_log_health_reports"),
                "--producer-report",
                str(repo_DIR / "reports/producer_reports/test_log_reports/latest_report.json"),
                "--log-level",
                os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO"),
                "--artifacts-to-keep",
                "5",
            ]
            if consumer_script.exists()
            else [
                py,
                "-c",
                "import sys; print('missing generate_test_log_health_report.py', file=sys.stderr); sys.exit(1)",
            ],
            optional=not consumer_script.exists(),
        )
    )

    # 9) generate_typecheck_report.py — run mypy and produce artifacts (optional)
    script = find_script("typecheck_report.py")
    steps.append(
        Step(
            name="typecheck_report",
            argv=[
                py,
                str(script) if script else "-c",
                *(
                    [
                        "--repo-root",
                        ".",
                        "--output-dir",
                        str(repo_DIR / "reports/producer_reports/typecheck_reports"),
                        "--timestamp",
                        ts,
                        "--log-level",
                        os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO"),
                    ]
                    if script
                    else [
                        "import sys; print('missing generate_typecheck_report.py', file=sys.stderr); sys.exit(1)",
                    ]
                ),
            ],
            optional=script is None,
        )
    )

    # 10) refresh_mypy_baselines.py (utilities)
    script = find_script("refresh_mypy_baselines.py")
    steps.append(
        Step(
            name="refresh_mypy_baselines",
            argv=[
                py,
                str(script) if script else "-c",
                *(
                    [
                        "--repo-root",
                        ".",
                        "--log-level",
                        os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO"),
                    ]
                    if script
                    else [
                        "import sys; print('missing refresh_mypy_baselines.py', file=sys.stderr); sys.exit(1)",
                    ]
                ),
            ],
            optional=script is None,
        )
    )

    # 11) generate_import_graph_report.py
    script = find_script("import_graph_report.py")
    steps.append(
        Step(
            name="import_graph_report",
            argv=[
                py,
                str(script),
                "--repo-root",
                ".",
                "--output-dir",
                str(repo_DIR / "reports/producer_reports/import_graph_reports"),
                "--log-level",
                os.environ.get("COMMAND_CENTER_LOG_LEVEL", "INFO"),
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 12) churn_complexity_heatmap.py
    script = find_script("churn_complexity_heatmap.py")
    steps.append(
        Step(
            name="churn_complexity_heatmap",
            argv=[
                py,
                str(script),
                "--repo-root",
                ".",
                "--output-base",
                str(repo_DIR / "reports/aggregator_reports/churn_complexity_heatmap"),
                "--logs-dir",
                str(PYTEST_LOGS_DIR),
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 13) lizard complexity report (optional but expected in CI)
    lizard_script = repo_DIR / "lizard_report.py"
    steps.append(
        Step(
            name="lizard_report",
            argv=[
                py,
                str(lizard_script),
                "--repo-root",
                ".",
                "--timestamp",
                ts,
            ]
            if lizard_script.exists()
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=not lizard_script.exists(),
        )
    )

    # 14) one-time faulthandler dump (best-effort)
    script = find_script("dump_faulthandler_once.py")
    steps.append(
        Step(
            name="fault_dump_once",
            argv=[py, str(script)] if script else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
            env=fault_env,
        )
    )

    # 15) faulthandler artifacts generator (best-effort)
    script = find_script("generate_fault_artifacts.py")
    steps.append(
        Step(
            name="fault_artifacts",
            argv=[py, str(script)] if script else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
            env=fault_env,
        )
    )

    # 16) faulthandler aggregator under scripts/health (best-effort)
    agg_script = Path("scripts/health/faulthandler_aggregate.py")
    steps.append(
        Step(
            name="fault_aggregate",
            argv=[py, str(agg_script)] if agg_script.exists() else [py, "-c", "import sys; sys.exit(1)"],
            optional=not agg_script.exists(),
            env=fault_env,
        )
    )

    # 17) ci gate (best-effort, non-blocking in the suite)
    gate_script = Path("scripts/ci_faulthandler_gate.py")
    steps.append(
        Step(
            name="fault_gate",
            argv=[py, str(gate_script)] if gate_script.exists() else [py, "-c", "import sys; sys.exit(1)"],
            optional=not gate_script.exists(),
            env=fault_env,
        )
    )

    # 18) anchor health (generate timestamped anchor report artifacts)
    anchor_script = repo_DIR / "anchor_health_report.py"
    steps.append(
        Step(
            name="anchor_health",
            argv=[py, str(anchor_script)] if anchor_script.exists() else [py, "-c", "import sys; sys.exit(1)"],
            optional=not anchor_script.exists(),
        )
    )

    # 19) health_suite_summary.py (typo-tolerant) — now includes anchor health section
    script = find_script("health_suite_summary.py", "heath_suite_summary.py")
    out_dir = SUMMARY_BASE
    steps.append(
        Step(
            name="health_suite_summary",
            argv=[
                py,
                str(script) if script else "-c",
                *(
                    [
                        "--repo-root",
                        ".",
                        "--output-dir",
                        str(out_dir),
                        "--timestamp",
                        ts,
                    ]
                    if script
                    else [
                        "import sys; print('missing health_suite_summary.py', file=sys.stderr); sys.exit(1)",
                    ]
                ),
            ],
            optional=script is None,
        )
    )

    return steps


def run_step(
    step: Step,
    env: dict | None = None,
    log_dir: Path = Path(),
    live: bool = False,
    default_timeout_sec: float | None = None,
    default_heartbeat_sec: float | None = None,
) -> dict:
    start = time.time()
    log_dir.mkdir(parents=True, exist_ok=True)
    safe_name = step.name.replace("/", "_")
    log_path = log_dir / f"{safe_name}.log"
    err_path = log_dir / f"{safe_name}.err.log"
    current_path = log_dir / "current_step.txt"
    status: dict = {
        "name": step.name,
        "argv": step.argv,
        "start": start,
    }

    if step.optional and "-c" in step.argv and "missing" in " ".join(step.argv):
        status.update({"skipped": True, "reason": "missing script"})
        with log_path.open("w", encoding="utf-8") as f:
            f.write("[SKIP] Missing script — step marked as skipped.\n")
        return status

    try:
        # Update current step indicator
        current_path.write_text(step.name + "\n", encoding="utf-8")
        logging.info("[start] %s", step.name)

        if live:
            # Stream output to console and file, combining stderr into stdout for ordering
            with (
                log_path.open("w", encoding="utf-8") as out_f,
                err_path.open("w", encoding="utf-8") as err_f,
            ):
                proc = subprocess.Popen(
                    step.argv,
                    cwd=str(REPO_ROOT),
                    env={**os.environ, **(env or {})},
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert proc.stdout is not None
                # Heartbeat and timeout supervisor
                timeout_sec = step.timeout_sec if step.timeout_sec is not None else default_timeout_sec
                heartbeat_sec = step.heartbeat_sec if step.heartbeat_sec is not None else default_heartbeat_sec
                stop_evt = threading.Event()

                def _heartbeat():
                    # Emit heartbeat and enforce timeout
                    while not stop_evt.wait(heartbeat_sec or 0):
                        if proc.poll() is not None:
                            break
                        elapsed = time.time() - start
                        msg = f"[HEARTBEAT] {step.name} running — elapsed={int(elapsed)}s"
                        logging.info("%s", msg)
                        try:
                            out_f.write(msg + "\n")
                            out_f.flush()
                        except Exception:
                            pass
                        if timeout_sec and elapsed > timeout_sec and proc.poll() is None:
                            to_msg = f"[TIMEOUT] {step.name} exceeded {int(timeout_sec)}s — terminating"
                            logging.warning("%s", to_msg)
                            try:
                                err_f.write(to_msg + "\n")
                                err_f.flush()
                            except Exception:
                                pass
                            try:
                                proc.terminate()
                            except Exception:
                                pass
                            try:
                                proc.wait(timeout=5)
                            except Exception:
                                try:
                                    proc.kill()
                                except Exception:
                                    pass
                            break

                hb_thread = None
                if heartbeat_sec and heartbeat_sec > 0:
                    hb_thread = threading.Thread(target=_heartbeat, name=f"hb-{step.name}", daemon=True)
                    hb_thread.start()

                for line in proc.stdout:
                    # Echo live
                    logging.info("%s> %s", step.name, line.rstrip("\n"))
                    # Write to combined out log
                    out_f.write(line)
                # Process ended; stop heartbeat and wait
                stop_evt.set()
                if hb_thread is not None:
                    hb_thread.join(timeout=1)
                proc.wait()
                # No separate stderr when merged; keep err log empty unless non-zero
                if proc.returncode and proc.returncode != 0:
                    err_f.write(f"process exited with code {proc.returncode}\n")
        else:
            timeout_sec = step.timeout_sec if step.timeout_sec is not None else default_timeout_sec
            try:
                proc = subprocess.run(
                    step.argv,
                    cwd=str(REPO_ROOT),
                    env={**os.environ, **(env or {})},
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=timeout_sec,
                )
            except subprocess.TimeoutExpired as te:
                # Write partial output and mark timeout (handle bytes vs str safely)
                so = te.stdout
                se = te.stderr
                if isinstance(so, (bytes, bytearray)):
                    try:
                        so = so.decode("utf-8", errors="replace")
                    except Exception:
                        so = ""
                if isinstance(se, (bytes, bytearray)):
                    try:
                        se = se.decode("utf-8", errors="replace")
                    except Exception:
                        se = ""
                log_path.write_text(
                    (so or "") + f"\n[TIMEOUT] exceeded {int(timeout_sec or 0)}s\n",
                    encoding="utf-8",
                )
                err_path.write_text((se or "") + "\n[TIMEOUT]\n", encoding="utf-8")

                class _Proc:  # minimal shim to report a timeout exit code
                    returncode = 124

                proc = _Proc()
            else:
                # Write logs at once
                log_path.write_text(proc.stdout or "", encoding="utf-8")
                err_path.write_text(proc.stderr or "", encoding="utf-8")

        duration = time.time() - start
        status.update({"exit_code": proc.returncode, "duration_sec": round(duration, 3)})

        if proc.returncode == 0:
            status["status"] = "OK"
            logging.info("[done ] %s — OK (%.2fs)", step.name, round(duration, 2))
        else:
            status["status"] = "ERROR"
            status["error_log"] = str(err_path.relative_to(ROOT))
            logging.warning(
                "[fail ] %s — exit %s (%.2fs) — see %s",
                step.name,
                proc.returncode,
                round(duration, 2),
                status["error_log"],
            )
    except Exception as e:
        duration = time.time() - start
        status.update(
            {
                "status": "EXCEPTION",
                "error": repr(e),
                "duration_sec": round(duration, 3),
            }
        )
        err_path.write_text(f"[EXCEPTION] {e!r}\n", encoding="utf-8")
        logging.exception("[error] %s — exception: %r", step.name, e)
    return status


def write_status(log_dir: Path, run_status: dict) -> None:
    (log_dir / "status.json").write_text(json.dumps(run_status, indent=2), encoding="utf-8")
    # Compact human-readable summary
    lines = ["# Health Suite Run Status", ""]
    # Pointer to fault artifacts (if present)
    fault_outdir = run_status.get("fault_outdir")
    if isinstance(fault_outdir, str) and fault_outdir:
        lines.append(f"Fault artifacts outdir: {fault_outdir}")
        lines.append(f"Fault summary: {Path(fault_outdir) / 'SUMMARY.md'}")
        gate_fail = Path(fault_outdir) / "GATE_FAIL.md"
        if gate_fail.exists():
            lines.append(f"Gate: GATE_FAIL present — see {gate_fail}")
        lines.append("")
    for idx, s in enumerate(run_status.get("steps", []), start=1):
        name = s.get("name", "?")
        st = s.get("status", "?")
        code = s.get("exit_code", "-")
        dur = s.get("duration_sec", "-")
        mark = "✅" if st == "OK" else ("⚠️" if s.get("skipped") else "❌")
        lines.append(f"{idx:02d}. {mark} {name} — {st} (exit={code}, {dur}s)")
        if s.get("error_log"):
            lines.append(f"    ↳ error log: {s['error_log']}")
        if s.get("triage_listing"):
            lines.append(f"    ↳ gate triage listing: {s['triage_listing']}")
    (log_dir / "status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    legacy_dir = LEGACY_LOG_BASE / log_dir.name
    try:
        legacy_dir.mkdir(parents=True, exist_ok=True)
        for name in ("status.json", "status.md"):
            src = log_dir / name
            dest = legacy_dir / name
            dest.write_bytes(src.read_bytes())
    except Exception:
        pass


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run health suite steps sequentially, never aborting on errors.")
    ap.add_argument(
        "--timestamp",
        dest="timestamp",
        default=_ts_default(),
        help="Shared timestamp for outputs (YYYY-MM-DD_HHMM)",
    )
    ap.add_argument(
        "--live",
        action="store_true",
        help="Stream step outputs live to the console while writing logs.",
    )
    ap.add_argument(
        "--step-timeout-sec",
        type=float,
        default=float(os.getenv("ORCH_STEP_TIMEOUT_SEC", "900")),
        help="Liberal per-step timeout in seconds; 0 disables timeouts.",
    )
    ap.add_argument(
        "--heartbeat-sec",
        type=float,
        default=float(os.getenv("ORCH_HEARTBEAT_SEC", "30")),
        help="Heartbeat interval in seconds while steps run; 0 disables.",
    )
    args = ap.parse_args(argv)

    ts = args.timestamp
    log_dir = LOG_BASE / ts
    log_dir.mkdir(parents=True, exist_ok=True)
    legacy_log_dir = LEGACY_LOG_BASE / ts
    try:
        legacy_log_dir.mkdir(parents=True, exist_ok=True)
        marker = legacy_log_dir / "MOVED.txt"
        if not marker.exists():
            marker.write_text(f"Logs relocated to {log_dir.resolve()}\n", encoding="utf-8")
    except Exception:
        pass

    steps = make_steps(ts)
    run = {
        "timestamp": ts,
        "started_at": time.time(),
        "steps": [],
    }
    if USING_LEGACY:
        run["fault_outdir"] = str((FAULT_RUN_ROOT / ts).resolve())
        run["fault_outdir_legacy"] = str((LEGACY_FAULT_ROOT / ts).resolve())
    else:
        run["fault_outdir"] = ""
        run["fault_outdir_legacy"] = ""

    # Configure logging — show live progress if requested
    logging.basicConfig(level=logging.INFO if args.live else logging.WARNING, format="%(message)s")
    if not USING_LEGACY:
        logging.warning(
            "Health suite orchestrator now defers to topic orchestrators. Set HEALTH_SUITE_USE_LEGACY=1 to run the "
            "legacy pipeline."
        )

    def _capture_fault_gate_triage(outdir: Path, into_log_dir: Path) -> Path | None:
        try:
            triage_dir = outdir / "gate_triage"
            triage_dir.mkdir(parents=True, exist_ok=True)
            listing = triage_dir / "listing.txt"
            with listing.open("w", encoding="utf-8") as f:
                f.write(f"Listing for {outdir}\n\n")
                for p in sorted(outdir.rglob("*")):
                    try:
                        rel = p.relative_to(outdir)
                    except Exception:
                        rel = p.name
                    stat = p.stat() if p.exists() else None
                    size = stat.st_size if stat else 0
                    f.write(f"- {rel} ({size} bytes)\n")
            return listing
        except Exception:
            return None

    for idx, step in enumerate(steps, start=1):
        logging.info("[step ] %02d/%d %s", idx, len(steps), step.name)
        status = run_step(
            step,
            log_dir=log_dir,
            live=args.live,
            default_timeout_sec=(args.step_timeout_sec or None) if args.step_timeout_sec > 0 else None,
            default_heartbeat_sec=(args.heartbeat_sec or None) if args.heartbeat_sec > 0 else None,
        )
        # Capture triage for fault gate failures
        if step.name == "fault_gate" and status.get("exit_code") not in (None, 0):
            fault_outdir = Path(run["fault_outdir"]) if isinstance(run.get("fault_outdir"), str) else None
            if fault_outdir and fault_outdir.exists():
                listing = _capture_fault_gate_triage(fault_outdir, log_dir)
                if listing:
                    status["triage_listing"] = str(listing.relative_to(ROOT))
        run["steps"].append(status)

    run["finished_at"] = time.time()
    write_status(log_dir, run)

    # Never fail the orchestrator; per-step status is captured in logs
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
