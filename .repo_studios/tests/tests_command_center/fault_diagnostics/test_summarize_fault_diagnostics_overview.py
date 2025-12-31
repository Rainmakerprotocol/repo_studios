from __future__ import annotations

"""Tests for the summarize_fault_diagnostics_overview summarizer.

Validates HOP-compliant artifact consumption and generation including:
- Consumer artifacts: telemetry.json, manifest.json, summary.md
- HOP timestamp directory format (YYYYMMDD-HHMM)
- No pointer file dependencies
"""
import json
import re
from pathlib import Path

from command_center.scripts.summarizers import summarize_fault_diagnostics_overview as module

# HOP timestamp pattern: YYYYMMDD-HHMM
HOP_TIMESTAMP_PATTERN = re.compile(r"^\d{8}-\d{4}$")


def _write_bundle(
    root: Path,
    name: str,
    telemetry_payload: dict[str, object],
    manifest_payload: dict[str, object],
) -> Path:
    """Write HOP-compliant consumer bundle with telemetry.json and manifest.json."""
    bundle_dir = root / name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "telemetry.json").write_text(json.dumps(telemetry_payload), encoding="utf-8")
    (bundle_dir / "manifest.json").write_text(json.dumps(manifest_payload), encoding="utf-8")
    (bundle_dir / "summary.md").write_text("# Summary\n", encoding="utf-8")
    return bundle_dir


def _write_producer_run(root: Path, name: str, report_payload: dict[str, object]) -> Path:
    """Write HOP-compliant producer run with report.json."""
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(json.dumps(report_payload), encoding="utf-8")
    return run_dir


def test_summarizer_generates_overview(tmp_path: Path) -> None:
    consumer_dir = tmp_path / "consumer"
    producer_dir = tmp_path / "producer"
    summarizer_dir = tmp_path / "summaries"
    consumer_dir.mkdir(parents=True, exist_ok=True)
    producer_dir.mkdir(parents=True, exist_ok=True)
    summarizer_dir.mkdir(parents=True, exist_ok=True)

    # HOP timestamp format: YYYYMMDD-HHMM
    current_name = "20240102-0001"
    previous_name = "20240101-0001"
    producer_run_name = "20240102-0000"

    # Telemetry contains signatures and severity (from old summary.json)
    current_telemetry = {
        "summary": {
            "signature_count": 3,
            "active_signature_count": 2,
            "thread_block_count": 1,
            "severity_buckets": {
                "repeat_offender": 2,
                "multi_hit": 1,
                "single_hit": 0,
            },
        },
        "signatures": [
            {"signature_id": "sig-a"},
            {"signature_id": "sig-b"},
            {"signature_id": "sig-c"},
        ],
    }
    # Manifest contains metrics (from old bundle_summary.json)
    current_manifest = {
        "bundle": current_name,
        "metrics": {
            "signature_count": 3,
            "active_signature_count": 2,
            "repeat_offender": 2,
            "multi_hit": 1,
            "single_hit": 0,
            "thread_block_count": 1,
        },
    }
    previous_telemetry = {
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
    previous_manifest = {
        "bundle": previous_name,
        "metrics": {
            "signature_count": 2,
            "active_signature_count": 2,
            "repeat_offender": 1,
            "multi_hit": 1,
            "single_hit": 0,
            "thread_block_count": 1,
        },
    }

    _write_bundle(consumer_dir, previous_name, previous_telemetry, previous_manifest)
    _write_bundle(consumer_dir, current_name, current_telemetry, current_manifest)

    # Producer report in HOP format (no pointer files)
    producer_report = {
        "summary": {
            "severity_buckets": {
                "repeat_offender": 3,
                "multi_hit": 1,
                "single_hit": 0,
            }
        }
    }
    _write_producer_run(producer_dir, producer_run_name, producer_report)

    result = module.run(
        [
            "--consumer-output-dir",
            str(consumer_dir),
            "--producer-output-dir",
            str(producer_dir),
            "--output-dir",
            str(summarizer_dir),
            "--artifacts-to-keep",
            "2",
            "--timestamp",
            "2024-01-02T12:00:00+00:00",
            "--log-level",
            "DEBUG",
        ]
    )

    assert result["status"] == "ok"
    run_dir = Path(result["run_dir"])
    overview_json = json.loads((run_dir / "fault_diagnostics_overview.json").read_text(encoding="utf-8"))
    assert overview_json["metrics"]["signature_count"] == 3
    assert overview_json["severity_buckets"]["repeat_offender"] == 2
    assert overview_json["producer_repeat_offender"] == 3
    baseline = overview_json["baseline"]
    assert baseline["bundle"] == previous_name
    assert baseline["summary"]["new_signature_ids"] == ["sig-c"]
    assert baseline["summary"]["removed_signature_ids"] == []
    markdown = (run_dir / "fault_diagnostics_overview.md").read_text(encoding="utf-8")
    assert "Fault Diagnostics Overview" in markdown
