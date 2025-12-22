from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_PRODUCER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "collect_test_log_reports.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_junit(run_dir: Path) -> Path:
    content = """
<testsuite name=\"pytest\" tests=\"3\" failures=\"1\" errors=\"0\" skipped=\"1\">
  <testcase classname=\"pkg.test_mod\" name=\"test_ok\" />
  <testcase classname=\"pkg.test_mod\" name=\"test_warn\">
    <failure message=\"assert false\">AssertionError: false</failure>
  </testcase>
  <testcase classname=\"pkg.test_mod\" name=\"test_skip\">
    <skipped message=\"xfail\" />
  </testcase>
</testsuite>
""".strip()
    junit_path = run_dir / "junit_run.xml"
    junit_path.write_text(content, encoding="utf-8")
    return junit_path


def _write_pytest_log(run_dir: Path) -> Path:
    content = """
=============================== warnings summary ===============================
repo/tests/test_mod.py:10: UserWarning: sample
  warnings.warn("sample")
=========================== slowest 2 durations ================================
1.23s call repo/tests/test_mod.py::test_warn
0.50s call repo/tests/test_mod.py::test_ok
=================================== FAILURES ===================================
Traceback (most recent call last):
  File "repo/tests/test_mod.py", line 10, in test_warn
    raise AssertionError("boom")
AssertionError: boom
""".lstrip()
    log_path = run_dir / "pytest_20250101.txt"
    log_path.write_text(content, encoding="utf-8")
    return log_path


def test_collect_test_log_reports_emits_artifacts(tmp_path):
    producer_mod = _load_module("collect_test_log_reports", _PRODUCER_PATH)

    assert producer_mod.DEFAULT_OUTPUT_DIR == Path(".repo_studios/reports/healthview")

    repo = tmp_path / "repo"
    run_dir = repo / ".repo_studios" / "pytest_logs" / "smoke" / "2025-01-01_000000"
    run_dir.mkdir(parents=True)
    _write_junit(run_dir)
    _write_pytest_log(run_dir)

    output_dir = repo / ".repo_studios" / "command_center" / "reports"

    result = producer_mod.run(
        [
            "--logs-dir",
            str(run_dir.parents[2]),
            "--logs-run",
            str(run_dir),
            "--output-dir",
            str(output_dir),
            "--run-timestamp",
            "20250101-0000",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    artifacts_dir = Path(result["output_dir"])
    assert artifacts_dir.exists()

    manifest_path = artifacts_dir / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer_slug"] == "rawview"
    assert manifest["topic"] == "test_log_reports"
    assert manifest["run_timestamp"] == "20250101-0000"

    telemetry_path = artifacts_dir / "telemetry.json"
    assert telemetry_path.exists()
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert telemetry["viewer_slug"] == "rawview"
    assert telemetry["topic"] == "test_log_reports"
    assert telemetry["run_timestamp"] == "20250101-0000"

    metrics = telemetry["metrics"]
    assert metrics["tests_total"] == 3
    assert metrics["warnings_total"] == 1
    assert metrics["tracebacks"] == 1
    assert metrics["slow_tests_count"] == 2

    summary_md = artifacts_dir / "summary.md"
    assert summary_md.exists()
    summary_text = summary_md.read_text(encoding="utf-8")
    assert "Test Log Report" in summary_text
    assert "Warnings: 1" in summary_text
    assert "Tracebacks: 1" in summary_text

    # No mutable latest_* pointers in canonical report bundles.
    assert not (output_dir / "latest_report.json").exists()


def test_collect_test_log_reports_prunes_history(tmp_path):
    producer_mod = _load_module("collect_test_log_reports", _PRODUCER_PATH)

    assert producer_mod.DEFAULT_OUTPUT_DIR == Path(".repo_studios/reports/healthview")

    repo = tmp_path / "repo"
    logs_base = repo / ".repo_studios" / "pytest_logs"
    first_run = logs_base / "suite" / "run_a"
    second_run = logs_base / "suite" / "run_b"
    first_run.mkdir(parents=True)
    second_run.mkdir(parents=True)
    _write_junit(first_run)
    _write_pytest_log(first_run)
    _write_junit(second_run)
    _write_pytest_log(second_run)

    output_dir = repo / ".repo_studios" / "command_center" / "reports"

    producer_mod.run(
        [
            "--logs-dir",
            str(logs_base),
            "--logs-run",
            str(first_run),
            "--output-dir",
            str(output_dir),
            "--run-timestamp",
            "20250101-0000",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    result = producer_mod.run(
        [
            "--logs-dir",
            str(logs_base),
            "--logs-run",
            str(second_run),
            "--output-dir",
            str(output_dir),
            "--run-timestamp",
            "20250101-0001",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "ERROR",
        ]
    )

    artifacts_dir = Path(result["output_dir"])
    runs_root = output_dir / "rawview" / "test_log_reports"
    runs = [child.name for child in runs_root.iterdir() if child.is_dir()]
    assert len(runs) == 1
    assert artifacts_dir.name in runs


def test_collect_test_log_reports_handles_missing_runs(tmp_path):
    producer_mod = _load_module("collect_test_log_reports", _PRODUCER_PATH)

    repo = tmp_path / "repo"
    logs_dir = repo / ".repo_studios" / "pytest_logs"
    logs_dir.mkdir(parents=True)

    result = producer_mod.run(
        [
            "--logs-dir",
            str(logs_dir),
            "--output-dir",
            str(repo / "out"),
            "--log-level",
            "ERROR",
        ]
    )

    assert result["run_dir"] is None
    assert result["output_dir"] is None
