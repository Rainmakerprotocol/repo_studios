from __future__ import annotations

"""Tests for the generate_fault_artifacts consumer script.

Validates HOP-compliant artifact generation including:
- Path structure under .repo_studios/reports/healthview/consumer_reports/fault_artifacts/
- Timestamp directory format (YYYYMMDD-HHMM)
- Base package artifacts: manifest.json, summary.md, telemetry.json
- No pointer files (latest_*)
"""
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path

_PRODUCER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "collect_faulthandler_reports.py"

_CONSUMER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "consumers" / "generate_fault_artifacts.py"

# HOP timestamp pattern: YYYYMMDD-HHMM
HOP_TIMESTAMP_PATTERN = re.compile(r"^\d{8}-\d{4}$")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sample_stacks() -> str:
    return (
        "Current thread 0x0001:\n"
        '  File "/svc/worker.py", line 8, in work\n'
        "\n"
        "Thread 0x0002:\n"
        '  File "/svc/helper.py", line 3, in assist\n'
    )


def test_fault_artifacts_prefers_producer_report(tmp_path):
    consumer_mod = _load_module("generate_fault_artifacts", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    run_dir = (
        repo
        / ".repo_studios"
        / "reports"
        / "healthview"
        / "rawview"
        / "fault_diagnostics"
        / "2025-01-01_000000"
    )
    run_dir.mkdir(parents=True)
    (run_dir / "stacks.log").write_text(_sample_stacks(), encoding="utf-8")

    legacy_report = repo / "legacy_report.json"
    legacy_report.write_text(
        json.dumps(
            {
                "generated_utc": "2025-01-01T00:00:00+00:00",
                "run_dir": str(run_dir),
                "summary": {
                    "signature_count": 2,
                    "active_signature_count": 2,
                    "thread_block_count": 0,
                    "top_frame_limit": 0,
                    "stack_log_exists": True,
                    "stack_text_bytes": 10,
                    "severity_buckets": {"repeat_offender": 0, "multi_hit": 0, "single_hit": 2},
                },
                "signatures": [
                    {
                        "signature_id": "sig-1",
                        "count": 1,
                        "top_module": "svc",
                        "top_func": "work",
                        "top_file": "/svc/worker.py",
                        "top_line": 8,
                        "threads": ["0x0001"],
                        "first_seen_ts": "2025-01-01T00:00:00+00:00",
                        "last_seen_ts": "2025-01-01T00:00:00+00:00",
                    },
                    {
                        "signature_id": "sig-2",
                        "count": 1,
                        "top_module": "svc",
                        "top_func": "assist",
                        "top_file": "/svc/helper.py",
                        "top_line": 3,
                        "threads": ["0x0002"],
                        "first_seen_ts": "2025-01-01T00:00:00+00:00",
                        "last_seen_ts": "2025-01-01T00:00:00+00:00",
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    consumer_output_root = repo / ".repo_studios" / "reports" / "healthview" / "consumer_reports" / "fault_artifacts"
    result = consumer_mod.run(
        [
            "--outdir",
            str(run_dir),
            "--report",
            str(legacy_report),
            "--output-dir",
            str(consumer_output_root),
            "--log-level",
            "DEBUG",
        ]
    )

    assert result["outdir"] == str(run_dir.resolve())
    assert result["source_report"] == str(legacy_report.resolve())
    assert result["source"] == "producer"

    stacks_csv = run_dir / "stacks.csv"
    assert stacks_csv.exists()
    rows = stacks_csv.read_text(encoding="utf-8").splitlines()
    assert rows[0] == "signature_id,count,top_module,top_func,top_file,top_line,threads,first_seen_ts,last_seen_ts"
    assert len(rows) == 3  # header + two signature rows

    summary_md = run_dir / "SUMMARY.md"
    assert summary_md.exists()
    combined_txt = run_dir / "dumps" / "combined.txt"
    assert combined_txt.exists()
    assert "Current thread" in combined_txt.read_text(encoding="utf-8")

    manifest_path = run_dir / "MANIFEST.json"
    assert manifest_path.exists()

    report = json.loads(legacy_report.read_text(encoding="utf-8"))
    assert report["summary"]["signature_count"] == 2

    consumer_dir = Path(result["consumer_report"])
    assert consumer_dir.exists()

    # Validate HOP timestamp directory format
    assert HOP_TIMESTAMP_PATTERN.match(consumer_dir.name), f"Expected YYYYMMDD-HHMM format, got {consumer_dir.name}"

    # Validate HOP artifact names
    telemetry_json = json.loads((consumer_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry_json["source"] == "producer"
    assert telemetry_json["source_report"] == str(legacy_report.resolve())
    assert telemetry_json["run_dir"] == str(run_dir.resolve())
    assert telemetry_json["summary"]["signature_count"] == 2

    summary_md_content = (consumer_dir / "summary.md").read_text(encoding="utf-8")
    assert "Fault Diagnostics Summary" in summary_md_content
    assert "Source References" in summary_md_content
    assert str(run_dir.resolve()) in summary_md_content

    manifest_json = json.loads((consumer_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_json["viewer"] == "healthview"
    assert manifest_json["topic"] == "fault_artifacts"
    assert "generated_at" in manifest_json
    assert "metrics" in manifest_json

    # Validate no pointer files
    pointer_files = [f for f in consumer_output_root.iterdir() if f.is_file() and f.name.startswith("latest_")]
    assert not pointer_files, f"Found deprecated pointer files: {pointer_files}"


def test_fault_artifacts_scans_without_producer(tmp_path):
    consumer_mod = _load_module("generate_fault_artifacts", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    run_dir = (
        repo
        / ".repo_studios"
        / "reports"
        / "healthview"
        / "rawview"
        / "fault_diagnostics"
        / "2025-01-02_000000"
    )
    run_dir.mkdir(parents=True)
    (run_dir / "stacks.log").write_text(_sample_stacks(), encoding="utf-8")

    consumer_output_root = repo / ".repo_studios" / "reports" / "healthview" / "consumer_reports" / "fault_artifacts"
    result = consumer_mod.run(
        [
            "--outdir",
            str(run_dir),
            "--output-dir",
            str(consumer_output_root),
            "--log-level",
            "INFO",
        ]
    )

    assert result["source_report"] is None
    assert result["source"] == "scan"

    consumer_dir = Path(result["consumer_report"])
    assert consumer_dir.exists()

    # Validate HOP timestamp directory format
    assert HOP_TIMESTAMP_PATTERN.match(consumer_dir.name), f"Expected YYYYMMDD-HHMM format, got {consumer_dir.name}"

    # Validate HOP artifact names
    telemetry_json = json.loads((consumer_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry_json["source"] == "scan"
    assert telemetry_json["run_dir"] == str(run_dir.resolve())
    assert telemetry_json["summary"]["signature_count"] >= 1

    # Validate no pointer files
    pointer_files = [f for f in consumer_output_root.iterdir() if f.is_file() and f.name.startswith("latest_")]
    assert not pointer_files, f"Found deprecated pointer files: {pointer_files}"


def test_fault_artifacts_prunes_history(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_fault_artifacts", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    consumer_output_root = repo / ".repo_studios" / "reports" / "healthview" / "consumer_reports" / "fault_artifacts"
    run_dir = (
        repo
        / ".repo_studios"
        / "reports"
        / "healthview"
        / "rawview"
        / "fault_diagnostics"
        / "2025-01-03_000000"
    )
    run_dir.mkdir(parents=True)
    (run_dir / "stacks.log").write_text(_sample_stacks(), encoding="utf-8")

    # Need enough unique timestamps for 6 runs (each run calls datetime.now() multiple times)
    times = [datetime(2025, 1, 3, 0, minute, tzinfo=consumer_mod.UTC) for minute in range(24)]

    class _FakeDatetime(datetime):
        queue = times.copy()

        @classmethod
        def now(cls, tz=None):
            value = cls.queue.pop(0)
            if tz is not None:
                return value.astimezone(tz)
            return value.replace(tzinfo=None)

        @classmethod
        def utcnow(cls):
            return cls.now(consumer_mod.UTC)

    monkeypatch.setattr(consumer_mod, "datetime", _FakeDatetime)

    for _ in range(6):
        consumer_mod.run(
            [
                "--outdir",
                str(run_dir),
                "--output-dir",
                str(consumer_output_root),
                "--artifacts-to-keep",
                "3",
            ]
        )

    bundles = sorted(p for p in consumer_output_root.iterdir() if p.is_dir())
    assert len(bundles) == 3

    # Validate all bundles use HOP timestamp format
    for bundle in bundles:
        assert HOP_TIMESTAMP_PATTERN.match(bundle.name), f"Expected YYYYMMDD-HHMM format, got {bundle.name}"

    # Validate no pointer files
    pointer_files = [f for f in consumer_output_root.iterdir() if f.is_file() and f.name.startswith("latest_")]
    assert not pointer_files, f"Found deprecated pointer files: {pointer_files}"
