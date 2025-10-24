#!/usr/bin/env python3
"""Compatibility shim for legacy inventory validator entrypoint."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    repo_root = _resolve_repo_root()
    module_path = repo_root / ".repo_studios" / "scripts" / "producers" / "validate_inventory.py"
    spec = importlib.util.spec_from_file_location("repo_studios.tools.validate_inventory", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    runner = getattr(module, "main")
    args = argv if argv is not None else sys.argv[1:]
    return int(runner(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
