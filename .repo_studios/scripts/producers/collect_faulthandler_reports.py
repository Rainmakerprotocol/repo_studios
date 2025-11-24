#!/usr/bin/env python3
"""Collect structured summaries for faulthandler runs.

This producer converts raw faulthandler run directories into timestamped
artifacts under `.repo_studios/reports/producer_reports/faulthandler_reports/`.
It emits JSON and Markdown summaries alongside the aggregated signature CSV so
consumers can reuse the data without re-parsing the original stacks.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from utilities.fault_run_analysis import FaultAnalysisResult, FaultSignature, build_fault_report  # noqa: E402

DEFAULT_RUNS_BASE = Path(".repo_studios/faulthandler")
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/faulthandler_reports")
RUN_PREFIX = "faulthandler_report"
DEFAULT_KEEP = 10


def _find_latest_run(runs_base: Path) -> Path | None:
    try:
        candidates = [p for p in runs_base.iterdir() if p.is_dir()]
    except FileNotFoundError:
        return None
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _resolve_run_dir(explicit: Path | None, runs_base: Path) -> Path | None:
    if explicit is not None:
        return explicit
    return _find_latest_run(runs_base)


def _format_run_dir(ts: datetime) -> str:
    return f"{RUN_PREFIX}-{ts.strftime('%Y%m%d_%H%M%S')}"


def _render_markdown(report: dict[str, object], signatures: Sequence[FaultSignature]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines: list[str] = []
    lines.append("# Faulthandler Report Summary")
    lines.append("")
    lines.append(f"Generated (UTC): {report.get('generated_utc', 'unknown')}")
    lines.append(f"Source Run Dir: {report.get('run_dir', 'unknown')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- signature_count: {summary.get('signature_count', len(signatures))}")
    lines.append(f"- thread_block_count: {summary.get('thread_block_count')}")
    lines.append(f"- top_frame_limit: {summary.get('top_frame_limit')}")
    lines.append(f"- stack_log_exists: {summary.get('stack_log_exists')}")
    lines.append(f"- stack_text_bytes: {summary.get('stack_text_bytes')}")
    lines.append("")
    lines.append("## Top Signatures (up to 25)")
    lines.append("")
    if signatures:
        lines.append("| count | signature_id | top | file:line | threads |")
        lines.append("|------:|--------------|-----|----------:|---------|")
        for sig in signatures[:25]:
            top = f"{sig.top_module}.{sig.top_func}"
            fileline = f"{sig.top_file}:{sig.top_line}"
            thread_list = ",".join(sig.threads)
            lines.append(f"| {sig.count} | {sig.signature_id} | {top} | {fileline} | {thread_list} |")
    else:
        lines.append("(none)")
    lines.append("")
    return "\n".join(lines) + "\n"


def _write_csv(run_dir: Path, signatures: Sequence[FaultSignature]) -> None:
    csv_path = run_dir / "stacks.csv"
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


def _write_log(run_dir: Path, report: dict[str, object], signatures: Sequence[FaultSignature]) -> None:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"generated_utc={report.get('generated_utc')}",
        f"run_dir={report.get('run_dir')}",
        f"signatures={len(signatures)}",
        f"thread_block_count={summary.get('thread_block_count')}",
        f"stack_text_bytes={summary.get('stack_text_bytes')}",
    ]
    try:
        (run_dir / "log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        pass


def _update_latest(output_dir: Path, run_dir: Path) -> None:
    latest_pairs = {
        "report.json": output_dir / "latest_report.json",
        "report.md": output_dir / "latest_report.md",
        "stacks.csv": output_dir / "latest_stacks.csv",
        "combined.txt": output_dir / "latest_combined.txt",
    }
    for name, dest in latest_pairs.items():
        src = run_dir / name
        if not src.exists():
            continue
        try:
            if dest.exists():
                dest.unlink()
            dest.hardlink_to(src)
        except Exception:
            dest.write_bytes(src.read_bytes())


def _prune_old_runs(output_dir: Path, keep: int, current_run: Path) -> list[Path]:
    keep = max(1, keep)
    removed: list[Path] = []
    if not output_dir.exists():
        return removed
    candidates = [child for child in output_dir.iterdir() if child.is_dir() and child.name.startswith(RUN_PREFIX)]
    candidates.sort(key=lambda p: p.name, reverse=True)
    for idx, path in enumerate(candidates):
        if idx < keep or path == current_run:
            continue
        try:
            for blob in path.glob("*"):
                if blob.is_file():
                    blob.unlink()
            path.rmdir()
            removed.append(path)
        except Exception:
            continue
    return removed


def _write_artifacts(result: FaultAnalysisResult, output_dir: Path, *, keep: int) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = result.report.get("generated_utc")
    try:
        ts = datetime.fromisoformat(str(generated))
    except Exception:
        ts = datetime.now(UTC)
    run_dir = output_dir / _format_run_dir(ts)
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "report.json").write_text(json.dumps(result.report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "report.md").write_text(_render_markdown(result.report, result.signatures), encoding="utf-8")
    _write_csv(run_dir, result.signatures)
    try:
        (run_dir / "combined.txt").write_text(result.combined_text, encoding="utf-8")
    except Exception:
        pass
    _write_log(run_dir, result.report, result.signatures)
    _update_latest(output_dir, run_dir)
    _prune_old_runs(output_dir, keep, run_dir)
    return run_dir


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect faulthandler reports into structured artifacts")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_BASE)
    parser.add_argument("--run-dir", type=Path, default=None, help="Explicit faulthandler run directory")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_KEEP)
    parser.add_argument("--top-frames", type=int, default=None, help="Override top frame capture limit")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s %(message)s"
    )
    log = logging.getLogger("faulthandler_report")

    runs_base = args.runs_dir.resolve()
    run_dir = _resolve_run_dir(args.run_dir.resolve() if args.run_dir else None, runs_base)
    if run_dir is None or not run_dir.exists():
        log.info("No faulthandler runs available under %s", runs_base)
        return {"run_dir": None, "artifacts": None}

    top_frames = args.top_frames if args.top_frames is not None else None
    result = (
        build_fault_report(run_dir.resolve(), top_n=top_frames) if top_frames else build_fault_report(run_dir.resolve())
    )
    output_dir = args.output_dir.resolve()
    run_artifacts = _write_artifacts(result, output_dir, keep=args.artifacts_to_keep)

    log.info(
        "Faulthandler report captured (run_dir=%s, signatures=%d, output=%s)",
        run_dir,
        len(result.signatures),
        run_artifacts,
    )
    return {
        "run_dir": str(run_dir.resolve()),
        "output_dir": str(run_artifacts),
        "signatures": len(result.signatures),
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
