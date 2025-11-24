#!/usr/bin/env python3
"""Orchestrate the command center pipeline (inventory → analysis → duplicate scan)."""

from __future__ import annotations

import argparse
import importlib.util
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


@dataclass(frozen=True)
class StepResult:
    exit_code: int
    artifacts: tuple[Path, ...] = ()


INVENTORY_SCRIPT_RELATIVE = Path(".repo_studios/command_center/scripts/producers/generate_commandview_inventory.py")
ANALYSIS_SCRIPT_RELATIVE = Path(".repo_studios/command_center/scripts/summarizers/generate_function_analysis.py")
SCAN_SCRIPT_RELATIVE = Path(".repo_studios/command_center/scripts/aggregators/scan_duplicates.py")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    target: Path


@dataclass(frozen=True)
class Options:
    log_level: str


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_command_center_pipeline",
        description=__doc__ or "",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "target",
        help="Directory whose inventory, analysis, and duplicate scan should be refreshed.",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root. Defaults to this script's grandparent directory.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity shared with delegated scripts.",
    )
    return parser.parse_args(argv)


def build_options(args: argparse.Namespace) -> Options:
    return Options(log_level=args.log_level)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def _resolve_within_repo(repo_root: Path, candidate: Path) -> Path:
    resolved = candidate if candidate.is_absolute() else repo_root / candidate
    resolved = resolved.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Path must reside within the repo root: {resolved}") from exc
    return resolved


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[4]
    raw_target = str(args.target)
    if raw_target.startswith("/."):
        target_candidate = repo_root / raw_target.lstrip("/\\")
    else:
        target_candidate = Path(raw_target)
    target = _resolve_within_repo(repo_root, target_candidate)
    return Paths(repo_root=repo_root, target=target)


def _load_cli_module(script_path: Path, module_name: str):
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_run_function(script_path: Path, module_name: str) -> Callable[[Iterable[str] | None], int]:
    if not script_path.exists():
        raise FileNotFoundError(f"Required script not found: {script_path}")
    module = _load_cli_module(script_path, module_name)
    run_fn = getattr(module, "run", None)
    if not callable(run_fn):
        raise RuntimeError(f"Module {module_name} at {script_path} does not expose a callable run().")
    return run_fn  # type: ignore[return-value]


def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:
    candidates = sorted(directory.glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"No {label} artifacts matching '{pattern}' found in {directory}.")
    return candidates[-1]


def _run_inventory(paths: Paths, options: Options) -> StepResult:
    script_path = (paths.repo_root / INVENTORY_SCRIPT_RELATIVE).resolve()
    run_fn = _load_run_function(script_path, "command_center.producers.generate_commandview_inventory")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--log-level",
        options.log_level,
        str(paths.target),
    ]
    exit_code = int(run_fn(argv))
    if exit_code != 0:
        return StepResult(exit_code=exit_code)
    index_dir = paths.target / f"{paths.target.name}_index"
    try:
        artifact = _latest_artifact(index_dir, f"{paths.target.name}_commandview_[0-9]*.json", "inventory")
    except FileNotFoundError as exc:
        logging.error("Inventory step succeeded but produced no artifacts: %s", exc)
        return StepResult(exit_code=1)
    return StepResult(exit_code=0, artifacts=(artifact,))


def _run_analysis(paths: Paths, options: Options, inventory_path: Path | None) -> StepResult:
    if inventory_path is None:
        logging.error("Inventory artifact not available; analysis step cannot proceed.")
        return StepResult(exit_code=1)
    script_path = (paths.repo_root / ANALYSIS_SCRIPT_RELATIVE).resolve()
    run_fn = _load_run_function(script_path, "command_center.summarizers.generate_function_analysis")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--log-level",
        options.log_level,
        "--inventory-file",
        str(inventory_path),
        str(paths.target),
    ]
    exit_code = int(run_fn(argv))
    if exit_code != 0:
        return StepResult(exit_code=exit_code)
    index_dir = inventory_path.parent
    try:
        artifact = _latest_artifact(index_dir, f"{paths.target.name}_analysis-*.json", "analysis")
    except FileNotFoundError as exc:
        logging.error("Analysis step succeeded but produced no artifacts: %s", exc)
        return StepResult(exit_code=1)
    return StepResult(exit_code=0, artifacts=(artifact,))


