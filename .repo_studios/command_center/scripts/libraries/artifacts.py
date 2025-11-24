"""Artifact lifecycle helpers for Command Center scripts."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Literal


def copy_latest_artifact(src: Path, dest: Path) -> None:
    """Mirror ``src`` to ``dest`` using a hard link when possible."""
    try:
        if dest.exists():
            dest.unlink()
        dest.hardlink_to(src)
    except OSError:
        dest.write_bytes(src.read_bytes())


ArtifactKind = Literal["json", "text", "bytes", "copy"]


@dataclass(frozen=True)
class ReportArtifact:
    """Descriptor for a report artifact written alongside producer runs."""

    filename: str
    pointer: str | None = None
    kind: ArtifactKind = "text"
    content: Any | None = None
    encoding: str = "utf-8"
    sort_keys: bool = True
    writer: Callable[[Path], Path] | None = None

    def materialize(self, run_dir: Path) -> Path:
        """Write the artifact into ``run_dir`` and return its path."""

        if self.writer is not None:
            path = self.writer(run_dir)
            if not isinstance(path, Path):  # pragma: no cover - defensive
                raise TypeError("Artifact writer must return a pathlib.Path")
            if not path.exists():  # pragma: no cover - defensive
                raise FileNotFoundError(path)
            return path

        target = run_dir / self.filename
        target.parent.mkdir(parents=True, exist_ok=True)

        value = self.content() if callable(self.content) else self.content

        if self.kind == "json":
            payload = value if value is not None else {}
            text = json.dumps(payload, indent=2, sort_keys=self.sort_keys) + "\n"
            target.write_text(text, encoding=self.encoding)
        elif self.kind == "text":
            text = "" if value is None else str(value)
            target.write_text(text, encoding=self.encoding)
        elif self.kind == "bytes":
            if value is None:
                data = b""
            elif isinstance(value, (bytes, bytearray)):
                data = bytes(value)
            else:  # pragma: no cover - defensive
                raise TypeError("Byte artifacts require bytes-like content")
            target.write_bytes(data)
        elif self.kind == "copy":
            src_path = value if isinstance(value, Path) else Path(value)
            if not src_path.exists():  # pragma: no cover - defensive
                raise FileNotFoundError(src_path)
            if src_path.resolve() == target.resolve():
                return target
            target.write_bytes(src_path.read_bytes())
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unsupported artifact kind: {self.kind}")

        return target


@dataclass(frozen=True)
class WriteReportArtifactsResult:
    """Result metadata returned after writing report artifacts."""

    run_dir: Path
    slug: str
    artifacts: dict[str, Path]


def _normalize_timestamp(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _prune_old_runs(output_dir: Path, *, stem: str, keep: int, current_run: Path) -> None:
    keep = max(keep, 1)
    if not output_dir.exists():
        return
    candidates = [node for node in output_dir.iterdir() if node.is_dir() and node.name.startswith(f"{stem}-")]
    candidates.sort(key=lambda node: node.name, reverse=True)
    for index, node in enumerate(candidates):
        if index < keep or node == current_run:
            continue
        if (node / ".keep").exists():
            continue
        shutil.rmtree(node, ignore_errors=True)


def write_report_artifacts(
    *,
    stem: str,
    timestamp: datetime,
    output_dir: Path,
    artifacts: Iterable[ReportArtifact],
    keep: int,
) -> WriteReportArtifactsResult:
    """Write report artifacts and mirror latest pointers.

    Parameters
    ----------
    stem:
        Prefix used for the run directory (e.g. ``dependency_hygiene``).
    timestamp:
        Timestamp associated with the run; naive values assume UTC.
    output_dir:
        Directory that will contain the timestamped run folder and latest pointers.
    artifacts:
        Iterable of :class:`ReportArtifact` descriptors describing files to write.
    keep:
        Number of historical runs to retain (minimum of one).
    """

    normalized = _normalize_timestamp(timestamp)
    slug = normalized.strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = output_dir / f"{stem}-{slug}"
    run_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for descriptor in artifacts:
        path = descriptor.materialize(run_dir)
        written[descriptor.filename] = path
        if descriptor.pointer:
            copy_latest_artifact(path, output_dir / descriptor.pointer)

    _prune_old_runs(output_dir, stem=stem, keep=keep, current_run=run_dir)

    return WriteReportArtifactsResult(run_dir=run_dir, slug=slug, artifacts=written)
