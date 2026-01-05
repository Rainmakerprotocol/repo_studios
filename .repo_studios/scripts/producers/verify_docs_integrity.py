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
    """Result of processing a JSON code block in a document.

    Attributes:
        index: Zero-based index of the block within the document.
        hash: Computed hash of the JSON block content.
        updated: Whether the block was updated during processing.
        path: Path to the document containing the block.
    """

    index: int
    hash: str
    updated: bool
    path: Path


@dataclass(frozen=True)
class Paths:
    """Path configuration for the docs integrity verifier.

    Attributes:
        repo_root: Repository root directory.
        output_dir: Output directory for generated artifacts.
        index_path: Path to the documentation index file.
    """

    repo_root: Path
    output_dir: Path
    index_path: Path


@dataclass(frozen=True)
class Options:
    """Runtime options for the docs integrity verifier.

    Attributes:
        update: Whether to update mismatched JSON blocks in place.
        regen_table: Whether to regenerate the index table.
        artifacts_to_keep: Number of historical artifact bundles to retain.
        log_level: Logging level for output.
    """

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
    """Aggregate results from processing all documents.

    Attributes:
        mismatches: List of JsonBlockResult objects for mismatched blocks.
        json_blocks_checked: Total JSON blocks examined.
        documents_processed: Total documents processed.
        documents_updated: Documents that were modified.
        missing_documents: Paths of documents that could not be found.
        errors: Error messages encountered during processing.
    """

    mismatches: list[JsonBlockResult] = field(default_factory=list)
    json_blocks_checked: int = 0
    documents_processed: int = 0
    documents_updated: int = 0
    missing_documents: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class VerificationOutcome:
    """Complete verification results including index processing.

    Attributes:
        mismatches: List of JsonBlockResult objects for mismatched blocks.
        json_blocks_checked: Total JSON blocks examined.
        documents_processed: Total documents processed.
        documents_updated: Documents that were modified.
        index_blocks_checked: JSON blocks checked in the index file.
        index_updated: Whether the index file was updated.
        table_regenerated: Whether the index table was regenerated.
        missing_documents: Paths of documents that could not be found.
        errors: Error messages encountered during processing.
    """

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
    """Parse command-line arguments for the docs integrity verifier.

    Configure and parse CLI arguments including repo root, output directory,
    index path, update mode, and table regeneration options.

    Args:
        argv: Command-line arguments to parse, or None for sys.argv.

    Returns:
        A Namespace object with parsed argument values.
    """
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
    """Configure logging with the specified level.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def _format_run_timestamp(timestamp: dt.datetime) -> str:
    """Format a datetime as a run timestamp for directory naming.

    Args:
        timestamp: A datetime object.

    Returns:
        A string in YYYYMMDD-HHMM format in UTC.
    """
    return timestamp.astimezone(dt.timezone.utc).strftime("%Y%m%d-%H%M")


def build_paths(args: argparse.Namespace) -> Paths:
    """Build the Paths configuration from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        A Paths dataclass with resolved paths.
    """
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    """Build the Options configuration from parsed arguments.

    Merge CLI arguments with defaults to produce the runtime options.

    Args:
        args: Parsed command-line arguments.

    Returns:
        An Options dataclass with runtime configuration.
    """
    base_options = cast(Options, build_standard_options(args, OPTIONS_CONFIG))
    return replace(
        base_options,
        update=bool(args.update),
        regen_table=not bool(args.no_table),
        log_level=str(args.log_level),
    )


def _extract_json_blocks(text: str) -> list[dict[str, Any]]:
    """Extract JSON objects from fenced code blocks in markdown.

    Parse all json code blocks and return successfully decoded dictionaries.

    Args:
        text: Markdown content to parse.

    Returns:
        A list of parsed JSON dictionaries.
    """
    blocks: list[dict[str, Any]] = []
    for match in JSON_BLOCK_PATTERN.finditer(text):
        raw = match.group(1).strip()
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return blocks


def _stable_serialize(data: dict[str, Any]) -> str:
    """Serialize a dictionary to a stable JSON string for hashing.

    Args:
        data: Dictionary to serialize.

    Returns:
        A compact, sorted JSON string.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def compute_exit_codes_hash() -> str:
    """Compute the hash of the exit codes policy document.

    Read the exit code doc, extract the codes array, and compute
    a SHA-256 hash for integrity verification.

    Returns:
        A hexadecimal hash string.

    Raises:
        SystemExit: If no JSON blocks or malformed codes array.
    """
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
    """Compute a SHA-256 hash for a JSON block excluding content_hash.

    Args:
        block: JSON block dictionary.

    Returns:
        A hexadecimal hash string.
    """
    clone = {k: v for k, v in block.items() if k != "content_hash"}
    return hashlib.sha256(_stable_serialize(clone).encode("utf-8")).hexdigest()


def _replace_nth_code_block(text: str, n: int, new_json: dict[str, Any]) -> str:
    """Replace the nth JSON code block in markdown text.

    Args:
        text: Markdown content.
        n: Zero-based index of the block to replace.
        new_json: New JSON content for the block.

    Returns:
        Updated markdown text with the block replaced.
    """
    matches = list(JSON_BLOCK_PATTERN.finditer(text))
    if n >= len(matches):  # pragma: no cover - defensive
        return text
    match = matches[n]
    pretty = json.dumps(new_json, indent=2, sort_keys=True) + "\n"
    replacement = f"```json\n{pretty}```"
    return text[: match.start()] + replacement + text[match.end() :]


