"""Audit report naming compliance for Command Center artifacts."""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
_TIMESTAMP_PATTERN = re.compile(r"^\d{8}-\d{4}$")
_DEFAULT_ARTIFACT_ROLES = (
    "manifest.json",
    "summary.md",
    "summary.json",
    "matrix.json",
    "matrix.csv",
    "matrix.tsv",
    "telemetry.json",
    "report.md",
    "report.json",
    "metrics.json",
    "metrics.md",
)
_DEFAULT_VIEWERS = ("commandview", "rawview", "healthview", "jarvis", "vscode")


@dataclass(frozen=True)
class AuditEntry:
    path: Path
    issues: list[str]

    @property
    def is_compliant(self) -> bool:
        return not self.issues


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan report folders for naming compliance.")
    parser.add_argument(
        "--reports-root",
        default=".repo_studios/command_center/reports",
        help="Root directory containing report artifacts (default: %(default)s).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for audit outputs. Defaults to <reports-root>/reports_naming_audit/<timestamp>.",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Explicit path for the JSON summary. Overrides --output-dir placement when provided.",
    )
    parser.add_argument(
        "--markdown-output",
        default=None,
        help="Explicit path for the Markdown summary. Overrides --output-dir placement when provided.",
    )
    parser.add_argument(
        "--artifact-roles",
        nargs="*",
        default=None,
        help="Accepted artifact filenames (default set includes manifest.json, summary.md, etc.).",
    )
    parser.add_argument(
        "--allowed-viewers",
        nargs="*",
        default=None,
        help="Optional allowlist of viewer slugs. Defaults to commandview, rawview, healthview, jarvis, vscode.",
    )
    parser.add_argument(
        "--ignore-prefix",
        nargs="*",
        default=(),
        help="Relative path prefixes to ignore (e.g., legacy directories).",
    )
    parser.add_argument(
        "--fail-threshold",
        type=int,
        default=0,
        help="Maximum allowed violation count before exiting with a non-zero status (default: 0).",
    )
    parser.add_argument(
        "--dry-run-rename",
        action="store_true",
        help="Suggest compliant target paths for non-conforming artifacts without mutating files.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: %(default)s).",
    )
    return parser.parse_args(argv)


def _should_ignore(rel_path: Path, prefixes: Iterable[str]) -> bool:
    posix_path = rel_path.as_posix()
    for prefix in prefixes:
        if posix_path.startswith(prefix.rstrip("/")):
            return True
    return False


def _issues_for_path(
    rel_path: Path,
    *,
    artifact_roles: set[str],
    allowed_viewers: set[str] | None,
) -> list[str]:
    issues: list[str] = []
    parts = rel_path.parts
    normalized_parts = [part.lower() for part in parts]
    if any(part.startswith("latest") for part in normalized_parts):
        issues.append("latest_alias_present")
    if len(parts) < 4:
        issues.append("insufficient_depth")
        return issues
    if len(parts) > 4:
        issues.append("unexpected_nesting")
    viewer, topic, timestamp = parts[0], parts[1], parts[2]
    filename = parts[-1]
    if not _SLUG_PATTERN.match(viewer):
        issues.append("invalid_viewer_slug")
    elif allowed_viewers is not None and viewer not in allowed_viewers:
        issues.append("unexpected_viewer_slug")
    if not _SLUG_PATTERN.match(topic):
        issues.append("invalid_topic_slug")
    if not _TIMESTAMP_PATTERN.match(timestamp):
        issues.append("invalid_timestamp")
    if filename.lower().startswith("latest"):
        if "latest_alias_present" not in issues:
            issues.append("latest_alias_present")
    if len(parts) == 4 and filename not in artifact_roles:
        issues.append("unexpected_artifact_name")
    return issues


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    return normalized or value.lower()


def _suggest_timestamp(segment: str) -> str | None:
    if _TIMESTAMP_PATTERN.match(segment):
        return segment
    digits = re.findall(r"\d", segment)
    if len(digits) >= 12:
        candidate = "".join(digits[:12])
        return f"{candidate[:8]}-{candidate[8:12]}"
    return None


