"""
Generate structured fault artifacts for a faulthandler run directory.

This consumer processes raw faulthandler stack dumps and producer reports
to emit HOP-compliant HealthView artifacts for downstream summarization.

Output Path Contract (HOP)
--------------------------
``.repo_studios/reports/healthview/consumer_reports/fault_artifacts/<YYYYMMDD-HHMM>/``

Base Package
------------
- ``manifest.json`` — bundle metadata and artifact registry
- ``summary.md`` — human-readable digest
- ``telemetry.json`` — machine-readable metrics and signatures

Rawview Artifacts (within run_dir)
----------------------------------
- ``MANIFEST.json`` — best-effort run manifest
- ``dumps/combined.txt`` — raw copy of stacks.log
- ``stacks.csv`` — parsed signature table

CSV Schema
----------
``signature_id,count,top_module,top_func,top_file,top_line,threads,first_seen_ts,last_seen_ts``

CLI Arguments
-------------
--outdir
    Run directory containing stacks.log. Defaults to latest under
    ``.repo_studios/command_center/reports/rawview/fault_diagnostics_runs/``.
--report
    Explicit producer report JSON to reuse (skips fresh scan).
--output-dir
    Consumer output root. Defaults to HOP path.
--artifacts-to-keep
    Retention budget for timestamped bundles.

Environment Variables
---------------------
FAULT_OUTDIR
    Alternative to ``--outdir`` CLI argument.
FAULT_TOP_FRAMES_N
    Override frame depth for signature extraction (default: 10).

Notes
-----
- Parser is best-effort against stdlib faulthandler format.
- Timestamps default to current UTC when unavailable.
- No pointer files (``latest_*``) are emitted per HOP contract.

.. seealso::
    :doc:`REPORT_NAMING_STANDARDS` for HOP path contract.
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
from typing import Any, Sequence, cast

REPO_ROOT = Path(__file__).resolve().parents[3]
COMMAND_CENTER_SCRIPTS_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"
if str(COMMAND_CENTER_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMAND_CENTER_SCRIPTS_ROOT))

from libraries import prune_run_directories  # noqa: E402
from libraries.cli import resolve_repo_root  # noqa: E402
from libraries.retention_policy import get_keep  # noqa: E402
from libraries.report_paths import build_topic_path  # noqa: E402

RAWVIEW_RUNS_BASE = build_topic_path("rawview", "fault_diagnostics")
LEGACY_RUNS_BASE = Path(".repo_studios/faulthandler")
TOPIC_SLUG = "fault_artifacts"
DEFAULT_OUTPUT_DIR = build_topic_path("consumer", TOPIC_SLUG)
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("generate_fault_artifacts")

# HOP artifact names (REPORT_NAMING_STANDARDS.md)
MANIFEST_NAME = "manifest.json"
SUMMARY_NAME = "summary.md"
TELEMETRY_NAME = "telemetry.json"
SCHEMA_VERSION = 1

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
scripts_root_str = str(SCRIPTS_ROOT)
if scripts_root_str and scripts_root_str in sys.path:
    sys.path.remove(scripts_root_str)
if scripts_root_str:
    sys.path.insert(0, scripts_root_str)

from utilities.fault_run_analysis import (  # noqa: E402
    DEFAULT_TOP_N,
    FaultSignature,
    build_fault_report,
    ensure_manifest,
    read_stacks_text,
)


def _timestamp_slug() -> str:
    """Generate HOP-compliant timestamp slug.

    Returns:
        UTC timestamp in YYYYMMDD-HHMM format (13 characters).
    """
    return datetime.now(UTC).strftime("%Y%m%d-%H%M")


def _allow_legacy_runs() -> bool:
    """Check if legacy faulthandler run paths are permitted.

    Returns:
        True if FAULT_LOGS_ALLOW_LEGACY env var is not disabled.
    """
    flag = os.getenv("FAULT_LOGS_ALLOW_LEGACY", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def _resolve_runs_base(logger: logging.Logger | None) -> Path:
    """Resolve faulthandler runs base directory using repo root.

    Args:
        logger: Logger for fallback notices.

    Returns:
        Resolved runs base path.
    """
    return _resolve_runs_base_for_repo(REPO_ROOT, logger)


def _resolve_runs_base_for_repo(repo_root: Path, logger: logging.Logger | None) -> Path:
    """Resolve faulthandler runs base directory with legacy fallback.

    Args:
        repo_root: Repository root path.
        logger: Logger for fallback notices.

    Returns:
        Rawview runs base or legacy fallback path.
    """
    rawview_runs_base = (repo_root / RAWVIEW_RUNS_BASE).resolve()
    legacy_runs_base = (repo_root / LEGACY_RUNS_BASE).resolve()
    if rawview_runs_base.exists():
        return rawview_runs_base
    if _allow_legacy_runs() and legacy_runs_base.exists():
        if logger is not None:
            logger.info(
                "Faulthandler rawview runs directory %s missing; falling back to legacy %s",
                rawview_runs_base,
                legacy_runs_base,
            )
        return legacy_runs_base
    return rawview_runs_base


def _find_latest_outdir(runs_base: Path) -> Path | None:
    """Find most recent run directory by mtime.

    Args:
        runs_base: Base directory containing run subdirectories.

    Returns:
        Path to latest run directory or None.
    """
    try:
        if not runs_base.exists():
            return None
        candidates = [p for p in runs_base.iterdir() if p.is_dir()]
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0] if candidates else None
    except Exception:
        return None


def _discover_outdir(explicit: str | None, runs_base: Path) -> Path | None:
    """Discover run directory from explicit arg, env, or latest scan.

    Args:
        explicit: Explicit outdir path from CLI.
        runs_base: Base directory for run discovery.

    Returns:
        Resolved run directory or None.
    """
    if explicit:
        return Path(explicit)
    env = os.getenv("FAULT_OUTDIR")
    if env:
        return Path(env)
    return _find_latest_outdir(runs_base)


def _is_compatible_producer_report(payload: dict[str, Any]) -> bool:
    """Check if payload matches the legacy producer report schema.

    Args:
        payload: JSON payload to validate.

    Returns:
        True when payload looks like the legacy producer report schema.
    """
    summary = payload.get("summary")
    signatures = payload.get("signatures")
    return isinstance(summary, dict) and isinstance(signatures, list)


def _load_json(path: Path) -> dict[str, Any] | None:
    """Load JSON file into dict or return None on failure.

    Args:
        path: Path to JSON file.

    Returns:
        Parsed dict or None if loading fails or payload is not a dict.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return cast(dict[str, Any], payload)
        return None
    except Exception:
        return None


