from __future__ import annotations

from pathlib import Path

import pytest

from command_center.scripts.orchestrators import run_inventory_update as inventory_update


def test_inventory_update_invokes_producer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    target_dir = repo_root / ".repo_studios" / "command_center" / "demo"
    target_dir.mkdir(parents=True, exist_ok=True)

    captured = {}

    def fake_run(argv: list[str] | None = None) -> int:
        captured["argv"] = list(argv or [])
        return 0

    monkeypatch.setattr(inventory_update.generate_commandview_inventory, "run", fake_run)

    exit_code = inventory_update.run([
        ".repo_studios/command_center/demo",
        "--repo-root",
        str(repo_root),
        "--log-level",
        "WARNING",
    ])

    assert exit_code == 0
    assert captured["argv"] == [
        str(target_dir),
        "--repo-root",
        str(repo_root),
        "--log-level",
        "WARNING",
    ]


def test_inventory_update_validates_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    disallowed = repo_root / "external"
    disallowed.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(inventory_update.generate_commandview_inventory, "run", lambda argv=None: 0)

    with pytest.raises(SystemExit) as excinfo:
        inventory_update.run([
            str(disallowed),
            "--repo-root",
            str(repo_root),
        ])

    assert "Target must reside" in str(excinfo.value)


def test_inventory_update_requires_existing_directory(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    missing = repo_root / ".repo_studios" / "command_center" / "missing"

    with pytest.raises(SystemExit):
        inventory_update.run([
            str(missing),
            "--repo-root",
            str(repo_root),
        ])
