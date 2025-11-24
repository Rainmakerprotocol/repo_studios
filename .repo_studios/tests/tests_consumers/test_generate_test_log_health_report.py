from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_CONSUMER_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "consumers"
    / "generate_test_log_health_report.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_junit(run_dir: Path) -> Path:
    content = (
        """
<testsuite name="pytest" tests="3" failures="1" errors="0" skipped="1">
  <testcase classname="pkg.test_mod" name="test_ok" />
  <testcase classname="pkg.test_mod" name="test_warn">
    <failure message="assert false">AssertionError: false</failure>
  </testcase>
  <testcase classname="pkg.test_mod" name="test_skip">
    <skipped message="xfail" />
  </testcase>
</testsuite>
"""
        .strip()
    )
    junit_path = run_dir / "junit_run.xml"
    junit_path.write_text(content, encoding="utf-8")
    return junit_path


def _write_pytest_log(run_dir: Path) -> Path:
    content = (
        """
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
"""
        .lstrip()
    )
    log_path = run_dir / "pytest_20250101.txt"
    log_path.write_text(content, encoding="utf-8")
    return log_path


def test_generate_test_log_health_report_prefers_producer_bundle(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_test_log_health_report", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    producer_dir = repo / ".repo_studios" / "reports" / "producer_reports" / "test_log_reports"
    producer_dir.mkdir(parents=True)

    logs_dir = repo / ".repo_studios" / "pytest_logs" / "run_a"
    logs_dir.mkdir(parents=True)

    payload = {
        "schema_version": 1,
        "meta": {
            "generated_at": "2025-11-23T12:00:00",
            "logs_dir": str(logs_dir),
            "junit": str(logs_dir / "junit_run.xml"),
            "full_log": str(logs_dir / "pytest_20250101.txt"),
        },
        "summary": {
            "total": 3,
            "passed": 1,
            "skipped": 1,
            "xfailed": 1,
            "failed": 1,
            "errors": 0,
            "warnings_total": 2,
            "tracebacks": 1,
        },
        "warnings": {
            "by_type": {"UserWarning": 2},
            "by_file": {"repo/tests/test_mod.py": 2},
        },
        "slow_tests": [
            {"seconds": 1.23, "nodeid": "repo/tests/test_mod.py::test_warn"},
        ],
    }

    report_path = producer_dir / "latest_report.json"
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    output_base = (
        repo
        / ".repo_studios"
        / "reports"
        / "consumer_reports"
        / "test_log_health_reports"
    )

    result = consumer_mod.run(
        [
            "--logs-dir",
            str(logs_dir),
            "--output-base",
            str(output_base),
            "--producer-report",
            str(report_path),
            "--log-level",
            "ERROR",
        ]
    )

    artifacts_dir = Path(result["output_dir"])
    assert artifacts_dir.exists()
    assert result["source"] == "producer"
    assert Path(result["producer_report"]).resolve() == report_path.resolve()

    report = json.loads((artifacts_dir / "report.json").read_text(encoding="utf-8"))
    assert report == payload

    markdown = (artifacts_dir / "report.md").read_text(encoding="utf-8")
    assert "warnings_total: 2" in markdown
    assert "slowest tests" in markdown.lower()


def test_generate_test_log_health_report_falls_back_to_logs(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_test_log_health_report", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    logs_base = repo / ".repo_studios" / "pytest_logs"
    run_dir = logs_base / "suite" / "2025-01-01"
    run_dir.mkdir(parents=True)
    _write_junit(run_dir)
    _write_pytest_log(run_dir)

    output_base = (
        repo
        / ".repo_studios"
        / "reports"
        / "consumer_reports"
        / "test_log_health_reports"
    )

    result = consumer_mod.run(
        [
            "--logs-dir",
            str(logs_base),
            "--output-base",
            str(output_base),
            "--producer-report",
            str(repo / "missing_report.json"),
            "--log-level",
            "ERROR",
        ]
    )

    artifacts_dir = Path(result["output_dir"])
    assert artifacts_dir.exists()
    assert result["source"] == "logs"
    assert Path(result["logs_source"]).resolve() == run_dir.resolve()

    report = json.loads((artifacts_dir / "report.json").read_text(encoding="utf-8"))
    summary = report["summary"]
    assert summary["total"] == 3
    assert summary["warnings_total"] == 1
    assert summary["tracebacks"] == 1

    markdown = (artifacts_dir / "report.md").read_text(encoding="utf-8")
    assert "UserWarning" in markdown
    assert "repo/tests/test_mod.py::test_warn" in markdown
