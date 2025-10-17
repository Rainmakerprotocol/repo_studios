"""Anchor Health Report Generator.

Generates a machine + human consumable snapshot of top-level (H1/H2) markdown
anchor slug duplication across the `docs/` tree. Intended to integrate with
AI assistance workflows so agents can:

1. Detect drift vs the committed baseline (`tests/docs/anchor_slug_baseline.json`).
2. See which slugs are still duplicated, their file membership, and cluster sizes.
3. Recommend the next slugs to collapse (largest clusters first) while respecting
   canonical file choices recorded in an optional mapping file.
4. Emit artifacts for dashboards / summaries: JSON + compact markdown.

Outputs (by default under `.repo_studios/anchor_health/`):
  - anchor_report_latest.json
  - anchor_report_latest.md

Exit code is 0 even if duplicates exist (pipeline decides policy). Use the JSON
field `strict_duplicate_count` to gate if desired.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,2})\s+(.*)$")
GENERIC_ALLOWED = {"overview", "introduction", "faq", "notes"}
BASELINE_PATH = Path("tests/docs/anchor_slug_baseline.json")
# Permanent root for anchor health artifacts (contains latest + historical runs)
OUTPUT_DIR = Path(".repo_studios/anchor_health")

# Subfolder naming pattern: anchor_health-YYYY-MM-DD_hhmm
RUN_PREFIX = "anchor_health-"


def _slugify(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"`+", "", s)
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


@dataclass
class Cluster:
    slug: str
    files: set[str]

    @property
    def file_count(self) -> int:  # pragma: no cover - trivial
        return len(self.files)


def collect_h1_h2_slugs(skip: set[str] | None = None) -> dict[str, list[str]]:
    root = Path("docs")
    assert root.exists(), "docs directory missing"
    mapping: dict[str, list[str]] = {}
    for md in root.rglob("*.md"):
        if any(p in md.parts for p in ("coverage_history",)):
            continue
        for lineno, line in enumerate(md.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = HEADING_RE.match(line)
            if not m:
                continue
            if len(m.group(1)) > 2:
                continue
            slug = _slugify(m.group(2))
            if skip and slug in skip:
                continue
            mapping.setdefault(slug, []).append(f"{md}:{lineno}")
    return mapping


def multi_file_duplicates(slug_map: dict[str, list[str]]) -> dict[str, list[str]]:
    dupes: dict[str, list[str]] = {}
    for slug, locs in slug_map.items():
        files = {loc.split(":")[0] for loc in locs}
        if len(files) > 1:
            dupes[slug] = locs
    return dupes


def load_baseline() -> dict | None:
    if not BASELINE_PATH.exists():
        return None
    try:
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:  # pragma: no cover - defensive
        return None


def build_report() -> dict:
    strict_map = collect_h1_h2_slugs(GENERIC_ALLOWED)
    strict_dupes = multi_file_duplicates(strict_map)
    clusters: list[Cluster] = []
    for slug, locs in strict_dupes.items():
        files = {loc.split(":")[0] for loc in locs}
        clusters.append(Cluster(slug=slug, files=files))
    clusters.sort(key=lambda c: (-c.file_count, c.slug))
    baseline = load_baseline()
    baseline_dupes = baseline.get("summary", {}).get("cross_file_duplicates") if baseline else None
    return {
        "schema_version": 1,
        "strict_duplicate_count": len(clusters),
        "baseline_cross_file_duplicates": baseline_dupes,
        "delta_vs_baseline": (len(clusters) - baseline_dupes) if baseline_dupes is not None else None,
        "clusters": [
            {
                "slug": c.slug,
                "file_count": c.file_count,
                "files": sorted(c.files),
            }
            for c in clusters
        ],
    }


def _run_dir(ts: datetime) -> Path:
    stamp = ts.strftime("%Y-%m-%d_%H%M")
    return OUTPUT_DIR / f"{RUN_PREFIX}{stamp}"


def write_artifacts(report: dict, ts: datetime | None = None) -> Path:
    ts = ts or datetime.utcnow()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = _run_dir(ts)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Base JSON artifact (timestamped)
    (run_dir / "anchor_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # Compact markdown summary
    lines = [
        "# Anchor Health Report",
        "",
        f"Generated (UTC): {ts.isoformat()}",
        f"Strict Duplicate Count: {report['strict_duplicate_count']}",
        f"Baseline (cross_file_duplicates): {report['baseline_cross_file_duplicates']}",
        f"Delta vs Baseline: {report['delta_vs_baseline']}",
        "",
        "## Top Clusters (up to 25)",
    ]
    for c in report["clusters"][:25]:
        lines.append(f"- `{c['slug']}` — {c['file_count']} files")
    lines.append("")
    lines.append("## Next Actions Guidance")
    lines.append("Prioritize largest clusters first; rename all but canonical file.")
    (run_dir / "anchor_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Full cluster listing for tooling consumption (tsv for quick grep)
    tsv_lines = ["slug\tfile_count\tfiles"]
    for c in report["clusters"]:
        tsv_lines.append(
            f"{c['slug']}\t{c['file_count']}\t" + ",".join(c["files"])  # type: ignore[index]
        )
    (run_dir / "clusters.tsv").write_text("\n".join(tsv_lines) + "\n", encoding="utf-8")

    # Update latest symlink / copies
    latest_json = OUTPUT_DIR / "anchor_report_latest.json"
    latest_md = OUTPUT_DIR / "anchor_report_latest.md"
    latest_tsv = OUTPUT_DIR / "clusters_latest.tsv"
    for src, dest in [
        (run_dir / "anchor_report.json", latest_json),
        (run_dir / "anchor_report.md", latest_md),
        (run_dir / "clusters.tsv", latest_tsv),
    ]:
        try:
            if dest.exists():
                dest.unlink()
            dest.hardlink_to(src)  # fast copy when same FS
        except Exception:
            # Fallback copy
            dest.write_bytes(src.read_bytes())

    # Append to run log
    log_line = (
        f"{ts.isoformat()} duplicates={report['strict_duplicate_count']} baseline={report['baseline_cross_file_duplicates']}"  # noqa: E501
    )
    with (OUTPUT_DIR / "runs.log").open("a", encoding="utf-8") as fh:
        fh.write(log_line + "\n")

    return run_dir


def main() -> None:  # pragma: no cover - CLI side effect
    report = build_report()
    run_dir = write_artifacts(report)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.info(
        "Anchor health artifacts written to %s (duplicates=%s baseline=%s)",
        run_dir,
        report["strict_duplicate_count"],
        report["baseline_cross_file_duplicates"],
    )


if __name__ == "__main__":  # pragma: no cover
    main()
