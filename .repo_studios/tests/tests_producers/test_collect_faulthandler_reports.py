from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import pytest

_PRODUCER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "collect_faulthandler_reports.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sample_stacks() -> str:
    return (
        "Current thread 0x0001 (most recent call first):\n"
        '  File "/app/main.py", line 12, in run\n'
        '  File "/app/service.py", line 5, in handle\n'
        "\n"
        "Thread 0x0002:\n"
        '  File "/lib/utils.py", line 7, in helper\n'
    )


def test_collect_faulthandler_reports_emits_artifacts(tmp_path):
    producer_mod = _load_module("collect_faulthandler_reports", _PRODUCER_PATH)

    repo = tmp_path / "repo"
    runs_dir = (
        repo
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "rawview"
        / "fault_diagnostics_runs"
    )
    run_dir = runs_dir / "2025-01-01_000000"
    run_dir.mkdir(parents=True)
    (run_dir / "stacks.log").write_text(_sample_stacks(), encoding="utf-8")

    output_dir = repo / ".repo_studios" / "reports" / "producer_reports" / "faulthandler_reports"

    result = producer_mod.run(
        [
            "--runs-dir",
            str(runs_dir),
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(output_dir),
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    produced_run = Path(result["output_dir"])
    assert produced_run.exists()

    manifest_path = produced_run / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer_slug"] == "healthview"
    assert manifest["topic"] == "faulthandler_reports"

    summary_path = produced_run / "summary.md"
    assert summary_path.exists()
    assert "Faulthandler Report Summary" in summary_path.read_text(encoding="utf-8")

    telemetry_path = produced_run / "telemetry.json"
    assert telemetry_path.exists()
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert telemetry["metrics"]["signature_count"] == 2

    assert not (output_dir / "latest_report.json").exists()
    assert not (output_dir / "latest_stacks.csv").exists()


def test_collect_faulthandler_reports_validate_only_missing_topic_dir(tmp_path):
    producer_mod = _load_module("collect_faulthandler_reports", _PRODUCER_PATH)

    repo = tmp_path / "repo"
    output_dir = repo / ".repo_studios" / "command_center" / "reports"

    result = producer_mod.run(
        [
            "--output-dir",
            str(output_dir),
            "--validate-only",
            "--log-level",
            "ERROR",
        ]
    )

    assert result["status"] == "fail"
    assert result["bundle_dir"] is None


def test_collect_faulthandler_reports_returns_no_runs_when_missing(tmp_path):
    producer_mod = _load_module("collect_faulthandler_reports", _PRODUCER_PATH)

    repo = tmp_path / "repo"
    runs_dir = repo / ".repo_studios" / "command_center" / "reports" / "rawview" / "fault_diagnostics_runs"
    output_dir = repo / ".repo_studios" / "command_center" / "reports"

    result = producer_mod.run(
        [
            "--runs-dir",
            str(runs_dir),
            "--output-dir",
            str(output_dir),
            "--log-level",
            "ERROR",
        ]
    )

    assert result["run_dir"] is None
    assert result["artifacts"] is None


def test_collect_faulthandler_reports_timestamp_parsing_helpers(tmp_path):
    producer_mod = _load_module("collect_faulthandler_reports", _PRODUCER_PATH)

    compact = producer_mod._resolve_timestamp("20250101-0000")
    assert compact.tzinfo is not None
    assert producer_mod._timestamp_slug(compact) == "20250101-0000"

    iso = producer_mod._resolve_timestamp("2025-01-01T00:00:00+00:00")
    assert iso.tzinfo is not None
    assert producer_mod._timestamp_slug(iso) == "20250101-0000"

    with pytest.raises(RuntimeError):
        producer_mod._resolve_timestamp("not-a-timestamp")


def test_collect_faulthandler_reports_runs_base_falls_back_to_legacy(tmp_path, monkeypatch):
    producer_mod = _load_module("collect_faulthandler_reports", _PRODUCER_PATH)

    repo = tmp_path / "repo"
    runs_dir = repo / "missing_runs"
    output_dir = repo / "out"
    legacy_dir = repo / producer_mod.LEGACY_RUNS_RELATIVE
    legacy_dir.mkdir(parents=True)

    paths = producer_mod.Paths(repo_root=repo, runs_dir=runs_dir, output_dir=output_dir)

    monkeypatch.delenv("FAULT_LOGS_ALLOW_LEGACY", raising=False)
    resolved = producer_mod._resolve_runs_base(paths)
    assert resolved == legacy_dir

    monkeypatch.setenv("FAULT_LOGS_ALLOW_LEGACY", "0")
    resolved = producer_mod._resolve_runs_base(paths)
    assert resolved == runs_dir
