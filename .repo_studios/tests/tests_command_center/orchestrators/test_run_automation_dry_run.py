from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "command_center"
    / "scripts"
    / "orchestrators"
    / "run_automation_dry_run.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("run_automation_dry_run", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _seed_guardrail_config(config_dir: Path) -> Path:
    allowed_targets = config_dir / "allowed_targets.yaml"
    allowed_targets.write_text("targets: []\n", encoding="utf-8")
    cfg = config_dir / "automation_config.yaml"
    cfg.write_text(
        (
            "metadata:\n"
            "  version: 1\n"
            "allow_list:\n"
            "  source: allowed_targets.yaml\n"
            "constraints:\n"
            "  max_files_per_run: 10\n"
            "  max_groups_per_run: 5\n"
            "  require_lock_check: true\n"
        ),
        encoding="utf-8",
    )
    return cfg


def test_run_creates_bundle() -> None:
    mod = _load_module()

    repo_root = Path(__file__).resolve().parents[4]
    scratch_root = repo_root / ".repo_studios" / "tmp_tests" / f"automation_dry_run_{uuid.uuid4().hex}"
    output_dir = scratch_root / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    files_payload = {
        "updated": [
            {"path": "src/module_a.py", "duplicate_groups": ["dup-1"]},
            "src/module_b.py",
        ],
        "skipped": ["docs/README.md"],
        "conflicted": [],
    }
    files_file = scratch_root / "files.json"
    files_file.write_text(json.dumps(files_payload), encoding="utf-8")

    tests_payload = {
        "library_integration": {
            "status": "passed",
            "duration_seconds": 45.0,
            "artifacts": ["reports/library.xml"],
        }
    }
    tests_file = scratch_root / "tests.json"
    tests_file.write_text(json.dumps(tests_payload), encoding="utf-8")

    config_dir = scratch_root / "config"
    config_dir.mkdir()
    guardrail_config = _seed_guardrail_config(config_dir)

    post_run_matrix = scratch_root / "post_run_matrix.md"
    post_run_matrix.write_text(
        (
            "# Post Run Matrix\n"
            "\n"
            "## Required Suites\n"
            "| Suite | Command | Purpose |\n"
            "| --- | --- | --- |\n"
            "| Library Integration | `pytest -m integration` | Validate integration path |\n"
            "\n"
            "## Conditional Suites\n"
            "| Condition | Additional Command | Rationale |\n"
            "| --- | --- | --- |\n"
            "| Docs touched | `pytest docs/tests` | Ensure docs tooling passes |\n"
        ),
        encoding="utf-8",
    )

    timestamp = "2025-11-02T19:30:00+00:00"

    try:
        exit_code = mod.run(
            [
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(output_dir.relative_to(repo_root)),
                "--run-id",
                "run-123",
                "--baseline-sha",
                "abcdef123456",
                "--target",
                "library",
                "--lines-touched",
                "120",
                "--files-changed",
                "2",
                "--duplicate-groups-resolved",
                "1",
                "--runtime-seconds",
                "18.5",
                "--files-file",
                str(files_file.relative_to(repo_root)),
                "--tests-file",
                str(tests_file.relative_to(repo_root)),
                "--timestamp",
                timestamp,
                "--operator",
                "genet",
                "--notes",
                "dry run bundle",
                "--dry-run",
                "--guardrail-config",
                str(guardrail_config.relative_to(repo_root)),
                "--post-run-matrix",
                str(post_run_matrix.relative_to(repo_root)),
                "--log-level",
                "ERROR",
            ]
        )
        assert exit_code == 0

        run_dir = output_dir / "automation_manifest-20251102_193000"
        manifest_path = run_dir / "manifest.json"
        metrics_path = run_dir / "metrics_summary.json"
        readme_path = run_dir / "README.md"
        inputs_dir = run_dir / "inputs"

        assert manifest_path.is_file()
        assert metrics_path.is_file()
        assert readme_path.is_file()
        assert inputs_dir.is_dir()
        assert (inputs_dir / files_file.name).is_file()
        assert (inputs_dir / tests_file.name).is_file()
        assert (inputs_dir / guardrail_config.name).is_file()
        assert (inputs_dir / post_run_matrix.name).is_file()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["baseline_sha"] == "abcdef123456"
        assert manifest["guardrails"]["files_considered"] == 2

        readme = readme_path.read_text(encoding="utf-8")
        assert "run_id: `run-123`" in readme
        assert "notes" in readme.lower()
        assert "## Post-Run Test Commands" in readme
        assert "- Library Integration: `pytest -m integration`" in readme
        assert "- Docs touched: `pytest docs/tests`" in readme
        expected_reference = f"Matrix reference: `{Path('inputs') / post_run_matrix.name}`"
        assert expected_reference in readme
    finally:
        if scratch_root.exists():
            shutil.rmtree(scratch_root, ignore_errors=True)


def test_missing_script(tmp_path: Path) -> None:
    mod = _load_module()
    bogus_root = tmp_path / "repo"
    bogus_root.mkdir()
    exit_code = mod.run(
        [
            "--repo-root",
            str(bogus_root),
            "--run-id",
            "run-bogus",
            "--baseline-sha",
            "deadbeef",
            "--target",
            "library",
            "--lines-touched",
            "0",
            "--files-changed",
            "0",
            "--duplicate-groups-resolved",
            "0",
            "--runtime-seconds",
            "0.0",
            "--files-file",
            "files.json",
            "--tests-file",
            "tests.json",
        ]
    )
    assert exit_code == 1
