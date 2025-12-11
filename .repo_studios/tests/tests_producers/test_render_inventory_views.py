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
    docs_latest = output_dir / "latest_docs_overview.yaml"
    scripts_latest = output_dir / "latest_scripts_overview.yaml"
    tests_latest = output_dir / "latest_tests_overview.yaml"
    summary_latest = output_dir / "latest_summary.json"
    dashboard_latest = output_dir / "latest_dashboard.json"
    assert docs_latest.exists()
    assert scripts_latest.exists()
    assert tests_latest.exists()
    assert summary_latest.exists()
    assert dashboard_latest.exists()

    docs_payload = yaml.safe_load(docs_latest.read_text(encoding="utf-8"))
    scripts_payload = yaml.safe_load(scripts_latest.read_text(encoding="utf-8"))
    tests_payload = yaml.safe_load(tests_latest.read_text(encoding="utf-8"))
    summary_payload = json.loads(summary_latest.read_text(encoding="utf-8"))
    assert len(docs_payload) == 1
    assert len(scripts_payload) == 1
    assert len(tests_payload) == 1
    assert summary_payload["total"] == 3

    healthview_root = tmp_path / ".repo_studios" / "command_center" / "reports" / "healthview" / "inventory_overview"
    assert healthview_root.exists()
    healthview_dirs = [node.name for node in healthview_root.iterdir() if node.is_dir()]
    assert healthview_dirs == ["20251022-1234"]
    healthview_dir = healthview_root / healthview_dirs[0]
    assert healthview_dir.exists()
    assert (healthview_dir / "docs_overview.yaml").exists()
    assert (healthview_dir / "summary.json").exists()

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
    assert docs_stub[0]["redirect"] == "reports/producer_reports/render_inventory_views/latest_docs_overview.yaml"
    summary_stub = json.loads((views_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary_stub["redirect"] == "reports/producer_reports/render_inventory_views/latest_summary.json"

    remaining_runs = sorted(node.name for node in output_dir.iterdir() if node.is_dir())
    assert set(remaining_runs) == {f"render_inventory_views-{slug}", "render_inventory_views-20251020_010101"}
