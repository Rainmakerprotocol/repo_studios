from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_doc_index.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_doc_index", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_doc_index_produces_artifacts_and_placeholder(tmp_path):
    mod = _load_module()
    repo_root = tmp_path / "repo"
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True)
    internal_dir = repo_root / ".repo_studios" / "docs"
    internal_dir.mkdir(parents=True)
    (repo_root / ".venv").mkdir()

    (docs_dir / "guide.md").write_text(
        """\
# Guide Title

Welcome to the guide. This paragraph should become the description.

## Getting Started

See the [internal doc](../.repo_studios/docs/internal.md) for more details.
""",
        encoding="utf-8",
    )

    (internal_dir / "internal.md").write_text(
        """\
# Internal Notes

Second paragraph lives here.

## Deep Dive

Refer to [Guide](../../docs/guide.md).
""",
        encoding="utf-8",
    )

    (repo_root / ".venv" / "ignore.md").write_text("# Ignore\n", encoding="utf-8")

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "doc_index"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-01-02T00:00:00+00:00",
            "--db-target",
            "placeholder://inventory",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240102_000000"
    assert run_dir.is_dir()

    payload = json.loads((run_dir / "doc_index.json").read_text(encoding="utf-8"))

    summary = payload["summary"]
    assert summary["total_documents"] == 2
    assert summary["total_h1"] == 2
    assert summary["total_h2"] == 2
    assert summary["total_links"] == 2

    documents = {doc["filename"]: doc for doc in payload["documents"]}
    assert "docs/guide.md" in documents
    assert ".repo_studios/docs/internal.md" in documents
    assert ".venv/ignore.md" not in documents

    guide = documents["docs/guide.md"]
    assert guide["description"].startswith("Welcome to the guide")
    assert guide["h1_headings"][0]["title"] == "Guide Title"
    assert guide["h2_headings"][0]["parent_slug"] == guide["h1_headings"][0]["slug"]
    assert guide["links"] == ["../.repo_studios/docs/internal.md"]

    internal = documents[".repo_studios/docs/internal.md"]
    assert internal["description"].startswith("Second paragraph lives here")
    assert internal["links"] == ["../../docs/guide.md"]

    database = payload["outputs"]["database"]
    assert database["target"] == "placeholder://inventory"
    assert database["implemented"] is False

    bundle_text = (run_dir / "doc_index_bundle.md").read_text(encoding="utf-8")
    assert "# Documentation Index Bundle" in bundle_text
    assert "```json" in bundle_text
    assert "```yaml" in bundle_text
    assert "```csv" in bundle_text

    assert (output_dir / "latest_doc_index.json").is_file()
    assert (output_dir / "latest_doc_index_bundle.md").is_file()


def test_doc_index_retention_keeps_single_run(tmp_path):
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "one.md").write_text("# Title\n", encoding="utf-8")

    output_dir = repo_root / "out"

    mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "ERROR",
        ]
    )

    mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-01-02T00:00:00+00:00",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "ERROR",
        ]
    )

    run_dirs = [node.name for node in output_dir.iterdir() if node.is_dir()]
    assert run_dirs == [f"{mod.RUN_PREFIX}-20240102_000000"]
    assert (output_dir / "latest_doc_index.json").is_file()
    assert (output_dir / "latest_doc_index_bundle.md").is_file()
