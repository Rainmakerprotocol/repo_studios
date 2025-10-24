"""Repository bootstrap and warning filters (relocated from sitecustomize.py).

This module carries the previous sitecustomize.py behavior (import-time side
effects) to ensure consistent path setup and warning hygiene across all Python
entry points when executed via the sitecustomize shim.

Actions performed:
- Ensure the repository root is on sys.path so that imports like `agents.*`
  succeed when invoked from nested contexts.
- Apply a small set of global warning filters to reduce non-actionable noise
  (e.g., transient sqlite ResourceWarnings; pydantic v2 config deprecation).

Note: This module is executed by the root-level sitecustomize shim using a
file-loader to avoid name conflicts with the stdlib module `faulthandler`.
"""

from __future__ import annotations

import os
import sys
import warnings
from datetime import UTC, datetime
from pathlib import Path

root = Path(__file__).resolve().parent.parent  # repo root
root_str = str(root)
if root_str and root_str not in sys.path:
    sys.path.insert(0, root_str)

# Reduce noise from known, non-actionable warnings across all entry points:
# - ResourceWarning about transient unclosed sqlite3 connections (coverage and
#   other libs may open/close handles at process teardown, which can trigger GC
#   warnings after pytest's own filtering window). Filter specifically on the
#   message to avoid hiding other ResourceWarnings.
warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message=r".*unclosed database in <sqlite3\.Connection object.*",
)

# - Pydantic v2 deprecation about class-based `config` seen in upstream libs.
#   Safe to ignore globally for test runs; pytest.ini also filters this, but we
#   include it here to catch non-pytest entry points.
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*Support for class-based `config` is deprecated.*",
)

# ---------------------------------------------------------------------------
# Standardize faulthandler environment flags and output layout
# ---------------------------------------------------------------------------


def _is_ci() -> bool:
    """Best-effort CI detection (GitHub Actions, generic CI)."""
    return os.getenv("GITHUB_ACTIONS") == "1" or os.getenv("CI") == "1"


"""Compute local defaults for FAULT_* without mutating the environment."""
_FAULT_ENABLE = os.getenv("FAULT_ENABLE", "1" if _is_ci() else "0")
_FAULT_MIN_INTERVAL_SEC = os.getenv("FAULT_MIN_INTERVAL_SEC", "60")
_FAULT_DUMP_TIMEOUT = os.getenv("FAULT_DUMP_TIMEOUT", "300")
_FAULT_MAX_DUMPS_PER_RUN = os.getenv("FAULT_MAX_DUMPS_PER_RUN", "5")
_FAULT_DUMP_LATER = os.getenv("FAULT_DUMP_LATER", "1" if _is_ci() else "0")
_FAULT_REDACT_PATHS = os.getenv("FAULT_REDACT_PATHS", "0")
_FAULT_OUTDIR = os.getenv("FAULT_OUTDIR")

