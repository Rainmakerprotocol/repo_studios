import json
import importlib.util
import os
import sys
from pathlib import Path

import pytest
import yaml

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "render_inventory_views.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("render_inventory_views", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _seed_inventory(tmp_path: Path) -> None:
    schema_root = tmp_path / ".repo_studios" / "inventory_schema"
    schema_root.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "id": "docs.handbook",
            "asset_kind": "document",
            "name": "Handbook",
            "path": "docs/handbook.md",
            "maturity": "legacy",
            "status": "needs_review",
            "consumers": ["coding_agent"],
            "tags": ["reference"],
            "artifact_type": "md",
        },
        {
            "id": "scripts.render_inventory_views",
            "asset_kind": "script",
            "name": "Render Inventory Views",
            "path": "scripts/render_inventory_views.py",
            "roles": ["report_generator"],
            "maturity": "legacy",
            "status": "needs_review",
            "tags": ["inventory"],
            "artifact_type": "py",
        },
        {
            "id": "tests.inventory_views",
            "asset_kind": "test",
            "name": "Inventory Views Test",
            "path": "tests/test_inventory_views.py",
            "status": "needs_review",
            "related_assets": ["scripts.render_inventory_views"],
            "artifact_type": "py",
        },
    ]
    (schema_root / "inventory.yaml").write_text(yaml.safe_dump(entries, sort_keys=False), encoding="utf-8")


def test_render_inventory_views_structured_output(tmp_path: Path):
    module = _load_module()
    _seed_inventory(tmp_path)

    output_dir = tmp_path / ".repo_studios" / "reports" / "producer_reports"
    topic_dir = output_dir / "healthview" / "inventory_overview"
    topic_dir.mkdir(parents=True, exist_ok=True)

    older = topic_dir / "20251020-0101"
    older.mkdir(parents=True, exist_ok=True)
    (older / "manifest.json").write_text("{}", encoding="utf-8")
    os.utime(older, (1760922061, 1760922061))

    stale = topic_dir / "20251019-0101"
    stale.mkdir(parents=True, exist_ok=True)
    (stale / "manifest.json").write_text("{}", encoding="utf-8")
    os.utime(stale, (1760835661, 1760835661))

    args = [
        "--repo-root",
        str(tmp_path),
        "--schema-root",
        str(Path(".repo_studios/inventory_schema")),
        "--views-dir",
        str(Path(".repo_studios/inventory_schema/views")),
        "--reports-root",
        str(Path(".repo_studios/reports")),
        "--output-dir",
        str(Path(".repo_studios/reports/producer_reports")),
        "--timestamp",
        "2025-10-22T12:34:56+00:00",
        "--log-level",
        "INFO",
    ]

    module.main(args)

    slug = "20251022-1234"
    run_dir = output_dir / "healthview" / "inventory_overview" / slug
    assert run_dir.exists()

    produced_files = sorted(node.name for node in run_dir.iterdir() if node.is_file())
    assert produced_files == ["manifest.json", "summary.md", "telemetry.json"]

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["viewer_slug"] == "healthview"
    assert manifest["topic"] == "inventory_overview"
    assert manifest["run_timestamp"] == slug
    assert "inputs" in manifest

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["schema_version"] == 1
    assert telemetry["viewer_slug"] == "healthview"
    assert telemetry["topic"] == "inventory_overview"
    assert telemetry["run_timestamp"] == slug
    assert telemetry["summary"]["total"] == 3
    assert telemetry["counts"]["totals"] == {
        "total": 3,
        "docs": 1,
        "scripts": 1,
        "tests": 1,
    }

    reports_root = tmp_path / ".repo_studios" / "reports"

    legacy_docs_dir = reports_root / "docs"
    legacy_scripts_dir = reports_root / "scripts"
    legacy_tests_dir = reports_root / "tests"
    legacy_summary_dir = reports_root / "summary"
    assert not legacy_docs_dir.exists()
    assert not legacy_scripts_dir.exists()
    assert not legacy_tests_dir.exists()
    assert not legacy_summary_dir.exists()

    views_dir = tmp_path / ".repo_studios" / "inventory_schema" / "views"
    docs_stub = yaml.safe_load((views_dir / "docs_overview.yaml").read_text(encoding="utf-8"))
    assert docs_stub[0]["redirect"] == "reports/producer_reports/healthview/inventory_overview"
    summary_stub = json.loads((views_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary_stub["redirect"] == "reports/producer_reports/healthview/inventory_overview"

    remaining_runs = sorted(node.name for node in topic_dir.iterdir() if node.is_dir())
    assert remaining_runs == [slug]
