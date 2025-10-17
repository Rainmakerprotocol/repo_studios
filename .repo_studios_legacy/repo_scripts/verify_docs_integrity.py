"""Documentation Integrity Verification & (Optional) Update Utility.

Features:
1. Multi-surface hashing for governed docs enumerated in the global docs index.
2. Stable SHA256 `content_hash` injection (with `--update`) for every fenced JSON block.
3. Automatic regeneration of the docs index navigation table from the machine-readable JSON
   (between `<!-- BEGIN:DOCS_INDEX_TABLE -->` and `<!-- END:DOCS_INDEX_TABLE -->`).
4. Backwards-compatible exit codes hash output retained (`--exit-codes-hash`).

Hash Algorithm:
* Canonical serialization = `json.dumps(obj_without_content_hash, sort_keys=True, separators=(",", ":"))`.
* `content_hash` stored as lowercase hex of SHA256 digest.

Exit Codes Back-Compat:
* `compute_exit_codes_hash()` preserved for any external scripts depending on legacy behavior.

Usage:
    python scripts/verify_docs_integrity.py --index docs/standards/docs_index.md
    python scripts/verify_docs_integrity.py --index docs/standards/docs_index.md --update

Optional Flags:
    --no-table   Skip navigation table regeneration.
    --exit-codes-hash  Print legacy exit code hash only and exit 0.

Exit Codes:
    0 success (or updated successfully with --update)
    1 mismatch detected (without --update) or processing error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXIT_CODE_DOC = Path("docs/standards/exit_code_stability_policy.md")
JSON_BLOCK_PATTERN = re.compile(r"```jsonc?\n(.*?)```", re.DOTALL)
HASH_KEYS_ORDER = ["code", "symbol", "class", "stable"]
INDEX_TABLE_BEGIN = "<!-- BEGIN:DOCS_INDEX_TABLE -->"
INDEX_TABLE_END = "<!-- END:DOCS_INDEX_TABLE -->"


@dataclass
class JsonBlockResult:
    index: int
    hash: str
    updated: bool
    path: Path


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
    # Assume first block corresponds to exit codes set
    block = blocks[0]
    codes = block.get("codes")
    if not isinstance(codes, list):
        raise SystemExit("Malformed codes array in JSON block")
    # Normalized list of dicts restricted to known keys
    normalized = [{k: c.get(k) for k in HASH_KEYS_ORDER} for c in codes if isinstance(c, dict)]
    serialized = _stable_serialize({"codes": normalized})
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _compute_hash_for_json_block(block: dict[str, Any]) -> str:
    clone = {k: v for k, v in block.items() if k != "content_hash"}
    return hashlib.sha256(_stable_serialize(clone).encode("utf-8")).hexdigest()


def _replace_nth_code_block(text: str, n: int, new_json: dict[str, Any]) -> str:
    """Replace the Nth fenced json/jsonc block with pretty printed JSON including content_hash.

    Args:
        text: original file content
        n: zero-based index of JSON block
        new_json: dict already containing updated content_hash
    """
    matches = list(JSON_BLOCK_PATTERN.finditer(text))
    if n >= len(matches):  # pragma: no cover - defensive
        return text
    match = matches[n]
    pretty = json.dumps(new_json, indent=2, sort_keys=True) + "\n"
    replacement = f"```json\n{pretty}```"
    return text[: match.start()] + replacement + text[match.end() :]


def process_file(path: Path, update: bool) -> list[JsonBlockResult]:
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
        else:
            results.append(JsonBlockResult(idx, digest, False, path))
    if update and changed:
        path.write_text(text, encoding="utf-8")
    return results


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
    pattern = re.compile(
        rf"{re.escape(INDEX_TABLE_BEGIN)}.*?{re.escape(INDEX_TABLE_END)}", re.DOTALL
    )
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
    # Simple heuristic mapping; keep extremely short to satisfy MD013.
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


def verify_all(index_path: Path, update: bool, regen_table: bool) -> int:
    index_json = _load_index_json(index_path)
    docs_raw = index_json.get("documents", [])
    if not isinstance(docs_raw, list):
        logging.error("'documents' array missing in index JSON")
        return 1
    governed = [d for d in docs_raw if isinstance(d, dict) and d.get("json_block")]
    mismatches = _process_documents(governed, update)
    process_file(index_path, update=update)  # ensure index JSON has its hash
    if regenerate_index_table(index_path, skip=not regen_table):
        process_file(index_path, update=update)
    return _summarize(mismatches, update)


def _process_documents(docs: list[dict[str, Any]], update: bool) -> list[JsonBlockResult]:
    results: list[JsonBlockResult] = []
    for d in docs:
        path = Path(d.get("path", ""))
        if not path.exists():
            logging.error("Listed doc path missing: %s", path)
            return results
        results.extend(process_file(path, update=update))
    return results


def _summarize(mismatches: list[JsonBlockResult], update: bool) -> int:
    if not mismatches:
        logging.info("All governed JSON blocks verified.")
        return 0
    heading = (
        "Updated content_hash for blocks:"
        if update
        else "Mismatched or missing content_hash for blocks:"
    )
    (logging.info if update else logging.warning)(heading)
    for m in mismatches:
        logging.info(
            " - %s#block%d => %s%s", m.path, m.index, m.hash, " (updated)" if update else ""
        )
    return 0 if update else 1


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Verify (and optionally update) governed doc content hashes."
    )
    p.add_argument(
        "--index",
        type=Path,
        required=False,
        default=Path("docs/standards/docs_index.md"),
        help="Path to docs index markdown file",
    )
    p.add_argument("--update", action="store_true", help="Write back computed content_hash values")
    p.add_argument("--no-table", action="store_true", help="Skip index table regeneration")
    p.add_argument(
        "--exit-codes-hash", action="store_true", help="Print legacy exit codes hash and exit"
    )
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    if ns.exit_codes_hash:
        try:
            digest = compute_exit_codes_hash()
        except SystemExit as e:  # pragma: no cover
            logging.exception("%s", e)
            return 1
        logging.info("exit_codes_hash=%s", digest)
        return 0
    return verify_all(ns.index, update=ns.update, regen_table=not ns.no_table)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
