from __future__ import annotations

import json
from pathlib import Path

from command_center.scripts.orchestrators import run_fault_diagnostics_overview as orchestrator


def _seed_fault_artifacts(base_dir: Path) -> None:
    current_name = "fault_artifacts-20240102_000001-run"
    current_summary = {
        "summary": {
            "signature_count": 2,
            "active_signature_count": 2,
            "thread_block_count": 1,
            "severity_buckets": {
                "repeat_offender": 1,
                "multi_hit": 1,
                "single_hit": 0,
            },
        },
        "signatures": [
            {"signature_id": "sig-a"},
            {"signature_id": "sig-b"},
        ],
    }
    current_bundle_summary = {
        "bundle": current_name,
        "metrics": {
            "signature_count": 2,
            "active_signature_count": 2,
            "repeat_offender": 1,
            "multi_hit": 1,
            "single_hit": 0,
            "thread_block_count": 1,
        },
    }
    bundle_dir = base_dir / current_name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "summary.json").write_text(json.dumps(current_summary), encoding="utf-8")
    (bundle_dir / "bundle_summary.json").write_text(json.dumps(current_bundle_summary), encoding="utf-8")
    (base_dir / "latest_summary.json").write_text(json.dumps(current_summary), encoding="utf-8")
    (base_dir / "latest_bundle_summary.json").write_text(json.dumps(current_bundle_summary), encoding="utf-8")


def _seed_producer_report(base_dir: Path) -> None:
    payload = {
        "summary": {
            "severity_buckets": {
                "repeat_offender": 2,
                "multi_hit": 1,
                "single_hit": 0,
            }
        }
    }
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "latest_report.json").write_text(json.dumps(payload), encoding="utf-8")


def test_orchestrator_writes_manifest_with_summarizer(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    consumer_dir = tmp_path / "consumer"
    producer_dir = tmp_path / "producer"
    summarizer_dir = tmp_path / "summaries"
    runs_dir = tmp_path / "runs"
    healthview_root = tmp_path / "healthview"
    producer_cc_dir = tmp_path / "cc_producer"
    consumer_cc_dir = tmp_path / "cc_consumer"

    for directory in (consumer_dir, producer_dir, summarizer_dir, runs_dir, healthview_root, producer_cc_dir, consumer_cc_dir):
        directory.mkdir(parents=True, exist_ok=True)

    _seed_fault_artifacts(consumer_dir)
    _seed_producer_report(producer_dir)

    exit_code = orchestrator.run(
        [
            "--repo-root",
            str(repo_root),
            "--runs-dir",
            str(runs_dir),
            "--producer-output-dir",
            str(producer_dir),
            "--producer-command-center-dir",
            str(producer_cc_dir),
            "--consumer-output-dir",
            str(consumer_dir),
            "--consumer-command-center-dir",
            str(consumer_cc_dir),
            "--summarizer-output-dir",
            str(summarizer_dir),
            "--healthview-root",
            str(healthview_root),
            "--artifacts-to-keep",
            "2",
            "--producer-artifacts-to-keep",
            "2",
            "--consumer-artifacts-to-keep",
            "2",
            "--summarizer-artifacts-to-keep",
            "2",
            "--skip-producer",
            "--skip-consumer",
            "--timestamp",
            "2024-01-02T12:00:00+00:00",
            "--log-level",
            "DEBUG",
        ]
    )

    assert exit_code == 0

    manifest_paths = list(healthview_root.glob("commandview/fault_diagnostics/*/manifest.json"))
    assert manifest_paths
    manifest_path = manifest_paths[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer"] == "commandview"
    assert manifest["topic"] == "fault_diagnostics"
    statuses = {step["status"] for step in manifest["telemetry"]["steps"]}
    assert statuses == {"skipped", "success"}
    summarizer_step = next(step for step in manifest["telemetry"]["steps"] if step["name"] == "summarizer")
    assert summarizer_step["status"] == "success"
    assert summarizer_step["payload"]["slug"]
    summary_path = manifest_path.with_name("summary.md")
    assert summary_path.exists()
    telemetry_path = manifest_path.with_name("telemetry.json")
    assert telemetry_path.exists()
