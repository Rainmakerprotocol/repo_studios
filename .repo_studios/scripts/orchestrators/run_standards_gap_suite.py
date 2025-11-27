#!/usr/bin/env python3
"""Coordinate standards index regeneration and gap analysis."""

from __future__ import annotations

import argparse
import importlib.util
import logging
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Sequence

LIBRARIES_ROOT = Path(__file__).resolve().parents[2] / "command_center" / "scripts"

try:  # Prefer direct import when command center libraries are on sys.path
    from libraries import (  # type: ignore
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when running in isolation
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore  # noqa: E402
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )


GENERATE_SCRIPT_RELATIVE = Path(".repo_studios/scripts/producers/generate_standards_index.py")
GAP_SCRIPT_RELATIVE = Path(".repo_studios/scripts/producers/analyze_standards_index_gaps.py")

DEFAULT_INDEX_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_index_reports")
DEFAULT_GAP_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_gap_reports")
DEFAULT_INDEX_PATH = Path(
    ".repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml"
)
LEGACY_INDEX_PATH = Path(".repo_studios/scripts/repo_standards_index.yaml")
DEFAULT_CATEGORIES_PATH = Path(".repo_studios/scripts/.repo_studios/standards_categories.yaml")

DEFAULT_ARTIFACTS_TO_KEEP = 5
DEFAULT_MAX_SHOW = 8


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    index_output_dir: Path
    gap_output_dir: Path
    index_path: Path
    categories_path: Path


@dataclass(frozen=True)
class KeepValues:
    index_keep: int
    gap_keep: int


@dataclass
class Options:
    log_level: str
    timestamp: str | None
    max_show: int
    skip_index: bool
    legacy_json: Path | None
    index_keep: int
    gap_keep: int


@dataclass
class StepOutcome:
    name: str
    exit_code: int
    argv: tuple[str, ...]
    payload: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "exit_code": self.exit_code,
            "argv": list(self.argv),
        }
        if self.payload is not None:
            data["payload"] = self.payload
        if self.error is not None:
            data["error"] = self.error
        return data


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "index_output_dir": PathSpec(
            field="index_output_dir",
            default=DEFAULT_INDEX_OUTPUT_DIR,
            ensure_dir=True,
            within_repo=True,
        ),
        "gap_output_dir": PathSpec(
            field="gap_output_dir",
            default=DEFAULT_GAP_OUTPUT_DIR,
            ensure_dir=True,
            within_repo=True,
        ),
        "index_path": PathSpec(field="index_path", default=DEFAULT_INDEX_PATH, within_repo=True),
        "categories_path": PathSpec(field="categories_path", default=DEFAULT_CATEGORIES_PATH, within_repo=True),
    },
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={
        "index_keep": KeepSpec(field="index_artifacts_to_keep", minimum=1),
        "gap_keep": KeepSpec(field="gap_artifacts_to_keep", minimum=1),
    },
)


def _ensure_index_path(paths: Paths, logger: logging.Logger) -> Paths:
    if paths.index_path.exists():
        return paths
    legacy_candidate = (paths.repo_root / LEGACY_INDEX_PATH).resolve()
    if legacy_candidate.exists():
        logger.warning(
            "standards index missing at %s; falling back to legacy snapshot %s",
            paths.index_path,
            legacy_candidate,
        )
        return replace(paths, index_path=legacy_candidate)
    return paths


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--index-output-dir", help="Override index run output directory")
    parser.add_argument("--gap-output-dir", help="Override gap analysis output directory")
    parser.add_argument(
        "--index-path",
        help=(
            "Path to repo_standards_index.yaml (defaults to "
            ".repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml)"
        ),
    )
    parser.add_argument("--categories-path", help="Path to standards_categories.yaml")
    parser.add_argument("--legacy-json", help="Optional legacy JSON output path passed to the analyzer")
    parser.add_argument("--timestamp", help="ISO8601 timestamp forwarded to both steps")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity shared with delegated scripts",
    )
    parser.add_argument(
        "--max-show",
        type=int,
        default=DEFAULT_MAX_SHOW,
        help="Maximum gap candidates to echo per source during analysis logs",
    )
    parser.add_argument(
        "--index-artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention budget for index generator runs",
    )
    parser.add_argument(
        "--gap-artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention budget for gap analyzer runs",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Reuse the existing index artifacts without re-running the generator",
    )
    return parser.parse_args(argv)


def _configure_logging(level: str) -> logging.Logger:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")
    return logging.getLogger("run_standards_gap_suite")


def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    return candidate