def _run_scan(paths: Paths, options: Options, analysis_path: Path | None) -> StepResult:
    if analysis_path is None:
        logging.error("Analysis artifact not available; duplicate scan cannot proceed.")
        return StepResult(exit_code=1)
    script_path = (paths.repo_root / SCAN_SCRIPT_RELATIVE).resolve()
    run_fn = _load_run_function(script_path, "command_center.aggregators.scan_duplicates")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--log-level",
        options.log_level,
        "--target",
        str(paths.target),
        "--skip-upstream",
        "--analysis-file",
        str(analysis_path),
    ]
    exit_code = int(run_fn(argv))
    if exit_code != 0:
        return StepResult(exit_code=exit_code)
    index_dir = paths.target / f"{paths.target.name}_index"
    try:
        matrix_path = _latest_artifact(index_dir, f"{paths.target.name}_duplicate_matrix-*.json", "duplicate matrix")
        summary_path = _latest_artifact(index_dir, f"{paths.target.name}_duplicate_summary-*.md", "duplicate summary")
    except FileNotFoundError as exc:
        logging.error("Duplicate scan step succeeded but expected artifacts are missing: %s", exc)
        return StepResult(exit_code=1)
    return StepResult(exit_code=0, artifacts=(matrix_path, summary_path))


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    options = build_options(args)
    configure_logging(options.log_level)
    try:
        paths = build_paths(args)
    except ValueError as exc:
        logging.error("%s", exc)
        return 1
    if not paths.target.exists():
        logging.error("Target does not exist: %s", paths.target)
        return 1
    if not paths.target.is_dir():
        logging.error("Target is not a directory: %s", paths.target)
        return 1

    logging.info("Running function inventory step")
    try:
        inventory_result = _run_inventory(paths, options)
    except (FileNotFoundError, ImportError, RuntimeError) as exc:
        logging.error("%s", exc)
        return 1
    if inventory_result.exit_code != 0:
        logging.error("Function inventory step failed with exit code %d", inventory_result.exit_code)
        return inventory_result.exit_code
    if not inventory_result.artifacts:
        logging.error("Function inventory step completed without producing an index artifact.")
        return 1

    logging.info("Running function analysis step")
    try:
        analysis_result = _run_analysis(paths, options, inventory_result.artifacts[0])
    except (FileNotFoundError, ImportError, RuntimeError) as exc:
        logging.error("%s", exc)
        return 1
    if analysis_result.exit_code != 0:
        logging.error("Function analysis step failed with exit code %d", analysis_result.exit_code)
        return analysis_result.exit_code
    if not analysis_result.artifacts:
        logging.error("Function analysis step completed without producing an analysis artifact.")
        return 1

    logging.info("Running duplicate scan step")
    try:
        scan_result = _run_scan(paths, options, analysis_result.artifacts[0])
    except (FileNotFoundError, ImportError, RuntimeError) as exc:
        logging.error("%s", exc)
        return 1
    if scan_result.exit_code != 0:
        logging.error("Duplicate scan step failed with exit code %d", scan_result.exit_code)
        return scan_result.exit_code
    if len(scan_result.artifacts) < 2:
        logging.error("Duplicate scan step completed without producing matrix and summary artifacts.")
        return 1

    logging.info(
        "Pipeline complete for %s (matrix=%s summary=%s)",
        paths.target,
        scan_result.artifacts[0],
        scan_result.artifacts[1],
    )
    return 0


def main() -> None:
    raise SystemExit(run())


__all__ = [
    "run",
    "main",
    "parse_args",
    "build_options",
    "build_paths",
]
