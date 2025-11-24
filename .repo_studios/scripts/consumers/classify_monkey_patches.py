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
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_STRUCTURED_ROOT = Path(
    ".repo_studios/reports/producer_reports/monkey_patch_scans"
)
LEGACY_ROOT = Path(".repo_studios/monkey_patch")
LEGACY_REPORT_NAME = "report.json"
STRUCTURED_MATCHES_NAME = "matches.json"


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
            raise FileNotFoundError(
                f"Scan directory {explicit_scan} is missing expected artifacts"
            )
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
    if f.category in {"sys_modules_assignment", "import_time_side_effect"} and not f.is_test:
        return "HIGH"
    if f.category == "global_env_mutation" and (not f.is_test) and f.is_module_scope:
        return "HIGH"
    if f.category == "attribute_reassignment_on_import" and (not f.is_test):
        return "MODERATE"
    if f.category == "global_env_mutation" and f.is_test:
        return "MODERATE"
    return "SAFE"


def aggregate(findings: Iterable[Finding], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    findings_list = list(findings)
    buckets: dict[str, list[Finding]] = defaultdict(list)
    for f in findings_list:
        buckets[classify(f)].append(f)
    counts = {k: len(v) for k, v in buckets.items()}

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
        "run_metadata": metadata or {},
    }


def write_outputs(scan_dir: Path, agg: dict[str, Any]) -> None:
    # JSON
    with (scan_dir / "RISK_SUMMARY.json").open("w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)
    # Markdown
    md = ["# Monkey-Patch Risk Summary", ""]
    total = agg.get("total_findings")
    if total is not None:
        md.append(f"- Total Findings: {int(total)}")
        md.append("")
    md.append("## Counts by Risk")
    counts = agg["counts_by_risk"]
    for level in ("HIGH", "MODERATE", "SAFE"):
        md.append(f"- {level}: {int(counts.get(level, 0))}")
    md.append("")
    md.append("## Top Files")
    for file, count in agg["top_files"]:
        md.append(f"- {file}: {count}")
    md.append("")
    md.append("## Top Categories")
    for cat, count in agg["top_categories"]:
        md.append(f"- {cat}: {count}")
    (scan_dir / "RISK_SUMMARY.md").write_text("\n".join(md) + "\n", encoding="utf-8")


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
        "--output-dir",
        type=Path,
        help="Directory for risk summary outputs (defaults to scan directory)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Increase logging verbosity",
    )
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    scan_dir = _resolve_latest_scan(
        explicit_scan=args.scan_dir,
        base_dir=args.base_dir,
        default_roots=[DEFAULT_STRUCTURED_ROOT, LEGACY_ROOT],
    )

    findings, metadata = _load_structured_findings(scan_dir)
    if not findings:
        legacy_report = scan_dir / LEGACY_REPORT_NAME
        if legacy_report.exists():
            findings = _load_legacy_findings(legacy_report)
            metadata = None
        else:
            raise FileNotFoundError(
                f"No {STRUCTURED_MATCHES_NAME} or legacy {LEGACY_REPORT_NAME} found in {scan_dir}"
            )

    result = aggregate(findings, metadata)
    output_dir = args.output_dir or scan_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_outputs(output_dir, result)
    logging.info("Wrote risk summary to %s", output_dir)
    result.update({"scan_dir": str(scan_dir), "output_dir": str(output_dir)})
    return result


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
