import json
from pathlib import Path

from . import utils  # type: ignore[attr-defined]

from ..conftest import load_validator


def write_yaml(path: Path, data):
    path.write_text(utils.dump_yaml(data), encoding="utf-8")


def test_validation_passes_for_valid_entry(tmp_path: Path):
    schema_root = tmp_path / "inventory_schema"
    schema_root.mkdir()

    enums = {
        "asset_kind": ["script"],
        "roles": ["validator"],
        "maturity": ["legacy"],
        "consumers": ["coding_agent"],
        "status": ["needs_review"],
    }
    write_yaml(schema_root / "enums.yaml", enums)

    records = [
        {
            "id": "scripts.example",
            "name": "Example Script",
            "path": "foo.py",
            "asset_kind": "script",
            "roles": ["validator"],
            "maturity": "legacy",
            "description": "Example",
            "consumers": ["coding_agent"],
            "status": "needs_review",
            "artifact_type": "py",
        }
    ]
    write_yaml(schema_root / "valid.yaml", records)

    validator = load_validator(tmp_path)
    rc, stdout = validator()
    assert rc == 0
    assert "Inventory validation passed" in stdout


def test_validation_detects_duplicate_ids(tmp_path: Path):
    schema_root = tmp_path / "inventory_schema"
    schema_root.mkdir()

    enums = {
        "asset_kind": ["script"],
        "roles": ["validator"],
        "maturity": ["legacy"],
        "consumers": ["coding_agent"],
        "status": ["needs_review"],
    }
    write_yaml(schema_root / "enums.yaml", enums)

    duplicate_records = [
        {
            "id": "scripts.dup",
            "name": "Dup1",
            "path": "dup1.py",
            "asset_kind": "script",
            "roles": ["validator"],
            "maturity": "legacy",
            "description": "Dup",
            "consumers": ["coding_agent"],
            "status": "needs_review",
            "artifact_type": "py",
        },
        {
            "id": "scripts.dup",
            "name": "Dup2",
            "path": "dup2.py",
            "asset_kind": "script",
            "roles": ["validator"],
            "maturity": "legacy",
            "description": "Dup",
            "consumers": ["coding_agent"],
            "status": "needs_review",
            "artifact_type": "py",
        },
    ]
    write_yaml(schema_root / "dup.yaml", duplicate_records)

    validator = load_validator(tmp_path)
    rc, stdout = validator()
    assert rc == 1
    assert "Duplicate id" in stdout


def test_json_output(tmp_path: Path):
    schema_root = tmp_path / "inventory_schema"
    schema_root.mkdir()

    enums = {
        "asset_kind": ["script"],
        "roles": ["validator"],
        "maturity": ["legacy"],
        "consumers": ["coding_agent"],
        "status": ["needs_review"],
    }
    write_yaml(schema_root / "enums.yaml", enums)

    invalid_records = [
        {
            "id": "scripts.invalid",
            "name": "Invalid",
            "path": "invalid.py",
            "asset_kind": "script",
            "roles": ["validator"],
            "maturity": "legacy",
            "description": "Invalid",
            "consumers": ["coding_agent"],
            "status": "not_real",
            "artifact_type": "py",
        }
    ]
    write_yaml(schema_root / "invalid.yaml", invalid_records)

    validator = load_validator(tmp_path, json_output=True)
    rc, stdout = validator()
    assert rc == 1
    payload = json.loads(stdout)
    assert payload["issues"][0]["level"] == "error"
    assert payload["issues"][0]["context"]["enum"] == "status"
