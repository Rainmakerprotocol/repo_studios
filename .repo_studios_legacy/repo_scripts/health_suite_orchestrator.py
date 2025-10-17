#!/usr/bin/env python3
"""
Health Suite Orchestrator

Runs repo health scripts sequentially, always continuing to the next step.
Each step is considered complete whether it succeeds or fails; failures are
logged to per-step error logs and included in a final status summary.

Requested order (with tolerant filename matching for historical typos):
  1) batch_clean.py
  2) pytest_log_runner.py
  3) scan_monkey_patches.py
  4) dep_hygiene_report.py
  5) compare_monkey_patch_trends.py
  6) check_import_boundaries.py
  7) test_log_health_report.py
  8) import_graph_report.py
  9) churn_complexity_heatmap.py
 10) dump_faulthandler_once.py (best-effort)
 11) generate_fault_artifacts.py (best-effort)
 12) scripts/health/faulthandler_aggregate.py (best-effort)
 13) scripts/ci_faulthandler_gate.py (best-effort, report-only)
 14) health_suite_summary.py

Outputs:
- Per-step logs under .repo_studios/health_suite/logs/<timestamp>/
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
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
repo_DIR = ROOT / ".repo_studios"
LOG_BASE = repo_DIR / "health_suite" / "logs"


def _ts_default() -> str:
    return time.strftime("%Y-%m-%d_%H%M")


def exe() -> str:
    return sys.executable or "python"


def find_script(*candidates: str) -> Path | None:
    for name in candidates:
        p = repo_DIR / name
        if p.exists():
            return p
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
    py = exe()
    steps: list[Step] = []
    # Prepare a shared FAULT_OUTDIR for fault steps so all child processes
    # write into a deterministic run folder for this orchestrator execution.
    fault_base = repo_DIR / "faulthandler" / ts
    try:
        fault_base.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    fault_env = {
        "FAULT_ENABLE": "1",
        "FAULT_OUTDIR": str(fault_base),
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

    # 2) pytest_log_runner.py
    script = find_script("pytest_log_runner.py")
    steps.append(
        Step(
            name="pytest_logs",
            argv=[py, str(script)] if script else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 3) scan_monkey_patches.py
    script = find_script("scan_monkey_patches.py")
    steps.append(
        Step(
            name="scan_monkey_patches",
            argv=[py, str(script), "--repo-root", ".", "--with-git", "--verbose", "--strict"]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 4) dep_hygiene_report.py
    script = find_script("dep_hygiene_report.py")
    steps.append(
        Step(
            name="dep_health",
            argv=[
                py,
                str(script),
                "--repo-root",
                ".",
                "--output-base",
                str(repo_DIR / "dep_health"),
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 5) compare_monkey_patch_trends.py
    script = find_script("compare_monkey_patch_trends.py")
    steps.append(
        Step(
            name="compare_monkey_patch_trends",
            argv=[py, str(script)] if script else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 6) check_import_boundaries.py (typo-tolerant)
    script = find_script("check_import_boundaries.py", "check_import_boundries.py")
    steps.append(
        Step(
            name="check_import_boundaries",
            argv=[py, str(script)] if script else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 7) test_log_health_report.py
    script = find_script("test_log_health_report.py")
    steps.append(
        Step(
            name="test_log_health_report",
            argv=[
                py,
                str(script),
                "--logs-dir",
                str(repo_DIR / "pytest_logs"),
                "--output-base",
                str(repo_DIR / "test_health"),
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # New) typecheck_report.py — run mypy and produce artifacts (optional)
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
                        "--output-base",
                        str(repo_DIR / "typecheck"),
                        "--timestamp",
                        ts,
                    ]
                    if script
                    else [
                        "import sys; print('missing typecheck_report.py', file=sys.stderr); sys.exit(1)",
                    ]
                ),
            ],
            optional=script is None,
        )
    )

    # 8) import_graph_report.py
    script = find_script("import_graph_report.py")
    steps.append(
        Step(
            name="import_graph_report",
            argv=[
                py,
                str(script),
                "--repo-root",
                ".",
                "--output-base",
                str(repo_DIR / "import_graph"),
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 9) churn_complexity_heatmap.py
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
                str(repo_DIR / "churn_complexity"),
                "--logs-dir",
                str(repo_DIR / "pytest_logs"),
            ]
            if script
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
        )
    )

    # 9.5) lizard complexity report (optional but expected in CI)
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

    # 10) one-time faulthandler dump (best-effort)
    script = find_script("dump_faulthandler_once.py")
    steps.append(
        Step(
            name="fault_dump_once",
            argv=[py, str(script)] if script else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
            env=fault_env,
        )
    )

    # 11) faulthandler artifacts generator (best-effort)
    script = find_script("generate_fault_artifacts.py")
    steps.append(
        Step(
            name="fault_artifacts",
            argv=[py, str(script)] if script else [py, "-c", "import sys; sys.exit(1)"],
            optional=script is None,
            env=fault_env,
        )
    )

    # 12) faulthandler aggregator under scripts/health (best-effort)
    agg_script = Path("scripts/health/faulthandler_aggregate.py")
    steps.append(
        Step(
            name="fault_aggregate",
            argv=[py, str(agg_script)]
            if agg_script.exists()
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=not agg_script.exists(),
            env=fault_env,
        )
    )

    # 13) ci gate (best-effort, non-blocking in the suite)
    gate_script = Path("scripts/ci_faulthandler_gate.py")
    steps.append(
        Step(
            name="fault_gate",
            argv=[py, str(gate_script)]
            if gate_script.exists()
            else [py, "-c", "import sys; sys.exit(1)"],
            optional=not gate_script.exists(),
            env=fault_env,
        )
    )

    # 13.5) anchor health (generate timestamped anchor report artifacts)
    anchor_script = repo_DIR / "anchor_health_report.py"
    steps.append(
        Step(
            name="anchor_health",
            argv=[py, str(anchor_script)] if anchor_script.exists() else [py, "-c", "import sys; sys.exit(1)"],
            optional=not anchor_script.exists(),
        )
    )

    # 14) health_suite_summary.py (typo-tolerant) — now includes anchor health section
    script = find_script("health_suite_summary.py", "heath_suite_summary.py")
    out_dir = repo_DIR / "health_suite"
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
                    cwd=str(ROOT),
                    env={**os.environ, **(env or {})},
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert proc.stdout is not None
                # Heartbeat and timeout supervisor
                timeout_sec = (
                    step.timeout_sec if step.timeout_sec is not None else default_timeout_sec
                )
                heartbeat_sec = (
                    step.heartbeat_sec if step.heartbeat_sec is not None else default_heartbeat_sec
                )
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
                            to_msg = (
                                f"[TIMEOUT] {step.name} exceeded {int(timeout_sec)}s — terminating"
                            )
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
                    hb_thread = threading.Thread(
                        target=_heartbeat, name=f"hb-{step.name}", daemon=True
                    )
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
                    cwd=str(ROOT),
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


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Run health suite steps sequentially, never aborting on errors."
    )
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

    steps = make_steps(ts)
    run = {
        "timestamp": ts,
        "started_at": time.time(),
        "steps": [],
    }
    # Echo the resolved fault outdir for this run (if created by make_steps)
    run["fault_outdir"] = str(repo_DIR / "faulthandler" / ts)

    # Configure logging — show live progress if requested
    logging.basicConfig(level=logging.INFO if args.live else logging.WARNING, format="%(message)s")

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
            default_timeout_sec=(args.step_timeout_sec or None)
            if args.step_timeout_sec > 0
            else None,
            default_heartbeat_sec=(args.heartbeat_sec or None) if args.heartbeat_sec > 0 else None,
        )
        # Capture triage for fault gate failures
        if step.name == "fault_gate" and status.get("exit_code") not in (None, 0):
            fault_outdir = (
                Path(run["fault_outdir"]) if isinstance(run.get("fault_outdir"), str) else None
            )
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
