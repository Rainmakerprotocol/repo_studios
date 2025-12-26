#!/usr/bin/env python3
"""Compatibility shim for legacy inventory validator entrypoint."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _discover_repo_root(origin: Path) -> Path:
    origin = origin.resolve()
    for candidate in (origin, *origin.parents):
        if candidate.name == ".repo_studios":
            continue
        if (candidate / ".repo_studios").is_dir():
            return candidate
    raise ValueError(
        "Unable to locate repo root from origin; expected a '.repo_studios' directory marker."
    )


def _bootstrap_scripts_root(repo_root: Path) -> Path:
    return (repo_root / ".repo_studios" / "command_center" / "scripts").resolve()


def _bootstrap_repo_studios_root(repo_root: Path) -> Path:
    return (repo_root / ".repo_studios").resolve()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Explicit repo root; defaults to marker-based discovery when omitted.",
    )
    parsed, _unknown = parser.parse_known_args(args)

    bootstrap_root = Path(parsed.repo_root).resolve() if parsed.repo_root else _discover_repo_root(Path(__file__))
    repo_studios_root = _bootstrap_repo_studios_root(bootstrap_root)
    scripts_root = _bootstrap_scripts_root(bootstrap_root)
    for candidate in (repo_studios_root, scripts_root):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))

    from libraries.cli import resolve_repo_root  # noqa: E402

    repo_root = resolve_repo_root(parsed.repo_root, origin=Path(__file__))
    module_path = repo_root / ".repo_studios" / "scripts" / "producers" / "validate_inventory.py"
    spec = importlib.util.spec_from_file_location("repo_studios.tools.validate_inventory", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    runner = getattr(module, "main")
    return int(runner(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
