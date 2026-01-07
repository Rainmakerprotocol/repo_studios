from __future__ import annotations

import json
from pathlib import Path

from command_center.scripts.orchestrators import run_fault_diagnostics_overview as orchestrator


def _seed_fault_artifacts(base_dir: Path) -> None:
    def write_bundle(slug: str, *, signature_ids: list[str]) -> None:
        bundle_dir = base_dir / slug
        bundle_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": 1,
            "viewer": "healthview",
            "topic": "fault_artifacts",
            "generated_at": "2024-01-02T00:00:00+00:00",
            "metrics": {
                "signature_count": len(signature_ids),
                "active_signature_count": len(signature_ids),
                "repeat_offender": 1 if signature_ids else 0,
                "multi_hit": 0,
                "single_hit": 0,
                "thread_block_count": 0,
            },
            "artifacts": {
                "telemetry": "telemetry.json",
                "summary": "summary.md",
            },
            "source": "seed",
            "run_dir": "seed",
        }
        telemetry = {
            "schema_version": 1,
            "viewer": "healthview",
            "topic": "fault_artifacts",
            "run_timestamp": "2024-01-02T00:00:00+00:00",
            "summary": {
                "severity_buckets": {
                    "repeat_offender": 1 if signature_ids else 0,
                    "multi_hit": 0,
                    "single_hit": 0,
                }
            },
            "signatures": [{"signature_id": signature_id} for signature_id in signature_ids],
        }
        (bundle_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (bundle_dir / "telemetry.json").write_text(json.dumps(telemetry), encoding="utf-8")
        (bundle_dir / "summary.md").write_text("# Seed\n", encoding="utf-8")

    write_bundle("20240101-2359", signature_ids=["sig-a"])
    write_bundle("20240102-0001", signature_ids=["sig-a", "sig-b"])


def _seed_producer_report(base_dir: Path) -> None:
    bundle_dir = base_dir / "20240102-0001"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    telemetry = {
        "schema_version": 1,
        "viewer": "healthview",
        "topic": "faulthandler_reports",
        "run_timestamp": "2024-01-02T00:00:00+00:00",
        "metrics": {"repeat_offender_signatures": 2},
    }
    (bundle_dir / "telemetry.json").write_text(json.dumps(telemetry), encoding="utf-8")


def test_orchestrator_writes_manifest_with_summarizer(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    consumer_dir = tmp_path / "consumer"
    producer_dir = tmp_path / "producer"
    summarizer_dir = tmp_path / "summaries"
    runs_dir = tmp_path / "runs"
    orchestrator_dir = tmp_path / "orchestrator"

    for directory in (consumer_dir, producer_dir, summarizer_dir, runs_dir, orchestrator_dir):
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
            "--consumer-output-dir",
            str(consumer_dir),
            "--summarizer-output-dir",
            str(summarizer_dir),
            "--orchestrator-output-dir",
            str(orchestrator_dir),
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

    manifest_paths = list(orchestrator_dir.glob("*/manifest.json"))
    assert manifest_paths
    manifest_path = manifest_paths[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer"] == "healthview"
    assert manifest["topic"] == "fault_diagnostics_overview"
    statuses = {step["status"] for step in manifest["telemetry"]["steps"]}
    assert statuses == {"skipped", "success"}
    summarizer_step = next(step for step in manifest["telemetry"]["steps"] if step["name"] == "summarizer")
    assert summarizer_step["status"] == "success"
    assert summarizer_step["payload"]["slug"]
    summary_path = manifest_path.with_name("summary.md")
    assert summary_path.exists()
    summary_text = summary_path.read_text(encoding="utf-8")
    assert "# Fault Diagnostics Run" in summary_text
    assert "## Pipeline Status" in summary_text
    assert "| Step | Status | Detail |" in summary_text
    assert "## Artifacts" in summary_text
    assert "## Producer" in summary_text
    assert "## Consumer" in summary_text
    assert "## Summarizer" in summary_text
    telemetry_path = manifest_path.with_name("telemetry.json")
    assert telemetry_path.exists()