def _suggest_filename(filename: str, artifact_roles: set[str]) -> str | None:
    if filename in artifact_roles:
        return filename
    lower = filename.lower()
    for role in artifact_roles:
        if role.lower() == lower:
            return role
    return None


def _suggest_rename(rel_path: Path, *, artifact_roles: set[str]) -> Path | None:
    parts = list(rel_path.parts)
    if len(parts) < 4:
        return None
    viewer = _slugify(parts[0])
    topic = _slugify(parts[1])
    timestamp = _suggest_timestamp(parts[2])
    if timestamp is None:
        return None
    tail = parts[3:]
    if not tail:
        return None
    directories = [_slugify(segment) for segment in tail[:-1]]
    filename = _suggest_filename(tail[-1], artifact_roles)
    if filename is None:
        return None
    candidate_parts = [viewer, topic, timestamp, *directories, filename]
    return Path(*candidate_parts)


def audit_reports(
    reports_root: Path,
    *,
    artifact_roles: Iterable[str],
    allowed_viewers: Iterable[str] | None,
    ignore_prefixes: Iterable[str],
    collect_suggestions: bool = False,
) -> dict[str, object]:
    roles = {role for role in artifact_roles}
    if not roles:
        roles = set(_DEFAULT_ARTIFACT_ROLES)
    viewers = {viewer for viewer in allowed_viewers} if allowed_viewers is not None else None
    files_scanned = 0
    entries: list[AuditEntry] = []
    latest_aliases: list[str] = []
    if not reports_root.exists():
        logging.warning("Reports root %s does not exist; returning empty audit.", reports_root)
        timestamp = datetime.now(timezone.utc).isoformat()
        return {
            "reports_root": str(reports_root),
            "timestamp": timestamp,
            "total_files": 0,
            "compliant_files": 0,
            "violations": [],
            "issue_totals": {},
            "latest_aliases": [],
            "artifact_roles": sorted(roles),
        }
    for path in sorted(reports_root.rglob("*")):
        if not path.is_file():
            continue
        rel_path = path.relative_to(reports_root)
        if _should_ignore(rel_path, ignore_prefixes):
            continue
        files_scanned += 1
        issues = _issues_for_path(rel_path, artifact_roles=roles, allowed_viewers=viewers)
        entry = AuditEntry(path=rel_path, issues=issues)
        entries.append(entry)
        if any(issue == "latest_alias_present" for issue in issues):
            latest_aliases.append(rel_path.as_posix())
    issue_totals: dict[str, int] = {}
    violations: list[dict[str, object]] = []
    compliant = 0
    rename_suggestions: list[dict[str, str]] = []
    for entry in entries:
        if entry.is_compliant:
            compliant += 1
            continue
        violations.append({"path": entry.path.as_posix(), "issues": entry.issues})
        for issue in entry.issues:
            issue_totals[issue] = issue_totals.get(issue, 0) + 1
        if collect_suggestions:
            suggestion = _suggest_rename(entry.path, artifact_roles=roles)
            if suggestion is not None and suggestion.as_posix() != entry.path.as_posix():
                rename_suggestions.append(
                    {"current": entry.path.as_posix(), "suggested": suggestion.as_posix()}
                )
    timestamp = datetime.now(timezone.utc).isoformat()
    summary: dict[str, object] = {
        "reports_root": str(reports_root),
        "timestamp": timestamp,
        "total_files": files_scanned,
        "compliant_files": compliant,
        "violation_count": len(violations),
        "compliance_ratio": float(compliant) / float(files_scanned) if files_scanned else 1.0,
        "violations": violations,
        "issue_totals": issue_totals,
        "latest_aliases": sorted(set(latest_aliases)),
        "artifact_roles": sorted(roles),
        "allowed_viewers": sorted(viewers) if viewers is not None else None,
        "ignore_prefixes": list(ignore_prefixes),
        "rename_suggestions": rename_suggestions if collect_suggestions else [],
    }
    return summary


