"""Anchor Health Report Generator.

Generates a machine + human consumable snapshot of top-level (H1/H2) markdown
anchor slug duplication using the latest `generate_anchor_inventory.py`
artifacts when available. Falls back to an in-process docs scan when no
inventory report exists. Intended to integrate with AI assistance workflows so
agents can:

1. Detect drift vs the committed baseline (`tests/docs/anchor_slug_baseline.json`).
2. Surface remaining cross-file duplicates, their file membership, and context.
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

import argparse
import json
import logging
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Sequence

HEADING_RE = re.compile(r"^(#{1,2})\s+(.*)$")
GENERIC_ALLOWED = {"overview", "introduction", "faq", "notes"}
BASELINE_PATH = Path("tests/docs/anchor_slug_baseline.json")
# Permanent root for anchor health artifacts (contains latest + historical runs)
OUTPUT_DIR = Path(".repo_studios/anchor_health")
INVENTORY_DIR = Path(".repo_studios/reports/producer_reports/anchor_inventory_reports")
INVENTORY_LATEST = INVENTORY_DIR / "latest_report.json"
DEFAULT_ARTIFACTS_TO_KEEP = 10

# Subfolder naming pattern: anchor_health-YYYY-MM-DD_hhmm
RUN_PREFIX = "anchor_health-"


def _slugify(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"`+", "", s)
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


class Cluster:
    """Container for duplicate slug membership."""

    def __init__(self, slug: str, files: set[str], locations: list[str]) -> None:
        self.slug = slug
        self.files = files
        self.locations = locations

    @property
    def file_count(self) -> int:  # pragma: no cover - trivial
        return len(self.files)


def collect_h1_h2_slugs(skip: set[str] | None = None, *, docs_root: Path | None = None) -> dict[str, list[str]]:
    root = docs_root or Path("docs")
    if not root.exists():
        raise FileNotFoundError(f"docs directory missing: {root}")
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
            mapping.setdefault(slug, []).append(f"{md.relative_to(root)}:{lineno}")
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


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _iter_inventory_reports(base_dir: Path) -> Iterable[Path]:
    if not base_dir.exists():
        return []
    run_dirs = sorted(
        (child for child in base_dir.iterdir() if child.is_dir() and child.name.startswith("anchor_inventory-")),
        key=lambda p: p.name,
        reverse=True,
    )
    for run_dir in run_dirs:
        candidate = run_dir / "report.json"
        if candidate.exists():
            yield candidate


def load_inventory_report(explicit: Path | None = None) -> tuple[dict, Path] | tuple[None, None]:
    """Load the latest anchor inventory report if available."""

    if explicit is not None:
        payload = _load_json(explicit)
        if payload is not None:
            return payload, explicit
        return None, None

    if INVENTORY_LATEST.exists():
        payload = _load_json(INVENTORY_LATEST)
        if payload is not None:
            return payload, INVENTORY_LATEST

    for candidate in _iter_inventory_reports(INVENTORY_DIR):
        payload = _load_json(candidate)
        if payload is not None:
            return payload, candidate

    return None, None


def _clusters_from_inventory(inventory: dict) -> list[Cluster]:
    clusters: list[Cluster] = []
    for entry in inventory.get("duplicates", []):
        slug = entry.get("slug")
        files = entry.get("files", [])
        if not slug or not files:
            continue
        file_set = {str(f) for f in files}
        if len(file_set) < 2:
            continue
        if slug in GENERIC_ALLOWED:
            continue
        locations = sorted(str(loc) for loc in entry.get("locations", []))
        clusters.append(Cluster(slug=slug, files=file_set, locations=locations))
    clusters.sort(key=lambda c: (-c.file_count, c.slug))
    return clusters


def _clusters_from_scan() -> list[Cluster]:
    strict_map = collect_h1_h2_slugs(GENERIC_ALLOWED)
    strict_dupes = multi_file_duplicates(strict_map)
    clusters: list[Cluster] = []
    for slug, locs in strict_dupes.items():
        files = {loc.split(":")[0] for loc in locs}
        clusters.append(Cluster(slug=slug, files=files, locations=sorted(locs)))
    clusters.sort(key=lambda c: (-c.file_count, c.slug))
    return clusters


def build_report(*, inventory: dict | None, inventory_path: Path | None) -> dict:
    if inventory is not None:
        clusters = _clusters_from_inventory(inventory)
        source = "inventory"
        strict_count = len(clusters)
        base_summary = inventory.get("summary", {}) if isinstance(inventory, dict) else {}
        cross_file_duplicates = base_summary.get("cross_file_duplicates")
    else:
        clusters = _clusters_from_scan()
        source = "scan"
        strict_count = len(clusters)
        cross_file_duplicates = None

    baseline = load_baseline()
    baseline_dupes = baseline.get("summary", {}).get("cross_file_duplicates") if baseline else None
    return {
        "schema_version": 2,
        "source": source,
        "inventory_report": str(inventory_path) if inventory_path else None,
        "strict_duplicate_count": strict_count,
        "baseline_cross_file_duplicates": baseline_dupes,
        "delta_vs_baseline": (len(clusters) - baseline_dupes) if baseline_dupes is not None else None,
        "inventory_cross_file_duplicates": cross_file_duplicates,
        "clusters": [
            {
                "slug": c.slug,
                "file_count": c.file_count,
                "files": sorted(c.files),
                "locations": c.locations,
            }
            for c in clusters
        ],
    }


def _run_dir(ts: datetime, base: Path = OUTPUT_DIR) -> Path:
    stamp = ts.strftime("%Y-%m-%d_%H%M")
    return base / f"{RUN_PREFIX}{stamp}"


def _prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> list[Path]:
    if keep is None:
        return []
    keep = max(int(keep), 0)
    if not output_dir.exists():
        return []
    run_dirs = sorted(
        [
            path
            for path in output_dir.iterdir()
            if path.is_dir() and path.name.startswith(RUN_PREFIX) and path != current_run
        ],
        key=lambda p: p.name,
        reverse=True,
    )
    limit = max(keep - 1, 0)
    stale = run_dirs[limit:]
    for path in stale:
        shutil.rmtree(path, ignore_errors=True)
    if stale:
        logging.debug("Pruned %s old anchor health runs", len(stale))
    return stale


def write_artifacts(report: dict, ts: datetime | None = None, *, output_dir: Path = OUTPUT_DIR) -> Path:
    ts = ts or datetime.now(UTC)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = _run_dir(ts, output_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Base JSON artifact (timestamped)
    (run_dir / "anchor_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

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
    tsv_lines = ["slug\tfile_count\tfiles\tlocations"]
    for c in report["clusters"]:
        files_joined = ",".join(c["files"])  # type: ignore[index]
        locations_joined = ";".join(c.get("locations", []))
        tsv_lines.append(f"{c['slug']}\t{c['file_count']}\t{files_joined}\t{locations_joined}")
    (run_dir / "clusters.tsv").write_text("\n".join(tsv_lines) + "\n", encoding="utf-8")

    # Update latest symlink / copies
    latest_json = output_dir / "anchor_report_latest.json"
    latest_md = output_dir / "anchor_report_latest.md"
    latest_tsv = output_dir / "clusters_latest.tsv"
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
    log_line = f"{ts.isoformat()} duplicates={report['strict_duplicate_count']} baseline={report['baseline_cross_file_duplicates']}"  # noqa: E501
    with (output_dir / "runs.log").open("a", encoding="utf-8") as fh:
        fh.write(log_line + "\n")

    return run_dir


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate anchor health report from inventory artifacts")
    parser.add_argument(
        "--inventory-report", type=Path, default=None, help="Explicit anchor inventory report to consume"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override anchor health output directory (defaults to .repo_studios/anchor_health)",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of timestamped runs to retain (including the newest run)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (e.g. INFO, DEBUG)",
    )
    return parser.parse_args(argv)


def run(
    *,
    inventory_report: Path | None = None,
    output_dir: Path | None = None,
    artifacts_to_keep: int | None = None,
    argv: Sequence[str] | None = None,
) -> dict:
    if argv is not None:
        args = parse_args(argv)
    else:
        args = argparse.Namespace(
            inventory_report=inventory_report,
            output_dir=output_dir,
            artifacts_to_keep=artifacts_to_keep if artifacts_to_keep is not None else DEFAULT_ARTIFACTS_TO_KEEP,
            log_level="INFO",
        )

    log_level = getattr(logging, str(args.log_level).upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s %(message)s", force=True)

    inventory_payload, inventory_path = load_inventory_report(args.inventory_report)
    report = build_report(inventory=inventory_payload, inventory_path=inventory_path)
    target_output = args.output_dir if args.output_dir is not None else OUTPUT_DIR
    run_dir = write_artifacts(report, output_dir=target_output)
    _prune_old_runs(target_output, keep=args.artifacts_to_keep, current_run=run_dir)
    return {"report": report, "run_dir": str(run_dir)}


def main(argv: Sequence[str] | None = None) -> None:  # pragma: no cover - CLI side effect
    result = run(argv=argv)
    report = result["report"]
    run_dir = result["run_dir"]
    logging.info(
        "Anchor health artifacts written to %s (duplicates=%s baseline=%s)",
        run_dir,
        report["strict_duplicate_count"],
        report["baseline_cross_file_duplicates"],
    )


if __name__ == "__main__":  # pragma: no cover
    main()
