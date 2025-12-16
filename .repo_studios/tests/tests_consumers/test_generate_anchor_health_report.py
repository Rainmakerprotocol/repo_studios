from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

_INVENTORY_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_anchor_inventory.py"

_CONSUMER_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "consumers" / "generate_anchor_health_report.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
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

    inventory_output = repo / ".repo_studios" / "reports" / "producer_reports"
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

    topic_dir = inventory_output / inventory_mod.VIEWER_SLUG / inventory_mod.TOPIC_SLUG
    assert topic_dir.exists()

    # Remove docs to ensure we do not fall back to rescan
    for child in docs.iterdir():
        child.unlink()
    docs.rmdir()

    cwd = os.getcwd()
    os.chdir(repo)
    try:
        result = consumer_mod.run(
            inventory_report=topic_dir,
            output_dir=repo
            / ".repo_studios"
            / "reports"
            / "consumer_reports"
            / "anchor_health_reports",
            artifacts_to_keep=5,
        )
    finally:
        os.chdir(cwd)

    report = result["report"]
    summary = result["summary"]
    assert report["source"] == "inventory"
    assert report["strict_duplicate_count"] == 1
    assert report["inventory_cross_file_duplicates"] == 1
    database_placeholder = report["outputs"]["database"]
    assert database_placeholder["status"] == "not_implemented"
    assert database_placeholder["target"] == "anchor_health_snapshot"
    cluster = next(item for item in report["clusters"] if item["slug"] == "shared")
    assert cluster["files"] == ["one.md", "two.md"]
    assert cluster["locations"] == ["one.md:1", "two.md:1"]
    assert summary["strict_duplicate_count"] == 1
    top_cluster = next(item for item in summary["top_clusters"] if item["slug"] == "shared")
    assert top_cluster["file_count"] == 2
    bundle_dir = Path(result["bundle_dir"])
    assert bundle_dir.exists()
    assert (bundle_dir / "summary.json").exists()
    assert (bundle_dir / "SUMMARY.md").exists()
    assert (bundle_dir / "bundle_summary.json").exists()
    assert (bundle_dir / "anchor_report.json").exists()
    assert (bundle_dir / "anchor_report.md").exists()
    assert (bundle_dir / "clusters.tsv").exists()

    output_dir = bundle_dir.parent
    assert (output_dir / "latest_summary.json").exists()
    assert (output_dir / "latest_SUMMARY.md").exists()
    assert (output_dir / "latest_bundle_summary.json").exists()
    assert (output_dir / "anchor_report_latest.json").exists()
    assert (output_dir / "anchor_report_latest.md").exists()
    assert (output_dir / "clusters_latest.tsv").exists()


def test_anchor_health_falls_back_to_docs_scan(tmp_path):
    consumer_mod = _load_module("generate_anchor_health_report", _CONSUMER_MODULE_PATH)

    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (docs / "alpha.md").write_text("# Intro\n\n## Shared\n", encoding="utf-8")
    (docs / "beta.md").write_text("# Shared\n", encoding="utf-8")

    baseline_path = repo / "tests" / "docs"
    baseline_path.mkdir(parents=True)
    (baseline_path / "anchor_slug_baseline.json").write_text(
        json.dumps({"summary": {"cross_file_duplicates": 0}}, indent=2),
        encoding="utf-8",
    )

    cwd = os.getcwd()
    os.chdir(repo)
    try:
        result = consumer_mod.run(
            output_dir=repo
            / ".repo_studios"
            / "reports"
            / "consumer_reports"
            / "anchor_health_reports",
            artifacts_to_keep=5,
        )
    finally:
        os.chdir(cwd)

    report = result["report"]
    summary = result["summary"]
    assert report["source"] == "scan"
    assert report["strict_duplicate_count"] == 1
    database_placeholder = report["outputs"]["database"]
    assert database_placeholder["status"] == "not_implemented"
    assert database_placeholder["target"] == "anchor_health_snapshot"
    cluster = next(item for item in report["clusters"] if item["slug"] == "shared")
    assert sorted(cluster["files"]) == ["alpha.md", "beta.md"]
    assert summary["source"] == "scan"
    assert summary["strict_duplicate_count"] == 1


def test_anchor_health_prunes_history(tmp_path, monkeypatch):
    consumer_mod = _load_module("generate_anchor_health_report", _CONSUMER_MODULE_PATH)

    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (docs / "one.md").write_text("# Shared\n", encoding="utf-8")
    (docs / "two.md").write_text("# Shared\n", encoding="utf-8")

    baseline_path = repo / "tests" / "docs"
    baseline_path.mkdir(parents=True)
    (baseline_path / "anchor_slug_baseline.json").write_text(
        json.dumps({"summary": {"cross_file_duplicates": 0}}, indent=2),
        encoding="utf-8",
    )

    times = [datetime(2025, 1, 1, 0, minute, tzinfo=consumer_mod.UTC) for minute in range(6)]

    class _FakeDatetime(datetime):
        queue = times.copy()

        @classmethod
        def now(cls, tz=None):
            value = cls.queue.pop(0)
            if tz is None:
                return value.replace(tzinfo=None)
            return value

        @classmethod
        def utcnow(cls):
            return cls.now(consumer_mod.UTC)

    monkeypatch.setattr(consumer_mod, "datetime", _FakeDatetime)

    cwd = os.getcwd()
    os.chdir(repo)
    try:
        for _ in range(6):
            consumer_mod.run(
                output_dir=repo
                / ".repo_studios"
                / "reports"
                / "consumer_reports"
                / "anchor_health_reports",
                artifacts_to_keep=3,
            )
    finally:
        os.chdir(cwd)

    output_dir = (
        repo
        / ".repo_studios"
        / "reports"
        / "consumer_reports"
        / "anchor_health_reports"
    )
    run_dirs = sorted(p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith("anchor_health-"))
    assert len(run_dirs) == 3
    assert all(run_dirs)
