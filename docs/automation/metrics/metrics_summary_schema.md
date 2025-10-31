# Automation Metrics Summary Schema

**Status:** Draft (2025-10-31)

## Purpose

Define the JSON payload emitted alongside Phase 4 automation manifests so operators and reporting jobs can reason about impact, runtime, and test coverage in a consistent format.

## Schema Overview

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | string | Yes | Semantic version of the schema (start at `1.0`). Bump on breaking layout changes. |
| `run_id` | string | Yes | ISO-8601-like identifier (reuse run timestamp slug). |
| `targets` | array[string] | Yes | Slugged targets processed during the run. |
| `lines_touched` | integer | Yes | Total lines modified across all files (matches manifest aggregate). |
| `files_changed` | integer | Yes | Count of unique files modified (matches manifest aggregate). |
| `duplicate_groups_resolved` | integer | Yes | Number of duplicate groups addressed in this run. |
| `runtime_seconds` | integer | Yes | Wall-clock runtime for the automation step (in seconds). |
| `tests_executed` | object | Yes | Map of test suite identifiers to status/duration metadata (see below). |
| `notes` | string | No | Optional remarks for operators (e.g., "Dry-run rehearsal" or override rationale). |

### `tests_executed` structure

Each entry uses the test suite name as the key, mapping to:

```json
{
  "status": "passed" | "failed" | "skipped",
  "duration_seconds": 155,
  "artifacts": [".repo_studios/command_center/reports/.../pytest_results.json"]
}
```

At minimum include `library_integration` and `producer_suite`. Additional suites (e.g., automation smoke tests) may be appended.

## Validation Rules

1. `lines_touched` and `files_changed` must reconcile with the manifest totals prior to writing the summary. Fail fast if any mismatch is detected.
2. Ensure `runtime_seconds` is non-negative and recorded even for dry runs.
3. When `notes` is omitted, emit an empty string to keep the schema stable.
4. Store the JSON alongside `manifest.json` and the rollback bundle; reference the path in the automation log header for discoverability.
5. Version the schema via the `schema_version` field and update this document when adding or deprecating fields.
