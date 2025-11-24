from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "command_center"
    / "scripts"
    / "producers"
    / "generate_commandview_inventory.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_commandview_inventory", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    sys.modules[spec.name] = module
    loader.exec_module(module)
    return module


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


def test_generate_commandview_inventory_emits_extended_metrics(tmp_path: Path) -> None:
    module = _load_module()

    repo_root = tmp_path
    _git(["init"], repo_root)
    _git(["config", "user.email", "ci@example.com"], repo_root)
    _git(["config", "user.name", "CI"], repo_root)

    target = repo_root / "pkg"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        "def act(value: int) -> int:\n    if value > 0:\n        return value + 1\n    return value - 1\n",
    )
    _git(["add", "pkg/__init__.py", "pkg/module.py"], repo_root)
    _git(["commit", "-m", "Initial"], repo_root)

    _write(
        target / "module.py",
        "def act(value: int) -> int:\n    result = value + 1\n    return result\n",
    )
    _git(["add", "pkg/module.py"], repo_root)
    _git(["commit", "-m", "Refine"], repo_root)

    coverage_payload = {
        "files": {
            "pkg/module.py": {
                "executed_lines": [1, 2],
                "missing_lines": [3],
                "contexts": {"tests": [1]},
            }
        }
    }
    coverage_file = repo_root / "coverage.json"
    coverage_file.write_text(json.dumps(coverage_payload), encoding="utf-8")

    exit_code = module.run(
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

    assert payload["metadata"]["schema_version"] >= 2
    assert payload["metadata"]["coverage_sources"] == ["coverage.json"]

    statistics = payload["statistics"]
    coverage_stats = statistics.get("coverage")
    assert coverage_stats is not None
    assert coverage_stats["files_with_data"] == 1
    assert coverage_stats["tracked_lines"] == 3

    churn_stats = statistics.get("git_churn")
    assert churn_stats is not None
    assert churn_stats["files_with_data"] >= 1
    assert churn_stats["total_commits"] >= 2
    assert churn_stats["total_additions"] >= 1
    assert churn_stats["net_changes"] == churn_stats["total_additions"] - churn_stats["total_deletions"]

    module_entry = next(entry for entry in payload["files"] if entry["relative_path"] == "module.py")
    assert module_entry["coverage"]["executed_lines"] == [1, 2]
    assert module_entry["git_churn"]["commit_count"] >= 2
    latest_commit = module_entry["git_churn"]["latest_commit"]
    assert latest_commit["hash"]
    assert latest_commit["timestamp"].endswith("+00:00")

    central_dir = repo_root / ".repo_studios" / "command_center" / "reports" / "index_scan" / "pkg_index"
    central_files = _inventory_files(central_dir, "pkg")
    assert len(central_files) == 1
    assert json.loads(central_files[0].read_text(encoding="utf-8")) == payload


def test_commandview_inventory_keeps_static_and_dynamic_outputs_in_lockstep(tmp_path: Path) -> None:
    module = _load_module()

    repo_root = tmp_path
    target = repo_root / "pkg"
    _write(target / "__init__.py", "")
    _write(
        target / "module.py",
        (
            "def hydrate(value: int) -> int:\n"
            "    if value < 0:\n"
            "        return value - 1\n"
            "    return value + 1\n"
        ),
    )

    exit_code = module.run(
        [
            "--repo-root",
            str(repo_root),
            str(target),
        ]
    )
    assert exit_code == 0

    local_dir = target / "pkg_index"
    static_dir = repo_root / ".repo_studios" / "command_center" / "reports" / "index_scan" / "pkg_index"

    assert local_dir.exists()
    assert static_dir.exists()

    local_inventory = sorted(_inventory_files(local_dir, "pkg"), key=lambda path: path.name)
    static_inventory = sorted(_inventory_files(static_dir, "pkg"), key=lambda path: path.name)
    assert local_inventory
    assert static_inventory
    assert [path.name for path in local_inventory] == [path.name for path in static_inventory]

    for local_file, static_file in zip(local_inventory, static_inventory):
        assert local_file.name == static_file.name
        assert json.loads(local_file.read_text(encoding="utf-8")) == json.loads(static_file.read_text(encoding="utf-8"))

    local_screening = sorted(_screening_files(local_dir, "pkg"), key=lambda path: path.name)
    static_screening = sorted(_screening_files(static_dir, "pkg"), key=lambda path: path.name)
    assert local_screening
    assert static_screening
    assert [path.name for path in local_screening] == [path.name for path in static_screening]

    for local_file, static_file in zip(local_screening, static_screening):
        assert local_file.name == static_file.name
        assert json.loads(local_file.read_text(encoding="utf-8")) == json.loads(static_file.read_text(encoding="utf-8"))

    assert not (local_dir / "latest.json").exists()
    assert not (static_dir / "latest.json").exists()
