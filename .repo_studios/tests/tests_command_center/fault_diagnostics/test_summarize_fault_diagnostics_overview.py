from __future__ import annotations

import json
from pathlib import Path

from command_center.scripts.summarizers import summarize_fault_diagnostics_overview as module


def _write_bundle(root: Path, name: str, summary_payload: dict[str, object], bundle_summary: dict[str, object]) -> Path:
    bundle_dir = root / name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "summary.json").write_text(json.dumps(summary_payload), encoding="utf-8")
    (bundle_dir / "bundle_summary.json").write_text(json.dumps(bundle_summary), encoding="utf-8")
    return bundle_dir


def test_summarizer_generates_overview(tmp_path: Path) -> None:
    consumer_dir = tmp_path / "consumer"
    producer_dir = tmp_path / "producer"
    summarizer_dir = tmp_path / "summaries"
    consumer_dir.mkdir(parents=True, exist_ok=True)
    producer_dir.mkdir(parents=True, exist_ok=True)
    summarizer_dir.mkdir(parents=True, exist_ok=True)

    current_name = "fault_artifacts-20240102_000001-run"
    previous_name = "fault_artifacts-20240101_000001-old"

    current_summary = {
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
    current_bundle_summary = {
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
    previous_summary = {
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
    previous_bundle_summary = {
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

    _write_bundle(consumer_dir, previous_name, previous_summary, previous_bundle_summary)
    latest_bundle = _write_bundle(consumer_dir, current_name, current_summary, current_bundle_summary)

    (consumer_dir / "latest_summary.json").write_text(json.dumps(current_summary), encoding="utf-8")
    (consumer_dir / "latest_bundle_summary.json").write_text(json.dumps(current_bundle_summary), encoding="utf-8")

    producer_report = {
        "summary": {
            "severity_buckets": {
                "repeat_offender": 3,
                "multi_hit": 1,
                "single_hit": 0,
            }
        }
    }
    (producer_dir / "latest_report.json").write_text(json.dumps(producer_report), encoding="utf-8")

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
