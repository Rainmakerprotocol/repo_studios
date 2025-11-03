from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


SCRIPTS_ROOT = (
    Path(__file__).resolve().parents[4]
    / ".repo_studios"
    / "command_center"
    / "scripts"
)


def _load_libraries():
    try:
        return importlib.import_module("libraries")
    except ModuleNotFoundError:  # pragma: no cover - mirrors existing pattern
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        return importlib.import_module("libraries")


libraries = _load_libraries()
ManifestFile = libraries.ManifestFile
GuardrailState = libraries.GuardrailState
build_automation_manifest = libraries.build_automation_manifest
write_automation_manifest = libraries.write_automation_manifest
TestRunResult = libraries.TestRunResult
build_metrics_summary = libraries.build_metrics_summary


def test_build_automation_manifest_round_trip(tmp_path: Path) -> None:
    timestamp = datetime(2025, 11, 2, 19, 30, tzinfo=timezone.utc)
    metrics_summary = build_metrics_summary(
        schema_version="1.0",
        run_id="run-123",
        targets=("library",),
        lines_touched=42,
        files_changed=2,
        duplicate_groups_resolved=1,
        runtime_seconds=12.5,
        tests_executed={
            "library_integration": TestRunResult(status="passed", duration_seconds=8.0),
            "producer_suite": TestRunResult(status="skipped", duration_seconds=0.0),
        },
        notes="dry run",
    )

    files = {
        "updated": (ManifestFile(path="src/module_a.py", duplicate_groups=("dup-1",)),),
        "skipped": (ManifestFile(path="docs/README.md"),),
        "conflicted": tuple(),
    }

    guardrail = GuardrailState(
        max_files_per_run=15,
        files_considered=2,
        override_applied=False,
        config_path=Path("config/automation_config.yaml"),
        allow_list_source=Path("config/allowed_targets.yaml"),
        metadata={"version": "1"},
    )

    manifest = build_automation_manifest(
        schema_version="1.0",
        run_id="run-123",
        timestamp=timestamp,
        targets=("library",),
        baseline_sha="abcdef123456",
        dry_run=True,
        operator="genet",
        notes="dry run",
        files=files,
        guardrail_state=guardrail,
        metrics_summary=metrics_summary,
        metrics_summary_path="metrics_summary.json",
    )

    payload = manifest.to_dict()
    assert payload["baseline_sha"] == "abcdef123456"
    assert payload["files"]["updated"][0]["duplicate_groups"] == ["dup-1"]
    assert payload["metrics_summary"]["files_changed"] == 2
    assert payload["metrics_summary_path"] == "metrics_summary.json"
    assert payload["guardrails"]["max_files_per_run"] == 15

    output_path = tmp_path / "bundle" / "manifest.json"
    written = write_automation_manifest(manifest, output_path)
    assert written == output_path
    round_trip = json.loads(output_path.read_text(encoding="utf-8"))
    assert round_trip == payload


def test_manifest_rejects_unknown_status() -> None:
    timestamp = datetime.now(timezone.utc)
    metrics_summary = build_metrics_summary(
        schema_version="1.0",
        run_id="run-456",
        targets=("library",),
        lines_touched=0,
        files_changed=0,
        duplicate_groups_resolved=0,
        runtime_seconds=0.0,
        tests_executed={"library_integration": TestRunResult(status="passed", duration_seconds=0.1)},
    )

    with pytest.raises(ValueError):
        build_automation_manifest(
            schema_version="1.0",
            run_id="run-456",
            timestamp=timestamp,
            targets=("library",),
            baseline_sha="deadbeef",
            dry_run=False,
            operator=None,
            notes="",
            files={"unknown": (ManifestFile(path="src/example.py"),)},
            guardrail_state=None,
            metrics_summary=metrics_summary,
            metrics_summary_path="metrics_summary.json",
        )
