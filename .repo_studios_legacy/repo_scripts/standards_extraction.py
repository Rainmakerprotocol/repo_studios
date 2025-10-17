"""Heuristic standards extraction (Phase v0)

Parses structured marker blocks and simple heading-based rule patterns from
Markdown source documents to propose standards rules.

Supported patterns:
1. Marker block delimited by HTML comments:

    <!-- standards:rule
    id: example-id
    categories: markdown
    severity: warn
    applies_to: **/*.md
    summary: One line summary
    rationale: Longer rationale sentence.
    -->
    <!-- /standards:rule -->

   All key/value pairs are single-line. `categories` is a space or comma
   separated list. Required keys: id, categories, severity, applies_to,
   summary, rationale.

2. Heading pattern:

    ### Rule: Descriptive Title
    - Summary: Short summary sentence
    - Rationale: Explanation text
    - Severity: warn|error|info|critical
    - Applies-To: **/*.md

   The rule id is a slugified form of the title (lowercase, hyphenated). The
   category_ids derive from the `categories` parameter passed into
   `extract_rules` (the build script provides per‑file categories). All bullets
   must be present for a heading rule to be accepted.

Return format matches expectations of the build pipeline:
(list[rules], diagnostics_dict)

Each rule dict MUST contain the schema-required fields validated by the build
script: id, category_ids, summary, rationale, severity, applies_to, source,
last_updated.

This module is intentionally dependency‑light (only stdlib) for portability in
restricted CI sandboxes.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
_slug_re = re.compile(r"[^a-z0-9]+")
_heading_rule_re = re.compile(r"^#{3}\s+Rule:\s+(?P<title>.+?)\s*$", re.IGNORECASE)
_bullet_kv_re = re.compile(r"^-\s+(?P<key>[A-Za-z-]+):\s*(?P<value>.+?)\s*$")


@dataclass
class ParsedRule:
    id: str
    category_ids: list[str]
    summary: str
    rationale: str
    severity: str
    applies_to: list[str]
    source_file: str
    anchor: str
    last_updated: str

    def to_dict(self) -> dict[str, Any]:  # noqa: D401 - simple transformer
        return {
            "id": self.id,
            "category_ids": self.category_ids,
            "summary": self.summary,
            "rationale": self.rationale,
            "severity": self.severity,
            "applies_to": self.applies_to,
            "source": {"file": self.source_file, "anchor": self.anchor},
            "last_updated": self.last_updated,
        }


# ---------------------------------------------------------------------------
# Public extraction function
# ---------------------------------------------------------------------------

def extract_rules(
    path: Path,
    categories: list[str],
    existing_ids: set[str],
    today: str | None = None,
):  # noqa: D401 - documented in module docstring
    text = path.read_text(encoding="utf-8")
    rel_file = _relative_to_repo_root(path)
    today_str = today or date.today().isoformat()

    marker_rules, marker_dupes, marker_conflicts = _extract_marker_blocks(
        text, categories, existing_ids, rel_file, today_str
    )

    heading_rules, heading_conflicts = _extract_heading_rules(
        text, categories, existing_ids | {r.id for r in marker_rules}, rel_file, today_str
    )

    # Combine, avoiding duplicate ids
    combined: dict[str, ParsedRule] = {r.id: r for r in marker_rules}
    for r in heading_rules:
        if r.id not in combined:
            combined[r.id] = r

    accepted_rules = [combined[k] for k in sorted(combined.keys())]

    diagnostics = {
        "rules_found": len(accepted_rules),
        "skipped_conflicts": sorted(marker_conflicts | heading_conflicts),
        "duplicate_ids": sorted(marker_dupes),
        "notes": [
            f"marker_blocks={len(marker_rules)}",
            f"heading_rules={len(heading_rules)}",
        ],
    }

    return [r.to_dict() for r in accepted_rules], diagnostics


# ---------------------------------------------------------------------------
# Marker block extraction
# ---------------------------------------------------------------------------

def _extract_marker_blocks(
    text: str,
    categories: list[str],
    existing_ids: set[str],
    rel_file: str,
    today: str,
) -> tuple[list[ParsedRule], set[str], set[str]]:
    rules: list[ParsedRule] = []
    duplicates: set[str] = set()
    conflicts: set[str] = set()

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("<!-- standards:rule"):
            block_lines: list[str] = []
            i += 1
            # Collect until closing delimiter or EOF
            while i < len(lines) and "<!-- /standards:rule" not in lines[i]:
                block_lines.append(lines[i])
                i += 1
            # Skip closing line if present
            if i < len(lines):
                i += 1
            meta = _parse_simple_kv(block_lines)
            # Validate minimal required keys
            required = {"id", "categories", "severity", "applies_to", "summary", "rationale"}
            if not required.issubset(meta.keys()):
                # Ignore silently (could add error note in future)
                continue
            rid = meta["id"].strip()
            if rid in existing_ids:
                conflicts.add(rid)
                continue
            if any(r.id == rid for r in rules):
                duplicates.add(rid)
                continue
            cat_ids = _split_multi(meta["categories"]) if meta.get("categories") else categories
            applies = [meta["applies_to"].strip()]
            rule = ParsedRule(
                id=rid,
                category_ids=cat_ids or categories,
                summary=meta["summary"].strip(),
                rationale=meta["rationale"].strip(),
                severity=meta["severity"].strip().lower(),
                applies_to=applies,
                source_file=rel_file,
                anchor=_anchor_from_id(rid),
                last_updated=today,
            )
            rules.append(rule)
        else:
            i += 1
    return rules, duplicates, conflicts


# ---------------------------------------------------------------------------
# Heading rule extraction
# ---------------------------------------------------------------------------

def _extract_heading_rules(
    text: str,
    categories: list[str],
    existing_ids: set[str],
    rel_file: str,
    today: str,
) -> tuple[list[ParsedRule], set[str]]:
    rules: list[ParsedRule] = []
    conflicts: set[str] = set()
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = _heading_rule_re.match(lines[i])
        if not match:
            i += 1
            continue
        title = match.group("title").strip()
        # Collect bullet metadata until blank line or next heading
        i += 1
        bullets: dict[str, str] = {}
        while i < len(lines):
            raw = lines[i].strip()
            if not raw:
                break
            if raw.startswith("### "):
                break
            bmatch = _bullet_kv_re.match(raw)
            if bmatch:
                key = bmatch.group("key").lower()
                bullets[key] = bmatch.group("value").strip()
            i += 1
        # Validate required bullet fields
        bullet_map = {
            "summary": bullets.get("summary"),
            "rationale": bullets.get("rationale"),
            "severity": bullets.get("severity"),
            "applies-to": bullets.get("applies-to"),
        }
        if all(bullet_map.values()):
            rid = _slugify(title)
            if rid in existing_ids:
                conflicts.add(rid)
            else:
                rules.append(
                    ParsedRule(
                        id=rid,
                        category_ids=categories,
                        summary=bullet_map["summary"],
                        rationale=bullet_map["rationale"],
                        severity=bullet_map["severity"].lower(),
                        applies_to=[bullet_map["applies-to"]],
                        source_file=rel_file,
                        anchor=_anchor_from_id(rid),
                        last_updated=today,
                    )
                )
        # Continue scanning after bullet section
        i += 1
    return rules, conflicts


# ---------------------------------------------------------------------------
# Helper parsing functions
# ---------------------------------------------------------------------------

def _split_multi(raw: str) -> list[str]:
    if "," in raw:
        parts = [p.strip() for p in raw.split(",") if p.strip()]
    else:
        parts = [p.strip() for p in raw.split() if p.strip()]
    return parts


def _parse_simple_kv(lines: Iterable[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    for ln in lines:
        stripped = ln.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, val = stripped.split(":", 1)
        meta[key.strip().lower()] = val.strip()
    return meta


def _slugify(title: str) -> str:
    title = title.lower()
    title = _slug_re.sub("-", title).strip("-")
    return re.sub(r"-+", "-", title)


def _anchor_from_id(rid: str) -> str:
    return rid


def _relative_to_repo_root(path: Path) -> str:
    # Expect repo root two levels up: .repo_studios/standards_extraction.py -> repo root parent
    # Safe fallback to basename if unexpected layout.
    try:
        root = Path(__file__).resolve().parent.parent
        return str(path.resolve().relative_to(root))
    except Exception:  # pragma: no cover - defensive
        return path.name


__all__ = ["extract_rules"]
