#!/usr/bin/env python3
"""Collect structured summaries for faulthandler runs.

This producer converts raw faulthandler run directories into timestamped
artifacts under `.repo_studios/reports/producer_reports/faulthandler_reports/`.
It emits JSON, Markdown, CSV, and log summaries that downstream consumers can
reuse without re-parsing stacks. The script also mirrors key files into the
Command Center reports tree so agents have a single discovery point.
"""

import argparse
import csv
import json
import logging
import os
import sys
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Sequence

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
REPO_LIB_ROOT = Path(__file__).resolve().parents[2]
for candidate in (SCRIPTS_ROOT, REPO_LIB_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from command_center.scripts.libraries.artifacts import (  # noqa: E402
    ReportArtifact,
    WriteReportArtifactsResult,
    copy_latest_artifact,
    write_report_artifacts,
)
from command_center.scripts.libraries.cli import (  # noqa: E402
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    build_standard_options,
    build_standard_paths,
)
from command_center.scripts.libraries import prune_run_directories  # noqa: E402
from utilities.fault_run_analysis import (  # noqa: E402
    FaultAnalysisResult,
    FaultSignature,
    build_fault_report,
)

DEFAULT_RUNS_RELATIVE = Path(".repo_studios/reports/orchestrator_logs/faulthandler_logs")
LEGACY_RUNS_RELATIVE = Path(".repo_studios/faulthandler")
DEFAULT_OUTPUT_RELATIVE = Path(".repo_studios/reports/producer_reports/faulthandler_reports")
DEFAULT_COMMAND_CENTER_RELATIVE = Path(".repo_studios/command_center/reports/fault_artifacts_producer")
RUN_PREFIX = "faulthandler_report"
DEFAULT_KEEP = 5

EXPECTED_SUMMARY_KEYS = frozenset(
    {
        "signature_count",
        "thread_block_count",
        "top_frame_limit",
        "stack_log_exists",
        "stack_text_bytes",
        "severity_buckets",
        "active_signature_count",
        "first_seen_utc",
        "last_seen_utc",
    }
)
EXPECTED_BUCKET_KEYS = frozenset({"repeat_offender", "multi_hit", "single_hit"})


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    runs_dir: Path
    output_dir: Path
    command_center_dir: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int
    log_level: str = "INFO"
    validate_only: bool = False
    top_frames: int | None = None


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "runs_dir": PathSpec(field="runs_dir", default=DEFAULT_RUNS_RELATIVE, ensure_dir=False, within_repo=False),
        "output_dir": PathSpec(
            field="output_dir",
            default=DEFAULT_OUTPUT_RELATIVE,
            ensure_dir=True,
            within_repo=False,
        ),
        "command_center_dir": PathSpec(
            field="command_center_dir",
            default=DEFAULT_COMMAND_CENTER_RELATIVE,
            ensure_dir=True,
            within_repo=False,
        ),
    },
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
    },
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="collect_faulthandler_reports",
        description=__doc__ or "",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", help="Repository root (defaults to auto-detect)")
    parser.add_argument("--runs-dir", help="Directory containing faulthandler capture folders")
    parser.add_argument("--run-dir", help="Explicit faulthandler run directory to process")
    parser.add_argument("--output-dir", help="Destination for structured producer artifacts")
    parser.add_argument(
        "--command-center-dir",
        help="Mirror location under .repo_studios/command_center/reports for Command Center discovery",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_KEEP,
        help="Number of historical runs to retain (minimum 1)",
    )
    parser.add_argument(
        "--top-frames",
        type=int,
        default=None,
        help="Override the number of frames captured per signature",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the latest report.json schema without writing new artifacts",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace) -> Options:
    base = build_standard_options(args, OPTIONS_CONFIG)
    return replace(
        base,
        log_level=str(args.log_level),
        validate_only=bool(args.validate_only),
        top_frames=int(args.top_frames) if args.top_frames is not None else None,
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def _allow_legacy_runs() -> bool:
    flag = os.environ.get("FAULTHANDLER_ALLOW_LEGACY", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def _resolve_runs_base(paths: Paths) -> Path:
    runs_dir = paths.runs_dir
    if runs_dir.exists():
        return runs_dir

    legacy = LEGACY_RUNS_RELATIVE
    if not legacy.is_absolute():
        legacy = paths.repo_root / legacy

    if _allow_legacy_runs() and legacy.exists():
        logging.getLogger("faulthandler_report").info(
            "Faulthandler runs directory %s missing; falling back to legacy %s",
            runs_dir,
            legacy,
        )
        return legacy

    return runs_dir


def _find_latest_run(runs_base: Path) -> Path | None:
    try:
        candidates = [p for p in runs_base.iterdir() if p.is_dir()]
    except FileNotFoundError:
        return None
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _resolve_run_dir(explicit: str | None, runs_base: Path) -> Path | None:
    if explicit:
        return Path(explicit)
    return _find_latest_run(runs_base)


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
    lines.append(f"- active_signature_count: {summary.get('active_signature_count')}")
    lines.append(f"- thread_block_count: {summary.get('thread_block_count')}")
    lines.append(f"- top_frame_limit: {summary.get('top_frame_limit')}")
    lines.append(f"- stack_log_exists: {summary.get('stack_log_exists')}")
    lines.append(f"- stack_text_bytes: {summary.get('stack_text_bytes')}")
    lines.append(f"- first_seen_utc: {summary.get('first_seen_utc')}")
    lines.append(f"- last_seen_utc: {summary.get('last_seen_utc')}")
    lines.append("")
    severity = summary.get("severity_buckets") if isinstance(summary, dict) else {}
    if isinstance(severity, dict):
        lines.append("## Severity Buckets")
        lines.append("")
        lines.append(f"- repeat_offender: {severity.get('repeat_offender', 0)}")
        lines.append(f"- multi_hit: {severity.get('multi_hit', 0)}")
        lines.append(f"- single_hit: {severity.get('single_hit', 0)}")
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
    return "\n".join(lines) + "\n"


def _write_csv_writer(signatures: Sequence[FaultSignature]) -> Callable[[Path], Path]:
    def _writer(run_dir: Path) -> Path:
        csv_path = run_dir / "stacks.csv"
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
        return csv_path

    return _writer


def _write_combined_writer(combined_text: str) -> Callable[[Path], Path]:
    def _writer(run_dir: Path) -> Path:
        path = run_dir / "combined.txt"
        path.write_text(combined_text, encoding="utf-8")
        return path

    return _writer


def _write_log_writer(report: dict[str, Any], signatures: Sequence[FaultSignature]) -> Callable[[Path], Path]:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}

    def _writer(run_dir: Path) -> Path:
        lines = [
            f"generated_utc={report.get('generated_utc')}",
            f"run_dir={report.get('run_dir')}",
            f"signatures={len(signatures)}",
            f"thread_block_count={summary.get('thread_block_count')}",
            f"stack_text_bytes={summary.get('stack_text_bytes')}",
            f"repeat_offender={summary.get('severity_buckets', {}).get('repeat_offender', 0)}",
        ]
        path = run_dir / "log.txt"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    return _writer


def _bundle_summary_writer(result: FaultAnalysisResult) -> Callable[[Path], Path]:
    summary = result.report.get("summary") if isinstance(result.report.get("summary"), dict) else {}

    def _writer(run_dir: Path) -> Path:
        payload = {
            "schema_version": 1,
            "bundle": run_dir.name,
            "generated_at": result.report.get("generated_utc"),
            "source": "collect_faulthandler_reports",
            "run_dir": result.report.get("run_dir"),
            "metrics": {
                "signature_count": summary.get("signature_count"),
                "active_signature_count": summary.get("active_signature_count"),
                "repeat_offender": summary.get("severity_buckets", {}).get("repeat_offender"),
                "multi_hit": summary.get("severity_buckets", {}).get("multi_hit"),
                "single_hit": summary.get("severity_buckets", {}).get("single_hit"),
                "thread_block_count": summary.get("thread_block_count"),
            },
            "artifacts": {
                "report_json": str((run_dir / "report.json").resolve()),
                "report_md": str((run_dir / "report.md").resolve()),
                "stacks_csv": str((run_dir / "stacks.csv").resolve()),
                "combined_txt": str((run_dir / "combined.txt").resolve()) if (run_dir / "combined.txt").exists() else None,
                "log_txt": str((run_dir / "log.txt").resolve()),
            },
            "summary": summary,
        }
        path = run_dir / "bundle_summary.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    return _writer


def _write_artifacts(result: FaultAnalysisResult, output_dir: Path, *, keep: int) -> WriteReportArtifactsResult:
    generated = result.report.get("generated_utc")
    try:
        timestamp = datetime.fromisoformat(str(generated))
    except Exception:
        timestamp = datetime.now(UTC)
    return write_report_artifacts(
        stem=RUN_PREFIX,
        timestamp=timestamp,
        output_dir=output_dir,
        keep=keep,
        artifacts=[
            ReportArtifact(
                filename="report.json",
                kind="json",
                content=result.report,
                pointer="latest_report.json",
            ),
            ReportArtifact(
                filename="report.md",
                kind="text",
                content=_render_markdown(result.report, result.signatures),
                pointer="latest_report.md",
            ),
            ReportArtifact(
                filename="stacks.csv",
                writer=_write_csv_writer(result.signatures),
                pointer="latest_stacks.csv",
            ),
            ReportArtifact(
                filename="combined.txt",
                writer=_write_combined_writer(result.combined_text),
                pointer="latest_combined.txt",
            ),
            ReportArtifact(
                filename="log.txt",
                writer=_write_log_writer(result.report, result.signatures),
                pointer="latest_log.txt",
            ),
            ReportArtifact(
                filename="bundle_summary.json",
                writer=_bundle_summary_writer(result),
                pointer="latest_bundle_summary.json",
            ),
        ],
    )


def _mirror_to_command_center(
    write_result: WriteReportArtifactsResult,
    command_center_dir: Path,
    *,
    keep: int,
    logger: logging.Logger | None,
) -> None:
    command_center_dir.mkdir(parents=True, exist_ok=True)
    cc_run_dir = command_center_dir / write_result.run_dir.name
    cc_run_dir.mkdir(parents=True, exist_ok=True)

    for filename in ("report.json", "report.md", "bundle_summary.json"):
        src = write_result.artifacts.get(filename)
        if not src:
            continue
        dest = cc_run_dir / filename
        dest.write_bytes(src.read_bytes())
        copy_latest_artifact(src, command_center_dir / f"latest_{filename}")

    prune_run_directories(
        command_center_dir,
        keep=max(1, keep),
        stem_prefix=RUN_PREFIX,
        current_run=cc_run_dir,
        logger=logger,
    )


def _validate_latest(paths: Paths, log: logging.Logger) -> dict[str, Any]:
    latest_report = paths.output_dir / "latest_report.json"
    issues: list[str] = []
    payload: dict[str, Any] | None = None
    if not latest_report.exists():
        issues.append("latest_report.json missing")
    else:
        try:
            payload = json.loads(latest_report.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            issues.append(f"latest_report.json invalid JSON: {exc}")

    summary = payload.get("summary") if isinstance(payload, dict) else None
    if summary is None:
        issues.append("summary section missing")
    else:
        missing = sorted(EXPECTED_SUMMARY_KEYS - summary.keys())
        if missing:
            issues.append(f"missing summary keys: {', '.join(missing)}")
        buckets = summary.get("severity_buckets") if isinstance(summary, dict) else None
        if not isinstance(buckets, dict):
            issues.append("severity_buckets missing or not a dict")
        else:
            bucket_missing = sorted(EXPECTED_BUCKET_KEYS - buckets.keys())
            if bucket_missing:
                issues.append(f"missing severity bucket keys: {', '.join(bucket_missing)}")

    for pointer in ("latest_bundle_summary.json", "latest_report.md", "latest_stacks.csv"):
        if not (paths.output_dir / pointer).exists():
            issues.append(f"{pointer} missing")

    status = "pass" if not issues else "fail"
    for entry in issues:
        log.error("Validation issue: %s", entry)

    return {
        "status": status,
        "issues": issues,
        "report_path": str(latest_report.resolve()) if latest_report.exists() else None,
    }


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)
    log = logging.getLogger("faulthandler_report")

    runs_dir = _resolve_runs_base(paths)

    if options.validate_only:
        return _validate_latest(paths, log)

    run_dir_path = _resolve_run_dir(args.run_dir, runs_dir)
    if run_dir_path is None or not Path(run_dir_path).exists():
        log.info("No faulthandler runs available under %s", runs_dir)
        return {
            "run_dir": None,
            "artifacts": None,
            "output_dir": str(paths.output_dir),
        }

    run_dir = Path(run_dir_path).resolve()
    if options.top_frames is not None:
        analysis = build_fault_report(run_dir, top_n=options.top_frames)
    else:
        analysis = build_fault_report(run_dir)

    write_result = _write_artifacts(analysis, paths.output_dir, keep=options.artifacts_to_keep)
    _mirror_to_command_center(
        write_result,
        paths.command_center_dir,
        keep=options.artifacts_to_keep,
        logger=log,
    )

    summary = analysis.report.get("summary", {}) if isinstance(analysis.report, dict) else {}
    severity = summary.get("severity_buckets", {}) if isinstance(summary, dict) else {}
    log.info(
        "Faulthandler report captured (run_dir=%s, signatures=%d, repeat_offender=%s, output=%s)",
        run_dir,
        len(analysis.signatures),
        severity.get("repeat_offender", 0),
        write_result.run_dir,
    )
    return {
        "run_dir": str(run_dir),
        "output_dir": str(write_result.run_dir),
        "report": str((write_result.artifacts.get("report.json") or (write_result.run_dir / "report.json")).resolve()),
        "signatures": len(analysis.signatures),
        "repeat_offender_signatures": int(severity.get("repeat_offender", 0)),
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