def _load_producer_report(explicit: Path | None, *, run_dir: Path | None) -> tuple[dict[str, Any] | None, Path | None]:
    """Load producer report if explicitly provided.

    Args:
        explicit: Explicit producer report path.
        run_dir: Run directory for context (unused but reserved).

    Returns:
        Tuple of (payload dict, resolved path) or (None, None) if not found
        or incompatible.
    """
    if explicit is not None:
        payload = _load_json(explicit)
        if payload is not None and _is_compatible_producer_report(payload):
            return payload, explicit.resolve()
        return None, None
    return None, None


def _top_n_from_env() -> int:
    """Get top frame count from FAULT_TOP_FRAMES_N env var.

    Returns:
        Frame count clamped to [1, 100].
    """
    try:
        n = int(os.getenv("FAULT_TOP_FRAMES_N", str(DEFAULT_TOP_N)) or DEFAULT_TOP_N)
        return max(1, min(n, 100))
    except Exception:
        return DEFAULT_TOP_N


def _decode_signatures(payload: dict[str, Any], *, default_top_line: int = 0) -> list[FaultSignature]:
    """Decode signatures list from producer report payload.

    Args:
        payload: Producer report dict containing 'signatures' key.
        default_top_line: Default line number if missing.

    Returns:
        List of FaultSignature objects sorted by count descending.
    """
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
    """Write signatures to CSV file in run directory.

    Args:
        outdir: Run directory for output.
        signatures: Fault signatures to serialize.
    """
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
    """Write run-level SUMMARY.md and return content.

    Args:
        outdir: Run directory for output.
        report: Fault analysis report dict.
        signatures: Fault signatures for table.
        dumps_dir: Directory containing dump files.

    Returns:
        Generated Markdown content.
    """
    lines: list[str] = []
    lines.append("# Fault Diagnostics Summary")
    lines.append("")
    lines.append(f"Generated (UTC): {datetime.now(UTC).isoformat(timespec='seconds')}")
    lines.append("")
    summary = report.get("summary") or {}
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- signature_count: {summary.get('signature_count', len(signatures))}")
    lines.append(f"- active_signature_count: {summary.get('active_signature_count')}")
    lines.append(f"- thread_block_count: {summary.get('thread_block_count')}")
    lines.append(f"- top_frame_limit: {summary.get('top_frame_limit', DEFAULT_TOP_N)}")
    lines.append(f"- stack_log_exists: {summary.get('stack_log_exists')}")
    lines.append(f"- stack_text_bytes: {summary.get('stack_text_bytes')}")
    lines.append(f"- first_seen_utc: {summary.get('first_seen_utc')}")
    lines.append(f"- last_seen_utc: {summary.get('last_seen_utc')}")
    lines.append("")
    severity = summary.get("severity_buckets") if isinstance(summary, dict) else None
    if isinstance(severity, dict):
        lines.append("## Severity Buckets")
        lines.append("")
        lines.append(f"- repeat_offender: {severity.get('repeat_offender')}")
        lines.append(f"- multi_hit: {severity.get('multi_hit')}")
        lines.append(f"- single_hit: {severity.get('single_hit')}")
        lines.append("")
    lines.append("## Dumps")
    lines.append("")
    try:
        dump_files = sorted(p.name for p in dumps_dir.glob("*.txt"))
    except Exception:
        dump_files = []
    if dump_files:
        for name in dump_files:
            lines.append(f"- {name}")
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
    """Convert FaultSignature objects to serializable dicts.

    Args:
        signatures: Fault signatures to serialize.

    Returns:
        List of signature dictionaries.
    """
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
    ts_slug: str,
) -> dict[str, Path]:
    """Write HOP-compliant consumer bundle to timestamped directory.

    Args:
        target_root: Base output directory for consumer bundles.
        run_dir: Source rawview run directory.
        report: Parsed fault report payload.
        signatures: Extracted fault signatures.
        summary_text: Pre-rendered summary markdown.
        source: Data source label (``"producer"`` or ``"scan"``).
        source_report: Path to producer report if used.
        ts_slug: HOP timestamp slug (``YYYYMMDD-HHMM``).

    Returns:
        Mapping of artifact names to paths.

    Note:
        Output structure::

            <target_root>/<ts_slug>/
                manifest.json
                summary.md
                telemetry.json
    """
    generated_at = datetime.now(UTC)
    target_root.mkdir(parents=True, exist_ok=True)
    bundle_dir = target_root / ts_slug
    bundle_dir.mkdir(parents=True, exist_ok=True)

    run_summary_path = (run_dir / "SUMMARY.md").resolve()
    stacks_csv_path = (run_dir / "stacks.csv").resolve()
    combined_txt_path = (run_dir / "dumps" / "combined.txt").resolve()

    source_report_path = source_report.resolve() if source_report else None

    # Build rawview artifact references
    rawview_artifacts = {
        "run_summary_md": str(run_summary_path) if run_summary_path.exists() else None,
        "stacks_csv": str(stacks_csv_path) if stacks_csv_path.exists() else None,
        "combined_txt": str(combined_txt_path) if combined_txt_path.exists() else None,
    }

    # Build telemetry.json (machine-readable metrics and signatures)
    telemetry_payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "source": source,
        "source_report": str(source_report_path) if source_report_path else None,
        "run_dir": str(run_dir.resolve()),
        "summary": report.get("summary") if isinstance(report, dict) else None,
        "signatures": _serialize_signatures(signatures),
        "rawview_artifacts": rawview_artifacts,
    }
    telemetry_path = bundle_dir / TELEMETRY_NAME
    telemetry_path.write_text(json.dumps(telemetry_payload, indent=2) + "\n", encoding="utf-8")

    # Build summary.md (human-readable digest)
    base_lines = summary_text.rstrip("\n").splitlines()
    base_lines.append("")
    base_lines.append("<!-- markdownlint-disable-next-line MD013 -->")
    base_lines.append("## Source References")
    base_lines.append("")
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
    summary_path = bundle_dir / SUMMARY_NAME
    summary_path.write_text(consumer_summary, encoding="utf-8")

    # Build manifest.json (bundle metadata and artifact registry)
    summary_data = telemetry_payload.get("summary") if isinstance(telemetry_payload, dict) else None
    severity = summary_data.get("severity_buckets") if isinstance(summary_data, dict) else {}
    manifest_payload = {
        "schema_version": SCHEMA_VERSION,
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "source": source,
        "run_dir": str(run_dir.resolve()),
        "metrics": {
            "signature_count": summary_data.get("signature_count") if isinstance(summary_data, dict) else None,
            "active_signature_count": summary_data.get("active_signature_count") if isinstance(summary_data, dict) else None,
            "repeat_offender": severity.get("repeat_offender") if isinstance(severity, dict) else None,
            "multi_hit": severity.get("multi_hit") if isinstance(severity, dict) else None,
            "single_hit": severity.get("single_hit") if isinstance(severity, dict) else None,
            "thread_block_count": summary_data.get("thread_block_count") if isinstance(summary_data, dict) else None,
        },
        "artifacts": {
            "telemetry": TELEMETRY_NAME,
            "summary": SUMMARY_NAME,
        },
        "source_report": str(source_report_path) if source_report_path else None,
    }
    manifest_path = bundle_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")

    return {
        "bundle_dir": bundle_dir,
        "manifest": manifest_path,
        "telemetry": telemetry_path,
        "summary": summary_path,
    }


