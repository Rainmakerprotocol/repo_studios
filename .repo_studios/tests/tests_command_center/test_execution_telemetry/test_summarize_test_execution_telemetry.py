from __future__ import annotations

import json
from pathlib import Path

from command_center.scripts.summarizers import summarize_test_execution_telemetry as module

RUN_SLUG = "20251201-0101"
RUN_TIMESTAMP = "2025-12-01T01:05:00+00:00"
COLLECT_SLUG = "20251201_010100"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_artifacts(repo_root: Path) -> dict[str, str]:
    base_reports = repo_root / ".repo_studios" / "reports"

    log_report_dir = base_reports / "producer_reports" / "test_log_reports" / f"test_log_reports-{COLLECT_SLUG}"
    _write_json(
        log_report_dir / "report.json",
        {
            "warnings_total": 2,
            "slow_tests": 1,
        },
    )

    coverage_dir = base_reports / "producer_reports" / "test_coverage_reports" / f"test_coverage-{COLLECT_SLUG}"
    coverage_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        coverage_dir / "report.json",
        {
            "summary": {
                "status": "ok",
                "overall_coverage_pct": 97.4,
            }
        },
    )

    heatmap_dir = base_reports / "aggregator_reports" / "churn_complexity_heatmap" / f"churn_complexity_heatmap-{COLLECT_SLUG}"
    _write_json(heatmap_dir / "bundle_summary.json", {"mode": "fixture"})

    hardening_dir = (
        repo_root
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "healthview"
        / "test_hardening"
        / RUN_SLUG
    )
    _write_json(
        hardening_dir / "telemetry.json",
        {
            "schema_version": 1,
            "viewer_slug": "healthview",
            "topic": "test_hardening",
            "run_timestamp": RUN_SLUG,
            "status": "ok",
            "components": {
                "hardening": {
                    "summary": {
                        "severity_totals": {
                            "high": 0,
                            "medium": 1,
                            "low": 0,
                        }
                    }
                }
            },
        },
    )

    health_dir = base_reports / "consumer_reports" / "test_log_health_reports" / f"test_log_health-{COLLECT_SLUG}"
    _write_text(health_dir / "report.md", "Health summary placeholder")
    _write_json(
        health_dir / "bundle_summary.json",
        {
            "status": "ok",
            "notes": [],
        },
    )

    artifacts = {
        "log_report": log_report_dir.relative_to(repo_root).as_posix(),
        "coverage_report": coverage_dir.relative_to(repo_root).as_posix(),
        "heatmap": heatmap_dir.relative_to(repo_root).as_posix(),
        "hardening": hardening_dir.relative_to(repo_root).as_posix(),
        "health_report": health_dir.relative_to(repo_root).as_posix(),
        "health_bundle_summary": (health_dir / "bundle_summary.json").relative_to(repo_root).as_posix(),
    }
    return artifacts


def _write_manifest(repo_root: Path, manifest_path: Path, artifacts: dict[str, str], telemetry_payload: dict[str, object]) -> None:
    manifest = {
        "schema_version": 1,
        "viewer": module.VIEWER_SLUG,
        "topic": module.TOPIC_SLUG,
        "run_slug": RUN_SLUG,
        "generated_at": RUN_TIMESTAMP,
        "telemetry": telemetry_payload,
        "artifacts": artifacts,
        "inputs": {
            "logs_dir": "logs",
            "coverage_xml": "coverage.xml",
            "metrics_source": None,
        },
        "catalog": [],
    }
    _write_json(manifest_path, manifest)


def _write_telemetry(telemetry_path: Path) -> dict[str, object]:
    telemetry_payload = {
        "viewer": module.VIEWER_SLUG,
        "topic": "test-execution-telemetry",
        "run_slug": RUN_SLUG,
        "success": True,
        "steps": [
            {
                "name": "collect",
                "status": "success",
                "detail": "log report captured",
                "started_at": "2025-12-01T01:00:00+00:00",
                "finished_at": "2025-12-01T01:00:05+00:00",
                "payload": {
                    "coverage": {
                        "status": "ok",
                        "overall_coverage_pct": 97.4,
                    },
                    "log_report": {
                        "warnings_total": 2,
                        "slow_tests": 1,
                    },
                },
            },
            {
                "name": "analyse",
                "status": "success",
                "detail": "analysis completed",
                "started_at": "2025-12-01T01:00:05+00:00",
                "finished_at": "2025-12-01T01:01:00+00:00",
                "payload": {
                    "hardening_status": "ok",
                    "heatmap_mode": "fixture",
                },
            },
            {
                "name": "summarize",
                "status": "success",
                "detail": "health summary generated",
                "started_at": "2025-12-01T01:01:00+00:00",
                "finished_at": "2025-12-01T01:01:05+00:00",
                "payload": {
                    "source": "producer",
                },
            },
        ],
    }
    _write_json(telemetry_path, telemetry_payload)
    return telemetry_payload


def test_summarizer_generates_summary_bundle(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    artifacts = _seed_artifacts(repo_root)

    manifest_path = repo_root / "artifacts" / "manifest.json"
    telemetry_path = repo_root / "artifacts" / "telemetry.json"
    telemetry_payload = _write_telemetry(telemetry_path)
    _write_manifest(repo_root, manifest_path, artifacts, telemetry_payload)

    output_dir = repo_root / ".repo_studios" / "command_center" / "reports"
    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--manifest",
            str(manifest_path),
            "--telemetry",
            str(telemetry_path),
            "--output-dir",
            str(output_dir),
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "DEBUG",
        ]
    )

    assert result["status"] == "ok"
    assert result["slug"] == RUN_SLUG

    run_dir = Path(result["run_dir"])
    assert run_dir.exists()
    summary_json_path = run_dir / f"{module.SUMMARY_STEM}.json"
    summary_md_path = run_dir / f"{module.SUMMARY_STEM}.md"
    assert summary_json_path.exists()
    assert summary_md_path.exists()

    result_artifacts = {name: Path(path) for name, path in result["artifacts"].items()}
    assert result_artifacts[f"{module.SUMMARY_STEM}.json"] == summary_json_path
    assert result_artifacts[f"{module.SUMMARY_STEM}.md"] == summary_md_path

    summary_payload = json.loads(summary_json_path.read_text(encoding="utf-8"))
    assert summary_payload["viewer"] == module.VIEWER_SLUG
    assert summary_payload["topic"] == module.TOPIC_SLUG
    assert summary_payload["run_slug"] == RUN_SLUG
    metrics = summary_payload["metrics"]
    assert metrics["pipeline_status"] == "success"
    assert metrics["warnings_total"] == 2
    assert metrics["slow_tests_over_threshold"] == 1
    assert metrics["heatmap_mode"] == "fixture"
    assert metrics["hardening_status"] == "ok"
    assert metrics["coverage_status"] == "ok"
    assert metrics["health_report_source"] == "producer"
    components = summary_payload["components"]
    assert components["collect"]["producer_report"].endswith("report.json")
    assert components["hardening"]["payload"]["summary"]["severity_totals"]["high"] == 0
    assert summary_payload["failures"]["detected"] == 0
    assert [step["name"] for step in summary_payload["steps"]] == ["collect", "analyse", "summarize"]

    markdown = summary_md_path.read_text(encoding="utf-8")
    assert "# Test Execution Telemetry Summary" in markdown
    assert "- run_slug: `20251201-0101`" in markdown
    assert "- warnings_total: 2" in markdown
    assert "| collect | success" in markdown
    assert "## Artifact Locations" in markdown
