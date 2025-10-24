#!/usr/bin/env python3
"""Structured legacy anchor stub validator with pruning-aware artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

RE_MD_LINK = re.compile(r"metrics_orchestrator\.md#([a-zA-Z0-9\-._]+)")
RE_HEADING = re.compile(r"^(#{2,6})\s+(.*)$")

DEFAULT_OUTPUT_DIR = Path(
    ".repo_studios/reports/producer_reports/metrics_anchor_stub_reports"
)
DEFAULT_LEGACY_FILE = Path("docs/api/metrics_orchestrator.md")
DEFAULT_ALLOWLIST_PATH = Path(
    ".repo_studios/scripts/producers/metrics_anchor_allowlist.json"
)
RUN_PREFIX = "metrics_anchor_stub_check"
DEFAULT_ARTIFACTS_TO_KEEP = 10
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    legacy_file: Path
    allowlist_path: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int


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
        help="JSON file with anchors to allow (format: {\"anchors\": [\"foo\"]})",
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
    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path(__file__).resolve().parents[3]
    )
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else (repo_root / DEFAULT_OUTPUT_DIR).resolve()
    )
    legacy_file = (
        Path(args.legacy_file).resolve()
        if args.legacy_file
        else (repo_root / DEFAULT_LEGACY_FILE).resolve()
    )
    allowlist_path = (
        Path(args.allowlist_path).resolve()
        if args.allowlist_path
        else (repo_root / DEFAULT_ALLOWLIST_PATH).resolve()
    )
    return Paths(
        repo_root=repo_root,
        output_dir=output_dir,
        legacy_file=legacy_file,
        allowlist_path=allowlist_path,
    )


def build_options(args: argparse.Namespace) -> Options:
    return Options(artifacts_to_keep=max(1, int(args.artifacts_to_keep)))


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


def collect_referenced_anchors(
    files: Iterable[Path], repo_root: Path
) -> dict[str, list[str]]:
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


def compose_payload(
    *,
    paths: Paths,
    options: Options,
    referenced: dict[str, list[str]],
    legacy: set[str],
    allowlist: set[str],
    missing: list[dict[str, Any]],
    allowlisted_count: int,
    markdown_count: int,
    timestamp: dt.datetime,
) -> dict[str, Any]:
    run_id = f"{RUN_PREFIX}-{timestamp.strftime('%Y%m%d_%H%M%S')}"
    summary = {
        "files_checked": markdown_count,
        "anchors_referenced": len(referenced),
        "legacy_stub_count": len(legacy),
        "missing_count": len(missing),
        "allowlisted_count": allowlisted_count,
    }
    status = "ok" if summary["missing_count"] == 0 else "missing-anchors"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "timestamp": timestamp.isoformat(),
        "run_id": run_id,
        "repo_root": str(paths.repo_root),
        "output_dir": str(paths.output_dir),
        "legacy_file": str(paths.legacy_file),
        "allowlist_path": str(paths.allowlist_path) if paths.allowlist_path.exists() else None,
        "options": {"artifacts_to_keep": options.artifacts_to_keep},
        "summary": summary,
        "missing": missing,
        "referenced_anchors": sorted(referenced.keys()),
        "legacy_anchors": sorted(legacy),
        "allowlisted_anchors": sorted(allowlist),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# Metrics Anchor Stub Report\n\n",
        f"- Status: `{payload.get('status', 'unknown')}`\n",
        f"- Timestamp: `{payload.get('timestamp', '')}`\n",
        f"- Repo Root: `{payload.get('repo_root', '')}`\n",
        f"- Legacy File: `{payload.get('legacy_file', '')}`\n",
        f"- Allowlist: `{payload.get('allowlist_path') or 'none'}`\n",
        f"- Anchors Referenced: {summary.get('anchors_referenced', 0)}\n",
        f"- Missing Anchors: {summary.get('missing_count', 0)}\n",
        f"- Allowlisted Anchors: {summary.get('allowlisted_count', 0)}\n",
    ]

    missing = payload.get("missing", [])
    if missing:
        lines.append("\n## Missing Anchors\n\n")
        lines.append("| Anchor | Referenced In |\n| --- | --- |")
        for entry in missing:
            files = "<br>".join(entry.get("files", [])) or "—"
            lines.append(f"\n| `{entry.get('anchor')}` | {files} |")

    lines.append(
        "\n\n## Next Steps\n\n"
        "- [ ] Add legacy stub entries for anchors listed above or document intentional drift.\n"
        "- [ ] Update the allowlist JSON with justification if exceptions are required.\n"
        "- [ ] Re-run `validate_metrics_anchor_stubs.py` to confirm a clean state.\n"
    )
    return "".join(lines)


def render_log(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    entries = [
        f"status={payload.get('status', 'unknown')}",
        f"timestamp={payload.get('timestamp', '')}",
        f"anchors_referenced={summary.get('anchors_referenced', 0)}",
        f"missing_count={summary.get('missing_count', 0)}",
        f"allowlisted_count={summary.get('allowlisted_count', 0)}",
    ]
    entries.append(f"legacy_file={payload.get('legacy_file', '')}")
    if payload.get("allowlist_path"):
        entries.append(f"allowlist_path={payload['allowlist_path']}")
    return "\n".join(entries) + "\n"


def write_artifacts(run_dir: Path, output_dir: Path, payload: dict[str, Any]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "report.md").write_text(
        render_markdown_report(payload), encoding="utf-8"
    )
    (run_dir / "log.txt").write_text(render_log(payload), encoding="utf-8")
    (run_dir / "missing.json").write_text(
        json.dumps(payload.get("missing", []), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    latest_dir = output_dir / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "report.json": latest_dir / "latest_report.json",
        "report.md": latest_dir / "latest_report.md",
        "log.txt": latest_dir / "latest_log.txt",
        "missing.json": latest_dir / "latest_missing.json",
    }
    for source, target in mapping.items():
        src_path = run_dir / source
        if src_path.exists():
            target.write_bytes(src_path.read_bytes())


def prune_history(base_dir: Path, keep: int) -> None:
    if not base_dir.exists():
        return
    run_dirs = sorted(
        [p for p in base_dir.iterdir() if p.is_dir() and p.name.startswith(RUN_PREFIX)],
        key=lambda p: p.name,
    )
    excess = len(run_dirs) - keep
    if excess <= 0:
        return
    for directory in run_dirs[:excess]:
        for child in sorted(directory.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if child.is_file():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                child.rmdir()
        directory.rmdir()


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    configure_logging(args.log_level)
    paths = build_paths(args)
    options = build_options(args)
    paths.output_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Repo root: %s", paths.repo_root)
    logging.info("Output directory: %s", paths.output_dir)
    logging.info("Legacy file: %s", paths.legacy_file)

    markdown_files = list(iter_markdown_files(paths.repo_root))
    referenced = collect_referenced_anchors(markdown_files, paths.repo_root)
    legacy = collect_legacy_stub_anchors(paths.legacy_file)
    allowlist = load_allowlist(paths.allowlist_path)
    missing, allowlisted_count = summarize_missing(referenced, legacy, allowlist)

    timestamp = dt.datetime.now(dt.timezone.utc)
    payload = compose_payload(
        paths=paths,
        options=options,
        referenced=referenced,
        legacy=legacy,
        allowlist=allowlist,
        missing=missing,
        allowlisted_count=allowlisted_count,
        markdown_count=len(markdown_files),
        timestamp=timestamp,
    )

    run_dir = paths.output_dir / payload["run_id"]
    write_artifacts(run_dir, paths.output_dir, payload)
    prune_history(paths.output_dir, options.artifacts_to_keep)

    if payload["summary"]["missing_count"] == 0:
        logging.info("[metrics-anchor-stubs] OK — no missing anchors detected")
    else:
        logging.error(
            "[metrics-anchor-stubs] Missing anchors detected (%s)",
            payload["summary"]["missing_count"],
        )
        for entry in payload["missing"]:
            logging.error("  - %s: %s", entry.get("anchor"), ", ".join(entry.get("files", [])))

    return payload


def main(argv: list[str] | None = None) -> int:
    payload = run(argv)
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
