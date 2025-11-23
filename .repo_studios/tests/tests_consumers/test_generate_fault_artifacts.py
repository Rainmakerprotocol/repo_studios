from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_PRODUCER_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "producers"
    / "collect_faulthandler_reports.py"
)

_CONSUMER_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "consumers"
    / "generate_fault_artifacts.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sample_stacks() -> str:
    return (
        "Current thread 0x0001:\n"
        "  File \"/svc/worker.py\", line 8, in work\n"
        "\n"
        "Thread 0x0002:\n"
        "  File \"/svc/helper.py\", line 3, in assist\n"
    )


def test_fault_artifacts_prefers_producer_report(tmp_path):
    producer_mod = _load_module("collect_faulthandler_reports", _PRODUCER_PATH)
    consumer_mod = _load_module("generate_fault_artifacts", _CONSUMER_PATH)

    repo = tmp_path / "repo"
    run_dir = repo / ".repo_studios" / "faulthandler" / "2025-01-01_000000"
    run_dir.mkdir(parents=True)
    (run_dir / "stacks.log").write_text(_sample_stacks(), encoding="utf-8")

    output_dir = repo / ".repo_studios" / "reports" / "producer_reports" / "faulthandler_reports"

    producer_mod.run(
        [
            "--runs-dir",
            str(run_dir.parent),
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(output_dir),
            "--log-level",
            "ERROR",
        ]
    )
    latest_report = output_dir / "latest_report.json"
    assert latest_report.exists()

    result = consumer_mod.run(
        [
            "--outdir",
            str(run_dir),
            "--report",
            str(latest_report),
        ]
    )

    assert result["outdir"] == str(run_dir.resolve())
    assert result["source_report"] == str(latest_report.resolve())

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

    report = json.loads(latest_report.read_text(encoding="utf-8"))
    assert report["summary"]["signature_count"] == 2
