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

REPORTS_ROOT = Path(".repo_studios/reports/producer_reports")
DEFAULT_OUTPUT_DIR = REPORTS_ROOT
DEFAULT_LEGACY_FILE = Path("docs/api/metrics_orchestrator.md")
DEFAULT_ALLOWLIST_PATH = Path(".repo_studios/scripts/producers/metrics_anchor_allowlist.json")
SCHEMA_VERSION = 1
VIEWER_SLUG = "healthview"
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
    from libraries.retention_policy import get_keep

try:
    from libraries.database_integration import create_storage
except ModuleNotFoundError:  # pragma: no cover - fallback for script execution without package path
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries.database_integration import create_storage

# Must be after import block where get_keep is defined
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("validate_metrics_anchor_stubs")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    legacy_file: Path
    allowlist_path: Path


@dataclass(frozen=True)
class Options:
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
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    return cast(Options, build_standard_options(args, OPTIONS_CONFIG))


def _format_run_timestamp(timestamp: dt.datetime) -> str:
    return timestamp.astimezone(dt.timezone.utc).strftime("%Y%m%d-%H%M")


def _normalize_anchor(text: str) -> str:
    normalized = text.strip().lower().replace("`", "")
    normalized = re.sub(r"\s+", "-", normalized)
    return re.sub(r"[^a-z0-9._-]", "", normalized)


def iter_markdown_files(repo_root: Path) -> Iterable[Path]:
    for path in repo_root.rglob("*.md"):
        rel = path.relative_to(repo_root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if rel.parts[0] in {"vendor", "external"}:
            continue
        yield path


def collect_referenced_anchors(files: Iterable[Path], repo_root: Path) -> dict[str, list[str]]:
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
    timestamp: dt.datetime,
) -> dict[str, Any]:
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
        "summary": summary,
        "missing": missing,
        "referenced_anchors": sorted(referenced.keys()),
        "legacy_anchors": sorted(legacy),
        "allowlisted_anchors": sorted(allowlist),
    }


def compose_manifest(*, report: dict[str, Any], run_timestamp: str, inputs: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    return {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
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
    summary = report.get("summary", {})
    status = report.get("status", "ok")
    lines: list[str] = [
        "# Metrics Anchor Stub Validation\n\n",
        f"- Status: `{status}`\n",
        f"- Run Timestamp (UTC): `{run_timestamp}`\n",
        f"- Legacy File: `{report.get('legacy_file', '')}`\n",
        f"- Allowlist: `{report.get('allowlist_path') or 'none'}`\n",
        f"- Files Checked: {summary.get('files_checked', 0)}\n",
        f"- Anchors Referenced: {summary.get('anchors_referenced', 0)}\n",
        f"- Legacy Stub Count: {summary.get('legacy_stub_count', 0)}\n",
        f"- Missing Anchors: {summary.get('missing_count', 0)}\n",
        f"- Allowlisted Anchors: {summary.get('allowlisted_count', 0)}\n",
    ]

    missing = report.get("missing", [])
    if missing:
        lines.append("\n## Missing Anchors\n\n")
        lines.append("| Anchor | Referenced In |\n| --- | --- |")
        for entry in missing:
            files = "<br>".join(entry.get("files", [])) or "—"
            lines.append(f"\n| `{entry.get('anchor')}` | {files} |")

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
    result = prune_run_directories(
        base_dir,
        keep=max(keep, 1),
        current_run=current_run,
        logger=logger,
    )
    return result.removed


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    configure_logging(args.log_level)
    logger = logging.getLogger(__name__)
    paths = build_paths(args)
    options = build_options(args)
    paths.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Repo root: %s", paths.repo_root)
    logger.info("Output directory: %s", paths.output_dir)
    logger.info("Legacy file: %s", paths.legacy_file)

    markdown_files = list(iter_markdown_files(paths.repo_root))
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
        timestamp=timestamp,
    )

    inputs: dict[str, Any] = {
        "repo_root": str(paths.repo_root),
        "legacy_file": str(paths.legacy_file),
        "allowlist_path": str(paths.allowlist_path) if paths.allowlist_path.exists() else None,
        "artifacts_to_keep": options.artifacts_to_keep,
    }
    manifest = compose_manifest(report=report, run_timestamp=run_timestamp, inputs=inputs)
    telemetry = compose_telemetry(report=report)
    summary_md = render_summary_markdown(report=report, run_timestamp=run_timestamp)

    output_dir = paths.output_dir
    storage = create_storage(output_dir, VIEWER_SLUG, TOPIC_SLUG, timestamp=run_timestamp)

    # DB_INTEGRATION_MARKER: metrics anchor stub validation manifest
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: metrics anchor stub validation summary markdown
    storage.write_summary({"markdown": summary_md}, format="markdown")
    # DB_INTEGRATION_MARKER: metrics anchor stub validation telemetry
    storage.write_telemetry(telemetry)

    run_dir = output_dir / VIEWER_SLUG / TOPIC_SLUG / run_timestamp
    removed = prune_history(
        run_dir.parent,
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
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": run_timestamp,
        "output_dir": str(output_dir),
        "summary": report.get("summary", {}),
        "missing": report.get("missing", []),
    }


def main(argv: list[str] | None = None) -> int:
    payload = run(argv)
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
