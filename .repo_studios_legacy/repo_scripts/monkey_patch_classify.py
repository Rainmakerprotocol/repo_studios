#!/usr/bin/env python3
"""
Monkey-Patch Risk Classifier

Reads the latest scan output under .repo_studios/monkey_patch/<ts>/report.json
and writes a risk-classified summary to RISK_SUMMARY.md + RISK_SUMMARY.json in the same folder.

Risk levels
- HIGH: sys_modules_assignment, import_time_side_effect (non-test), global_env_mutation (non-test, module-scope)
- MODERATE: attribute_reassignment_on_import (non-test), global_env_mutation (tests)
- SAFE: attribute_reassignment_on_import (tests only)

Exit 0 always; this script is for reporting. Enforcement is handled by the ratchet.
"""

from __future__ import annotations

import json
import logging
import os
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCAN_ROOT = Path(".repo_studios/monkey_patch")


def latest_scan_dir(root: Path) -> Path:
    subdirs = [p for p in root.iterdir() if p.is_dir() and p.name[0].isdigit()]
    if not subdirs:
        raise FileNotFoundError(f"No scan dirs under {root}")
    return sorted(subdirs)[-1]


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


def load_findings(report_path: Path) -> list[Finding]:
    with report_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [Finding.from_obj(x) for x in data]


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


def aggregate(findings: Iterable[Finding]) -> dict[str, Any]:
    buckets: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        buckets[classify(f)].append(f)
    counts = {k: len(v) for k, v in buckets.items()}

    # Top files by count
    file_counts = Counter(f.file for f in findings)
    top_files = file_counts.most_common(10)

    # Top categories
    cat_counts = Counter(f.category for f in findings).most_common()

    return {
        "counts_by_risk": counts,
        "top_files": top_files,
        "top_categories": cat_counts,
    }


def write_outputs(scan_dir: Path, agg: dict[str, Any]) -> None:
    # JSON
    with (scan_dir / "RISK_SUMMARY.json").open("w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)
    # Markdown
    md = ["# Monkey-Patch Risk Summary", ""]
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


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    root = Path(os.environ.get("MONKEY_DIR", str(SCAN_ROOT)))
    scan_dir = latest_scan_dir(root)
    report = scan_dir / "report.json"
    findings = load_findings(report)
    agg = aggregate(findings)
    write_outputs(scan_dir, agg)
    # Emit a compact machine-readable line for caller
    import sys

    sys.stdout.write(json.dumps({"status": "OK", "dir": str(scan_dir), **agg}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
