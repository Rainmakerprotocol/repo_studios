"""Structured placeholder scan producer.

Transforms the legacy stdout-only placeholder search into a structured
producer that emits JSON/Markdown/log artifacts with pruning and optional
allowlisting support.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, NamedTuple

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/code_placeholder_scans")
RUN_PREFIX = "placeholder_scan"
DEFAULT_ARTIFACTS_TO_KEEP = 10
SCHEMA_VERSION = 1
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

LIBRARIES_ROOT = (
    Path(__file__).resolve().parents[3]
    / ".repo_studios"
    / "command_center"
    / "scripts"
)

try:
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when running standalone
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )


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
    parser.add_argument("--repo-root", default=None, help="Repository root (defaults to three levels up from this script)")
    parser.add_argument("--root", default=".", help="Directory to scan (relative to repo root by default)")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where structured artifacts are written (defaults to code_placeholder_scans)",
    )
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
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))


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
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as exc:  # pragma: no cover - defensive guard
            logging.debug("skip unreadable file %s: %s", file_path, exc)
            continue
        for idx, line in enumerate(text, start=1):
            if not _looks_like_comment(line):
                continue
            for token, regex in compiled_patterns.items():
                if not regex.search(line):
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


def compose_payload(
    *,
    paths: Paths,
    options: ScanOptions,
    records: list[PlaceholderRecord],
    timestamp: datetime,
) -> dict[str, object]:
    rel_scan_root = str(paths.scan_root.resolve().relative_to(paths.repo_root))
    by_pattern: Counter[str] = Counter(record.pattern for record in records)
    by_extension: Counter[str] = Counter(Path(record.relative_path).suffix.lower() for record in records)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "timestamp": timestamp.isoformat(),
        "run_id": f"{RUN_PREFIX}-{timestamp.strftime('%Y%m%d_%H%M%S')}",
        "repo_root": str(paths.repo_root),
        "scan_root": rel_scan_root,
        "include_extensions": list(options.extensions),
        "patterns": list(options.patterns),
        "allowlist_size": len(options.allowlist),
        "total_matches": len(records),
        "summary": {
            "by_pattern": dict(sorted(by_pattern.items())),
            "by_extension": dict(sorted(by_extension.items())),
        },
    }
    return payload


def render_markdown_report(payload: dict[str, object], records: list[PlaceholderRecord]) -> str:
    lines = [
        "# Placeholder Scan Report\n\n",
        f"- Status: `{payload['status']}`\n",
        f"- Timestamp: `{payload['timestamp']}`\n",
        f"- Scan Root: `{payload['scan_root']}`\n",
        f"- Total Matches: {payload['total_matches']}\n",
        f"- Patterns: {', '.join(payload['patterns'])}\n",
        f"- Extensions: {', '.join(payload['include_extensions'])}\n",
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
            lines.append(
                f"| {record.relative_path} | {record.line_number} | `{record.pattern}` | {snippet} |\n"
            )
        lines.append("\n")
    return "".join(lines)


def render_log(payload: dict[str, object]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    entries = [
        f"status={payload['status']}",
        f"timestamp={payload['timestamp']}",
        f"scan_root={payload['scan_root']}",
        f"total_matches={payload['total_matches']}",
        f"patterns={','.join(payload['patterns'])}",
        f"extensions={','.join(payload['include_extensions'])}",
        f"allowlist_size={payload['allowlist_size']}",
    ]
    for token, count in sorted(summary.get("by_pattern", {}).items()):
        entries.append(f"by_pattern_{token}={count}")
    return "\n".join(entries) + "\n"


def ensure_run_directory(base_dir: Path, run_id: str) -> Path:
    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_artifacts(
    *,
    run_dir: Path,
    payload: dict[str, object],
    records: list[PlaceholderRecord],
    output_dir: Path,
) -> None:
    (run_dir / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "report.md").write_text(render_markdown_report(payload, records), encoding="utf-8")
    (run_dir / "log.txt").write_text(render_log(payload), encoding="utf-8")
    matches = [record.to_dict() for record in records]
    (run_dir / "matches.json").write_text(json.dumps(matches, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if records:
        tsv_lines = ["path\tline\tpattern\tsnippet"]
        for record in records:
            snippet = record.line_text.replace("\t", " ")
            tsv_lines.append(
                f"{record.relative_path}\t{record.line_number}\t{record.pattern}\t{snippet}"
            )
        (run_dir / "matches.tsv").write_text("\n".join(tsv_lines) + "\n", encoding="utf-8")
    _write_latest_artifacts(run_dir, output_dir)


def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:
    latest_dir = output_dir / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "report.json": latest_dir / "latest_report.json",
        "report.md": latest_dir / "latest_report.md",
        "log.txt": latest_dir / "latest_log.txt",
        "matches.json": latest_dir / "latest_matches.json",
        "matches.tsv": latest_dir / "latest_matches.tsv",
    }
    for filename, target in mapping.items():
        source = run_dir / filename
        if source.exists():
            shutil.copyfile(source, target)


def prune_history(base_dir: Path, keep: int) -> None:
    if keep < 1:
        keep = 1
    run_dirs = sorted(
        (path for path in base_dir.iterdir() if path.is_dir() and path.name.startswith(RUN_PREFIX)),
        key=lambda item: item.name,
    )
    excess = len(run_dirs) - keep
    for old_dir in run_dirs[:max(excess, 0)]:
        shutil.rmtree(old_dir, ignore_errors=True)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level), format="%(levelname)s %(message)s")


def run(argv: list[str] | None = None) -> dict[str, object]:
    args = parse_args(argv)
    configure_logging(args.log_level)
    paths = build_paths(args)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    patterns = normalize_patterns(args.patterns)
    extensions = normalize_extensions(args.include_ext)
    allowlist = load_allowlist(args.allowlist_file, paths.repo_root)
    base_options = build_standard_options(args, OPTIONS_CONFIG)
    options = ScanOptions(
        extensions=extensions,
        patterns=patterns,
        allowlist=allowlist,
        artifacts_to_keep=base_options.artifacts_to_keep,
    )
    compiled_patterns = compile_pattern_regex(patterns)
    timestamp = datetime.now(timezone.utc)
    records = scan_placeholders(paths, options, compiled_patterns)
    payload = compose_payload(paths=paths, options=options, records=records, timestamp=timestamp)
    run_id = payload["run_id"]  # type: ignore[index]
    run_dir = ensure_run_directory(paths.output_dir, str(run_id))
    write_artifacts(run_dir=run_dir, payload=payload, records=records, output_dir=paths.output_dir)
    prune_history(paths.output_dir, options.artifacts_to_keep)
    return payload


def main(argv: list[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
