from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[3] / "command_center" / "scripts" / "aggregators" / "generate_metrics_summary.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_metrics_summary", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_metrics_summary_run(tmp_path: Path) -> None:
    mod = _load_module()

    tests_payload = {
        "library_integration": {
            "status": "passed",
            "duration_seconds": 90.0,
            "artifacts": ["reports/library.xml"],
        },
        "producer_suite": {
            "status": "skipped",
            "duration_seconds": 0,
            "artifacts": [],
        },
    }
    tests_file = tmp_path / "tests.json"
    tests_file.write_text(json.dumps(tests_payload), encoding="utf-8")

    output_dir = tmp_path / "reports" / "automation_metrics"

    exit_code = mod.main(
        [
            "--repo-root",
            str(tmp_path),
            "--output-dir",
            str(output_dir),
            "--tests-file",
            str(tests_file),
            "--schema-version",
            "1.0",
            "--run-id",
            "2025-11-02T19-30-00Z",
            "--target",
            "library",
            "--lines-touched",
            "42",
            "--files-changed",
            "5",
            "--duplicate-groups-resolved",
            "2",
            "--runtime-seconds",
            "18.5",
            "--notes",
            "dry run",
            "--timestamp",
            "2025-11-02T19:30:00+00:00",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0

    run_dir = output_dir / f"{mod.RUN_STEM}-20251102_193000"
    summary_path = run_dir / mod.SUMMARY_FILENAME
    assert summary_path.is_file()

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "2025-11-02T19-30-00Z"
    assert payload["files_changed"] == 5
    assert payload["targets"] == ["library"]
    assert payload["tests_executed"]["library_integration"]["status"] == "passed"

    latest_pointer = output_dir / mod.LATEST_POINTER
    assert latest_pointer.is_file()
    assert latest_pointer.read_text(encoding="utf-8") == summary_path.read_text(encoding="utf-8")


def test_invalid_tests_payload(tmp_path: Path, caplog) -> None:
    mod = _load_module()

    tests_file = tmp_path / "tests.json"
    tests_file.write_text("{}", encoding="utf-8")  # Missing required suites

    output_dir = tmp_path / "reports"

    with caplog.at_level("ERROR"):
        exit_code = mod.main(
            [
                "--repo-root",
                str(tmp_path),
                "--output-dir",
                str(output_dir),
                "--tests-file",
                str(tests_file),
                "--run-id",
                "2025-11-02T20-00-00Z",
                "--target",
                "library",
                "--lines-touched",
                "10",
                "--files-changed",
                "1",
                "--duplicate-groups-resolved",
                "0",
                "--runtime-seconds",
                "5.0",
                "--log-level",
                "ERROR",
            ]
        )

    assert exit_code == 1
    assert any("At least one test entry is required" in message for message in caplog.messages)
