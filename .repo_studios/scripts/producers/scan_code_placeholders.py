"""Scan for placeholder comments and emit canonical Healthview artifacts.

This producer scans repository files for placeholder markers (e.g., TODO, FIXME)
and emits a canonical 3-artifact bundle under
`.repo_studios/reports/producer_reports/<viewer>/<topic>/<YYYYMMDD-HHMM>/`.

Outputs:
- manifest.json
- summary.md
- telemetry.json
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, NamedTuple, cast

DEFAULT_EXTENSIONS = (
    ".py",
    ".md",
    ".txt",
    ".js",
    ".ts",
    ".yaml",
    ".yml",
    ".json",
)
DEFAULT_PATTERNS = ("TODO", "FIXME", "NOTE", "XXX", "OPTIMIZE", "REVIEW")
COMMENT_ANCHORS = ("#", "//", "<!--", "/*", "*")
DEFAULT_EXCLUDE_PREFIXES = (".venv/", "node_modules/", "*/site-packages/")

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
    from libraries.database_integration import create_storage
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback when running standalone
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
    from libraries.database_integration import create_storage
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep

SCHEMA_VERSION = 1
TOPIC_SLUG = "code_placeholders"
DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("scan_code_placeholders")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    scan_root: Path
    output_dir: Path


@dataclass(frozen=True)
class ScanOptions:
    extensions: tuple[str, ...]
    patterns: tuple[str, ...]
    allowlist: set[tuple[str, int]]
    artifacts_to_keep: int
    exclude_prefixes: tuple[str, ...]
    exclude_segments: tuple[str, ...]
    default_exclusions_applied: bool


class Options(NamedTuple):
    artifacts_to_keep: int


PATH_SPECS: dict[str, PathSpec] = {
    "scan_root": PathSpec(field="root", default=Path("."), within_repo=False),
    "output_dir": PathSpec(
        field="output_dir",
        default=DEFAULT_OUTPUT_DIR,
        ensure_dir=True,
        within_repo=False,
    ),
}

KEEP_SPECS: dict[str, KeepSpec] = {
    "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
}


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs=PATH_SPECS,
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs=KEEP_SPECS,
)


@dataclass
class PlaceholderRecord:
    relative_path: str
    absolute_path: str
    line_number: int
    pattern: str
    line_text: str

    def to_dict(self) -> dict[str, str | int]:
        return {
            "path": self.relative_path,
            "absolute_path": self.absolute_path,
            "line": self.line_number,
            "pattern": self.pattern,
            "text": self.line_text,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan for placeholder comments and emit structured artifacts")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument("--root", default=".", help="Directory to scan (relative to repo root by default)")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Base directory for structured artifacts (defaults to .repo_studios/reports/producer_reports)",
    )
    parser.add_argument("--timestamp", default=None, help="ISO8601 timestamp to seed the run directory")
    parser.add_argument(
        "--include-ext",
        nargs="*",
        default=None,
        metavar="EXT",
        help="File extensions to include (defaults to repo standard list)",
    )
    parser.add_argument(
        "--patterns",
        nargs="*",
        default=None,
        help="Placeholder tokens to search for (defaults to TODO/FIXME/NOTE/XXX/OPTIMIZE/REVIEW)",
    )
    parser.add_argument(
        "--allowlist-file",
        default=None,
        help="Optional file of <path>:<line> entries to ignore (paths relative to repo root)",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical scans to retain",
    )
    parser.add_argument(
        "--exclude-prefix",
        nargs="*",
        default=None,
        metavar="PREFIX",
        help="Relative directory prefixes to exclude (defaults applied when scanning the repo root)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def load_allowlist(path: str | None, repo_root: Path) -> set[tuple[str, int]]:
    if not path:
        return set()
    allowlist_path = Path(path)
    if not allowlist_path.is_absolute():
        allowlist_path = repo_root / allowlist_path
    allowed: set[tuple[str, int]] = set()
    if not allowlist_path.exists():
        logging.warning("allowlist file not found: %s", allowlist_path)
        return allowed
    for raw in allowlist_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        rel, number = line.split(":", 1)
        try:
            allowed.add((rel.strip(), int(number.strip())))
        except ValueError:
            logging.debug("ignored malformed allowlist entry: %s", raw)
    return allowed


def normalize_patterns(raw: Iterable[str] | None) -> tuple[str, ...]:
    values = tuple(str(p).strip() for p in (raw or DEFAULT_PATTERNS) if str(p).strip())
    if not values:
        return DEFAULT_PATTERNS
    return tuple(sorted({v.upper() for v in values}))


def normalize_extensions(raw: Iterable[str] | None) -> tuple[str, ...]:
    values = tuple(str(ext).strip().lower() for ext in (raw or DEFAULT_EXTENSIONS) if str(ext).strip())
    if not values:
        return DEFAULT_EXTENSIONS
    normalized: set[str] = set()
    for ext in values:
        normalized.add(ext if ext.startswith(".") else f".{ext}")
    return tuple(sorted(normalized))


def normalize_exclude_prefixes(raw: Iterable[str] | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    prefixes: set[str] = set()
    segments: set[str] = set()
    for entry in raw or ():
        value = str(entry).strip()
        if not value:
            continue
        pointer = value.replace("\\", "/")
        if pointer.startswith("*/"):
            segment = pointer[2:]
            if segment.endswith("/"):
                segment = segment[:-1]
            if segment:
                segments.add(segment.lower())
            continue
        if pointer.startswith("./"):
            pointer = pointer[2:]
        if pointer.startswith("/"):
            pointer = pointer[1:]
        if pointer and not pointer.endswith("/"):
            pointer = f"{pointer}/"
        if pointer:
            prefixes.add(pointer)
    return tuple(sorted(prefixes)), tuple(sorted(segments))


def compile_pattern_regex(patterns: tuple[str, ...]) -> dict[str, re.Pattern[str]]:
    compiled: dict[str, re.Pattern[str]] = {}
    for token in patterns:
        compiled[token] = re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE)
    return compiled


def scan_placeholders(
    paths: Paths,
    options: ScanOptions,
    compiled_patterns: dict[str, re.Pattern[str]],
) -> list[PlaceholderRecord]:
    results: list[PlaceholderRecord] = []
    for file_path in sorted(paths.scan_root.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in options.extensions:
            continue
        rel_path = file_path.resolve().relative_to(paths.repo_root)
        rel_display = rel_path.as_posix()
        if _should_exclude(rel_display, options):
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as exc:  # pragma: no cover - defensive guard
            logging.debug("skip unreadable file %s: %s", file_path, exc)
            continue
        for idx, line in enumerate(text, start=1):
            if not _looks_like_comment(line):
                continue
            for token, regex in compiled_patterns.items():
                match = regex.search(line)
                if not match or not _is_uppercase_match(match.group(0)):
                    continue
                if (rel_display, idx) in options.allowlist:
                    break
                record = PlaceholderRecord(
                    relative_path=rel_display,
                    absolute_path=str(file_path.resolve()),
                    line_number=idx,
                    pattern=token,
                    line_text=line.strip(),
                )
                results.append(record)
                break
    return results


def _looks_like_comment(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    lowered = stripped.lower()
    return any(lowered.startswith(anchor) for anchor in COMMENT_ANCHORS)


def _is_uppercase_match(token: str) -> bool:
    stripped = token.strip()
    return bool(stripped) and stripped.isupper()


def _should_exclude(rel_display: str, options: ScanOptions) -> bool:
    normalized = rel_display.replace("\\", "/")
    for prefix in options.exclude_prefixes:
        if normalized.startswith(prefix):
            return True
    decorated = f"/{normalized}/"
    for segment in options.exclude_segments:
        needle = f"/{segment}/"
        if needle in decorated:
            return True
    return False


def compose_payload(
    *,
    paths: Paths,
    options: ScanOptions,
    records: list[PlaceholderRecord],
    run_slug: str,
    generated_at: datetime,
    bundle_dir: Path,
) -> dict[str, Any]:
    rel_scan_root = str(paths.scan_root.resolve().relative_to(paths.repo_root))
    by_pattern: Counter[str] = Counter(record.pattern for record in records)
    by_extension: Counter[str] = Counter(Path(record.relative_path).suffix.lower() for record in records)
    bundle_rel = _relativize(bundle_dir, paths.repo_root)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "status": "ok",
        "timestamp": generated_at.isoformat(),
        "generated_utc": generated_at.isoformat(),
        "run_timestamp": run_slug,
        "run_id": run_slug,
        "repo_root": str(paths.repo_root),
        "bundle_dir": bundle_rel,
        "scan_root": rel_scan_root,
        "include_extensions": list(options.extensions),
        "patterns": list(options.patterns),
        "allowlist_size": len(options.allowlist),
        "exclude_prefixes": list(options.exclude_prefixes),
        "exclude_segments": list(options.exclude_segments),
        "default_exclusions_applied": options.default_exclusions_applied,
        "total_matches": len(records),
        "summary": {
            "by_pattern": dict(sorted(by_pattern.items())),
            "by_extension": dict(sorted(by_extension.items())),
        },
    }
    return payload


def render_markdown_report(payload: dict[str, Any], records: list[PlaceholderRecord]) -> str:
    lines = [
        "# Placeholder Scan Report\n\n",
        f"- Status: `{payload['status']}`\n",
        f"- Run Timestamp: `{payload.get('run_timestamp', payload['timestamp'])}`\n",
        f"- Scan Root: `{payload['scan_root']}`\n",
        f"- Total Matches: {payload['total_matches']}\n",
        f"- Patterns: {', '.join(cast(list[str], payload['patterns']))}\n",
        f"- Extensions: {', '.join(cast(list[str], payload['include_extensions']))}\n",
        f"- Allowlist Entries: {payload['allowlist_size']}\n\n",
    ]
    summary = payload.get("summary", {})
    by_pattern = summary.get("by_pattern", {}) if isinstance(summary, dict) else {}
    if by_pattern:
        lines.append("## Matches by Pattern\n\n")
        lines.append("| Pattern | Count |\n| --- | ---: |\n")
        for token, count in sorted(by_pattern.items(), key=lambda item: item[0]):
            lines.append(f"| `{token}` | {count} |\n")
        lines.append("\n")
    if records:
        lines.append("## Sample Findings\n\n")
        lines.append("| Path | Line | Pattern | Snippet |\n| --- | ---: | --- | --- |\n")
        for record in records[:20]:
            snippet = record.line_text.replace("|", "\\|")
            lines.append(f"| {record.relative_path} | {record.line_number} | `{record.pattern}` | {snippet} |\n")
        lines.append("\n")
    content = "".join(lines).rstrip() + "\n"
    return content


def render_log(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    entries = [
        f"status={payload['status']}",
        f"run_timestamp={payload.get('run_timestamp', payload['timestamp'])}",
        f"scan_root={payload['scan_root']}",
        f"total_matches={payload['total_matches']}",
        f"patterns={','.join(cast(list[str], payload['patterns']))}",
        f"extensions={','.join(cast(list[str], payload['include_extensions']))}",
        f"allowlist_size={payload['allowlist_size']}",
    ]
    for token, count in sorted(summary.get("by_pattern", {}).items()):
        entries.append(f"by_pattern_{token}={count}")
    return "\n".join(entries) + "\n"


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - defensive parsing
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timestamp_slug(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")


def _relativize(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _build_manifest(
    *,
    payload: dict[str, Any],
    rendered_log: str,
    records: list[PlaceholderRecord],
    sample_limit: int = 200,
) -> dict[str, Any]:
    manifest: dict[str, Any] = dict(payload)
    manifest["log"] = rendered_log
    manifest["matches_total"] = int(payload.get("total_matches", 0) or 0)
    manifest["matches_sample_limit"] = sample_limit
    manifest["matches_sample_truncated"] = len(records) > sample_limit
    manifest["matches_sample"] = [record.to_dict() for record in records[:sample_limit]]
    return manifest


def _build_telemetry(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    total_matches = int(payload.get("total_matches", 0) or 0)
    allowlist_size = int(payload.get("allowlist_size", 0) or 0)
    return {
        "viewer": payload.get("viewer"),
        "topic": payload.get("topic"),
        "run_timestamp": payload.get("run_timestamp"),
        "generated_utc": payload.get("generated_utc"),
        "metrics": {
            "status": payload.get("status"),
            "total_matches": total_matches,
            "allowlist_size": allowlist_size,
            "unallowlisted_matches": max(total_matches - allowlist_size, 0),
        },
        "summary": payload,
    }


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level), format="%(levelname)s %(message)s")


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    configure_logging(args.log_level)
    logger = logging.getLogger(__name__)
    paths = build_paths(args)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    patterns = normalize_patterns(args.patterns)
    extensions = normalize_extensions(args.include_ext)
    allowlist = load_allowlist(args.allowlist_file, paths.repo_root)
    base_options = build_standard_options(args, OPTIONS_CONFIG)
    raw_exclusions: Iterable[str] | None
    default_exclusions_applied = False
    if args.exclude_prefix is None:
        if paths.scan_root.resolve() == paths.repo_root.resolve():
            raw_exclusions = DEFAULT_EXCLUDE_PREFIXES
            default_exclusions_applied = True
        else:
            raw_exclusions = ()
    else:
        raw_exclusions = args.exclude_prefix
    exclude_prefixes, exclude_segments = normalize_exclude_prefixes(raw_exclusions)
    options = ScanOptions(
        extensions=extensions,
        patterns=patterns,
        allowlist=allowlist,
        artifacts_to_keep=base_options.artifacts_to_keep,
        exclude_prefixes=exclude_prefixes,
        exclude_segments=exclude_segments,
        default_exclusions_applied=default_exclusions_applied,
    )
    compiled_patterns = compile_pattern_regex(patterns)

    generated_at = _parse_timestamp(args.timestamp)
    run_slug = _timestamp_slug(generated_at)
    topic_dir = paths.output_dir
    storage = create_storage(paths.output_dir, "", "", timestamp=run_slug)
    bundle_dir = storage.file_storage.bundle_dir

    records = scan_placeholders(paths, options, compiled_patterns)

    payload = compose_payload(
        paths=paths,
        options=options,
        records=records,
        run_slug=run_slug,
        generated_at=generated_at,
        bundle_dir=bundle_dir,
    )
    markdown = render_markdown_report(payload, records)
    rendered_log = render_log(payload)
    manifest = _build_manifest(payload=payload, rendered_log=rendered_log, records=records)
    telemetry = _build_telemetry(payload=payload)

    # DB_INTEGRATION_MARKER: placeholder scan manifest write
    storage.write_manifest(manifest)

    # DB_INTEGRATION_MARKER: placeholder scan summary markdown write
    storage.write_summary({"markdown": markdown}, format="md")

    # DB_INTEGRATION_MARKER: placeholder scan telemetry write
    storage.write_telemetry(telemetry)

    pruned = prune_run_directories(
        topic_dir,
        keep=options.artifacts_to_keep,
        current_run=bundle_dir,
        logger=logger,
    )
    if pruned.removed:
        logger.debug("Pruned placeholder runs: %s", ", ".join(sorted(path.name for path in pruned.removed)))

    logger.info("Placeholder scan run_dir=%s matches=%d", bundle_dir, len(records))
    return payload


def main(argv: list[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
