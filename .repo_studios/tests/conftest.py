from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable

VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "tools" / "validate_inventory.py"


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
