from __future__ import annotations

import importlib.util
import json
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
    assert mod.SUMMARY_LATEST == expected_root / "reports" / "summary" / "latest" / "summary.json"
    assert mod.BASELINE_PATH == expected_root / "reports" / "summary" / "main_baseline.json"
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

    output_dir = root / ".repo_studios" / "reports" / "producer_reports" / "inventory_health_reports"

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
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240101_000000"
    assert run_dir.is_dir()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["summary"]["issues"] == 0
    assert report["summary"]["total_assets"] == 5

    markdown = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "# Inventory Health Report" in markdown
    assert "- (none)" in markdown  # issues block when nothing flagged

    assert (run_dir / "log.txt").is_file()
    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()
    assert (output_dir / "latest_report.log").is_file()


def test_threshold_breach_and_pruning(tmp_path):
    mod = _load_module()
    root = tmp_path / "project"
    output_dir = root / ".repo_studios" / "reports" / "producer_reports" / "inventory_health_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_names = [
        f"{mod.RUN_PREFIX}-20240101_000000",
        f"{mod.RUN_PREFIX}-20240115_000000",
    ]
    for name in stale_names:
        run_dir = output_dir / name
        run_dir.mkdir()
        (run_dir / "report.json").write_text("{}\n", encoding="utf-8")

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
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240203_000000"
    assert run_dir.is_dir()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    assert report["summary"]["issues"] >= 1
    issue_ids = {entry["id"] for entry in report["issues"]}
    assert "status:deprecated" in issue_ids
    assert "asset:doc" in issue_ids

    run_dirs = {path.name for path in output_dir.iterdir() if path.is_dir() and path.name.startswith(mod.RUN_PREFIX)}
    assert run_dirs == {
        f"{mod.RUN_PREFIX}-20240115_000000",
        f"{mod.RUN_PREFIX}-20240203_000000",
    }

    latest_log = (output_dir / "latest_report.log").read_text(encoding="utf-8")
    assert "failure_reason=threshold breach detected" in latest_log
