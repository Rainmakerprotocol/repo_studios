from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[3] / ".repo_studios" / "scripts" / "producers" / "validate_inventory.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_inventory_module", MODULE_PATH)
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

    run_dir = output_dir / "validate_inventory-20250101_000000"
    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_json["status"] == "ok"
    assert report_json["summary"]["issue_counts"]["errors"] == 0
    assert report_json["summary"]["files_checked"] == 1
    assert (run_dir / "raw.json").is_file()

    latest = json.loads((output_dir / "latest_report.json").read_text(encoding="utf-8"))
    assert latest["timestamp"] == "20250101_000000"

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

    run_dir_error = output_dir / "validate_inventory-20250102_000000"
    assert run_dir_error.exists()
    assert not run_dir.exists()

    error_report = json.loads((run_dir_error / "report.json").read_text(encoding="utf-8"))
    assert error_report["status"] == "error"
    assert error_report["summary"]["issue_counts"]["errors"] == 1

    raw_payload = json.loads((run_dir_error / "raw.json").read_text(encoding="utf-8"))
    errors = raw_payload["issues"]["errors"]
    assert errors
    assert "does not exist" in errors[0]["message"]

    latest = json.loads((output_dir / "latest_report.json").read_text(encoding="utf-8"))
    assert latest["timestamp"] == "20250102_000000"
    assert latest["status"] == "error"
