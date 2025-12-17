#!/usr/bin/env python3
"""
Health Suite Summary — Compose a compact summary into one markdown from:
- Repo Insight trends (monkey patch trend preview)
- Dependency Hygiene (summary)
- Import Graph (hotspots + cycles)
- Test Log Health (pytest warnings/exceptions + slowest tests)
- Churn × Complexity Heatmap (top risk items)

Writes: .repo_studios/reports/summarizer_reports/health_suite_summary_reports/health_suite_YYYY-MM-DD_HHMM.md
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from command_center.scripts.libraries import (
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    ReportArtifact,
    WriteReportArtifactsResult,
    build_standard_options,
    build_standard_paths,
    write_report_artifacts,
)

SUMMARY_OUTPUT_DEFAULT = Path(".repo_studios/command_center/reports")
LEGACY_SUMMARY_DIR = Path(".repo_studios/health_suite")
SUMMARY_STEM = "health_suite_summary"
VIEWER_SLUG = "healthview"
TOPIC_SLUG = "health_suite_overview"
SCHEMA_VERSION = 1
DEFAULT_ARTIFACTS_TO_KEEP = 5


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    legacy_dir: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(field="output_dir", default=SUMMARY_OUTPUT_DEFAULT, ensure_dir=True, within_repo=False),
        "legacy_dir": PathSpec(field="legacy_dir", default=LEGACY_SUMMARY_DIR, ensure_dir=True, within_repo=False),
    },
    repo_root_depth=5,
)


@dataclass(frozen=True)
class Options:
    log_level: str
    artifacts_to_keep: int
    run_timestamp: datetime
    mirror_legacy: bool


@dataclass(frozen=True)
class KeepValues:
    artifacts_to_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


def _parse_args(argv: Iterable[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument(
        "--output-dir",
        default=str(SUMMARY_OUTPUT_DEFAULT),
        help="Root directory for Healthview artifacts",
    )
    parser.add_argument(
        "--legacy-dir",
        default=str(LEGACY_SUMMARY_DIR),
        help="Optional legacy mirror directory for markdown copies",
    )
    parser.add_argument(
        "--timestamp",
        help="ISO-8601 timestamp for emitted artifacts (defaults to current UTC time)",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention budget for Healthview runs",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--skip-legacy-mirror",
        action="store_true",
        help="Disable legacy markdown mirror in .repo_studios/health_suite",
    )
    return parser.parse_args(argv)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - defensive parsing
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timestamp_slug(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%d_%H%M")


def _healthview_run_slug(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")


def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace) -> Options:
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    artifacts_to_keep = max(int(getattr(keep_values, "artifacts_to_keep", DEFAULT_ARTIFACTS_TO_KEEP)), 1)
    return Options(
        log_level=str(args.log_level),
        artifacts_to_keep=artifacts_to_keep,
        run_timestamp=_parse_timestamp(getattr(args, "timestamp", None)),
        mirror_legacy=not bool(getattr(args, "skip_legacy_mirror", False)),
    )


def _read_text(path: Path, default: str = "(missing)") -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return default


def _latest_dir(base: Path) -> Path | None:
    if not base.exists():
        return None
    dirs = [p for p in base.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return sorted(dirs)[-1]


def _prefer_ts(base: Path, ts: str) -> Path | None:
    """Return base/ts if it exists, else fall back to the latest directory.

    This ensures the health suite summary links to artifacts produced during
    the same orchestrator run when available, avoiding cross-run mismatches
    (e.g., picking a future-dated placeholder folder).
    """
    try:
        if ts:
            candidate = base / ts
            if candidate.exists() and candidate.is_dir():
                return candidate
    except Exception:
        # Fall through to latest on any error
        pass
    return _latest_dir(base)


def _ensure_blank_separator(lines: list[str]) -> None:
    if lines and lines[-1].strip():
        lines.append("")


def _append_section_header(lines: list[str], level: int, title: str) -> None:
    _ensure_blank_separator(lines)
    lines.append(f"{'#' * level} {title}")
    lines.append("")


def _append_paragraph(lines: list[str], text: str) -> None:
    if not text:
        return
    _ensure_blank_separator(lines)
    for chunk in text.splitlines():
        lines.append(chunk.rstrip())
    lines.append("")


def _append_list(lines: list[str], items: list[str]) -> None:
    data = items or ["(none)"]
    _ensure_blank_separator(lines)
    for item in data:
        lines.append(f"- {item}")
    lines.append("")


def _append_table(lines: list[str], rows: list[str]) -> None:
    if not rows:
        return
    _ensure_blank_separator(lines)
    for row in rows:
        lines.append(row.rstrip())
    lines.append("")


def _append_blockquote(lines: list[str], rows: list[str]) -> None:
    if not rows:
        return
    _ensure_blank_separator(lines)
    for row in rows:
        content = row.rstrip()
        lines.append(f"> {content}" if content else ">")
    lines.append("")


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return default


def _read_json_dict(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _extract_section_lines(report: str, heading: str) -> list[str]:
    lines: list[str] = []
    capture = False
    for raw in report.splitlines():
        stripped = raw.strip()
        if stripped.startswith(("## ", "### ")):
            if stripped == heading:
                capture = True
                continue
            if capture:
                break
        if capture:
            lines.append(raw.rstrip())
    return lines


def _extract_markdown_list(report: str, heading: str, limit: int | None = None) -> list[str]:
    items: list[str] = []
    capture = False
    for raw in report.splitlines():
        stripped = raw.strip()
        if stripped.startswith(("## ", "### ")):
            if stripped == heading:
                capture = True
                continue
            if capture:
                break
        if capture and stripped.startswith("- "):
            items.append(stripped[2:].strip())
            if limit is not None and len(items) >= limit:
                break
    return items


def _load_trend_head(root: Path) -> tuple[list[str], Path | None]:
    trend_latest = root / ".repo_studios/reports/producer_reports/monkey_patch_scans/trend_latest.md"
    trend_txt = _read_text(trend_latest, "").strip()
    lines = [line.rstrip() for line in trend_txt.splitlines()[:40]] if trend_txt else []
    return lines, trend_latest if trend_latest.exists() else None


def _load_dep_summary(root: Path, ts: str) -> tuple[str, Path | None]:
    dep_base = root / ".repo_studios/dep_health"
    dep_dir = _prefer_ts(dep_base, ts)
    dep_report = _read_text(dep_dir / "report.md") if dep_dir else ""
    summary_lines = [line.strip() for line in _extract_section_lines(dep_report, "## Summary") if line.strip()]
    summary_text = "\n".join(summary_lines) if summary_lines else "(no summary)"
    return summary_text, dep_dir


def _load_import_graph(root: Path, ts: str) -> tuple[list[str], list[str], list[str], Path | None]:
    ig_base = root / ".repo_studios" / "reports" / "producer_reports" / "healthview" / "import_graph"
    ig_dir = _prefer_ts(ig_base, ts)
    ig_report = _read_text(ig_dir / "summary.md") if ig_dir else ""

    fan_in = (
        _extract_markdown_list(ig_report, "### Top fan-in (modules most depended on)")
        or _extract_markdown_list(ig_report, "## Top Fan-In")
    )
    fan_out = (
        _extract_markdown_list(ig_report, "### Top fan-out (modules with many dependencies)")
        or _extract_markdown_list(ig_report, "## Top Fan-Out")
    )
    cycles = (
        _extract_markdown_list(ig_report, "### Cycles (first 10)", limit=10)
        or _extract_markdown_list(ig_report, "## Cycles", limit=10)
    )
    if not cycles:
        cycles = ["None detected"]
    return fan_in, fan_out, cycles, ig_dir


def _load_test_health_summary(root: Path, ts: str) -> tuple[list[str], Path | None]:
    th_base = root / ".repo_studios/reports/consumer_reports/test_log_health_reports"
    th_dir = _prefer_ts(th_base, ts)
    th_report = _read_text(th_dir / "report.md") if th_dir else ""
    summary_lines = [
        line.lstrip("- ").strip() for line in _extract_section_lines(th_report, "## Summary") if line.strip()
    ]
    return summary_lines or ["(no summary)"], th_dir


def _load_churn_table(root: Path, ts: str) -> tuple[list[str], Path | None]:
    cc_base = root / ".repo_studios/reports/aggregator_reports/churn_complexity_heatmap"
    cc_dir = _prefer_ts(cc_base, ts)
    cc_report = _read_text(cc_dir / "heatmap.md") if cc_dir else ""
    lines = cc_report.splitlines()
    start_index = next(
        (idx for idx, raw in enumerate(lines) if raw.strip().startswith("| File | ")),
        None,
    )
    if start_index is None:
        return [], cc_dir
    table_rows = []
    for raw in lines[start_index:]:
        stripped = raw.strip()
        if not stripped or not stripped.startswith("|"):
            break
        table_rows.append(raw.rstrip())
        if len(table_rows) >= 12:
            break
    return table_rows, cc_dir


def _load_fault_trends(root: Path) -> list[tuple[str, str, float]]:
    tpath = root / ".repo_studios/health/faulthandler/trends.json"
    if not tpath.exists():
        return []
    try:
        data = json.loads(tpath.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(data, list) or len(data) < 2:
        return []
    prev = data[-2].get("metrics", {}) if isinstance(data[-2], dict) else {}
    curr = data[-1].get("metrics", {}) if isinstance(data[-1], dict) else {}

    def arrow(curr_v: float, prev_v: float) -> str:
        try:
            if curr_v > prev_v:
                return "▲"
            if curr_v < prev_v:
                return "▼"
            return "→"
        except Exception:
            return "→"

    def safe(value: object, default: float = 0.0) -> float:
        try:
            return float(value)  # type: ignore[arg-type]
        except Exception:
            return float(default)

    metrics = [
        "fault_dumps_total",
        "unique_signatures_count",
        "top_signature_repeat_count",
        "dump_rate_per_minute",
    ]
    results: list[tuple[str, str, float]] = []
    for metric in metrics:
        results.append(
            (
                metric,
                arrow(safe(curr.get(metric, 0.0)), safe(prev.get(metric, 0.0))),
                safe(curr.get(metric, 0.0)),
            )
        )
    return results


def _load_typecheck_summary(root: Path, ts: str) -> tuple[str, int, int, list[str], Path | None]:
    tc_base = root / ".repo_studios/typecheck"
    tc_dir = _prefer_ts(tc_base, ts)
    if not tc_dir:
        return "(missing)", 0, 0, [], None
    tc_json_path = tc_dir / "report.json"
    if not tc_json_path.exists():
        return "(no report.json)", 0, 0, [], tc_dir
    tc_data = _read_json_dict(tc_json_path)
    if tc_data is None:
        return "(error)", 0, 0, [], tc_dir

    status = str(tc_data.get("status", "UNKNOWN"))
    total_errors = _to_int(tc_data.get("total_errors", 0))
    files_with_issues = _to_int(tc_data.get("files_with_issues", 0))
    samples: list[str] = []
    for item in tc_data.get("error_samples", [])[:10]:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "?"))
        line = _to_int(item.get("line", 1), default=1)
        code = str(item.get("code", "") or "")
        message = str(item.get("message", "") or "")
        samples.append(f"{path}:{line} — [{code}] {message}" if code else f"{path}:{line} — {message}")
    return status, total_errors, files_with_issues, samples, tc_dir


def _parse_lizard_offenders(
    raw_json_path: Path,
    repo_root: Path,
    max_ccn: int,
    max_length: int,
) -> list[tuple[str, str, int, int]]:
    try:
        payload = json.loads(raw_json_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    offenders: list[tuple[str, str, int, int]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        file_name_raw = entry.get("filename") or entry.get("file_name") or entry.get("file")
        if not isinstance(file_name_raw, str):
            continue
        file_path = Path(file_name_raw)
        try:
            normalized_path = str(file_path.resolve().relative_to(repo_root))
        except Exception:
            normalized_path = str(file_path)
        functions = entry.get("function_list")
        if not isinstance(functions, list):
            continue
        for func in functions:
            if not isinstance(func, dict):
                continue
            name = func.get("name") or func.get("long_name") or "<unnamed>"
            ccn_val = _to_int(func.get("cyclomatic_complexity", 0))
            length_val = _to_int(func.get("length", 0))
            if ccn_val > max_ccn or length_val > max_length:
                offenders.append((str(name), normalized_path, ccn_val, length_val))
    offenders.sort(key=lambda item: (item[2], item[3]), reverse=True)
    return offenders


def _load_lizard_summary(
    root: Path, ts: str
) -> tuple[
    str,
    int,
    str,
    list[str],
    int | None,
    int | None,
    list[tuple[str, str, int, int]],
    Path | None,
]:
    lizard_base = root / ".repo_studios/lizard"
    lizard_dir = _prefer_ts(lizard_base, ts)
    if not lizard_dir:
        return "(missing)", 0, "", [], None, None, [], None
    report_path = lizard_dir / "report.json"
    if not report_path.exists():
        return "(no report.json)", 0, "", [], None, None, [], lizard_dir
    data = _read_json_dict(report_path)
    if data is None:
        return "(error)", 0, "", [], None, None, [], lizard_dir
    status = str(data.get("status", "UNKNOWN"))
    issue_count = _to_int(data.get("issue_count", 0))
    notes = str(data.get("notes", "") or "").strip()
    targets_raw = data.get("targets", [])
    targets: list[str] = []
    if isinstance(targets_raw, list):
        for target in targets_raw[:6]:
            target_path = Path(target)
            try:
                targets.append(str(target_path.resolve().relative_to(root)))
            except Exception:
                targets.append(str(target_path))
    max_ccn_value = data.get("max_ccn")
    max_length_value = data.get("max_length")
    max_ccn = _to_int(max_ccn_value) if max_ccn_value is not None else None
    max_length = _to_int(max_length_value) if max_length_value is not None else None
    offenders: list[tuple[str, str, int, int]] = []
    raw_path = lizard_dir / "raw.json"
    if raw_path.exists() and max_ccn is not None and max_length is not None:
        offenders = _parse_lizard_offenders(raw_path, root, max_ccn, max_length)
    return status, issue_count, notes, targets, max_ccn, max_length, offenders, lizard_dir


def _find_anchor_dir(anchor_base: Path, ts: str) -> Path | None:
    if ts:
        prefix = ts[:16]
        for directory in sorted(anchor_base.glob(f"anchor_health-{prefix}*")):
            if directory.is_dir():
                return directory
    candidates = [p for p in anchor_base.glob("anchor_health-*") if p.is_dir()]
    return sorted(candidates)[-1] if candidates else None


def _load_anchor_data(root: Path, ts: str) -> tuple[dict | None, Path | None]:
    anchor_base = root / ".repo_studios/anchor_health"
    anchor_latest_json = anchor_base / "anchor_report_latest.json"
    anchor_dir = _find_anchor_dir(anchor_base, ts)
    anchor_data = _read_json_dict(anchor_latest_json) if anchor_latest_json.exists() else None
    return anchor_data, anchor_dir


def _compose_anchor_section(lines: list[str], anchor_data: dict | None, anchor_dir: Path | None) -> None:
    _append_section_header(lines, 2, "Anchor Health — Top-Level Markdown Slugs")
    if not anchor_data:
        _append_paragraph(lines, "(no data)")
        return

    metrics = [
        f"strict duplicate count: {anchor_data.get('strict_duplicate_count', 'n/a')}",
        f"baseline (cross_file_duplicates): {anchor_data.get('baseline_cross_file_duplicates', 'n/a')}",
        f"delta vs baseline: {anchor_data.get('delta_vs_baseline', 'n/a')}",
    ]
    _append_list(lines, metrics)

    clusters = anchor_data.get("clusters", []) if isinstance(anchor_data, dict) else []
    formatted = [
        f"`{cluster.get('slug', '?')}` — {cluster.get('file_count', 0)} files"
        for cluster in clusters[:10]
        if isinstance(cluster, dict)
    ]
    _append_section_header(lines, 3, "Largest Remaining Duplicate Slugs (top 10)")
    _append_list(lines, formatted or ["(none)"])

    if anchor_dir:
        _append_paragraph(
            lines,
            f"[Full anchor report](/.repo_studios/anchor_health/{anchor_dir.name}/anchor_report.md)",
        )


def _compose_fault_handler_section(lines: list[str], fh_trends: list[tuple[str, str, float]]) -> None:
    if not fh_trends:
        return
    _append_section_header(lines, 2, "Fault Handler — Trends")
    entries = [f"{name}: {value} {symbol}" for name, symbol, value in fh_trends]
    _append_list(lines, entries)
    _append_paragraph(lines, "[All runs](/.repo_studios/health/faulthandler/trends.json)")


def _compose_repo_insight_section(lines: list[str], trend_excerpt: list[str]) -> None:
    _append_section_header(lines, 2, "Repo Insight — Monkey Patch Trend (preview)")
    if trend_excerpt:
        _append_blockquote(lines, trend_excerpt)
    else:
        _append_paragraph(lines, "(no data)")
    _append_paragraph(
        lines,
        "[Full trend](/.repo_studios/reports/producer_reports/monkey_patch_scans/trend_latest.md)",
    )


def _compose_dependency_section(lines: list[str], summary_text: str, dep_dir: Path | None) -> None:
    _append_section_header(lines, 2, "Dependency Hygiene — Summary")
    _append_paragraph(lines, summary_text or "(no summary)")
    if dep_dir:
        _append_paragraph(
            lines,
            f"[Full report](/.repo_studios/dep_health/{dep_dir.name}/report.md)",
        )


def _compose_import_graph_section(
    lines: list[str],
    fan_in: list[str],
    fan_out: list[str],
    cycles: list[str],
    ig_dir: Path | None,
) -> None:
    _append_section_header(lines, 2, "Import Graph — Hotspots")
    _append_section_header(lines, 3, "Top fan-in (modules most depended on)")
    _append_list(lines, fan_in or ["(none)"])
    _append_section_header(lines, 3, "Top fan-out (modules with many dependencies)")
    _append_list(lines, fan_out or ["(none)"])
    _append_section_header(lines, 3, "Cycles (first 10)")
    _append_list(lines, cycles or ["None detected"])
    if ig_dir:
            _append_paragraph(
                lines,
                f"[Full report](/.repo_studios/reports/producer_reports/healthview/import_graph/{ig_dir.name}/summary.md)",
            )


def _compose_test_health_section(lines: list[str], summary_items: list[str], th_dir: Path | None) -> None:
    _append_section_header(lines, 2, "Test Log Health — Summary")
    _append_list(lines, summary_items)
    if th_dir:
        _append_paragraph(
            lines,
            f"[Full report](/.repo_studios/reports/consumer_reports/test_log_health_reports/{th_dir.name}/report.md)",
        )


def _compose_typecheck_section(
    lines: list[str],
    status: str,
    total_errors: int,
    files_with_issues: int,
    samples: list[str],
    tc_dir: Path | None,
) -> None:
    _append_section_header(lines, 2, "Typecheck — Summary")
    metrics = [
        f"status: {status}",
        f"total errors: {total_errors}",
        f"files with issues: {files_with_issues}",
    ]
    _append_list(lines, metrics)
    _append_section_header(lines, 3, "Top Issues (up to 10)")
    _append_list(lines, samples or ["(none)"])
    if tc_dir:
        _append_paragraph(
            lines,
            f"[Full report](/.repo_studios/typecheck/{tc_dir.name}/report.md)",
        )


def _compose_lizard_section(
    lines: list[str],
    status: str,
    issue_count: int,
    notes: str,
    targets: list[str],
    max_ccn: int | None,
    max_length: int | None,
    offenders: list[tuple[str, str, int, int]],
    lizard_dir: Path | None,
) -> None:
    _append_section_header(lines, 2, "Lizard Complexity — Summary")
    metrics = [f"status: {status}", f"offenders: {issue_count}"]
    if targets:
        metrics.append(f"targets: {' '.join(targets)}")
    if notes:
        metrics.append(f"notes: {notes}")
    if max_ccn is not None and max_length is not None:
        metrics.append(f"thresholds: CCN ≤ {max_ccn}, length ≤ {max_length}")
    _append_list(lines, metrics)
    if offenders:
        _append_section_header(lines, 3, "Top Offenders (up to 10)")
        table_rows = ["| Function | File | CCN | Length |", "|---|---|---:|---:|"]
        for name, file_name, ccn_val, length_val in offenders[:10]:
            table_rows.append(f"| `{name}` | `{file_name}` | {ccn_val} | {length_val} |")
        _append_table(lines, table_rows)
    if lizard_dir:
        _append_paragraph(
            lines,
            f"[Full report](/.repo_studios/lizard/{lizard_dir.name}/report.md)",
        )


def _compose_churn_section(lines: list[str], table_rows: list[str], cc_dir: Path | None) -> None:
    _append_section_header(lines, 2, "Churn × Complexity — Top (up to 10)")
    if table_rows:
        _append_table(lines, table_rows)
    else:
        _append_paragraph(lines, "(none)")
    if cc_dir:
        _append_paragraph(
            lines,
            f"[Full heatmap](/.repo_studios/reports/aggregator_reports/churn_complexity_heatmap/{cc_dir.name}/heatmap.md)",
        )


def run(argv: Iterable[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)
    logger = logging.getLogger("summarize_health_suite")

    timestamp_slug = _timestamp_slug(options.run_timestamp)
    run_slug = _healthview_run_slug(options.run_timestamp)
    repo_root = paths.repo_root

    trend_excerpt, trend_path = _load_trend_head(repo_root)
    dep_summary_text, dep_dir = _load_dep_summary(repo_root, timestamp_slug)
    fan_in, fan_out, cycles, ig_dir = _load_import_graph(repo_root, timestamp_slug)
    th_summary_items, th_dir = _load_test_health_summary(repo_root, timestamp_slug)
    cc_table_rows, cc_dir = _load_churn_table(repo_root, timestamp_slug)
    fh_trends = _load_fault_trends(repo_root)
    tc_status, tc_total_errors, tc_files_with_issues, tc_samples, tc_dir = _load_typecheck_summary(repo_root, timestamp_slug)
    (
        lizard_status,
        lizard_issue_count,
        lizard_notes,
        lizard_targets,
        lizard_max_ccn,
        lizard_max_length,
        lizard_offenders,
        lizard_dir,
    ) = _load_lizard_summary(repo_root, timestamp_slug)
    anchor_data, anchor_dir = _load_anchor_data(repo_root, timestamp_slug)

    notes: list[str] = []
    if not trend_excerpt:
        notes.append("Monkey patch trend preview unavailable; rerun generate_monkey_patch_trend.")
    if dep_dir is None:
        notes.append("Dependency hygiene report not located; rerun the dependency hygiene pipeline.")
    if ig_dir is None:
        notes.append("Import graph report missing; rerun the import graph producer.")
    if th_dir is None:
        notes.append("Test log health summary missing; rerun the test log health consumer.")
    if tc_dir is None:
        notes.append("Typecheck summary missing; rerun the typecheck pipeline.")
    if lizard_dir is None:
        notes.append("Lizard complexity report missing; rerun generate_lizard_report.")
    if cc_dir is None:
        notes.append("Churn × Complexity heatmap missing; rerun the churn complexity aggregator.")
    if anchor_data is None:
        notes.append("Anchor health dataset missing; rerun anchor health pipeline.")

    fault_trends_path = repo_root / ".repo_studios/health/faulthandler/trends.json"
    anchor_latest_json = repo_root / ".repo_studios/anchor_health/anchor_report_latest.json"

    artifact_paths = {
        "monkey_patch_trend": _normalize_relative(trend_path, repo_root),
        "dependency_report": _normalize_relative(dep_dir / "report.md" if dep_dir else None, repo_root),
        "import_graph_report": _normalize_relative(ig_dir / "summary.md" if ig_dir else None, repo_root),
        "test_log_health_report": _normalize_relative(th_dir / "report.md" if th_dir else None, repo_root),
        "churn_complexity_heatmap": _normalize_relative(cc_dir / "heatmap.md" if cc_dir else None, repo_root),
        "fault_trends": _normalize_relative(fault_trends_path if fault_trends_path.exists() else None, repo_root),
        "typecheck_report": _normalize_relative(tc_dir / "report.json" if tc_dir else None, repo_root),
        "lizard_report": _normalize_relative(lizard_dir / "report.json" if lizard_dir else None, repo_root),
        "lizard_raw": _normalize_relative(
            lizard_dir / "raw.json" if lizard_dir and (lizard_dir / "raw.json").exists() else None,
            repo_root,
        ),
        "anchor_report_directory": _normalize_relative(anchor_dir, repo_root),
        "anchor_report_latest": _normalize_relative(anchor_latest_json if anchor_latest_json.exists() else None, repo_root),
    }

    anchor_metrics = None
    anchor_clusters: list[dict[str, Any]] = []
    if isinstance(anchor_data, dict):
        anchor_metrics = {
            "strict_duplicate_count": anchor_data.get("strict_duplicate_count"),
            "baseline_cross_file_duplicates": anchor_data.get("baseline_cross_file_duplicates"),
            "delta_vs_baseline": anchor_data.get("delta_vs_baseline"),
        }
        clusters = anchor_data.get("clusters")
        if isinstance(clusters, list):
            for entry in clusters[:10]:
                if isinstance(entry, dict):
                    anchor_clusters.append(
                        {
                            "slug": entry.get("slug"),
                            "file_count": entry.get("file_count"),
                        }
                    )

    fault_trend_section = [
        {"metric": name, "direction": symbol, "value": value}
        for name, symbol, value in fh_trends
    ]

    lizard_offender_section = [
        {"function": name, "file": file_name, "ccn": ccn_val, "length": length_val}
        for name, file_name, ccn_val, length_val in lizard_offenders[:10]
    ]

    sections = {
        "anchor_health": {
            "metrics": anchor_metrics,
            "top_clusters": anchor_clusters,
            "bundle": anchor_dir.name if anchor_dir else None,
        },
        "fault_handler": {"trends": fault_trend_section},
        "monkey_patch_trend": {"excerpt": trend_excerpt},
        "dependency_hygiene": {"summary": dep_summary_text},
        "import_graph": {"fan_in": fan_in, "fan_out": fan_out, "cycles": cycles},
        "test_log_health": {"summary": th_summary_items},
        "typecheck": {
            "status": tc_status,
            "total_errors": tc_total_errors,
            "files_with_issues": tc_files_with_issues,
            "samples": tc_samples,
        },
        "lizard_complexity": {
            "status": lizard_status,
            "issue_count": lizard_issue_count,
            "notes": lizard_notes,
            "targets": lizard_targets,
            "thresholds": {"max_ccn": lizard_max_ccn, "max_length": lizard_max_length},
            "top_offenders": lizard_offender_section,
        },
        "churn_complexity": {"table_rows": cc_table_rows},
    }

    summary_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "generated_at": options.run_timestamp.isoformat(timespec="seconds"),
        "run_slug": run_slug,
        "timestamp_slug": timestamp_slug,
        "artifacts": artifact_paths,
        "sections": sections,
        "notes": notes,
    }

    lines: list[str] = []
    _append_section_header(lines, 1, "Health Suite Summary")
    lines.append(f"Generated (UTC): {options.run_timestamp.isoformat(timespec='seconds')}")
    lines.append(f"Run slug: {run_slug}")
    lines.append("")

    _compose_anchor_section(lines, anchor_data if isinstance(anchor_data, dict) else None, anchor_dir)
    _compose_fault_handler_section(lines, fh_trends)
    _compose_repo_insight_section(lines, trend_excerpt)
    _compose_dependency_section(lines, dep_summary_text, dep_dir)
    _compose_import_graph_section(lines, fan_in, fan_out, cycles, ig_dir)
    _compose_test_health_section(lines, th_summary_items, th_dir)
    _compose_typecheck_section(
        lines,
        tc_status,
        tc_total_errors,
        tc_files_with_issues,
        tc_samples,
        tc_dir,
    )
    _compose_lizard_section(
        lines,
        lizard_status,
        lizard_issue_count,
        lizard_notes,
        lizard_targets,
        lizard_max_ccn,
        lizard_max_length,
        lizard_offenders,
        lizard_dir,
    )
    _compose_churn_section(lines, cc_table_rows, cc_dir)
    if notes:
        _append_section_header(lines, 2, "Notes")
        _append_list(lines, notes)

    summary_markdown = "\n".join(lines).strip("\n") + "\n"

    artifacts = [
        ReportArtifact(filename=f"{SUMMARY_STEM}.json", kind="json", content=lambda: summary_payload),
        ReportArtifact(filename=f"{SUMMARY_STEM}.md", kind="text", content=lambda: summary_markdown),
    ]
    result: WriteReportArtifactsResult = write_report_artifacts(
        stem=SUMMARY_STEM,
        timestamp=options.run_timestamp,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer=VIEWER_SLUG,
        topic=TOPIC_SLUG,
    )

    legacy_path: Path | None = None
    if options.mirror_legacy:
        legacy_path = paths.legacy_dir / f"{SUMMARY_STEM}_{timestamp_slug}.md"
        legacy_path.write_text(summary_markdown, encoding="utf-8")
        marker = paths.legacy_dir / "MOVED.txt"
        if not marker.exists():
            marker.write_text(
                f"Summaries now emit via write_report_artifacts under {(paths.output_dir / VIEWER_SLUG / TOPIC_SLUG).as_posix()}/\n",
                encoding="utf-8",
            )

    logger.info("Health suite summary artifacts written to %s (slug=%s)", result.run_dir, result.slug)

    response = {
        "status": "ok",
        "run_dir": str(result.run_dir),
        "slug": result.slug,
        "artifacts": {name: str(path) for name, path in result.artifacts.items()},
        "notes": notes,
    }
    if legacy_path is not None:
        response["legacy_markdown"] = str(legacy_path)
    return response


def main(argv: Iterable[str] | None = None) -> None:
    result = run(argv)
    raise SystemExit(0 if result.get("status") == "ok" else 1)


__all__ = ["run", "main", "build_paths", "build_options"]


if __name__ == "__main__":  # pragma: no cover
    main()
