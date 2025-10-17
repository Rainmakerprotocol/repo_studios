"""
Generate structured fault artifacts for a faulthandler run directory.

Inputs (env / discovery):
  - --outdir or FAULT_OUTDIR: target run dir. If unset, auto-pick the latest under
    ./.repo_studios/faulthandler/<ts>/.

Outputs (within FAULT_OUTDIR):
  - MANIFEST.json (best-effort: create minimal if missing)
  - dumps/combined.txt (raw copy of stacks.log)
  - stacks.csv (schema below)
  - SUMMARY.md (human-readable summary)

CSV schema (headers):
  signature_id,count,top_module,top_func,top_file,top_line,threads,first_seen_ts,last_seen_ts

Notes:
  - Parser is best-effort against stdlib faulthandler format. If segmentation
    is unreliable, we still emit dumps/combined.txt and aggregate across the file.
  - Timestamps default to current UTC when per-observation times are unavailable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Anchor runs base to the repository root (parent of .repo_studios)
ROOT = Path(__file__).resolve().parents[1]
RUNS_BASE = ROOT / ".repo_studios/faulthandler"
DEFAULT_TOP_N = 10


def _find_latest_outdir() -> Path | None:
    try:
        if not RUNS_BASE.exists():
            return None
        candidates = [p for p in RUNS_BASE.iterdir() if p.is_dir()]
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0] if candidates else None
    except Exception:
        return None


def _discover_outdir(explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit)
    env = os.getenv("FAULT_OUTDIR")
    if env:
        return Path(env)
    return _find_latest_outdir()


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _ensure_manifest(outdir: Path) -> None:
    mf = outdir / "MANIFEST.json"
    if mf.exists():
        return
    manifest = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "pid": None,
        "python": None,
        "platform": None,
        "flags": {},
        "writer": None,
    }
    try:
        mf.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except Exception:
        pass


@dataclass
class TopFrame:
    module: str | None
    func: str | None
    file: str | None
    line: int | None


THREAD_HEADER_RE = re.compile(r"^(Current thread|Thread) ")
FRAME_RE = re.compile(r"^\s*File \"(?P<file>.+?)\", line (?P<line>\d+), in (?P<func>[^\n]+)")


def _iter_thread_blocks(lines: Iterable[str]) -> Iterable[list[str]]:
    """Yield lines per thread block, separated by thread headers.

    This groups contiguous lines starting at a line matching THREAD_HEADER_RE
    until just before the next header or EOF.
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


def _extract_top_frames(block: list[str], n: int) -> list[TopFrame]:
    frames: list[TopFrame] = []
    for ln in block:
        m = FRAME_RE.match(ln)
        if not m:
            continue
        file_path = m.group("file")
        try:
            module = Path(file_path).stem
        except Exception:
            module = None
        func = m.group("func").strip()
        top_file = file_path
        try:
            top_line = int(m.group("line"))
        except Exception:
            top_line = None
        frames.append(TopFrame(module=module, func=func, file=top_file, line=top_line))
        if len(frames) >= n:
            break
    if not frames:
        frames.append(TopFrame(module=None, func=None, file=None, line=None))
    return frames


def _load_process_salt(outdir: Path) -> str:
    """Build a salt using process python version + platform from MANIFEST if present.

    Falls back to current interpreter/platform when fields are missing.
    """
    py = None
    plat = None
    try:
        mf = outdir / "MANIFEST.json"
        if mf.exists():
            data = json.loads(mf.read_text(encoding="utf-8"))
            py = (data.get("python") or None) if isinstance(data, dict) else None
            plat = (data.get("platform") or None) if isinstance(data, dict) else None
    except Exception:
        py = None
        plat = None
    if not py or not plat:
        try:
            import platform as _platform
            import sys as _sys

            py = py or _sys.version.split(" ")[0]
            plat = plat or _platform.platform()
        except Exception:
            py = py or "unknown"
            plat = plat or "unknown"
    return f"py={py}|plat={plat}"


def _top_n_from_env() -> int:
    try:
        n = int(os.getenv("FAULT_TOP_FRAMES_N", str(DEFAULT_TOP_N)) or DEFAULT_TOP_N)
        return max(1, min(n, 100))
    except Exception:
        return DEFAULT_TOP_N


