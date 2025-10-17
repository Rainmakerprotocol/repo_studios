"""Build script for generating repo_standards_index.yaml

Phase: Seed + optional heuristic extraction (v0)

Responsibilities:
- Load category & source mapping from standards_categories.yaml
- Load seed rules from standards_seed.yaml
- Optionally perform heuristic extraction (markers + heading pattern) when
    ENABLE_STANDARDS_EXTRACTION=1 (or truthy alias) is set in the environment.
- Optionally auto-accept extracted rules into the main index when
    AUTO_ACCEPT_EXTRACTED=1; otherwise write them to repo_standards_pending.yaml.
- Compute integrity hash over (id|last_updated|severity) fragments deterministically.
- Write YAML file (idempotent apart from generated_at timestamp).

Future phases will add:
- Overrides merge & deprecation lifecycle fields
- Coverage statistics and source section mapping
- Enforcement integration feedback loop

Usage:
    python ./.repo_studios/build_standards_index.py

Exit codes:
    0 success
    1 failure (IO/parse)
"""
from __future__ import annotations

import hashlib
import logging
import os
import runpy
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, TypedDict, cast

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover - dependency issue surfaced early
    logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(message)s")
    logging.error("missing dependency pyyaml: %s", exc)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
INSTRUCTIONS_DIR = ROOT / ".repo_studios"
CATEGORIES_FILE = INSTRUCTIONS_DIR / "standards_categories.yaml"
SEED_FILE = INSTRUCTIONS_DIR / "standards_seed.yaml"
OUTPUT_FILE = ROOT / "repo_standards_index.yaml"
PENDING_FILE = ROOT / "repo_standards_pending.yaml"
SCHEMA_VERSION = 1


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


def _load_categories() -> tuple[dict[str, Category], list[Source]]:
    if not CATEGORIES_FILE.exists():
        raise FileNotFoundError(f"Category mapping file not found: {CATEGORIES_FILE}")
    data = yaml.safe_load(CATEGORIES_FILE.read_text(encoding="utf-8"))
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
        sources.append(Source(path=ROOT / src["path"], categories=src.get("categories", [])))
    return categories, sources


def _validate_sources(categories: dict[str, Category], sources: list[Source]) -> None:
    missing = [s for s in sources if not s.path.exists()]
    if missing:
        missing_str = ", ".join(str(m.path) for m in missing)
        raise FileNotFoundError(f"Missing source files: {missing_str}")
    for s in sources:
        for cid in s.categories:
            if cid not in categories:
                raise ValueError(f"Source {s.path} references unknown category '{cid}'")


def _compute_integrity_hash(rule_fragments: list[str]) -> str:
    # Deterministic hash: join fragments with \n and sha256
    joined = "\n".join(rule_fragments)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _build_empty_rules_hash() -> str:
    # No rules yet: still produce a stable hash constant for initial commit
    return _compute_integrity_hash([])


try:  # Provide a UTC constant (support older minor versions where attribute may be absent)
    UTC = datetime.UTC  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - fallback path
    UTC = timezone.utc


def _env_flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


def _load_seed_rules() -> tuple[list[dict[str, Any]], set[str]]:
    rules: list[dict[str, Any]] = []
    seed_ids: set[str] = set()
    if SEED_FILE.exists():
        seed_data = yaml.safe_load(SEED_FILE.read_text(encoding="utf-8")) or {}
        for r in seed_data.get("rules", []) or []:
            rules.append(r)
            if r.get("id"):
                seed_ids.add(r["id"])
    return rules, seed_ids


class ExtractDiagnostics(TypedDict, total=False):
    errors: list[str]
    notes: list[str]
    file: str
    rules_found: int
    skipped_conflicts: list[str]
    duplicate_ids: list[str]


ExtractFn = Callable[[Path, list[str], set[str], str | None], tuple[list[dict[str, Any]], ExtractDiagnostics]]


def _dynamic_import_extract() -> ExtractFn:  # pragma: no cover - best effort
    """Load the extraction function via a controlled exec sandbox.

    Rationale: importlib spec loader proved flaky in some environments (returned a
    spec without a loader). For a repo‑local, trusted module this simplified path
    is acceptable and more reliable. Falls back to a stub if any exception occurs.
    """
    spec_path = INSTRUCTIONS_DIR / "standards_extraction.py"
    if not spec_path.exists():
        def _absent(_: Path, __: list[str], ___: set[str], today: str | None = None):  # type: ignore[unused-ignore]
            return [], {"notes": ["extraction module not present"]}
        return cast(ExtractFn, _absent)
    try:
        # Use runpy to execute the trusted repository-local extraction module without relying on
        # importlib spec loader (which was flaky in some environments). This avoids direct 'exec'.
        sandbox: dict[str, Any] = runpy.run_path(str(spec_path))  # type: ignore[assignment]
        fn = sandbox.get("extract_rules")
        if callable(fn):
            return cast(ExtractFn, fn)
        raise RuntimeError("extract_rules symbol missing or not callable")
    except Exception as exc:  # pragma: no cover - defensive boundary
        logging.warning("extraction import failed (sandbox path): %s", exc)
        msg = f"extraction unavailable: {exc}"  # capture for closure
        def _empty(_: Path, __: list[str], ___: set[str], today: str | None = None):  # type: ignore[unused-ignore]
            return [], {"notes": [msg]}
        return cast(ExtractFn, _empty)


