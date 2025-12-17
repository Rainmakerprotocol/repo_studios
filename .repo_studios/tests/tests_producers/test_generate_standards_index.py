from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_standards_index.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_standards_index", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_yaml(path: Path, payload: dict) -> None:
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, width=100), encoding="utf-8")


def test_structured_artifacts_success(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()

    instructions_dir = repo_root / ".repo_studios" / "scripts" / ".repo_studios"
    instructions_dir.mkdir(parents=True, exist_ok=True)

    categories_path = instructions_dir / "standards_categories.yaml"
    _write_yaml(
        categories_path,
        {
            "categories": {
                "docs": {
                    "title": "Documentation",
                    "description": "Ensure documentation stays current",
                    "tags": ["guideline"],
                }
            },
            "sources": [
                {
                    "path": "docs/rule_source.md",
                    "categories": ["docs"],
                }
            ],
        },
    )

    seed_path = instructions_dir / "standards_seed.yaml"
    _write_yaml(
        seed_path,
        {
            "rules": [
                {
                    "id": "STD-001",
                    "category_ids": ["docs"],
                    "summary": "Ensure documentation stays updated",
                    "rationale": "Docs drift quickly",
                    "severity": "medium",
                    "applies_to": ["docs"],
                    "source": "seed",
                    "last_updated": "2024-01-01",
                }
            ]
        },
    )

    docs_dir = repo_root / "docs"
    docs_dir.mkdir()
    (docs_dir / "rule_source.md").write_text("# Rules\n", encoding="utf-8")

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "3",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0

    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240101-0000"
    assert run_dir.is_dir()

    canonical_index_path = repo_root / ".repo_studios" / "scripts" / "repo_standards_index.yaml"
    assert canonical_index_path.is_file()

    manifest_path = run_dir / "manifest.json"
    summary_path = run_dir / "summary.md"
    telemetry_path = run_dir / "telemetry.json"
    assert manifest_path.is_file()
    assert summary_path.is_file()
    assert telemetry_path.is_file()

    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert telemetry["metrics"]["status"] == "ok"
    assert telemetry["metrics"]["rule_count"] == 1
    assert telemetry["metrics"]["pending_written"] is False

    summary_md = summary_path.read_text(encoding="utf-8")
    assert "# Standards Index Build Report" in summary_md

    assert not (output_dir / "latest_index.yaml").exists()


def test_failure_path_writes_artifacts_and_prunes(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports"
    (output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG).mkdir(parents=True, exist_ok=True)

    stale_dirs = [
        output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20231231-2359",
        output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240101-0001",
    ]
    for path in stale_dirs:
        path.mkdir(parents=True, exist_ok=True)
        (path / "manifest.json").write_text("{}\n", encoding="utf-8")

    missing_categories = repo_root / "missing" / "categories.yaml"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--categories-path",
            str(missing_categories),
            "--timestamp",
            "2024-01-02T00:00:00+00:00",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1

    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240102-0000"
    assert run_dir.is_dir()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["metrics"]["status"] == "error"
    assert "Category mapping file not found" in telemetry["payload"]["notes"]

    assert not (output_dir / "latest_index.yaml").exists()

    remaining_dirs = sorted(
        path.name
        for path in (output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG).iterdir()
        if path.is_dir()
    )
    assert remaining_dirs == ["20240102-0000"]


def test_missing_source_file_reports_error(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()

    instructions_dir = repo_root / ".repo_studios" / "scripts" / ".repo_studios"
    instructions_dir.mkdir(parents=True, exist_ok=True)

    categories_path = instructions_dir / "standards_categories.yaml"
    _write_yaml(
        categories_path,
        {
            "categories": {
                "docs": {
                    "title": "Documentation",
                    "description": "Ensure documentation stays current",
                    "tags": ["guideline"],
                }
            },
            "sources": [
                {
                    "path": "docs/missing_rule_source.md",
                    "categories": ["docs"],
                }
            ],
        },
    )

    seed_path = instructions_dir / "standards_seed.yaml"
    _write_yaml(
        seed_path,
        {
            "rules": [
                {
                    "id": "STD-001",
                    "category_ids": ["docs"],
                    "summary": "Ensure documentation stays updated",
                    "rationale": "Docs drift quickly",
                    "severity": "medium",
                    "applies_to": ["docs"],
                    "source": "seed",
                    "last_updated": "2024-01-01",
                }
            ]
        },
    )

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--timestamp",
            "2024-01-03T00:00:00+00:00",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1

    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240103-0000"
    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["metrics"]["status"] == "error"
    assert "Missing source files" in telemetry["payload"]["notes"]


def test_extraction_enabled_writes_pending_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()

    instructions_dir = repo_root / ".repo_studios" / "scripts" / ".repo_studios"
    instructions_dir.mkdir(parents=True, exist_ok=True)

    categories_path = instructions_dir / "standards_categories.yaml"
    _write_yaml(
        categories_path,
        {
            "categories": {
                "docs": {
                    "title": "Documentation",
                    "description": "Ensure documentation stays current",
                    "tags": ["guideline"],
                }
            },
            "sources": [
                {
                    "path": "docs/rule_source.md",
                    "categories": ["docs"],
                }
            ],
        },
    )

    seed_path = instructions_dir / "standards_seed.yaml"
    _write_yaml(
        seed_path,
        {
            "rules": [
                {
                    "id": "STD-001",
                    "category_ids": ["docs"],
                    "summary": "Ensure documentation stays updated",
                    "rationale": "Docs drift quickly",
                    "severity": "medium",
                    "applies_to": ["docs"],
                    "source": "seed",
                    "last_updated": "2024-01-01",
                }
            ]
        },
    )

    docs_dir = repo_root / "docs"
    docs_dir.mkdir()
    (docs_dir / "rule_source.md").write_text("# Rules\n", encoding="utf-8")

    extraction_module = instructions_dir / "standards_extraction.py"
    extraction_module.write_text(
        """
from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_rules(path: Path, categories: list[str], seed_ids: set[str], today: str | None = None):
    rule: dict[str, Any] = {
        'id': 'EXTRACT-001',
        'category_ids': categories,
        'summary': 'Extracted rule',
        'rationale': 'Test extraction path',
        'severity': 'low',
        'applies_to': ['docs'],
        'source': str(path),
        'last_updated': today or '2024-01-01',
    }
    return [rule], {'rules_found': 1}
""".lstrip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("ENABLE_STANDARDS_EXTRACTION", "1")
    monkeypatch.setenv("AUTO_ACCEPT_EXTRACTED", "0")

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--timestamp",
            "2024-01-04T00:00:00+00:00",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0

    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240104-0000"
    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["metrics"]["status"] == "pending_extractions"
    assert telemetry["metrics"]["pending_written"] is True
    assert telemetry["metrics"]["extracted_count"] == 1
    assert telemetry["metrics"]["accepted_count"] == 0

    pending_path = repo_root / ".repo_studios" / "scripts" / "repo_standards_pending.yaml"
    assert pending_path.is_file()
