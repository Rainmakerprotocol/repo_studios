#!/usr/bin/env python
"""Refresh mypy baselines for agents and monitoring scopes.

Writes/overwrites:
  - mypy_agents_full.txt
  - mypy_monitoring_full.txt

Appends a trailing '# Refreshed: <timestamp>' line to each for auditability.

Exit code is always 0 (non-blocking) so this can be invoked in soft gates.
Use CI enforcement separately if needed.
"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

TARGETS = [
    ("agents", Path("mypy_agents_full.txt")),
    ("agents/core/monitoring", Path("mypy_monitoring_full.txt")),
]

MYPY_BASE_CMD = [
    "python",
    "-m",
    "mypy",
    "--hide-error-context",
    "--no-error-summary",
]


def run(cmd: list[str]) -> str:
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        return proc.stdout + proc.stderr
    except Exception as e:
        return f"[mypy-baseline] error invoking mypy: {e}\n"


def refresh() -> None:
    ts = time.strftime("%Y-%m-%d_%H%M%S", time.gmtime())
    for target, outfile in TARGETS:
        logging.info("[mypy-baseline] Running mypy for %s -> %s", target, outfile)
        output = run(MYPY_BASE_CMD + [target])
        outfile.write_text(output + f"\n# Refreshed: {ts}\n")
    logging.info("[mypy-baseline] Completed refresh at %s", ts)


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    refresh()
