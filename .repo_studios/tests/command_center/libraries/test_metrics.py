from __future__ import annotations

from pathlib import Path
import importlib
import json
import sys

import pytest


SCRIPTS_ROOT = (
    Path(__file__).resolve().parents[4]
    / ".repo_studios"
    / "command_center"
    / "scripts"
)


def _load_libraries():
    try:
        return importlib.import_module("libraries")
    except ModuleNotFoundError:  # pragma: no cover - mirrors existing pattern
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        return importlib.import_module("libraries")


libraries = _load_libraries()
MetricsSummary = libraries.MetricsSummary
TestRunResult = libraries.TestRunResult
build_metrics_summary = libraries.build_metrics_summary
write_metrics_summary = libraries.write_metrics_summary


def test_test_run_result_validation() -> None:
    result = TestRunResult(status="passed", duration_seconds=12.3, artifacts=("logs/test.log",))
    assert result.to_dict() == {
        "status": "passed",
        "duration_seconds": 12.3,
        "artifacts": ["logs/test.log"],
    }

    with pytest.raises(ValueError):
        TestRunResult(status="unknown", duration_seconds=1.0)

    with pytest.raises(ValueError):
        TestRunResult(status="failed", duration_seconds=-1.0)


def test_build_metrics_summary_round_trip(tmp_path: Path) -> None:
    summary = build_metrics_summary(
        schema_version="1.0",
        run_id="2025-11-02T19-30-00Z",
        targets=("library",),
        lines_touched=120,
        files_changed=5,
        duplicate_groups_resolved=3,
        runtime_seconds=45.5,
        tests_executed={
            "pytest": TestRunResult(status="passed", duration_seconds=30.0, artifacts=("reports/pytest.xml",)),
            "lint": TestRunResult(status="skipped", duration_seconds=0.0),
        },
        notes="dry run",
    )

    assert summary.to_dict()["run_id"] == "2025-11-02T19-30-00Z"

    output_path = tmp_path / "metrics" / "summary.json"
    written_path = write_metrics_summary(summary, output_path)
    assert written_path == output_path
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["files_changed"] == 5
    assert payload["tests_executed"]["pytest"]["artifacts"] == ["reports/pytest.xml"]
    assert payload["notes"] == "dry run"


def test_metrics_summary_requires_tests() -> None:
    with pytest.raises(ValueError):
        MetricsSummary(
            schema_version="1.0",
            run_id="missing-tests",
            targets=("library",),
            lines_touched=0,
            files_changed=0,
            duplicate_groups_resolved=0,
            runtime_seconds=0.0,
            tests_executed={},
        )