def _signature_id(frames: list[TopFrame], salt: str) -> str:
    # Normalize per-frame data to reduce path churn: use basename for file
    parts: list[str] = []
    for f in frames:
        file_base = None
        try:
            file_base = Path(f.file or "?").name
        except Exception:
            file_base = f.file or "?"
        parts.append(
            "::".join(
                [
                    f.module or "?",
                    f.func or "?",
                    file_base or "?",
                    str(f.line if f.line is not None else "?"),
                ]
            )
        )
    raw = f"{salt}|N={len(frames)}|" + "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _write_stacks_csv(outdir: Path, stacks_text: str) -> list[dict[str, object]]:
    # Aggregate by signature
    now_iso = datetime.now(UTC).isoformat(timespec="seconds")
    lines = stacks_text.splitlines()
    rows_map: dict[str, dict[str, object]] = {}
    salt = _load_process_salt(outdir)
    top_n = _top_n_from_env()
    for block in _iter_thread_blocks(lines):
        # Header is the first line; use as thread id text
        thread_id = block[0].strip() if block else "(unknown)"
        frames = _extract_top_frames(block, top_n)
        sig = _signature_id(frames, salt)
        # Top-of-stack frame for readability in CSV columns
        tf0 = frames[0]
        top_module = tf0.module or "?"
        top_func = tf0.func or "?"
        top_file = tf0.file or "?"
        top_line = tf0.line or 0
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
        # Merge thread id
        th_set = row["threads"]  # type: ignore[assignment]
        assert isinstance(th_set, set)
        th_set.add(thread_id)

    # Materialize threads as counts and stable list
    rows: list[dict[str, object]] = []
    for v in rows_map.values():
        th_set = v.pop("threads")  # type: ignore[assignment]
        try:
            threads_list = sorted(th_set)  # type: ignore[arg-type]
        except Exception:
            threads_list = []
        v["threads"] = ",".join(threads_list)
        rows.append(v)

    # Write CSV
    csv_path = outdir / "stacks.csv"
    try:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "signature_id",
                    "count",
                    "top_module",
                    "top_func",
                    "top_file",
                    "top_line",
                    "threads",
                    "first_seen_ts",
                    "last_seen_ts",
                ],
            )
            writer.writeheader()
            for r in sorted(rows, key=lambda x: (-int(x["count"]), str(x["signature_id"]))):
                writer.writerow(r)
    except Exception:
        pass
    return rows


def _write_summary(outdir: Path, rows: list[dict[str, object]], dumps_dir: Path) -> None:
    lines: list[str] = []
    lines.append("# Fault Diagnostics Summary")
    lines.append("")
    lines.append(f"Time: {datetime.now(UTC).isoformat(timespec='seconds')}")
    lines.append("")
    # Dumps info
    try:
        dump_files = sorted([p.name for p in dumps_dir.glob("*.txt")])
    except Exception:
        dump_files = []
    lines.append("## Dumps")
    lines.append("")
    if dump_files:
        for name in dump_files:
            lines.append(f"* {name}")
    else:
        lines.append("(none)")
    lines.append("")
    # Top signatures table (first 20)
    lines.append("## Top Signatures")
    lines.append("")
    lines.append("| count | signature_id | top | file:line | threads |")
    lines.append("|------:|--------------|-----|----------:|---------|")
    for r in rows[:20]:
        top = f"{r.get('top_module', '?')}.{r.get('top_func', '?')}"
        fileline = f"{r.get('top_file', '?')}:{r.get('top_line', 0)}"
        lines.append(
            f"| {r.get('count', 0)} | {r.get('signature_id', '?')} | {top} | {fileline} | {r.get('threads', '')} |"
        )
    lines.append("")
    try:
        (outdir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    log = logging.getLogger("fault_artifacts")

    ap = argparse.ArgumentParser(description="Generate fault artifacts for a run directory")
    ap.add_argument("--outdir", help="Run directory containing stacks.log", default=None)
    args = ap.parse_args(argv)

    outdir = _discover_outdir(args.outdir)
    if outdir is None or not outdir.exists() or not outdir.is_dir():
        log.info("No valid FAULT_OUTDIR or runs found; nothing to generate")
        return 0

    outdir.mkdir(parents=True, exist_ok=True)
    _ensure_manifest(outdir)

    stacks_path = outdir / "stacks.log"
    dumps_dir = outdir / "dumps"
    dumps_dir.mkdir(exist_ok=True)

    stacks_text = _read_text(stacks_path)
    # Always emit a combined dump file for convenience
    try:
        (dumps_dir / "combined.txt").write_text(stacks_text, encoding="utf-8")
    except Exception:
        pass

    # Write CSV aggregation and summary
    rows = _write_stacks_csv(outdir, stacks_text)
    _write_summary(outdir, rows, dumps_dir)
    log.info("Artifacts generated under: %s", outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