def process_file(path: Path, update: bool) -> tuple[list[JsonBlockResult], int, bool]:
    """Process a markdown file for JSON block integrity.

    Extract JSON blocks, verify content_hash values, and optionally
    update mismatched hashes in place.

    Args:
        path: Path to the markdown file.
        update: Whether to update mismatched blocks.

    Returns:
        A tuple of (mismatches, blocks_checked, file_was_changed).
    """
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
    """Load the JSON block from the docs index file.

    Args:
        index_path: Path to the docs index markdown file.

    Returns:
        The first JSON block as a dictionary.

    Raises:
        SystemExit: If no JSON block is found.
    """
    content = index_path.read_text(encoding="utf-8")
    blocks = _extract_json_blocks(content)
    if not blocks:
        raise SystemExit("Global docs index JSON block not found")
    return blocks[0]


def regenerate_index_table(index_path: Path, skip: bool) -> bool:
    """Regenerate the markdown table in the docs index file.

    Parse the index JSON and rebuild the table between markers.

    Args:
        index_path: Path to the docs index markdown file.
        skip: If True, skip regeneration entirely.

    Returns:
        True if the file was updated, False otherwise.
    """
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
    """Build markdown table lines from document entries.

    Args:
        docs: List of document metadata dictionaries.

    Returns:
        A list of markdown table row strings.
    """
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
    """Derive a short summary label from a document ID.

    Map known doc IDs to human-readable summaries, or truncate
    the ID for unknown documents.

    Args:
        doc_id: The document identifier string.

    Returns:
        A short summary label.
    """
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
    """Convert a path to a relative POSIX path string.

    Args:
        path: Absolute or relative path to convert.
        base: Base directory for relative path computation.

    Returns:
        A POSIX-formatted relative path string.
    """
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def _process_documents(docs: list[dict[str, Any]], update: bool, repo_root: Path) -> DocumentProcessingResult:
    """Process all documents from the index for integrity checks.

    Iterate through document entries, verify JSON blocks, and
    optionally update mismatched hashes.

    Args:
        docs: List of document metadata dictionaries from the index.
        update: Whether to update mismatched blocks in place.
        repo_root: Repository root for resolving relative paths.

    Returns:
        A DocumentProcessingResult with aggregate statistics.
    """
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
    """Verify all governed documents and the index file.

    Load the index, process each document with a JSON block, and
    optionally regenerate the index table.

    Args:
        paths: Path configuration.
        options: Runtime options.

    Returns:
        A VerificationOutcome with aggregate results.
    """
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
    """Compose the complete verification report payload.

    Build the report dictionary with status, summary, mismatches,
    and metadata for artifact storage.

    Args:
        paths: Path configuration.
        options: Runtime options.
        outcome: Verification outcome from verify_all.
        run_id: Unique run identifier string.
        timestamp: Timestamp of the verification run.

    Returns:
        A dictionary containing the full verification report.
    """
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
    """Compose the manifest dictionary for the verification run.

    Build a manifest with run metadata, status, and artifact catalog.

    Args:
        report: The verification report dictionary.
        run_timestamp: Timestamp slug for the run.
        inputs: Dictionary of input parameters.

    Returns:
        A manifest dictionary for the verification bundle.
    """
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
    """Compose the telemetry dictionary for the verification run.

    Build telemetry with metrics about documents processed, blocks
    checked, and any errors or mismatches found.

    Args:
        report: The verification report dictionary.
        run_timestamp: Timestamp slug for the run.

    Returns:
        A telemetry dictionary with metrics and payload.
    """
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
    """Render the verification report as a markdown summary.

    Format the report with status, metrics, and any errors or
    mismatches for human readability.

    Args:
        report: The verification report dictionary.
        run_timestamp: Timestamp slug for the run.

    Returns:
        A markdown-formatted summary string.
    """
    summary = report.get("summary", {})
    paths = report.get("paths", {}) if isinstance(report.get("paths"), dict) else {}
    index_path = paths.get("index_path")
    lines = [
        "# Documentation Integrity Report\n\n",
        f"- Status: `{report.get('status', 'unknown')}`\n",
        f"- Run Timestamp (UTC): `{run_timestamp}`\n",
        f"- Index path: `{index_path}`\n" if index_path else "- Index path: (unknown)\n",
        "- Integrity: verifies governed fenced JSON blocks have a stable `content_hash` matching the computed SHA-256.\n",
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
    """Run the documentation integrity verification workflow.

    Parse arguments, verify documents, compose report artifacts,
    and write results to the output directory.

    Args:
        argv: Command-line arguments. Uses sys.argv[1:] if None.

    Returns:
        A dictionary with verification results, run metadata, and
        paths to generated artifacts.
    """
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
    """CLI entry point for documentation integrity verification.

    Run the verification workflow and return the exit code.

    Args:
        argv: Command-line arguments. Uses sys.argv[1:] if None.

    Returns:
        Integer exit code (0 for success).
    """
    payload = run(argv or sys.argv[1:])
    return int(payload.get("exit_code", 0))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
