"""Shared helpers for faulthandler run analysis.

This module centralizes the logic for parsing faulthandler stack dumps so both
producer and consumer scripts can reuse the same data model. Keeping the parsing
in one place helps the refactor loop avoid divergent heuristics.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Sequence

__all__ = [
    "FaultSignature",
    "FaultAnalysisResult",
    "DEFAULT_TOP_N",
    "THREAD_HEADER_RE",
    "FRAME_RE",
    "ensure_manifest",
    "read_stacks_text",
    "collect_signatures",
    "build_fault_report",
]

DEFAULT_TOP_N = 10
THREAD_HEADER_RE = re.compile(r"^(Current thread|Thread) ")
FRAME_RE = re.compile(r"^\s*File \"(?P<file>.+?)\", line (?P<line>\d+), in (?P<func>[^\n]+)")


@dataclass
class FaultSignature:
    """Aggregated signature for a distinct stack fingerprint."""

    signature_id: str
    count: int
    top_module: str
    top_func: str
    top_file: str
    top_line: int
    threads: list[str]
    first_seen_ts: str
    last_seen_ts: str


@dataclass
class FaultAnalysisResult:
    """Structured payload emitted by :func:`build_fault_report`."""

    report: dict[str, object]
    signatures: list[FaultSignature]
    combined_text: str


def _iter_thread_blocks(lines: Iterable[str]) -> Iterable[list[str]]:
    """Yield contiguous lines per thread block.

    A block starts at a line whose prefix indicates faulthandler thread output
    and continues until the next such header (or EOF).
    """

    buf: list[str] = []
    for ln in lines:
        if THREAD_HEADER_RE.match(ln):
            if buf:
                yield buf
                buf = []
        buf.append(ln)
    if buf:
        yield buf


@dataclass
class _TopFrame:
    module: str | None
    func: str | None
    file: str | None
    line: int | None


def _extract_top_frames(block: Sequence[str], n: int) -> list[_TopFrame]:
    frames: list[_TopFrame] = []
    for ln in block:
        m = FRAME_RE.match(ln)
        if not m:
            continue
        file_path = m.group("file")
        module = Path(file_path).stem if file_path else None
        func = m.group("func").strip()
        try:
            line = int(m.group("line"))
        except Exception:
            line = None
        frames.append(_TopFrame(module=module, func=func, file=file_path, line=line))
        if len(frames) >= n:
            break
    if not frames:
        frames.append(_TopFrame(module=None, func=None, file=None, line=None))
    return frames


def ensure_manifest(outdir: Path) -> dict[str, object]:
    """Ensure MANIFEST.json exists and return its parsed contents."""

    manifest_path = outdir / "MANIFEST.json"
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    manifest = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "pid": None,
        "python": None,
        "platform": None,
        "flags": {},
        "writer": None,
    }
    try:
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except Exception:
        # If we cannot persist the manifest, still return the in-memory copy so
        # downstream callers have a deterministic structure.
        pass
    return manifest


def read_stacks_text(stacks_path: Path) -> str:
    """Read stacks.log content with defensive fallbacks."""

    try:
        return stacks_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _load_process_salt(outdir: Path, manifest: dict[str, object] | None) -> str:
    """Build a salt that stabilizes signature IDs across runs."""

    py = None
    plat = None
    if isinstance(manifest, dict):
        py = manifest.get("python")
        plat = manifest.get("platform")
    if not py or not plat:
        try:
            import platform as _platform
            import sys as _sys

            py = py or _sys.version.split(" ")[0]
            plat = plat or _platform.platform()
        except Exception:
            py = py or "unknown"
            plat = plat or "unknown"
    return f"py={py}|plat={plat}|run={outdir.name}"


def _signature_id(frames: Sequence[_TopFrame], salt: str) -> str:
    parts: list[str] = []
    for frame in frames:
        file_base = None
        try:
            file_base = Path(frame.file or "?").name
        except Exception:
            file_base = frame.file or "?"
        parts.append(
            "::".join(
                [
                    frame.module or "?",
                    frame.func or "?",
                    file_base or "?",
                    str(frame.line if frame.line is not None else "?"),
                ]
            )
        )
    raw = f"{salt}|N={len(frames)}|" + "|".join(parts)
    return __import__("hashlib").sha256(raw.encode("utf-8")).hexdigest()[:16]


def collect_signatures(
    stacks_text: str,
    *,
    salt: str,
    top_n: int,
    now_iso: str,
) -> tuple[list[FaultSignature], int]:
    """Aggregate per-signature metrics from raw stack text."""

    lines = stacks_text.splitlines()
    rows_map: dict[str, dict[str, object]] = {}
    thread_block_count = 0
    for block in _iter_thread_blocks(lines):
        thread_block_count += 1
        thread_id = block[0].strip() if block else "(unknown)"
        frames = _extract_top_frames(block, top_n)
        sig = _signature_id(frames, salt)
        top_frame = frames[0]
        top_module = top_frame.module or "?"
        top_func = top_frame.func or "?"
        top_file = top_frame.file or "?"
        top_line = top_frame.line or 0
        if sig not in rows_map:
            rows_map[sig] = {
                "signature_id": sig,
                "count": 0,
                "top_module": top_module,
                "top_func": top_func,
                "top_file": top_file,
                "top_line": top_line,
                "threads": set(),
                "first_seen_ts": now_iso,
                "last_seen_ts": now_iso,
            }
        row = rows_map[sig]
        row["count"] = int(row["count"]) + 1
        row["last_seen_ts"] = now_iso
        threads = row["threads"]
        assert isinstance(threads, set)
        threads.add(thread_id)
    signatures: list[FaultSignature] = []
    for data in rows_map.values():
        threads = data.pop("threads")  # type: ignore[assignment]
        try:
            thread_list = sorted(threads)  # type: ignore[arg-type]
        except Exception:
            thread_list = []
        signatures.append(
            FaultSignature(
                signature_id=data["signature_id"],
                count=int(data["count"]),
                top_module=str(data["top_module"]),
                top_func=str(data["top_func"]),
                top_file=str(data["top_file"]),
                top_line=int(data["top_line"]),
                threads=thread_list,
                first_seen_ts=str(data["first_seen_ts"]),
                last_seen_ts=str(data["last_seen_ts"]),
            )
        )
    signatures.sort(key=lambda s: (-s.count, s.signature_id))
    return signatures, thread_block_count


def build_fault_report(
    outdir: Path,
    *,
    now: datetime | None = None,
    top_n: int = DEFAULT_TOP_N,
) -> FaultAnalysisResult:
    """Summarize a faulthandler run directory."""

    now = now or datetime.now(UTC)
    manifest = ensure_manifest(outdir)
    stacks_path = outdir / "stacks.log"
    stacks_text = read_stacks_text(stacks_path)
    salt = _load_process_salt(outdir, manifest)
    signatures, thread_block_count = collect_signatures(
        stacks_text,
        salt=salt,
        top_n=top_n,
        now_iso=now.isoformat(timespec="seconds"),
    )
    summary = {
        "signature_count": len(signatures),
        "thread_block_count": thread_block_count,
        "top_frame_limit": top_n,
        "stack_log_exists": stacks_path.exists(),
        "stack_text_bytes": len(stacks_text.encode("utf-8")),
    }
    report = {
        "schema_version": 1,
        "generated_utc": now.isoformat(timespec="seconds"),
        "run_dir": str(outdir.resolve()),
        "stacks_log": str(stacks_path.resolve()) if stacks_path.exists() else None,
        "summary": summary,
        "signatures": [asdict(sig) for sig in signatures],
        "manifest": manifest,
        "process_salt": salt,
    }
    return FaultAnalysisResult(report=report, signatures=signatures, combined_text=stacks_text)
