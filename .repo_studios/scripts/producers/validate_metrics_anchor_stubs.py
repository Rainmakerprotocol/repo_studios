#!/usr/bin/env python3
"""Metrics Anchor Stub Validation (canonical producer bundle).

Scans repository markdown for links to `metrics_orchestrator.md#<anchor>` and validates
that each referenced anchor has a corresponding legacy stub heading under the
"Legacy Anchor Compatibility" section of the legacy doc (defaults to
`docs/api/metrics_orchestrator.md`).

Artifacts:
        * Canonical bundle artifacts under
            `.repo_studios/reports/producer_reports/healthview/metrics_anchor_stub_validation/<YYYYMMDD-HHMM>/`
        * Files: `manifest.json`, `summary.md`, `telemetry.json`
        * Timestamped run folders with automatic pruning (keep last N by default)

Exit codes:
        0 - success, no missing legacy stubs
        1 - missing anchors detected (artifacts still emitted)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, cast

RE_MD_LINK = re.compile(r"metrics_orchestrator\.md#([a-zA-Z0-9\-._]+)")
RE_HEADING = re.compile(r"^(#{2,6})\s+(.*)$")

DEFAULT_LEGACY_FILE = Path("docs/api/metrics_orchestrator.md")
DEFAULT_ALLOWLIST_PATH = Path(".repo_studios/scripts/producers/metrics_anchor_allowlist.json")
SCHEMA_VERSION = 1
TOPIC_SLUG = "metrics_anchor_stub_validation"

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback for script execution without package path
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep

try:
    from libraries.database_integration import create_storage
except ModuleNotFoundError:  # pragma: no cover - fallback for script execution without package path
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries.database_integration import create_storage

# Must be after import block where get_keep is defined
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("validate_metrics_anchor_stubs")
DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)


@dataclass(frozen=True)
class Paths:
    """Path configuration for metrics anchor stub validation.

    Attributes:
        repo_root: Repository root directory.
        output_dir: Directory for structured artifacts.
        legacy_file: Path to metrics orchestrator markdown file.
        allowlist_path: Path to JSON file with allowed anchors.
    """

    repo_root: Path
    output_dir: Path
    legacy_file: Path
    allowlist_path: Path


@dataclass(frozen=True)
class Options:
    """Validation options for metrics anchor stub validation.

    Attributes:
        artifacts_to_keep: Number of historical run directories to retain.
    """

    artifacts_to_keep: int


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True, within_repo=False),
        "legacy_file": PathSpec(field="legacy_file", default=DEFAULT_LEGACY_FILE, within_repo=False),
        "allowlist_path": PathSpec(field="allowlist_path", default=DEFAULT_ALLOWLIST_PATH, within_repo=False),
    },
    repo_root_depth=4,
)

OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
    },
)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments for metrics anchor stub validation.

    Args:
        argv: Command-line arguments. Uses sys.argv[1:] if None.

    Returns:
        Parsed namespace with validated arguments.
    """
    parser = argparse.ArgumentParser(
        prog="validate_metrics_anchor_stubs",
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root (defaults to project root detected from script location)",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for structured artifacts",
    )
    parser.add_argument(
        "--legacy-file",
        help="Path to metrics orchestrator markdown file containing legacy stub section",
    )
    parser.add_argument(
        "--allowlist-path",
        help='JSON file with anchors to allow (format: {"anchors": ["foo"]})',
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical run directories to retain after pruning",
    )
    parser.add_argument(
        "--include-repo-studios",
        action="store_true",
        help=(
            "Include markdown files under .repo_studios/ in the repository scan. "
            "By default, hidden directories are excluded."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    """Configure logging with the specified verbosity level.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    """Build path configuration from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Paths dataclass with resolved path values.
    """
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    """Build options configuration from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Options dataclass with validated option values.
    """
    return cast(Options, build_standard_options(args, OPTIONS_CONFIG))


def _format_run_timestamp(timestamp: dt.datetime) -> str:
    """Format a datetime as a run timestamp slug.

    Args:
        timestamp: Datetime to format.

    Returns:
        Timestamp string in YYYYMMDD-HHMM format (UTC).
    """
    return timestamp.astimezone(dt.timezone.utc).strftime("%Y%m%d-%H%M")


def _normalize_anchor(text: str) -> str:
    """Normalize text into a URL-safe anchor slug.

    Strip whitespace, convert to lowercase, and remove special characters.

    Args:
        text: Raw heading or anchor text.

    Returns:
        Normalized anchor string.
    """
    normalized = text.strip().lower().replace("`", "")
    normalized = re.sub(r"\s+", "-", normalized)
    return re.sub(r"[^a-z0-9._-]", "", normalized)


def iter_markdown_files(repo_root: Path, *, include_repo_studios: bool) -> Iterable[Path]:
    """Iterate over markdown files in the repository.

    Exclude hidden directories (optionally allowing .repo_studios), vendor/external
    folders, and generated report artifacts.

    Args:
        repo_root: Repository root directory.

    Yields:
        Paths to markdown files.
    """
    for path in repo_root.rglob("*.md"):
        rel = path.relative_to(repo_root)

        # Exclude generated report artifacts to avoid self-referential scans.
        if rel.parts and rel.parts[0] == "reports":
            continue
        if rel.parts[:2] == (".repo_studios", "reports"):
            continue
        if rel.parts[:3] == (".repo_studios", "command_center", "reports"):
            continue

        if any(part.startswith(".") for part in rel.parts):
            if not (include_repo_studios and rel.parts and rel.parts[0] == ".repo_studios"):
                continue
        if rel.parts[0] in {"vendor", "external"}:
            continue
        yield path


def collect_referenced_anchors(files: Iterable[Path], repo_root: Path) -> dict[str, list[str]]:
    """Collect all anchors referenced in markdown link fragments.

    Scan files for markdown links with fragment identifiers and build
    a mapping of anchors to the files that reference them.

    Args:
        files: Iterable of markdown file paths.
        repo_root: Repository root for relative path computation.

    Returns:
        Dictionary mapping anchors to lists of referencing file paths.
    """
    anchors: dict[str, set[str]] = defaultdict(set)
    for md_file in files:
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in RE_MD_LINK.finditer(text):
            anchor = match.group(1).lower()
            anchors[anchor].add(md_file.relative_to(repo_root).as_posix())
    return {anchor: sorted(paths) for anchor, paths in anchors.items()}


def collect_legacy_stub_anchors(legacy_file: Path) -> set[str]:
    """Extract anchors defined in the legacy stub section.

    Parse the legacy file for the "Legacy Anchor Compatibility" section
    and collect all heading anchors defined therein.

    Args:
        legacy_file: Path to the metrics orchestrator markdown file.

    Returns:
        Set of normalized anchor strings from the legacy section.
    """
    if not legacy_file.exists():
        return set()
    try:
        lines = legacy_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()

    anchors: set[str] = set()
    in_legacy_block = False
    for line in lines:
        stripped = line.strip().lower()
        if stripped.startswith("## legacy anchor compatibility"):
            in_legacy_block = True
            continue
        if in_legacy_block and line.startswith("## ") and not stripped.startswith("## legacy anchor compatibility"):
            in_legacy_block = False
        if not in_legacy_block:
            continue
        match = RE_HEADING.match(line)
        if match:
            anchors.add(_normalize_anchor(match.group(2)))
    return anchors


def load_allowlist(path: Path) -> set[str]:
    """Load the anchor allowlist from a JSON file.

    Args:
        path: Path to JSON file with {"anchors": [...]} structure.

    Returns:
        Set of allowed anchor strings (lowercased).
    """
    if not path.exists():
        return set()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    anchors = raw.get("anchors", [])
    return {str(anchor).lower() for anchor in anchors}


def summarize_missing(
    referenced: dict[str, list[str]],
    legacy: set[str],
    allowlist: set[str],
) -> tuple[list[dict[str, Any]], int]:
    """Identify anchors missing from legacy stubs.

    Compare referenced anchors against legacy and allowlist to find
    those that need attention.

    Args:
        referenced: Dictionary mapping anchors to referencing files.
        legacy: Set of anchors defined in legacy stubs.
        allowlist: Set of explicitly allowed anchors.

    Returns:
        Tuple of (missing anchor records, count of allowlisted anchors).
    """
    missing: list[dict[str, Any]] = []
    allowlisted_count = 0
    for anchor, files in sorted(referenced.items()):
        if anchor in legacy:
            continue
        if anchor in allowlist:
            allowlisted_count += 1
            continue
        missing.append({"anchor": anchor, "files": files})
    return missing, allowlisted_count


def build_report(
    *,
    repo_root: Path,
    legacy_file: Path,
    allowlist_path: Path,
    artifacts_to_keep: int,
    referenced: dict[str, list[str]],
    legacy: set[str],
    allowlist: set[str],
    missing: list[dict[str, Any]],
    allowlisted_count: int,
    markdown_count: int,
    include_repo_studios: bool,
    timestamp: dt.datetime,
) -> dict[str, Any]:
    """Build the validation report dictionary.

    Assemble all validation results into a structured report with
    summary metrics, missing anchors, and configuration details.

    Args:
        repo_root: Repository root directory.
        legacy_file: Path to the legacy stub file.
        allowlist_path: Path to the allowlist JSON file.
        artifacts_to_keep: Number of artifacts to retain.
        referenced: Dictionary of referenced anchors.
        legacy: Set of legacy stub anchors.
        allowlist: Set of allowed anchors.
        missing: List of missing anchor records.
        allowlisted_count: Count of allowlisted anchors.
        markdown_count: Number of markdown files checked.
        timestamp: Report generation timestamp.

    Returns:
        Complete validation report dictionary.
    """
    summary = {
        "files_checked": markdown_count,
        "anchors_referenced": len(referenced),
        "legacy_stub_count": len(legacy),
        "missing_count": len(missing),
        "allowlisted_count": allowlisted_count,
    }
    status = "ok" if summary["missing_count"] == 0 else "fail"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": timestamp.astimezone(dt.timezone.utc).isoformat(),
        "status": status,
        "repo_root": str(repo_root),
        "legacy_file": str(legacy_file),
        "allowlist_path": str(allowlist_path) if allowlist_path.exists() else None,
        "options": {"artifacts_to_keep": artifacts_to_keep},
        "scan": {
            "include_repo_studios": include_repo_studios,
            "hidden_directories": "excluded (except .repo_studios when enabled)",
        },
        "summary": summary,
        "missing": missing,
        "referenced_anchors": sorted(referenced.keys()),
        "legacy_anchors": sorted(legacy),
        "allowlisted_anchors": sorted(allowlist),
    }


def compose_manifest(*, report: dict[str, Any], run_timestamp: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Compose the manifest dictionary for the validation run.

    Build a manifest with run metadata, status, and summary metrics.

    Args:
        report: The validation report dictionary.
        run_timestamp: Timestamp slug for the run.
        inputs: Dictionary of input parameters.

    Returns:
        A manifest dictionary for the validation bundle.
    """
    summary = report.get("summary", {})
    return {
        "schema_version": 1,
        "viewer_slug": "producer_reports",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_timestamp,
        "generated_utc": report.get("generated_utc"),
        "status": report.get("status", "ok"),
        "inputs": inputs,
        "summary": {
            "files_checked": summary.get("files_checked", 0),
            "anchors_referenced": summary.get("anchors_referenced", 0),
            "legacy_stub_count": summary.get("legacy_stub_count", 0),
            "missing_count": summary.get("missing_count", 0),
            "allowlisted_count": summary.get("allowlisted_count", 0),
        },
        "catalog": ["scripts.utilities.validate_metrics_anchor_stubs"],
        "provenance": {
            "requested_by": "cli",
            "trigger_type": "manual",
        },
    }


def compose_telemetry(*, report: dict[str, Any]) -> dict[str, Any]:
    """Compose the telemetry dictionary for the validation run.

    Build telemetry with metrics about files checked, anchors
    referenced, and missing counts.

    Args:
        report: The validation report dictionary.

    Returns:
        A telemetry dictionary with metrics and payload.
    """
    summary = report.get("summary", {})
    return {
        "schema_version": 1,
        "generated_utc": report.get("generated_utc"),
        "status": report.get("status", "ok"),
        "metrics": {
            "files_checked": summary.get("files_checked", 0),
            "anchors_referenced": summary.get("anchors_referenced", 0),
            "legacy_stub_count": summary.get("legacy_stub_count", 0),
            "missing_count": summary.get("missing_count", 0),
            "allowlisted_count": summary.get("allowlisted_count", 0),
        },
        "payload": {
            "report": report,
        },
    }


def render_summary_markdown(*, report: dict[str, Any], run_timestamp: str) -> str:
    """Render the validation report as a markdown summary.

    Format the report with status, metrics, missing anchors table,
    and next steps for human readability.

    Args:
        report: The validation report dictionary.
        run_timestamp: Timestamp slug for the run.

    Returns:
        A markdown-formatted summary string.
    """
    summary = report.get("summary", {})
    status = report.get("status", "ok")
    anchors_referenced = int(summary.get("anchors_referenced", 0) or 0)
    scan = cast(dict[str, Any], report.get("scan", {}))
    include_repo_studios = bool(scan.get("include_repo_studios", False))
    lines: list[str] = [
        "# Metrics Anchor Stub Validation\n\n",
        f"- Status: `{status}`\n",
        f"- Run Timestamp (UTC): `{run_timestamp}`\n",
        f"- Legacy File: `{report.get('legacy_file', '')}`\n",
        f"- Allowlist: `{report.get('allowlist_path') or 'none'}`\n",
        f"- Include .repo_studios: `{str(include_repo_studios).lower()}`\n",
        f"- Files Checked: {summary.get('files_checked', 0)}\n",
        f"- Anchors Referenced: {anchors_referenced}\n",
        f"- Legacy Stub Count: {summary.get('legacy_stub_count', 0)}\n",
        f"- Missing Anchors: {summary.get('missing_count', 0)}\n",
        f"- Allowlisted Anchors: {summary.get('allowlisted_count', 0)}\n",
    ]

    if anchors_referenced == 0:
        lines.append("- Signal: `low` (no references observed)\n")

    missing = report.get("missing", [])
    if missing:
        lines.append("\n## Missing Anchors\n\n")
        lines.append("| Anchor | Referenced In |\n| --- | --- |")
        for entry in missing:
            files = "<br>".join(entry.get("files", [])) or "—"
            lines.append(f"\n| `{entry.get('anchor')}` | {files} |")

    if anchors_referenced == 0:
        lines.append(
            "\n\n## Next Steps\n\n"
            "- [ ] If you expect references, confirm the repo contains `metrics_orchestrator.md#...` links and re-run.\n"
            "- [ ] If references are intentionally absent, treat this run as low-signal and validate the legacy file via a spot-check.\n"
        )
    else:
        lines.append(
            "\n\n## Next Steps\n\n"
            "- [ ] Add legacy stub entries for missing anchors listed above, or document intentional drift.\n"
            "- [ ] If exceptions are required, update the allowlist JSON with justification.\n"
            "- [ ] Re-run this producer to confirm a clean state.\n"
        )
    return "".join(lines)


def prune_history(
    base_dir: Path,
    keep: int,
    *,
    current_run: Path | None,
    logger: logging.Logger | None,
) -> list[Path]:
    """Prune old run directories to retain a fixed history depth.

    Args:
        base_dir: Directory containing timestamped run folders.
        keep: Number of run directories to retain.
        current_run: Path to the current run directory (protected).
        logger: Logger for debug output.

    Returns:
        List of paths that were removed.
    """
    result = prune_run_directories(
        base_dir,
        keep=max(keep, 1),
        current_run=current_run,
        logger=logger,
    )
    return result.removed


def run(argv: list[str] | None = None) -> dict[str, Any]:
    """Run the metrics anchor stub validation workflow.

    Parse arguments, collect anchors, validate against legacy stubs,
    and write results to the output directory.

    Args:
        argv: Command-line arguments. Uses sys.argv[1:] if None.

    Returns:
        A dictionary with validation results and run metadata.
    """
    args = parse_args(argv)
    configure_logging(args.log_level)
    logger = logging.getLogger(__name__)
    paths = build_paths(args)
    options = build_options(args)
    paths.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Repo root: %s", paths.repo_root)
    logger.info("Output directory: %s", paths.output_dir)
    logger.info("Legacy file: %s", paths.legacy_file)

    include_repo_studios = bool(getattr(args, "include_repo_studios", False))
    if include_repo_studios:
        logger.info("Including markdown under .repo_studios")

    markdown_files = list(iter_markdown_files(paths.repo_root, include_repo_studios=include_repo_studios))
    referenced = collect_referenced_anchors(markdown_files, paths.repo_root)
    legacy = collect_legacy_stub_anchors(paths.legacy_file)
    allowlist = load_allowlist(paths.allowlist_path)
    missing, allowlisted_count = summarize_missing(referenced, legacy, allowlist)

    timestamp = dt.datetime.now(dt.timezone.utc)
    run_timestamp = _format_run_timestamp(timestamp)

    report = build_report(
        repo_root=paths.repo_root,
        legacy_file=paths.legacy_file,
        allowlist_path=paths.allowlist_path,
        artifacts_to_keep=options.artifacts_to_keep,
        referenced=referenced,
        legacy=legacy,
        allowlist=allowlist,
        missing=missing,
        allowlisted_count=allowlisted_count,
        markdown_count=len(markdown_files),
        include_repo_studios=include_repo_studios,
        timestamp=timestamp,
    )

    inputs: dict[str, Any] = {
        "repo_root": str(paths.repo_root),
        "legacy_file": str(paths.legacy_file),
        "allowlist_path": str(paths.allowlist_path) if paths.allowlist_path.exists() else None,
        "artifacts_to_keep": options.artifacts_to_keep,
        "include_repo_studios": include_repo_studios,
    }
    manifest = compose_manifest(report=report, run_timestamp=run_timestamp, inputs=inputs)
    telemetry = compose_telemetry(report=report)
    summary_md = render_summary_markdown(report=report, run_timestamp=run_timestamp)

    output_dir = paths.output_dir
    # output_dir already contains full topic path - pass empty viewer/topic
    storage = create_storage(output_dir, "", "", timestamp=run_timestamp)

    # DB_INTEGRATION_MARKER: metrics anchor stub validation manifest
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: metrics anchor stub validation summary markdown
    storage.write_summary({"markdown": summary_md}, format="markdown")
    # DB_INTEGRATION_MARKER: metrics anchor stub validation telemetry
    storage.write_telemetry(telemetry)

    # output_dir already contains full topic path
    run_dir = output_dir / run_timestamp
    removed = prune_history(
        output_dir,
        options.artifacts_to_keep,
        current_run=run_dir,
        logger=logger,
    )
    if removed:
        logger.debug("Pruned metrics anchor runs: %s", ", ".join(sorted(path.name for path in removed)))

    if report["summary"]["missing_count"] == 0:
        logger.info("[metrics-anchor-stubs] OK — no missing anchors detected")
    else:
        logger.error(
            "[metrics-anchor-stubs] Missing anchors detected (%s)",
            report["summary"]["missing_count"],
        )
        for entry in report["missing"]:
            logger.error("  - %s: %s", entry.get("anchor"), ", ".join(entry.get("files", [])))

    return {
        "status": report.get("status", "ok"),
        "viewer_slug": "producer_reports",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_timestamp,
        "output_dir": str(output_dir),
        "summary": report.get("summary", {}),
        "missing": report.get("missing", []),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for metrics anchor stub validation.

    Run the validation workflow and return the exit code.

    Args:
        argv: Command-line arguments. Uses sys.argv[1:] if None.

    Returns:
        Integer exit code (0 for success, 1 for failures).
    """
    payload = run(argv)
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
