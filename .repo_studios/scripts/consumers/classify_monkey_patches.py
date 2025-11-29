#!/usr/bin/env python3
"""Monkey-Patch Risk Classifier.

This consumer prefers structured producer artifacts emitted in
``.repo_studios/reports/producer_reports/monkey_patch_scans/<run-id>/`` and falls
back to the legacy alias under ``.repo_studios/monkey_patch/<run-id>/`` when
needed. It locates the latest run (unless an explicit path is provided), reads
the scan matches, classifies risk, and emits ``RISK_SUMMARY.json`` and
``RISK_SUMMARY.md`` alongside the scan artifacts.

Risk levels:

- HIGH: ``sys_modules_assignment``, ``import_time_side_effect`` (non-test),
  ``global_env_mutation`` (non-test, module scope)
- MODERATE: ``attribute_reassignment_on_import`` (non-test),
  ``global_env_mutation`` (tests)
- SAFE: ``attribute_reassignment_on_import`` (tests only)

Exit 0 always; this script is for reporting. Enforcement is handled by the
ratchet.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
UTILITIES_ROOT = Path(__file__).resolve().parents[2]
for candidate in (SCRIPTS_ROOT, UTILITIES_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

ROOT = Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str and root_str not in sys.path:
    sys.path.insert(0, root_str)

COMMAND_CENTER_ROOT = ROOT / "command_center" / "scripts"
command_center_root_str = str(COMMAND_CENTER_ROOT)
if command_center_root_str and command_center_root_str not in sys.path:
    sys.path.insert(0, command_center_root_str)

from utilities.monkey_patch_risk import (  # noqa: E402
    FindingSignals,
    classify_monkey_patch as classify_monkey_patch_from_signals,
)
from command_center.scripts.libraries import prune_run_directories  # noqa: E402

DEFAULT_STRUCTURED_ROOT = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
LEGACY_ROOT = Path(".repo_studios/monkey_patch")
LEGACY_REPORT_NAME = "report.json"
STRUCTURED_MATCHES_NAME = "matches.json"
DEFAULT_OUTPUT_BASE = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")
DEFAULT_ARTIFACTS_TO_KEEP = 10
BUNDLE_PREFIX = "monkey_patch_risk-"


class NoScansFoundError(FileNotFoundError):
    """Raised when no scan runs are available."""


def _is_scan_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    if path.name.startswith("latest"):
        return False
    if (path / STRUCTURED_MATCHES_NAME).exists():
        return True
    legacy_report = path / LEGACY_REPORT_NAME
    if legacy_report.exists():
        try:
            data = json.loads(legacy_report.read_text(encoding="utf-8"))
        except Exception:
            return False
        return isinstance(data, list)
    return False


def _scan_dirs(base_dir: Path) -> list[Path]:
    if not base_dir.exists():
        return []
    candidates = [child for child in base_dir.iterdir() if _is_scan_dir(child)]
    candidates.sort(key=lambda p: p.name)
    return candidates


def _resolve_latest_scan(
    *,
    explicit_scan: Path | None,
    base_dir: Path | None,
    default_roots: Sequence[Path],
) -> Path:
    if explicit_scan is not None:
        if not _is_scan_dir(explicit_scan):
            raise FileNotFoundError(f"Scan directory {explicit_scan} is missing expected artifacts")
        return explicit_scan

    candidate_roots: list[Path] = []
    if base_dir is not None:
        candidate_roots.append(base_dir)
    else:
        env_value = os.environ.get("MONKEY_DIR")
        if env_value:
            env_path = Path(env_value)
            if _is_scan_dir(env_path):
                return env_path
            candidate_roots.append(env_path)
        candidate_roots.extend(default_roots)

    for root in candidate_roots:
        scans = _scan_dirs(root)
        if scans:
            return scans[-1]
    raise NoScansFoundError("No monkey patch scans found in configured locations.")


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    category: str
    is_test: bool
    is_module_scope: bool
    import_base: str | None

    @staticmethod
    def from_obj(o: dict[str, Any]) -> Finding:
        return Finding(
            file=o.get("file", ""),
            line=int(o.get("line", 0)),
            category=str(o.get("category", "unknown")),
            is_test=bool(o.get("is_test", False)),
            is_module_scope=bool(o.get("is_module_scope", False)),
            import_base=o.get("import_base"),
        )


def _load_structured_findings(run_dir: Path) -> tuple[list[Finding], dict[str, Any] | None]:
    matches_path = run_dir / STRUCTURED_MATCHES_NAME
    if not matches_path.exists():
        return [], None
    raw = json.loads(matches_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{matches_path} must contain a list of findings")
    metadata: dict[str, Any] | None = None
    report_path = run_dir / LEGACY_REPORT_NAME
    if report_path.exists():
        try:
            maybe_meta = json.loads(report_path.read_text(encoding="utf-8"))
            if isinstance(maybe_meta, dict):
                metadata = maybe_meta
        except Exception:
            metadata = None
    return [Finding.from_obj(obj) for obj in raw], metadata


def _load_legacy_findings(report_path: Path) -> list[Finding]:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Legacy report.json must contain a list of findings")
    return [Finding.from_obj(obj) for obj in data]


def classify(f: Finding) -> str:
    return classify_monkey_patch_from_signals(
        FindingSignals(
            category=f.category,
            is_test=f.is_test,
            is_module_scope=f.is_module_scope,
        )
    )


def aggregate(findings: Iterable[Finding], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    findings_list = list(findings)
    buckets: dict[str, list[Finding]] = defaultdict(list)
    for f in findings_list:
        buckets[classify(f)].append(f)
    counts = {k: len(v) for k, v in buckets.items()}
    high_category_counts = Counter(f.category for f in buckets.get("HIGH", []))

    # Top files by count
    file_counts = Counter(f.file for f in findings_list)
    top_files = file_counts.most_common(10)

    # Top categories
    cat_counts = Counter(f.category for f in findings_list).most_common()

    return {
        "total_findings": len(findings_list),
        "counts_by_risk": counts,
        "top_files": top_files,
        "top_categories": cat_counts,
        "high_risk_categories": high_category_counts.most_common(),
        "run_metadata": metadata or {},
    }


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _render_markdown(agg: dict[str, Any], *, generated: datetime | None = None) -> str:
    md: list[str] = ["# Monkey-Patch Risk Summary", ""]
    if generated is not None:
        md.append(f"Generated (UTC): {generated.isoformat(timespec='seconds')}")
        md.append("")
    total = agg.get("total_findings")
    if total is not None:
        md.append(f"- Total Findings: {int(total)}")
        md.append("")
    md.append("## Counts by Risk")
    md.append("")
    counts = agg["counts_by_risk"]
    for level in ("HIGH", "MODERATE", "SAFE"):
        md.append(f"- {level}: {int(counts.get(level, 0))}")
    md.append("")
    md.append("## Top Files")
    md.append("")
    for file, count in agg["top_files"]:
        md.append(f"- {file}: {count}")
    md.append("")
    md.append("## Top Categories")
    md.append("")
    for cat, count in agg["top_categories"]:
        md.append(f"- {cat}: {count}")
    high_risk = agg.get("high_risk_categories")
    if high_risk:
        md.append("")
        md.append("## High-Risk Focus")
        md.append("")
        for cat, count in high_risk:
            md.append(f"- {cat}: {count}")
    return "\n".join(md) + "\n"


def _write_legacy_outputs(scan_dir: Path, agg: dict[str, Any]) -> None:
    scan_dir.mkdir(parents=True, exist_ok=True)
    (scan_dir / "RISK_SUMMARY.json").write_text(json.dumps(agg, indent=2) + "\n", encoding="utf-8")
    (scan_dir / "RISK_SUMMARY.md").write_text(_render_markdown(agg), encoding="utf-8")


def _write_consumer_bundle(
    *,
    scan_dir: Path,
    agg: dict[str, Any],
    output_base: Path,
    source: str,
    producer_report: Path | None,
    keep: int,
    logger: logging.Logger | None,
) -> tuple[Path, Path, list[Path]]:
    output_base.mkdir(parents=True, exist_ok=True)
    ts = _utcnow()
    bundle_dir = output_base / f"{BUNDLE_PREFIX}{ts.strftime('%Y-%m-%d_%H%M%S')}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    summary_path = bundle_dir / "summary.json"
    summary_path.write_text(json.dumps(agg, indent=2) + "\n", encoding="utf-8")

    md_path = bundle_dir / "SUMMARY.md"
    markdown = _render_markdown(agg, generated=ts)
    md_lines = markdown.rstrip("\n").splitlines()
    if md_lines and md_lines[-1] != "":
        md_lines.append("")
    md_lines.append("## Source References")
    md_lines.append("")
    md_lines.append(f"- Source Type: {source}")
    md_lines.append(f"- Scan Directory: `{scan_dir.resolve()}`")
    if producer_report:
        md_lines.append(f"- Producer Report: `{producer_report.resolve()}`")
    md_lines.append(f"- Consumer Bundle: `{bundle_dir.resolve()}`")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    bundle_summary = {
        "schema_version": 1,
        "generated_at": ts.isoformat(timespec="seconds"),
        "source": source,
        "scan_dir": str(scan_dir.resolve()),
        "producer_report": str(producer_report.resolve()) if producer_report else None,
        "artifacts": {
            "summary_json": str(summary_path.resolve()),
            "summary_md": str(md_path.resolve()),
        },
        "counts_by_risk": agg.get("counts_by_risk"),
        "top_files": agg.get("top_files"),
        "top_categories": agg.get("top_categories"),
        "run_metadata": agg.get("run_metadata", {}),
    }
    bundle_summary_path = bundle_dir / "bundle_summary.json"
    bundle_summary_path.write_text(json.dumps(bundle_summary, indent=2) + "\n", encoding="utf-8")

    _update_latest(output_base, bundle_dir, ["summary.json", "SUMMARY.md", "bundle_summary.json"])
    pruned = _prune_history(output_base, keep=keep, current=bundle_dir, logger=logger)
    return bundle_dir, bundle_summary_path, pruned


def _update_latest(base: Path, bundle_dir: Path, filenames: list[str]) -> None:
    for name in filenames:
        src = bundle_dir / name
        dest = base / f"latest_{name}"
        try:
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            dest.hardlink_to(src)
        except Exception:
            dest.write_bytes(src.read_bytes())


def _prune_history(base: Path, *, keep: int | None, current: Path, logger: logging.Logger | None) -> list[Path]:
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
        base,
        keep=keep_count,
        stem_prefix=BUNDLE_PREFIX,
        current_run=current,
        logger=logger,
    )
    return result.removed


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify monkey patch risk levels.")
    parser.add_argument(
        "--scan-dir",
        type=Path,
        help="Explicit scan directory containing matches/report artifacts",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Directory that holds timestamped monkey patch scan runs",
    )
    parser.add_argument(
        "--output-base",
        type=Path,
        default=None,
        help="Directory for structured consumer bundles (defaults to .repo_studios/reports/consumer_reports/monkey_patch_risk)",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of consumer bundles to retain (including the newest run)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging verbosity (e.g. INFO, DEBUG)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Increase logging verbosity (alias for --log-level DEBUG)",
    )
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    log_level = logging.DEBUG if args.verbose else getattr(logging, str(args.log_level).upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s", force=True)
    logger = logging.getLogger("classify_monkey_patches")

    scan_dir = _resolve_latest_scan(
        explicit_scan=args.scan_dir,
        base_dir=args.base_dir,
        default_roots=[DEFAULT_STRUCTURED_ROOT, LEGACY_ROOT],
    )

    findings, metadata = _load_structured_findings(scan_dir)
    source = "structured" if findings else "legacy"
    if not findings:
        legacy_report = scan_dir / LEGACY_REPORT_NAME
        if legacy_report.exists():
            findings = _load_legacy_findings(legacy_report)
            metadata = None
            source = "legacy"
        else:
            raise FileNotFoundError(f"No {STRUCTURED_MATCHES_NAME} or legacy {LEGACY_REPORT_NAME} found in {scan_dir}")

    result = aggregate(findings, metadata)
    _write_legacy_outputs(scan_dir, result)

    output_base = args.output_base or DEFAULT_OUTPUT_BASE
    if not output_base.is_absolute():
        output_base = Path.cwd() / output_base
    producer_report_path = scan_dir / LEGACY_REPORT_NAME
    if not producer_report_path.exists():
        producer_report_path = None
    bundle_dir, bundle_summary, pruned = _write_consumer_bundle(
        scan_dir=scan_dir,
        agg=result,
        output_base=output_base,
        source=source,
        producer_report=producer_report_path,
        keep=args.artifacts_to_keep,
        logger=logger,
    )
    logger.info(
        "Wrote monkey patch risk bundle to %s (source=%s, pruned=%d)",
        bundle_dir,
        source,
        len(pruned),
    )
    return {
        "scan_dir": str(scan_dir.resolve()),
        "bundle_dir": str(bundle_dir.resolve()),
        "bundle_summary": str(bundle_summary.resolve()),
        "output_base": str(output_base.resolve()),
        "source": source,
        "pruned": [str(p.resolve()) for p in pruned],
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run(argv)
    except NoScansFoundError as exc:
        logging.error(str(exc))
        return 1
    except Exception as exc:  # pragma: no cover - unexpected runtime failures
        logging.exception("Failed to classify monkey patch risk: %s", exc)
        return 1

    import sys

    payload = {"status": "OK", **result}
    sys.stdout.write(json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
