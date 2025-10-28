"""Tests for generate_function_analysis producer."""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable


INVENTORY_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "command_center"
    / "scripts"
    / "producers"
    / "generate_function_inventory.py"
)
ANALYSIS_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "command_center"
    / "scripts"
    / "summarizers"
    / "generate_function_analysis.py"
)
INVENTORY_MODULE_NAME = "repo_studios_test.generate_function_inventory"
ANALYSIS_MODULE_NAME = "repo_studios_test.generate_function_analysis"

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
    sys.modules[spec.name] = module
    loader.exec_module(module)
    return module


INVENTORY_MODULE = _load_module(INVENTORY_MODULE_PATH, INVENTORY_MODULE_NAME)
ANALYSIS_MODULE = _load_module(ANALYSIS_MODULE_PATH, ANALYSIS_MODULE_NAME)


def run_inventory(args: list[str]) -> int:
    return INVENTORY_MODULE.run(args)


def run_analysis(args: list[str]) -> int:
    return ANALYSIS_MODULE.run(args)


def teardown_module() -> None:  # pragma: no cover
    sys.modules.pop(INVENTORY_MODULE_NAME, None)
    sys.modules.pop(ANALYSIS_MODULE_NAME, None)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_analysis_detects_duplicate_functions(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "sample_pkg"
    _write(target / "__init__.py", "")
    _write(
        target / "alpha.py",
        "def helper(value):\n"
        "    \"\"\"Alpha helpers.\"\"\"\n"
        "    return value * 2\n",
    )
    _write(
        target / "beta.py",
        "def helper(value):\n"
        "    \"\"\"Alpha helpers.\"\"\"\n"
        "    return value + 2\n",
    )

    assert run_inventory(["--repo-root", str(repo_root), str(target)]) == 0

    inventory_dir = target / "sample_pkg_index"
    inventory_files = list(inventory_dir.glob("sample_pkg_index-*.json"))
    assert len(inventory_files) == 1
    inventory_file = inventory_files[0]
    inventory_payload = _load_json(inventory_file)

    assert run_analysis(["--repo-root", str(repo_root), str(target)]) == 0

    analysis_files = list(inventory_dir.glob("sample_pkg_analysis-*.json"))
    assert len(analysis_files) == 1
    analysis_file = analysis_files[0]
    analysis_payload = _load_json(analysis_file)
    slug = slugify_relative(target.relative_to(repo_root))
    mirror_dir = (
        repo_root
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "index_scan_analysis"
        / f"{slug}_analysis"
    )
    mirror_files = list(mirror_dir.glob("sample_pkg_analysis-*.json"))
    assert len(mirror_files) == 1
    mirror_payload = _load_json(mirror_files[0])
    assert mirror_payload == analysis_payload
    assert not (inventory_dir / "latest.json").exists()
    assert not (mirror_dir / "latest.json").exists()

    inv_generated_at = inventory_payload["metadata"]["generated_at"]
    analysis_metadata = analysis_payload["metadata"]
    assert analysis_metadata["source_index_file"].endswith(inventory_file.name)
    assert analysis_metadata["source_index_generated_at"] == inv_generated_at

    findings = analysis_payload["findings"]
    assert findings
    duplicate_finding = findings[0]
    assert duplicate_finding["kind"] == "duplicate_function"
    assert duplicate_finding["metrics"]["duplicate_count"] == 2
    details = duplicate_finding["details"]
    assert details["function_name"] == "helper"
    assert details["signature"] == "def helper(value):"
    assert details["line_counts"] == [3, 3]
    action_items = duplicate_finding["action_items"]
    assert action_items
    item = action_items[0]
    assert item["type"] == "review_duplicate_function"
    assert any("alpha.py" in entry for entry in item["targets"])
    assert any("beta.py" in entry for entry in item["targets"])
    instances = duplicate_finding["instances"]
    assert len(instances) == 2
    assert all(instance["signature"] == "def helper(value):" for instance in instances)
    assert all(instance["line_count"] == 3 for instance in instances)
    assert instances[0]["docstring"] == "Alpha helpers."
    assert {instance["path"] for instance in instances} == {"alpha.py", "beta.py"}
    assert {instance["docstring"] for instance in instances} == {"Alpha helpers."}


def test_analysis_errors_without_inventory(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "empty_pkg"
    target.mkdir(parents=True, exist_ok=True)

    exit_code = run_analysis(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 1


def test_analysis_replaces_existing_outputs(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "pkg"
    _write(target / "__init__.py", "")
    _write(target / "mod.py", "def helper():\n    return True\n")

    assert run_inventory(["--repo-root", str(repo_root), str(target)]) == 0

    index_dir = target / "pkg_index"
    slug = slugify_relative(target.relative_to(repo_root))
    mirror_dir = (
        repo_root
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "index_scan_analysis"
        / f"{slug}_analysis"
    )
    old_file = index_dir / "pkg_analysis-2000-01-01.json"
    _write(old_file, "{}")
    legacy_file = index_dir / "pkg_analysis.json"
    _write(legacy_file, "{}")
    old_mirror = mirror_dir / "pkg_analysis-1999-12-31.json"
    _write(old_mirror, "{}")
    legacy_mirror = mirror_dir / "pkg_analysis.json"
    _write(legacy_mirror, "{}")

    assert run_analysis(["--repo-root", str(repo_root), str(target)]) == 0

    analysis_files = list(index_dir.glob("pkg_analysis-*.json"))
    assert len(analysis_files) == 1
    analysis_file = analysis_files[0]
    assert analysis_file.name != old_file.name
    assert not legacy_file.exists()
    mirror_files = list(mirror_dir.glob("pkg_analysis-*.json"))
    assert len(mirror_files) == 1
    mirror_file = mirror_files[0]
    assert mirror_file.name != old_mirror.name
    assert not legacy_mirror.exists()
    assert not (mirror_dir / "latest.json").exists()