def _invoke_extract(fn: ExtractFn, source: Source, seed_ids: set[str], today: str) -> tuple[list[dict[str, Any]], ExtractDiagnostics]:
    return fn(source.path, source.categories, seed_ids, today)


def _dedupe_extracted(extracted: list[dict[str, Any]], seed_ids: set[str]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for r in extracted:
        rid = r.get("id")
        if not rid or rid in seed_ids or rid in seen:
            continue
        seen[rid] = r
    return [seen[k] for k in sorted(seen.keys())]


def _maybe_extract_rules(
    sources: list[Source], seed_ids: set[str], enable: bool, auto_accept: bool
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not enable:
        return [], [], []
    extract_fn = _dynamic_import_extract()
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
    required_fields = {"id", "category_ids", "summary", "rationale", "severity", "applies_to", "source", "last_updated"}
    for r in rules:
        missing = required_fields - set(r.keys())
        if missing:
            raise ValueError(f"Rule {r.get('id')} missing fields: {sorted(missing)}")
        for cid in r["category_ids"]:
            if cid not in categories:
                raise ValueError(f"Rule {r['id']} references unknown category '{cid}'")


def _write_pending_file(extracted_all: list[dict[str, Any]], auto_accept: bool, extraction_diags: list[dict[str, Any]], enable_extraction: bool) -> None:
    if not (enable_extraction and not auto_accept and extracted_all):
        return
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "auto_accept": auto_accept,
        "extracted_count": len(extracted_all),
        "notes": "Pending extracted standards rules (not yet merged into main index)",
        "rules": extracted_all,
        "diagnostics": extraction_diags,
    }
    try:  # pragma: no cover - IO
        with PENDING_FILE.open("w", encoding="utf-8") as pf:
            yaml.safe_dump(payload, pf, sort_keys=False, width=100)
    except Exception as exc:  # pragma: no cover
        logging.error("failed to write pending file: %s", exc)


def _compute_rules_hash(rules: list[dict[str, Any]]) -> str:
    if not rules:
        return _build_empty_rules_hash()
    fragments = [f"{r['id']}|{r['last_updated']}|{r['severity']}" for r in sorted(rules, key=lambda x: x['id'])]
    return _compute_integrity_hash(fragments)


def _build_metadata(enable_extraction: bool, auto_accept: bool, extracted_all: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "build_script": str(Path(__file__).relative_to(ROOT)),
        "overrides_file": ".repo_studios/standards_index_overrides.yaml",
        "extraction": {
            "enabled": enable_extraction,
            "auto_accept": auto_accept,
            "extracted_count": len(extracted_all),
            "pending_file": (
                str(PENDING_FILE.relative_to(ROOT))
                if (enable_extraction and not auto_accept and extracted_all)
                else None
            ),
        },
        "notes": "Seed + optional heuristic extraction phase.",
    }


def build_index() -> dict[str, Any]:
    categories, sources = _load_categories()
    _validate_sources(categories, sources)

    rules, seed_ids = _load_seed_rules()
    enable_extraction = _env_flag("ENABLE_STANDARDS_EXTRACTION")
    auto_accept = _env_flag("AUTO_ACCEPT_EXTRACTED")
    accepted, extracted_all, extraction_diags = _maybe_extract_rules(
        sources, seed_ids, enable_extraction, auto_accept
    )
    if accepted:
        rules.extend(accepted)
    else:
        _write_pending_file(extracted_all, auto_accept, extraction_diags, enable_extraction)

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
            {"path": str(s.path.relative_to(ROOT)), "categories": s.categories} for s in sources
        ],
        "categories": {
            cid: {
                "title": c.title,
                **({"description": c.description} if c.description else {}),
                **({"tags": c.tags} if c.tags else {}),
            }
            for cid, c in sorted(categories.items(), key=lambda kv: kv[0])
        },
        "rules": rules,
        "coverage": {"source_stats": {}, "missing_sections": []},
        "metadata": _build_metadata(enable_extraction, auto_accept, extracted_all),
    }
    return index


def write_index(index: dict[str, Any]) -> None:
    # Preserve key order by constructing final dict intentionally (PyYAML >=5 preserves insertion order)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(index, f, sort_keys=False, width=100)


def main() -> int:
    try:
        index = build_index()
        write_index(index)
        rel = OUTPUT_FILE.relative_to(ROOT)
        logging.info(
            "Wrote %s (rules=%d, hash=%s)",
            rel,
            len(index['rules']),
            index['integrity_hash'][:12],
        )
        return 0
    except Exception as exc:  # pragma: no cover - coarse failure boundary
        logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(message)s")
        logging.exception("build failed: %s", exc)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
