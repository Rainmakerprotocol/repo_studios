from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from command_center.scripts.orchestrators import run_docs_health_overview as orchestrator


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _seed_aggregator_inputs(base_dir: Path) -> None:
    _write_json(
        base_dir / "churn" / "latest_report.json",
        {
            "summary": {
                "modules_with_code_churn": 4,
                "modules_with_doc_updates": 3,
                "modules_without_doc_updates": 1,
                "allowlisted_modules": ["pkg.skip"],
            },
        },
    )
    _write_json(
        base_dir / "undocumented" / "latest_report.json",
        {
            "summary": {
                "modules_scanned": 3,
                "modules_with_findings": 2,
                "entities_scanned": 20,
                "entities_missing_docs": 5,
                "docstring_coverage_percent": 75.0,
            },
        },
    )
    _write_json(
        base_dir / "anchor_inventory" / "latest_report.json",
        {
            "summary": {
                "total_documents": 10,
                "documents_missing_h1": 1,
                "documents_missing_h2": 2,
                "documents_with_cross_file_duplicates": 1,
                "documents_with_repeated_anchors": 1,
                "cross_file_duplicates": 3,
                "total_slugs": 120,
            }
        },
    )
    _write_json(
        base_dir / "anchor_validation" / "latest_report.json",
        {
            "status": "issues",
            "issue_count": 2,
        },
    )
    _write_json(
        base_dir / "docs_integrity" / "latest" / "latest_report.json",
        {
            "status": "warn",
            "summary": {
                "mismatched_blocks": 2,
                "json_blocks_checked": 10,
                "documents_processed": 5,
            },
        },
    )
    _write_json(
        base_dir / "metrics_stub" / "latest" / "latest_report.json",
        {
            "status": "warn",
            "summary": {
                "missing_count": 1,
                "anchors_referenced": 10,
            },
        },
    )


@contextmanager
def _patched_aggregator(repo_root: Path, aggregator_output: Path):
    original_loader = orchestrator._load_callable

    def _fake_loader(script_path: Path, module_name: str, attribute: str):
        if script_path.resolve() == (repo_root / orchestrator.AGGREGATOR_SCRIPT).resolve():
            def _fake(argv: list[str] | None = None) -> dict[str, object]:
                argv = argv or []
                output_dir = aggregator_output
                if "--output-dir" in argv:
                    try:
                        output_dir = Path(argv[argv.index("--output-dir") + 1])
                    except (ValueError, IndexError):  # pragma: no cover - defensive guard
                        output_dir = aggregator_output
                run_dir = output_dir / "docs_health_signals-20240102_000000"
                return {
                    "run_dir": str(run_dir),
                    "report_json": str(run_dir / "report.json"),
                    "report_md": str(run_dir / "report.md"),
                    "signals_tsv": str(run_dir / "signals.tsv"),
                    "signals_csv": str(run_dir / "signals.csv"),
                    "bundle_summary": str(run_dir / "bundle_summary.json"),
                    "summary": {
                        "overall_score": 82.5,
                        "category_scores": {"freshness": 80.0, "coverage": 75.0},
                        "statuses": {"freshness": "warning", "coverage": "warning"},
                        "status_counts": {"warning": 2},
                        "weights": {"freshness": 0.35, "coverage": 0.35},
                    },
                }

            return _fake
        return original_loader(script_path, module_name, attribute)

    orchestrator._load_callable = _fake_loader
    try:
        yield
    finally:
        orchestrator._load_callable = original_loader


