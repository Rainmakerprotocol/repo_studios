from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[3] / ".repo_studios" / "scripts" / "producers" / "validate_inventory.py"


def _load_module():
    """Load validate_inventory module fresh from disk, bypassing cache."""
    module_name = "validate_inventory_module"
    # Remove any cached version to ensure fresh load
    if module_name in sys.modules:
        del sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module


def _write_yaml(path: Path, data: str) -> None:
    path.write_text(data, encoding="utf-8")


def _base_enums_content() -> str:
    return (
        "roles:\n"
        "  - standards\n"
        "  - playbook\n"
        "consumers:\n"
        "  - internal\n"
        "  - external\n"
        "asset_kind:\n"
        "  - document\n"
        "maturity:\n"
        "  - draft\n"
        "  - published\n"
        "status:\n"
        "  - active\n"
        "  - needs_review\n"
        "artifact_type:\n"
        "  - markdown\n"
    )


def _base_config_content() -> str:
    return "path_existence: {}\n"


def _base_template_content() -> str:
    return "{}\n"


def _write_inventory_record(path: Path, *, record_id: str, target_path: str, status: str = "active") -> None:
    _write_yaml(
        path,
        (
            "- id: {record_id}\n"
            "  name: Sample Asset\n"
            "  path: {target_path}\n"
            "  asset_kind: document\n"
            "  roles:\n"
            "    - standards\n"
            "  maturity: published\n"
            "  description: Example description.\n"
            "  consumers:\n"
            "    - internal\n"
            "  status: {status}\n"
            "  artifact_type: markdown\n"
        ).format(record_id=record_id, target_path=target_path, status=status),
    )


def test_validate_inventory_success_and_pruning(tmp_path):
    module = _load_module()
    repo_root = tmp_path
    schema_root = repo_root / ".repo_studios" / "inventory_schema"
    schema_root.mkdir(parents=True)

    enums_path = schema_root / "enums.yaml"
    template_path = schema_root / "inventory_entry_template.yaml"
    config_path = schema_root / "validator_config.yaml"
    inventory_path = schema_root / "docs.yaml"

    _write_yaml(enums_path, _base_enums_content())
    _write_yaml(template_path, _base_template_content())
    _write_yaml(config_path, _base_config_content())

    docs_root = repo_root / "docs"
    target_doc = docs_root / "handbook.md"
    target_doc.parent.mkdir(parents=True)
    target_doc.write_text("sample", encoding="utf-8")

    _write_inventory_record(inventory_path, record_id="docs-handbook", target_path="docs/handbook.md")

    output_dir = repo_root / "artifacts"

    exit_code = module.main(
        [
            "--repo-root",
            str(repo_root),
            "--schema-root",
            str(schema_root),
            "--enums-path",
            str(enums_path),
            "--template-path",
            str(template_path),
            "--config-path",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2025-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "CRITICAL",
        ]
    )

    assert exit_code == 0

    # HOP-compliant directory format: YYYYMMDD-HHMM (timestamp only, no prefix)
    run_dir = output_dir / "20250101-0000"
    # HOP base package: manifest.json (was report.json)
    manifest_json = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_json["status"] == "ok"
    assert manifest_json["summary"]["issue_counts"]["errors"] == 0
    assert manifest_json["summary"]["files_checked"] == 1
    # HOP base package verification
    assert (run_dir / "summary.md").is_file(), "HOP base package requires summary.md"
    assert (run_dir / "telemetry.json").is_file(), "HOP base package requires telemetry.json"
    assert (run_dir / "raw.json").is_file(), "Supplementary raw.json should exist"

    # HOP compliance: no pointer files should exist
    assert not (output_dir / "latest_report.json").exists(), "HOP forbids pointer files"

    # Second run introduces an error and prunes the first run when keep=1.
    _write_inventory_record(
        inventory_path,
        record_id="docs-handbook",
        target_path="docs/missing.md",
        status="active",
    )

    exit_code = module.main(
        [
            "--repo-root",
            str(repo_root),
            "--schema-root",
            str(schema_root),
            "--enums-path",
            str(enums_path),
            "--template-path",
            str(template_path),
            "--config-path",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2025-01-02T00:00:00+00:00",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "CRITICAL",
        ]
    )

    assert exit_code == 1

    # HOP-compliant directory format: YYYYMMDD-HHMM
    run_dir_error = output_dir / "20250102-0000"
    assert run_dir_error.exists()
    assert not run_dir.exists()

    # HOP base package: manifest.json (was report.json)
    error_manifest = json.loads((run_dir_error / "manifest.json").read_text(encoding="utf-8"))
    assert error_manifest["status"] == "error"
    assert error_manifest["summary"]["issue_counts"]["errors"] == 1

    raw_payload = json.loads((run_dir_error / "raw.json").read_text(encoding="utf-8"))
    errors = raw_payload["issues"]["errors"]
    assert errors
    assert "does not exist" in errors[0]["message"]

    # HOP compliance: no pointer files should exist after second run either
    assert not (output_dir / "latest_report.json").exists(), "HOP forbids pointer files"


def test_run_returns_payload_dict(tmp_path):
    """Test that run(argv) returns a payload dict for orchestrator chaining."""
    module = _load_module()
    repo_root = tmp_path
    schema_root = repo_root / ".repo_studios" / "inventory_schema"
    schema_root.mkdir(parents=True)

    enums_path = schema_root / "enums.yaml"
    template_path = schema_root / "inventory_entry_template.yaml"
    config_path = schema_root / "validator_config.yaml"
    inventory_path = schema_root / "sample.yaml"

    _write_yaml(enums_path, _base_enums_content())
    _write_yaml(template_path, _base_template_content())
    _write_yaml(config_path, _base_config_content())

    docs_root = repo_root / "docs"
    target_doc = docs_root / "guide.md"
    target_doc.parent.mkdir(parents=True)
    target_doc.write_text("content", encoding="utf-8")

    _write_inventory_record(inventory_path, record_id="docs-guide", target_path="docs/guide.md")

    output_dir = repo_root / "output"

    payload = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--schema-root",
            str(schema_root),
            "--enums-path",
            str(enums_path),
            "--template-path",
            str(template_path),
            "--config-path",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2025-06-15T10:30:00+00:00",
            "--log-level",
            "CRITICAL",
        ]
    )

    # Verify payload structure
    assert isinstance(payload, dict)
    assert payload["status"] == "pass"
    assert payload["exit_code"] == 0
    assert Path(payload["run_dir"]).is_dir()

    # Verify HOP base package paths
    assert Path(payload["manifest"]).name == "manifest.json"
    assert Path(payload["summary"]).name == "summary.md"
    assert Path(payload["telemetry"]).name == "telemetry.json"

    # Verify artifacts exist
    assert Path(payload["manifest"]).is_file()
    assert Path(payload["summary"]).is_file()
    assert Path(payload["telemetry"]).is_file()

    # Verify report_payload is included
    assert "report_payload" in payload
    assert payload["report_payload"]["status"] == "ok"
