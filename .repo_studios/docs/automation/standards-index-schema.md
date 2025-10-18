---
title: Standards Index Schema Specification
audience:
  - coding_agent
  - automation_engineer
owners:
  - repo_studios_ai
status: draft
version: 0.2.0
updated: 2025-10-18
summary: >-
  Schema contract for `repo_standards_index.yaml`, detailing the deterministic structure consumed by Repo Studios automation and agents.
tags:
  - standards
  - schema
  - automation
legacy_source: .repo_studios_legacy/repo_docs/standards_index_schema.md
---

<!-- markdownlint-disable MD025 -->
# Standards Index Schema Specification

This specification defines the structure of `repo_standards_index.yaml`, which aggregates normalized rule objects for Repo Studios automation and agent workflows.

---

## Top-Level Structure

| Key | Type | Required | Description |
| --- | ---- | -------- | ----------- |
| schema_version | int | yes | Structural version (increments on breaking changes) |
| version | string | yes | Content revision (for example, `2025.09.0`) |
| generated_at | string (ISO8601 UTC) | yes | Build timestamp |
| offline | bool | yes | Must be `true` (asserts no remote fetch) |
| integrity_hash | string | yes | `sha256` over deterministic subset |
| sources | list[source] | yes | Source Markdown files feeding rules |
| categories | map[string]category | yes | Category metadata |
| rules | list[rule] | yes | Flattened list of normalized rules |
| coverage | coverage | no | Stats and gap tracking |
| metadata | metadata | no | Build script and notes |

---

## Object: source

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| path | string | yes | Repo-relative path |
| categories | list[string] | yes | Category IDs referencing `categories` |

## Object: category

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| title | string | yes | Human title |
| description | string | no | Optional detail |
| tags | list[string] | no | Free-form labels |

## Object: rule

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| id | string (kebab-case) | yes | Unique global rule id |
| category_ids | list[string] | yes | Non-empty subset of category keys |
| summary | string | yes | ≤100 char directive summary |
| rationale | string | yes | Why the rule matters |
| severity | enum(info,warn,error,critical) | yes | Enforcement priority |
| applies_to | list[string] | yes | Glob(s), e.g. `**/*.py` |
| examples | examples | no | Good/bad illustration |
| source | source_ref | yes | Original Markdown anchor |
| deprecated | bool | no | Default `false` |
| superseded_by | string | conditional | Required if `deprecated` is `true` |
| enforcement_hint | string | no | Optional automation guidance |
| last_updated | string (YYYY-MM-DD) | yes | Date of last meaningful change |

## Object: examples

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| bad | string | conditional | Provide when illustrating anti-pattern |
| good | string | conditional | Provide when offering remediation |

At least one of `bad` or `good` must exist when `examples` is supplied.

## Object: source_ref

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| file | string | yes | Repo-relative origin file |
| anchor | string | yes | Heading or slug reference |

---

## Object: coverage

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| source_stats | map[string]coverage_entry | yes | Per-source rule counts |
| missing_sections | list[string] | no | Unmapped headings/anchors |

### coverage_entry

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| total_rules | int | yes | Count derived from this source |
| last_scanned | string (ISO8601 UTC) | yes | Scan timestamp |

---

## Object: metadata

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| build_script | string | yes | Path to the builder script |
| overrides_file | string | no | Path if overrides apply |
| notes | string | no | Free-form commentary |

---

## Integrity Hash Algorithm

1. Collect for each rule: `id|last_updated|severity` (sorted by `id`).
2. Join entries with `\n`.
3. Compute the `sha256` hex digest and assign to `integrity_hash`.

Changes to rationale, examples, or enforcement hints do **not** alter the hash; structural, severity, or date changes do.

## Deterministic Ordering

- Rules sorted lexicographically by `(min(category_ids), id)`.
- Categories sorted by key.

## Validation Rules

- Rule IDs must be unique.
- All referenced categories must exist.
- Deprecated rules require `superseded_by` pointing to an existing id (or reserved `TODO:` id).
- `applies_to` entries cannot be empty strings.
- Severity must match the enumerated values.

## Backward Compatibility

- Increment `schema_version` only for breaking changes (field rename/removal).
- Additive fields do **not** bump `schema_version`.

## Future Reserved Fields

- rule: `confidence` (probabilistic extraction confidence).
- top-level: `extensions` (namespaced vendor metadata).

---

End of specification.

<!-- markdownlint-enable MD025 -->
