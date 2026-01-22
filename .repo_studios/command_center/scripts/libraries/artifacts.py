"""Artifact lifecycle helpers for Command Center scripts."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Literal

from .prune_logs import prune_run_directories


# Re-export for external consumers that may rely on the shared helper
__all__ = [
    "copy_latest_artifact",
    "ReportArtifact",
    "WriteReportArtifactsResult",
    "write_report_artifacts",
    "prune_run_directories",
]


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
    viewer: str | None = None
    topic: str | None = None


def _normalize_timestamp(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _prune_old_runs(output_dir: Path, *, stem: str, keep: int, current_run: Path) -> None:
    """Prune old stem-prefixed run directories.

    Uses name-based sorting since directory names encode timestamps in a sortable format
    (e.g., stem-YYYYMMDD_HHMMSS). This differs from prune_run_directories which uses mtime.
    """
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


def _prune_topic_runs(topic_dir: Path, *, keep: int, current_run: Path | None = None) -> None:
    """Prune old topic run directories.

    Uses name-based sorting since directory names encode timestamps in a sortable format
    (e.g., YYYYMMDD-HHMM). This differs from prune_run_directories which uses mtime.
    """
    keep = max(keep, 1)
    if not topic_dir.exists():
        return

    candidates = [node for node in topic_dir.iterdir() if node.is_dir()]

    kept: list[Path] = []
    filtered: list[Path] = []

    if current_run is not None:
        try:
            resolved_current = current_run.resolve()
        except OSError:
            resolved_current = None
    else:
        resolved_current = None

    for candidate in candidates:
        if resolved_current is not None:
            try:
                if candidate.resolve() == resolved_current:
                    kept.append(candidate)
                    continue
            except OSError:
                pass
        filtered.append(candidate)

    filtered.sort(key=lambda node: node.name, reverse=True)

    remaining_slots = max(keep - len(kept), 0)
    for node in filtered:
        if remaining_slots > 0:
            kept.append(node)
            remaining_slots -= 1
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
    viewer: str | None = None,
    topic: str | None = None,
) -> WriteReportArtifactsResult:
    """Write report artifacts using timestamped run directories.

    Parameters
    ----------
    stem:
        Prefix used for the run directory (e.g. ``dependency_hygiene``).
    timestamp:
        Timestamp associated with the run; naive values assume UTC.
    output_dir:
        Directory that will contain the timestamped run folder or hierarchical tree.
    artifacts:
        Iterable of :class:`ReportArtifact` descriptors describing files to write.
    keep:
        Number of historical runs to retain (minimum of one).
    viewer:
        Optional viewer slug enabling the ``viewer/topic/timestamp`` layout.
    topic:
        Optional topic slug enabling the ``viewer/topic/timestamp`` layout.
    """

    normalized = _normalize_timestamp(timestamp)

    use_hierarchical_layout = viewer is not None and topic is not None

    if use_hierarchical_layout:
        slug = normalized.strftime("%Y%m%d-%H%M")
        run_dir = output_dir / viewer / topic / slug
        run_dir.mkdir(parents=True, exist_ok=True)
        _prune_topic_runs(run_dir.parent, keep=keep, current_run=run_dir)
    else:
        slug = normalized.strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        run_dir = output_dir / f"{stem}-{slug}"
        run_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for descriptor in artifacts:
        path = descriptor.materialize(run_dir)
        written[descriptor.filename] = path
        if descriptor.pointer and not use_hierarchical_layout:
            copy_latest_artifact(path, output_dir / descriptor.pointer)

    if not use_hierarchical_layout:
        _prune_old_runs(output_dir, stem=stem, keep=keep, current_run=run_dir)

    return WriteReportArtifactsResult(
        run_dir=run_dir,
        slug=slug,
        artifacts=written,
        viewer=viewer,
        topic=topic,
    )
