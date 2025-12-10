from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_PRODUCER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "collect_faulthandler_reports.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sample_stacks() -> str:
    return (
        "Current thread 0x0001 (most recent call first):\n"
        '  File "/app/main.py", line 12, in run\n'
        '  File "/app/service.py", line 5, in handle\n'
        "\n"
        "Thread 0x0002:\n"
        '  File "/lib/utils.py", line 7, in helper\n'
    )


def test_collect_faulthandler_reports_emits_artifacts(tmp_path):
    producer_mod = _load_module("collect_faulthandler_reports", _PRODUCER_PATH)

    repo = tmp_path / "repo"
    runs_dir = (
        repo
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "rawview"
        / "fault_diagnostics_runs"
    )
    run_dir = runs_dir / "2025-01-01_000000"
    run_dir.mkdir(parents=True)
    (run_dir / "stacks.log").write_text(_sample_stacks(), encoding="utf-8")

    output_dir = repo / ".repo_studios" / "reports" / "producer_reports" / "faulthandler_reports"

    result = producer_mod.run(
        [
            "--runs-dir",
            str(runs_dir),
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(output_dir),
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    produced_run = Path(result["output_dir"])
    assert produced_run.exists()

    report_path = produced_run / "report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["summary"]["signature_count"] == 2
    assert Path(report["run_dir"]).resolve() == run_dir.resolve()

    markdown_path = produced_run / "report.md"
    assert markdown_path.exists()
    csv_path = produced_run / "stacks.csv"
    assert csv_path.exists()
    combined_path = produced_run / "combined.txt"
    assert combined_path.exists()
    assert "Current thread" in combined_path.read_text(encoding="utf-8")

    latest_json = output_dir / "latest_report.json"
    assert latest_json.exists()
    latest_csv = output_dir / "latest_stacks.csv"
    assert latest_csv.exists()

    manifest_path = run_dir / "MANIFEST.json"
    assert manifest_path.exists()
