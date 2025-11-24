import json
import importlib.util
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


@pytest.mark.parametrize("artifacts_to_keep", [2])
def test_render_inventory_views_structured_output(tmp_path: Path, artifacts_to_keep: int):
    module = _load_module()
    _seed_inventory(tmp_path)

    output_dir = tmp_path / ".repo_studios" / "reports" / "producer_reports" / "render_inventory_views"
    older = output_dir / "render_inventory_views-20251020_010101"
    older.mkdir(parents=True, exist_ok=True)
    (older / "report.json").write_text("{}", encoding="utf-8")
    stale = output_dir / "render_inventory_views-20251019_010101"
    stale.mkdir(parents=True, exist_ok=True)
    (stale / "report.json").write_text("{}", encoding="utf-8")

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
        str(Path(".repo_studios/reports/producer_reports/render_inventory_views")),
        "--timestamp",
        "2025-10-22T12:34:56+00:00",
        "--artifacts-to-keep",
        str(artifacts_to_keep),
        "--log-level",
        "INFO",
    ]

    module.main(args)

    slug = "20251022_123456"
    run_dir = output_dir / f"render_inventory_views-{slug}"
    assert run_dir.exists()

    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_json["schema_version"] == 1
    assert report_json["counts"]["totals"] == {
        "total": 3,
        "docs": 1,
        "scripts": 1,
        "tests": 1,
    }

    raw_json = json.loads((run_dir / "raw.json").read_text(encoding="utf-8"))
    assert len(raw_json["views"]["docs"]) == 1
    assert len(raw_json["views"]["scripts"]) == 1
    assert raw_json["summary"]["total"] == 3
    assert raw_json["dashboard"]["artifact_types"]["md"] == 1

    latest_json = output_dir / "latest_report.json"
    assert latest_json.exists()
    assert latest_json.read_text(encoding="utf-8") == (run_dir / "report.json").read_text(encoding="utf-8")

    reports_root = tmp_path / ".repo_studios" / "reports"
    docs_latest = reports_root / "docs" / "latest" / "docs_overview.yaml"
    scripts_latest = reports_root / "scripts" / "latest" / "scripts_overview.yaml"
    tests_latest = reports_root / "tests" / "latest" / "tests_overview.yaml"
    summary_latest = reports_root / "summary" / "latest" / "summary.json"
    assert docs_latest.exists()
    assert scripts_latest.exists()
    assert tests_latest.exists()
    assert summary_latest.exists()

    views_dir = tmp_path / ".repo_studios" / "inventory_schema" / "views"
    docs_stub = yaml.safe_load((views_dir / "docs_overview.yaml").read_text(encoding="utf-8"))
    assert docs_stub[0]["redirect"] == "reports/docs/latest/docs_overview.yaml"
    summary_stub = json.loads((views_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary_stub["redirect"] == "reports/summary/latest/summary.json"

    remaining_runs = sorted(node.name for node in output_dir.iterdir() if node.is_dir())
    assert set(remaining_runs) == {f"render_inventory_views-{slug}", "render_inventory_views-20251020_010101"}
