from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "scan_monkey_patches.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scan_monkey_patches", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_structured_artifacts(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    src_dir = repo_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    (src_dir / "monkey_patch.py").write_text(
        """
import requests
requests.adapters.DEFAULT_POOLSIZE = 1

import os
os.environ[\"EXAMPLE_FLAG\"] = \"1\"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            "src",
            "--context-lines",
            "1",
            "--artifacts-to-keep",
            "5",
        ]
    )
    assert payload["status"] == "ok"
    assert payload["scan_root"] == "src"

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "monkey_patch_scans"
    run_dirs = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith("monkey_patch_scan-")]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    report_path = run_dir / "report.json"
    matches_path = run_dir / "matches.json"
    assert report_path.exists()
    assert matches_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "ok"
    assert report["scan_root"] == "src"
    assert report["files_scanned"] == 1
    assert report["total_findings"] >= 2
    assert report["summary"]["by_category"]["global_env_mutation"] == 1
    assert report["summary"]["by_category"]["attribute_reassignment_on_import"] >= 1

    matches = json.loads(matches_path.read_text(encoding="utf-8"))
    categories = {entry["category"] for entry in matches}
    assert "global_env_mutation" in categories
    assert "attribute_reassignment_on_import" in categories

    latest_dir = output_dir / "latest"
    assert (latest_dir / "latest_report.json").exists()
    assert (latest_dir / "latest_matches.json").exists()
    assert (run_dir / "log.txt").exists()
    assert (run_dir / "report.md").exists()

    legacy_root = repo_root / ".repo_studios" / "monkey_patch"
    assert legacy_root.exists()
    legacy_runs = [p for p in legacy_root.iterdir() if p.is_dir() and p.name not in {"latest"}]
    assert len(legacy_runs) == 1
    legacy_run = legacy_runs[0]
    assert legacy_run.name[:1].isdigit()

    legacy_report = json.loads((legacy_run / "report.json").read_text(encoding="utf-8"))
    assert isinstance(legacy_report, list)
    legacy_categories = {entry["category"] for entry in legacy_report}
    assert "global_env_mutation" in legacy_categories
    assert "attribute_reassignment_on_import" in legacy_categories

    legacy_summary = json.loads((legacy_run / "summary.json").read_text(encoding="utf-8"))
    assert legacy_summary["run_id"] == payload["run_id"]

    legacy_latest = legacy_root / "latest"
    assert (legacy_latest / "report.json").exists()
    assert (legacy_latest / "summary.json").exists()


def test_prune_history(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    src_dir = repo_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    (src_dir / "first.py").write_text(
        "import builtins\nbuiltins.open = lambda *args, **kwargs: None\n",
        encoding="utf-8",
    )

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "monkey_patch_scans"

    mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            "src",
            "--artifacts-to-keep",
            "1",
        ]
    )

    # Second run should prune history down to a single directory.
    mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            "src",
            "--artifacts-to-keep",
            "1",
        ]
    )

    run_dirs = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith("monkey_patch_scan-")]
    assert len(run_dirs) == 1

    latest_dir = output_dir / "latest"
    assert (latest_dir / "latest_report.json").exists()

    legacy_root = repo_root / ".repo_studios" / "monkey_patch"
    legacy_runs = [p for p in legacy_root.iterdir() if p.is_dir() and p.name not in {"latest"}]
    assert len(legacy_runs) == 1
