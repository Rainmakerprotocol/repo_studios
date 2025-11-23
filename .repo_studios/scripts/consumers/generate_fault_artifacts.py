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
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
RUNS_BASE = ROOT / ".repo_studios/faulthandler"
PRODUCER_BASE = ROOT / ".repo_studios/reports/producer_reports/faulthandler_reports"
PRODUCER_LATEST = PRODUCER_BASE / "latest_report.json"

UTILITIES_ROOT = Path(__file__).resolve().parents[2]
if str(UTILITIES_ROOT) not in sys.path:
    sys.path.insert(0, str(UTILITIES_ROOT))

from utilities.fault_run_analysis import (  # noqa: E402
    DEFAULT_TOP_N,
    FaultSignature,
    build_fault_report,
    ensure_manifest,
    read_stacks_text,
)


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


def _iter_producer_reports(base_dir: Path) -> list[Path]:
    if not base_dir.exists():
        return []
    candidates: list[Path] = []
    for child in base_dir.iterdir():
        if not child.is_dir():
            continue
        if not child.name.startswith("faulthandler_report-"):
            continue
        candidate = child / "report.json"
        if candidate.exists():
            candidates.append(candidate)
    candidates.sort(key=lambda p: p.parent.name, reverse=True)
    return candidates


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_producer_report(explicit: Path | None, *, run_dir: Path | None) -> tuple[dict[str, Any] | None, Path | None]:
    if explicit is not None:
        payload = _load_json(explicit)
        if payload is not None:
            return payload, explicit.resolve()
        return None, None
    target_run = run_dir.resolve() if run_dir else None
    if PRODUCER_LATEST.exists():
        payload = _load_json(PRODUCER_LATEST)
        if payload is not None:
            run_path = payload.get("run_dir")
            if target_run is None:
                return payload, PRODUCER_LATEST.resolve()
            if run_path and Path(run_path).resolve() == target_run:
                return payload, PRODUCER_LATEST.resolve()
    for candidate in _iter_producer_reports(PRODUCER_BASE):
        payload = _load_json(candidate)
        if payload is None:
            continue
        run_path = payload.get("run_dir")
        if target_run is None or (run_path and Path(run_path).resolve() == target_run):
            return payload, candidate.resolve()
    return None, None


def _top_n_from_env() -> int:
    try:
        n = int(os.getenv("FAULT_TOP_FRAMES_N", str(DEFAULT_TOP_N)) or DEFAULT_TOP_N)
        return max(1, min(n, 100))
    except Exception:
        return DEFAULT_TOP_N


def _decode_signatures(payload: dict[str, Any], *, default_top_line: int = 0) -> list[FaultSignature]:
    signatures: list[FaultSignature] = []
    for entry in payload.get("signatures", []):
        try:
            raw_line = entry.get("top_line", default_top_line)
            try:
                top_line = int(raw_line)
            except Exception:
                top_line = default_top_line
            threads_raw = entry.get("threads", [])
            if isinstance(threads_raw, (list, tuple)):
                threads = [str(t) for t in threads_raw]
            elif isinstance(threads_raw, str):
                threads = [t for t in threads_raw.split(",") if t]
            else:
                threads = []
            signatures.append(
                FaultSignature(
                    signature_id=str(entry.get("signature_id", "")),
                    count=int(entry.get("count", 0)),
                    top_module=str(entry.get("top_module", "?")),
                    top_func=str(entry.get("top_func", "?")),
                    top_file=str(entry.get("top_file", "?")),
                    top_line=top_line,
                    threads=threads,
                    first_seen_ts=str(entry.get("first_seen_ts", "")),
                    last_seen_ts=str(entry.get("last_seen_ts", "")),
                )
            )
        except Exception:
            continue
    signatures.sort(key=lambda sig: (-sig.count, sig.signature_id))
    return signatures


def _write_stacks_csv(outdir: Path, signatures: Sequence[FaultSignature]) -> None:
    csv_path = outdir / "stacks.csv"
    try:
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
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
            for sig in signatures:
                writer.writerow(
                    {
                        "signature_id": sig.signature_id,
                        "count": sig.count,
                        "top_module": sig.top_module,
                        "top_func": sig.top_func,
                        "top_file": sig.top_file,
                        "top_line": sig.top_line,
                        "threads": ",".join(sig.threads),
                        "first_seen_ts": sig.first_seen_ts,
                        "last_seen_ts": sig.last_seen_ts,
                    }
                )
    except Exception:
        pass


