"""Tests for the health suite summarizer modernization."""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / ".repo_studios" / "scripts" / "summarizers" / "summarize_health_suite.py"
TIMESTAMP = "2025-12-02T12:34:00+00:00"
TIMESTAMP_SLUG = "2025-12-02_1234"
RUN_SLUG = "20251202-1234"


def _load_module():
    module_name = f"summarize_health_suite_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load summarizer module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _seed_health_artifacts(repo_root: Path) -> None:
    _write_text(
        repo_root / ".repo_studios" / "reports" / "producer_reports" / "monkey_patch_scans" / "trend_latest.md",
        "Latest monkey patch trend summary\nLine 2",
    )

    _write_text(
        repo_root / ".repo_studios" / "dep_health" / TIMESTAMP_SLUG / "report.md",
        "## Summary\n- Dependency hygiene is healthy",
    )

    _write_text(
        repo_root / ".repo_studios" / "reports" / "producer_reports" / "import_graph_reports" / TIMESTAMP_SLUG / "report.md",
        "### Top fan-in (modules most depended on)\n- core\n### Top fan-out (modules with many dependencies)\n- utils\n### Cycles (first 10)\n- packageA -> packageB",
    )

    _write_text(
        repo_root / ".repo_studios" / "reports" / "consumer_reports" / "test_log_health_reports" / TIMESTAMP_SLUG / "report.md",
        "## Summary\n- Tests passing with minor warnings",
    )

    _write_text(
        repo_root / ".repo_studios" / "reports" / "aggregator_reports" / "churn_complexity_heatmap" / TIMESTAMP_SLUG / "heatmap.md",
        "| File | Churn | Complexity |\n|---|---|---|\n| src/foo.py | high | medium |",
    )

    _write_json(
        repo_root / ".repo_studios" / "health" / "faulthandler" / "trends.json",
        [
            {"metrics": {"fault_dumps_total": 10, "unique_signatures_count": 5, "top_signature_repeat_count": 2}},
            {"metrics": {"fault_dumps_total": 12, "unique_signatures_count": 6, "top_signature_repeat_count": 3}},
        ],
    )

    _write_json(
        repo_root / ".repo_studios" / "typecheck" / TIMESTAMP_SLUG / "report.json",
        {
            "status": "FAILED",
            "total_errors": 3,
            "files_with_issues": 2,
            "error_samples": [
                {"path": "src/foo.py", "line": 10, "code": "TC001", "message": "Type mismatch"},
            ],
        },
    )

    _write_json(
        repo_root / ".repo_studios" / "lizard" / TIMESTAMP_SLUG / "report.json",
        {
            "status": "OK",
            "issue_count": 1,
            "notes": "Sample note",
            "targets": ["src/foo.py"],
            "max_ccn": 10,
            "max_length": 50,
        },
    )

    _write_json(
        repo_root / ".repo_studios" / "lizard" / TIMESTAMP_SLUG / "raw.json",
        [
            {
                "filename": str((repo_root / "src" / "foo.py")),
                "function_list": [
                    {"name": "foo", "cyclomatic_complexity": 12, "length": 60},
                ],
            }
        ],
    )

    anchor_dir = repo_root / ".repo_studios" / "anchor_health"
    _write_json(
        anchor_dir / "anchor_report_latest.json",
        {
            "strict_duplicate_count": 4,
            "baseline_cross_file_duplicates": 2,
            "delta_vs_baseline": 2,
            "clusters": [{"slug": "docs", "file_count": 3}],
        },
    )
    anchor_bundle = anchor_dir / f"anchor_health-{TIMESTAMP_SLUG}"
    _write_text(anchor_bundle / "anchor_report.md", "Anchor report placeholder")


def test_run_emits_healthview_bundle(tmp_path: Path) -> None:
    module = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _seed_health_artifacts(repo_root)

    output_dir = repo_root / "artifacts"
    legacy_dir = repo_root / "legacy"
    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--legacy-dir",
            str(legacy_dir),
            "--timestamp",
            TIMESTAMP,
            "--skip-legacy-mirror",
        ]
    )

    assert result["status"] == "ok"
    assert result["slug"] == RUN_SLUG

    run_dir = Path(result["run_dir"])
    assert run_dir.exists()
    assert "healthview" in run_dir.parts

    artifacts = {name: Path(path) for name, path in result["artifacts"].items()}
    json_path = artifacts[f"{module.SUMMARY_STEM}.json"]
    markdown_path = artifacts[f"{module.SUMMARY_STEM}.md"]

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["viewer"] == module.VIEWER_SLUG
    assert payload["topic"] == module.TOPIC_SLUG
    assert payload["run_slug"] == RUN_SLUG
    assert "Dependency hygiene is healthy" in payload["sections"]["dependency_hygiene"]["summary"]
    assert payload["sections"]["typecheck"]["status"] == "FAILED"
    assert payload["sections"]["lizard_complexity"]["top_offenders"]
    assert payload["notes"] == []

    markdown_content = markdown_path.read_text(encoding="utf-8")
    assert "# Health Suite Summary" in markdown_content
    assert "Run slug" in markdown_content
    assert "Typecheck" in markdown_content
    assert "Churn × Complexity" in markdown_content

    assert "legacy_markdown" not in result
