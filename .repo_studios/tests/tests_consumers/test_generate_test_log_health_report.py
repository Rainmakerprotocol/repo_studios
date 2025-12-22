from __future__ import annotations

import importlib.util
import json
import csv
import pytest
import sys
from datetime import datetime
from pathlib import Path

_CONSUMER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "consumers" / "generate_test_log_health_report.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_junit(run_dir: Path) -> Path:
    content = """
<testsuite name="pytest" tests="3" failures="1" errors="0" skipped="1">
  <testcase classname="pkg.test_mod" name="test_ok" />
  <testcase classname="pkg.test_mod" name="test_warn">
    <failure message="assert false">AssertionError: false</failure>
  </testcase>
  <testcase classname="pkg.test_mod" name="test_skip">
    <skipped message="xfail" />
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


def test_generate_test_log_health_report_prefers_producer_bundle(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_test_log_health_report", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    producer_dir = (
        repo
        / ".repo_studios"
        / "reports"
        / "healthview"
        / "rawview"
        / "test_log_reports"
        / "20250101-0000"
    )
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

    telemetry_payload = {
        "schema_version": 1,
        "viewer_slug": "rawview",
        "topic": "test_log_reports",
        "run_timestamp": "20250101-0000",
        "generated_at": "2025-11-23T12:00:00+00:00",
        "status": "ok",
        "metrics": {
            "tests_total": 3,
            "tests_passed": 1,
            "tests_failed": 1,
            "tests_skipped": 1,
            "tests_xfailed": 1,
            "tests_errors": 0,
            "warnings_total": 2,
            "tracebacks": 1,
            "slow_tests_count": 1,
        },
        "payload": {
            "summary": payload["summary"],
            "warnings": payload["warnings"],
            "slow_tests": payload["slow_tests"],
            "meta": payload["meta"],
        },
    }

    telemetry_path = producer_dir / "telemetry.json"
    telemetry_path.write_text(json.dumps(telemetry_payload), encoding="utf-8")

    output_base = (
        repo / ".repo_studios" / "reports" / "healthview" / "consumer_reports" / "test_log_health_reports"
    )

    first_result = consumer_mod.run(
        [
            "--logs-dir",
            str(logs_dir),
            "--output-base",
            str(output_base),
            "--producer-bundle-dir",
            str(producer_dir),
            "--timestamp",
            "2025-01-01T00:00:00+00:00",
            "--log-level",
            "ERROR",
        ]
    )

    artifacts_dir = Path(first_result["output_dir"])
    assert artifacts_dir.exists()
    assert first_result["source"] == "producer"
    assert Path(first_result["producer_bundle_dir"]).resolve() == producer_dir.resolve()
    assert first_result["producer_report"] is None

    report = json.loads((artifacts_dir / "report.json").read_text(encoding="utf-8"))
    assert report["summary"] == payload["summary"]

    markdown = (artifacts_dir / "report.md").read_text(encoding="utf-8")
    assert "warnings_total: 2" in markdown
    assert "slowest tests" in markdown.lower()
    assert "Source References" in markdown
    bundle_summary = json.loads((artifacts_dir / "bundle_summary.json").read_text(encoding="utf-8"))
    assert bundle_summary["source"] == "producer"
    assert bundle_summary["producer_report"] is None
    assert bundle_summary["producer_bundle_dir"] == str(producer_dir.resolve())
    assert bundle_summary["summary"] == payload["summary"]
    assert bundle_summary["comparisons"]["previous_run"]["pass_rate"]["previous"] is None
    csv_path = Path(first_result["report_csv"])
    assert csv_path.exists()
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["metric", "value"]
    assert ["total", "3"] in rows

    # second run to verify pass-rate delta and CSV update
    payload["summary"]["passed"] = 2
    payload["summary"]["failed"] = 0
    telemetry_payload["payload"]["summary"] = payload["summary"]
    telemetry_payload["metrics"]["tests_passed"] = 2
    telemetry_payload["metrics"]["tests_failed"] = 0
    telemetry_path.write_text(json.dumps(telemetry_payload), encoding="utf-8")

    second_result = consumer_mod.run(
        [
            "--logs-dir",
            str(logs_dir),
            "--output-base",
            str(output_base),
            "--producer-bundle-dir",
            str(producer_dir),
            "--timestamp",
            "2025-01-01T00:01:00+00:00",
            "--log-level",
            "ERROR",
        ]
    )

    second_dir = Path(second_result["output_dir"])
    second_report = json.loads((second_dir / "report.json").read_text(encoding="utf-8"))
    pass_rate_delta = second_report["comparisons"]["previous_run"]["pass_rate"]["delta"]
    assert pass_rate_delta == pytest.approx(33.34, abs=0.01)
    csv_path = Path(second_result["report_csv"])
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert ["pass_rate_delta_pct", "+33.34"] in rows


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
        repo / ".repo_studios" / "reports" / "healthview" / "consumer_reports" / "test_log_health_reports"
    )

    first_result = consumer_mod.run(
        [
            "--logs-dir",
            str(logs_base),
            "--output-base",
            str(output_base),
            "--timestamp",
            "2025-01-01T00:00:00+00:00",
            "--log-level",
            "ERROR",
        ]
    )

    artifacts_dir = Path(first_result["output_dir"])
    assert artifacts_dir.exists()
    assert first_result["source"] == "logs"
    assert Path(first_result["logs_source"]).resolve() == run_dir.resolve()

    report = json.loads((artifacts_dir / "report.json").read_text(encoding="utf-8"))
    summary = report["summary"]
    assert summary["total"] == 3
    assert summary["warnings_total"] == 1
    assert summary["tracebacks"] == 1

    markdown = (artifacts_dir / "report.md").read_text(encoding="utf-8")
    assert "UserWarning" in markdown
    assert "repo/tests/test_mod.py::test_warn" in markdown
    assert "Source References" in markdown
    bundle_summary = json.loads((artifacts_dir / "bundle_summary.json").read_text(encoding="utf-8"))
    assert bundle_summary["source"] == "logs"
    assert bundle_summary["producer_report"] is None
    assert bundle_summary["summary"]["total"] == 3
    assert bundle_summary["comparisons"]["previous_run"]["pass_rate"]["previous"] is None

    # Second run should compute zero delta because data unchanged
    second_result = consumer_mod.run(
        [
            "--logs-dir",
            str(logs_base),
            "--output-base",
            str(output_base),
            "--timestamp",
            "2025-01-01T00:01:00+00:00",
        ]
    )
    second_dir = Path(second_result["output_dir"])
    second_report = json.loads((second_dir / "report.json").read_text(encoding="utf-8"))
    delta = second_report["comparisons"]["previous_run"]["pass_rate"]["delta"]
    assert delta == 0.0
    csv_path = Path(second_result["report_csv"])
    assert csv_path.exists()


def test_generate_test_log_health_report_prunes_history(tmp_path, monkeypatch):
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
        repo / ".repo_studios" / "reports" / "healthview" / "consumer_reports" / "test_log_health_reports"
    )

    timestamps = [datetime(2025, 1, 1, 0, minute, tzinfo=consumer_mod.UTC) for minute in range(12)]

    class _FakeDatetime(datetime):
        queue = timestamps.copy()

        @classmethod
        def now(cls, tz=None):
            value = cls.queue.pop(0)
            if tz is not None:
                return value.astimezone(tz)
            return value.replace(tzinfo=None)

        @classmethod
        def utcnow(cls):
            return cls.now(consumer_mod.UTC)

    monkeypatch.setattr(consumer_mod, "datetime", _FakeDatetime)

    for _ in range(6):
        consumer_mod.run(
            [
                "--logs-dir",
                str(logs_base),
                "--output-base",
                str(output_base),
                "--artifacts-to-keep",
                "3",
            ]
        )

    runs = sorted(p for p in output_base.iterdir() if p.is_dir())
    assert len(runs) == 3


def test_timestamp_slug_helpers(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_test_log_health_report_helpers", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    assert consumer_mod._timestamp_slug_from_iso("2025-01-01T00:00:00+00:00") == "20250101-0000"
    assert consumer_mod._timestamp_slug_from_iso("2025-01-01T00:00:00") == "20250101-0000"
    assert consumer_mod._timestamp_slug_from_iso("not-a-timestamp") is None

    args = consumer_mod._parse_args(["--timestamp", "2025-01-01T00:01:00+00:00"])
    assert consumer_mod._run_slug(args) == "20250101-0001"

    args = consumer_mod._parse_args(["--timestamp", "invalid"])
    slug = consumer_mod._run_slug(args)
    assert len(slug) == 13
    assert slug[8] == "-"
    assert (slug[:8] + slug[9:]).isdigit()


def test_markdownlint_injection_is_idempotent(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_test_log_health_report_markdown", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    raw = "# Report\n\nBody\n"
    injected = consumer_mod._inject_markdownlint_exception(raw)
    assert injected.startswith("<!-- markdownlint-disable MD013 -->")
    injected_again = consumer_mod._inject_markdownlint_exception(injected)
    assert injected_again == injected


def test_append_delta_markdown_formats_values(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_test_log_health_report_delta", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    markdown = "# Report\n\nBody\n"
    comparisons = {
        "previous_run": {
            "pass_rate": {
                "current": 66.66,
                "previous": 33.33,
                "delta": 33.33,
            }
        }
    }
    out = consumer_mod._append_delta_markdown(markdown, comparisons)
    assert "## Pass Rate Delta" in out
    assert "Previous pass rate: 33.33%" in out
    assert "Current pass rate: 66.66%" in out
    assert "Delta: +33.33 percentage points" in out

    comparisons = {"previous_run": {"pass_rate": {"current": None, "previous": None, "delta": None}}}
    out = consumer_mod._append_delta_markdown(markdown, comparisons)
    assert "Previous pass rate: N/A" in out
    assert "Current pass rate: N/A" in out
    assert "Delta: N/A" in out


def test_select_latest_bundle_dir_prefers_latest_slug(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_test_log_health_report_bundle", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    root = repo / "bundles"
    root.mkdir()
    (root / "not-a-run").mkdir()
    (root / "20250101-0000").mkdir()
    (root / "20250101-0001").mkdir()

    assert consumer_mod._is_timestamp_slug("20250101-0001") is True
    assert consumer_mod._is_timestamp_slug("2025-01-01_0001") is False
    latest = consumer_mod._select_latest_bundle_dir(root)
    assert latest is not None
    assert latest.name == "20250101-0001"


def test_write_csv_emits_expected_rows(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_test_log_health_report_csv", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    out_dir = repo / "out"
    out_dir.mkdir()
    payload = {
        "summary": {
            "total": 3,
            "passed": 2,
            "skipped": 0,
            "xfailed": 0,
            "failed": 1,
            "errors": 0,
            "warnings_total": 4,
            "tracebacks": 1,
        },
        "slow_tests": [{"seconds": 1.23, "nodeid": "pkg::test_a"}],
    }
    comparisons = {"previous_run": {"pass_rate": {"current": 66.66, "previous": None, "delta": None}}}
    csv_path = consumer_mod._write_csv(out_dir, payload, comparisons)
    assert csv_path.exists()
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["metric", "value"]
    assert ["total", "3"] in rows
    assert ["slow_tests_count", "1"] in rows
