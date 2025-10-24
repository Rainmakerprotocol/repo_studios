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
    output_dir = (
        root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "markdown_anchor_validation_reports"
    )

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
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240101_000000"
    assert run_dir.is_dir()

    data = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert data["issue_count"] == 1
    assert data["issues"]
    assert data["issues"][0]["file"] == "docs/sample.md"
    assert (run_dir / "report.md").is_file()
    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()


def test_pruning_keeps_newest_run(tmp_path):
    mod = _load_module()
    root = tmp_path / "project"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "good.md").write_text("# Title\n\n[Self](#title)\n", encoding="utf-8")
    output_dir = (
        root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "markdown_anchor_validation_reports"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_names = [
        f"{mod.RUN_PREFIX}-20230101_000000",
        f"{mod.RUN_PREFIX}-20230201_000000",
        f"{mod.RUN_PREFIX}-20230301_000000",
    ]
    for name in stale_names:
        (output_dir / name).mkdir()

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
    expected_latest = {f"{mod.RUN_PREFIX}-20230301_000000", f"{mod.RUN_PREFIX}-20240203_000000"}
    run_dirs = {
        path.name
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(mod.RUN_PREFIX)
    }
    assert run_dirs == expected_latest
    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()