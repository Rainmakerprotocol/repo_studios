#!/usr/bin/env python3
"""Analyze monkey-patch risk trends from consumer bundles with provenance."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

DEFAULT_CONSUMER_BASE = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")
DEFAULT_PRODUCER_BASE = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
DEFAULT_OUTPUT_BASE = Path(".repo_studios/reports/aggregator_reports/monkey_patch_trends")
DEFAULT_ARTIFACTS_TO_KEEP = 10
DEFAULT_MAX_RUNS = 20

CONSUMER_BUNDLE_PREFIX = "monkey_patch_risk-"
CONSUMER_SUMMARY_NAME = "summary.json"
CONSUMER_BUNDLE_SUMMARY_NAME = "bundle_summary.json"

AGGREGATOR_PREFIX = "monkey_patch_trends-"
TREND_JSON_NAME = "trend.json"
TREND_MD_NAME = "trend.md"
AGGREGATOR_BUNDLE_SUMMARY_NAME = "bundle_summary.json"
CONSUMER_TREND_COPY_NAME = "TREND_SNAPSHOT.md"

PRODUCER_REPORT_NAME = "report.json"

RISK_LEVELS: tuple[str, ...] = ("HIGH", "MODERATE", "SAFE")

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
UTILITIES_ROOT = Path(__file__).resolve().parents[2]
for candidate in (SCRIPTS_ROOT, UTILITIES_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from utilities.monkey_patch_risk import (  # noqa: E402
    FindingSignals,
    classify_monkey_patch,
)


@dataclass(frozen=True)
class TrendRun:
    ts_label: str
    sort_key: datetime
    total: int
    counts: dict[str, int]
    bundle_dir: Path | None
    summary_path: Path | None
    bundle_summary_path: Path | None
    scan_dir: Path | None
    source: str
    metadata: dict[str, Any]


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Blend monkey-patch consumer bundles (or producer fallbacks) into trend artifacts.")
    )
    parser.add_argument(
        "--consumer-base",
        type=Path,
        default=DEFAULT_CONSUMER_BASE,
        help="Directory containing timestamped monkey_patch_risk bundles",
    )
    parser.add_argument(
        "--consumer-summary",
        type=Path,
        help="Optional explicit consumer summary path to include in the run",
    )
    parser.add_argument(
        "--producer-base",
        type=Path,
        default=DEFAULT_PRODUCER_BASE,
        help="Producer scans directory for fallback reporting",
    )
    parser.add_argument(
        "--output-base",
        type=Path,
        default=DEFAULT_OUTPUT_BASE,
        help="Output directory for aggregator bundles",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of trend bundles to retain (including newest)",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=DEFAULT_MAX_RUNS,
        help="Maximum runs to include when building the overview",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging verbosity (INFO, DEBUG, etc.)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Shortcut for --log-level DEBUG",
    )
    return parser.parse_args(argv)


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else Path.cwd() / path


def _iso_to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    candidate = candidate.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _dir_timestamp(name: str) -> datetime | None:
    stem = name
    if stem.startswith(CONSUMER_BUNDLE_PREFIX):
        stem = stem[len(CONSUMER_BUNDLE_PREFIX) :]
    if stem.startswith(AGGREGATOR_PREFIX):
        stem = stem[len(AGGREGATOR_PREFIX) :]
    for fmt in ("%Y-%m-%d_%H%M%S", "%Y%m%d%H%M%S"):
        try:
            parsed = datetime.strptime(stem, fmt)
        except ValueError:
            continue
        return parsed.replace(tzinfo=UTC)
    return None


def _classify(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = {level: 0 for level in RISK_LEVELS}
    for finding in findings:
        risk = classify_monkey_patch(
            FindingSignals(
                category=str(finding.get("category", "")),
                is_test=bool(finding.get("is_test", False)),
                is_module_scope=bool(finding.get("is_module_scope", False)),
            )
        )
        counts[risk] += 1
    return counts


def _complete_counts(counts: dict[str, int]) -> dict[str, int]:
    return {level: int(counts.get(level, 0)) for level in RISK_LEVELS}


def _load_consumer_runs(
    base_dir: Path,
    summary_override: Path | None,
    logger: logging.Logger,
) -> list[TrendRun]:
    candidates: dict[Path, Path] = {}
    if base_dir.exists():
        for child in base_dir.iterdir():
            if child.is_dir() and child.name.startswith(CONSUMER_BUNDLE_PREFIX):
                candidates[child.resolve()] = child
    if summary_override is not None:
        target = summary_override
        if target.is_file():
            target = target.parent
        if target.is_dir():
            candidates[target.resolve()] = target
    runs: list[TrendRun] = []
    for bundle_dir in sorted(candidates.values(), key=lambda p: p.name):
        summary_path = bundle_dir / CONSUMER_SUMMARY_NAME
        if not summary_path.exists():
            logger.debug("Skipping %s (missing %s)", bundle_dir, CONSUMER_SUMMARY_NAME)
            continue
        try:
            summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read consumer summary %s: %s", summary_path, exc)
            continue
        if not isinstance(summary_data, dict):
            logger.warning("Consumer summary %s must be a JSON object", summary_path)
            continue
        bundle_summary_path = bundle_dir / CONSUMER_BUNDLE_SUMMARY_NAME
        bundle_metadata: dict[str, Any] = {}
        if bundle_summary_path.exists():
            try:
                maybe_meta = json.loads(bundle_summary_path.read_text(encoding="utf-8"))
                if isinstance(maybe_meta, dict):
                    bundle_metadata = maybe_meta
            except Exception as exc:
                logger.warning("Failed to read bundle metadata %s: %s", bundle_summary_path, exc)
        timestamp = (
            _iso_to_datetime(bundle_metadata.get("generated_at"))
            or _dir_timestamp(bundle_dir.name)
            or datetime.fromtimestamp(bundle_dir.stat().st_mtime, UTC)
        )
        ts_label = bundle_metadata.get("generated_at") or timestamp.isoformat(timespec="seconds")
        counts_raw = summary_data.get("counts_by_risk", {})
        counts = _complete_counts(counts_raw if isinstance(counts_raw, dict) else {})
        total = int(summary_data.get("total_findings", sum(counts.values())))
        scan_dir_value = bundle_metadata.get("scan_dir")
        try:
            scan_path = Path(scan_dir_value).resolve() if scan_dir_value else None
        except Exception:
            scan_path = None
        runs.append(
            TrendRun(
                ts_label=ts_label,
                sort_key=timestamp,
                total=total,
                counts=counts,
                bundle_dir=bundle_dir,
                summary_path=summary_path,
                bundle_summary_path=bundle_summary_path if bundle_summary_path.exists() else None,
                scan_dir=scan_path,
                source=str(bundle_metadata.get("source", "consumer")),
                metadata={
                    "bundle_summary": bundle_metadata,
                    "run_metadata": summary_data.get("run_metadata", {}),
                },
            )
        )
    runs.sort(key=lambda run: run.sort_key)
    return runs


def _load_producer_runs(base_dir: Path, logger: logging.Logger) -> list[TrendRun]:
    runs: list[TrendRun] = []
    if not base_dir.exists():
        return runs
    for child in sorted(base_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        report_path = child / PRODUCER_REPORT_NAME
        if not report_path.exists():
            continue
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read producer report %s: %s", report_path, exc)
            continue
        if not isinstance(data, list):
            logger.warning("Producer report %s must contain a list", report_path)
            continue
        counts = _classify(data)
        timestamp = _dir_timestamp(child.name) or datetime.fromtimestamp(child.stat().st_mtime, UTC)
        ts_label = timestamp.isoformat(timespec="seconds")
        runs.append(
            TrendRun(
                ts_label=ts_label,
                sort_key=timestamp,
                total=sum(counts.values()),
                counts=_complete_counts(counts),
                bundle_dir=None,
                summary_path=report_path,
                bundle_summary_path=None,
                scan_dir=child.resolve(),
                source="producer_fallback",
                metadata={"producer_report": str(report_path.resolve())},
            )
        )
    runs.sort(key=lambda run: run.sort_key)
    return runs


def _latest_delta(runs: list[TrendRun]) -> dict[str, Any] | None:
    if len(runs) < 2:
        return None
    prev, cur = runs[-2], runs[-1]
    delta = {level: cur.counts.get(level, 0) - prev.counts.get(level, 0) for level in RISK_LEVELS}
    return {
        "prev": {
            "ts": prev.ts_label,
            "total": prev.total,
            "counts": _complete_counts(prev.counts),
        },
        "cur": {
            "ts": cur.ts_label,
            "total": cur.total,
            "counts": _complete_counts(cur.counts),
        },
        "delta": delta,
    }


def _render_markdown(
    *,
    generated_at: datetime,
    mode: str,
    runs: list[TrendRun],
    latest: dict[str, Any] | None,
    notes: list[str],
) -> str:
    lines: list[str] = ["# Monkey Patch Trend Summary", ""]
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append(f"Mode: {'Consumer bundles' if mode == 'consumer' else 'Producer fallback'}")
    lines.append("")
    if notes:
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.append("## Run Overview")
    lines.append("")
    if runs:
        lines.append("| Run | Total | HIGH | MODERATE | SAFE |")
        lines.append("|---|---:|---:|---:|---:|")
        for run in runs:
            counts = _complete_counts(run.counts)
            lines.append(
                f"| {run.ts_label} | {run.total} | {counts['HIGH']} | {counts['MODERATE']} | {counts['SAFE']} |"
            )
        lines.append("")
    else:
        lines.append("No runs available.")
        lines.append("")
    if runs:
        latest_run = runs[-1]
        lines.append("## Latest Run Detail")
        lines.append("")
        lines.append(f"- Run: {latest_run.ts_label}")
        lines.append(f"- Source: {latest_run.source}")
        if latest_run.scan_dir:
            lines.append(f"- Scan Dir: `{latest_run.scan_dir}`")
        if latest_run.summary_path:
            lines.append(f"- Summary: `{latest_run.summary_path}`")
        if latest_run.bundle_dir:
            lines.append(f"- Bundle: `{latest_run.bundle_dir}`")
        lines.append("")
    if latest:
        lines.append("## Delta vs Previous")
        lines.append("")
        lines.append("| Level | Prev | Curr | Δ |")
        lines.append("|---|---:|---:|---:|")
        for level in RISK_LEVELS:
            prev_val = latest["prev"]["counts"][level]
            cur_val = latest["cur"]["counts"][level]
            delta_val = latest["delta"][level]
            lines.append(f"| {level} | {prev_val} | {cur_val} | {delta_val:+d} |")
        lines.append("")
        lines.append(f"Total Δ: {latest['cur']['total'] - latest['prev']['total']:+d}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _update_latest(base: Path, bundle_dir: Path, filenames: Sequence[str]) -> None:
    base.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        src = bundle_dir / name
        dest = base / f"latest_{name}"
        try:
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            dest.hardlink_to(src)
        except Exception:
            dest.write_bytes(src.read_bytes())


def _prune_history(base: Path, current: Path, keep: int) -> list[Path]:
    try:
        keep_count = max(int(keep), 0)
    except Exception:
        keep_count = DEFAULT_ARTIFACTS_TO_KEEP
    if not base.exists():
        return []
    bundles = sorted(
        [
            path
            for path in base.iterdir()
            if path.is_dir() and path.name.startswith(AGGREGATOR_PREFIX) and path != current
        ],
        key=lambda p: p.name,
        reverse=True,
    )
    limit = max(keep_count - 1, 0)
    stale = bundles[limit:]
    for path in stale:
        shutil.rmtree(path, ignore_errors=True)
    return stale


def _copy_markdown_to_consumer(latest_run: TrendRun, trend_md: Path, logger: logging.Logger) -> Path | None:
    if latest_run.bundle_dir is None:
        return None
    target = latest_run.bundle_dir / CONSUMER_TREND_COPY_NAME
    try:
        target.write_bytes(trend_md.read_bytes())
    except Exception as exc:
        logger.debug("Unable to mirror trend markdown to consumer bundle: %s", exc)
        return None
    return target


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    log_level = logging.DEBUG if args.verbose else getattr(logging, str(args.log_level).upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s", force=True)
    logger = logging.getLogger("analyze_monkey_patch_trends")

    consumer_base = _resolve_path(args.consumer_base)
    consumer_summary = _resolve_path(args.consumer_summary) if args.consumer_summary is not None else None
    producer_base = _resolve_path(args.producer_base)
    output_base = _resolve_path(args.output_base)
    max_runs = max(int(args.max_runs or 0), 1)

    consumer_runs = _load_consumer_runs(consumer_base, consumer_summary, logger)
    mode = "consumer" if consumer_runs else "producer_fallback"
    runs = consumer_runs or _load_producer_runs(producer_base, logger)
    if not runs:
        raise FileNotFoundError("No consumer bundles or producer reports available for trend analysis.")
    runs = runs[-max_runs:]

    generated_at = datetime.now(UTC)
    bundle_dir = output_base / f"{AGGREGATOR_PREFIX}{generated_at.strftime('%Y-%m-%d_%H%M%S')}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    latest = _latest_delta(runs)
    notes: list[str] = []
    if mode != "consumer":
        notes.append("Consumer bundles not found; producer reports used for fallback analysis.")

    trend_json_path = bundle_dir / TREND_JSON_NAME
    trend_md_path = bundle_dir / TREND_MD_NAME
    trend_bundle_summary_path = bundle_dir / AGGREGATOR_BUNDLE_SUMMARY_NAME

    runs_payload = [
        {
            "ts": run.ts_label,
            "total_findings": run.total,
            "counts_by_risk": _complete_counts(run.counts),
            "bundle_dir": str(run.bundle_dir.resolve()) if run.bundle_dir else None,
            "summary_path": str(run.summary_path.resolve()) if run.summary_path else None,
            "bundle_summary": str(run.bundle_summary_path.resolve()) if run.bundle_summary_path else None,
            "scan_dir": str(run.scan_dir) if run.scan_dir else None,
            "source": run.source,
            "metadata": run.metadata,
        }
        for run in runs
    ]

    trend_payload = {
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "mode": mode,
        "requested_keep": int(args.artifacts_to_keep),
        "runs": runs_payload,
        "runs_considered": len(runs_payload),
        "latest": latest,
        "notes": notes,
    }
    trend_json_path.write_text(json.dumps(trend_payload, indent=2) + "\n", encoding="utf-8")

    trend_md = _render_markdown(generated_at=generated_at, mode=mode, runs=runs, latest=latest, notes=notes)
    trend_md_path.write_text(trend_md, encoding="utf-8")

    trend_bundle_summary = {
        "schema_version": 1,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "mode": mode,
        "trend_dir": str(bundle_dir.resolve()),
        "artifacts": {
            "trend_json": str(trend_json_path.resolve()),
            "trend_md": str(trend_md_path.resolve()),
        },
        "inputs": runs_payload,
        "latest": latest,
        "notes": notes,
    }
    trend_bundle_summary_path.write_text(json.dumps(trend_bundle_summary, indent=2) + "\n", encoding="utf-8")

    _update_latest(
        output_base,
        bundle_dir,
        [TREND_JSON_NAME, TREND_MD_NAME, AGGREGATOR_BUNDLE_SUMMARY_NAME],
    )
    pruned = _prune_history(output_base, bundle_dir, args.artifacts_to_keep)

    consumer_snapshot = None
    if runs and runs[-1].bundle_dir:
        consumer_snapshot = _copy_markdown_to_consumer(runs[-1], trend_md_path, logger)

    logger.info(
        "Trend bundle written to %s (mode=%s, runs=%d, pruned=%d)",
        bundle_dir,
        mode,
        len(runs),
        len(pruned),
    )

    return {
        "mode": mode,
        "trend_dir": str(bundle_dir.resolve()),
        "trend_json": str(trend_json_path.resolve()),
        "trend_markdown": str(trend_md_path.resolve()),
        "bundle_summary": str(trend_bundle_summary_path.resolve()),
        "latest_run": runs[-1].ts_label,
        "runs": len(runs),
        "pruned": [str(path.resolve()) for path in pruned],
        "consumer_snapshot": str(consumer_snapshot.resolve()) if consumer_snapshot else None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run(argv)
    except Exception as exc:  # pragma: no cover - unexpected runtime failures
        logging.exception("Failed to analyze monkey patch trends: %s", exc)
        return 1
    import sys

    sys.stdout.write(json.dumps({"status": "OK", **result}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
