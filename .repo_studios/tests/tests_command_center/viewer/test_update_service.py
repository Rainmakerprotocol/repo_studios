from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

from command_center.viewer import update_service


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_default_command_factory_uses_inventory_launcher() -> None:
    repo_root = _repo_root()
    launcher_path = repo_root / ".repo_studios/command_center/scripts/orchestrators/run_inventory_update.py"
    assert launcher_path.exists(), "Inventory launcher script must exist for update workflow tests"

    request = update_service.create_update_request(
        repo_root,
        ".repo_studios/command_center/scripts",
        slug="command_center_scripts",
    )

    command = update_service._default_command_factory(repo_root, request)

    assert command[0] == sys.executable
    assert command[1] == str(launcher_path)
    assert command[2] == request.target_relative
    assert command[3:] == ["--repo-root", str(repo_root), "--log-level", "INFO"]


def test_cancel_terminates_running_update(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / ".repo_studios/command_center/scripts"
    target.mkdir(parents=True, exist_ok=True)

    request = update_service.create_update_request(repo_root, str(target))

    def fake_command_factory(_repo_root: Path, _request: update_service.UpdateRequest):
        return [
            sys.executable,
            "-u",
            "-c",
            "import time; time.sleep(5)",
        ]

    manager = update_service.UpdateProcessManager(repo_root, command_factory=fake_command_factory)

    results: list[update_service.UpdateResult] = []

    def run_update() -> None:
        results.append(manager.start(request))

    worker = threading.Thread(target=run_update)
    worker.start()
    time.sleep(0.25)
    cancelled = manager.cancel()
    worker.join(timeout=10)

    assert cancelled is True
    assert worker.is_alive() is False
    assert results, "Update manager did not produce a result"
    result = results[0]
    assert result.was_cancelled is True
    assert result.selector_refreshed is False


def test_successful_update_refreshes_selector(tmp_path: Path) -> None:
    repo_root = tmp_path
    target = repo_root / ".repo_studios/command_center/scripts"
    target.mkdir(parents=True, exist_ok=True)

    request = update_service.create_update_request(repo_root, str(target))

    def fake_command_factory(_repo_root: Path, _request: update_service.UpdateRequest):
        return [
            sys.executable,
            "-u",
            "-c",
            "import sys",
        ]

    manager = update_service.UpdateProcessManager(repo_root, command_factory=fake_command_factory)

    calls: list[Path] = []

    original_refresh = update_service._regenerate_selector_json

    def fake_refresh(path: Path) -> None:
        calls.append(path)

    update_service._regenerate_selector_json = fake_refresh
    try:
        result = manager.start(request)
    finally:
        update_service._regenerate_selector_json = original_refresh

    assert calls, "Selector regeneration hook was not invoked"
    assert result.exit_code == 0
    assert result.was_cancelled is False
    assert result.selector_refreshed is True
    assert result.selector_error is None