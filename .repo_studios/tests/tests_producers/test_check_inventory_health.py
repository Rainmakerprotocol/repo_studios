from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "check_inventory_health.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_inventory_health", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_default_paths_point_to_repo_root():
    mod = _load_module()
    expected_root = Path(__file__).resolve().parents[2]
    assert mod.ROOT == expected_root
    assert (
        mod.SUMMARY_LATEST
        == expected_root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "healthview"
        / "inventory_overview"
    )
    assert (
        mod.BASELINE_PATH
        == expected_root / ".repo_studios" / "config" / "inventory" / "inventory_summary_baseline.json"
    )
    assert mod.THRESHOLD_PATH == expected_root / "config" / "ci_inventory_thresholds.json"


def test_reports_written_without_issues(tmp_path):
    mod = _load_module()
    root = tmp_path / "workspace"
    root.mkdir()

    summary = root / "summary.json"
    _write_json(
        summary,
        {
            "total": 5,
            "by_status": {"active": 4, "deprecated": 1},
            "by_asset_kind": {"doc": 4, "api": 1},
            "consumers": {"orchestrator": 1},
        },
    )

    baseline = root / "baseline.json"
    _write_json(baseline, {"total": 3})

    thresholds = root / "thresholds.json"
    _write_json(
        thresholds,
        {
            "status_limits": {"deprecated": 2},
            "minimum_assets": {"doc": 2},
            "consumer_required": ["orchestrator"],
        },
    )

    output_dir = root / ".repo_studios" / "command_center" / "reports"

    exit_code = mod.main(
        [
            "--summary",
            str(summary),
            "--baseline",
            str(baseline),
            "--thresholds",
            str(thresholds),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "3",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240101-0000"
    assert run_dir.is_dir()

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "passed"
    assert manifest["viewer_slug"] == mod.VIEWER_SLUG
    assert manifest["topic"] == mod.TOPIC_SLUG
    assert manifest["run_timestamp"] == "20240101-0000"

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["status"] == "passed"
    assert telemetry["summary"]["issues"] == 0
    assert telemetry["summary"]["total_assets"] == 5

    markdown = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "# Inventory Health Report" in markdown
    assert "- (none)" in markdown  # issues block when nothing flagged

    assert not (output_dir / "latest_report.json").exists()
    assert not (output_dir / "latest_report.md").exists()
    assert not (output_dir / "latest_report.log").exists()


def test_threshold_breach_and_pruning(tmp_path):
    mod = _load_module()
    root = tmp_path / "project"
    output_dir = root / ".repo_studios" / "command_center" / "reports"
    topic_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG
    topic_dir.mkdir(parents=True, exist_ok=True)

    stale_names = ["20240101-0000", "20240115-0000"]
    stale_mtimes = [1704067200, 1705276800]  # 2024-01-01, 2024-01-15 UTC
    for name, mtime in zip(stale_names, stale_mtimes, strict=True):
        run_dir = topic_dir / name
        run_dir.mkdir()
        (run_dir / "manifest.json").write_text("{}\n", encoding="utf-8")
        os.utime(run_dir, (mtime, mtime))

    summary = root / "summary.json"
    _write_json(
        summary,
        {
            "total": 10,
            "by_status": {"deprecated": 5},
            "by_asset_kind": {"doc": 1},
            "consumers": {"orchestrator": 0},
        },
    )

    baseline = root / "baseline.json"
    _write_json(baseline, {"total": 8})

    thresholds = root / "thresholds.json"
    _write_json(
        thresholds,
        {
            "status_limits": {"deprecated": 2},
            "minimum_assets": {"doc": 3},
            "consumer_required": ["orchestrator"],
        },
    )

    exit_code = mod.main(
        [
            "--summary",
            str(summary),
            "--baseline",
            str(baseline),
            "--thresholds",
            str(thresholds),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-02-03T00:00:00+00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1
    run_dir = topic_dir / "20240203-0000"
    assert run_dir.is_dir()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["status"] == "failed"
    assert telemetry["summary"]["issues"] >= 1
    issue_ids = {entry["id"] for entry in telemetry["issues"]}
    assert "status:deprecated" in issue_ids
    assert "asset:doc" in issue_ids

    run_dirs = {path.name for path in topic_dir.iterdir() if path.is_dir()}
    assert run_dirs == {"20240115-0000", "20240203-0000"}


def test_run_returns_payload_dict(tmp_path):
    """Verify run(argv) returns structured payload for orchestrator chaining."""
    mod = _load_module()
    root = tmp_path / "workspace"
    root.mkdir()

    summary = root / "summary.json"
    _write_json(
        summary,
        {
            "total": 5,
            "by_status": {"active": 4, "deprecated": 1},
            "by_asset_kind": {"doc": 4, "api": 1},
            "consumers": {"orchestrator": 1},
        },
    )

    baseline = root / "baseline.json"
    _write_json(baseline, {"total": 3})

    thresholds = root / "thresholds.json"
    _write_json(
        thresholds,
        {
            "status_limits": {"deprecated": 2},
            "minimum_assets": {"doc": 2},
            "consumer_required": ["orchestrator"],
        },
    )

    output_dir = root / ".repo_studios" / "reports"

    payload = mod.run(
        [
            "--summary",
            str(summary),
            "--baseline",
            str(baseline),
            "--thresholds",
            str(thresholds),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "3",
            "--log-level",
            "ERROR",
        ]
    )

    # Verify payload structure
    assert payload["status"] == "passed"
    assert payload["exit_code"] == 0
    assert payload["run_id"] == "20240101-0000"
    assert payload["manifest"] is not None
    assert payload["telemetry"] is not None
    assert payload["summary"]["issues_count"] == 0

    # Verify run_dir points to actual directory with artifacts
    run_dir = Path(payload["run_dir"])
    assert run_dir.exists()
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "summary.md").exists()
    assert (run_dir / "telemetry.json").exists()
