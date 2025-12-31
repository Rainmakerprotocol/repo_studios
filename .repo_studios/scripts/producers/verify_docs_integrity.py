"""Documentation integrity verifier (canonical producer bundle).

Validates governed documentation JSON blocks to ensure each fenced payload exposes a
stable `content_hash`. Optionally updates mismatched blocks in place (`--update`) and
regenerates the navigation table in `docs/standards/docs_index.md`.

Artifacts:
    * Canonical bundle artifacts under
        `.repo_studios/reports/producer_reports/healthview/docs_integrity_validation/<YYYYMMDD-HHMM>/`
    * Files: `manifest.json`, `summary.md`, `telemetry.json`
    * Timestamped run folders with automatic pruning (keep last N by default)

Exit codes:
    0 - clean or updated (when `--update` supplied)
    1 - mismatches detected (without `--update`) OR missing inputs/errors

`--exit-codes-hash` preserves the legacy behavior of printing the hash of
`docs/standards/exit_code_stability_policy.md` and exits without writing artifacts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, cast

EXIT_CODE_DOC = Path("docs/standards/exit_code_stability_policy.md")
JSON_BLOCK_PATTERN = re.compile(r"```jsonc?\n(.*?)```", re.DOTALL)
HASH_KEYS_ORDER = ["code", "symbol", "class", "stable"]
INDEX_TABLE_BEGIN = "<!-- BEGIN:DOCS_INDEX_TABLE -->"
INDEX_TABLE_END = "<!-- END:DOCS_INDEX_TABLE -->"

DEFAULT_INDEX_PATH = Path(".repo_studios/docs/standards/docs_index.md")
TOPIC_SLUG = "docs_integrity_validation"
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
        prune_run_directories,
    )
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
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep

try:
    from libraries.database_integration import create_storage
except ModuleNotFoundError:  # pragma: no cover - fallback when running standalone
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries.database_integration import create_storage

# Must be after import block where get_keep is defined
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("verify_docs_integrity")
DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)


@dataclass
class JsonBlockResult:
    index: int
    hash: str
    updated: bool
    path: Path


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    index_path: Path


@dataclass(frozen=True)
class Options:
    update: bool = False
    regen_table: bool = True
    artifacts_to_keep: int = 1
    log_level: str = "INFO"


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(
            field="output_dir",
            default=DEFAULT_OUTPUT_DIR,
            ensure_dir=True,
            within_repo=False,
        ),
        "index_path": PathSpec(
            field="index",
            default=DEFAULT_INDEX_PATH,
            within_repo=False,
        ),
    },
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
    },
)


@dataclass
class DocumentProcessingResult:
    mismatches: list[JsonBlockResult] = field(default_factory=list)
    json_blocks_checked: int = 0
    documents_processed: int = 0
    documents_updated: int = 0
    missing_documents: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class VerificationOutcome:
    mismatches: list[JsonBlockResult] = field(default_factory=list)
    json_blocks_checked: int = 0
    documents_processed: int = 0
    documents_updated: int = 0
    index_blocks_checked: int = 0
    index_updated: bool = False
    table_regenerated: bool = False
    missing_documents: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="verify_docs_integrity",
        description=__doc__ or "",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", help="Repository root directory")
    parser.add_argument("--output-dir", help="Directory for structured artifacts")
    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Path to docs index markdown file",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical run directories to retain",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Write back computed content_hash values",
    )
    parser.add_argument(
        "--no-table",
        action="store_true",
        help="Skip index table regeneration",
    )
    parser.add_argument(
        "--exit-codes-hash",
        action="store_true",
        help="Print legacy exit code hash and exit",
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


def _format_run_timestamp(timestamp: dt.datetime) -> str:
    return timestamp.astimezone(dt.timezone.utc).strftime("%Y%m%d-%H%M")


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    base_options = cast(Options, build_standard_options(args, OPTIONS_CONFIG))
    return replace(
        base_options,
        update=bool(args.update),
        regen_table=not bool(args.no_table),
        log_level=str(args.log_level),
    )


def _extract_json_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for match in JSON_BLOCK_PATTERN.finditer(text):
        raw = match.group(1).strip()
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return blocks


def _stable_serialize(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def compute_exit_codes_hash() -> str:
    content = EXIT_CODE_DOC.read_text(encoding="utf-8")
    blocks = _extract_json_blocks(content)
    if not blocks:
        raise SystemExit("No JSON blocks found in exit code policy doc")
    block = blocks[0]
    codes = block.get("codes")
    if not isinstance(codes, list):
        raise SystemExit("Malformed codes array in JSON block")
    normalized = [{k: c.get(k) for k in HASH_KEYS_ORDER} for c in codes if isinstance(c, dict)]
    serialized = _stable_serialize({"codes": normalized})
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _compute_hash_for_json_block(block: dict[str, Any]) -> str:
    clone = {k: v for k, v in block.items() if k != "content_hash"}
    return hashlib.sha256(_stable_serialize(clone).encode("utf-8")).hexdigest()


def _replace_nth_code_block(text: str, n: int, new_json: dict[str, Any]) -> str:
    matches = list(JSON_BLOCK_PATTERN.finditer(text))
    if n >= len(matches):  # pragma: no cover - defensive
        return text
    match = matches[n]
    pretty = json.dumps(new_json, indent=2, sort_keys=True) + "\n"
    replacement = f"```json\n{pretty}```"
    return text[: match.start()] + replacement + text[match.end() :]


def process_file(path: Path, update: bool) -> tuple[list[JsonBlockResult], int, bool]:
    text = path.read_text(encoding="utf-8")
    blocks = _extract_json_blocks(text)
    results: list[JsonBlockResult] = []
    changed = False
    for idx, block in enumerate(blocks):
        digest = _compute_hash_for_json_block(block)
        existing = block.get("content_hash")
        if existing != digest:
            if update:
                block["content_hash"] = digest
                text = _replace_nth_code_block(text, idx, block)
                changed = True
            results.append(JsonBlockResult(idx, digest, update, path))
    if update and changed:
        path.write_text(text, encoding="utf-8")
    return results, len(blocks), changed


def _load_index_json(index_path: Path) -> dict[str, Any]:
    content = index_path.read_text(encoding="utf-8")
    blocks = _extract_json_blocks(content)
    if not blocks:
        raise SystemExit("Global docs index JSON block not found")
    return blocks[0]


def regenerate_index_table(index_path: Path, skip: bool) -> bool:
    if skip:
        return False
    content = index_path.read_text(encoding="utf-8")
    if INDEX_TABLE_BEGIN not in content or INDEX_TABLE_END not in content:
        return False
    index_json = _load_index_json(index_path)
    docs = [d for d in index_json.get("documents", []) if isinstance(d, dict)]
    lines = _build_index_table_lines(docs)
    table_body = "\n".join(lines)
    pattern = re.compile(rf"{re.escape(INDEX_TABLE_BEGIN)}.*?{re.escape(INDEX_TABLE_END)}", re.DOTALL)
    new_section = f"{INDEX_TABLE_BEGIN}\n\n{table_body}\n\n{INDEX_TABLE_END}"
    new_content = pattern.sub(new_section, content)
    if new_content != content:
        index_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def _build_index_table_lines(docs: list[dict[str, Any]]) -> list[str]:
    header = "| Category | Doc ID | File | Summary | JSON | Stability |"
    sep = "|----------|--------|------|---------|------|-----------|"
    rows: list[str] = [header, sep]
    for d in docs:
        cat = d.get("category", "")
        doc_id = d.get("doc_id", "")
        path = d.get("path", "")
        short_path = path.replace("docs/", "", 1)
        stability = d.get("stability", "")
        has_json = "yes" if d.get("json_block") else "no"
        rows.append(
            f"| {cat.capitalize()} | {doc_id} | {short_path} | {_derive_summary(doc_id)} | {has_json} | {stability} |"
        )
    return rows


def _derive_summary(doc_id: str) -> str:
    mapping = {
        "exit_code_stability_policy": "Exit codes",
        "additive_observability_policy": "Additive",
        "test_flag_safety_policy": "Flag classes",
        "lifecycle_metrics_inventory": "Lifecycle",
        "degraded_reasons_taxonomy": "Degraded reasons",
        "drift_guard_matrix": "Drift matrix",
        "observability_roadmap": "Roadmap",
        "known_issues_tracker": "Issues",
        "glossary": "Glossary",
        "doc_template": "Template",
    }
    return mapping.get(doc_id, doc_id[:20])


def _relativize(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def _process_documents(docs: list[dict[str, Any]], update: bool, repo_root: Path) -> DocumentProcessingResult:
    result = DocumentProcessingResult()
    for entry in docs:
        raw_path = str(entry.get("path", ""))
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        if not candidate.exists():
            logging.error("Listed doc path missing: %s", candidate)
            result.missing_documents.append(raw_path or candidate.as_posix())
            continue
        try:
            processed, block_count, changed = process_file(candidate, update=update)
        except Exception as exc:  # pragma: no cover - defensive
            logging.exception("Failed to process %s", candidate)
            result.errors.append(f"{raw_path or candidate.as_posix()}: {exc}")
            continue
        result.json_blocks_checked += block_count
        result.documents_processed += 1
        if changed:
            result.documents_updated += 1
        result.mismatches.extend(processed)
    return result


def verify_all(paths: Paths, options: Options) -> VerificationOutcome:
    outcome = VerificationOutcome()
    if not paths.index_path.exists():
        msg = f"Index path not found: {paths.index_path}"
        logging.error(msg)
        outcome.errors.append(msg)
        return outcome
    try:
        index_json = _load_index_json(paths.index_path)
    except SystemExit as exc:
        msg = str(exc)
        logging.error(msg)
        outcome.errors.append(msg)
        return outcome

    docs_raw = index_json.get("documents", [])
    if not isinstance(docs_raw, list):
        msg = "'documents' array missing in index JSON"
        logging.error(msg)
        outcome.errors.append(msg)
        return outcome

    governed = [d for d in docs_raw if isinstance(d, dict) and d.get("json_block")]
    doc_result = _process_documents(governed, options.update, paths.repo_root)
    outcome.mismatches.extend(doc_result.mismatches)
    outcome.json_blocks_checked += doc_result.json_blocks_checked
    outcome.documents_processed += doc_result.documents_processed
    outcome.documents_updated += doc_result.documents_updated
    outcome.missing_documents.extend(doc_result.missing_documents)
    outcome.errors.extend(doc_result.errors)

    table_regenerated = regenerate_index_table(paths.index_path, skip=not options.regen_table)
    outcome.table_regenerated = table_regenerated

    try:
        index_results, index_blocks, index_changed = process_file(paths.index_path, update=options.update)
    except Exception as exc:  # pragma: no cover - defensive
        msg = f"{paths.index_path}: {exc}"
        logging.exception(msg)
        outcome.errors.append(msg)
        return outcome

    outcome.mismatches.extend(index_results)
    outcome.json_blocks_checked += index_blocks
    outcome.index_blocks_checked = index_blocks
    if index_changed:
        outcome.index_updated = True

    return outcome


def compose_payload(
    paths: Paths,
    options: Options,
    outcome: VerificationOutcome,
    run_id: str,
    timestamp: dt.datetime,
) -> dict[str, Any]:
    mismatches = [
        {
            "path": _relativize(result.path, paths.repo_root),
            "block_index": result.index,
            "computed_hash": result.hash,
            "updated": result.updated,
        }
        for result in outcome.mismatches
    ]

    if outcome.errors:
        status = "error"
        exit_code = 1
        message = "Errors encountered during documentation integrity verification."
    elif outcome.missing_documents:
        status = "missing-documents"
        exit_code = 1
        message = "One or more governed documents were missing."
    elif mismatches and not options.update:
        status = "mismatches"
        exit_code = 1
        message = "content_hash mismatches detected."
    elif mismatches and options.update:
        status = "updated"
        exit_code = 0
        message = "content_hash fields updated for mismatched blocks."
    else:
        status = "ok"
        exit_code = 0
        message = "All governed JSON blocks verified."

    mismatched_blocks = len(mismatches) if status == "mismatches" else 0

    summary = {
        "documents_processed": outcome.documents_processed,
        "json_blocks_checked": outcome.json_blocks_checked,
        "mismatched_blocks": mismatched_blocks,
        "documents_updated": outcome.documents_updated + (1 if outcome.index_updated else 0),
        "index_blocks_checked": outcome.index_blocks_checked,
        "table_regenerated": outcome.table_regenerated,
    }

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "timestamp": timestamp.isoformat(),
        "status": status,
        "exit_code": exit_code,
        "message": message,
        "run_id": run_id,
        "output_dir": str(paths.output_dir),
        "paths": {
            "repo_root": str(paths.repo_root),
            "index_path": _relativize(paths.index_path, paths.repo_root),
        },
        "options": {
            "update": options.update,
            "regen_table": options.regen_table,
            "artifacts_to_keep": options.artifacts_to_keep,
            "log_level": options.log_level,
        },
        "summary": summary,
        "mismatches": mismatches,
        "missing_documents": outcome.missing_documents,
        "errors": outcome.errors,
    }
    return payload


def compose_manifest(*, report: dict[str, Any], run_timestamp: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "viewer_slug": "producer_reports",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_timestamp,
        "generated_utc": report.get("timestamp"),
        "git_sha": None,
        "status": report.get("status", "unknown"),
        "catalog": [
            {"artifact": "manifest.json", "kind": "json"},
            {"artifact": "summary.md", "kind": "markdown"},
            {"artifact": "telemetry.json", "kind": "json"},
        ],
        "inputs": inputs,
        "provenance": {
            "requested_by": "cli",
            "trigger_type": "manual",
        },
        "summary": report.get("summary") or {},
    }


def compose_telemetry(*, report: dict[str, Any], run_timestamp: str) -> dict[str, Any]:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    return {
        "schema_version": 1,
        "viewer_slug": "producer_reports",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_timestamp,
        "generated_utc": report.get("timestamp"),
        "status": report.get("status", "unknown"),
        "metrics": {
            "documents_processed": summary.get("documents_processed", 0),
            "json_blocks_checked": summary.get("json_blocks_checked", 0),
            "mismatched_blocks": summary.get("mismatched_blocks", 0),
            "documents_updated": summary.get("documents_updated", 0),
            "index_blocks_checked": summary.get("index_blocks_checked", 0),
            "table_regenerated": bool(summary.get("table_regenerated", False)),
            "missing_documents_count": len(report.get("missing_documents", []) or []),
            "errors_count": len(report.get("errors", []) or []),
        },
        "payload": report,
    }


def render_summary_markdown(*, report: dict[str, Any], run_timestamp: str) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Documentation Integrity Report\n\n",
        f"- Status: `{report.get('status', 'unknown')}`\n",
        f"- Run Timestamp (UTC): `{run_timestamp}`\n",
        f"- Documents processed: {summary.get('documents_processed', 0)}\n",
        f"- JSON blocks checked: {summary.get('json_blocks_checked', 0)}\n",
        f"- Blocks updated: {summary.get('documents_updated', 0)}\n",
    ]
    if summary.get("table_regenerated"):
        lines.append("- Navigation table regenerated.\n")
    if report.get("missing_documents"):
        lines.append("\n## Missing Documents\n\n")
        for item in report["missing_documents"]:
            lines.append(f"- {item}\n")
    if report.get("errors"):
        lines.append("\n## Errors\n\n")
        for err in report["errors"]:
            lines.append(f"- {err}\n")
    if report.get("status") == "mismatches":
        lines.append("\n## Pending Mismatches\n\n")
        lines.append("| File | Block | Computed Hash |\n")
        lines.append("|------|-------|---------------|\n")
        for item in report.get("mismatches", []):
            lines.append(f"| `{item['path']}` | {item['block_index']} | `{item['computed_hash']}` |\n")
    if report.get("status") == "updated":
        lines.append("\nAll mismatched blocks were updated because `--update` was supplied.")
    return "".join(lines)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    configure_logging(args.log_level)
    logger = logging.getLogger(__name__)

    if args.exit_codes_hash:
        try:
            digest = compute_exit_codes_hash()
        except SystemExit as exc:  # pragma: no cover - legacy behavior
            logger.exception("%s", exc)
            return {
                "status": "error",
                "exit_code": 1,
                "message": str(exc),
                "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                "run_id": "exit-codes-hash",
            }
        logger.info("exit_codes_hash=%s", digest)
        return {
            "status": "exit-codes-hash",
            "exit_code": 0,
            "message": "Reported legacy exit codes hash.",
            "digest": digest,
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "run_id": "exit-codes-hash",
        }

    paths = build_paths(args)
    options = build_options(args)

    if paths.output_dir.name == "docs_integrity_reports":
        logger.warning(
            "Deprecated output dir detected (%s). Use build_topic_path('producer', '%s') instead.",
            paths.output_dir,
            TOPIC_SLUG,
        )
        paths = replace(paths, output_dir=paths.output_dir.parent)

    paths.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Repo root: %s", paths.repo_root)
    logger.info("Index path: %s", paths.index_path)
    logger.info("Output directory: %s", paths.output_dir)

    timestamp = dt.datetime.now(dt.timezone.utc)
    run_timestamp = _format_run_timestamp(timestamp)

    outcome = verify_all(paths, options)
    report = compose_payload(paths, options, outcome, run_timestamp, timestamp)

    inputs: dict[str, Any] = {
        "repo_root": str(paths.repo_root),
        "index_path": _relativize(paths.index_path, paths.repo_root),
        "update": options.update,
        "regen_table": options.regen_table,
        "artifacts_to_keep": options.artifacts_to_keep,
        "log_level": options.log_level,
    }
    manifest = compose_manifest(report=report, run_timestamp=run_timestamp, inputs=inputs)
    telemetry = compose_telemetry(report=report, run_timestamp=run_timestamp)
    summary_md = render_summary_markdown(report=report, run_timestamp=run_timestamp)

    storage = create_storage(
        output_dir=paths.output_dir,
        viewer_slug="",  # output_dir already contains full topic path
        topic="",  # output_dir already contains full topic path
        timestamp=run_timestamp,
    )

    # DB_INTEGRATION_MARKER: docs integrity manifest
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: docs integrity summary markdown
    storage.write_summary({"markdown": summary_md}, format="markdown")
    # DB_INTEGRATION_MARKER: docs integrity telemetry
    storage.write_telemetry(telemetry)

    run_dir = storage.file_storage.bundle_dir
    topic_dir = run_dir.parent
    prune_result = prune_run_directories(
        topic_dir,
        keep=max(options.artifacts_to_keep, 1),
        current_run=run_dir,
        logger=logger,
    )
    if prune_result.removed:
        logger.debug(
            "Pruned docs integrity bundles: kept=%s removed=%s protected=%s failures=%s",
            len(prune_result.kept),
            len(prune_result.removed),
            len(prune_result.protected),
            len(prune_result.failures),
        )

    result = dict(report)
    result.update(
        {
            "viewer_slug": "producer_reports",
            "topic": TOPIC_SLUG,
            "run_timestamp": run_timestamp,
            "run_dir": str(run_dir),
            "artifacts": {
                "manifest.json": str(run_dir / "manifest.json"),
                "summary.md": str(run_dir / "summary.md"),
                "telemetry.json": str(run_dir / "telemetry.json"),
            },
        }
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    payload = run(argv or sys.argv[1:])
    return int(payload.get("exit_code", 0))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
