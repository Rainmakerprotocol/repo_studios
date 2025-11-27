"""Build repo_standards_index.yaml and emit structured artifacts for auditing."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import runpy
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, TypedDict, cast

try:  # pragma: no cover - dependency issue surfaced early
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover - dependency issue surfaced early
    logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(message)s")
    logging.error("missing dependency pyyaml: %s", exc)
    sys.exit(1)


DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_index_reports")
RUN_PREFIX = "standards_index"
DEFAULT_ARTIFACTS_TO_KEEP = 5
SCHEMA_VERSION = 1

DEFAULT_RELATIVE_CATEGORIES = Path(".repo_studios/scripts/.repo_studios/standards_categories.yaml")
DEFAULT_RELATIVE_SEED = Path(".repo_studios/scripts/.repo_studios/standards_seed.yaml")
DEFAULT_RELATIVE_EXTRACTION = Path(".repo_studios/scripts/.repo_studios/standards_extraction.py")
DEFAULT_RELATIVE_INDEX = Path(
    ".repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml"
)
DEFAULT_RELATIVE_PENDING = Path(".repo_studios/scripts/repo_standards_pending.yaml")

LIBRARIES_ROOT = DEFAULT_REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import copy_latest_artifact
except ModuleNotFoundError:  # pragma: no cover - fallback for script execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import copy_latest_artifact


@dataclass
class Category:
    id: str
    title: str
    description: str | None
    tags: list[str] | None


@dataclass
class Source:
    path: Path
    categories: list[str]


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    categories_file: Path
    seed_file: Path
    extraction_module: Path
    output_index: Path
    pending_file: Path
    output_dir: Path


@dataclass(frozen=True)
class BuildStats:
    category_count: int
    source_count: int
    seed_rule_count: int
    extraction_enabled: bool
    auto_accept: bool
    extracted_count: int
    accepted_count: int
    pending_written: bool
    extraction_diags: list[dict[str, Any]]


class ExtractDiagnostics(TypedDict, total=False):
    errors: list[str]
    notes: list[str]
    file: str
    rules_found: int
    skipped_conflicts: list[str]
    duplicate_ids: list[str]
    invalid_severity_rules: list[str]


ExtractFn = Callable[[Path, list[str], set[str], str | None], tuple[list[dict[str, Any]], ExtractDiagnostics]]


try:  # Provide a UTC constant (support older minor versions where attribute may be absent)
    UTC = datetime.UTC  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - fallback path
    UTC = timezone.utc


def _resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def _load_categories(paths: Paths) -> tuple[dict[str, Category], list[Source]]:
    if not paths.categories_file.exists():
        raise FileNotFoundError(f"Category mapping file not found: {paths.categories_file}")
    data = yaml.safe_load(paths.categories_file.read_text(encoding="utf-8")) or {}
    raw_categories = data.get("categories", {}) or {}
    categories: dict[str, Category] = {}
    for cid, meta in raw_categories.items():
        categories[cid] = Category(
            id=cid,
            title=meta.get("title", cid),
            description=meta.get("description"),
            tags=meta.get("tags"),
        )
    raw_sources = data.get("sources", []) or []
    sources: list[Source] = []
    for src in raw_sources:
        sources.append(
            Source(
                path=_resolve_path(paths.repo_root, src["path"]),
                categories=src.get("categories", []),
            )
        )
    return categories, sources


def _validate_sources(categories: dict[str, Category], sources: list[Source]) -> None:
    missing = [s for s in sources if not s.path.exists()]
    if missing:
        missing_str = ", ".join(str(m.path) for m in missing)
        raise FileNotFoundError(f"Missing source files: {missing_str}")
    for src in sources:
        for cid in src.categories:
            if cid not in categories:
                raise ValueError(f"Source {src.path} references unknown category '{cid}'")


def _compute_integrity_hash(rule_fragments: list[str]) -> str:
    joined = "\n".join(rule_fragments)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _build_empty_rules_hash() -> str:
    return _compute_integrity_hash([])


def _env_flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


def _load_seed_rules(paths: Paths) -> tuple[list[dict[str, Any]], set[str]]:
    rules: list[dict[str, Any]] = []
    seed_ids: set[str] = set()
    if paths.seed_file.exists():
        seed_data = yaml.safe_load(paths.seed_file.read_text(encoding="utf-8")) or {}
        for rule in seed_data.get("rules", []) or []:
            rules.append(rule)
            if rule.get("id"):
                seed_ids.add(rule["id"])
    return rules, seed_ids


def _dynamic_import_extract(paths: Paths) -> ExtractFn:  # pragma: no cover - best effort
    spec_path = paths.extraction_module
    if not spec_path.exists():

        def _absent(_: Path, __: list[str], ___: set[str], today: str | None = None):  # type: ignore[unused-ignore]
            return [], {"notes": ["extraction module not present"]}

        return cast(ExtractFn, _absent)
    try:
        sandbox: dict[str, Any] = runpy.run_path(str(spec_path))  # type: ignore[assignment]
        fn = sandbox.get("extract_rules")
        if callable(fn):
            return cast(ExtractFn, fn)
        raise RuntimeError("extract_rules symbol missing or not callable")
    except Exception as exc:  # pragma: no cover - defensive boundary
        logging.warning("extraction import failed (sandbox path): %s", exc)
        message = f"extraction unavailable: {exc}"

        def _empty(_: Path, __: list[str], ___: set[str], today: str | None = None):  # type: ignore[unused-ignore]
            return [], {"notes": [message]}

        return cast(ExtractFn, _empty)


def _invoke_extract(
    fn: ExtractFn, source: Source, seed_ids: set[str], today: str
) -> tuple[list[dict[str, Any]], ExtractDiagnostics]:
    return fn(source.path, source.categories, seed_ids, today)


def _dedupe_extracted(extracted: list[dict[str, Any]], seed_ids: set[str]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for rule in extracted:
        rid = rule.get("id")
        if not rid or rid in seed_ids or rid in seen:
            continue
        seen[rid] = rule
    return [seen[key] for key in sorted(seen)]


def _maybe_extract_rules(
    paths: Paths,
    sources: list[Source],
    seed_ids: set[str],
    enable: bool,
    auto_accept: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not enable:
        return [], [], []
    extract_fn = _dynamic_import_extract(paths)
    today = date.today().isoformat()
    collected: list[dict[str, Any]] = []
    diags: list[dict[str, Any]] = []
    for src in sources:
        if src.path.suffix.lower() != ".md":
            continue
        try:
            new_rules, diag = _invoke_extract(extract_fn, src, seed_ids, today)
        except Exception as exc:  # pragma: no cover - defensive boundary
            diags.append({"file": str(src.path), "errors": [f"extraction failed: {exc}"], "rules_found": 0})
            continue
        if isinstance(diag, dict):
            diags.append(diag | {"file": str(src.path)})
        collected.extend(new_rules)
    extracted_sorted = _dedupe_extracted(collected, seed_ids)
    accepted = extracted_sorted if auto_accept else []
    return accepted, extracted_sorted, diags


def _validate_rules(rules: list[dict[str, Any]], categories: dict[str, Category]) -> None:
    required = {"id", "category_ids", "summary", "rationale", "severity", "applies_to", "source", "last_updated"}
    for rule in rules:
        missing = required - set(rule.keys())
        if missing:
            raise ValueError(f"Rule {rule.get('id')} missing fields: {sorted(missing)}")
        for cid in rule["category_ids"]:
            if cid not in categories:
                raise ValueError(f"Rule {rule['id']} references unknown category '{cid}'")


def _write_pending_file(
    paths: Paths,
    extracted_all: list[dict[str, Any]],
    auto_accept: bool,
    extraction_diags: list[dict[str, Any]],
    enable_extraction: bool,
) -> bool:
    if not (enable_extraction and not auto_accept and extracted_all):
        return False
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "auto_accept": auto_accept,
        "extracted_count": len(extracted_all),
        "notes": "Pending extracted standards rules (not yet merged into main index)",
        "rules": extracted_all,
        "diagnostics": extraction_diags,
    }
    try:  # pragma: no cover - IO
        paths.pending_file.parent.mkdir(parents=True, exist_ok=True)
        with paths.pending_file.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False, width=100)
        return True
    except Exception as exc:  # pragma: no cover
        logging.error("failed to write pending file: %s", exc)
    return False


def _compute_rules_hash(rules: list[dict[str, Any]]) -> str:
    if not rules:
        return _build_empty_rules_hash()
    fragments = [
        f"{rule['id']}|{rule['last_updated']}|{rule['severity']}" for rule in sorted(rules, key=lambda item: item["id"])
    ]
    return _compute_integrity_hash(fragments)


def _build_metadata(
    paths: Paths,
    enable_extraction: bool,
    auto_accept: bool,
    extracted_all: list[dict[str, Any]],
    pending_written: bool,
) -> dict[str, Any]:
    pending_file = str(paths.pending_file.relative_to(paths.repo_root)) if pending_written else None
    return {
        "build_script": _rel_to_repo(Path(__file__), paths.repo_root),
        "overrides_file": ".repo_studios/standards_index_overrides.yaml",
        "extraction": {
            "enabled": enable_extraction,
            "auto_accept": auto_accept,
            "extracted_count": len(extracted_all),
            "pending_file": pending_file,
        },
        "notes": "Seed + optional heuristic extraction phase.",
    }


def build_index(paths: Paths) -> tuple[dict[str, Any], BuildStats]:
    categories, sources = _load_categories(paths)
    _validate_sources(categories, sources)

    rules, seed_ids = _load_seed_rules(paths)
    enable_extraction = _env_flag("ENABLE_STANDARDS_EXTRACTION")
    auto_accept = _env_flag("AUTO_ACCEPT_EXTRACTED")
    accepted, extracted_all, extraction_diags = _maybe_extract_rules(
        paths, sources, seed_ids, enable_extraction, auto_accept
    )
    pending_written = False
    if accepted:
        rules.extend(accepted)
    else:
        pending_written = _write_pending_file(paths, extracted_all, auto_accept, extraction_diags, enable_extraction)

    _validate_rules(rules, categories)

    integrity_hash = _compute_rules_hash(rules)
    generated_at = datetime.now(UTC).isoformat()

    index: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "version": datetime.now(UTC).strftime("%Y.%m.0"),
        "generated_at": generated_at,
        "offline": True,
        "integrity_hash": integrity_hash,
        "sources": [
            {
                "path": str(source.path.relative_to(paths.repo_root)),
                "categories": source.categories,
            }
            for source in sources
        ],
        "categories": {
            cid: {
                "title": category.title,
                **({"description": category.description} if category.description else {}),
                **({"tags": category.tags} if category.tags else {}),
            }
            for cid, category in sorted(categories.items(), key=lambda kv: kv[0])
        },
        "rules": rules,
        "coverage": {"source_stats": {}, "missing_sections": []},
        "metadata": _build_metadata(paths, enable_extraction, auto_accept, extracted_all, pending_written),
    }

    stats = BuildStats(
        category_count=len(categories),
        source_count=len(sources),
        seed_rule_count=len(seed_ids),
        extraction_enabled=enable_extraction,
        auto_accept=auto_accept,
        extracted_count=len(extracted_all),
        accepted_count=len(accepted),
        pending_written=pending_written,
        extraction_diags=extraction_diags,
    )
    return index, stats


def write_index(paths: Paths, index: dict[str, Any]) -> None:
    paths.output_index.parent.mkdir(parents=True, exist_ok=True)
    with paths.output_index.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(index, handle, sort_keys=False, width=100)


def _current_utc() -> datetime:
    return datetime.now(UTC)


def _format_run_slug(moment: datetime) -> str:
    return moment.strftime("%Y%m%d_%H%M%S")


def _resolve_timestamp(raw: str | None) -> tuple[str, datetime]:
    if not raw:
        now = _current_utc()
        return _format_run_slug(now), now
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return _format_run_slug(parsed), parsed
    except ValueError:
        return raw, _current_utc()


def _ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_slug(slug: str) -> str:
    sanitized = slug.replace("/", "_").replace("\\", "_")
    if os.sep not in {"/", "\\"}:
        sanitized = sanitized.replace(os.sep, "_")
    return sanitized


def _prepare_run_dir(output_dir: Path, run_slug: str) -> Path:
    safe_slug = _sanitize_slug(run_slug)
    run_dir = output_dir / f"{RUN_PREFIX}-{safe_slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:
    keep = max(keep, 1)
    if not output_dir.exists():
        return
    dirs = [
        candidate
        for candidate in output_dir.iterdir()
        if candidate.is_dir() and candidate.name.startswith(f"{RUN_PREFIX}-")
    ]
    dirs.sort(key=lambda item: item.name, reverse=True)
    for index, path in enumerate(dirs):
        if index < keep or path == current_run:
            continue
        for child in path.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)
        path.rmdir()


_copy_latest = copy_latest_artifact


def _rel_to_repo(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path.resolve())


def _summarize_diags(diags: list[dict[str, Any]], limit: int = 5) -> str:
    if not diags:
        return ""
    notes: list[str] = []
    for diag in diags[:limit]:
        location = diag.get("file", "unknown")
        for err in diag.get("errors", []):
            notes.append(f"{location}: {err}")
    if len(diags) > limit:
        notes.append(f"(+{len(diags) - limit} more diagnostics)")
    return "; ".join(notes)


def _compose_report_payload(
    *,
    paths: Paths,
    run_slug: str,
    generated_at: datetime,
    status: str,
    index: dict[str, Any] | None,
    stats: BuildStats | None,
    notes: str,
) -> dict[str, Any]:
    rule_count = len(index.get("rules", [])) if index else 0
    summary = {
        "rule_count": rule_count,
        "category_count": stats.category_count if stats else 0,
        "source_count": stats.source_count if stats else 0,
        "extracted_count": stats.extracted_count if stats else 0,
        "accepted_count": stats.accepted_count if stats else 0,
    }
    extraction = {
        "enabled": stats.extraction_enabled if stats else False,
        "auto_accept": stats.auto_accept if stats else False,
        "extracted_count": stats.extracted_count if stats else 0,
        "accepted_count": stats.accepted_count if stats else 0,
        "pending_written": stats.pending_written if stats else False,
        "pending_file": (
            _rel_to_repo(paths.pending_file, paths.repo_root) if stats and stats.pending_written else None
        ),
        "diagnostics": stats.extraction_diags if stats else [],
    }
    return {
        "schema_version": 1,
        "status": status,
        "timestamp": run_slug,
        "generated_utc": generated_at.isoformat(),
        "repo_root": str(paths.repo_root),
        "index_path": _rel_to_repo(paths.output_index, paths.repo_root),
        "output_dir": _rel_to_repo(paths.output_dir, paths.repo_root),
        "pending_path": extraction["pending_file"],
        "integrity_hash": index.get("integrity_hash") if index else None,
        "version": index.get("version") if index else None,
        "summary": summary,
        "extraction": extraction,
        "notes": notes,
    }


def _render_report_md(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Standards Index Build Report\n\n")
    lines.append(f"- generated_utc: {payload['generated_utc']}\n")
    lines.append(f"- status: {payload['status']}\n")
    lines.append(f"- index_path: {payload['index_path']}\n")
    lines.append(f"- output_dir: {payload['output_dir']}\n")
    lines.append(f"- integrity_hash: {payload.get('integrity_hash')}\n")
    if payload.get("notes"):
        lines.append(f"- notes: {payload['notes']}\n")
    lines.append("\n## Summary\n\n")
    summary = payload.get("summary", {})
    if summary:
        lines.append("| Metric | Value |\n")
        lines.append("|---|---:|\n")
        for key, value in summary.items():
            lines.append(f"| {key} | {value} |\n")
        lines.append("\n")
    else:
        lines.append("No summary metrics captured.\n\n")

    extraction = payload.get("extraction", {})
    lines.append("## Extraction\n\n")
    lines.append(f"- enabled: {str(extraction.get('enabled', False)).lower()}\n")
    lines.append(f"- auto_accept: {str(extraction.get('auto_accept', False)).lower()}\n")
    lines.append(f"- extracted_count: {extraction.get('extracted_count', 0)}\n")
    lines.append(f"- accepted_count: {extraction.get('accepted_count', 0)}\n")
    if extraction.get("pending_file"):
        lines.append(f"- pending_file: {extraction['pending_file']}\n")
    diagnostics = extraction.get("diagnostics") or []
    if diagnostics:
        lines.append("\n### Diagnostics\n\n")
        for diag in diagnostics:
            file_path = diag.get("file", "(unknown)")
            lines.append(f"- **{file_path}**\n")
            for key in ("errors", "notes", "skipped_conflicts", "duplicate_ids", "invalid_severity_rules"):
                values = diag.get(key)
                if values:
                    for item in values:
                        lines.append(f"  - {key}: {item}\n")
    return "".join(lines)


def _render_log_text(payload: dict[str, Any]) -> str:
    lines = [
        f"status={payload['status']}",
        f"timestamp={payload['timestamp']}",
        f"integrity_hash={payload.get('integrity_hash')}",
        f"index_path={payload['index_path']}",
        f"output_dir={payload['output_dir']}",
    ]
    summary = payload.get("summary", {})
    for key, value in summary.items():
        lines.append(f"summary_{key}={value}")
    extraction = payload.get("extraction", {})
    lines.append(f"extraction_enabled={str(extraction.get('enabled', False)).lower()}")
    lines.append(f"extraction_auto_accept={str(extraction.get('auto_accept', False)).lower()}")
    lines.append(f"extraction_extracted_count={extraction.get('extracted_count', 0)}")
    lines.append(f"extraction_pending_written={str(extraction.get('pending_written', False)).lower()}")
    if payload.get("notes"):
        lines.append(f"notes={payload['notes']}")
    return "\n".join(lines) + "\n"


def write_artifacts(
    *,
    paths: Paths,
    run_dir: Path,
    run_slug: str,
    generated_at: datetime,
    index: dict[str, Any] | None,
    stats: BuildStats | None,
    status: str,
    notes: str,
) -> None:
    payload = _compose_report_payload(
        paths=paths,
        run_slug=run_slug,
        generated_at=generated_at,
        status=status,
        index=index,
        stats=stats,
        notes=notes,
    )
    report_json_path = run_dir / "report.json"
    report_json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    report_md_path = run_dir / "report.md"
    report_md_path.write_text(_render_report_md(payload), encoding="utf-8")

    log_path = run_dir / "log.txt"
    log_path.write_text(_render_log_text(payload), encoding="utf-8")

    latest_pairs: list[tuple[Path, Path]] = [
        (report_json_path, paths.output_dir / "latest_report.json"),
        (report_md_path, paths.output_dir / "latest_report.md"),
        (log_path, paths.output_dir / "latest_report.log"),
    ]

    if index is not None:
        serialized = yaml.safe_dump(index, sort_keys=False, width=100)
        run_index_path = run_dir / "index.yaml"
        run_index_path.write_text(serialized, encoding="utf-8")
        raw_yaml_path = run_dir / "raw.yaml"
        raw_yaml_path.write_text(serialized, encoding="utf-8")
        raw_txt_path = run_dir / "raw.txt"
        raw_txt_path.write_text(serialized, encoding="utf-8")
        latest_pairs.extend(
            [
                (run_index_path, paths.output_dir / "latest_index.yaml"),
                (raw_yaml_path, paths.output_dir / "latest_raw.yaml"),
                (raw_txt_path, paths.output_dir / "latest_raw.txt"),
            ]
        )

    for src, dest in latest_pairs:
        _copy_latest(src, dest)


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build repo_standards_index.yaml and emit structured artifacts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT), help="Repository root")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for run artifacts")
    parser.add_argument(
        "--categories-path", default=str(DEFAULT_RELATIVE_CATEGORIES), help="Path to standards_categories.yaml"
    )
    parser.add_argument("--seed-path", default=str(DEFAULT_RELATIVE_SEED), help="Path to standards_seed.yaml")
    parser.add_argument(
        "--extraction-module", default=str(DEFAULT_RELATIVE_EXTRACTION), help="Path to standards_extraction.py"
    )
    parser.add_argument(
        "--index-path",
        default=str(DEFAULT_RELATIVE_INDEX),
        help="Canonical index output path (defaults to latest_index.yaml bundle pointer)",
    )
    parser.add_argument("--pending-path", default=str(DEFAULT_RELATIVE_PENDING), help="Pending extraction output path")
    parser.add_argument("--timestamp", help="ISO8601 timestamp for the run directory")
    parser.add_argument(
        "--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP, help="How many historical runs to retain"
    )
    parser.add_argument("--log-level", default="INFO", help="Logging verbosity")
    return parser


def _paths_from_args(args: argparse.Namespace) -> Paths:
    repo_root = Path(args.repo_root).resolve()
    output_dir = _ensure_directory(_resolve_path(repo_root, args.output_dir))
    return Paths(
        repo_root=repo_root,
        categories_file=_resolve_path(repo_root, args.categories_path),
        seed_file=_resolve_path(repo_root, args.seed_path),
        extraction_module=_resolve_path(repo_root, args.extraction_module),
        output_index=_resolve_path(repo_root, args.index_path),
        pending_file=_resolve_path(repo_root, args.pending_path),
        output_dir=output_dir,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level)

    paths = _paths_from_args(args)
    run_slug, generated_at = _resolve_timestamp(args.timestamp)
    run_dir = _prepare_run_dir(paths.output_dir, run_slug)
    keep = max(args.artifacts_to_keep, 1)

    try:
        index, stats = build_index(paths)
    except Exception as exc:  # pragma: no cover - coarse failure boundary
        notes = str(exc)
        logging.exception("build failed: %s", exc)
        write_artifacts(
            paths=paths,
            run_dir=run_dir,
            run_slug=run_slug,
            generated_at=generated_at,
            index=None,
            stats=None,
            status="error",
            notes=notes,
        )
        prune_old_runs(paths.output_dir, keep=keep, current_run=run_dir)
        return 1

    write_index(paths, index)
    status = "pending_extractions" if stats.pending_written else "ok"
    notes = _summarize_diags(stats.extraction_diags)
    write_artifacts(
        paths=paths,
        run_dir=run_dir,
        run_slug=run_slug,
        generated_at=generated_at,
        index=index,
        stats=stats,
        status=status,
        notes=notes,
    )
    prune_old_runs(paths.output_dir, keep=keep, current_run=run_dir)

    logging.info(
        "Wrote %s (rules=%d, hash=%s)",
        paths.output_index.relative_to(paths.repo_root),
        len(index["rules"]),
        str(index["integrity_hash"])[:12],
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
