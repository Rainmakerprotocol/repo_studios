from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.fixtures.test_execution_telemetry import (
    TELEMETRY_JUNIT,
    TELEMETRY_LOG,
    TELEMETRY_TIMESTAMP,
    seed_capture_run,
)

_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "command_center"
    / "scripts"
    / "orchestrators"
    / "run_test_execution_telemetry.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("run_test_execution_telemetry", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="telemetry_module")
def telemetry_module_fixture():
    return _load_module()


def test_run_generates_healthview_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, telemetry_module) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    scratch = tmp_path / "telemetry"
    logs_root = scratch / "logs"
    run_dir = seed_capture_run(
        logs_root,
        timestamp=TELEMETRY_TIMESTAMP,
        log_text=TELEMETRY_LOG,
        junit_text=TELEMETRY_JUNIT,
    )

    coverage_output_dir = scratch / "coverage"
    hardening_output_dir = scratch / "hardening"
    heatmap_output_dir = scratch / "heatmap"
    test_log_reports_dir = scratch / "test_log_reports"
    test_log_health_dir = scratch / "test_log_health"
    healthview_root = scratch / "healthview"

    coverage_output_dir.mkdir(parents=True, exist_ok=True)
    hardening_output_dir.mkdir(parents=True, exist_ok=True)
    heatmap_output_dir.mkdir(parents=True, exist_ok=True)

    metrics_source = scratch / "metrics.json"
    metrics_source.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "file": "command_center/scripts/libraries/topic_pipeline.py",
                        "churn": 2,
                        "complexity": 5,
                        "failures": 1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    coverage_report_dir = coverage_output_dir / "test_coverage-20251201_010100"
    hardening_report_dir = hardening_output_dir / "test_hardening-20251201_010100"
    heatmap_report_dir = heatmap_output_dir / "churn_complexity_heatmap-20251201_010100"

    def fake_execute_coverage(paths, options):
        coverage_report_dir.mkdir(parents=True, exist_ok=True)
        report_path = coverage_report_dir / "report.json"
        report_path.write_text(
            json.dumps(
                {
                    "summary": {
                        "status": "ok",
                        "overall_coverage_pct": 98.0,
                        "total_files": 1,
                    }
                }
            ),
            encoding="utf-8",
        )
        return telemetry_module.CoverageOutcome(
            report_dir=coverage_report_dir,
            summary={"status": "ok", "overall_coverage_pct": 98.0, "total_files": 1},
        )

    def fake_execute_hardening(paths, options):
        hardening_report_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "status": "ok",
            "timestamp": "2025-12-01T01:01:00+00:00",
            "summary": {
                "severity_totals": {"high": 0, "medium": 0, "low": 0},
                "total_files": 1,
                "total_test_functions": 1,
                "total_issues": 0,
                "high_priority_files": 0,
                "clean_files": 1,
            },
        }
        (hardening_report_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
        return telemetry_module.HardeningOutcome(run_dir=hardening_report_dir, payload=payload)

    def fake_execute_heatmap(paths, options):
        heatmap_report_dir.mkdir(parents=True, exist_ok=True)
        bundle_summary = heatmap_report_dir / "bundle_summary.json"
        bundle_summary.write_text(json.dumps({"mode": "fixture"}), encoding="utf-8")
        payload = {
            "mode": "fixture",
            "output_dir": str(heatmap_report_dir),
        }
        return telemetry_module.HeatmapOutcome(run_dir=heatmap_report_dir, payload=payload)

    monkeypatch.setattr(telemetry_module, "_execute_coverage", fake_execute_coverage)
    monkeypatch.setattr(telemetry_module, "_execute_hardening", fake_execute_hardening)
    monkeypatch.setattr(telemetry_module, "_execute_heatmap", fake_execute_heatmap)

    args = [
        "--repo-root",
        str(repo_root),
        "--logs-dir",
        str(logs_root),
        "--test-log-reports-dir",
        str(test_log_reports_dir),
        "--test-log-health-dir",
        str(test_log_health_dir),
        "--test-coverage-output-dir",
        str(coverage_output_dir),
        "--test-coverage-xml",
        str((scratch / "coverage.xml")),
        "--heatmap-output-dir",
        str(heatmap_output_dir),
        "--heatmap-metrics-source",
        str(metrics_source),
        "--heatmap-window",
        "10",
        "--hardening-output-dir",
        str(hardening_output_dir),
        "--healthview-root",
        str(healthview_root),
        "--artifacts-to-keep",
        "1",
        "--collector-artifacts-to-keep",
        "1",
        "--health-artifacts-to-keep",
        "1",
        "--coverage-artifacts-to-keep",
        "1",
        "--heatmap-artifacts-to-keep",
        "1",
        "--hardening-artifacts-to-keep",
        "1",
        "--timestamp",
        "2025-12-01T01:01:00+00:00",
        "--log-level",
        "ERROR",
    ]

    coverage_xml = scratch / "coverage.xml"
    coverage_xml.write_text(
        """
<?xml version="1.0"?>
<coverage branch-rate="0" line-rate="1" version="6.5" timestamp="1733014860">
  <sources>
    <source>.</source>
  </sources>
  <packages>
    <package name="sample" branch-rate="0" line-rate="1">
      <classes>
        <class name="topic_pipeline" filename=".repo_studios/command_center/scripts/libraries/topic_pipeline.py" line-rate="1" branch-rate="0">
          <lines>
            <line number="1" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""".strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = telemetry_module.run(args)
    assert exit_code == 0

    topic_dir = healthview_root / "healthview" / "test_execution_telemetry"
    runs = sorted(child for child in topic_dir.iterdir() if child.is_dir())
    assert len(runs) == 1
    run_folder = runs[0]
    manifest_path = run_folder / "manifest.json"
    summary_path = run_folder / "test_execution_telemetry_summary.md"
    summary_json_path = run_folder / "test_execution_telemetry_summary.json"
    telemetry_path = run_folder / "telemetry.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["telemetry"]["success"] is True
    step_names = [step["name"] for step in manifest["telemetry"]["steps"]]
    assert step_names == ["collect", "analyse", "summarize"]
    expected_artifacts = {
        "log_report",
        "coverage_report",
        "heatmap",
        "hardening",
        "health_report",
        "health_bundle_summary",
        "summary_markdown",
        "summary_json",
    }
    assert set(manifest["artifacts"].keys()) == expected_artifacts
    assert manifest["artifacts"]["summary_markdown"].endswith("test_execution_telemetry/20251201-0101/test_execution_telemetry_summary.md")
    assert manifest["artifacts"]["summary_json"].endswith("test_execution_telemetry/20251201-0101/test_execution_telemetry_summary.json")

    summary_text = summary_path.read_text(encoding="utf-8")
    assert "# Test Execution Telemetry Summary" in summary_text
    assert "- run_slug: `20251201-0101`" in summary_text
    assert "- pipeline_status: success" in summary_text
    assert "- log_report_available: yes" in summary_text
    assert "- warnings_total: 1" in summary_text
    assert "- slow_tests_over_threshold: 1" in summary_text
    assert "- heatmap_mode: fixture" in summary_text
    assert "- hardening_status: ok" in summary_text
    assert "- coverage_status: ok" in summary_text
    assert "- health_report_source: producer" in summary_text
    assert "## Runtime Metrics" in summary_text
    assert "| collect | success" in summary_text
    assert "## Failure Highlights" in summary_text
    assert "## Artifact Locations" in summary_text
    assert "## Step Outcomes" in summary_text
    assert "- summarize: success" in summary_text

    summary_json = json.loads(summary_json_path.read_text(encoding="utf-8"))
    assert summary_json["viewer"] == "healthview"
    assert summary_json["topic"] == "test_execution_telemetry"
    assert summary_json["metrics"]["pipeline_status"] == "success"
    assert summary_json["metrics"]["slow_tests_over_threshold"] == 1
    assert summary_json["failures"]["detected"] == 0

    telemetry_payload = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert telemetry_payload["topic"] == "test-execution-telemetry"
    assert len(telemetry_payload["steps"]) == 3


def test_run_handles_missing_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, telemetry_module) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    scratch = tmp_path / "telemetry_missing"
    logs_root = scratch / "logs"
    logs_root.mkdir(parents=True, exist_ok=True)

    coverage_output_dir = scratch / "coverage"
    hardening_output_dir = scratch / "hardening"
    heatmap_output_dir = scratch / "heatmap"
    test_log_reports_dir = scratch / "test_log_reports"
    test_log_health_dir = scratch / "test_log_health"
    healthview_root = scratch / "healthview"

    coverage_output_dir.mkdir(parents=True, exist_ok=True)
    hardening_output_dir.mkdir(parents=True, exist_ok=True)
    heatmap_output_dir.mkdir(parents=True, exist_ok=True)

    coverage_report_dir = coverage_output_dir / "test_coverage-20251201_010100"
    hardening_report_dir = hardening_output_dir / "test_hardening-20251201_010100"
    heatmap_report_dir = heatmap_output_dir / "churn_complexity_heatmap-20251201_010100"

    def fake_execute_coverage(paths, options):
        coverage_report_dir.mkdir(parents=True, exist_ok=True)
        return telemetry_module.CoverageOutcome(report_dir=coverage_report_dir, summary={"status": "ok"})

    def fake_execute_hardening(paths, options):
        hardening_report_dir.mkdir(parents=True, exist_ok=True)
        return telemetry_module.HardeningOutcome(
            run_dir=hardening_report_dir,
            payload={"status": "ok", "summary": {"severity_totals": {"high": 0}}},
        )

    def fake_execute_heatmap(paths, options):
        heatmap_report_dir.mkdir(parents=True, exist_ok=True)
        return telemetry_module.HeatmapOutcome(run_dir=heatmap_report_dir, payload={"mode": "fixture"})

    monkeypatch.setattr(telemetry_module, "_execute_coverage", fake_execute_coverage)
    monkeypatch.setattr(telemetry_module, "_execute_hardening", fake_execute_hardening)
    monkeypatch.setattr(telemetry_module, "_execute_heatmap", fake_execute_heatmap)

    args = [
        "--repo-root",
        str(repo_root),
        "--logs-dir",
        str(logs_root),
        "--test-log-reports-dir",
        str(test_log_reports_dir),
        "--test-log-health-dir",
        str(test_log_health_dir),
        "--test-coverage-output-dir",
        str(coverage_output_dir),
        "--test-coverage-xml",
        str((scratch / "coverage.xml")),
        "--heatmap-output-dir",
        str(heatmap_output_dir),
        "--hardening-output-dir",
        str(hardening_output_dir),
        "--healthview-root",
        str(healthview_root),
        "--artifacts-to-keep",
        "1",
        "--collector-artifacts-to-keep",
        "1",
        "--health-artifacts-to-keep",
        "1",
        "--coverage-artifacts-to-keep",
        "1",
        "--heatmap-artifacts-to-keep",
        "1",
        "--hardening-artifacts-to-keep",
        "1",
        "--timestamp",
        "2025-12-01T03:03:00+00:00",
        "--log-level",
        "ERROR",
    ]

    coverage_xml = scratch / "coverage.xml"
    coverage_xml.write_text(
        """
<?xml version="1.0"?>
<coverage branch-rate="0" line-rate="1" version="6.5" timestamp="1733014860">
  <sources>
    <source>.</source>
  </sources>
  <packages />
</coverage>
""".strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = telemetry_module.run(args)
    assert exit_code == 0

    topic_dir = healthview_root / "healthview" / "test_execution_telemetry"
    runs = sorted(child for child in topic_dir.iterdir() if child.is_dir())
    assert len(runs) == 1
    summary_text = (runs[0] / "test_execution_telemetry_summary.md").read_text(encoding="utf-8")
    assert "log_report_available: no" in summary_text
    assert "- summarize: skipped" in summary_text