"""Helpers for invoking Command Center summarizers from orchestrators."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Callable, Iterable, cast

SummarizerCallable = Callable[[Iterable[str] | None], int]


class SummarizerError(RuntimeError):
    """Raised when a summarizer fails to execute successfully."""


def load_summarizer(script_path: Path, *, module_name: str) -> SummarizerCallable:
    """Load a summarizer module from ``script_path`` and return its ``run`` helper."""

    script_path = script_path.resolve()
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Unable to load module spec for {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not isinstance(module, ModuleType):  # pragma: no cover
        raise ImportError(f"Failed to load module from {script_path}")
    run_callable = getattr(module, "run", None)
    if not callable(run_callable):
        raise AttributeError(f"Summarizer module at {script_path} does not expose a callable run() helper")
    return cast(SummarizerCallable, run_callable)


def run_summarizer(run_callable: SummarizerCallable, argv: Iterable[str] | None = None, *, name: str | None = None) -> None:
    """Execute a summarizer ``run`` helper and raise :class:`SummarizerError` on failure."""

    exit_code = run_callable(argv)
    if exit_code != 0:
        label = name or getattr(run_callable, "__name__", "summarizer")
        raise SummarizerError(f"{label} failed with exit code {exit_code}")
