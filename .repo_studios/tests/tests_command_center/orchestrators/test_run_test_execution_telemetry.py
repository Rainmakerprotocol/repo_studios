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
    libraries_root = str(_MODULE_PATH.resolve().parents[1])
    while libraries_root in sys.path:
        sys.path.remove(libraries_root)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="telemetry_module")
def telemetry_module_fixture():
    return _load_module()


def test_parse_timestamp_invalid_raises(telemetry_module) -> None:
    with pytest.raises(SystemExit, match=r"Invalid --timestamp value"):
        telemetry_module._parse_timestamp("not-a-timestamp")


def test_parse_timestamp_naive_assumes_utc(telemetry_module) -> None:
    parsed = telemetry_module._parse_timestamp("2025-12-01T01:01:00")
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None
    assert parsed.utcoffset().total_seconds() == 0


def test_latest_directory_selects_latest(tmp_path: Path, telemetry_module) -> None:
    base = tmp_path / "runs"
    base.mkdir(parents=True)
    (base / "20251201-0100").mkdir()
    (base / "20251201-0200").mkdir()
    latest = telemetry_module._latest_directory(base, "")
    assert latest is not None
    assert latest.name == "20251201-0200"


def test_read_json_returns_dict_only(tmp_path: Path, telemetry_module) -> None:
    missing = telemetry_module._read_json(tmp_path / "missing.json")
    assert missing is None

    not_a_dict_path = tmp_path / "list.json"
    not_a_dict_path.write_text("[1, 2, 3]", encoding="utf-8")
    assert telemetry_module._read_json(not_a_dict_path) is None

    dict_path = tmp_path / "payload.json"
    dict_path.write_text(json.dumps({"a": 1}), encoding="utf-8")
    assert telemetry_module._read_json(dict_path) == {"a": 1}


def test_relativize_handles_outside_repo(tmp_path: Path, telemetry_module) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    inside = repo_root / "nested" / "file.json"
    inside.parent.mkdir(parents=True)
    inside.write_text("{}", encoding="utf-8")

    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")

    assert telemetry_module._relativize(inside, repo_root) == "nested/file.json"
    assert telemetry_module._relativize(outside, repo_root) == outside.resolve().as_posix()


def test_load_run_callable_errors_when_missing_run(tmp_path: Path, telemetry_module) -> None:
    script_path = tmp_path / "no_run.py"
    script_path.write_text("VALUE = 1\n", encoding="utf-8")
    with pytest.raises(AttributeError, match=r"callable run\(\) helper"):
        telemetry_module._load_run_callable(script_path, "tests.no_run_module")


def test_load_run_callable_uses_sys_modules_shortcut(telemetry_module, monkeypatch: pytest.MonkeyPatch) -> None:
    module_name = "tests.run_callable_module"

    class DummyModule:
        @staticmethod
        def run(argv):
            return 0

    monkeypatch.setitem(sys.modules, module_name, DummyModule)
    run_callable = telemetry_module._load_run_callable(Path("does_not_matter.py"), module_name)
    assert callable(run_callable)
    assert run_callable([]) == 0


