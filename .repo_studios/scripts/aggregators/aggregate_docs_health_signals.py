#!/usr/bin/env python3
"""Aggregate documentation health signals into a consolidated bundle."""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:  # pragma: no cover - import path bootstrap
    sys.path.insert(0, str(SCRIPTS_ROOT))

from utilities.anchor_inventory_loader import load_anchor_inventory  # noqa: E402

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/aggregator_reports/docs_health_signals")
DEFAULT_CHURN_REPORT = Path(".repo_studios/reports/producer_reports/code_doc_churn_reports/latest_report.json")
DEFAULT_UNDOCUMENTED_REPORT = Path(
    ".repo_studios/reports/producer_reports/undocumented_logic_reports/latest_report.json"
)
DEFAULT_ANCHOR_INVENTORY = Path(
    ".repo_studios/reports/producer_reports/healthview/anchor_inventory"
)
DEFAULT_ANCHOR_VALIDATION = Path(
    ".repo_studios/reports/producer_reports/markdown_anchor_validation_reports/latest_report.json"
)
DEFAULT_DOCS_INTEGRITY = Path(
    ".repo_studios/reports/producer_reports/docs_integrity_reports/latest/latest_report.json"
)
DEFAULT_METRICS_STUB = Path(
    ".repo_studios/reports/producer_reports/metrics_anchor_stub_reports/latest/latest_report.json"
)
DEFAULT_PLACEHOLDER_REPORT = Path(
    ".repo_studios/reports/producer_reports/code_placeholder_scans/latest/latest_report.json"
)
DEFAULT_MONKEY_PATCH_REPORT = Path(
    ".repo_studios/reports/producer_reports/monkey_patch_scans/latest/latest_report.json"
)
DEFAULT_ARTIFACTS_TO_KEEP = 5
RUN_STEM = "docs_health_signals"
SCHEMA_VERSION = 1

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:  # pragma: no cover - prefer import when packaged
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    import sys

    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    churn_report: Path
    undocumented_report: Path
    anchor_inventory: Path
    anchor_validation: Path
    docs_integrity: Path
    metrics_stub: Path
    placeholder_report: Path
    monkey_patch_report: Path


@dataclass
class Options:
    artifacts_to_keep: int
    include_hygiene: bool = True


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True, within_repo=True),
        "churn_report": PathSpec(field="churn_report", default=DEFAULT_CHURN_REPORT, within_repo=True),
        "undocumented_report": PathSpec(field="undocumented_report", default=DEFAULT_UNDOCUMENTED_REPORT, within_repo=True),
        "anchor_inventory": PathSpec(field="anchor_inventory", default=DEFAULT_ANCHOR_INVENTORY, within_repo=True),
        "anchor_validation": PathSpec(field="anchor_validation", default=DEFAULT_ANCHOR_VALIDATION, within_repo=True),
        "docs_integrity": PathSpec(field="docs_integrity", default=DEFAULT_DOCS_INTEGRITY, within_repo=True),
        "metrics_stub": PathSpec(field="metrics_stub", default=DEFAULT_METRICS_STUB, within_repo=True),
        "placeholder_report": PathSpec(field="placeholder_report", default=DEFAULT_PLACEHOLDER_REPORT, within_repo=True),
        "monkey_patch_report": PathSpec(field="monkey_patch_report", default=DEFAULT_MONKEY_PATCH_REPORT, within_repo=True),
    },
    repo_root_depth=4,
)

OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


@dataclass
class SignalResult:
    category: str
    title: str
    score: float | None
    status: str
    metrics: dict[str, Any]
    top_findings: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    source_versions: dict[str, Any] = field(default_factory=dict)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--output-dir", help="Output directory for aggregator artifacts")
    parser.add_argument("--churn-report", help="Path to code/doc churn report JSON")
    parser.add_argument("--undocumented-report", help="Path to undocumented logic report JSON")
    parser.add_argument(
        "--anchor-inventory",
        help=(
            "Path to anchor inventory input (canonical topic dir, specific bundle dir containing telemetry.json, "
            "or legacy report.json)"
        ),
    )
    parser.add_argument("--anchor-validation", help="Path to markdown anchor validation report JSON")
    parser.add_argument("--docs-integrity", help="Path to docs integrity report JSON")
    parser.add_argument("--metrics-stub", help="Path to metrics anchor stub validation report JSON")
    parser.add_argument("--placeholder-report", help="Path to code placeholder scan report JSON")
    parser.add_argument("--monkey-patch-report", help="Path to monkey patch scan report JSON")
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention count for timestamped runs",
    )
    parser.add_argument("--skip-hygiene", action="store_true", help="Skip hygiene signal blending")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _load_json(path: Path, label: str, logger: logging.Logger) -> dict[str, Any] | None:
    if not path.exists():
        logger.warning("%s path missing: %s", label, path)
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to parse %s: %s", path, exc)
        return None
    if not isinstance(data, dict):
        logger.warning("%s must be a JSON object: %s", label, path)
        return None
    return data


