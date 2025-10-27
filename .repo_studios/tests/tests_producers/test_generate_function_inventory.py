"""Tests for generate_function_inventory producer."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "command_center"
    / "scripts"
    / "producers"
    / "generate_function_inventory.py"
)
MODULE_NAME = "repo_studios_test.generate_function_inventory"


def _load_module():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    sys.modules[spec.name] = module
    loader.exec_module(module)
    return module


MODULE = _load_module()


def run_inventory(args: list[str]) -> int:
    return MODULE.run(args)


def teardown_module() -> None:  # pragma: no cover - cleanup hook
    sys.modules.pop(MODULE_NAME, None)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_inventory_generates_structured_output(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "sample_pkg"
    _write(target / "__init__.py", '"""Utility package."""\n')
    _write(
        target / "module.py",
        """
class Example:
    def method_one(self):
        return True

def helper(value):
    return value * 2
""".strip()
        + "\n",
    )
    _write(
        target / "class_only.py",
        "class Only:\n    def do(self):\n        return 42\n",
    )

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "sample_pkg_index"
    files = list(output_dir.glob("sample_pkg_index-*.json"))
    assert len(files) == 1
    output_file = files[0]
    assert output_file.exists()
    assert not (output_dir / "sample_pkg_index.json").exists()
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    latest_pointer = output_dir / "latest.json"
    assert not latest_pointer.exists()
    reports_dir = (
        repo_root
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "index_scan"
        / "sample_pkg_index"
    )
    central_files = list(reports_dir.glob("sample_pkg_index-*.json"))
    assert len(central_files) == 1
    central_file = central_files[0]
    assert json.loads(central_file.read_text(encoding="utf-8")) == payload
    assert not (reports_dir / "latest.json").exists()
    metadata = payload["metadata"]
    assert metadata["schema_version"] == 2
    assert metadata["folder_name"] == "sample_pkg"
    assert metadata["total_files"] == 3
    assert metadata["total_functions"] == 3  # two methods + one function
    assert metadata["total_classes"] == 2

    files = {entry["relative_path"]: entry for entry in payload["files"]}
    assert "module.py" in files
    module_entry = files["module.py"]
    assert module_entry["module_id"] == "sample_pkg.module"
    assert module_entry["imports_detailed"] == []
    assert module_entry["entrypoints"] == {"has_main_guard": False, "cli_parser": False}
    assert module_entry["module_first_line"] == "def helper(value):"
    function_names = {func["name"] for func in module_entry["functions"]}
    assert function_names == {"helper"}
    helper_entry = module_entry["functions"][0]
    assert helper_entry["signature"] == "def helper(value):"
    assert helper_entry["qualified_name"] == "sample_pkg.module::helper"
    assert helper_entry["returns_kind"] == "value"
    assert helper_entry["locals_summary"]["assign"] == 0
    assert helper_entry["line_count"] == 2
    assert helper_entry["io_effects"] == {"reads": False, "writes": False, "env": False, "network": False}
    class_names = {cls["name"] for cls in module_entry["classes"]}
    assert class_names == {"Example"}
    class_entry = module_entry["classes"][0]
    assert class_entry["bases"] == []
    assert class_entry["line_count"] >= 2
    method_entry = class_entry["methods"][0]
    assert method_entry["signature"] == "def method_one(self):"
    assert method_entry["qualified_name"] == "sample_pkg.module::Example.method_one"
    assert method_entry["line_count"] == 2
    only_entry = files["class_only.py"]
    assert only_entry["module_id"] == "sample_pkg.class_only"
    assert only_entry["module_first_line"] == "class Only:"
    init_entry = files["__init__.py"]
    assert init_entry["module_doc"] == "Utility package."
    assert init_entry["module_first_line"] is None

    summary_files = list(output_dir.glob("sample_pkg_screening-*.json"))
    assert len(summary_files) == 1
    summary_payload = json.loads(summary_files[0].read_text(encoding="utf-8"))
    assert "graphs" in summary_payload
    assert summary_payload["violations"] == {"cycles": False}
    central_summary = list(reports_dir.glob("sample_pkg_screening-*.json"))
    assert len(central_summary) == 1
    assert json.loads(central_summary[0].read_text(encoding="utf-8")) == summary_payload


def test_inventory_captures_warnings_for_problem_files(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "pkg"
    _write(target / "good.py", "def ok():\n    return 1\n")
    _write(target / "bad.py", "def broken(:\n    pass\n")

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "pkg_index"
    files = list(output_dir.glob("pkg_index-*.json"))
    assert len(files) == 1
    output_file = files[0]
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert "warnings" in payload
    assert any("bad.py" in warning for warning in payload["warnings"])


def test_inventory_skips_hidden_and_virtualenv_dirs(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "workspace"
    _write(target / "visible.py", "def run():\n    return True\n")
    hidden_dir = target / ".hidden"
    _write(hidden_dir / "should_skip.py", "def nope():\n    return False\n")
    venv_dir = target / "venv" / "mod.py"
    _write(venv_dir, "def skip():\n    return False\n")

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "workspace_index"
    files = list(output_dir.glob("workspace_index-*.json"))
    assert len(files) == 1
    output_file = files[0]
    assert not (output_dir / "workspace_index.json").exists()
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    relative_paths = {entry["relative_path"] for entry in payload["files"]}
    assert relative_paths == {"visible.py"}


def test_inventory_removes_preexisting_outputs(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "pkg"
    _write(target / "main.py", "def run():\n    return True\n")

    output_dir = target / "pkg_index"
    output_dir.mkdir(parents=True, exist_ok=True)
    _write(output_dir / "pkg_index.json", "{}")
    _write(output_dir / "pkg_index-2000-01-01.json", "{}")
    _write(output_dir / "latest.json", "{}")
    _write(output_dir / "pkg_screening-2000-01-01.json", "{}")
    reports_dir = (
        repo_root
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "index_scan"
        / "pkg_index"
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write(reports_dir / "pkg_index.json", "{}")
    _write(reports_dir / "pkg_index-1999-12-31.json", "{}")
    _write(reports_dir / "latest.json", "{}")
    _write(reports_dir / "pkg_screening-1999-12-31.json", "{}")

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    files = list(output_dir.glob("pkg_index-*.json"))
    assert len(files) == 1
    output_file = files[0]
    assert output_file.exists()
    assert output_file.name != "pkg_index-2000-01-01.json"
    assert not (output_dir / "pkg_index.json").exists()
    latest_pointer = output_dir / "latest.json"
    assert not latest_pointer.exists()
    central_files = list(reports_dir.glob("pkg_index-*.json"))
    assert len(central_files) == 1
    central_file = central_files[0]
    assert central_file.name != "pkg_index-1999-12-31.json"
    assert not (reports_dir / "pkg_index.json").exists()
    assert not (reports_dir / "latest.json").exists()
    summary_files = list(output_dir.glob("pkg_screening-*.json"))
    assert len(summary_files) == 1
    assert summary_files[0].name != "pkg_screening-2000-01-01.json"
    central_summary = list(reports_dir.glob("pkg_screening-*.json"))
    assert len(central_summary) == 1
    assert central_summary[0].name != "pkg_screening-1999-12-31.json"


def test_inventory_errors_when_no_python_files(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "empty"
    target.mkdir(parents=True, exist_ok=True)

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 1