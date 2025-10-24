# extract_standards_rules.py

**Last updated:** 2025-10-23

## Purpose

`extract_standards_rules.py` parses curated markdown sources for guardrail rules that enrich the standards index build. It gathers candidate rules from dedicated HTML marker blocks and heading conventions, normalizes their metadata (severity, categories, applies-to globs), and returns a `(rules, diagnostics)` tuple that the `generate_standards_index` producer ingests during extraction.

The helper is dependency-light (stdlib only) so it can run inside constrained CI sandboxes and third-party agents without extra wheels.

## Supported patterns

### Marker blocks

```markdown
<!-- standards:rule
id: unique-rule-id
categories: markdown docs
severity: warn
applies_to: docs/**/*.md docs/**/*.markdown
summary: One-line summary
rationale: Why this matters
-->
<!-- /standards:rule -->
```

Required keys: `id`, `categories`, `severity`, `applies_to`, `summary`, `rationale`. Optional keys are ignored. Multi-value fields such as `categories` or `applies_to` may be space- or comma-delimited. The extractor derives

- `category_ids`: list from the explicit `categories` value; falls back to the per-source category list when omitted.
- `applies_to`: array of glob patterns.
- `severity`: normalized to one of `info`, `warn`, `error`, `critical` (`warning`, `err`, `fatal`, `blocker`, etc. fold into these canonical levels).
- `source`: `{"file": <repo-relative path>, "anchor": <rule id>}`
- `last_updated`: ISO date provided by the caller (defaults to `date.today()`).

Marker blocks whose severity cannot be normalized are skipped and surfaced via diagnostics.

### Heading rules

```markdown
### Rule: Descriptive Title
- Summary: Short summary sentence
- Rationale: Why the rule exists
- Severity: error
- Applies-To: docs/**/*.md, docs/**/*.markdown
- Categories: markdown docs
```

The extractor slugifies the heading to produce an `id`. Bullet metadata is mandatory; missing fields cause the block to be ignored. Categories default to the associated source categories when the bullet is absent. Severity normalization and diagnostics mirror marker blocks.

## Invocation

The module exposes a single public function:

```python
from pathlib import Path
from .extract_standards_rules import extract_rules

rules, diagnostics = extract_rules(
    path=Path("docs/standards/global/std-global-markdown-authoring.md"),
    categories=["markdown"],
    existing_ids={"STD-001"},
)
```

- `path`: absolute or relative path to the markdown file.
- `categories`: default category identifiers supplied by the caller for the source document.
- `existing_ids`: known rule identifiers (seed + previously extracted) used to flag conflicts.
- `today`: optional ISO string (defaults to `date.today().isoformat()`).

The return value is:

- `rules`: list of dicts conforming to the standards index schema (`id`, `category_ids`, `summary`, `rationale`, `severity`, `applies_to`, `source`, `last_updated`). Duplicate IDs within a single file are dropped after the first occurrence.
- `diagnostics`: metadata for health reporting:
  - `rules_found`
  - `duplicate_ids`
  - `skipped_conflicts`
  - `invalid_severity_rules`
  - `notes` (marker/heading counts)

## Diagnostics and error handling

- Unknown severities are ignored and recorded under `invalid_severity_rules` so downstream producers can alert instead of failing the entire build.
- Marker blocks missing required keys are skipped silently today (future TODO: emit explicit warnings).
- Repository-relative source paths are computed defensively; when the repo layout is unexpected the extractor falls back to the filename to avoid hard failures.

## Testing

`pytest .repo_studios/tests/tests_producers/test_extract_standards_rules.py`

The suite covers mixed marker/heading extraction, severity normalization, multi-glob handling, and invalid severity diagnostics.

## Integration notes

- The `generate_standards_index` producer runs this module via `runpy.run_path`, so maintainers should avoid top-level side effects.
- Keep the dependency surface to stdlib only; downstream environments expect zero third-party imports here.
- Add new severity aliases to `_SEVERITY_MAP` whenever documentation adopts alternate terminology.
- When extending supported patterns, propagate diagnostic fields so artifact consumers remain in sync.