def _validate_payload(
    payload: dict[str, Any] | None,
    *,
    label: str,
    required_summary_keys: Iterable[str],
    logger: logging.Logger,
) -> None:
    if payload is None:
        return
    summary = payload.get("summary")
    if required_summary_keys and not isinstance(summary, dict):
        logger.warning("%s missing summary block", label)
        return
    if not isinstance(summary, dict):
        return
    missing = sorted(key for key in required_summary_keys if key not in summary)
    if missing:
        logger.warning("%s summary missing keys: %s", label, ", ".join(missing))


def _ratio_score(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 100.0 if numerator <= 0 else 0.0
    ratio = max(0.0, min(1.0, numerator / denominator))
    return ratio * 100.0


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _status_for_score(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 80.0:
        return "healthy"
    if score >= 60.0:
        return "warning"
    return "critical"


def _format_score(score: float | None) -> str:
    return "n/a" if score is None else f"{score:.2f}"


def _compute_freshness(churn: dict[str, Any] | None) -> tuple[float | None, dict[str, Any], list[dict[str, Any]], list[str]]:
    if not churn:
        return None, {}, [], ["Churn report unavailable."]
    summary = churn.get("summary") or {}
    total = int(summary.get("modules_with_code_churn") or 0)
    with_docs = int(summary.get("modules_with_doc_updates") or 0)
    without_docs = int(summary.get("modules_without_doc_updates") or 0)
    allowlisted = list(summary.get("allowlisted_modules") or [])
    score = _ratio_score(with_docs, total if total > 0 else with_docs + without_docs)
    metrics = {
        "modules_with_code_churn": total,
        "modules_with_doc_updates": with_docs,
        "modules_without_doc_updates": without_docs,
        "allowlisted_modules": allowlisted,
    }
    findings: list[dict[str, Any]] = []
    for entry in (churn.get("modules_missing_docs") or [])[:5]:
        module_name = entry.get("module")
        findings.append(
            {
                "module": module_name,
                "code_paths": list(entry.get("code_paths") or []),
                "doc_candidates": [candidate.get("path") for candidate in entry.get("doc_candidates", []) if isinstance(candidate, dict)],
                "last_commit_utc": entry.get("last_commit_utc"),
            }
        )
    notes: list[str] = []
    if total == 0:
        notes.append("No modules with recent code churn; freshness defaults to 100%.")
    if allowlisted:
        notes.append(f"Allowlist suppressed {len(allowlisted)} modules.")
    return _clamp(score), metrics, findings, notes


def _compute_coverage(report: dict[str, Any] | None) -> tuple[float | None, dict[str, Any], list[dict[str, Any]], list[str]]:
    if not report:
        return None, {}, [], ["Undocumented logic report unavailable."]
    summary = report.get("summary") or {}
    coverage = summary.get("docstring_coverage_percent")
    score = float(coverage) if isinstance(coverage, (int, float)) else None
    if score is not None:
        score = _clamp(score)
    metrics = {
        "modules_scanned": int(summary.get("modules_scanned") or 0),
        "modules_with_findings": int(summary.get("modules_with_findings") or 0),
        "entities_scanned": int(summary.get("entities_scanned") or 0),
        "entities_missing_docs": int(summary.get("entities_missing_docs") or 0),
        "docstring_coverage_percent": coverage,
    }
    modules = report.get("modules") or []
    modules_sorted = sorted(
        (module for module in modules if isinstance(module, dict)),
        key=lambda module: len(module.get("findings") or []),
        reverse=True,
    )
    findings: list[dict[str, Any]] = []
    for module in modules_sorted[:5]:
        findings.append(
            {
                "module_path": module.get("module_path"),
                "missing_entities": len(module.get("findings") or []),
                "coverage_percent": module.get("coverage_percent"),
                "doc_candidates": [candidate.get("path") for candidate in module.get("doc_candidates", []) if isinstance(candidate, dict)],
            }
        )
    notes: list[str] = []
    if metrics["entities_scanned"] and metrics["entities_missing_docs"]:
        ratio = metrics["entities_missing_docs"] / max(metrics["entities_scanned"], 1)
        notes.append(f"{ratio:.0%} of scanned entities lack docstrings.")
    return score, metrics, findings, notes


def _compute_structure(
    inventory: dict[str, Any] | None,
    validation: dict[str, Any] | None,
) -> tuple[float | None, dict[str, Any], list[dict[str, Any]], list[str]]:
    if not inventory and not validation:
        return None, {}, [], ["Anchor inventory and validation reports unavailable."]
    summary = inventory.get("summary") if inventory else {}
    total_docs = int((summary or {}).get("total_documents") or 0)
    missing_h1 = int((summary or {}).get("documents_missing_h1") or 0)
    missing_h2 = int((summary or {}).get("documents_missing_h2") or 0)
    duplicates_docs = int((summary or {}).get("documents_with_cross_file_duplicates") or 0)
    repeated_docs = int((summary or {}).get("documents_with_repeated_anchors") or 0)
    cross_file_duplicates = int((summary or {}).get("cross_file_duplicates") or 0)
    total_slugs = int((summary or {}).get("total_slugs") or 0)
    h1_score = _ratio_score(total_docs - missing_h1, total_docs)
    h2_score = _ratio_score(total_docs - missing_h2, total_docs)
    duplicate_penalty = ((duplicates_docs + repeated_docs) / max(total_docs, 1)) * 70.0
    slug_penalty = (cross_file_duplicates / max(total_slugs, 1)) * 40.0
    score = (h1_score + h2_score) / 2.0
    score = max(0.0, score - duplicate_penalty - slug_penalty)
    metrics: dict[str, Any] = {
        "total_documents": total_docs,
        "documents_missing_h1": missing_h1,
        "documents_missing_h2": missing_h2,
        "documents_with_cross_file_duplicates": duplicates_docs,
        "documents_with_repeated_anchors": repeated_docs,
        "cross_file_duplicates": cross_file_duplicates,
        "total_slugs": total_slugs,
    }
    findings: list[dict[str, Any]] = []
    for entry in (summary or {}).get("top_document_roots", [])[:5]:
        if isinstance(entry, dict):
            findings.append({"root": entry.get("root"), "documents": entry.get("count")})
    notes: list[str] = []
    if validation:
        issue_count = int(validation.get("issue_count") or 0)
        metrics["anchor_validation_issue_count"] = issue_count
        metrics["anchor_validation_status"] = validation.get("status")
        if issue_count > 0:
            score = max(0.0, score - 20.0)
            notes.append(f"Markdown anchor validator reported {issue_count} issues.")
    return _clamp(score), metrics, findings, notes


def _compute_integrity(
    docs_integrity: dict[str, Any] | None,
    metrics_stub: dict[str, Any] | None,
) -> tuple[float | None, dict[str, Any], list[dict[str, Any]], list[str]]:
    if not docs_integrity and not metrics_stub:
        return None, {}, [], ["Docs integrity and metrics stub reports unavailable."]
    score = 100.0
    metrics: dict[str, Any] = {}
    findings: list[dict[str, Any]] = []
    notes: list[str] = []
    if docs_integrity:
        summary = docs_integrity.get("summary") or {}
        mismatched = int(summary.get("mismatched_blocks") or 0)
        json_blocks = int(summary.get("json_blocks_checked") or 0)
        documents_processed = int(summary.get("documents_processed") or 0)
        metrics.update(
            {
                "docs_integrity_status": docs_integrity.get("status"),
                "mismatched_blocks": mismatched,
                "json_blocks_checked": json_blocks,
                "documents_processed": documents_processed,
            }
        )
        if mismatched:
            ratio = mismatched / max(json_blocks, 1)
            score = max(0.0, score - min(60.0, ratio * 100.0))
            for entry in docs_integrity.get("mismatches", [])[:5]:
                if isinstance(entry, dict):
                    findings.append(entry)
            notes.append(f"Docs integrity found {mismatched} mismatched blocks.")
        if docs_integrity.get("status") not in {None, "ok"}:
            score = max(0.0, score - 10.0)
            notes.append(f"Integrity status reported as {docs_integrity.get('status')!r}.")
    if metrics_stub:
        summary = metrics_stub.get("summary") or {}
        missing = int(summary.get("missing_count") or 0)
        anchors_referenced = int(summary.get("anchors_referenced") or 0)
        metrics.update(
            {
                "missing_metrics_stubs": missing,
                "anchors_referenced": anchors_referenced,
            }
        )
        if missing:
            score = max(0.0, score - min(30.0, missing * 10.0))
            notes.append(f"Missing {missing} metrics anchor stubs.")
        if metrics_stub.get("missing"):
            findings.extend(metrics_stub.get("missing")[:5])
    return _clamp(score), metrics, findings, notes


def _compute_hygiene(
    placeholder_report: dict[str, Any] | None,
    monkey_report: dict[str, Any] | None,
) -> tuple[float | None, dict[str, Any], list[dict[str, Any]], list[str]]:
    if not placeholder_report and not monkey_report:
        return None, {}, [], ["Hygiene signals unavailable."]
    score = 100.0
    metrics: dict[str, Any] = {}
    findings: list[dict[str, Any]] = []
    notes: list[str] = []
    if placeholder_report:
        total_matches = int(placeholder_report.get("total_matches") or 0)
        metrics["placeholder_total_matches"] = total_matches
        metrics["placeholder_status"] = placeholder_report.get("status")
        score = max(0.0, score - min(40.0, total_matches * 5.0))
        by_pattern = placeholder_report.get("summary", {}).get("by_pattern", {})
        if isinstance(by_pattern, dict) and by_pattern:
            findings.append({"placeholder_by_pattern": dict(list(by_pattern.items())[:5])})
        if total_matches:
            notes.append(f"Placeholder scan surfaced {total_matches} matches.")
    if monkey_report:
        total_findings = int(monkey_report.get("total_findings") or 0)
        metrics["monkey_patch_total_findings"] = total_findings
        metrics["monkey_patch_status"] = monkey_report.get("status")
        score = max(0.0, score - min(40.0, float(total_findings)))
        by_category = monkey_report.get("summary", {}).get("by_category", {})
        if isinstance(by_category, dict) and by_category:
            findings.append({"monkey_patch_by_category": dict(list(by_category.items())[:5])})
        if total_findings:
            notes.append(f"Monkey patch scan reported {total_findings} findings.")
    return _clamp(score), metrics, findings, notes


def _flatten_metrics(metrics: dict[str, Any], category: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for key, value in metrics.items():
        if isinstance(value, (dict, list)):
            value_repr = json.dumps(value, sort_keys=True)
        else:
            value_repr = "" if value is None else str(value)
        rows.append((category, key, value_repr))
    return rows


def _weighted_score(signals: Iterable[SignalResult], weights: dict[str, float]) -> float | None:
    total = 0.0
    weight_sum = 0.0
    for signal in signals:
        weight = weights.get(signal.category, 0.0)
        if signal.score is None or weight <= 0:
            continue
        total += signal.score * weight
        weight_sum += weight
    if weight_sum == 0.0:
        return None
    return total / weight_sum


def _render_markdown(
    *,
    generated_at: datetime,
    summary: dict[str, Any],
    signals: list[SignalResult],
) -> str:
    lines: list[str] = ["# Docs Health Signals", ""]
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append("")
    overall = summary.get("overall_score")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Overall score: {_format_score(overall)}")
    counts = summary.get("status_counts", {})
    if counts:
        lines.append(
            "- Status tally: "
            + ", ".join(f"{name}={value}" for name, value in counts.items())
        )
    lines.append("- Signals scored: " + ", ".join(signal.category for signal in signals))
    lines.append("")
    lines.append("## Signal Details")
    lines.append("")
    for signal in signals:
        lines.append(f"### {signal.title} — {signal.status.title()} ({_format_score(signal.score)})")
        lines.append("")
        if signal.notes:
            lines.append("Notes:")
            lines.append("")
            for note in signal.notes:
                lines.append(f"- {note}")
            lines.append("")
        if signal.metrics:
            lines.append("| Metric | Value |")
            lines.append("| --- | --- |")
            for key, value in signal.metrics.items():
                if isinstance(value, (dict, list)):
                    value_repr = json.dumps(value, sort_keys=True)
                else:
                    value_repr = "" if value is None else str(value)
                lines.append(f"| {key} | {value_repr} |")
            lines.append("")
        if signal.top_findings:
            lines.append("<!-- markdownlint-disable MD013 -->")
            lines.append("Top findings:")
            lines.append("")
            for finding in signal.top_findings:
                value_repr = json.dumps(finding, sort_keys=True)
                lines.append(f"- {value_repr}")
            lines.append("<!-- markdownlint-enable MD013 -->")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_tsv(signals: list[SignalResult]) -> str:
    rows: list[list[str]] = [["category", "metric", "status", "score", "value"]]
    for signal in signals:
        score_str = _format_score(signal.score)
        for category, key, value in _flatten_metrics(signal.metrics, signal.category):
            rows.append([category, key, signal.status, score_str, value])
    return "\n".join("\t".join(row) for row in rows) + "\n"


def _render_csv(signals: list[SignalResult]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["category", "metric", "status", "score", "value"])
    for signal in signals:
        score_str = _format_score(signal.score)
        for category, key, value in _flatten_metrics(signal.metrics, signal.category):
            writer.writerow([category, key, signal.status, score_str, value])
    return buffer.getvalue()


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    _configure_logging(args.log_level)
    logger = logging.getLogger("aggregate_docs_health_signals")

    paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
    options = build_standard_options(args, OPTIONS_CONFIG)
    options.include_hygiene = not args.skip_hygiene

    churn_report = _load_json(paths.churn_report, "churn report", logger)
    undocumented_report = _load_json(paths.undocumented_report, "undocumented logic report", logger)
    anchor_inventory, anchor_inventory_path = load_anchor_inventory(paths.anchor_inventory, logger=logger)
    if anchor_inventory is None:
        logger.warning("anchor inventory path missing or unreadable: %s", paths.anchor_inventory)
    anchor_validation = _load_json(paths.anchor_validation, "markdown anchor validation", logger)
    docs_integrity = _load_json(paths.docs_integrity, "docs integrity", logger)
    metrics_stub = _load_json(paths.metrics_stub, "metrics anchor stub", logger)
    placeholder_report = None
    monkey_report = None
    if options.include_hygiene:
        placeholder_report = _load_json(paths.placeholder_report, "placeholder scan", logger)
        monkey_report = _load_json(paths.monkey_patch_report, "monkey patch scan", logger)

    _validate_payload(
        churn_report,
        label="churn report",
        required_summary_keys=[
            "modules_with_code_churn",
            "modules_with_doc_updates",
            "modules_without_doc_updates",
        ],
        logger=logger,
    )
    _validate_payload(
        undocumented_report,
        label="undocumented logic report",
        required_summary_keys=[
            "modules_scanned",
            "entities_scanned",
            "docstring_coverage_percent",
        ],
        logger=logger,
    )
    _validate_payload(
        anchor_inventory,
        label="anchor inventory",
        required_summary_keys=[
            "total_documents",
            "documents_missing_h1",
            "documents_missing_h2",
        ],
        logger=logger,
    )
    _validate_payload(
        docs_integrity,
        label="docs integrity",
        required_summary_keys=["mismatched_blocks", "json_blocks_checked"],
        logger=logger,
    )
    if options.include_hygiene:
        if placeholder_report is not None and "total_matches" not in placeholder_report:
            logger.warning("placeholder scan missing total_matches field")
        if monkey_report is not None and "total_findings" not in monkey_report:
            logger.warning("monkey patch scan missing total_findings field")

    freshness = _compute_freshness(churn_report)
    coverage = _compute_coverage(undocumented_report)
    structure = _compute_structure(anchor_inventory, anchor_validation)
    integrity = _compute_integrity(docs_integrity, metrics_stub)
    signals_data: list[
        tuple[
            str,
            str,
            tuple[float | None, dict[str, Any], list[dict[str, Any]], list[str]],
            list[tuple[str, dict[str, Any] | None]],
        ]
    ] = [
        (
            "freshness",
            "Freshness",
            freshness,
            [(str(paths.churn_report), churn_report)],
        ),
        (
            "coverage",
            "Coverage",
            coverage,
            [(str(paths.undocumented_report), undocumented_report)],
        ),
        (
            "structure",
            "Structure",
            structure,
            [
                (str(anchor_inventory_path or paths.anchor_inventory), anchor_inventory),
                (str(paths.anchor_validation), anchor_validation),
            ],
        ),
        (
            "integrity",
            "Integrity",
            integrity,
            [
                (str(paths.docs_integrity), docs_integrity),
                (str(paths.metrics_stub), metrics_stub),
            ],
        ),
    ]
    if options.include_hygiene:
        hygiene = _compute_hygiene(placeholder_report, monkey_report)
        signals_data.append(
            (
                "hygiene",
                "Hygiene",
                hygiene,
                [
                    (str(paths.placeholder_report), placeholder_report),
                    (str(paths.monkey_patch_report), monkey_report),
                ],
            )
        )

    signals: list[SignalResult] = []
    for category, title, payload, sources in signals_data:
        score, metrics, findings, notes = payload
        source_versions: dict[str, Any] = {}
        source_paths: list[str] = []
        for source_path, source_payload in sources:
            if source_path:
                source_paths.append(source_path)
            version: Any = None
            if isinstance(source_payload, dict):
                version = source_payload.get("schema_version")
            if source_path:
                source_versions[source_path] = version
        result = SignalResult(
            category=category,
            title=title,
            score=score,
            status=_status_for_score(score),
            metrics=metrics,
            top_findings=findings,
            notes=notes,
            sources=source_paths,
            source_versions=source_versions,
        )
        signals.append(result)

    weights = {"freshness": 0.35, "coverage": 0.35, "structure": 0.15, "integrity": 0.1, "hygiene": 0.05}
    overall_score = _weighted_score(signals, weights)
    generated_at = datetime.now(timezone.utc)

    status_counts: dict[str, int] = {}
    for signal in signals:
        status_counts[signal.status] = status_counts.get(signal.status, 0) + 1

    summary_payload = {
        "overall_score": round(overall_score, 2) if overall_score is not None else None,
        "category_scores": {signal.category: signal.score for signal in signals},
        "statuses": {signal.category: signal.status for signal in signals},
        "status_counts": status_counts,
        "weights": weights,
    }

    provenance = {}
    for signal in signals:
        provenance[signal.category] = {
            "inputs": signal.sources,
            "schema_versions": signal.source_versions,
            "status": signal.status,
            "score": signal.score,
        }

    report_payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at.isoformat(),
        "summary": summary_payload,
        "signals": {
            signal.category: {
                "title": signal.title,
                "status": signal.status,
                "score": signal.score,
                "metrics": signal.metrics,
                "top_findings": signal.top_findings,
                "notes": signal.notes,
            }
            for signal in signals
        },
        "provenance": provenance,
    }

    markdown_payload = _render_markdown(generated_at=generated_at, summary=summary_payload, signals=signals)
    tsv_payload = _render_tsv(signals)
    csv_payload = _render_csv(signals)
    bundle_summary = {
        "overall_score": summary_payload["overall_score"],
        "statuses": summary_payload["statuses"],
        "category_scores": summary_payload["category_scores"],
    }

    artifacts = [
        ReportArtifact(filename="report.json", pointer="latest_report.json", kind="json", content=report_payload),
        ReportArtifact(filename="report.md", pointer="latest_report.md", kind="text", content=markdown_payload),
        ReportArtifact(filename="signals.tsv", pointer="latest_signals.tsv", kind="text", content=tsv_payload),
        ReportArtifact(filename="signals.csv", pointer="latest_signals.csv", kind="text", content=csv_payload),
        ReportArtifact(
            filename="bundle_summary.json",
            pointer="latest_bundle_summary.json",
            kind="json",
            content=bundle_summary,
        ),
    ]

    write_result = write_report_artifacts(
        stem=RUN_STEM,
        timestamp=generated_at,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    logging.info("Docs health overall score: %s", _format_score(summary_payload["overall_score"]))

    return {
        "run_dir": str(write_result.run_dir),
        "report_json": str(write_result.artifacts["report.json"]),
        "report_md": str(write_result.artifacts["report.md"]),
        "signals_tsv": str(write_result.artifacts["signals.tsv"]),
        "signals_csv": str(write_result.artifacts["signals.csv"]),
        "bundle_summary": str(write_result.artifacts["bundle_summary.json"]),
        "summary": summary_payload,
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
