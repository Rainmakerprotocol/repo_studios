from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "standards_index_reports"

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

    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240101_000000"
    assert run_dir.is_dir()

    canonical_index_path = repo_root / ".repo_studios" / "scripts" / "repo_standards_index.yaml"
    assert canonical_index_path.is_file()

    report_payload = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_payload["status"] == "ok"
    assert report_payload["summary"]["rule_count"] == 1
    assert report_payload["extraction"]["enabled"] is False
    assert report_payload["pending_path"] is None

    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "# Standards Index Build Report" in report_md

    log_text = (run_dir / "log.txt").read_text(encoding="utf-8")
    assert "status=ok" in log_text

    index_yaml = (run_dir / "index.yaml").read_text(encoding="utf-8")
    raw_yaml = (run_dir / "raw.yaml").read_text(encoding="utf-8")
    raw_txt = (run_dir / "raw.txt").read_text(encoding="utf-8")
    assert index_yaml == raw_yaml == raw_txt

    latest_files = [
        "latest_report.json",
        "latest_report.md",
        "latest_report.log",
        "latest_index.yaml",
        "latest_raw.yaml",
        "latest_raw.txt",
    ]
    for filename in latest_files:
        assert (output_dir / filename).is_file()


def test_failure_path_writes_artifacts_and_prunes(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "standards_index_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_dirs = [
        output_dir / f"{mod.RUN_PREFIX}-20231231_235959",
        output_dir / f"{mod.RUN_PREFIX}-20240101_000001",
    ]
    for path in stale_dirs:
        path.mkdir(parents=True, exist_ok=True)
        (path / "report.json").write_text("{}\n", encoding="utf-8")

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

    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240102_000000"
    assert run_dir.is_dir()

    report_payload = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_payload["status"] == "error"
    assert "Category mapping file not found" in report_payload["notes"]

    log_text = (run_dir / "log.txt").read_text(encoding="utf-8")
    assert "status=error" in log_text

    assert not (run_dir / "index.yaml").exists()
    assert not (output_dir / "latest_index.yaml").exists()

    remaining_dirs = sorted(
        path.name for path in output_dir.iterdir() if path.is_dir() and path.name.startswith(mod.RUN_PREFIX)
    )
    assert remaining_dirs == [f"{mod.RUN_PREFIX}-20240102_000000"]
