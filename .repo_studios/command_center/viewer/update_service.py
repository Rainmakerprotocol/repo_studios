"""Update orchestration helpers for the Command Center viewer."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

MAX_LOG_LINES = 50


class UpdateError(Exception):
    """Base class for update-related failures."""

    status_code: int = 400


class UpdateValidationError(UpdateError):
    """Raised when the update request is not valid."""


class UpdateAlreadyRunningError(UpdateError):
    """Raised when an update is already in progress."""

    status_code = 409


@dataclass(frozen=True)
class UpdateRequest:
    """Describes an update run request."""

    target_path: Path
    target_relative: str
    slug: str | None
    relative_path: str | None
    timestamp_iso: str | None


@dataclass(frozen=True)
class UpdateResult:
    """Outcome of an update run."""

    exit_code: int
    duration_seconds: float
    stdout_lines: list[str]
    stderr_lines: list[str]
    stdout_truncated: bool
    stderr_truncated: bool
    was_cancelled: bool
    slug: str | None
    target_relative: str
    timestamp_iso: str | None
    selector_refreshed: bool
    selector_error: str | None

    def to_payload(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the result."""

        return {
            "status": "ok",
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "was_cancelled": self.was_cancelled,
            "slug": self.slug,
            "timestamp_iso": self.timestamp_iso,
            "target_relative": self.target_relative,
            "selector_refreshed": self.selector_refreshed,
            "selector_error": self.selector_error,
            "logs": {
                "stdout": self.stdout_lines,
                "stderr": self.stderr_lines,
                "stdout_truncated": self.stdout_truncated,
                "stderr_truncated": self.stderr_truncated,
            },
        }


def _tail_lines(content: str, limit: int) -> tuple[list[str], bool]:
    lines = content.splitlines()
    if len(lines) <= limit:
        return lines, False
    return lines[-limit:], True


def _default_command_factory(repo_root: Path, request: UpdateRequest) -> Sequence[str]:
    launcher_path = repo_root / ".repo_studios/command_center/scripts/orchestrators/run_inventory_update.py"
    if not launcher_path.exists():
        raise UpdateValidationError(f"Inventory launcher not found: {launcher_path}")
    if not request.target_relative:
        raise UpdateValidationError("Update request is missing the target relative path")
    return [
        sys.executable,
        str(launcher_path),
        request.target_relative,
        "--repo-root",
        str(repo_root),
        "--log-level",
        "INFO",
    ]


CommandFactory = Callable[[Path, UpdateRequest], Sequence[str]]


def _regenerate_selector_json(repo_root: Path) -> None:
    from command_center.viewer.refresh import refresh_selector_payload

    payload = refresh_selector_payload(repo_root)
    output_path = repo_root / ".repo_studios/command_center/reports/selector.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class UpdateProcessManager:
    """Coordinates CommandView update subprocesses."""

    def __init__(self, repo_root: Path, command_factory: CommandFactory | None = None) -> None:
        self._repo_root = repo_root.resolve()
        self._command_factory = command_factory or _default_command_factory
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._cancelled = False

    def start(self, request: UpdateRequest) -> UpdateResult:
        """Launch the update process and wait for completion."""

        command = list(self._command_factory(self._repo_root, request))
        if not command:
            raise UpdateValidationError("Command factory produced an empty command")

        with self._lock:
            if self._process and self._process.poll() is None:
                raise UpdateAlreadyRunningError("Another update is already running")
            self._cancelled = False
            self._process = subprocess.Popen(
                command,
                cwd=str(self._repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            process = self._process

        start_time = time.monotonic()
        try:
            stdout, stderr = process.communicate()
        finally:
            duration = time.monotonic() - start_time
            with self._lock:
                was_cancelled = self._cancelled
                self._process = None
                self._cancelled = False

        stdout_lines, stdout_truncated = _tail_lines(stdout or "", MAX_LOG_LINES)
        stderr_lines, stderr_truncated = _tail_lines(stderr or "", MAX_LOG_LINES)

        selector_refreshed = False
        selector_error: str | None = None
        if process.returncode == 0 and not was_cancelled:
            try:
                _regenerate_selector_json(self._repo_root)
                selector_refreshed = True
            except Exception as exc:  # pragma: no cover - defensive fallback
                selector_error = f"Failed to refresh selector.json: {exc}"

        return UpdateResult(
            exit_code=process.returncode,
            duration_seconds=duration,
            stdout_lines=stdout_lines,
            stderr_lines=stderr_lines,
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
            was_cancelled=was_cancelled,
            slug=request.slug,
            target_relative=request.target_relative,
            timestamp_iso=request.timestamp_iso,
            selector_refreshed=selector_refreshed,
            selector_error=selector_error,
        )

    def cancel(self) -> bool:
        """Attempt to cancel the running update."""

        with self._lock:
            process = self._process
            if not process or process.poll() is not None:
                return False
            self._cancelled = True

        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        return True

    def is_running(self) -> bool:
        with self._lock:
            return bool(self._process and self._process.poll() is None)


def create_update_request(
    repo_root: Path,
    target: str,
    *,
    slug: str | None = None,
    relative_path: str | None = None,
    timestamp_iso: str | None = None,
) -> UpdateRequest:
    """Validate inputs and build an ``UpdateRequest``."""

    if not target or not isinstance(target, str):
        raise UpdateValidationError("A target path is required for the update request")

    repo_root = repo_root.resolve()
    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = (repo_root / target_path).resolve()
    else:
        target_path = target_path.resolve()

    try:
        target_relative = str(target_path.relative_to(repo_root))
    except ValueError as exc:
        raise UpdateValidationError("Target must reside within the repository root") from exc

    if not target_path.exists():
        raise UpdateValidationError(f"Target directory does not exist: {target_relative}")
    if not target_path.is_dir():
        raise UpdateValidationError(f"Target path is not a directory: {target_relative}")

    return UpdateRequest(
        target_path=target_path,
        target_relative=target_relative,
        slug=slug,
        relative_path=relative_path,
        timestamp_iso=timestamp_iso,
    )


__all__ = [
    "UpdateAlreadyRunningError",
    "UpdateError",
    "UpdateProcessManager",
    "UpdateRequest",
    "UpdateResult",
    "UpdateValidationError",
    "create_update_request",
]