def test_orchestrator_writes_healthview_manifest(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    aggregator_inputs = tmp_path / "inputs"
    _seed_aggregator_inputs(aggregator_inputs)

    healthview_root = tmp_path / "healthview"
    aggregator_output = tmp_path / "aggregator_output"

    with _patched_aggregator(repo_root, aggregator_output):
        exit_code = orchestrator.run(
            [
                "--repo-root",
                str(repo_root),
                "--doc-index-output-dir",
                str(tmp_path / "doc_index"),
                "--anchor-inventory-output-dir",
                str(aggregator_inputs / "anchor_inventory"),
                "--anchor-validation-output-dir",
                str(aggregator_inputs / "anchor_validation"),
                "--docs-integrity-output-dir",
                str(aggregator_inputs / "docs_integrity"),
                "--metrics-stub-output-dir",
                str(aggregator_inputs / "metrics_stub"),
                "--churn-output-dir",
                str(aggregator_inputs / "churn"),
                "--undocumented-output-dir",
                str(aggregator_inputs / "undocumented"),
                "--aggregator-output-dir",
                str(aggregator_output),
                "--healthview-root",
                str(healthview_root),
                "--artifacts-to-keep",
                "2",
                "--aggregator-artifacts-to-keep",
                "2",
                "--skip-doc-index",
                "--skip-anchor-inventory",
                "--skip-anchor-validation",
                "--skip-docs-integrity",
                "--skip-metrics-stub",
                "--skip-churn",
                "--skip-undocumented",
                "--skip-hygiene-signals",
                "--timestamp",
                "2024-01-02T12:00:00+00:00",
                "--log-level",
                "DEBUG",
            ]
        )

    assert exit_code == 0

    manifest_paths = list(healthview_root.glob("healthview/docs_health/*/manifest.json"))
    assert manifest_paths
    manifest_path = manifest_paths[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer"] == "healthview"
    assert manifest["topic"] == "docs_health"
    assert manifest["summary"]["overall_score"] is not None
    telemetry_steps = {step["name"]: step for step in manifest["telemetry"]["steps"]}
    assert telemetry_steps["aggregate"]["status"] == "success"
    assert telemetry_steps["aggregate"]["payload"]["overall_score"] == manifest["summary"]["overall_score"]
    summary_path = manifest_path.with_name("summary.md")
    assert summary_path.exists()
    telemetry_path = manifest_path.with_name("telemetry.json")
    assert telemetry_path.exists()


def test_orchestrator_blocks_invalid_topic_alias(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    aggregator_inputs = tmp_path / "inputs"
    _seed_aggregator_inputs(aggregator_inputs)

    healthview_root = tmp_path / "healthview"
    alias_dir = healthview_root / "healthview" / "docs_health"
    alias_dir.mkdir(parents=True, exist_ok=True)
    (alias_dir / "latest_summary.md").write_text("stub", encoding="utf-8")

    aggregator_output = tmp_path / "aggregator_output"

    with _patched_aggregator(repo_root, aggregator_output):
        exit_code = orchestrator.run(
            [
                "--repo-root",
                str(repo_root),
                "--doc-index-output-dir",
                str(tmp_path / "doc_index"),
                "--anchor-inventory-output-dir",
                str(aggregator_inputs / "anchor_inventory"),
                "--anchor-validation-output-dir",
                str(aggregator_inputs / "anchor_validation"),
                "--docs-integrity-output-dir",
                str(aggregator_inputs / "docs_integrity"),
                "--metrics-stub-output-dir",
                str(aggregator_inputs / "metrics_stub"),
                "--churn-output-dir",
                str(aggregator_inputs / "churn"),
                "--undocumented-output-dir",
                str(aggregator_inputs / "undocumented"),
                "--aggregator-output-dir",
                str(aggregator_output),
                "--healthview-root",
                str(healthview_root),
                "--artifacts-to-keep",
                "2",
                "--aggregator-artifacts-to-keep",
                "2",
                "--skip-doc-index",
                "--skip-anchor-inventory",
                "--skip-anchor-validation",
                "--skip-docs-integrity",
                "--skip-metrics-stub",
                "--skip-churn",
                "--skip-undocumented",
                "--skip-hygiene-signals",
                "--timestamp",
                "2024-01-03T12:00:00+00:00",
                "--log-level",
                "DEBUG",
            ]
        )

    assert exit_code == 1
    assert (alias_dir / "latest_summary.md").exists()