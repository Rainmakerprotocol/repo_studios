"""Tests for the run_pytest_log_capture orchestrator modernization."""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from pathlib import Path
from types import ModuleType

import pytest

from tests.fixtures.test_execution_telemetry import (
    BASIC_JUNIT,
    BASIC_LOG,
    SUMMARY_TIMESTAMP,
    write_pytest_bundle,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / ".repo_studios" / "scripts" / "orchestrators" / "run_pytest_log_capture.py"


def _load_module() -> ModuleType:
    module_name = f"run_pytest_log_capture_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load orchestrator module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _prepare_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo_root = tmp_path / "repo"
    logs_dir = repo_root / ".repo_studios" / "pytest_logs"
    output_dir = repo_root / ".repo_studios" / "reports" / "pytest_log_capture"
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return repo_root, logs_dir, output_dir


def test_summary_mode_produces_structured_bundle(tmp_path: Path) -> None:
    module = _load_module()
    repo_root, logs_dir, output_dir = _prepare_repo(tmp_path)

    log_path, junit_path = write_pytest_bundle(
        logs_dir,
        SUMMARY_TIMESTAMP,
        log_text=BASIC_LOG,
        junit_text=BASIC_JUNIT,
    )

    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--logs-dir",
            str(logs_dir),
            "--output-dir",
            str(output_dir),
            "--from-log",
            str(log_path),
            "--from-junit",
            str(junit_path),
        ]
    )

    assert result["exit_code"] == 1
    summary = result["summary"]
    assert summary["failures"] == 1
    assert summary["skips"] == 1
    run_dir = Path(result["run_dir"])
    assert run_dir.is_dir()

    report_path = Path(result["report_json"])
    assert report_path.exists()
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_payload["summary"]["failures"] == 1
    assert report_payload["summary"]["overall_status"] == "failed"

    latest_report = output_dir / "latest_report.json"
    assert latest_report.exists()
    pointer_payload = json.loads(latest_report.read_text(encoding="utf-8"))
    assert pointer_payload["summary"]["failures"] == 1

    failed_summary = logs_dir / "pytest_failed_logs" / f"pytest_failed_{SUMMARY_TIMESTAMP}.txt"
    skip_summary = logs_dir / "pytest_skip_logs" / f"pytest_skip_{SUMMARY_TIMESTAMP}.txt"
    assert failed_summary.exists()
    assert skip_summary.exists()
    assert "FAILED tests" in failed_summary.read_text(encoding="utf-8")
    assert "SKIPPED tests" in skip_summary.read_text(encoding="utf-8")


def test_execute_mode_captures_and_writes_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    repo_root, logs_dir, output_dir = _prepare_repo(tmp_path)

    run_timestamp = "2025-01-02_1010"
    monkeypatch.setattr(module, "timestamp", lambda: run_timestamp)
    monkeypatch.setattr(module, "_pytest_help_supports", lambda options, cwd: {opt: False for opt in options})

    commands: list[list[str]] = []

    def _fake_run_pytest(cmd: list[str], cwd: Path) -> tuple[str, int, bool]:
        commands.append(list(cmd))
        junit_arg = next((part for part in cmd if part.startswith("--junitxml=")), None)
        assert junit_arg is not None
        junit_target = Path(junit_arg.split("=", 1)[1])
        junit_target.write_text(BASIC_JUNIT, encoding="utf-8")
        return BASIC_LOG, 1, False

    monkeypatch.setattr(module, "run_pytest_and_capture", _fake_run_pytest)

    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--logs-dir",
            str(logs_dir),
            "--output-dir",
            str(output_dir),
            "--log-level",
            "INFO",
            "--",
            "tests/test_sample.py::test_fail",
        ]
    )

    assert commands, "pytest was not invoked"
    assert result["exit_code"] == 1
    summary = result["summary"]
    assert summary["failures"] == 1
    assert summary["skips"] == 1

    run_dir = Path(result["run_dir"])
    assert run_dir.is_dir()
    bundle_summary = json.loads(Path(result["bundle_summary"]).read_text(encoding="utf-8"))
    assert bundle_summary["failures"] == 1

    full_log_pointer = output_dir / "latest_full_log.txt"
    assert full_log_pointer.exists()
    assert "test_fail" in full_log_pointer.read_text(encoding="utf-8")

    failed_summary = logs_dir / "pytest_failed_logs" / f"pytest_failed_{run_timestamp}.txt"
    assert failed_summary.exists()
    failed_text = failed_summary.read_text(encoding="utf-8")
    assert "FAILED tests" in failed_text
    assert "tests/test_sample.py::test_fail" in failed_text

    report_payload = json.loads(Path(result["report_json"]).read_text(encoding="utf-8"))
    command = report_payload["run"]["command"]
    assert command[-1] == "tests/test_sample.py::test_fail"
    assert report_payload["summary"]["overall_status"] == "failed"

    junit_copy = run_dir / "junit.xml"
    assert junit_copy.exists()
    latest_junit = output_dir / "latest_junit.xml"
    assert latest_junit.exists()