def _write_summary(outdir: Path, report: dict[str, Any], signatures: Sequence[FaultSignature], dumps_dir: Path) -> None:
    lines: list[str] = []
    lines.append("# Fault Diagnostics Summary")
    lines.append("")
    lines.append(f"Generated (UTC): {datetime.now(UTC).isoformat(timespec='seconds')}")
    lines.append("")
    summary = report.get("summary") or {}
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- signature_count: {summary.get('signature_count', len(signatures))}")
    lines.append(f"- thread_block_count: {summary.get('thread_block_count')}")
    lines.append(f"- top_frame_limit: {summary.get('top_frame_limit', DEFAULT_TOP_N)}")
    lines.append(f"- stack_log_exists: {summary.get('stack_log_exists')}")
    lines.append(f"- stack_text_bytes: {summary.get('stack_text_bytes')}")
    lines.append("")
    lines.append("## Dumps")
    lines.append("")
    try:
        dump_files = sorted(p.name for p in dumps_dir.glob("*.txt"))
    except Exception:
        dump_files = []
    if dump_files:
        for name in dump_files:
            lines.append(f"* {name}")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Top Signatures")
    lines.append("")
    if signatures:
        lines.append("| count | signature_id | top | file:line | threads |")
        lines.append("|------:|--------------|-----|----------:|---------|")
        for sig in signatures[:20]:
            top = f"{sig.top_module}.{sig.top_func}"
            fileline = f"{sig.top_file}:{sig.top_line}"
            lines.append(f"| {sig.count} | {sig.signature_id} | {top} | {fileline} | {','.join(sig.threads)} |")
    else:
        lines.append("(none)")
    lines.append("")
    try:
        (outdir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate fault artifacts for a run directory")
    parser.add_argument("--outdir", default=None, help="Run directory containing stacks.log (defaults to latest)")
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Explicit faulthandler producer report JSON to reuse",
    )
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    log = logging.getLogger("fault_artifacts")

    args = _parse_args(argv)
    outdir = _discover_outdir(args.outdir)
    if outdir is None or not outdir.exists() or not outdir.is_dir():
        log.info("No valid FAULT_OUTDIR or runs found; nothing to generate")
        return {"outdir": None, "source_report": None, "signatures": 0}

    outdir = outdir.resolve()
    ensure_manifest(outdir)

    payload, payload_path = _load_producer_report(args.report, run_dir=outdir)

    if payload:
        summary = payload.get("summary") or {}
        top_frame_limit = summary.get("top_frame_limit")
        default_line = int(top_frame_limit) if isinstance(top_frame_limit, int) else 0
        signatures = _decode_signatures(payload, default_top_line=default_line)
        report = payload
        combined_text = read_stacks_text(outdir / "stacks.log")
        source_path = payload_path.resolve() if payload_path else None
        source_label = str(source_path) if source_path else "producer"
    else:
        top_n = _top_n_from_env()
        analysis = build_fault_report(outdir, top_n=top_n)
        report = analysis.report
        signatures = analysis.signatures
        combined_text = analysis.combined_text
        source_path = None
        source_label = "scan"

    dumps_dir = outdir / "dumps"
    dumps_dir.mkdir(parents=True, exist_ok=True)

    if not combined_text:
        combined_text = read_stacks_text(outdir / "stacks.log")
    try:
        (dumps_dir / "combined.txt").write_text(combined_text, encoding="utf-8")
    except Exception:
        pass

    _write_stacks_csv(outdir, signatures)
    _write_summary(outdir, report, signatures, dumps_dir)

    log.info(
        "Fault artifacts refreshed (run=%s, source=%s, signatures=%d)",
        outdir,
        source_label,
        len(signatures),
    )

    return {
        "outdir": str(outdir),
        "source_report": str(source_path) if source_path else None,
        "signatures": len(signatures),
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
