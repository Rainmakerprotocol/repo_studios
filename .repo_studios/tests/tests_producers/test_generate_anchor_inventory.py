from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "producers"
    / "generate_anchor_inventory.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "generate_anchor_inventory", _MODULE_PATH
    )
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
        "ALLOWED = {\n    \"foo\",\n    \"bar\",\n}\n",
        encoding="utf-8",
    )

    output_dir = (
        root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "anchor_inventory_reports"
    )

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
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240101_000000"
    assert run_dir.is_dir()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    summary = report["summary"]
    assert summary["total_slugs"] == 3
    assert summary["cross_file_duplicates"] == 1
    assert report["allowlist_size"] == 2
    assert any(entry["slug"] == "shared" for entry in report["duplicates"])
    assert (run_dir / "report.md").is_file()
    assert (run_dir / "slugs.tsv").is_file()
    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()
    assert (output_dir / "latest_slugs.tsv").is_file()

    baseline = json.loads(json_out.read_text(encoding="utf-8"))
    assert baseline["summary"] == summary


def test_pruning_keeps_newest_run(tmp_path):
    mod = _load_module()
    root = tmp_path / "project"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
    output_dir = (
        root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "anchor_inventory_reports"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_names = [
        f"{mod.RUN_PREFIX}-20230101_000000",
        f"{mod.RUN_PREFIX}-20230201_000000",
        f"{mod.RUN_PREFIX}-20230301_000000",
    ]
    for name in stale_names:
        stale_dir = output_dir / name
        stale_dir.mkdir()
        (stale_dir / "report.json").write_text("{}", encoding="utf-8")

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
    expected = {
        f"{mod.RUN_PREFIX}-20230301_000000",
        f"{mod.RUN_PREFIX}-20240203_000000",
    }
    run_dirs = {
        path.name
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(mod.RUN_PREFIX)
    }
    assert run_dirs == expected
    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()
    assert (output_dir / "latest_slugs.tsv").is_file()