def test_execute_coverage_finds_run_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, telemetry_module) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)

    coverage_output_dir = tmp_path / "producer_reports" / "test_coverage_inventory"
    coverage_output_dir.mkdir(parents=True)

    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text("<coverage></coverage>\n", encoding="utf-8")

    run_timestamp = telemetry_module._parse_timestamp("2025-12-01T01:01:00+00:00")
    run_slug = run_timestamp.strftime("%Y%m%d-%H%M")
    expected_run_dir = coverage_output_dir / run_slug

    def fake_load_run_callable(_script_path: Path, _module_name: str):
        def _runner(_argv):
            expected_run_dir.mkdir(parents=True, exist_ok=True)
            (expected_run_dir / "telemetry.json").write_text(
                json.dumps({"payload": {"summary": {"status": "ok", "total_files": 1}}}),
                encoding="utf-8",
            )
            return 0

        return _runner

    monkeypatch.setattr(telemetry_module, "_load_run_callable", fake_load_run_callable)

    paths = telemetry_module.Paths(
        repo_root=repo_root,
        logs_dir=tmp_path / "logs",
        test_log_reports_dir=tmp_path / "test_log_reports",
        test_log_health_dir=tmp_path / "test_log_health",
        coverage_output_dir=coverage_output_dir,
        coverage_xml=coverage_xml,
        heatmap_output_dir=tmp_path / "heatmap",
        hardening_output_dir=tmp_path / "hardening",
        healthview_root=tmp_path / "healthview",
        summarizer_output_dir=tmp_path / "summarizer",
    )

    options = telemetry_module.Options(
        log_level="ERROR",
        artifacts_to_keep=1,
        collector_keep=1,
        health_keep=1,
        coverage_keep=1,
        heatmap_keep=1,
        hardening_keep=1,
        heatmap_window=10,
        metrics_source=None,
        run_timestamp=run_timestamp,
    )

    outcome = telemetry_module._execute_coverage(paths, options)
    assert outcome.report_dir is not None
    assert outcome.report_dir.resolve() == expected_run_dir.resolve()
    assert outcome.summary is not None
    assert outcome.summary.get("total_files") == 1


def test_execute_hardening_passes_tests_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, telemetry_module) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)

    hardening_output_dir = tmp_path / "producer_reports" / "test_hardening"
    hardening_output_dir.mkdir(parents=True)

    run_timestamp = telemetry_module._parse_timestamp("2025-12-01T01:01:00+00:00")
    expected_slug = run_timestamp.strftime("%Y%m%d-%H%M")
    expected_run_dir = hardening_output_dir / expected_slug

    captured: dict[str, list[str]] = {}

    def fake_load_run_callable(_script_path: Path, _module_name: str):
        def _runner(argv):
            captured["argv"] = list(argv)
            expected_run_dir.mkdir(parents=True, exist_ok=True)
            return {"output_dir": str(expected_run_dir), "status": "ok"}

        return _runner

    monkeypatch.setattr(telemetry_module, "_load_run_callable", fake_load_run_callable)

    paths = telemetry_module.Paths(
        repo_root=repo_root,
        logs_dir=tmp_path / "logs",
        test_log_reports_dir=tmp_path / "test_log_reports",
        test_log_health_dir=tmp_path / "test_log_health",
        coverage_output_dir=tmp_path / "coverage",
        coverage_xml=tmp_path / "coverage.xml",
        heatmap_output_dir=tmp_path / "heatmap",
        hardening_output_dir=hardening_output_dir,
        healthview_root=tmp_path / "healthview",
        summarizer_output_dir=tmp_path / "summarizer",
    )

    options = telemetry_module.Options(
        log_level="ERROR",
        artifacts_to_keep=1,
        collector_keep=1,
        health_keep=1,
        coverage_keep=1,
        heatmap_keep=1,
        hardening_keep=1,
        heatmap_window=10,
        metrics_source=None,
        run_timestamp=run_timestamp,
    )

    outcome = telemetry_module._execute_hardening(paths, options)
    assert outcome.run_dir is not None
    assert outcome.run_dir.resolve() == expected_run_dir.resolve()

    argv = captured.get("argv")
    assert argv is not None
    assert "--tests-dir" in argv
    tests_dir_value = argv[argv.index("--tests-dir") + 1]
    assert tests_dir_value == ".repo_studios/tests"


def test_section_hardening_uses_telemetry_metrics(telemetry_module) -> None:
    telemetry = {
        "metrics": {
            "total_files": 3,
            "total_issues": 7,
            "severity": {"high": 2, "medium": 5, "low": 0},
        },
        "components": {
            "hardening": {
                "summary": {
                    "total_files": 3,
                    "total_issues": 7,
                    "severity_totals": {"high": 2, "medium": 5, "low": 0},
                }
            }
        },
    }
    outcome = telemetry_module.HardeningOutcome(run_dir=None, payload={})
    lines = telemetry_module._section_hardening(outcome, "some/artifact", telemetry)
    rendered = "\n".join(lines)
    assert "| Files Analyzed | 3 |" in rendered
    assert "| Total Issues | 7 |" in rendered
    assert "| High Severity | 2 |" in rendered