def _prune_history(root: Path, keep: int | None, current: Path, *, logger: logging.Logger | None) -> list[Path]:
    """Prune old bundle directories to enforce retention budget.

    Args:
        root: Base directory containing timestamped bundles.
        keep: Number of bundles to retain.
        current: Current run directory (excluded from pruning).
        logger: Logger instance for debug output.

    Returns:
        List of removed directory paths.
    """
    if keep is None:
        return []
    try:
        keep_count = int(keep)
    except Exception:
        keep_count = DEFAULT_ARTIFACTS_TO_KEEP
    if keep_count < 0:
        keep_count = DEFAULT_ARTIFACTS_TO_KEEP
    keep_count = max(keep_count, 1)
    result = prune_run_directories(
        root,
        keep=keep_count,
        stem_prefix="",  # HOP uses bare timestamp directories
        current_run=current,
        logger=logger,
    )
    return result.removed


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse command-line arguments for fault artifact generation.

    Args:
        argv: Command-line arguments; defaults to sys.argv[1:].

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(description="Generate fault artifacts for a run directory")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--outdir",
        default=None,
        help=(
            "Run directory containing stacks.log (defaults to latest under "
            ".repo_studios/command_center/reports/rawview/fault_diagnostics_runs)"
        ),
    )
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
        help="Consumer output root (defaults to .repo_studios/reports/healthview/consumer_reports/fault_artifacts)",
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
    """Execute fault artifact generation pipeline.

    Process rawview run directory, decode signatures, and write
    HOP-compliant consumer artifacts.

    Args:
        argv: Command-line arguments; defaults to sys.argv[1:].

    Returns:
        Execution result with outdir, source, signatures count, etc.

    Note:
        Output is written to
        ``.repo_studios/reports/healthview/consumer_reports/fault_artifacts/<YYYYMMDD-HHMM>/``.
    """
    args = _parse_args(argv)
    log_level = getattr(logging, str(args.log_level).upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s", force=True)
    log = logging.getLogger("fault_artifacts")

    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))
    runs_base = _resolve_runs_base_for_repo(repo_root, log)
    outdir = _discover_outdir(args.outdir, runs_base)
    if outdir is None or not outdir.exists() or not outdir.is_dir():
        log.info("No valid FAULT_OUTDIR or runs found; nothing to generate")
        return {"outdir": None, "source_report": None, "signatures": 0}

    outdir = (repo_root / outdir).resolve() if not outdir.is_absolute() else outdir.resolve()
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

    raw_target_root = Path(args.output_dir) if args.output_dir is not None else DEFAULT_OUTPUT_DIR
    target_root = raw_target_root if raw_target_root.is_absolute() else (repo_root / raw_target_root).resolve()

    ts_slug = _timestamp_slug()
    artifact_paths = _write_consumer_bundle(
        target_root=target_root,
        run_dir=outdir,
        report=report,
        signatures=signatures,
        summary_text=summary_text,
        source=source_label,
        source_report=source_path,
        ts_slug=ts_slug,
    )
    bundle_dir = artifact_paths["bundle_dir"]
    pruned = _prune_history(target_root, args.artifacts_to_keep, bundle_dir, logger=log)

    source_report_log = str(source_path) if source_path else "scan"
    severity = report.get("summary", {}).get("severity_buckets", {}) if isinstance(report, dict) else {}
    repeat_offender = int(severity.get("repeat_offender", 0)) if isinstance(severity, dict) else 0
    log.info(
        "Fault artifacts refreshed (run=%s, source=%s, report=%s, signatures=%d, repeat_offender=%d, consumer=%s, pruned=%d)",
        outdir,
        source_label,
        source_report_log,
        len(signatures),
        repeat_offender,
        bundle_dir,
        len(pruned),
    )

    return {
        "outdir": str(outdir.resolve()),
        "source": source_label,
        "source_report": str(source_path) if source_path else None,
        "consumer_report": str(bundle_dir.resolve()),
        "artifacts_root": str(target_root.resolve()),
        "signatures": len(signatures),
        "manifest": str(artifact_paths["manifest"].resolve()),
        "repeat_offender_signatures": repeat_offender,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for fault artifact generation.

    Args:
        argv: Command-line arguments; defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success).
    """
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
