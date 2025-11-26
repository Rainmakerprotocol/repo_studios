from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "analyze_standards_index_gaps.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "analyze_standards_index_gaps",
        _MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_index(path: Path) -> None:
    payload = textwrap.dedent(
        """
        schema_version: 1
        rules:
          - id: STD-001
            summary: Encourage consistent linting across modules.
        """
    ).strip()
    path.write_text(payload + "\n", encoding="utf-8")


def _write_categories(path: Path, sources: list[Path]) -> None:
    body = ["sources:"]
    for src in sources:
        body.append(f"  - path: {src}")
    body.append("")
    path.write_text("\n".join(body), encoding="utf-8")


def test_basic_shim_delegates_to_command_center():
    mod = _load_module()
    impl = mod.COMMAND_CENTER_MODULE

    assert mod.run is impl.run
    assert mod.main is impl.main
    assert mod.RUN_PREFIX == impl.RUN_PREFIX
    assert mod.PATHS_CONFIG is impl.PATHS_CONFIG
    assert mod.COMMAND_CENTER_SCRIPT_PATH.is_file()


def test_structured_artifacts_created(tmp_path):
    mod = _load_module()
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    docs = workspace / "docs"
    docs.mkdir()
    doc = docs / "std-project-guidelines.md"
    doc.write_text(
        """
        - Avoid direct database access for command handlers.
        - Enforce sandbox boundaries before running external tools.
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    index_path = workspace / "repo_standards_index.yaml"
    _write_index(index_path)

    categories_path = workspace / "standards_categories.yaml"
    _write_categories(categories_path, [doc])

    output_dir = workspace / ".repo_studios" / "reports" / "producer_reports" / "standards_gap_reports"
    legacy_json = workspace / "legacy_gap.json"

    result = mod.run(
        [
            "--repo-root",
            str(workspace),
            "--index-path",
            str(index_path),
            "--categories-path",
            str(categories_path),
            "--output-dir",
            str(output_dir),
            "--json",
            str(legacy_json),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    run_dir = Path(result["run_dir"])
    assert run_dir == output_dir / f"{mod.RUN_PREFIX}-20240101_000000"
    assert run_dir.is_dir()

    report = json.loads(Path(result["report_json"]).read_text(encoding="utf-8"))
    summary = report["summary"]
    possible_keys = {
        str(doc),
        str(doc.relative_to(workspace)),
        str(doc.relative_to(workspace)).replace("\\", "/"),
    }
    key = next((candidate for candidate in possible_keys if candidate in report["sources"]), None)
    assert key is not None
    assert summary == result["summary"]
    assert summary["total_candidates"] == 2
    assert summary["sources_with_candidates"] == 1
    assert summary["top_source_candidates"] == 2
    assert summary["scanned_sources"] == 1
    assert report["total_candidates"] == 2
    assert len(report["sources"][key]) == 2
    assert (run_dir / "report.md").is_file()
    assert (run_dir / "candidates.tsv").is_file()
    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()
    assert (output_dir / "latest_candidates.tsv").is_file()
    assert (output_dir / "latest_bundle_summary.json").is_file()

    bundle_summary = json.loads(Path(result["bundle_summary"]).read_text(encoding="utf-8"))
    assert bundle_summary["total_candidates"] == 2
    assert bundle_summary["sources_with_candidates"] == 1
    assert bundle_summary["top_sources"][0]["path"].endswith(doc.name)

    legacy = json.loads(Path(result["legacy_json"]).read_text(encoding="utf-8"))
    assert legacy["summary"] == summary


def test_pruning_keeps_recent_runs(tmp_path):
    mod = _load_module()
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    docs = workspace / "docs"
    docs.mkdir()
    doc = docs / "std-guidance.md"
    doc.write_text("- Avoid stale dependencies in production.\n", encoding="utf-8")

    index_path = workspace / "repo_standards_index.yaml"
    _write_index(index_path)

    categories_path = workspace / "standards_categories.yaml"
    _write_categories(categories_path, [doc])

    output_dir = workspace / ".repo_studios" / "reports" / "producer_reports" / "standards_gap_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_dirs = [
        output_dir / f"{mod.RUN_PREFIX}-20230101_000000",
        output_dir / f"{mod.RUN_PREFIX}-20230201_000000",
        output_dir / f"{mod.RUN_PREFIX}-20230301_000000",
    ]
    for path in stale_dirs:
        path.mkdir()
        (path / "report.json").write_text("{}", encoding="utf-8")

    mod.run(
        [
            "--repo-root",
            str(workspace),
            "--index-path",
            str(index_path),
            "--categories-path",
            str(categories_path),
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

    expected = {
        f"{mod.RUN_PREFIX}-20230301_000000",
        f"{mod.RUN_PREFIX}-20240203_000000",
    }
    remaining = {path.name for path in output_dir.iterdir() if path.is_dir() and path.name.startswith(mod.RUN_PREFIX)}
    assert remaining == expected
    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()
    assert (output_dir / "latest_candidates.tsv").is_file()
    assert (output_dir / "latest_bundle_summary.json").is_file()
