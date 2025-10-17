#!/usr/bin/env python3
"""
compare_monkey_patch_trends.py — Summarize deltas across monkey‑patch scans.

Reads timestamped scan outputs under .repo_studios/monkey_patch/<TS>/report.json
and generates a compact trend summary comparing the latest two scans, plus an optional
multi-scan overview. Outputs a Markdown summary and a JSON with computed stats.

Usage examples:
  python .repo_studios/compare_monkey_patch_trends.py
  python .repo_studios/compare_monkey_patch_trends.py \
    --base-dir .repo_studios/monkey_patch --max-scans 5 --recent-n 5 --verbose

Outputs:
  - <base-dir>/trend_latest.md       (overview + latest vs previous delta)
  - <base-dir>/trend_latest.json     (machine-readable stats)
  - <latest-scan-dir>/trend.md       (same summary co-located with latest scan)

Exit codes: 0 on success; 1 on error or if fewer than 2 scans found (still writes overview).
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BASE_DIR_DEFAULT = Path(".repo_studios/monkey_patch")
REPORT_NAME = "report.json"


@dataclass
class Scan:
    ts: str
    dir: Path
    findings: list[dict[str, Any]]


def _find_scans(base_dir: Path) -> list[Scan]:
    scans: list[Scan] = []
    if not base_dir.exists():
        return scans
    for child in sorted(base_dir.iterdir()):
        if not child.is_dir():
            continue
        rep = child / REPORT_NAME
        if not rep.exists():
            continue
        try:
            data = json.loads(rep.read_text(encoding="utf-8", errors="ignore"))
            if not isinstance(data, list):
                continue
            scans.append(Scan(ts=child.name, dir=child, findings=data))
        except Exception:
            continue
    scans.sort(key=lambda s: s.ts)
    return scans


def _agg_counts(findings: list[dict[str, Any]]) -> tuple[Counter, Counter, Counter]:
    by_cat: Counter[str] = Counter()
    by_import: Counter[str] = Counter()
    by_file: Counter[str] = Counter()
    for f in findings:
        by_cat[f.get("category") or "<unknown>"] += 1
        base = f.get("import_base") or "<none>"
        by_import[str(base)] += 1
        by_file[str(f.get("file") or "<unknown>")] += 1
    return by_cat, by_import, by_file


def _agg_policy_counts(findings: list[dict[str, Any]]) -> tuple[int, Counter, Counter, Counter]:
    """Aggregate counts for policy evaluation.

    Current policy: consider only non-test files (is_test == False).
    This focuses hygiene on runtime/production code and avoids inflating counts
    from test fixtures that intentionally patch behavior.
    """
    filtered = [f for f in findings if not bool(f.get("is_test"))]
    by_cat, by_import, by_file = _agg_counts(filtered)
    return len(filtered), by_cat, by_import, by_file


def _fmt_table(rows: list[tuple[str, int, int, int]], headers: tuple[str, str, str, str]) -> str:
    # Simple monospace table
    out = []
    out.append(f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} |")
    out.append("|---|---:|---:|---:|")
    for name, prev, cur, delta in rows:
        sign = "+" if delta > 0 else ("" if delta == 0 else "-")
        out.append(f"| {name} | {prev} | {cur} | {sign}{abs(delta)} |")
    return "\n".join(out)


def _mk_summary(scans: list[Scan]) -> dict[str, Any]:
    summary: dict[str, Any] = {"scans": [], "latest_vs_prev": None}
    for s in scans:
        by_cat, _, _ = _agg_counts(s.findings)
        policy_total, policy_by_cat, _, _ = _agg_policy_counts(s.findings)
        summary["scans"].append(
            {
                "ts": s.ts,
                "dir": str(s.dir),
                "total": len(s.findings),
                "by_category": dict(by_cat),
                # Policy-focused metrics (non-test only)
                "policy_total": policy_total,
                "policy_by_category": dict(policy_by_cat),
            }
        )
    if len(scans) < 2:
        return summary
    prev, cur = scans[-2], scans[-1]
    p_cat, p_imp, p_file = _agg_counts(prev.findings)
    c_cat, c_imp, c_file = _agg_counts(cur.findings)
    # Policy (non-test) aggregates
    p_policy_total, p_policy_cat, _, _ = _agg_policy_counts(prev.findings)
    c_policy_total, c_policy_cat, _, _ = _agg_policy_counts(cur.findings)
    # Build rows sorted by |delta| desc
    all_cats = sorted(set(p_cat) | set(c_cat))
    rows = []
    for cat in all_cats:
        pv, cv = p_cat.get(cat, 0), c_cat.get(cat, 0)
        rows.append((cat, pv, cv, cv - pv))
    rows.sort(key=lambda r: abs(r[3]), reverse=True)

    # Top import_base deltas (increases preferred)
    all_imps = set(p_imp) | set(c_imp)
    imp_rows = []
    for name in all_imps:
        pv, cv = p_imp.get(name, 0), c_imp.get(name, 0)
        if pv != cv:
            imp_rows.append((name, pv, cv, cv - pv))
    imp_rows.sort(key=lambda r: r[3], reverse=True)

    # Top files with largest increases
    all_files = set(p_file) | set(c_file)
    file_rows = []
    for name in all_files:
        pv, cv = p_file.get(name, 0), c_file.get(name, 0)
        if pv != cv:
            file_rows.append((name, pv, cv, cv - pv))
    file_rows.sort(key=lambda r: r[3], reverse=True)

    summary["latest_vs_prev"] = {
        "prev": {
            "ts": prev.ts,
            "total": len(prev.findings),
            "policy_total": p_policy_total,
        },
        "cur": {
            "ts": cur.ts,
            "total": len(cur.findings),
            "policy_total": c_policy_total,
        },
        "by_category_rows": rows,
        "top_import_deltas": imp_rows[:15],
        "top_file_deltas": file_rows[:15],
        # Policy category deltas (non-test)
        "policy_by_category_rows": [
            (
                cat,
                p_policy_cat.get(cat, 0),
                c_policy_cat.get(cat, 0),
                c_policy_cat.get(cat, 0) - p_policy_cat.get(cat, 0),
            )
            for cat in sorted(set(p_policy_cat) | set(c_policy_cat))
        ],
    }
    return summary


def _write_markdown(
    base_dir: Path, latest_dir: Path, summary: dict[str, Any], recent_n: int = 5
) -> None:
    # Use timezone-aware UTC timestamp; ensure Z suffix for UTC
    now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    scans = summary.get("scans", [])
    latest_vs = summary.get("latest_vs_prev")

    lines: list[str] = []
    lines.append("# Monkey Patch Trend Summary")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    if not scans:
        lines.append("No scans found under base directory.")
    else:
        lines.append("## Scans Overview")
        lines.append("")
        # Recent N table (compact view)
        recent = scans[-recent_n:]
        lines.append(f"Showing last {len(recent)} scans (most recent last):")
        lines.append("")
        lines.append("| Timestamp | Total | Δ vs prev |")
        lines.append("|---|---:|---:|")
        for idx, s in enumerate(recent):
            if idx == 0 and len(scans) == 1:
                delta = "n/a"
            else:
                prev_total = (
                    (recent[idx - 1]["total"])
                    if idx > 0
                    else (scans[-(len(recent) + 1)]["total"] if len(scans) > len(recent) else None)
                )
                delta = "n/a" if prev_total is None else f"{s['total'] - prev_total:+d}"
            lines.append(f"| {s['ts']} | {s['total']} | {delta} |")
        lines.append("")
        # Keep a short bullet list as well for quick skim (up to 10)
        for s in scans[-10:]:
            lines.append(f"- {s['ts']}: total={s['total']}")
        lines.append("")
    if latest_vs:
        prev = latest_vs["prev"]["ts"]
        cur = latest_vs["cur"]["ts"]
        lines.append(f"## Latest vs Previous\n\n- prev: {prev}\n- curr: {cur}")
        lines.append("")
        # Category table
        cat_rows = latest_vs.get("by_category_rows", [])
        lines.append("### By Category")
        lines.append(_fmt_table(cat_rows, ("Category", "Prev", "Curr", "Δ")))
        lines.append("")
        # Policy metric (non-test) category table
        policy_rows = latest_vs.get("policy_by_category_rows", [])
        if policy_rows:
            lines.append("### Policy (non-test only) — By Category")
            lines.append(_fmt_table(policy_rows, ("Category", "Prev", "Curr", "Δ")))
            lines.append("")
        # Top import_base increases
        imp_rows = latest_vs.get("top_import_deltas", [])
        if imp_rows:
            lines.append("### Top import_base increases")
            lines.append(_fmt_table(imp_rows, ("import_base", "Prev", "Curr", "Δ")))
            lines.append("")
        # Top file increases
        file_rows = latest_vs.get("top_file_deltas", [])
        if file_rows:
            lines.append("### Files with largest increases")
            lines.append(_fmt_table(file_rows, ("file", "Prev", "Curr", "Δ")))
            lines.append("")
    else:
        lines.append("Note: fewer than two scans available; add another scan to see deltas.")

    # Write outputs
    trend_latest_md = base_dir / "trend_latest.md"
    trend_latest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (latest_dir / "trend.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # JSON
    trend_latest_json = base_dir / "trend_latest.json"
    trend_latest_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Compare monkey‑patch scans and summarize deltas.")
    p.add_argument("--base-dir", default=str(BASE_DIR_DEFAULT), help="Base directory with scans")
    p.add_argument("--max-scans", type=int, default=20, help="Max scans to load (sorted by ts)")
    p.add_argument(
        "--recent-n", type=int, default=5, help="Show a compact table for the last N scans"
    )
    p.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    # Resolve base dir relative to repo root when not absolute
    base_dir = Path(args.base_dir)
    if not base_dir.is_absolute():
        base_dir = Path.cwd() / base_dir
    scans = _find_scans(base_dir)
    if not scans:
        logging.warning("No scans found under %s", base_dir)
        return 1
    if len(scans) > args.max_scans:
        scans = scans[-args.max_scans :]

    summary = _mk_summary(scans)
    latest_dir = scans[-1].dir
    _write_markdown(base_dir, latest_dir, summary, recent_n=max(1, args.recent_n))

    if len(scans) < 2:
        logging.warning("Only one scan present; wrote overview without deltas.")
        return 1
    logging.info("Trend written: %s / trend_latest.md and %s", base_dir, latest_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
