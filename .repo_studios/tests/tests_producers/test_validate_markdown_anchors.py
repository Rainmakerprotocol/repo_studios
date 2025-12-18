from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "validate_markdown_anchors.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_markdown_anchors", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reports_written_with_issues(tmp_path):
    mod = _load_module()
    root = tmp_path / "workspace"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "sample.md").write_text(
        "# Title\n\nMissing anchor [bad](#missing)\n",
        encoding="utf-8",
    )
    output_dir = root / ".repo_studios" / "reports" / "producer_reports"

    exit_code = mod.main(
        [
            "--root",
            str(root),
            "--glob",
            "docs/**/*.md",
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-01-01T00:00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1
    run_dir = output_dir / "healthview" / "markdown_anchor_validation" / "20240101-0000"
    assert run_dir.is_dir()

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["viewer_slug"] == "healthview"
    assert manifest["topic"] == "markdown_anchor_validation"
    assert manifest["run_timestamp"] == "20240101-0000"

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["metrics"]["issue_count"] == 1
    assert telemetry["payload"]["report"]["issues"]
    assert telemetry["payload"]["report"]["issues"][0]["file"] == "docs/sample.md"
    assert (run_dir / "summary.md").is_file()

    topic_dir = output_dir / "healthview" / "markdown_anchor_validation"
    assert not (topic_dir / "latest_report.json").exists()
    assert not (topic_dir / "latest_report.md").exists()


def test_pruning_keeps_newest_run(tmp_path):
    mod = _load_module()
    root = tmp_path / "project"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "good.md").write_text("# Title\n\n[Self](#title)\n", encoding="utf-8")
    output_dir = root / ".repo_studios" / "reports" / "producer_reports"
    topic_dir = output_dir / "healthview" / "markdown_anchor_validation"
    topic_dir.mkdir(parents=True, exist_ok=True)

    stale_names = [
        "20230101-0000",
        "20230201-0000",
        "20230301-0000",
    ]
    for name in stale_names:
        (topic_dir / name).mkdir()

    exit_code = mod.main(
        [
            "--root",
            str(root),
            "--glob",
            "docs/**/*.md",
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-02-03T00:00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    expected_latest = {"20230301-0000", "20240203-0000"}
    run_dirs = {path.name for path in topic_dir.iterdir() if path.is_dir()}
    assert run_dirs == expected_latest
    assert not (topic_dir / "latest_report.json").exists()
    assert not (topic_dir / "latest_report.md").exists()
