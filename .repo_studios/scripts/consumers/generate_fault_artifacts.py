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
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
RUNS_BASE = ROOT / ".repo_studios/faulthandler"
PRODUCER_BASE = ROOT / ".repo_studios/reports/producer_reports/faulthandler_reports"
PRODUCER_LATEST = PRODUCER_BASE / "latest_report.json"
CONSUMER_BASE = ROOT / ".repo_studios/reports/consumer_reports/fault_artifacts"
CONSUMER_DIR_PREFIX = "fault_artifacts-"
DEFAULT_ARTIFACTS_TO_KEEP = 10

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


def _write_summary(outdir: Path, report: dict[str, Any], signatures: Sequence[FaultSignature], dumps_dir: Path) -> str:
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
    content = "\n".join(lines) + "\n"
    try:
        (outdir / "SUMMARY.md").write_text(content, encoding="utf-8")
    except Exception:
        pass
    return content


def _serialize_signatures(signatures: Sequence[FaultSignature]) -> list[dict[str, Any]]:
    return [
        {
            "signature_id": sig.signature_id,
            "count": sig.count,
            "top_module": sig.top_module,
            "top_func": sig.top_func,
            "top_file": sig.top_file,
            "top_line": sig.top_line,
            "threads": list(sig.threads),
            "first_seen_ts": sig.first_seen_ts,
            "last_seen_ts": sig.last_seen_ts,
        }
        for sig in signatures
    ]


def _write_consumer_bundle(
    *,
    target_root: Path,
    run_dir: Path,
    report: dict[str, Any],
    signatures: Sequence[FaultSignature],
    summary_text: str,
    source: str,
    source_report: Path | None,
) -> Path:
    generated_at = datetime.now(UTC)
    target_root.mkdir(parents=True, exist_ok=True)
    slug = run_dir.name
    bundle_name = f"{CONSUMER_DIR_PREFIX}{generated_at.strftime('%Y-%m-%d_%H%M%S')}-{slug}"
    bundle_dir = target_root / bundle_name
    bundle_dir.mkdir(parents=True, exist_ok=True)

    run_summary_path = (run_dir / "SUMMARY.md").resolve()
    stacks_csv_path = (run_dir / "stacks.csv").resolve()
    combined_txt_path = (run_dir / "dumps" / "combined.txt").resolve()

    source_report_path = source_report.resolve() if source_report else None

    summary_payload = {
        "schema_version": 1,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "source": source,
        "source_report": str(source_report_path) if source_report_path else None,
        "run_dir": str(run_dir.resolve()),
        "summary": report.get("summary") if isinstance(report, dict) else None,
        "signatures": _serialize_signatures(signatures),
        "artifacts": {
            "run_summary_md": str(run_summary_path) if run_summary_path.exists() else None,
            "stacks_csv": str(stacks_csv_path) if stacks_csv_path.exists() else None,
            "combined_txt": str(combined_txt_path) if combined_txt_path.exists() else None,
        },
    }

    (bundle_dir / "summary.json").write_text(json.dumps(summary_payload, indent=2) + "\n", encoding="utf-8")

    base_lines = summary_text.rstrip("\n").splitlines()
    base_lines.append("")
    base_lines.append("## Source References")
    base_lines.append(f"- Run Directory: `{run_dir.resolve()}`")
    base_lines.append(f"- Source Type: {source}")
    if source_report_path:
        base_lines.append(f"- Producer Report: `{source_report_path}`")
    if run_summary_path.exists():
        base_lines.append(f"- Run Summary: `{run_summary_path}`")
    if stacks_csv_path.exists():
        base_lines.append(f"- Stacks CSV: `{stacks_csv_path}`")
    if combined_txt_path.exists():
        base_lines.append(f"- Combined Stack Text: `{combined_txt_path}`")
    consumer_summary = "\n".join(base_lines) + "\n"
    (bundle_dir / "SUMMARY.md").write_text(consumer_summary, encoding="utf-8")
    return bundle_dir


def _prune_history(root: Path, keep: int | None, current: Path) -> list[Path]:
    if keep is None:
        return []
    try:
        keep_count = max(int(keep), 0)
    except Exception:
        keep_count = DEFAULT_ARTIFACTS_TO_KEEP
    if not root.exists():
        return []
    candidates = sorted(
        [
            path
            for path in root.iterdir()
            if path.is_dir() and path.name.startswith(CONSUMER_DIR_PREFIX) and path != current
        ],
        key=lambda p: p.name,
        reverse=True,
    )
    limit = max(keep_count - 1, 0)
    stale = candidates[limit:]
    for path in stale:
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            continue
    return stale


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate fault artifacts for a run directory")
    parser.add_argument("--outdir", default=None, help="Run directory containing stacks.log (defaults to latest)")
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Explicit faulthandler producer report JSON to reuse",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to store consumer summaries (defaults to .repo_studios/reports/consumer_reports/fault_artifacts)",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of consumer summary directories to retain (including the newest run)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging verbosity (e.g. INFO, DEBUG)",
    )
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    log_level = getattr(logging, str(args.log_level).upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s", force=True)
    log = logging.getLogger("fault_artifacts")

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
        source_label = "producer"
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
    summary_text = _write_summary(outdir, report, signatures, dumps_dir)

    target_root = args.output_dir if args.output_dir is not None else CONSUMER_BASE
    target_root = Path(target_root)
    consumer_dir = _write_consumer_bundle(
        target_root=target_root,
        run_dir=outdir,
        report=report,
        signatures=signatures,
        summary_text=summary_text,
        source=source_label,
        source_report=source_path,
    )
    pruned = _prune_history(target_root, args.artifacts_to_keep, consumer_dir)

    source_report_log = str(source_path) if source_path else "scan"
    log.info(
        "Fault artifacts refreshed (run=%s, source=%s, report=%s, signatures=%d, consumer=%s, pruned=%d)",
        outdir,
        source_label,
        source_report_log,
        len(signatures),
        consumer_dir,
        len(pruned),
    )

    return {
        "outdir": str(outdir.resolve()),
        "source": source_label,
        "source_report": str(source_path) if source_path else None,
        "consumer_report": str(consumer_dir.resolve()),
        "artifacts_root": str(target_root.resolve()),
        "signatures": len(signatures),
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
