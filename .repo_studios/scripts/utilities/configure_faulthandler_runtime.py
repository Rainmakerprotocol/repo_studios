"""Faulthandler bootstrap and runtime configuration helpers.

This module keeps the historical sitecustomize side effects but now routes the
faulthandler setup through testable helpers so we can exercise retention,
manifests, and import-time behaviour safely. It is imported by the repository
sitecustomize shim.
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import sys
import threading
import warnings
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Dict, Mapping, MutableMapping, Optional

root = Path(__file__).resolve().parents[3]  # repository root
root_str = str(root)
if root_str and root_str not in sys.path:
    sys.path.insert(0, root_str)

libraries_root = root / ".repo_studios" / "command_center" / "scripts"
libraries_root_str = str(libraries_root)
if libraries_root_str and libraries_root_str not in sys.path:
    sys.path.insert(0, libraries_root_str)

from libraries import prune_run_directories

# Reduce noise from known, non-actionable warnings across all entry points.
warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message=r".*unclosed database in <sqlite3\.Connection object.*",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*Support for class-based `config` is deprecated.*",
)

_LOCK = threading.Lock()
try:  # POSIX-only; ignored elsewhere.
    import fcntl as _FCNTL  # type: ignore
except Exception:  # pragma: no cover - Windows and other platforms
    _FCNTL = None  # type: ignore


def _default_base_dir(allow_legacy: bool) -> Path:
    if allow_legacy:
        return root / ".repo_studios" / "faulthandler"
    return root / ".repo_studios" / "reports" / "orchestrator_logs" / "faulthandler_logs"


def _is_truthy(value: Optional[str], *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _get_env(env: Mapping[str, str], key: str, default: str) -> str:
    value = env.get(key)
    return value if value is not None else default


def _safe_int(value: str, fallback: int) -> int:
    try:
        return int(value)
    except Exception:
        return fallback


def _is_ci(env: Mapping[str, str]) -> bool:
    return env.get("GITHUB_ACTIONS") == "1" or env.get("CI") == "1"


@dataclass
class FaultSettings:
    enable: bool
    dump_later: bool
    tee_stderr: bool
    min_interval: int
    dump_timeout: int
    max_dumps_per_run: int
    redact_paths: bool
    artifacts_to_keep: int
    outdir: Path
    base_dir: Path
    derived_outdir: bool
    allow_legacy: bool
    env_snapshot: Dict[str, str]


def _resolve_fault_settings(
    env: Mapping[str, str],
    now_factory: Callable[[], datetime],
) -> FaultSettings:
    ci_default = "1" if _is_ci(env) else "0"
    enable_flag = _get_env(env, "FAULT_ENABLE", ci_default)
    dump_later_flag = _get_env(env, "FAULT_DUMP_LATER", ci_default)
    tee_stderr_flag = _get_env(env, "FAULT_TEE_STDERR", "1")
    artifacts_flag = _get_env(env, "FAULT_ARTIFACTS_TO_KEEP", "10")

    allow_legacy_flag = _get_env(env, "FAULT_LOGS_ALLOW_LEGACY", "0")
    allow_legacy = _is_truthy(allow_legacy_flag, default=False)

    base_override = env.get("FAULT_BASE_DIR")
    base_dir = Path(base_override) if base_override else _default_base_dir(allow_legacy)

    outdir_override = env.get("FAULT_OUTDIR")
    if outdir_override:
        outdir = Path(outdir_override)
        derived = False
    else:
        ts = now_factory().strftime("%Y-%m-%d_%H%M")
        outdir = base_dir / ts
        derived = True

    env_snapshot = {
        "FAULT_ENABLE": enable_flag,
        "FAULT_OUTDIR": outdir_override or "",
        "FAULT_BASE_DIR": base_override or "",
        "FAULT_MIN_INTERVAL_SEC": _get_env(env, "FAULT_MIN_INTERVAL_SEC", "60"),
        "FAULT_DUMP_TIMEOUT": _get_env(env, "FAULT_DUMP_TIMEOUT", "300"),
        "FAULT_MAX_DUMPS_PER_RUN": _get_env(env, "FAULT_MAX_DUMPS_PER_RUN", "5"),
        "FAULT_DUMP_LATER": dump_later_flag,
        "FAULT_REDACT_PATHS": _get_env(env, "FAULT_REDACT_PATHS", "0"),
        "FAULT_TEE_STDERR": tee_stderr_flag,
        "FAULT_ARTIFACTS_TO_KEEP": artifacts_flag,
        "FAULT_LOGS_ALLOW_LEGACY": allow_legacy_flag,
    }

    return FaultSettings(
        enable=_is_truthy(enable_flag, default=_is_truthy(ci_default, default=False)),
        dump_later=_is_truthy(dump_later_flag, default=_is_truthy(ci_default, default=False)),
        tee_stderr=_is_truthy(tee_stderr_flag, default=True),
        min_interval=_safe_int(env_snapshot["FAULT_MIN_INTERVAL_SEC"], 60),
        dump_timeout=_safe_int(env_snapshot["FAULT_DUMP_TIMEOUT"], 300),
        max_dumps_per_run=_safe_int(env_snapshot["FAULT_MAX_DUMPS_PER_RUN"], 5),
        redact_paths=_is_truthy(env_snapshot["FAULT_REDACT_PATHS"], default=False),
        artifacts_to_keep=max(0, _safe_int(artifacts_flag, 10)),
        outdir=outdir,
        base_dir=base_dir,
        derived_outdir=derived,
        allow_legacy=allow_legacy,
        env_snapshot=env_snapshot,
    )


class _LockedFile:
    def __init__(self, path: Path, tee_stderr: bool) -> None:
        self._path = path
        self._tee = tee_stderr
        self._fh = open(path, "a", buffering=1, encoding="utf-8", errors="replace")

    def write(self, data: str) -> int:  # type: ignore[override]
        with _LOCK:
            if _FCNTL is not None:
                try:
                    _FCNTL.flock(self._fh.fileno(), _FCNTL.LOCK_EX)
                except Exception:
                    pass
            try:
                self._fh.write(data)
                self._fh.flush()
            finally:
                if _FCNTL is not None:
                    try:
                        _FCNTL.flock(self._fh.fileno(), _FCNTL.LOCK_UN)
                    except Exception:
                        pass
        if self._tee:
            try:
                sys.stderr.write(data)
                sys.stderr.flush()
            except Exception:
                pass
        return len(data)

    def flush(self) -> None:
        with _LOCK:
            try:
                self._fh.flush()
            except Exception:
                pass

    def fileno(self) -> int:
        return self._fh.fileno()


def _build_writer(outdir: Path, tee_stderr: bool) -> tuple[Optional[_LockedFile], str]:
    out_path = outdir / "stacks.log"
    try:
        return _LockedFile(out_path, tee_stderr=tee_stderr), "file"
    except Exception:
        return None, "stderr"


def _activate_faulthandler(writer: Optional[_LockedFile], tee_label: str, dump_later: bool, dump_timeout: int) -> Dict[str, object]:
    info: Dict[str, object] = {
        "activated": False,
        "writer": tee_label,
        "registered_sigusr1": False,
        "dump_later": False,
        "errors": [],
    }

    try:
        fh = importlib.import_module("faulthandler")
    except Exception as exc:  # pragma: no cover - happens when module absent
        info["errors"].append(f"import_failed:{exc}")
        return info

    target = writer or sys.stderr

    try:
        fh.enable(file=target, all_threads=True)
        info["activated"] = True
    except Exception as exc:
        info["errors"].append(f"enable_failed:{exc}")
        try:
            fh.enable()
            info["activated"] = True
            info["writer"] = "stderr"
        except Exception as inner:
            info["errors"].append(f"fallback_failed:{inner}")

    try:
        import signal

        if hasattr(signal, "SIGUSR1"):
            fh.register(signal.SIGUSR1, file=target, all_threads=True)
            info["registered_sigusr1"] = True
    except Exception as exc:
        info["errors"].append(f"sigusr1_failed:{exc}")

    if dump_later:
        try:
            fh.dump_traceback_later(dump_timeout, repeat=True, file=target)
            info["dump_later"] = True
        except Exception as exc:
            info["errors"].append(f"dump_later_failed:{exc}")

    return info


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    try:
        path.write_text(json.dumps(payload, indent=2))
    except Exception:
        pass


ACTIVE_WRITER: Optional[_LockedFile] = None
LAST_BOOTSTRAP: Optional[Dict[str, object]] = None


def bootstrap(
    env: Optional[Mapping[str, str]] = None,
    now_factory: Optional[Callable[[], datetime]] = None,
) -> Dict[str, object]:
    effective_env: MutableMapping[str, str] = dict(env or os.environ)
    if _is_truthy(effective_env.get("FAULT_DISABLE"), default=False):
        return {"status": "skipped", "reason": "disabled_by_env"}

    now = now_factory or (lambda: datetime.now(UTC))
    settings = _resolve_fault_settings(effective_env, now)

    result: Dict[str, object] = {
        "status": "enabled" if settings.enable else "disabled",
        "outdir": str(settings.outdir if settings.enable else ""),
        "base_dir": str(settings.base_dir),
        "artifacts_to_keep": settings.artifacts_to_keep,
        "allow_legacy": settings.allow_legacy,
        "derived_outdir": settings.derived_outdir,
    }

    if not settings.enable:
        return result

    try:
        settings.outdir.mkdir(parents=True, exist_ok=True)
    except Exception:
        result["status"] = "error"
        result["reason"] = "mkdir_failed"
        return result

    writer, label = _build_writer(settings.outdir, settings.tee_stderr)
    global ACTIVE_WRITER
    ACTIVE_WRITER = writer

    try:
        sys.stderr.write(
            f"[faulthandler] enable=1 outdir={settings.outdir} dump_later={int(settings.dump_later)}\n"
        )
        sys.stderr.flush()
    except Exception:
        pass

    prune_count = 0
    if settings.derived_outdir and settings.outdir.parent == settings.base_dir:
        prune_summary = prune_run_directories(
            settings.base_dir,
            keep=settings.artifacts_to_keep,
            current_run=settings.outdir,
        )
        prune_count = len(prune_summary.removed)

    activation = _activate_faulthandler(writer, label, settings.dump_later, settings.dump_timeout)

    manifest = {
        "ts": now().isoformat(timespec="seconds"),
        "pid": os.getpid(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "flags": settings.env_snapshot,
        "resolved": {
            "outdir": str(settings.outdir),
            "base_dir": str(settings.base_dir),
            "tee_stderr": settings.tee_stderr,
            "artifacts_to_keep": settings.artifacts_to_keep,
            "derived_outdir": settings.derived_outdir,
            "allow_legacy": settings.allow_legacy,
        },
        "faulthandler": activation,
        "retention": {"keep": settings.artifacts_to_keep, "pruned": prune_count},
    }
    _write_json(settings.outdir / "MANIFEST.json", manifest)

    bundle_summary = {
        "status": result["status"],
        "outdir": manifest["resolved"]["outdir"],
        "writer": activation["writer"],
        "retention": manifest["retention"],
        "flags": settings.env_snapshot,
    }
    _write_json(settings.outdir / "bundle_summary.json", bundle_summary)

    result.update({
        "manifest": manifest,
        "bundle_summary": bundle_summary,
        "pruned": prune_count,
    })
    if activation.get("errors"):
        result["status"] = "warning"
    return result


def _auto_bootstrap() -> None:
    global LAST_BOOTSTRAP
    try:
        LAST_BOOTSTRAP = bootstrap()
    except Exception:
        LAST_BOOTSTRAP = {"status": "error"}


if not _is_truthy(os.getenv("FAULT_DISABLE"), default=False):
    _auto_bootstrap()


if __name__ == "__main__":
    payload = LAST_BOOTSTRAP if LAST_BOOTSTRAP is not None else bootstrap()
    try:
        print(json.dumps(payload, indent=2))
    except Exception:
        print(payload)
