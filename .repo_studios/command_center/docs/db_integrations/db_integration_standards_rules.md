# DB Integration: Standards Rules Extractor

## Script Identity

- **Script**: `extract_standards_rules.py`
- **Path**: `.repo_studios/scripts/producers/extract_standards_rules.py`
- **Category**: Producer (heuristic extraction)
- **Planned Stage**: 6.2

## Purpose

Heuristic standards extraction (Phase v0). Parses structured marker blocks and simple heading-based rule patterns from Markdown source documents to propose standards rules.

## Supported Patterns

### 1. Marker Block Pattern

```html
<!-- standards:rule
id: example-id
categories: markdown
severity: warn
applies_to: **/*.md
summary: One line summary
rationale: Longer rationale sentence.
-->
<!-- /standards:rule -->
```

Required keys: `id`, `categories`, `severity`, `applies_to`, `summary`, `rationale`

### 2. Heading Pattern

```markdown
### Rule: Descriptive Title
- Summary: Short summary sentence
- Rationale: Explanation text
- Severity: warn|error|info|critical
- Applies-To: **/*.md
```

Rule ID is slugified from title. All bullets must be present.

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Source markdown files | Directory | Markdown documents to scan |
| Categories parameter | Function | Per-file categories from build script |

### Outputs

Returns tuple: `(list[rules], diagnostics_dict)`

Each rule dict contains schema-required fields:
- `id`
- `category_ids`
- `summary`
- `rationale`
- `severity`
- `applies_to`
- `source` (file and anchor)
- `last_updated`

## ParsedRule Dataclass

```python
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
```

## Design Notes

- Intentionally dependency-light (stdlib only) for CI sandbox portability
- Return format matches build pipeline expectations
- Validates against schema-required fields

## Dependencies

- None (stdlib only)

## Notes

- Producer for heuristic standards extraction
- Planned for Stage 6.2 (not yet integrated into orchestrator)
- Feeds into standards index build pipeline
