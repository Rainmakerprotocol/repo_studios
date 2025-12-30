#!/usr/bin/env python3
"""Code ↔ documentation churn detector with structured artifacts."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports")
RUN_PREFIX = "code_doc_churn"
DEFAULT_GIT_WINDOW = "14 days"
ALLOWED_CODE_EXTENSIONS = {
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".kt",
    ".kts",
    ".swift",
    ".go",
    ".rb",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".scala",
    ".sql",
}

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:  # pragma: no cover - import guard for standalone execution
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback when script is run directly
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories
    from libraries.retention_policy import get_keep

DEFAULT_ARTIFACTS_TO_KEEP = get_keep("generate_code_doc_churn_report")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    doc_index: Path
    anchor_inventory: Path
    allowlist: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int


PATH_SPECS: dict[str, PathSpec] = {
    "output_dir": PathSpec(
        field="output_dir",
        default=DEFAULT_OUTPUT_DIR,
        ensure_dir=True,
        within_repo=True,
    ),
    "doc_index": PathSpec(
        field="doc_index",
        default=Path(".repo_studios/reports/healthview/producer_reports/doc_index"),
        ensure_dir=False,
        within_repo=True,
    ),
    "anchor_inventory": PathSpec(
        field="anchor_inventory",
        default=Path(".repo_studios/reports/producer_reports/healthview/anchor_inventory"),
        ensure_dir=False,
        within_repo=True,
    ),
    "allowlist": PathSpec(
        field="allowlist",
        default=Path(".repo_studios/config/code_doc_churn_allowlist.txt"),
        ensure_dir=False,
        within_repo=True,
    ),
}

PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs=PATH_SPECS,
    repo_root_depth=4,
)

KEEP_SPECS: dict[str, KeepSpec] = {
    "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
}

OPTIONS_CONFIG = OptionsConfig(dataclass_type=Options, keep_specs=KEEP_SPECS)


@dataclass
class ModuleActivity:
    module: str
    code_paths: set[str] = field(default_factory=set)
    doc_paths: set[str] = field(default_factory=set)
    commit_hashes: set[str] = field(default_factory=set)
    authors: set[str] = field(default_factory=set)
    last_commit_utc: datetime | None = None

    def to_payload(self, *, doc_candidates: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "module": self.module,
            "code_paths": sorted(self.code_paths),
            "doc_paths": sorted(self.doc_paths),
            "commit_hashes": sorted(self.commit_hashes),
            "authors": sorted(self.authors),
            "last_commit_utc": self.last_commit_utc.isoformat() if self.last_commit_utc else None,
            "doc_candidates": doc_candidates,
        }


@dataclass
class GitMetadata:
    commits_examined: int
    authors: set[str]
    head_commit: str | None
    window: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "window": self.window,
            "commits_examined": self.commits_examined,
            "distinct_authors": len(self.authors),
            "authors": sorted(self.authors),
            "head_commit": self.head_commit,
        }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate code/doc churn discrepancy report")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--output-dir", help="Directory for report artifacts")
    parser.add_argument("--doc-index", help="Path to latest doc index JSON")
    parser.add_argument("--anchor-inventory", help="Path to latest anchor inventory JSON")
    parser.add_argument("--allowlist", help="Path to module allowlist (one module per line)")
    parser.add_argument(
        "--git-window",
        default=DEFAULT_GIT_WINDOW,
        help="Git log window for churn detection (passed to git --since)",
    )
    parser.add_argument(
        "--git-until",
        help="Optional git --until value to cap the window",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention count for timestamped runs",
    )
    return parser.parse_args(argv)


def _read_allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    entries = {line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()}
    return {item for item in entries if item}


def _git(args: Sequence[str], *, repo_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "--no-pager", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _collect_commits(repo_root: Path, *, window: str, until: str | None) -> tuple[list[dict[str, Any]], set[str]]:
    base_args = ["log", f"--since={window}", "--date=iso", "--name-status", "--pretty=format:%H\x01%an\x01%ad"]
    if until:
        base_args.append(f"--until={until}")
    base_args.append("--")
    result = _git(base_args, repo_root=repo_root)
    stdout = result.stdout.strip()
    if result.returncode != 0:
        # Repos with no commits or outside window produce exit code 128; treat as empty.
        return [], set()
    if not stdout:
        return [], set()
    commits: list[dict[str, Any]] = []
    authors: set[str] = set()
    current: dict[str, Any] | None = None
    for raw in stdout.splitlines():
        if "\x01" in raw:
            parts = raw.split("\x01")
            if len(parts) >= 3:
                commit_hash, author, when = parts[:3]
                current = {
                    "hash": commit_hash,
                    "author": author,
                    "date": when,
                    "files": [],
                }
                commits.append(current)
                authors.add(author)
            continue
        if current is None or not raw:
            continue
        segments = raw.split("\t")
        if not segments:
            continue
        status = segments[0]
        if len(segments) == 2:
            path = segments[1]
        elif len(segments) > 2:
            path = segments[-1]
        else:
            continue
        current["files"].append({"status": status, "path": path})
    return commits, authors


def _module_key(path: str) -> str:
    path = path.strip().lstrip("./")
    if not path:
        return "root"
    parts = path.split("/")
    if parts[0] == "docs":
        if len(parts) >= 3:
            return parts[1]
        if len(parts) == 2:
            return Path(parts[1]).stem or "docs"
        return "docs"
    if parts[0] == ".repo_studios" and len(parts) > 1:
        if parts[1] == "docs" and len(parts) > 2:
            if len(parts) >= 4:
                return parts[2]
            return Path(parts[2]).stem or parts[2]
        return parts[1]
    return parts[0]


def _is_doc_path(path: str) -> bool:
    normalized = path.lower()
    if normalized.startswith("docs/"):
        return True
    if normalized.startswith(".repo_studios/docs/"):
        return True
    return normalized.endswith(".md") or normalized.endswith(".mdx")


def _is_code_path(path: str) -> bool:
    if _is_doc_path(path):
        return False
    suffix = Path(path).suffix.lower()
    return suffix in ALLOWED_CODE_EXTENSIONS


def _parse_datetime(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _latest_run_dir(topic_dir: Path) -> Path | None:
    if not topic_dir.exists() or not topic_dir.is_dir():
        return None
    runs = [node for node in topic_dir.iterdir() if node.is_dir()]
    if not runs:
        return None
    runs.sort(key=lambda node: (node.name, node.stat().st_mtime), reverse=True)
    return runs[0]


def _load_doc_index(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}

    candidate = path
    if candidate.is_dir():
        latest = _latest_run_dir(candidate)
        if latest is None:
            return {}
        telemetry_path = latest / "telemetry.json"
        if telemetry_path.exists():
            candidate = telemetry_path
        else:
            return {}

    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    if isinstance(payload, dict) and "payload" in payload:
        payload = payload.get("payload", {})

    documents = payload.get("documents", []) if isinstance(payload, dict) else []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for doc in documents:
        filename = doc.get("filename") or doc.get("path")
        if not filename:
            continue
        module = _module_key(filename)
        grouped.setdefault(module, []).append(
            {
                "path": filename,
                "owners": doc.get("owners", []),
                "modified_utc": doc.get("modified_utc"),
            }
        )
    return grouped


def _build_module_activity(
    commits: Iterable[dict[str, Any]],
    *,
    allowlist: set[str],
) -> tuple[list[ModuleActivity], list[ModuleActivity]]:
    activity: dict[str, ModuleActivity] = {}
    for commit in commits:
        commit_hash = commit.get("hash")
        author = commit.get("author")
        when_str = commit.get("date")
        when = _parse_datetime(when_str) if isinstance(when_str, str) else None
        files = commit.get("files", [])
        for entry in files:
            path = entry.get("path")
            if not isinstance(path, str) or not path:
                continue
            path = path.replace("\\", "/")
            module = _module_key(path)
            bucket = activity.setdefault(module, ModuleActivity(module=module))
            if commit_hash:
                bucket.commit_hashes.add(commit_hash)
            if author:
                bucket.authors.add(author)
            if when and (bucket.last_commit_utc is None or when > bucket.last_commit_utc):
                bucket.last_commit_utc = when
            if _is_doc_path(path):
                bucket.doc_paths.add(path)
            elif _is_code_path(path):
                bucket.code_paths.add(path)
    flagged: list[ModuleActivity] = []
    doc_updated: list[ModuleActivity] = []
    for module, bucket in activity.items():
        if not bucket.code_paths:
            continue
        if module in allowlist:
            continue
        if bucket.doc_paths:
            doc_updated.append(bucket)
            continue
        flagged.append(bucket)
    flagged.sort(key=lambda b: (-len(b.code_paths), b.module))
    doc_updated.sort(key=lambda b: (-len(b.doc_paths), b.module))
    return flagged, doc_updated


def build_report(
    *,
    repo_root: Path,
    window: str,
    commits: list[dict[str, Any]],
    authors: set[str],
    flagged: list[ModuleActivity],
    doc_updated: list[ModuleActivity],
    allowlist: set[str],
    doc_index: dict[str, list[dict[str, Any]]],
    generated_ts: datetime,
    head_commit: str | None,
    doc_index_path: Path,
    anchor_inventory_path: Path,
) -> dict[str, Any]:
    git_meta = GitMetadata(
        commits_examined=len(commits),
        authors=authors,
        head_commit=head_commit,
        window=window,
    )
    modules_payload = [bucket.to_payload(doc_candidates=doc_index.get(bucket.module, [])) for bucket in flagged]
    updated_payload = [bucket.to_payload(doc_candidates=doc_index.get(bucket.module, [])) for bucket in doc_updated]
    summary = {
        "modules_with_code_churn": len([bucket for bucket in (flagged + doc_updated)]),
        "modules_without_doc_updates": len(flagged),
        "modules_with_doc_updates": len(doc_updated),
        "allowlisted_modules": sorted(allowlist),
    }
    return {
        "schema_version": 1,
        "generated_utc": generated_ts.isoformat(),
        "repo_root": str(repo_root),
        "git": git_meta.to_payload(),
        "summary": summary,
        "modules_missing_docs": modules_payload,
        "modules_with_docs": updated_payload,
        "doc_index_path": str(doc_index_path) if doc_index_path.exists() else None,
        "anchor_inventory_path": str(anchor_inventory_path) if anchor_inventory_path.exists() else None,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    git_meta = report.get("git", {})
    modules = report.get("modules_missing_docs", [])
    lines = [
        "# Code ↔ Docs Churn Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Repo Root: {report['repo_root']}",
        f"Git Window: {git_meta.get('window')}",
        f"Commits Examined: {git_meta.get('commits_examined')}",
        f"Distinct Authors: {git_meta.get('distinct_authors')}",
        f"Modules With Code Churn: {summary.get('modules_with_code_churn')}",
        f"Modules Missing Doc Updates: {summary.get('modules_without_doc_updates')}",
        "",
        "## Modules Missing Doc Updates (up to 25)",
        "",
    ]
    if modules:
        for module in modules[:25]:
            authors = ", ".join(module.get("authors", [])) or "unknown"
            code_paths = ", ".join(module.get("code_paths", [])[:5])
            last_commit = module.get("last_commit_utc")
            doc_candidates = module.get("doc_candidates", [])
            candidate_paths = ", ".join(item.get("path", "") for item in doc_candidates[:3])
            lines.append(
                f"- `{module.get('module')}` — {len(module.get('code_paths', []))} code paths, authors: {authors}, "
                f"last commit: {last_commit or 'n/a'}"
            )
            if candidate_paths:
                lines.append(f"  - Suggested docs: {candidate_paths}")
            if code_paths:
                lines.append(f"  - Sample code paths: {code_paths}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("<!-- markdownlint-disable MD013 -->")
    lines.append("## Modules With Doc Updates (context)")
    lines.append("")
    modules_with_docs = report.get("modules_with_docs", [])
    if modules_with_docs:
        for module in modules_with_docs[:10]:
            authors = ", ".join(module.get("authors", [])) or "unknown"
            doc_paths = ", ".join(module.get("doc_paths", [])[:3])
            lines.append(
                f"- `{module.get('module')}` — docs updated ({len(module.get('doc_paths', []))} paths), authors: {authors}"
            )
            if doc_paths:
                lines.append(f"  - Sample doc paths: {doc_paths}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("<!-- markdownlint-enable MD013 -->")
    lines.append("## References")
    lines.append("")
    if report.get("doc_index_path"):
        lines.append(f"- Doc Index: `{report['doc_index_path']}`")
    if report.get("anchor_inventory_path"):
        lines.append(f"- Anchor Inventory: `{report['anchor_inventory_path']}`")
    lines.append("- Allowlist modules: " + (", ".join(summary.get("allowlisted_modules", [])) or "(none)"))
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_tsv(modules: list[dict[str, Any]]) -> str:
    lines = ["module\tcode_paths\tdoc_paths\tcommit_hashes\tauthors\tlast_commit_utc"]
    for module in modules:
        lines.append(
            "\t".join(
                [
                    module.get("module", ""),
                    ";".join(module.get("code_paths", [])),
                    ";".join(module.get("doc_paths", [])),
                    ";".join(module.get("commit_hashes", [])),
                    ";".join(module.get("authors", [])),
                    module.get("last_commit_utc", ""),
                ]
            )
        )
    return "\n".join(lines)


def _bundle_summary(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    git_meta = report.get("git", {})
    return {
        "generated_utc": report.get("generated_utc"),
        "modules_missing_docs": summary.get("modules_without_doc_updates", 0),
        "modules_with_docs": summary.get("modules_with_doc_updates", 0),
        "commits_examined": git_meta.get("commits_examined", 0),
        "distinct_authors": git_meta.get("distinct_authors", 0),
    }


def _git_head(repo_root: Path) -> str | None:
    result = _git(["rev-parse", "HEAD"], repo_root=repo_root)
    if result.returncode == 0:
        return result.stdout.strip() or None
    return None


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
        force=True,
    )
    logger = logging.getLogger("code_doc_churn")

    paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
    options = build_standard_options(args, OPTIONS_CONFIG)

    allowlist = _read_allowlist(paths.allowlist)
    logger.debug("Loaded %s allowlist entries", len(allowlist))

    commits, authors = _collect_commits(paths.repo_root, window=args.git_window, until=args.git_until)
    logger.info("Commits examined: %s", len(commits))
    doc_index = _load_doc_index(paths.doc_index)
    flagged, doc_updated = _build_module_activity(commits, allowlist=allowlist)

    generated_ts = datetime.now(timezone.utc)
    report = build_report(
        repo_root=paths.repo_root,
        window=args.git_window,
        commits=commits,
        authors=authors,
        flagged=flagged,
        doc_updated=doc_updated,
        allowlist=allowlist,
        doc_index=doc_index,
        generated_ts=generated_ts,
        head_commit=_git_head(paths.repo_root),
        doc_index_path=paths.doc_index,
        anchor_inventory_path=paths.anchor_inventory,
    )

    viewer_slug = "healthview"
    topic = RUN_PREFIX
    timestamp = generated_ts.strftime("%Y%m%d-%H%M")

    markdown = render_markdown(report)
    summary_metrics = _bundle_summary(report)

    manifest: dict[str, Any] = {
        "viewer_slug": viewer_slug,
        "topic": topic,
        "run_timestamp": timestamp,
        "generated_utc": report.get("generated_utc"),
        "git_sha": report.get("git", {}).get("head_commit"),
        "status": "ok",
        "catalog": [
            {"artifact": "manifest.json", "kind": "json"},
            {"artifact": "summary.md", "kind": "markdown"},
            {"artifact": "telemetry.json", "kind": "json"},
        ],
        "inputs": {
            "repo_root": str(paths.repo_root),
            "git_window": args.git_window,
            "git_until": args.git_until,
            "doc_index": str(paths.doc_index),
            "anchor_inventory": str(paths.anchor_inventory),
            "allowlist": str(paths.allowlist),
            "artifacts_to_keep": options.artifacts_to_keep,
        },
        "provenance": {
            "trigger_type": "manual",
        },
        "summary": summary_metrics,
    }

    telemetry: dict[str, Any] = {
        "viewer_slug": viewer_slug,
        "topic": topic,
        "run_timestamp": timestamp,
        "generated_utc": report.get("generated_utc"),
        "metrics": {
            **summary_metrics,
            "allowlisted_modules": len(report.get("summary", {}).get("allowlisted_modules", [])),
        },
        "payload": report,
    }

    storage = create_storage(
        output_dir=paths.output_dir,
        viewer_slug=viewer_slug,
        topic=topic,
        timestamp=timestamp,
    )

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
        keep=options.artifacts_to_keep,
        current_run=run_dir,
        logger=logger,
    )
    logger.debug(
        "Pruned churn bundles: kept=%s removed=%s protected=%s failures=%s",
        len(prune_result.kept),
        len(prune_result.removed),
        len(prune_result.protected),
        len(prune_result.failures),
    )

    logger.info(
        "Modules missing doc updates: %s", report.get("summary", {}).get("modules_without_doc_updates", 0)
    )

    return {
        "run_dir": str(run_dir),
        "artifacts": {
            "manifest.json": str(run_dir / "manifest.json"),
            "summary.md": str(run_dir / "summary.md"),
            "telemetry.json": str(run_dir / "telemetry.json"),
        },
        "summary": report["summary"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
