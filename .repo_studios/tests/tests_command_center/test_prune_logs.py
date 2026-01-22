from __future__ import annotations

import os
from pathlib import Path

from libraries import prune_run_directories


def _make_run(base_dir: Path, name: str) -> Path:
    run = base_dir / name
    run.mkdir(parents=True, exist_ok=True)
    (run / "artifact.txt").write_text("data", encoding="utf-8")
    os.utime(run, None)
    return run


def test_prune_respects_keep_and_keep_sentinel(tmp_path: Path) -> None:
    base_dir = tmp_path / "runs"
    base_dir.mkdir()

    old = _make_run(base_dir, "run-20240101_000000")
    protected = _make_run(base_dir, "run-20240102_000000")
    newest = _make_run(base_dir, "run-20240103_000000")
    current = _make_run(base_dir, "run-20240104_000000")
    (protected / ".keep").write_text("", encoding="utf-8")

    result = prune_run_directories(
        base_dir,
        keep=3,
        stem_prefix="run-",
        current_run=current,
    )

    assert current in result.kept
    assert newest in result.kept
    assert protected in result.kept or protected in result.protected
    assert protected not in result.removed
    assert old in result.removed
    assert not result.failures


def test_prune_skips_unmatched_prefix(tmp_path: Path) -> None:
    base_dir = tmp_path / "runs"
    base_dir.mkdir()

    _make_run(base_dir, "run-20240101_000000")
    extra = _make_run(base_dir, "other-20240101")

    result = prune_run_directories(base_dir, keep=1, stem_prefix="run-")

    assert extra in result.skipped
    assert not result.removed
    assert not result.failures


def test_prune_timestamp_dirs_uses_name_sort_over_mtime(tmp_path: Path) -> None:
    base_dir = tmp_path / "runs"
    base_dir.mkdir()

    oldest_by_name = _make_run(base_dir, "20240101-0000")
    middle_by_name = _make_run(base_dir, "20240102-0000")
    newest_by_name = _make_run(base_dir, "20240103-0000")

    # Make mtimes misleading: set the oldest name to have the newest mtime.
    os.utime(oldest_by_name, (2000000000, 2000000000))
    os.utime(middle_by_name, (1500000000, 1500000000))
    os.utime(newest_by_name, (1000000000, 1000000000))

    result = prune_run_directories(base_dir, keep=1)

    assert newest_by_name in result.kept
    assert oldest_by_name in result.removed
    assert middle_by_name in result.removed
    assert not result.failures
