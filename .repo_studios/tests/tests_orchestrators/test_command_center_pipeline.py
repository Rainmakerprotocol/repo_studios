"""Integration coverage for the command center pipeline orchestrator."""

from __future__ import annotations

import importlib
import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ORCHESTRATOR_DIR = REPO_ROOT / ".repo_studios" / "command_center" / "scripts" / "orchestrators"
AGGREGATOR_DIR = REPO_ROOT / ".repo_studios" / "command_center" / "scripts" / "aggregators"
SCRIPTS_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"


def _load_slugify() -> Callable[[Path], str]:
    try:
        module = importlib.import_module("libraries")
    except ModuleNotFoundError:  # pragma: no cover - test sandbox fallback
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        module = importlib.import_module("libraries")
    return module.slugify_relative


slugify_relative = _load_slugify()


def _load_module(module_path: Path, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ORCHESTRATOR_MODULE = _load_module(
    ORCHESTRATOR_DIR / "run_command_center_pipeline.py",
    "run_command_center_pipeline",
)
AGGREGATOR_MODULE = _load_module(
    AGGREGATOR_DIR / "scan_duplicates.py",
    "command_center.scan_duplicates",
)

orchestrator_run = getattr(ORCHESTRATOR_MODULE, "run", None)
if not callable(orchestrator_run):
    raise AttributeError("Orchestrator module is missing a callable run() helper.")
_slugify_relative_callable = getattr(AGGREGATOR_MODULE, "_slugify_relative", None)
if not callable(_slugify_relative_callable):
    raise AttributeError("Aggregator module is missing _slugify_relative().")
orchestrator_run_fn: Callable[[list[str] | None], int] = orchestrator_run  # type: ignore[assignment]
_slugify_relative: Callable[[Path], str] = _slugify_relative_callable  # type: ignore[assignment]
assert _slugify_relative is slugify_relative

TARGET_DIR = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"


def _duplicate_run_dir(repo_root: Path, target: Path) -> Path:
    return (
        repo_root
        / ".repo_studios"
        / "command_center"
        / "reports"
        / AGGREGATOR_MODULE.VIEWER_SLUG
        / AGGREGATOR_MODULE.TOPIC_SLUG
    )


def test_pipeline_smoke_updates_artifacts() -> None:
    repo_root = REPO_ROOT
    target = TARGET_DIR
    start_time = time.time()

    exit_code = orchestrator_run_fn(["--repo-root", str(repo_root), "--log-level", "INFO", str(target)])
    assert exit_code == 0

    viewer_base = _duplicate_run_dir(repo_root, target)
    assert viewer_base.exists(), "Expected duplicate scan viewer directory to exist."
    run_dirs = sorted(node for node in viewer_base.iterdir() if node.is_dir())
    assert run_dirs, "Expected at least one duplicate scan run directory."
    latest_run = run_dirs[-1]
    matrix_path = latest_run / f"{target.name}_duplicate_matrix.json"
    summary_path = latest_run / f"{target.name}_duplicate_summary.md"
    assert matrix_path.exists(), "Expected duplicate matrix artifact after pipeline run."
    assert summary_path.exists(), "Expected duplicate summary artifact after pipeline run."
    assert matrix_path.stat().st_mtime >= start_time

    inventory_dir = target / f"{target.name}_index"
    inventory_files = list(inventory_dir.glob(f"{target.name}_commandview_[0-9]*.json"))
    assert inventory_files, "Expected inventory artifacts after pipeline run."
    assert any(path.stat().st_mtime >= start_time for path in inventory_files)
    index_matrices = list(inventory_dir.glob(f"{target.name}_duplicate_matrix-*.json"))
    assert index_matrices, "Expected duplicate index artifacts after pipeline run."
    assert any(path.stat().st_mtime >= start_time for path in index_matrices)


def test_pipeline_failure_propagates_exit_code() -> None:
    repo_root = REPO_ROOT
    missing_target = repo_root / "nonexistent_orchestrator_target"
    if missing_target.exists():
        pytest.skip("Synthetic failure target unexpectedly exists.")

    exit_code = orchestrator_run_fn(["--repo-root", str(repo_root), str(missing_target)])
    assert exit_code != 0


def test_pipeline_allows_repo_root_prefixed_target() -> None:
    repo_root = REPO_ROOT
    target = "/.repo_studios/command_center/scripts"
    exit_code = orchestrator_run_fn(["--repo-root", str(repo_root), target])
    assert exit_code == 0
    viewer_base = _duplicate_run_dir(repo_root, TARGET_DIR)
    run_dirs = sorted(node for node in viewer_base.iterdir() if node.is_dir())
    assert run_dirs
