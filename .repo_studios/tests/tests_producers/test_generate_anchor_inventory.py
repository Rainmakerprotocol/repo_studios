from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_anchor_inventory.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_anchor_inventory", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reports_written_with_duplicates(tmp_path):
    mod = _load_module()
    root = tmp_path / "workspace"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "one.md").write_text("# Shared\n", encoding="utf-8")
    (docs / "two.md").write_text("# Shared\n\n## Details\n\n# Unique\n", encoding="utf-8")

    allow_file = root / "allow.txt"
    allow_file.write_text("overview\n", encoding="utf-8")
    test_file = root / "test_global_anchors.py"
    test_file.write_text(
        'ALLOWED = {\n    "foo",\n    "bar",\n}\n',
        encoding="utf-8",
    )

    output_dir = root / ".repo_studios" / "reports" / "healthview" / "producer_reports" / mod.TOPIC_SLUG

    json_out = root / "baseline.json"

    exit_code = mod.main(
        [
            "--docs-root",
            str(docs),
            "--output-dir",
            str(output_dir),
            "--allow-file",
            str(allow_file),
            "--test-file",
            str(test_file),
            "--json-out",
            str(json_out),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    run_dir = output_dir / "20240101-0000"
    assert run_dir.is_dir()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    report = telemetry["payload"]
    summary = report["summary"]
    assert summary["total_slugs"] == 3
    assert summary["cross_file_duplicates"] == 1
    assert summary["total_documents"] == 2
    assert summary["documents_missing_h1"] == 0
    assert summary["documents_missing_h2"] == 1
    assert summary["documents_with_repeated_anchors"] == 0
    assert summary["documents_with_cross_file_duplicates"] == 2
    assert summary["top_document_roots"][0] == {"root": ".", "count": 2}
    assert report["allowlist_size"] == 2
    duplicate = next(entry for entry in report["duplicates"] if entry["slug"] == "shared")
    assert duplicate["locations"] == ["one.md:1", "two.md:1"]
    assert duplicate["files"] == ["one.md", "two.md"]
    documents = {doc["path"]: doc for doc in report["documents"]}
    assert set(documents) == {"one.md", "two.md"}
    assert documents["one.md"]["h1_count"] == 1
    assert documents["one.md"]["h2_count"] == 0
    assert documents["one.md"]["cross_file_duplicate_slugs"] == ["shared"]
    assert documents["one.md"]["duplicate_slugs"] == []
    assert documents["two.md"]["h1_count"] == 2
    assert documents["two.md"]["h2_count"] == 1
    assert documents["two.md"]["cross_file_duplicate_slugs"] == ["shared"]
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "summary.md").is_file()
    assert (run_dir / "telemetry.json").is_file()

    summary_md = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "Scanned Roots:" in summary_md
    assert f"- `{docs}`" in summary_md
    assert "## Documents Missing H1 Headings (up to 15)" in summary_md
    assert "## Documents Missing H2 Headings (up to 15)" in summary_md

    baseline = json.loads(json_out.read_text(encoding="utf-8"))
    assert baseline["summary"] == summary


def test_pruning_keeps_newest_run(tmp_path):
    mod = _load_module()
    root = tmp_path / "project"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
    output_dir = root / ".repo_studios" / "reports" / "healthview" / "producer_reports" / mod.TOPIC_SLUG
    topic_dir = output_dir
    topic_dir.mkdir(parents=True, exist_ok=True)

    stale_names = ["20230101-0000", "20230201-0000", "20230301-0000"]
    for index, name in enumerate(stale_names, start=1):
        stale_dir = topic_dir / name
        stale_dir.mkdir()
        (stale_dir / "telemetry.json").write_text("{}", encoding="utf-8")
        (stale_dir / "summary.md").write_text("# stale\n", encoding="utf-8")
        (stale_dir / "manifest.json").write_text("{}", encoding="utf-8")
        os.utime(stale_dir, (index, index))

    exit_code = mod.main(
        [
            "--docs-root",
            str(docs),
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
    expected = {"20230301-0000", "20240203-0000"}
    run_dirs = {path.name for path in topic_dir.iterdir() if path.is_dir()}
    assert run_dirs == expected
    for name in expected:
        bundle_dir = topic_dir / name
        assert (bundle_dir / "manifest.json").is_file()
        assert (bundle_dir / "summary.md").is_file()
        assert (bundle_dir / "telemetry.json").is_file()
