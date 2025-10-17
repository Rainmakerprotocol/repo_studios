---
title: Standards Rule Extraction Spec
audience: [Automation, repo]
status: draft
version: 0.1.0
updated_at: 2025-09-28
---

# Standards Rule Extraction Specification

Defines deterministic heuristic pipeline converting markdown standards sources into
normalized `rule` objects prior to overrides.

## Goals

* High recall of actionable directives
* Low duplication
* Deterministic ordering & ID generation
* Clean separation between heuristic output and manual overrides

## Input Sources

Configured via `standards_categories.yaml` → iterate `sources[].path`.

## Pipeline Stages

1. Load markdown text
2. Segment into blocks (heading → lines until next heading)
3. Enumerate candidate lines (bullets, checklist entries, table rows, directive sentences)
4. Normalize & filter
5. Derive rule fields (id, summary, rationale, severity guess, applies_to)
6. Attach source ref (file + anchor from nearest heading)
7. Deduplicate (summary hash)
8. Sort & emit candidate list (pre-override)

## Candidate Detection

### Bullet / Checklist Patterns

Regex: `^[ \t]*[-*+] +(?:\[[ xX]\] +)?(.+)$` Captured text trimmed → candidate_text.

### Directive Line Patterns

Leading directive verbs (case-insensitive):
`ALWAYS|NEVER|AVOID|PREFER|USE|DO NOT|MUST|SHOULD|SHOULD NOT|KEEP|ENSURE|LIMIT|DOCUMENT`
Sentence qualifies if it starts with one of these tokens or contains a colon after directive
phrase (e.g., `Never:`).

### Table Rows

Tables scanned where header contains directive-ish column (e.g., starts with `Pattern`,
`Directive`, `Rule`). For each non-header row first cell treated as candidate_text if length ≥ 15
chars and includes a verb.

## Normalization

* Collapse multiple spaces → single space
* Strip trailing punctuation (`.;:`) for summary
* If text contains `—` or ` - ` split on first and take left for summary, remainder for rationale
  candidate
* Remove leading directive verb for rationale derivation if duplicated

## Rationale Derivation

If neighboring (next) sentence expands with causal marker (`because`, `ensures`, `so that`,
`to avoid`, `helps`) append that sentence to rationale; else rationale = candidate_text (full
original before summary trimming).

## Severity Heuristic

| Condition | Severity |
| --------- | -------- |
| Starts with NEVER / DO NOT / MUST NOT / security keywords ("secret","credential","injection") | critical |
| Starts with ALWAYS / MUST / ENSURE / AVOID | error |
| Starts with SHOULD / PREFER / LIMIT | warn |
| Else | info |

## Applies-To Guessing

Pattern mapping by keywords:

* If contains `python`, `exception`, `type`, `async`, `FastAPI` → `**/*.py`
* If contains `markdown`, `heading`, `front matter`, `docs` → `**/*.md`
* If contains both sets → `["**/*.py","**/*.md"]`

Default fallback: `["**/*"]` (may be trimmed by overrides).

## ID Generation

1. Base words: first 8 words of normalized summary (lowercased, alphanumerics + hyphen)
2. Join with hyphen → draft_id
3. Prefix with shortest category id from parent mapping (if multiple categories choose
   lexicographically) + `-` unless summary already begins with that prefix.
4. If collision: append incremental numeric suffix `-2`, `-3`, ...

Example: `Use explicit timeouts for external calls` (category python_coding) → words: use
explicit timeouts for external calls → `python_coding-use-explicit-timeouts-for-external`

## Deduplication

Candidate key: lowercased summary without stopwords (`a, an, the, to, for, of, and, or`) + file
path. If duplicate encountered, keep first (earliest in file order).

## Anchor Resolution

Heading slug algorithm:

* Lowercase heading text
* Replace spaces with `-`
* Remove characters not `[a-z0-9-]`
* Collapse multiple `-`

Nearest preceding heading yields `anchor`.

## Overrides Merge Order

1. Heuristic candidates (list)
2. Manual curated seed (if implemented separately)
3. Overrides file entries (match on id, replace or extend fields)
4. Final validation pass

## Exclusions

Reject candidate if:

* Length < 15 chars (after trim) and not severity-critical pattern
* Contains only formatting instructions (regex: `^(table|image|see )`)
* More than 65% uppercase letters (likely acronym blob) unless starts with directive verb

## Deterministic Sorting

Sort final (pre-override) by `(file, anchor, candidate_text)`; post-merge re-sort by
`(min(category_ids), id)` for output.

## Pseudo-code (Simplified)

```python
for source in sources:
    text = read(source.path)
    sections = split_by_headings(text)
    for section in sections:
        anchor = slug(section.heading)
        for line in section.lines:
            if bullet_or_checklist(line) or directive_sentence(line) or table_row_candidate(line):
                cand = normalize(extract_text(line))
                if excluded(cand):
                    continue
                summary = summarize(cand)
                rationale = derive_rationale(section, line, cand)
                severity = classify(summary)
                applies_to = guess_applies(summary, rationale)
                rid = generate_id(summary, source.categories)
                yield Candidate(rid,...)
# de-dupe, merge seeds, merge overrides, validate, sort, emit
```

## Validation Hooks (Pre-Index)

* No empty `summary`
* Severity valid
* `applies_to` non-empty
* ID regex: `^[a-z0-9]+[a-z0-9_-]*[a-z0-9]$`

## Future Enhancements

* ML-assisted confidence scoring
* Multi-language applies-to detection
* Inline ignore markers (`<!-- index:ignore -->`)

---

End of extraction spec.
