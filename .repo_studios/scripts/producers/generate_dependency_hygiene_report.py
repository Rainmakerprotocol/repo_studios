#!/usr/bin/env python3
"""Dependency hygiene scanner with structured artifacts and pruning support.

This producer reports risky dependency specifications (unpinned constraints, VCS refs,
editable installs, local paths, and duplicates) across the repo's dependency manifests.

Artifacts (default):
    - `.repo_studios/reports/producer_reports/healthview/dependency_hygiene/<YYYYMMDD-HHMM>/`
        - `manifest.json`
        - `summary.md`
        - `telemetry.json`

Exit codes:
    0 success (no hygiene issues detected)
    1 hygiene issues detected
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore


ROOT = Path(__file__).resolve().parents[2]

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARIES_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories
    from libraries.cli import resolve_repo_root
    from libraries.retention_policy import get_keep
    from libraries.report_paths import build_topic_path
except ModuleNotFoundError:  # pragma: no cover - fallback for script execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories
    from libraries.cli import resolve_repo_root
    from libraries.retention_policy import get_keep
    from libraries.report_paths import build_topic_path

TOPIC_SLUG = "dependency_hygiene"
DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("generate_dependency_hygiene_report")
DEFAULT_REQ_PATTERNS: tuple[str, ...] = (
    "requirements.txt",
    "requirements-dev.txt",
    "requirements/*.txt",
)


@dataclass
class Issue:
    kind: str
    file: str
    line: int
    spec: str


def _rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path.resolve())


def _iter_req_files(root: Path, patterns: Sequence[str]) -> list[Path]:
    files: set[Path] = set()
    for pat in patterns:
        files.update(root.glob(pat))
    return sorted(p for p in files if p.exists())


def _parse_requirements_file(path: Path, *, repo_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    seen: dict[str, list[str]] = {}
    for i, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r ", "--requirement")):
            continue
        file_str = _rel_path(path, repo_root)
        if line.startswith(("-e ", "--editable")):
            issues.append(Issue("editable_install", file_str, i, raw))
            continue
        if re.match(r"^(git\+|hg\+|svn\+|bzr\+)", line):
            issues.append(Issue("vcs_ref", file_str, i, raw))
        if re.match(r"^\./|^\.\.|^/", line):
            issues.append(Issue("local_path", file_str, i, raw))

        # Split on version specifiers
        name = re.split(r"[<>=!~]", line)[0].strip()
        if name:
            seen.setdefault(name.lower(), []).append(line)
        # Pinning check: prefer '==' exact pins
        if "==" not in line:
            issues.append(Issue("unpinned", file_str, i, raw))
    # Duplicates
    for pkg, specs in seen.items():
        if len(specs) > 1:
            issues.append(Issue("duplicate", file_str, 0, f"{pkg}: {specs}"))
    return issues


def _parse_pyproject(path: Path, *, repo_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    if tomllib is None or not path.exists():
        return issues
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:  # pragma: no cover - malformed TOML handled upstream
        return issues
    # PEP 621 / Poetry dependencies
    deps = data.get("project", {}).get("dependencies", []) or data.get("tool", {}).get("poetry", {}).get(
        "dependencies", {}
    )
    if isinstance(deps, dict):
        items = [(k, str(v)) for k, v in deps.items() if k != "python"]
    else:
        items = [(d, d) for d in deps]
    file_str = _rel_path(path, repo_root)
    for raw_name, spec in items:
        pinned = "==" in spec or re.fullmatch(r"\d+\.\d+(\.\d+)?", spec) is not None
        if not pinned:
            issues.append(Issue("unpinned", file_str, 0, f"{raw_name} {spec}"))
        if re.match(r"^(git\+|hg\+|svn\+|bzr\+)", spec):
            issues.append(Issue("vcs_ref", file_str, 0, f"{raw_name} {spec}"))
    return issues


def _collect_issues(
    repo_root: Path,
    *,
    patterns: Sequence[str],
    include_pyproject: bool,
) -> tuple[list[Issue], list[Path], Path | None]:
    req_files = _iter_req_files(repo_root, patterns)
    issues: list[Issue] = []
    for req in req_files:
        issues.extend(_parse_requirements_file(req, repo_root=repo_root))

    pyproject_path = repo_root / "pyproject.toml"
    pyproject_used: Path | None = None
    if include_pyproject and pyproject_path.exists():
        issues.extend(_parse_pyproject(pyproject_path, repo_root=repo_root))
        pyproject_used = pyproject_path

    return issues, req_files, pyproject_used


def _issue_counts(issues: Iterable[Issue]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for issue in issues:
        counts[issue.kind] = counts.get(issue.kind, 0) + 1
    return [{"kind": kind, "count": counts[kind]} for kind in sorted(counts, key=lambda k: (-counts[k], k))]


def build_report(
    *,
    issues: list[Issue],
    repo_root: Path,
    requirements: list[Path],
    pyproject: Path | None,
    generated_ts: datetime,
    patterns: Sequence[str],
) -> dict[str, Any]:
    status = "failed" if issues else "passed"
    summary = {
        "status": status,
        "issue_count": len(issues),
        "requirements_scanned": len(requirements),
        "pyproject_scanned": bool(pyproject),
    }
    issue_entries = [
        {"kind": issue.kind, "file": issue.file, "line": issue.line, "spec": issue.spec} for issue in issues
    ]
    return {
        "schema_version": 1,
        "generated_utc": generated_ts.isoformat(),
        "repo_root": str(repo_root),
        "summary": summary,
        "issue_counts": _issue_counts(issues),
        "requirements_patterns": list(patterns),
        "requirements_files": [str(_rel_path(path, repo_root)) for path in requirements],
        "pyproject_path": str(_rel_path(pyproject, repo_root)) if pyproject else None,
        "issues": issue_entries,
    }


def write_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Dependency Hygiene Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Repo Root: {report['repo_root']}",
        "",
        "## Summary",
        "",
        f"- status: {report['summary']['status']}",
        f"- issue count: {report['summary']['issue_count']}",
        f"- requirements scanned: {report['summary']['requirements_scanned']}",
        f"- pyproject scanned: {str(report['summary']['pyproject_scanned']).lower()}",
        "",
        "## Issue Counts",
        "",
    ]
    counts = report.get("issue_counts", [])
    if not counts:
        lines.append("- (none)")
    else:
        for entry in counts:
            lines.append(f"- {entry['kind']}: {entry['count']}")

    lines.extend(["", "## Issues", ""])
    issues = report.get("issues", [])
    if not issues:
        lines.append("- (none)")
    else:
        for entry in issues:
            location = f"{entry['file']}:{entry['line']}" if entry.get("line") else entry["file"]
            lines.append(f"- [{entry['kind']}] {location} — {entry['spec']}")

    return "\n".join(lines) + "\n"


def write_log(report: dict[str, Any]) -> str:
    lines = [
        f"status={report['summary']['status']}",
        f"issue_count={report['summary']['issue_count']}",
        f"requirements_scanned={report['summary']['requirements_scanned']}",
        f"pyproject_scanned={int(report['summary']['pyproject_scanned'])}",
        "issue_counts:",
    ]
    for entry in report.get("issue_counts", []):
        lines.append(f"  {entry['kind']}={entry['count']}")
    lines.append("issues:")
    for issue in report.get("issues", []):
        location = f"{issue['file']}:{issue['line']}" if issue.get("line") else issue["file"]
        lines.append(f"  {issue['kind']} -> {location} :: {issue['spec']}")
    if report["summary"]["status"] == "failed":
        lines.append("failure_reason=dependency hygiene issues detected")
    return "\n".join(lines) + "\n"


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def _build_manifest(*, report: dict[str, Any], repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "run_timestamp": report.get("generated_utc"),
        "git_sha": None,
        "status": "ok" if report.get("summary", {}).get("status") == "passed" else "failed",
        "catalog": [
            {"artifact": "manifest.json", "kind": "json"},
            {"artifact": "summary.md", "kind": "markdown"},
            {"artifact": "telemetry.json", "kind": "json"},
        ],
        "inputs": {
            "repo_root": str(repo_root),
            **inputs,
        },
        "provenance": {
            "trigger_type": "manual",
        },
        "summary": report.get("summary", {}),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate dependency hygiene report (offline)")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Base directory for generated report bundles (e.g., .repo_studios/reports/producer_reports)",
    )
    parser.add_argument(
        "--requirements-pattern",
        action="append",
        dest="requirements_patterns",
        help="Glob pattern(s) for requirements files (defaults applied if omitted)",
    )
    parser.add_argument(
        "--skip-pyproject",
        action="store_true",
        help="Skip scanning pyproject.toml dependencies",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="How many historical runs to retain",
    )
    parser.add_argument(
        "--timestamp",
        help="ISO timestamp for run directory naming (UTC if absent)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    args = parser.parse_args(argv)

    configure_logging(args.log_level)

    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (repo_root / output_dir).resolve()

    patterns = args.requirements_patterns if args.requirements_patterns else list(DEFAULT_REQ_PATTERNS)

    issues, requirements, pyproject = _collect_issues(
        repo_root,
        patterns=patterns,
        include_pyproject=not args.skip_pyproject,
    )

    generated_ts = _parse_timestamp(args.timestamp)
    report = build_report(
        issues=issues,
        repo_root=repo_root,
        requirements=requirements,
        pyproject=pyproject,
        generated_ts=generated_ts,
        patterns=patterns,
    )

    timestamp = generated_ts.strftime("%Y%m%d-%H%M")
    inputs = {
        "requirements_patterns": list(patterns),
        "skip_pyproject": bool(args.skip_pyproject),
        "artifacts_to_keep": args.artifacts_to_keep,
    }

    manifest = _build_manifest(report=report, repo_root=repo_root, inputs=inputs)
    telemetry: dict[str, Any] = {
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp,
        "generated_utc": report.get("generated_utc"),
        "metrics": {
            "status": report.get("summary", {}).get("status"),
            "issue_count": report.get("summary", {}).get("issue_count"),
            "requirements_scanned": report.get("summary", {}).get("requirements_scanned"),
            "pyproject_scanned": report.get("summary", {}).get("pyproject_scanned"),
            "issue_counts": report.get("issue_counts", []),
        },
        "payload": report,
    }

    storage = create_storage(
        output_dir=output_dir,
        viewer_slug="",
        topic="",
        timestamp=timestamp,
    )

    markdown = write_markdown(report)

    # DB_INTEGRATION_MARKER: write manifest.json (report_runs)
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: write summary.md (report_summaries)
    storage.write_summary({"markdown": markdown}, format="markdown")
    # DB_INTEGRATION_MARKER: write telemetry.json + extracted metrics (test_metrics)
    storage.write_telemetry(telemetry)

    run_dir = storage.file_storage.bundle_dir
    topic_dir = run_dir.parent
    prune_result = prune_run_directories(
        topic_dir,
        keep=args.artifacts_to_keep,
        current_run=run_dir,
        logger=logging.getLogger(__name__),
    )
    logging.debug(
        "Pruned dependency hygiene bundles: kept=%s removed=%s protected=%s failures=%s",
        len(prune_result.kept),
        len(prune_result.removed),
        len(prune_result.protected),
        len(prune_result.failures),
    )

    logging.info("Dependency hygiene report written to %s", run_dir)

    return 1 if issues else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
