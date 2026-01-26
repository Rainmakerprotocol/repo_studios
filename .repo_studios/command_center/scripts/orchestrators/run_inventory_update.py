#!/usr/bin/env python3
"""Launch CommandView inventory regeneration for viewer updates."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

try:
    from libraries import PathSpec, PathsConfig, build_standard_paths
    from cc_producers import generate_commandview_inventory
except ModuleNotFoundError:  # pragma: no cover - CLI fallback for script execution
    SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
    if str(SCRIPTS_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_ROOT))
    from libraries import PathSpec, PathsConfig, build_standard_paths  # noqa: E402
    from cc_producers import generate_commandview_inventory  # noqa: E402

ALLOWED_ROOT = Path(".repo_studios")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    target: Path


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "target": PathSpec(field="target", default=Path(".")),
    },
    repo_root_depth=4,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument(
        "target",
        help="Command Center target directory to refresh. Relative paths resolve within the repo root.",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root. Defaults to ancestor traversal from this script.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity shared with delegated scripts.",
    )
    return parser


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s %(message)s")


def _ensure_target_allowed(repo_root: Path, target: Path) -> None:
    allowed_root = (repo_root / ALLOWED_ROOT).resolve()
    try:
        target.relative_to(allowed_root)
    except ValueError as exc:
        raise SystemExit(f"Target must reside within {allowed_root} (got {target})") from exc


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__).resolve())
    target = paths.target
    if not target.exists():
        parser.error(f"Target directory does not exist: {target}")
    if not target.is_dir():
        parser.error(f"Target path is not a directory: {target}")

    _ensure_target_allowed(paths.repo_root, target)

    configure_logging(args.log_level)

    inventory_args = [
        str(target),
        "--repo-root",
        str(paths.repo_root),
        "--log-level",
        args.log_level,
    ]
    exit_code = generate_commandview_inventory.run(inventory_args)
    try:
        return int(exit_code)
    except (TypeError, ValueError):  # pragma: no cover - defensive guard
        return 1


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
