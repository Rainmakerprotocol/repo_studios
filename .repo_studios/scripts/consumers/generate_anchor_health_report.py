"""HOP-compliant Anchor Health Report Consumer.

Generates a machine + human consumable snapshot of top-level (H1/H2) markdown
anchor slug duplication using the latest `generate_anchor_inventory.py`
artifacts when available. Falls back to an in-process docs scan when no
inventory report exists. Intended to integrate with AI assistance workflows so
agents can:

1. Detect drift vs the committed baseline (`tests/docs/anchor_slug_baseline.json`).
2. Surface remaining cross-file duplicates, their file membership, and context.
3. Recommend the next slugs to collapse (largest clusters first) while respecting
     canonical file choices recorded in an optional mapping file.
4. Emit artifacts for dashboards / summaries.

HOP Base Package (under `.repo_studios/reports/consumer_reports/anchor_health/<timestamp>/`):
    - manifest.json (bundle metadata and metrics)
    - summary.md (human-readable report)
    - telemetry.json (execution metrics)

Supplementary:
    - anchor_report.json (legacy full report)
    - anchor_report.md (legacy markdown)
    - clusters.tsv (tabular cluster data)

Exit code is 0 even if duplicates exist (pipeline decides policy). Use the JSON
field `strict_duplicate_count` to gate if desired.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:  # pragma: no cover - import path bootstrap
    sys.path.insert(0, str(SCRIPTS_ROOT))

from utilities.anchor_inventory_loader import load_anchor_inventory  # noqa: E402

HEADING_RE = re.compile(r"^(#{1,2})\s+(.*)$")
GENERIC_ALLOWED = {"overview", "introduction", "faq", "notes"}
BASELINE_PATH = Path("tests/docs/anchor_slug_baseline.json")
# HOP-compliant output root for anchor health artifacts
TOPIC_SLUG = "anchor_health"

# Subfolder naming pattern: anchor_health-YYYY-MM-DD_hhmm
RUN_PREFIX = "anchor_health-"
DATABASE_PLACEHOLDER_TARGET = "anchor_health_snapshot"

# HOP base package artifact names
TELEMETRY_JSON_NAME = "telemetry.json"
SUMMARY_MD_NAME = "summary.md"
MANIFEST_JSON_NAME = "manifest.json"
# Legacy/supplementary artifacts
LEGACY_JSON_NAME = "anchor_report.json"
LEGACY_MD_NAME = "anchor_report.md"
CLUSTERS_TSV_NAME = "clusters.tsv"


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


def build_database_placeholder(target: str) -> dict[str, str]:
    """Return a clearly marked stub for future database sinks."""

    return {
        "target": target,
        "status": "not_implemented",
        "note": "Database sink placeholder; no data persisted during this run.",
    }


def collect_h1_h2_slugs(
    skip: set[str] | None = None,
    *,
    docs_roots: list[Path] | None = None,
) -> dict[str, list[str]]:
    """Collect H1/H2 heading slugs from markdown files in one or more docs directories.

    Args:
        skip: Set of slug names to exclude from collection.
        docs_roots: List of documentation root directories to scan. Each file's
            location is prefixed with the root's name for disambiguation when
            multiple roots exist.

    Returns:
        Mapping of slug -> list of "root_name/relative_path:lineno" locations.
    """
    all_roots = docs_roots or [Path("docs")]
    # Filter to only existing roots
    roots = [r for r in all_roots if r.exists()]
    if not roots:
        return {}

    mapping: dict[str, list[str]] = {}
    use_prefix = len(roots) > 1  # Only prefix when multiple roots exist
    for root in roots:
        # Use parent name to disambiguate when roots share the same name
        # e.g., "docs" vs ".repo_studios/docs"
        if use_prefix and root.parent.name == ".repo_studios":
            root_prefix = ".repo_studios/docs"
        else:
            root_prefix = root.name
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
                # Include root prefix in location for multi-root disambiguation
                rel_path = md.relative_to(root)
                if use_prefix:
                    location = f"{root_prefix}/{rel_path}:{lineno}"
                else:
                    location = f"{rel_path}:{lineno}"
                mapping.setdefault(slug, []).append(location)
    return mapping


def multi_file_duplicates(slug_map: dict[str, list[str]]) -> dict[str, list[str]]:
    dupes: dict[str, list[str]] = {}
    for slug, locs in slug_map.items():
        files = {loc.split(":")[0] for loc in locs}
        if len(files) > 1:
            dupes[slug] = locs
    return dupes


def load_baseline(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:  # pragma: no cover - defensive
        return None
    return payload if isinstance(payload, dict) else None


def _load_json(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_inventory_report(explicit: Path | None = None) -> tuple[dict, Path] | tuple[None, None]:
    """Load the latest anchor inventory report if available."""

    payload, payload_path = load_anchor_inventory(explicit)
    if payload is None or payload_path is None:
        return None, None
    return payload, payload_path


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


def _clusters_from_scan(*, docs_roots: list[Path]) -> list[Cluster]:
    """Build duplicate clusters by scanning multiple docs directories.

    Args:
        docs_roots: List of documentation root directories to scan.

    Returns:
        List of Cluster objects representing cross-file duplicate anchors.
    """
    strict_map = collect_h1_h2_slugs(GENERIC_ALLOWED, docs_roots=docs_roots)
    strict_dupes = multi_file_duplicates(strict_map)
    clusters: list[Cluster] = []
    for slug, locs in strict_dupes.items():
        files = {loc.split(":")[0] for loc in locs}
        clusters.append(Cluster(slug=slug, files=files, locations=sorted(locs)))
    clusters.sort(key=lambda c: (-c.file_count, c.slug))
    return clusters


def build_report(
    *,
    inventory: dict | None,
    inventory_path: Path | None,
    baseline_path: Path,
    docs_roots: list[Path],
) -> dict:
    """Build anchor health report from inventory or direct scan.

    Args:
        inventory: Optional pre-loaded inventory payload.
        inventory_path: Path to inventory file (for provenance).
        baseline_path: Path to baseline JSON for delta calculation.
        docs_roots: List of documentation root directories to scan when no inventory.

    Returns:
        Report dictionary with duplicate clusters and metrics.
    """
    if inventory is not None:
        clusters = _clusters_from_inventory(inventory)
        source = "inventory"
        strict_count = len(clusters)
        base_summary = inventory.get("summary", {}) if isinstance(inventory, dict) else {}
        cross_file_duplicates = base_summary.get("cross_file_duplicates")
    else:
        clusters = _clusters_from_scan(docs_roots=docs_roots)
        source = "scan"
        strict_count = len(clusters)
        cross_file_duplicates = None

    baseline = load_baseline(baseline_path)
    baseline_dupes = baseline.get("summary", {}).get("cross_file_duplicates") if baseline else None
    report = {
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
    report["outputs"] = {"database": build_database_placeholder(DATABASE_PLACEHOLDER_TARGET)}
    return report


ROOT = Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str and root_str not in sys.path:
    sys.path.insert(0, root_str)

LIBRARIES_ROOT = ROOT / "command_center" / "scripts"
libraries_root_str = str(LIBRARIES_ROOT)
if libraries_root_str and libraries_root_str not in sys.path:
    sys.path.insert(0, libraries_root_str)

from libraries import prune_run_directories  # noqa: E402
from libraries.cli import resolve_repo_root  # noqa: E402
from libraries.report_paths import build_topic_path  # noqa: E402
from libraries.retention_policy import get_keep  # noqa: E402

# HOP-compliant default output directory
OUTPUT_DIR = build_topic_path("consumer", TOPIC_SLUG)
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("generate_anchor_health_report")


def _run_dir(ts: datetime, base: Path = OUTPUT_DIR) -> Path:
    stamp = ts.strftime("%Y-%m-%d_%H%M")
    return base / f"{RUN_PREFIX}{stamp}"


def _prune_old_runs(output_dir: Path, *, keep: int, current_run: Path, logger: logging.Logger | None) -> list[Path]:
    try:
        keep_count = int(keep)
    except Exception:
        keep_count = DEFAULT_ARTIFACTS_TO_KEEP
    if keep_count < 0:
        keep_count = DEFAULT_ARTIFACTS_TO_KEEP
    keep_count = max(keep_count, 1)
    result = prune_run_directories(
        output_dir,
        keep=keep_count,
        stem_prefix=RUN_PREFIX,
        current_run=current_run,
        logger=logger,
    )
    return result.removed


def _build_summary(report: dict[str, Any]) -> dict[str, Any]:
    clusters: list[dict[str, Any]] = list(report.get("clusters", []))
    top_clusters: list[dict[str, Any]] = []
    for cluster in clusters[:10]:
        top_clusters.append(
            {
                "slug": cluster.get("slug"),
                "file_count": int(cluster.get("file_count", 0)),
                "files": list(cluster.get("files", [])),
                "locations": list(cluster.get("locations", [])),
            }
        )
    return {
        "schema_version": 1,
        "source": report.get("source"),
        "strict_duplicate_count": int(report.get("strict_duplicate_count", 0)),
        "baseline_cross_file_duplicates": report.get("baseline_cross_file_duplicates"),
        "delta_vs_baseline": report.get("delta_vs_baseline"),
        "inventory_cross_file_duplicates": report.get("inventory_cross_file_duplicates"),
        "inventory_report": report.get("inventory_report"),
        "total_clusters": len(clusters),
        "top_clusters": top_clusters,
        "database_placeholder": report.get("outputs", {}).get("database"),
    }


def _render_summary_markdown(
    summary: dict[str, Any], *, generated_at: datetime, bundle_dir: Path, baseline_path: Path
) -> str:
    lines: list[str] = ["# Anchor Health Summary", ""]
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append(f"- Strict Duplicate Count: {summary['strict_duplicate_count']}")
    baseline = summary.get("baseline_cross_file_duplicates")
    lines.append(f"- Baseline Cross-File Duplicates: {baseline if baseline is not None else 'unknown'}")
    delta = summary.get("delta_vs_baseline")
    lines.append(f"- Delta vs Baseline: {delta if delta is not None else 'N/A'}")
    cross_file = summary.get("inventory_cross_file_duplicates")
    if cross_file is not None:
        lines.append(f"- Inventory Cross-File Duplicates: {cross_file}")
    lines.append(f"- Source: {summary.get('source', 'unknown')}")
    lines.append("")
    lines.append("<!-- markdownlint-disable MD013 -->")
    lines.append("## Top Clusters")
    lines.append("")
    raw_top_clusters = summary.get("top_clusters", [])
    top_clusters: list[dict[str, Any]] = list(raw_top_clusters) if isinstance(raw_top_clusters, list) else []
    if top_clusters:
        for cluster in top_clusters:
            slug = cluster.get("slug", "unknown")
            file_count = cluster.get("file_count", 0)
            files_list = list(cluster.get("files", []))
            files = ", ".join(files_list[:3])
            if files:
                lines.append(f"- `{slug}` — {file_count} files ({files})")
            else:
                lines.append(f"- `{slug}` — {file_count} files")
    else:
        lines.append("- None")
    lines.append("<!-- markdownlint-enable MD013 -->")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    lines.append("- Prioritize the largest duplicate clusters and align headings across files.")
    lines.append("- Confirm updates against the committed baseline before closing remediation items.")
    lines.append("")
    lines.append("## Source References")
    lines.append("")
    lines.append(f"- Source Type: {summary.get('source', 'unknown')}")
    inventory_report = summary.get("inventory_report")
    if inventory_report:
        try:
            lines.append(f"- Inventory Report: `{Path(str(inventory_report)).resolve()}`")
        except Exception:
            lines.append(f"- Inventory Report: `{inventory_report}`")
    try:
        lines.append(f"- Baseline File: `{baseline_path.resolve()}`")
    except Exception:
        lines.append(f"- Baseline File: `{baseline_path}`")
    lines.append(f"- Consumer Bundle: `{bundle_dir.resolve()}`")
    return "\n".join(lines) + "\n"


def write_artifacts(
    report: dict,
    ts: datetime | None = None,
    *,
    output_dir: Path,
    baseline_path: Path,
) -> dict[str, Any]:
    """Write HOP-compliant artifact bundle.

    Base package (HOP standard):
        - manifest.json: Bundle metadata, artifact paths, metrics
        - summary.md: Human-readable anchor health report
        - telemetry.json: Execution metrics for aggregation

    Supplementary artifacts:
        - anchor_report.json: Legacy full report (for backward compatibility)
        - anchor_report.md: Legacy markdown report
        - clusters.tsv: Tabular cluster data

    Args:
        report: Full report dict from build_report()
        ts: Optional timestamp override (defaults to now UTC)
        output_dir: Parent output directory
        baseline_path: Path to baseline JSON file

    Returns:
        Dict with artifact paths and summary data
    """
    ts = ts or datetime.now(UTC)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = _run_dir(ts, output_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = _build_summary(report)

    # HOP base package: telemetry.json (was summary.json)
    telemetry_path = run_dir / TELEMETRY_JSON_NAME
    telemetry_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    # HOP base package: summary.md (was SUMMARY.md)
    summary_md_path = run_dir / SUMMARY_MD_NAME
    summary_md_path.write_text(
        _render_summary_markdown(summary, generated_at=ts, bundle_dir=run_dir, baseline_path=baseline_path),
        encoding="utf-8",
    )

    # HOP base package: manifest.json (was bundle_summary.json)
    manifest = {
        "schema_version": 1,
        "generated_at": ts.isoformat(timespec="seconds"),
        "source": report.get("source"),
        "inventory_report": report.get("inventory_report"),
        "artifacts": {
            "telemetry_json": str(telemetry_path.resolve()),
            "summary_md": str(summary_md_path.resolve()),
            "legacy_report_json": str((run_dir / LEGACY_JSON_NAME).resolve()),
            "legacy_report_md": str((run_dir / LEGACY_MD_NAME).resolve()),
            "clusters_tsv": str((run_dir / CLUSTERS_TSV_NAME).resolve()),
        },
        "metrics": {
            "strict_duplicate_count": summary["strict_duplicate_count"],
            "baseline_cross_file_duplicates": summary.get("baseline_cross_file_duplicates"),
            "delta_vs_baseline": summary.get("delta_vs_baseline"),
            "inventory_cross_file_duplicates": summary.get("inventory_cross_file_duplicates"),
            "total_clusters": summary.get("total_clusters"),
        },
        "database_placeholder": summary.get("database_placeholder"),
    }

    manifest_path = run_dir / MANIFEST_JSON_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    legacy_json_path = run_dir / LEGACY_JSON_NAME
    legacy_json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    legacy_md_lines = [
        "# Anchor Health Report",
        "",
        f"Generated (UTC): {ts.isoformat()}",
        f"Strict Duplicate Count: {report['strict_duplicate_count']}",
        f"Baseline (cross_file_duplicates): {report['baseline_cross_file_duplicates']}",
        f"Delta vs Baseline: {report['delta_vs_baseline']}",
        "",
        "## Top Clusters (up to 25)",
        "",
    ]
    for cluster in report["clusters"][:25]:
        legacy_md_lines.append(f"- `{cluster['slug']}` — {cluster['file_count']} files")
    legacy_md_lines.append("")
    legacy_md_lines.append("## Next Actions Guidance")
    legacy_md_lines.append("")
    legacy_md_lines.append("Prioritize largest clusters first; rename all but canonical file.")
    (run_dir / LEGACY_MD_NAME).write_text("\n".join(legacy_md_lines) + "\n", encoding="utf-8")

    tsv_lines = ["slug\tfile_count\tfiles\tlocations"]
    for cluster in report["clusters"]:
        files_raw = cluster.get("files")
        files: list[str] = []
        if isinstance(files_raw, list):
            files = [str(item) for item in files_raw]
        locations_raw = cluster.get("locations")
        locations: list[str] = []
        if isinstance(locations_raw, list):
            locations = [str(item) for item in locations_raw]
        files_joined = ",".join(files)
        locations_joined = ";".join(locations)
        tsv_lines.append(
            f"{cluster.get('slug','')}\t{int(cluster.get('file_count',0))}\t{files_joined}\t{locations_joined}"
        )
    (run_dir / CLUSTERS_TSV_NAME).write_text("\n".join(tsv_lines) + "\n", encoding="utf-8")

    log_line = f"{ts.isoformat()} duplicates={report['strict_duplicate_count']} baseline={report['baseline_cross_file_duplicates']}"
    with (output_dir / "runs.log").open("a", encoding="utf-8") as fh:
        fh.write(log_line + "\n")

    return {
        "bundle_dir": run_dir,
        "summary": summary,
        "telemetry_path": telemetry_path,
        "summary_path": summary_md_path,
        "manifest_path": manifest_path,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate anchor health report from inventory artifacts")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root override (auto-detected by scanning ancestors for a .repo_studios/ marker when omitted)"
        ),
    )
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
    repo_root: str | Path | None = None,
    inventory_report: Path | None = None,
    output_dir: Path | None = None,
    artifacts_to_keep: int | None = None,
    argv: Sequence[str] | None = None,
) -> dict:
    if argv is not None:
        args = parse_args(argv)
    else:
        args = argparse.Namespace(
            repo_root=repo_root,
            inventory_report=inventory_report,
            output_dir=output_dir,
            artifacts_to_keep=artifacts_to_keep if artifacts_to_keep is not None else DEFAULT_ARTIFACTS_TO_KEEP,
            log_level="INFO",
        )

    resolved_repo_root = resolve_repo_root(getattr(args, "repo_root", None), origin=Path(__file__))
    baseline_path = (resolved_repo_root / BASELINE_PATH).resolve()

    # Scan both repo root docs/ and .repo_studios/docs/
    docs_roots = [
        (resolved_repo_root / "docs").resolve(),
        (resolved_repo_root / ".repo_studios" / "docs").resolve(),
    ]

    log_level = getattr(logging, str(args.log_level).upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s %(message)s", force=True)

    log = logging.getLogger("anchor_health")

    inventory_report_path = args.inventory_report
    if inventory_report_path is not None and not inventory_report_path.is_absolute():
        inventory_report_path = (resolved_repo_root / inventory_report_path).resolve()

    inventory_payload, inventory_path = load_inventory_report(inventory_report_path)
    report = build_report(
        inventory=inventory_payload,
        inventory_path=inventory_path,
        baseline_path=baseline_path,
        docs_roots=docs_roots,
    )

    target_output = args.output_dir if args.output_dir is not None else OUTPUT_DIR
    if not target_output.is_absolute():
        target_output = (resolved_repo_root / target_output).resolve()
    else:
        target_output = target_output.resolve()

    artifact_info = write_artifacts(report, output_dir=target_output, baseline_path=baseline_path)
    pruned = _prune_old_runs(
        target_output,
        keep=args.artifacts_to_keep,
        current_run=artifact_info["bundle_dir"],
        logger=log,
    )
    return {
        "report": report,
        "summary": artifact_info["summary"],
        "bundle_dir": str(artifact_info["bundle_dir"].resolve()),
        "manifest_path": str(artifact_info["manifest_path"].resolve()),
        "telemetry_path": str(artifact_info["telemetry_path"].resolve()),
        "summary_path": str(artifact_info["summary_path"].resolve()),
        "output_dir": str(target_output.resolve()),
        "source": report.get("source"),
        "pruned": [str(p.resolve()) for p in pruned],
    }


def main(argv: Sequence[str] | None = None) -> None:  # pragma: no cover - CLI side effect
    if argv is None:
        argv = sys.argv[1:]
    result = run(argv=argv)
    report = result["report"]
    bundle_dir = result["bundle_dir"]
    logging.info(
        "Anchor health artifacts written to %s (duplicates=%s baseline=%s)",
        bundle_dir,
        report["strict_duplicate_count"],
        report["baseline_cross_file_duplicates"],
    )


if __name__ == "__main__":  # pragma: no cover
    main()
