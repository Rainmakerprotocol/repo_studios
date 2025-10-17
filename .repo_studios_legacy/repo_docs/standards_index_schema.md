---
title: Standards Index Schema Specification
audience: [Developers, repo, Automation]
status: draft
version: 0.1.0
updated_at: 2025-09-28
---

# Standards Index Schema Specification

This document defines the schema for `repo_standards_index.yaml` consumed by automation and agent workflows.

## Top-Level Structure

| Key | Type | Required | Description |
| --- | ---- | -------- | ----------- |
| schema_version | int | yes | Structural version (increments on breaking changes) |
| version | string | yes | Content revision (e.g. 2025.09.0) |
| generated_at | string (ISO8601 UTC) | yes | Build timestamp |
| offline | bool | yes | Must be `true` (asserts no remote fetch) |
| integrity_hash | string | yes | sha256 over deterministic subset |
| sources | list[source] | yes | Source markdown files feeding rules |
| categories | map[string]category | yes | Category metadata |
| rules | list[rule] | yes | Flattened list of normalized rules |
| coverage | coverage | no | Stats & gaps |
| metadata | metadata | no | Build script & notes |

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
| summary | string | yes | <=100 chars concise directive |
| rationale | string | yes | Why rule matters |
| severity | enum(info,warn,error,critical) | yes | Governs enforcement priority |
| applies_to | list[string] | yes | Glob/globs (e.g. `**/*.py`) |
| examples | examples | no | Good/bad illustration |
| source | source_ref | yes | Original markdown anchor |
| deprecated | bool | no | Default false |
| superseded_by | string | conditional | Required if deprecated true |
| enforcement_hint | string | no | Optional automation guidance |
| last_updated | string (YYYY-MM-DD) | yes | Date of last meaningful change |

## Object: examples
| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| bad | string | conditional | Provide when illustrating anti-pattern |
| good | string | conditional | Provide when offering remediation |

At least one of `bad` or `good` must be present if `examples` exists.

## Object: source_ref
| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| file | string | yes | Repo-relative origin file |
| anchor | string | yes | Heading or slug reference |

## Object: coverage
| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| source_stats | map[string]coverage_entry | yes | Per source counts |
| missing_sections | list[string] | no | Unmapped headings/anchors |

### coverage_entry
| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| total_rules | int | yes | Count derived from this source |
| last_scanned | string (ISO8601 UTC) | yes | Scan timestamp |

## Object: metadata
| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| build_script | string | yes | Path to builder script |
| overrides_file | string | no | Path if present |
| notes | string | no | Free-form commentary |

## Integrity Hash Algorithm
1. Collect for each rule: `id|last_updated|severity` (sorted by `id`)
2. Join with `\n`
3. sha256 hex digest → `integrity_hash`

Changing rationale, examples, or enforcement hint does not change the hash; structural / severity / date changes do.

## Deterministic Ordering
Rules sorted lexicographically by `(min(category_ids), id)`; categories sorted by key.

## Validation Rules
- Rule IDs unique
- All referenced categories exist
- Deprecated rules must have `superseded_by` pointing to existing id (unless future id reserved with `TODO:` prefix) 
- `applies_to` entries must not be empty strings
- Severity must be one of enumerated values

## Backward Compatibility
Increment `schema_version` only on breaking changes (field rename/removal). Additive fields do not bump it.

## Future Reserved Fields
- rule: `confidence` (probabilistic extraction confidence)
- top-level: `extensions` (namespaced vendor metadata)

---
End of schema spec.
