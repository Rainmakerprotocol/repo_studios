#!/usr/bin/env python3
"""Repo Studios Basic shim that delegates to the Command Center gap analyzer."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_command_center_module() -> ModuleType:
    module_name = "repo_studios.command_center.producers.analyze_standards_index_gaps"
    script_path = (
        Path(__file__).resolve().parents[2]
        / "command_center"
        / "scripts"
        / "producers"
        / "analyze_standards_index_gaps.py"
    )
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError("Unable to load Command Center standards gap analyzer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_IMPL = _load_command_center_module()

DEFAULT_OUTPUT_DIR = _IMPL.DEFAULT_OUTPUT_DIR
DEFAULT_INDEX_PATH = _IMPL.DEFAULT_INDEX_PATH
DEFAULT_CATEGORIES_PATH = _IMPL.DEFAULT_CATEGORIES_PATH
DEFAULT_ARTIFACTS_TO_KEEP = _IMPL.DEFAULT_ARTIFACTS_TO_KEEP
RUN_STEM = _IMPL.RUN_STEM
RUN_PREFIX = _IMPL.RUN_PREFIX
SCHEMA_VERSION = _IMPL.SCHEMA_VERSION
GapCandidate = _IMPL.GapCandidate
Paths = _IMPL.Paths
Options = _IMPL.Options
PATHS_CONFIG = _IMPL.PATHS_CONFIG
OPTIONS_CONFIG = _IMPL.OPTIONS_CONFIG
parse_args = _IMPL.parse_args
run = _IMPL.run
main = _IMPL.main
build_report = _IMPL.build_report
render_markdown = _IMPL.render_markdown
render_tsv = _IMPL.render_tsv
emit_runtime_log = _IMPL.emit_runtime_log

COMMAND_CENTER_MODULE = _IMPL
COMMAND_CENTER_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "command_center"
    / "scripts"
    / "producers"
    / "analyze_standards_index_gaps.py"
)

__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_INDEX_PATH",
    "DEFAULT_CATEGORIES_PATH",
    "DEFAULT_ARTIFACTS_TO_KEEP",
    "RUN_STEM",
    "RUN_PREFIX",
    "SCHEMA_VERSION",
    "GapCandidate",
    "Paths",
    "Options",
    "PATHS_CONFIG",
    "OPTIONS_CONFIG",
    "parse_args",
    "run",
    "main",
    "build_report",
    "render_markdown",
    "render_tsv",
    "emit_runtime_log",
    "COMMAND_CENTER_MODULE",
    "COMMAND_CENTER_SCRIPT_PATH",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
