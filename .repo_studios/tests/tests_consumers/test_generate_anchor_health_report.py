from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

_INVENTORY_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "producers"
    / "generate_anchor_inventory.py"
)

_CONSUMER_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "consumers"
    / "generate_anchor_health_report.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_anchor_health_uses_inventory_artifacts(tmp_path):
    inventory_mod = _load_module("generate_anchor_inventory", _INVENTORY_MODULE_PATH)
    consumer_mod = _load_module("generate_anchor_health_report", _CONSUMER_MODULE_PATH)

    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (docs / "one.md").write_text("# Shared\n", encoding="utf-8")
    (docs / "two.md").write_text("# Shared\n\n## Details\n", encoding="utf-8")

    baseline_path = repo / "tests" / "docs"
    baseline_path.mkdir(parents=True)
    (baseline_path / "anchor_slug_baseline.json").write_text(
        json.dumps({"summary": {"cross_file_duplicates": 0}}, indent=2),
        encoding="utf-8",
    )

    inventory_output = (
        repo
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "anchor_inventory_reports"
    )
    inventory_output.mkdir(parents=True, exist_ok=True)

    exit_code = inventory_mod.main(
        [
            "--docs-root",
            str(docs),
            "--output-dir",
            str(inventory_output),
            "--timestamp",
            "2025-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "3",
            "--log-level",
            "ERROR",
        ]
    )
    assert exit_code == 0

    latest_report = inventory_output / "latest_report.json"
    assert latest_report.exists()

    # Remove docs to ensure we do not fall back to rescan
    for child in docs.iterdir():
        child.unlink()
    docs.rmdir()

    cwd = os.getcwd()
    os.chdir(repo)
    try:
        result = consumer_mod.run(inventory_report=latest_report, output_dir=repo / ".repo_studios" / "anchor_health")
    finally:
        os.chdir(cwd)

    report = result["report"]
    assert report["source"] == "inventory"
    assert report["strict_duplicate_count"] == 1
    assert report["inventory_cross_file_duplicates"] == 1
    cluster = next(item for item in report["clusters"] if item["slug"] == "shared")
    assert cluster["files"] == ["one.md", "two.md"]
    assert cluster["locations"] == ["one.md:1", "two.md:1"]
    run_dir = Path(result["run_dir"])
    assert run_dir.exists()
    assert (run_dir / "anchor_report.json").exists()
    assert (run_dir / "anchor_report.md").exists()
    assert (run_dir / "clusters.tsv").exists()

    latest_json = run_dir.parent / "anchor_report_latest.json"
    assert latest_json.exists()