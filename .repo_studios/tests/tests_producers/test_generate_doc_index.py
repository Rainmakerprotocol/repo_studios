from __future__ import annotations

import csv
import importlib.util
import io
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
    (repo_root / ".repo_studios").mkdir(parents=True)
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

    output_dir = repo_root / ".repo_studios" / "reports" / "healthview"

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
    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240102-0000"
    assert run_dir.is_dir()

    csv_path = run_dir / "doc_index.csv"
    assert csv_path.exists()

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["viewer_slug"] == mod.VIEWER_SLUG
    assert manifest["topic"] == mod.TOPIC_SLUG
    assert manifest["run_timestamp"] == "20240102-0000"

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    payload = telemetry["payload"]

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

    outputs = payload["outputs"]
    files_output = outputs["files"]
    assert files_output["manifest"] == "manifest.json"
    assert files_output["summary"] == "summary.md"
    assert files_output["telemetry"] == "telemetry.json"

    database = outputs["database"]
    assert database["target"] == "placeholder://inventory"
    assert database["implemented"] is False

    metrics = payload["metrics"]
    assert metrics["documents_missing_description_count"] == 0
    assert metrics["duplicate_slug_count"] == 0
    assert metrics["link_density"] == 1.0

    advisories = payload["advisories"]
    assert advisories["documents_missing_description"] == []
    assert advisories["duplicate_slugs"] == {}

    bundle_text = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "# Documentation Index Bundle" in bundle_text
    assert "```json" in bundle_text
    assert "```yaml" in bundle_text
    assert "```csv" in bundle_text
    assert "<!-- markdownlint-disable MD013 -->" in bundle_text
    assert "<!-- markdownlint-enable MD013 -->" in bundle_text

    csv_block = bundle_text.split("```csv", 1)[1].split("```", 1)[0].strip()
    csv_rows = list(csv.reader(io.StringIO(csv_block)))
    assert csv_rows[0] == [
        "folder",
        "filename",
        "level",
        "heading",
        "slug",
        "parent_slug",
        "description",
        "size_bytes",
        "modified_utc",
        "tags",
        "owners",
        "status",
        "contains_placeholder",
        "links",
    ]
    guide_row = next(row for row in csv_rows if row[1] == "docs/guide.md" and row[2] == "h1")
    link_index = csv_rows[0].index("links")
    placeholder_index = csv_rows[0].index("contains_placeholder")
    assert guide_row[link_index] == "../.repo_studios/docs/internal.md"
    assert guide_row[placeholder_index] == "no"

    disk_rows = list(csv.reader(io.StringIO(csv_path.read_text(encoding="utf-8"))))
    assert disk_rows[0] == csv_rows[0]

    assert not (output_dir / "latest_doc_index.json").exists()
    assert not (output_dir / "latest_doc_index_bundle.md").exists()
    assert not (output_dir / "latest_doc_index.csv").exists()


def test_doc_index_retention_keeps_single_run(tmp_path):
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    (repo_root / ".repo_studios").mkdir(parents=True)
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

    topic_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG
    run_dirs = sorted(node.name for node in topic_dir.iterdir() if node.is_dir())
    assert run_dirs == ["20240102-0000"]
    assert not (output_dir / "latest_doc_index.json").exists()


def test_doc_index_refreshes_checkbox_report_and_tier3_index(tmp_path):
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    (repo_root / ".repo_studios").mkdir(parents=True)
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "one.md").write_text("# Title\n\nA paragraph.\n", encoding="utf-8")

    checkbox_script = (
        repo_root
        / ".repo_studios"
        / "docs"
        / "pipeline"
        / "checkbox_report"
        / "checkbox_report.py"
    )
    checkbox_script.parent.mkdir(parents=True)
    checkbox_script.write_text(
        """\
from __future__ import annotations

from pathlib import Path


def main(argv=None):
    args = list(argv or [])
    repo_root = Path(args[args.index('--repo-root') + 1]).resolve()
    output_dir = Path(args[args.index('--output-dir') + 1]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'checkbox_report.csv').write_text('stub\\n', encoding='utf-8')
    (output_dir / 'checkbox_report.md').write_text('# Checkbox Report\\n', encoding='utf-8')
    (repo_root / 'checkbox_invoked.txt').write_text('yes\\n', encoding='utf-8')
""",
        encoding="utf-8",
    )

    tier3_script = (
        repo_root
        / ".repo_studios"
        / "docs"
        / "pipeline"
        / "tier3_index"
        / "generate_tier3_index.py"
    )
    tier3_script.parent.mkdir(parents=True)
    tier3_script.write_text(
        """\
from __future__ import annotations

from pathlib import Path


def run(argv):
    args = list(argv)
    repo_root = Path(args[args.index('--repo-root') + 1]).resolve()
    output = repo_root / '.repo_studios' / 'docs' / 'pipeline' / 'tier3_index' / 'outputs' / 'tier3_scripts_index.yaml'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('version: stub\\n', encoding='utf-8')
    (repo_root / 'tier3_invoked.txt').write_text('yes\\n', encoding='utf-8')
    return 0
""",
        encoding="utf-8",
    )

    output_dir = repo_root / ".repo_studios" / "reports" / "healthview"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-01-02T00:00:00+00:00",
            "--artifacts-to-keep",
            "1",
            "--refresh-checkbox-report",
            "--refresh-tier3-index",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    assert (repo_root / "checkbox_invoked.txt").exists()
    assert (repo_root / "tier3_invoked.txt").exists()

    checkbox_outputs = repo_root / ".repo_studios" / "docs" / "pipeline" / "checkbox_report" / "outputs"
    assert (checkbox_outputs / "checkbox_report.csv").exists()
    assert (checkbox_outputs / "checkbox_report.md").exists()

    tier3_outputs = repo_root / ".repo_studios" / "docs" / "pipeline" / "tier3_index" / "outputs"
    assert (tier3_outputs / "tier3_scripts_index.yaml").exists()

    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240102-0000"
    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    filenames = {doc["filename"] for doc in telemetry["payload"]["documents"]}
    assert ".repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.md" in filenames