if _FAULT_ENABLE == "1":  # only derive paths and create dirs when enabled
    # Base output dir under repo root
    base_dir = root / ".repo_studios" / "faulthandler"
    # Timestamp (UTC) for run folder; e.g., 2025-09-10_1553
    ts = datetime.now(UTC).strftime("%Y-%m-%d_%H%M")
    # Respect explicit FAULT_OUTDIR if provided; else derive from timestamp
    default_outdir = str(base_dir / ts)
    outdir = _FAULT_OUTDIR or default_outdir
    # Create directory if possible; ignore failures to avoid breaking startup
    try:  # pragma: no cover - import-time and filesystem dependent
        Path(outdir).mkdir(parents=True, exist_ok=True)
    except Exception:
        # Non-fatal: continue without artifact directory if filesystem not writable
        pass

    # Enable stdlib faulthandler with safe fallbacks
    try:  # pragma: no cover - import-time behavior depends on platform
        import faulthandler as _fh
        import json as _json
        import platform as _platform
        import sys as _sys
        import threading as _threading

        try:
            import fcntl as _fcntl  # POSIX-only
        except Exception:  # pragma: no cover - non-POSIX
            _fcntl = None  # type: ignore

        _lock = _threading.Lock()

        class _LockedFile:
            """Append-only file wrapper with optional POSIX flock and thread lock.

            Also tees writes to stderr so CI logs capture activation and dumps.
            """

            def __init__(self, path: Path, tee_stderr: bool = True):
                self._path = path
                self._tee = tee_stderr
                # Use line buffering if possible
                self._fh = open(path, "a", buffering=1, encoding="utf-8", errors="replace")

            def write(self, data: str) -> int:  # type: ignore[override]
                with _lock:
                    if _fcntl is not None:
                        try:
                            _fcntl.flock(self._fh.fileno(), _fcntl.LOCK_EX)
                        except Exception:
                            pass
                    try:
                        self._fh.write(data)
                        self._fh.flush()
                    finally:
                        if _fcntl is not None:
                            try:
                                _fcntl.flock(self._fh.fileno(), _fcntl.LOCK_UN)
                            except Exception:
                                pass
                if self._tee:
                    try:
                        _sys.stderr.write(data)
                        _sys.stderr.flush()
                    except Exception:
                        pass
                return len(data)

            def flush(self) -> None:
                with _lock:
                    try:
                        self._fh.flush()
                    except Exception:
                        pass

            def fileno(self) -> int:  # for faulthandler compliance
                return self._fh.fileno()

        _writer = None
        out_path = Path(outdir) / "stacks.log" if outdir else None
        if out_path is not None:
            try:
                _writer = _LockedFile(out_path)
            except Exception:
                _writer = None

        # Activation banner (compact)
        try:
            _sys.stderr.write(
                f"[faulthandler] enable=1 outdir={outdir or '-'} dump_later={_FAULT_DUMP_LATER}\n"
            )
            _sys.stderr.flush()
        except Exception:
            pass

        # Enable with all threads; prefer file writer when available
        try:
            _fh.enable(file=_writer or _sys.stderr, all_threads=True)
        except Exception:
            # Minimal fallback
            with _lock:
                try:
                    _fh.enable()
                except Exception:
                    pass

        # Register SIGUSR1 if available for on-demand dumps
        try:
            import signal as _signal

            if hasattr(_signal, "SIGUSR1"):
                with _lock:
                    _fh.register(_signal.SIGUSR1, file=_writer or _sys.stderr, all_threads=True)
        except Exception:
            # Non-POSIX or registration failure; ignore
            pass

        # Optional repeating hang dumps
        if _FAULT_DUMP_LATER == "1":
            try:
                timeout = int(_FAULT_DUMP_TIMEOUT or 300)
            except Exception:
                timeout = 300
            try:
                _fh.dump_traceback_later(timeout, repeat=True, file=_writer or _sys.stderr)
            except Exception:
                pass

        # MANIFEST.json (machine-readable)
        try:
            manifest_json = {
                "ts": datetime.now(UTC).isoformat(timespec="seconds"),
                "pid": os.getpid(),
                "python": _sys.version.split(" ")[0],
                "platform": _platform.platform(),
                "flags": {
                    "FAULT_ENABLE": _FAULT_ENABLE,
                    "FAULT_OUTDIR": outdir,
                    "FAULT_MIN_INTERVAL_SEC": _FAULT_MIN_INTERVAL_SEC,
                    "FAULT_DUMP_LATER": _FAULT_DUMP_LATER,
                    "FAULT_DUMP_TIMEOUT": _FAULT_DUMP_TIMEOUT,
                    "FAULT_MAX_DUMPS_PER_RUN": _FAULT_MAX_DUMPS_PER_RUN,
                    "FAULT_REDACT_PATHS": _FAULT_REDACT_PATHS,
                },
                "out_file": str(out_path) if out_path else None,
                "writer": "ok" if _writer is not None else "stderr",
            }
            (Path(outdir) / "MANIFEST.json").write_text(_json.dumps(manifest_json, indent=2))
        except Exception:
            pass
    except Exception:
        # If faulthandler is missing or any step fails, do not interrupt startup
        pass