def test_section_coverage_prefers_telemetry_metrics_even_when_zero(telemetry_module) -> None:
    telemetry = {
        "metrics": {
            "total_files": 0,
            "total_functions": 10,
            "covered_functions": 0,
            "overall_coverage_pct": 0.0,
            "threshold": 50.0,
        },
        "payload": {
            "summary": {
                "total_files": 123,
                "total_functions": 123,
                "covered_functions": 123,
                "overall_coverage_pct": 99.9,
                "threshold": 99.0,
            }
        },
    }
    outcome = telemetry_module.CoverageOutcome(
        report_dir=None,
        summary={
            "total_files": 999,
            "total_functions": 999,
            "covered_functions": 999,
            "overall_coverage_pct": 88.8,
            "threshold": 88.8,
        },
    )
    lines = telemetry_module._section_coverage(outcome, "some/artifact", telemetry)
    rendered = "\n".join(lines)
    assert "| Files | 0 |" in rendered
    assert "| Functions | 10 |" in rendered
    assert "| Covered | 0 |" in rendered
    assert "| Coverage % | 0.0 |" in rendered


def test_section_coverage_labels_heuristic_threshold_when_none_configured(telemetry_module) -> None:
    telemetry = {
        "metrics": {
            "total_files": 1,
            "total_functions": 2,
            "covered_functions": 0,
            "overall_coverage_pct": 0.0,
            "threshold": None,
        },
        "payload": {"summary": {"threshold": None}},
    }
    outcome = telemetry_module.CoverageOutcome(report_dir=None, summary={"threshold": None})
    lines = telemetry_module._section_coverage(outcome, "some/artifact", telemetry)
    rendered = "\n".join(lines)
    assert "heuristic threshold" in rendered


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

    topic_dir = healthview_root / "orchestrator_reports" / "test_execution_telemetry"
    runs = sorted(child for child in topic_dir.iterdir() if child.is_dir())
    assert len(runs) == 1
    run_folder = runs[0]
    manifest_path = run_folder / "manifest.json"
    summary_path = run_folder / "summary.md"
    telemetry_path = run_folder / "telemetry.json"

    assert summary_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer"] == "orchestrator_reports"
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

    summary_markdown_rel = manifest["artifacts"]["summary_markdown"]
    summary_json_rel = manifest["artifacts"]["summary_json"]
    assert summary_markdown_rel.endswith(
        "summarizer_reports/test_execution_telemetry/20251201-0101/test_execution_telemetry_summary.md"
    )
    assert summary_json_rel.endswith(
        "summarizer_reports/test_execution_telemetry/20251201-0101/test_execution_telemetry_summary.json"
    )

    summary_path = Path(summary_markdown_rel)
    if not summary_path.is_absolute():
        summary_path = (repo_root / summary_path).resolve()
    summary_json_path = Path(summary_json_rel)
    if not summary_json_path.is_absolute():
        summary_json_path = (repo_root / summary_json_path).resolve()

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
    assert summary_json["viewer"] == "summarizer_reports"
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

    def fake_execute_collect(paths, options):
        return telemetry_module.CollectOutcome(
            report_dir=None,
            producer_bundle_dir=None,
            warnings_total=0,
            slow_tests=0,
            payload={"status": "no_data"},
        )

    monkeypatch.setattr(telemetry_module, "_execute_coverage", fake_execute_coverage)
    monkeypatch.setattr(telemetry_module, "_execute_collect", fake_execute_collect)
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
    assert exit_code == 1

    topic_dir = healthview_root / "orchestrator_reports" / "test_execution_telemetry"
    runs = sorted(child for child in topic_dir.iterdir() if child.is_dir())
    assert len(runs) == 1

    run_folder = runs[0]
    manifest_path = run_folder / "manifest.json"
    assert (run_folder / "summary.md").exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary_markdown = Path(manifest["artifacts"]["summary_markdown"])
    if not summary_markdown.is_absolute():
        summary_markdown = (repo_root / summary_markdown).resolve()

    summary_text = summary_markdown.read_text(encoding="utf-8")
    assert "log_report_available: no" in summary_text
    assert "pipeline_status: failed" in summary_text
    assert "- collect: failed" in summary_text