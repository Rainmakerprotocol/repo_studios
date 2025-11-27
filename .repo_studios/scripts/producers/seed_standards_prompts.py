#!/usr/bin/env python3
"""Generate structured prompt seed bundles from the standards index."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import shutil
import sys
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, NamedTuple

import yaml

DEFAULT_RELATIVE_INDEX = Path(
    ".repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml"
)
LEGACY_INDEX_PATH = Path(".repo_studios/scripts/repo_standards_index.yaml")
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_prompt_seeds")
RUN_PREFIX = "standards_prompt_seed"
DEFAULT_ARTIFACTS_TO_KEEP = 10
FORMAT_CHOICES = ("text", "yaml", "json")
SCHEMA_VERSION = 1

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

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
    index_path: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    include_warn: bool
    artifact_formats: tuple[str, ...]
    artifacts_to_keep: int
    legacy_format: str | None
    legacy_output: str | None


PATH_SPECS: dict[str, PathSpec] = {
    "index_path": PathSpec(field="index_path", default=DEFAULT_RELATIVE_INDEX, within_repo=False),
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


class KeepOptions(NamedTuple):
    artifacts_to_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepOptions,
    keep_specs=KEEP_SPECS,
)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="seed_standards_prompts",
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", help="Repository root (defaults to project root)")
    parser.add_argument(
        "--index-path",
        help=(
            "Path to repo_standards_index.yaml (defaults to "
            ".repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml)"
        ),
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to store structured artifacts (defaults to producer_reports/standards_prompt_seeds)",
    )
    parser.add_argument("--include-warn", action="store_true", help="Include warn severity rules")
    parser.add_argument(
        "--artifact-formats",
        nargs="+",
        choices=FORMAT_CHOICES,
        default=list(FORMAT_CHOICES),
        help="Formats to materialize inside the run bundle",
    )
    parser.add_argument(
        "--format",
        choices=FORMAT_CHOICES,
        default="text",
        help="Legacy output format to stream to stdout or --out",
    )
    parser.add_argument("--out", help="Write the --format payload to this file instead of stdout")
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical run directories to retain",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
    if paths.index_path.exists():
        return paths
    legacy_candidate = (paths.repo_root / LEGACY_INDEX_PATH).resolve()
    if legacy_candidate.exists():
        logging.warning(
            "standards index missing at %s; falling back to legacy snapshot %s",
            paths.index_path,
            legacy_candidate,
        )
        return replace(paths, index_path=legacy_candidate)
    return paths


def build_options(args: argparse.Namespace) -> Options:
    artifact_formats = tuple(dict.fromkeys(args.artifact_formats))  # preserve order, dedupe
    if not artifact_formats:
        raise SystemExit("--artifact-formats must include at least one format")
    base_options = build_standard_options(args, OPTIONS_CONFIG)
    return Options(
        include_warn=bool(args.include_warn),
        artifact_formats=artifact_formats,
        artifacts_to_keep=base_options.artifacts_to_keep,
        legacy_format=args.format,
        legacy_output=args.out,
    )


def load_index(index_path: Path) -> dict[str, Any]:
    raw = index_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError("standards index must be a mapping at the root")
    return data


def build_seed(include_warn: bool, index: dict[str, Any]) -> dict[str, Any]:
    categories = index.get("categories", {}) or {}
    rules = index.get("rules", []) or []
    keep_levels = {"critical", "error"} | ({"warn"} if include_warn else set())
    grouped: dict[str, dict[str, Any]] = {}
    for rule in rules:
        if rule.get("severity") not in keep_levels:
            continue
        for category in rule.get("category_ids", []) or []:
            entry = grouped.setdefault(
                category,
                {"title": categories.get(category, {}).get("title", category), "rules": []},
            )
            entry["rules"].append(
                {
                    "id": rule.get("id"),
                    "summary": rule.get("summary"),
                    "severity": rule.get("severity"),
                }
            )
    for entry in grouped.values():
        entry["rules"].sort(key=lambda item: item.get("id") or "")
    return {"integrity_hash": index.get("integrity_hash"), "categories": grouped}


def summarize_seed(seed: dict[str, Any]) -> dict[str, Any]:
    categories = seed.get("categories", {}) or {}
    category_count = len(categories)
    category_summaries: list[dict[str, Any]] = []
    seen_rules: dict[tuple[str | None, str | None], str] = {}
    for category_id, data in sorted(categories.items()):
        rules = data.get("rules", [])
        for rule in rules:
            key = (rule.get("id"), rule.get("summary"))
            severity = rule.get("severity") or "unknown"
            seen_rules.setdefault(key, severity)
        category_summaries.append(
            {
                "id": category_id,
                "title": data.get("title", category_id),
                "rule_count": len(rules),
            }
        )
    unique_total = len(seen_rules)
    severity_counts = Counter(seen_rules.values())
    return {
        "category_count": category_count,
        "total_rules": unique_total,
        "severity_counts": dict(sorted(severity_counts.items())),
        "categories": category_summaries,
    }


def render_seed(seed: dict[str, Any], fmt: str) -> str:
    if fmt == "text":
        lines = [f"Integrity: {seed.get('integrity_hash')}", ""]
        for category_id, data in sorted(seed.get("categories", {}).items()):
            lines.append(f"Category: {data['title']} ({category_id})")
            for rule in data.get("rules", []):
                severity = (rule.get("severity") or "").upper()
                lines.append(f"  - [{severity}] {rule.get('id')}: {rule.get('summary')}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"
    if fmt == "yaml":
        return yaml.safe_dump(seed, sort_keys=True)
    if fmt == "json":
        return json.dumps(seed, indent=2, sort_keys=True) + "\n"
    raise ValueError(f"unknown format: {fmt}")


def ensure_run_directory(base_dir: Path, run_id: str) -> Path:
    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_seed_files(run_dir: Path, seed: dict[str, Any], formats: tuple[str, ...]) -> list[Path]:
    written: list[Path] = []
    for fmt in formats:
        content = render_seed(seed, fmt)
        filename = {
            "text": "seed.txt",
            "yaml": "seed.yaml",
            "json": "seed.json",
        }[fmt]
        path = run_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def render_markdown_report(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    categories = summary.get("categories", []) if isinstance(summary, dict) else []
    severity_counts = summary.get("severity_counts", {}) if isinstance(summary, dict) else {}
    lines = [
        "# Standards Prompt Seed Report\n\n",
        f"- Status: `{payload.get('status', 'unknown')}`\n",
        f"- Timestamp: `{payload.get('timestamp', '')}`\n",
        f"- Index Path: `{payload.get('index_path', '')}`\n",
        f"- Include Warn: `{payload.get('include_warn', False)}`\n",
        f"- Total Categories: {summary.get('category_count', 0)}\n",
        f"- Total Rules: {summary.get('total_rules', 0)}\n\n",
    ]
    if severity_counts:
        lines.append("## Rules by Severity\n\n")
        lines.append("| Severity | Count |\n| --- | ---: |\n")
        for severity, count in sorted(severity_counts.items()):
            lines.append(f"| {severity} | {count} |\n")
        lines.append("\n")
    if categories:
        lines.append("## Categories Included\n\n")
        lines.append("| Category ID | Title | Rule Count |\n| --- | --- | ---: |\n")
        for entry in categories:
            lines.append(f"| {entry.get('id')} | {entry.get('title')} | {entry.get('rule_count', 0)} |\n")
        lines.append("\n")
    lines.append("## Next Steps\n\n")
    lines.append("- [ ] Review seed for high-severity coverage gaps.\n")
    lines.append("- [ ] Feed seed into standards-aware prompt tuning flows.\n")
    lines.append("- [ ] Capture rationale for any warn-level inclusions.\n")
    return "".join(lines)


def render_log(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    severity_counts = summary.get("severity_counts", {}) if isinstance(summary, dict) else {}
    entries: list[str] = [
        f"status={payload.get('status', 'unknown')}",
        f"timestamp={payload.get('timestamp', '')}",
        f"index_path={payload.get('index_path', '')}",
        f"include_warn={str(payload.get('include_warn', False)).lower()}",
        f"categories={summary.get('category_count', 0)}",
        f"total_rules={summary.get('total_rules', 0)}",
    ]
    for severity, count in sorted(severity_counts.items()):
        entries.append(f"severity_{severity}={count}")
    return "\n".join(entries) + "\n"


def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:
    latest_dir = output_dir / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "report.json": latest_dir / "latest_report.json",
        "report.md": latest_dir / "latest_report.md",
        "log.txt": latest_dir / "latest_log.txt",
        "seed.json": latest_dir / "latest_seed.json",
        "seed.yaml": latest_dir / "latest_seed.yaml",
        "seed.txt": latest_dir / "latest_seed.txt",
    }
    for source_name, target_path in mapping.items():
        src = run_dir / source_name
        if src.exists():
            target_path.write_bytes(src.read_bytes())


def write_artifacts(
    *,
    run_dir: Path,
    payload: dict[str, Any],
    seed: dict[str, Any],
    formats: tuple[str, ...],
    output_dir: Path,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "report.md").write_text(render_markdown_report(payload), encoding="utf-8")
    (run_dir / "log.txt").write_text(render_log(payload), encoding="utf-8")
    write_seed_files(run_dir, seed, formats)
    _write_latest_artifacts(run_dir, output_dir)


def prune_history(base_dir: Path, keep: int) -> None:
    keep = max(keep, 1)
    if not base_dir.exists():
        return
    run_dirs = sorted(
        (p for p in base_dir.iterdir() if p.is_dir() and p.name.startswith(RUN_PREFIX)),
        key=lambda path: path.name,
    )
    excess = len(run_dirs) - keep
    for old_dir in run_dirs[: max(excess, 0)]:
        shutil.rmtree(old_dir, ignore_errors=True)


def emit_legacy_output(seed: dict[str, Any], fmt: str | None, out_path: str | None) -> None:
    if not fmt:
        return
    data = render_seed(seed, fmt)
    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")
        logging.info("Wrote %s seed to %s", fmt, path)
    else:
        print(data, end="")


def compose_payload(
    *,
    paths: Paths,
    options: Options,
    seed: dict[str, Any],
    summary: dict[str, Any],
    timestamp: dt.datetime,
) -> dict[str, Any]:
    run_id = f"{RUN_PREFIX}-{timestamp.strftime('%Y%m%d_%H%M%S')}"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "timestamp": timestamp.isoformat(),
        "run_id": run_id,
        "repo_root": str(paths.repo_root),
        "index_path": str(paths.index_path),
        "output_dir": str(paths.output_dir),
        "include_warn": options.include_warn,
        "artifact_formats": list(options.artifact_formats),
        "legacy_format": options.legacy_format,
        "seed_integrity_hash": seed.get("integrity_hash"),
        "summary": summary,
    }


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    configure_logging(args.log_level)
    paths = build_paths(args)
    options = build_options(args)
    paths.output_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Repo root: %s", paths.repo_root)
    logging.info("Index path: %s", paths.index_path)
    logging.info("Output directory: %s", paths.output_dir)
    logging.info("Include warn: %s", options.include_warn)
    logging.info("Artifact formats: %s", ", ".join(options.artifact_formats))

    try:
        index = load_index(paths.index_path)
    except Exception as exc:  # pragma: no cover - exercised via error paths
        logging.error("Failed to load standards index: %s", exc)
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "error",
            "error": str(exc),
            "index_path": str(paths.index_path),
        }

    seed = build_seed(options.include_warn, index)
    summary = summarize_seed(seed)
    timestamp = dt.datetime.now(dt.timezone.utc)
    payload = compose_payload(paths=paths, options=options, seed=seed, summary=summary, timestamp=timestamp)

    run_dir = ensure_run_directory(paths.output_dir, payload["run_id"])
    write_artifacts(
        run_dir=run_dir, payload=payload, seed=seed, formats=options.artifact_formats, output_dir=paths.output_dir
    )
    prune_history(paths.output_dir, options.artifacts_to_keep)
    emit_legacy_output(seed, options.legacy_format, options.legacy_output)

    return payload


def main(argv: list[str] | None = None) -> int:
    payload = run(argv)
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
