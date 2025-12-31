from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import sys
import textwrap
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "seed_standards_prompts.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("seed_standards_prompts", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_index(repo_root: Path) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    index_dir = repo_root / ".repo_studios" / "scripts"
    index_dir.mkdir(parents=True, exist_ok=True)
    index_content = textwrap.dedent(
        """
        integrity_hash: deadbeef
        categories:
          cat.core:
            title: Core Standards
          cat.doc:
            title: Documentation
        rules:
          - id: STD-001
            summary: Critical rule
            severity: critical
            category_ids: [cat.core]
          - id: STD-002
            summary: Error rule
            severity: error
            category_ids: [cat.core, cat.doc]
          - id: STD-003
            summary: Warn rule
            severity: warn
            category_ids: [cat.doc]
        """
    ).strip()
    (index_dir / "repo_standards_index.yaml").write_text(index_content + "\n", encoding="utf-8")


def test_structured_artifacts(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    _write_index(repo_root)

    legacy_out = repo_root / "seed_legacy.txt"

    payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--include-warn",
            "--artifacts-to-keep",
            "5",
            "--out",
            str(legacy_out),
        ]
    )

    assert payload["status"] == "ok"
    assert payload["seed_integrity_hash"] == "deadbeef"
    assert payload["summary"]["total_rules"] == 3
    assert payload["summary"]["severity_counts"] == {
        "critical": 1,
        "error": 1,
        "warn": 1,
    }

    output_dir = repo_root / mod.DEFAULT_OUTPUT_DIR
    run_dirs = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith("standards_prompt_seed-")]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    for filename in [
        "report.json",
        "report.md",
        "log.txt",
        "seed.json",
        "seed.yaml",
        "seed.txt",
    ]:
        assert (run_dir / filename).exists()

    seed_data = json.loads((run_dir / "seed.json").read_text(encoding="utf-8"))
    assert set(seed_data["categories"].keys()) == {"cat.core", "cat.doc"}

    # HOP compliance: no pointer files
    latest_dir = output_dir / "latest"
    assert not latest_dir.exists()

    assert legacy_out.exists()
    legacy_text = legacy_out.read_text(encoding="utf-8")
    assert "STD-003" in legacy_text


def test_prune_history(tmp_path: Path, monkeypatch) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    _write_index(repo_root)

    output_dir = repo_root / mod.DEFAULT_OUTPUT_DIR

    class _FakeDateTime(_dt.datetime):
        _counter = 0

        @classmethod
        def now(cls, tz=None):
            cls._counter += 1
            base = _dt.datetime(2025, 1, 1, 0, 0, cls._counter)
            if tz is not None:
                return base.replace(tzinfo=tz)
            return base

    monkeypatch.setattr(mod.dt, "datetime", _FakeDateTime)

    for _ in range(2):
        mod.run(
            [
                "--repo-root",
                str(repo_root),
                "--artifacts-to-keep",
                "1",
                "--format",
                "json",
                "--out",
                str(repo_root / "legacy_seed.json"),
            ]
        )

    run_dirs = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith("standards_prompt_seed-")]
    assert len(run_dirs) == 1

    # HOP compliance: no pointer files
    latest_dir = output_dir / "latest"
    assert not latest_dir.exists()
