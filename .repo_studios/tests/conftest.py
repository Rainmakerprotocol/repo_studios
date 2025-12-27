from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest

VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "tools" / "validate_inventory.py"

REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[1]
COMMAND_CENTER_SCRIPTS_ROOT = REPO_STUDIOS_ROOT / "command_center" / "scripts"

for candidate in (REPO_STUDIOS_ROOT, COMMAND_CENTER_SCRIPTS_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Create a temporary directory with the `.repo_studios/` marker.

    Many scripts call `validate_repo_root()` which requires the `.repo_studios/`
    directory to exist. Use this fixture to get a valid repo root for testing.

    Returns:
        Path to tmp_path with `.repo_studios/` subdirectory created.
    """
    marker = tmp_path / ".repo_studios"
    marker.mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def repo_root_with_reports(tmp_path: Path) -> Path:
    """Create a temporary repo root with standard report directory structure.

    Creates:
        - `.repo_studios/`
        - `.repo_studios/command_center/reports/`
        - `.repo_studios/reports/`

    Returns:
        Path to tmp_path with directories created.
    """
    marker = tmp_path / ".repo_studios"
    marker.mkdir(parents=True, exist_ok=True)
    (marker / "command_center" / "reports").mkdir(parents=True, exist_ok=True)
    (marker / "reports").mkdir(parents=True, exist_ok=True)
    return tmp_path


def load_validator(tmp_path: Path, json_output: bool = False) -> Callable[[], tuple[int, str]]:
    schema_root = tmp_path / "inventory_schema"

    def _run() -> tuple[int, str]:
        args = [
            sys.executable,
            str(VALIDATOR_PATH),
            "--schema-root",
            str(schema_root),
        ]
        if json_output:
            args.append("--json")
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
        stdout = proc.stdout.strip()
        return proc.returncode, stdout

    return _run
