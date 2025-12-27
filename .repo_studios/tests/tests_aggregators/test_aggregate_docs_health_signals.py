from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_AGGREGATOR_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "aggregators" / "aggregate_docs_health_signals.py"
)


def _load_module(name: str, path: Path):
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _build_inputs(base: Path) -> dict[str, Path]:
    inputs = base / "inputs"
    churn_report = _write_json(
        inputs / "churn.json",
        {
            "summary": {
                "modules_with_code_churn": 4,
                "modules_with_doc_updates": 3,
                "modules_without_doc_updates": 1,
                "allowlisted_modules": ["pkg.skip"],
            },
            "modules_missing_docs": [
                {
                    "module": "pkg.module1",
                    "code_paths": ["pkg/module1.py"],
                    "doc_candidates": [{"path": "docs/module1.md"}],
                    "last_commit_utc": "2025-06-01T00:00:00Z",
                }
            ],
        },
    )
    undocumented_report = _write_json(
        inputs / "undocumented.json",
        {
            "summary": {
                "modules_scanned": 3,
                "modules_with_findings": 2,
                "entities_scanned": 20,
                "entities_missing_docs": 5,
                "docstring_coverage_percent": 75.0,
            },
            "modules": [
                {
                    "module_path": "pkg/module2.py",
                    "coverage_percent": 60,
                    "findings": [{"symbol": "foo"}, {"symbol": "bar"}],
                    "doc_candidates": [{"path": "docs/module2.md"}],
                },
                {
                    "module_path": "pkg/module3.py",
                    "coverage_percent": 80,
                    "findings": [{"symbol": "baz"}],
                },
            ],
        },
    )
    anchor_inventory = _write_json(
        inputs / "anchor_inventory.json",
        {
            "summary": {
                "total_documents": 10,
                "documents_missing_h1": 1,
                "documents_missing_h2": 2,
                "documents_with_cross_file_duplicates": 1,
                "documents_with_repeated_anchors": 1,
                "cross_file_duplicates": 3,
                "total_slugs": 120,
                "top_document_roots": [
                    {"root": "docs/howto", "count": 6},
                    {"root": "docs/reference", "count": 4},
                ],
            }
        },
    )
    anchor_validation = _write_json(
        inputs / "anchor_validation.json",
        {
            "status": "issues",
            "issue_count": 2,
        },
    )
    docs_integrity = _write_json(
        inputs / "docs_integrity.json",
        {
            "status": "warn",
            "summary": {
                "mismatched_blocks": 2,
                "json_blocks_checked": 10,
                "documents_processed": 5,
            },
            "mismatches": [
                {"path": "docs/module1.md", "anchor": "metrics-foo", "reason": "Missing metrics anchor"}
            ],
        },
    )
    metrics_stub = _write_json(
        inputs / "metrics_stub.json",
        {
            "summary": {
                "missing_count": 1,
                "anchors_referenced": 10,
            },
            "missing": [
                {"path": "docs/module1.md", "anchor": "metrics.bar"}
            ],
        },
    )
    placeholder_report = _write_json(
        inputs / "placeholder.json",
        {
            "status": "warn",
            "total_matches": 3,
            "summary": {"by_pattern": {"TODO": 2, "FIXME": 1}},
        },
    )
    monkey_patch_report = _write_json(
        inputs / "monkey.json",
        {
            "status": "warn",
            "total_findings": 2,
            "summary": {"by_category": {"runtime": 1, "tests": 1}},
        },
    )
    return {
        "churn": churn_report,
        "undocumented": undocumented_report,
        "anchor_inventory": anchor_inventory,
        "anchor_validation": anchor_validation,
        "docs_integrity": docs_integrity,
        "metrics_stub": metrics_stub,
        "placeholder": placeholder_report,
        "monkey": monkey_patch_report,
    }


def test_generates_docs_health_bundle(tmp_path):
    aggregator = _load_module("aggregate_docs_health_signals", _AGGREGATOR_PATH)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir()

    inputs = _build_inputs(repo_root)
    output_dir = repo_root / "aggregator_output"

    result = aggregator.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--churn-report",
            str(inputs["churn"]),
            "--undocumented-report",
            str(inputs["undocumented"]),
            "--anchor-inventory",
            str(inputs["anchor_inventory"]),
            "--anchor-validation",
            str(inputs["anchor_validation"]),
            "--docs-integrity",
            str(inputs["docs_integrity"]),
            "--metrics-stub",
            str(inputs["metrics_stub"]),
            "--placeholder-report",
            str(inputs["placeholder"]),
            "--monkey-patch-report",
            str(inputs["monkey"]),
            "--artifacts-to-keep",
            "2",
        ]
    )

    report = json.loads(Path(result["report_json"]).read_text(encoding="utf-8"))
    assert report["schema_version"] == 1
    assert report["summary"]["overall_score"] is not None
    assert report["signals"]["freshness"]["status"] == "warning"
    assert report["signals"]["coverage"]["status"] == "warning"
    assert report["signals"]["structure"]["metrics"]["documents_missing_h1"] == 1
    assert "placeholder_total_matches" in report["signals"]["hygiene"]["metrics"]
    assert report["provenance"]["freshness"]["schema_versions"] == {str(inputs["churn"]): None}

    markdown_path = Path(result["report_md"])
    assert markdown_path.read_text(encoding="utf-8").startswith("# Docs Health Signals")
    tsv_rows = Path(result["signals_tsv"]).read_text(encoding="utf-8").splitlines()
    assert tsv_rows[0].split("\t") == ["category", "metric", "status", "score", "value"]
    assert any(row.startswith("hygiene\tplaceholder_total_matches") for row in tsv_rows[1:])
    csv_rows = Path(result["signals_csv"]).read_text(encoding="utf-8").splitlines()
    assert csv_rows[0].split(",") == ["category", "metric", "status", "score", "value"]
    assert any(row.startswith("hygiene,placeholder_total_matches") for row in csv_rows[1:])


def test_skip_hygiene_omits_category(tmp_path):
    aggregator = _load_module("aggregate_docs_health_signals", _AGGREGATOR_PATH)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir()

    inputs = _build_inputs(repo_root)
    output_dir = repo_root / "aggregator_output"

    result = aggregator.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--churn-report",
            str(inputs["churn"]),
            "--undocumented-report",
            str(inputs["undocumented"]),
            "--anchor-inventory",
            str(inputs["anchor_inventory"]),
            "--anchor-validation",
            str(inputs["anchor_validation"]),
            "--docs-integrity",
            str(inputs["docs_integrity"]),
            "--metrics-stub",
            str(inputs["metrics_stub"]),
            "--skip-hygiene",
        ]
    )

    report = json.loads(Path(result["report_json"]).read_text(encoding="utf-8"))
    assert "hygiene" not in report["signals"]
    assert "hygiene" not in report["summary"]["statuses"]
    assert "hygiene" not in report["summary"]["category_scores"]