def _invoke_main(func: Callable[[Sequence[str]], Any], argv: Sequence[str]) -> int:
    try:
        result = func(list(argv))
    except SystemExit as exc:  # pragma: no cover - defensive guard for argparse exits
        code = exc.code
        if isinstance(code, int):
            return code
        return 1
    if isinstance(result, int):
        return result
    try:
        return int(result)
    except (TypeError, ValueError):
        return 0


def _load_callable(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str]], Any]:
    script_path = script_path.resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"Required script not found: {script_path}")
    if module_name in sys.modules:
        module = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load module from {script_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    func = getattr(module, attribute, None)
    if not callable(func):
        raise AttributeError(f"Module {module_name} missing callable {attribute}()")
    return func


def _run_generator(paths: Paths, options: Options) -> StepOutcome:
    script_path = paths.repo_root / GENERATE_SCRIPT_RELATIVE
    main_callable = _load_callable(script_path, "repo_studios.scripts.producers.generate_standards_index", "main")
    argv: list[str] = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.index_output_dir),
        "--index-path",
        str(paths.index_path),
        "--categories-path",
        str(paths.categories_path),
        "--artifacts-to-keep",
        str(options.index_keep),
        "--log-level",
        options.log_level,
    ]
    if options.timestamp:
        argv.extend(["--timestamp", options.timestamp])
    exit_code = _invoke_main(main_callable, argv)
    return StepOutcome(name="generate_standards_index", exit_code=exit_code, argv=tuple(argv))


def _run_gap_analysis(paths: Paths, options: Options) -> StepOutcome:
    script_path = paths.repo_root / GAP_SCRIPT_RELATIVE
    run_callable = _load_callable(script_path, "repo_studios.scripts.producers.analyze_standards_index_gaps", "run")
    argv: list[str] = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.gap_output_dir),
        "--index-path",
        str(paths.index_path),
        "--categories-path",
        str(paths.categories_path),
        "--artifacts-to-keep",
        str(options.gap_keep),
        "--log-level",
        options.log_level,
        "--max",
        str(options.max_show),
    ]
    if options.timestamp:
        argv.extend(["--timestamp", options.timestamp])
    if options.legacy_json is not None:
        argv.extend(["--json", str(options.legacy_json)])
    try:
        payload = run_callable(argv)
        exit_code = 0
        error: str | None = None
    except RuntimeError as exc:
        logging.getLogger("run_standards_gap_suite").error("%s", exc)
        payload = None
        exit_code = 2
        error = str(exc)
    return StepOutcome(
        name="analyze_standards_index_gaps",
        exit_code=exit_code,
        argv=tuple(argv),
        payload=payload if isinstance(payload, dict) else None,
        error=error,
    )


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    logger = _configure_logging(args.log_level)
    paths = build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__).resolve())
    paths = _ensure_index_path(paths, logger)
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    options = Options(
        log_level=args.log_level,
        timestamp=args.timestamp,
        max_show=max(1, args.max_show),
        skip_index=args.skip_index,
        legacy_json=_resolve_optional_path(paths.repo_root, args.legacy_json),
        index_keep=keep_values.index_keep,
        gap_keep=keep_values.gap_keep,
    )

    logger = _configure_logging(options.log_level)

    result: dict[str, Any] = {"status": "pending", "index": None, "gap": None}

    index_outcome: StepOutcome | None = None
    if not options.skip_index:
        logger.info("Running standards index generator")
        index_outcome = _run_generator(paths, options)
        result["index"] = index_outcome.to_dict()
        if index_outcome.exit_code != 0:
            result["status"] = "index_failed"
            logger.error("Index generation failed with exit code %d", index_outcome.exit_code)
            return result

    logger.info("Running standards gap analyzer")
    gap_outcome = _run_gap_analysis(paths, options)
    result["gap"] = gap_outcome.to_dict()

    if gap_outcome.exit_code != 0:
        result["status"] = "gap_failed"
        return result

    result["status"] = "success"
    return result


def main(argv: Sequence[str] | None = None) -> int:
    result = run(argv)
    status = result.get("status")
    if status == "success":
        return 0
    if status == "index_failed":
        index_info = result.get("index")
        exit_code = index_info.get("exit_code") if isinstance(index_info, dict) else None
        return exit_code if isinstance(exit_code, int) and exit_code > 0 else 1
    if status == "gap_failed":
        gap_info = result.get("gap")
        exit_code = gap_info.get("exit_code") if isinstance(gap_info, dict) else None
        return exit_code if isinstance(exit_code, int) and exit_code > 0 else 1
    return 1


__all__ = [
    "run",
    "main",
    "parse_args",
    "PATHS_CONFIG",
    "OPTIONS_CONFIG",
    "Paths",
    "Options",
    "KeepValues",
    "StepOutcome",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
