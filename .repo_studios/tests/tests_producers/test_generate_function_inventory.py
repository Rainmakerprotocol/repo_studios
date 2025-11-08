"""Tests for generate_commandview_inventory producer."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
import subprocess
import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "command_center"
    / "scripts"
    / "producers"
    / "generate_commandview_inventory.py"
)
MODULE_NAME = "repo_studios_test.generate_commandview_inventory"


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


def _git(args: list[str], cwd: Path) -> None:
    completed = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if completed.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {completed.stderr}")


def _inventory_files(directory: Path, slug: str) -> list[Path]:
    return [path for path in directory.glob(f"{slug}_commandview_*.json") if "_screening_" not in path.name]


def _screening_files(directory: Path, slug: str) -> list[Path]:
    return list(directory.glob(f"{slug}_commandview_screening_*.json"))


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
    files = _inventory_files(output_dir, "sample_pkg")
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
    central_files = _inventory_files(reports_dir, "sample_pkg")
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
    assert helper_entry["cyclomatic_complexity"] == 1
    assert helper_entry["type_hint_coverage"] == 0
    class_names = {cls["name"] for cls in module_entry["classes"]}
    assert class_names == {"Example"}
    class_entry = module_entry["classes"][0]
    assert class_entry["bases"] == []
    assert class_entry["line_count"] >= 2
    method_entry = class_entry["methods"][0]
    assert method_entry["signature"] == "def method_one(self):"
    assert method_entry["qualified_name"] == "sample_pkg.module::Example.method_one"
    assert method_entry["line_count"] == 2
    assert method_entry["parent_class"] == "Example"
    call_graph = module_entry["call_graph"]
    assert call_graph["summary"]["total_edges"] == 0
    assert "locals" in call_graph
    locals_set = set(call_graph["locals"])
    assert "sample_pkg.module::helper" in locals_set
    assert "sample_pkg.module::Example.method_one" in locals_set
    only_entry = files["class_only.py"]
    assert only_entry["module_id"] == "sample_pkg.class_only"
    assert only_entry["module_first_line"] == "class Only:"
    init_entry = files["__init__.py"]
    assert init_entry["module_doc"] == "Utility package."
    assert init_entry["module_first_line"] is None

    summary_files = _screening_files(output_dir, "sample_pkg")
    assert len(summary_files) == 1
    summary_payload = json.loads(summary_files[0].read_text(encoding="utf-8"))
    assert "graphs" in summary_payload
    assert summary_payload["violations"] == {"cycles": False}
    assert "score_snapshot" in summary_payload
    snapshot = summary_payload["score_snapshot"]
    assert snapshot["packs"], "Expected at least one score pack"
    doc_pack = next(pack for pack in snapshot["packs"] if pack["id"] == "docstring_coverage")
    assert doc_pack["metrics"]["functions_total"] == 3
    assert doc_pack["metrics"]["functions_documented"] == 0
    assert doc_pack["score"] == 0.0
    assert summary_payload["score_history"]
    assert len(summary_payload["score_history"]) == 1
    assert summary_payload["score_latest"] == summary_payload["score_history"][-1]
    central_summary = _screening_files(reports_dir, "sample_pkg")
    assert len(central_summary) == 1
    assert json.loads(central_summary[0].read_text(encoding="utf-8")) == summary_payload


def test_inventory_merges_coverage_reports(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "pkg"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        (
            "def act(value: int) -> int:\n"
            "    if value > 0:\n"
            "        return value + 1\n"
            "    return value - 1\n"
        ),
    )

    coverage_payload = {
        "files": {
            "pkg/module.py": {
                "executed_lines": [1, 2, 3],
                "missing_lines": [4],
                "contexts": {"tests": [1, 2]},
            }
        }
    }
    coverage_file = repo_root / "coverage.json"
    coverage_file.write_text(json.dumps(coverage_payload), encoding="utf-8")

    exit_code = run_inventory(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-json",
            str(coverage_file),
            str(target),
        ]
    )
    assert exit_code == 0

    output_dir = target / "pkg_index"
    inventory_files = _inventory_files(output_dir, "pkg")
    assert len(inventory_files) == 1
    payload = json.loads(inventory_files[0].read_text(encoding="utf-8"))

    metadata = payload["metadata"]
    assert metadata.get("coverage_sources") == ["coverage.json"]

    statistics = payload["statistics"]
    coverage_stats = statistics.get("coverage")
    assert coverage_stats is not None
    assert coverage_stats["sources"] == 1
    assert coverage_stats["files_with_data"] == 1
    assert coverage_stats["executed_lines"] == 3
    assert coverage_stats["missing_lines"] == 1
    assert coverage_stats["tracked_lines"] == 4
    assert coverage_stats["line_rate"] == 0.75

    module_entry = next(entry for entry in payload["files"] if entry["relative_path"] == "module.py")
    coverage_entry = module_entry.get("coverage")
    assert coverage_entry is not None
    assert coverage_entry["executed_lines"] == [1, 2, 3]
    assert coverage_entry["missing_lines"] == [4]
    assert coverage_entry["executed_count"] == 3
    assert coverage_entry["missing_count"] == 1
    assert coverage_entry["tracked_count"] == 4
    assert coverage_entry["line_rate"] == 0.75
    assert coverage_entry["contexts"] == {"tests": [1, 2]}
    assert coverage_entry["contexts_count"] == {"tests": 2}


def test_inventory_includes_git_churn_summary(tmp_path: Path) -> None:
    repo_root = tmp_path
    _git(["init"], repo_root)
    _git(["config", "user.email", "ci@example.com"], repo_root)
    _git(["config", "user.name", "CI"], repo_root)

    target = repo_root / "pkg"
    _write(target / "__init__.py", "")
    _write(target / "module.py", "def act():\n    return 1\n")
    _git(["add", "pkg/__init__.py", "pkg/module.py"], repo_root)
    _git(["commit", "-m", "Initial"], repo_root)

    _write(target / "module.py", "def act(value: int) -> int:\n    return value + 1\n")
    _git(["add", "pkg/module.py"], repo_root)
    _git(["commit", "-m", "Adjust"], repo_root)

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "pkg_index"
    inventory_files = _inventory_files(output_dir, "pkg")
    assert len(inventory_files) == 1
    payload = json.loads(inventory_files[0].read_text(encoding="utf-8"))

    module_entry = next(entry for entry in payload["files"] if entry["relative_path"] == "module.py")
    churn = module_entry.get("git_churn")
    assert churn is not None
    assert churn["commit_count"] >= 2
    assert churn["additions"] >= 1
    assert churn["deletions"] >= 0
    assert churn["net_changes"] == churn["additions"] - churn["deletions"]
    latest = churn["latest_commit"]
    assert latest["hash"]
    assert latest["timestamp"].endswith("+00:00")

    stats = payload["statistics"].get("git_churn")
    assert stats is not None
    assert stats["files_with_data"] >= 1
    assert stats["total_commits"] >= churn["commit_count"]
    assert stats["total_additions"] >= churn["additions"]
    assert stats["net_changes"] == stats["total_additions"] - stats["total_deletions"]


def test_inventory_captures_warnings_for_problem_files(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "pkg"
    _write(target / "good.py", "def ok():\n    return 1\n")
    _write(target / "bad.py", "def broken(:\n    pass\n")

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "pkg_index"
    files = _inventory_files(output_dir, "pkg")
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
    files = _inventory_files(output_dir, "workspace")
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

    files = _inventory_files(output_dir, "pkg")
    assert len(files) == 1
    output_file = files[0]
    assert output_file.exists()
    assert output_file.name.startswith("pkg_commandview_")
    assert not (output_dir / "pkg_index-2000-01-01.json").exists()
    assert not (output_dir / "pkg_index.json").exists()
    latest_pointer = output_dir / "latest.json"
    assert not latest_pointer.exists()
    central_files = _inventory_files(reports_dir, "pkg")
    assert len(central_files) == 1
    central_file = central_files[0]
    assert central_file.name.startswith("pkg_commandview_")
    assert not (reports_dir / "pkg_index-1999-12-31.json").exists()
    assert not (reports_dir / "pkg_index.json").exists()
    assert not (reports_dir / "latest.json").exists()
    summary_files = _screening_files(output_dir, "pkg")
    assert len(summary_files) == 1
    assert summary_files[0].name.startswith("pkg_commandview_screening_")
    assert not (output_dir / "pkg_screening-2000-01-01.json").exists()
    central_summary = _screening_files(reports_dir, "pkg")
    assert len(central_summary) == 1
    assert central_summary[0].name.startswith("pkg_commandview_screening_")
    assert not (reports_dir / "pkg_screening-1999-12-31.json").exists()


def test_screening_score_history_accumulates_across_runs(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "pkg"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        "def run(value: int) -> int:\n    return value\n",
    )

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "pkg_index"
    summary_files = _screening_files(output_dir, "pkg")
    assert summary_files
    summary_payload = json.loads(summary_files[-1].read_text(encoding="utf-8"))
    history = summary_payload.get("score_history") or []
    assert len(history) == 1
    first_pack = history[0]["packs"][0]
    assert first_pack["score"] == 0.0
    assert first_pack["severity"] == "critical"

    _write(
        target / "module.py",
        (
            "def run(value: int) -> int:\n"
            '    """Return supplied value."""\n'
            "    return value\n"
        ),
    )

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    summary_files = _screening_files(output_dir, "pkg")
    assert summary_files
    updated_payload = json.loads(summary_files[-1].read_text(encoding="utf-8"))
    updated_history = updated_payload.get("score_history") or []
    assert len(updated_history) == 2
    assert updated_history[0]["timestamp"] < updated_history[1]["timestamp"]
    latest_pack = updated_history[-1]["packs"][0]
    assert latest_pack["score"] == 100.0
    assert latest_pack["severity"] == "ok"

    mirror_dir = (
        repo_root
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "index_scan"
        / "pkg_index"
    )
    mirror_files = _screening_files(mirror_dir, "pkg")
    assert mirror_files
    assert json.loads(mirror_files[-1].read_text(encoding="utf-8")) == updated_payload


def test_call_graph_resolves_local_and_imported_calls(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "sample"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        (
            "import json\n"
            "from math import sqrt\n\n"
            "def helper(value: int) -> int:\n"
            "    return value + 1\n\n"
            "def outer(value: int) -> dict[str, float]:\n"
            "    total = helper(value)\n"
            "    encoded = Example.encode({'value': total})\n"
            "    root = sqrt(total)\n"
            "    return {'encoded': len(encoded), 'root': root}\n\n"
            "class Example:\n"
            "    def method_one(self, payload):\n"
            "        return self.method_two(payload)\n\n"
            "    def method_two(self, payload):\n"
            "        return len(payload)\n\n"
            "    @staticmethod\n"
            "    def encode(data):\n"
            "        return json.dumps(data)\n"
        ),
    )

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "sample_index"
    inventory_files = _inventory_files(output_dir, "sample")
    assert len(inventory_files) == 1
    output_file = inventory_files[0]
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    module_entry = next(entry for entry in payload["files"] if entry["relative_path"] == "module.py")
    call_graph = module_entry["call_graph"]

    assert call_graph["summary"]["total_edges"] == 7
    by_kind = call_graph["summary"]["by_kind"]
    assert by_kind["local_function"] == 1
    assert by_kind["local_method"] == 2
    assert by_kind["imported"] == 2
    assert by_kind["builtin"] == 2

    edges = call_graph["edges"]

    def _find_edge(source: str, target: str | None = None, expression: str | None = None) -> dict[str, Any]:
        for edge in edges:
            if edge["source"] != source:
                continue
            if target is not None and edge.get("target") != target:
                continue
            if expression is not None and edge.get("expression") != expression:
                continue
            return edge
        target_desc = target or expression or "<unknown>"
        raise AssertionError(f"Edge from {source} to {target_desc} not found")

    outer_source = "sample.module::outer"
    helper_edge = _find_edge(outer_source, target="sample.module::helper")
    assert helper_edge["resolution"]["kind"] == "local_function"

    encode_edge = _find_edge(outer_source, target="sample.module::Example.encode")
    assert encode_edge["resolution"]["kind"] == "local_method"

    sqrt_edge = _find_edge(outer_source, target="math.sqrt")
    assert sqrt_edge["resolution"]["kind"] == "imported"
    assert sqrt_edge["resolution"]["category"] == "standard_library"
    assert sqrt_edge["resolution"]["detail"]["alias"] == "sqrt"

    len_outer_edge = _find_edge(outer_source, target="builtins.len")
    assert len_outer_edge["resolution"]["kind"] == "builtin"

    method_one_source = "sample.module::Example.method_one"
    method_edge = _find_edge(method_one_source, target="sample.module::Example.method_two")
    assert method_edge["resolution"]["kind"] == "local_method"

    method_two_source = "sample.module::Example.method_two"
    len_method_edge = _find_edge(method_two_source, target="builtins.len")
    assert len_method_edge["resolution"]["kind"] == "builtin"

    encode_source = "sample.module::Example.encode"
    json_edge = _find_edge(encode_source, target="json.dumps")
    assert json_edge["resolution"]["kind"] == "imported"
    assert json_edge["resolution"]["module"] == "json"

    assert set(call_graph.get("external_modules", [])) == {"json", "math"}
    assert call_graph["by_function"][outer_source]["total"] == 4


def test_inventory_records_class_bases(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "pkg"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        (
            "class Base:\n"
            "    pass\n\n"
            "class Mixin:\n"
            "    pass\n\n"
            "class Derived(Base, Mixin):\n"
            "    def act(self):\n"
            "        return super().act() if hasattr(super(), 'act') else None\n"
        ),
    )

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "pkg_index"
    inventory_files = _inventory_files(output_dir, "pkg")
    assert len(inventory_files) == 1
    payload = json.loads(inventory_files[0].read_text(encoding="utf-8"))
    module_entry = next(entry for entry in payload["files"] if entry["relative_path"] == "module.py")
    classes = {cls["name"]: cls for cls in module_entry["classes"]}
    assert classes["Base"]["bases"] == []
    assert classes["Mixin"]["bases"] == []
    assert classes["Derived"]["bases"] == ["Base", "Mixin"]


def test_cyclomatic_complexity_counts_branches(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "work"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        (
            "def decision(value):\n"
            "    total = 0\n"
            "    for item in value:\n"
            "        if item and item > 0:\n"
            "            total += item\n"
        
            "        elif item == 0:\n"
            "            total += 1\n"
            "        else:\n"
            "            total -= item\n"
            "    while total > 10 and any(v < 0 for v in value):\n"
            "        total -= 1\n"
            "    return total\n"
        ),
    )

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "work_index"
    inventory_files = _inventory_files(output_dir, "work")
    assert len(inventory_files) == 1
    payload = json.loads(inventory_files[0].read_text(encoding="utf-8"))
    module_entry = next(entry for entry in payload["files"] if entry["relative_path"] == "module.py")
    decision_entry = module_entry["functions"][0]
    assert decision_entry["cyclomatic_complexity"] == 8
    assert decision_entry["type_hint_coverage"] == 0


def test_type_hint_coverage_reports_ratio(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "annot"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        (
            "def fully_typed(a: int, b: str) -> bool:\n"
            "    return str(a) == b\n\n"
            "def partially_typed(a: int, b: str, c, d) -> None:\n"
            "    return None\n"
        ),
    )

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "annot_index"
    inventory_files = _inventory_files(output_dir, "annot")
    assert len(inventory_files) == 1
    payload = json.loads(inventory_files[0].read_text(encoding="utf-8"))
    module_entry = next(entry for entry in payload["files"] if entry["relative_path"] == "module.py")
    by_name = {func["name"]: func for func in module_entry["functions"]}
    assert by_name["fully_typed"]["type_hint_coverage"] == 1
    assert by_name["partially_typed"]["type_hint_coverage"] == 0.5


def test_function_metadata_persists_effects_and_decorators(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "effects"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        (
            "import logging\n\n"
            "GLOBAL = 0\n\n"
            "def identity(fn):\n"
            "    return fn\n\n"
            "@identity\n"
            "def decorated_function(path):\n"
            "    global GLOBAL\n"
            "    logging.info('start')\n"
            "    with open(path, 'w+') as handle:\n"
            "        handle.write('data')\n"
            "    if GLOBAL < 0:\n"
            "        raise ValueError('bad state')\n"
            "    return path\n\n"
            "@identity\n"
            "class DecoratedClass:\n"
            "    @classmethod\n"
            "    def build(cls, filename):\n"
            "        global GLOBAL\n"
            "        logging.error('failure')\n"
            "        with open(filename) as handle:\n"
            "            data = handle.read()\n"
            "        if data:\n"
            "            return data\n"
            "        raise RuntimeError('empty file')\n"
        ),
    )

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "effects_index"
    inventory_files = _inventory_files(output_dir, "effects")
    assert len(inventory_files) == 1
    payload = json.loads(inventory_files[0].read_text(encoding="utf-8"))
    module_entry = next(entry for entry in payload["files"] if entry["relative_path"] == "module.py")

    functions = {func["name"]: func for func in module_entry["functions"]}
    decorated_func = functions["decorated_function"]

    assert decorated_func["used_globals"] == ["GLOBAL"]
    assert decorated_func["io_effects"] == {"reads": True, "writes": True, "env": False, "network": False}
    assert any(item["exception"] == "ValueError('bad state')" for item in decorated_func["raises"])
    assert any(call["level"] == "info" for call in decorated_func["logging_calls"])
    assert decorated_func["decorators"] == ["identity"]
    assert decorated_func["decorators_detailed"]

    decorated_class = next(cls for cls in module_entry["classes"] if cls["name"] == "DecoratedClass")
    assert decorated_class["decorators"] == ["identity"]
    assert decorated_class["decorators_detailed"]

    method_entry = next(method for method in decorated_class["methods"] if method["name"].endswith("build"))
    assert method_entry["used_globals"] == ["GLOBAL"]
    assert method_entry["io_effects"] == {"reads": True, "writes": False, "env": False, "network": False}
    assert any(item["exception"] == "RuntimeError('empty file')" for item in method_entry["raises"])
    assert any(call["level"] == "error" for call in method_entry["logging_calls"])
    assert "classmethod" in method_entry["decorators"]
    assert method_entry["decorators_detailed"]


def test_unused_imports_and_unreachable_functions_reported(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "deadcode"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        (
            "import logging\n"
            "from math import sqrt\n\n"
            "def used(value):\n"
            "    return sqrt(value)\n\n"
            "def execute(value):\n"
            "    return orchestrate(value)\n\n"
            "def orchestrate(value):\n"
            "    helper = Sample()\n"
            "    return helper.active(value)\n\n"
            "def unused_helper(value):\n"
            "    return value + 1\n\n"
            "class Sample:\n"
            "    def active(self, value):\n"
            "        return used(value)\n\n"
            "    def orphan(self, value):\n"
            "        return value - 1\n"
        ),
    )

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 0

    output_dir = target / "deadcode_index"
    inventory_files = _inventory_files(output_dir, "deadcode")
    assert len(inventory_files) == 1
    payload = json.loads(inventory_files[0].read_text(encoding="utf-8"))
    module_entry = next(entry for entry in payload["files"] if entry["relative_path"] == "module.py")

    unused_imports = module_entry["unused_imports"]
    assert any(item["target"] == "logging" for item in unused_imports)

    unreachable = module_entry["unreachable_functions"]
    unreachable_names = {item["qualified_name"] for item in unreachable}
    assert any(name.endswith("unused_helper") for name in unreachable_names)
    assert any(name.endswith("Sample.orphan") for name in unreachable_names)


def test_inventory_errors_when_no_python_files(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / "empty"
    target.mkdir(parents=True, exist_ok=True)

    exit_code = run_inventory(["--repo-root", str(repo_root), str(target)])
    assert exit_code == 1


def test_reports_root_outside_static_scope_rejected(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    repo_root = tmp_path
    target = repo_root / "pkg"
    _write(target / "__init__.py", "")

    caplog.set_level("ERROR")
    exit_code = run_inventory(
        [
            "--repo-root",
            str(repo_root),
            "--reports-root",
            str(Path("custom_reports")),
            str(target),
        ]
    )
    assert exit_code == 1
    assert any(".repo_studios/command_center/reports" in message for message in caplog.messages)