def _default_output_dir(reports_root: Path, now: datetime) -> Path:
    return reports_root / "reports_naming_audit" / now.strftime("%Y%m%d-%H%M%S")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_markdown(path: Path, payload: dict[str, object]) -> None:
    lines: list[str] = []
    lines.append("# Report Naming Audit")
    lines.append("")
    lines.append(f"- Reports root: `{payload['reports_root']}`")
    lines.append(f"- Generated at: {payload['timestamp']}")
    lines.append(f"- Scanned files: {payload['total_files']}")
    lines.append(f"- Compliant files: {payload['compliant_files']}")
    lines.append(f"- Violations: {payload['violation_count']}")
    ratio = payload.get("compliance_ratio", 0.0)
    lines.append(f"- Compliance ratio: {ratio:.4f}")
    lines.append("")
    issue_totals = payload.get("issue_totals", {})
    if issue_totals:
        lines.append("## Issue Totals")
        lines.append("")
        lines.append("| Issue | Count |")
        lines.append("| --- | --- |")
        for issue, count in sorted(issue_totals.items()):
            lines.append(f"| {issue} | {count} |")
        lines.append("")
    violations = payload.get("violations", [])
    if violations:
        lines.append("## Violations")
        lines.append("")
        lines.append("| Path | Issues |")
        lines.append("| --- | --- |")
        for entry in violations:
            joined = ", ".join(entry["issues"])
            lines.append(f"| `{entry['path']}` | {joined} |")
        lines.append("")
    else:
        lines.append("## Violations")
        lines.append("")
        lines.append("No violations detected.")
        lines.append("")
    latest_aliases = payload.get("latest_aliases", [])
    if latest_aliases:
        lines.append("## Latest Aliases")
        lines.append("")
        for alias in latest_aliases:
            lines.append(f"- `{alias}`")
        lines.append("")
    suggestions = payload.get("rename_suggestions", [])
    if suggestions:
        lines.append("## Rename Suggestions")
        lines.append("")
        lines.append("| Current Path | Suggested Path |")
        lines.append("| --- | --- |")
        for suggestion in suggestions:
            lines.append(f"| `{suggestion['current']}` | `{suggestion['suggested']}` |")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(argv: Sequence[str] | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(levelname)s %(message)s")
    reports_root = Path(args.reports_root).expanduser().resolve()
    now = datetime.now(timezone.utc)
    summary = audit_reports(
        reports_root,
        artifact_roles=args.artifact_roles or _DEFAULT_ARTIFACT_ROLES,
        allowed_viewers=args.allowed_viewers or _DEFAULT_VIEWERS,
        ignore_prefixes=args.ignore_prefix,
        collect_suggestions=args.dry_run_rename,
    )
    threshold = max(args.fail_threshold, 0)
    summary["fail_threshold"] = threshold
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else _default_output_dir(reports_root, now)
    json_path = Path(args.json_output).expanduser().resolve() if args.json_output else output_dir / "summary.json"
    markdown_path = (
        Path(args.markdown_output).expanduser().resolve() if args.markdown_output else output_dir / "summary.md"
    )
    logging.info("Writing JSON summary to %s", json_path)
    _write_json(json_path, summary)
    logging.info("Writing Markdown summary to %s", markdown_path)
    _write_markdown(markdown_path, summary)
    if args.dry_run_rename and summary.get("rename_suggestions"):
        for entry in summary["rename_suggestions"]:
            logging.info("Suggest rename: %s -> %s", entry["current"], entry["suggested"])
    violations = int(summary.get("violation_count", 0))
    threshold = summary.get("fail_threshold", 0)
    if violations > threshold:
        logging.error("Violation count %s exceeds threshold %s", violations, threshold)
    else:
        logging.info("Violation count %s within threshold %s", violations, threshold)
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    summary = run(argv)
    violations = int(summary.get("violation_count", 0))
    threshold = int(summary.get("fail_threshold", 0))
    return 1 if violations > threshold else 0


if __name__ == "__main__":
    raise SystemExit(main())
