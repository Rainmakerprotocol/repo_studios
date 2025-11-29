"""Shared helpers for pruning timestamped run directories."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PruneResult:
    """Summary of a pruning operation."""

    kept: list[Path]
    removed: list[Path]
    protected: list[Path]
    skipped: list[Path]
    failures: list[Path]


def prune_run_directories(
    base_dir: Path,
    *,
    keep: int,
    stem_prefix: str | None = None,
    current_run: Path | None = None,
    honor_keep_sentinel: bool = True,
    logger: logging.Logger | None = None,
) -> PruneResult:
    """Prune historical run directories under ``base_dir``.

    Parameters
    ----------
    base_dir:
        Directory containing timestamped run subdirectories.
    keep:
        Maximum number of runs to retain (minimum of one).
    stem_prefix:
        Optional directory name prefix filter (e.g. ``"fault_pipeline-"``).
        When provided, only matching directories are considered for pruning.
    current_run:
        Path to the run that triggered pruning, if known. When the run lives
        inside ``base_dir`` it is always retained and does not count toward the
        ``keep`` budget.
    honor_keep_sentinel:
        When ``True``, directories containing a ``.keep`` file are never
        deleted, regardless of position.
    logger:
        Optional logger used for debug/warning messages.
    """

    kept: list[Path] = []
    removed: list[Path] = []
    protected: list[Path] = []
    skipped: list[Path] = []
    failures: list[Path] = []

    if keep <= 0 or not base_dir.exists():
        return PruneResult(kept, removed, protected, skipped, failures)

    try:
        candidates = [node for node in base_dir.iterdir() if node.is_dir()]
    except OSError:
        if logger:
            logger.debug("prune_run_directories: unable to list %s", base_dir, exc_info=True)
        return PruneResult(kept, removed, protected, skipped, failures)

    def _is_current(path: Path) -> bool:
        if current_run is None:
            return False
        try:
            return path.resolve() == current_run.resolve()
        except OSError:
            return False

    filtered: list[Path] = []
    for candidate in candidates:
        if stem_prefix and not candidate.name.startswith(stem_prefix):
            skipped.append(candidate)
            continue
        if _is_current(candidate):
            kept.append(candidate)
            continue
        filtered.append(candidate)

    def _sort_key(path: Path) -> tuple[float, str]:
        try:
            stat = path.stat()
            return (stat.st_mtime, path.name)
        except OSError:
            return (0.0, path.name)

    filtered.sort(key=_sort_key, reverse=True)

    remaining_slots = max(keep, 0)
    if kept:
        remaining_slots = max(keep - len(kept), 0)

    for entry in filtered:
        if remaining_slots > 0:
            kept.append(entry)
            remaining_slots -= 1
            continue

        if honor_keep_sentinel and (entry / ".keep").exists():
            protected.append(entry)
            continue

        try:
            for child in entry.rglob("*"):
                try:
                    child.chmod(0o700)
                except Exception:  # pragma: no cover - best-effort cleanup
                    pass
            try:
                entry.chmod(0o700)
            except Exception:  # pragma: no cover - best-effort cleanup
                pass
            shutil.rmtree(entry, ignore_errors=False)
            removed.append(entry)
        except Exception:  # pragma: no cover - defensive
            failures.append(entry)
            if logger:
                logger.warning("prune_run_directories: failed to remove %s", entry, exc_info=True)

    return PruneResult(kept, removed, protected, skipped, failures)
