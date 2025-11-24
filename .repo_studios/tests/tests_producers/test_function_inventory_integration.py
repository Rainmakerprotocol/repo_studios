"""Integration tests for inventory and analysis producers."""

from __future__ import annotations

import importlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Callable

import jsonschema
import pytest

INVENTORY_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "command_center"
    / "scripts"
    / "producers"
    / "generate_commandview_inventory.py"
)
ANALYSIS_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "command_center" / "scripts" / "summarizers" / "generate_function_analysis.py"
)
INVENTORY_MODULE_NAME = "repo_studios_test.integration_inventory"
ANALYSIS_MODULE_NAME = "repo_studios_test.integration_analysis"
SCHEMA_DIR = Path(__file__).resolve().parents[2] / "docs" / "schemas"
FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "function_inventory" / "sample_pkg"

SCRIPTS_ROOT = Path(__file__).resolve().parents[2] / "command_center" / "scripts"


def _load_slugify() -> Callable[[Path], str]:
    try:
        module = importlib.import_module("libraries")
    except ModuleNotFoundError:  # pragma: no cover - test sandbox fallback
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        module = importlib.import_module("libraries")
    return module.slugify_relative


slugify_relative = _load_slugify()


def _load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


INVENTORY_MODULE = _load_module(INVENTORY_MODULE_PATH, INVENTORY_MODULE_NAME)
ANALYSIS_MODULE = _load_module(ANALYSIS_MODULE_PATH, ANALYSIS_MODULE_NAME)


@pytest.fixture(scope="module", autouse=True)
def _cleanup_modules():
    yield
    sys.modules.pop(INVENTORY_MODULE_NAME, None)
    sys.modules.pop(ANALYSIS_MODULE_NAME, None)


def _run_inventory(args: list[str]) -> int:
    return INVENTORY_MODULE.run(args)


def _run_analysis(args: list[str]) -> int:
    return ANALYSIS_MODULE.run(args)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _inventory_artifacts(directory: Path, slug: str) -> list[Path]:
    return sorted(path for path in directory.glob(f"{slug}_commandview_*.json") if "_screening_" not in path.name)


def _screening_artifacts(directory: Path, slug: str) -> list[Path]:
    return sorted(directory.glob(f"{slug}_commandview_screening_*.json"))


def _validate_with_schema(payload: dict, schema_name: str) -> None:
    schema_path = SCHEMA_DIR / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    errors = [error for error in validator.iter_errors(payload) if error.validator != "additionalProperties"]
    if errors:
        raise errors[0]


def test_inventory_and_analysis_round_trip(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    target = workspace / "sample_pkg"
    shutil.copytree(FIXTURE_ROOT, target)

    exit_code = _run_inventory(["--repo-root", str(workspace), str(target)])
    assert exit_code == 0

    index_dir = target / "sample_pkg_index"
    inventory_files = _inventory_artifacts(index_dir, "sample_pkg")
    assert inventory_files, "Expected inventory artifact to be created"
    inventory_file = inventory_files[-1]
    latest_pointer = index_dir / "latest.json"
    assert not latest_pointer.exists()

    inventory_payload = _load_json(inventory_file)

    _validate_with_schema(inventory_payload, "function_inventory.schema.json")

    metadata = inventory_payload["metadata"]
    assert metadata["total_files"] == 4
    assert metadata["total_functions"] >= 4
    module_entry = next(item for item in inventory_payload["files"] if item["relative_path"] == "alpha.py")
    assert module_entry["module_first_line"].startswith("def duplicate_helper")
    screening_files = _screening_artifacts(index_dir, "sample_pkg")
    assert screening_files, "Expected screening summary artifact"
    screening_payload = _load_json(screening_files[-1])
    assert "graphs" in screening_payload
    slug = slugify_relative(target.relative_to(workspace))
    reports_root = workspace / ".repo_studios" / "command_center" / "reports"
    mirror_index_dir = reports_root / "index_scan" / f"{slug}_index"
    mirror_index_files = _inventory_artifacts(mirror_index_dir, "sample_pkg")
    assert mirror_index_files
    assert _load_json(mirror_index_files[-1]) == inventory_payload
    mirror_screening = _screening_artifacts(mirror_index_dir, "sample_pkg")
    assert mirror_screening

    exit_code = _run_analysis(["--repo-root", str(workspace), str(target)])
    assert exit_code == 0

    analysis_files = sorted(index_dir.glob("sample_pkg_analysis-*.json"))
    assert analysis_files, "Expected analysis artifact to be created"
    analysis_payload = _load_json(analysis_files[-1])
    _validate_with_schema(analysis_payload, "function_analysis.schema.json")

    analysis_summary = analysis_payload["summary"]
    assert analysis_summary["duplicate_groups"] == 1
    assert analysis_summary["total_duplicate_functions"] == 2

    mirror_dir = reports_root / "index_scan_analysis" / f"{slug}_analysis"
    mirror_files = sorted(mirror_dir.glob("sample_pkg_analysis-*.json"))
    assert mirror_files, "Expected mirrored analysis artifact"
    mirror_payload = _load_json(mirror_files[-1])
    assert mirror_payload == analysis_payload
    assert not (mirror_dir / "latest.json").exists()

    finding = analysis_payload["findings"][0]
    assert finding["details"]["signature"].startswith("def duplicate_helper")
    assert {instance["path"] for instance in finding["instances"]} == {"alpha.py", "beta.py"}
    assert finding["metrics"]["duplicate_count"] == 2
