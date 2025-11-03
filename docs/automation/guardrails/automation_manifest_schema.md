# Automation Manifest Schema

**Status:** Draft (2025-11-03)

## Purpose

Define the JSON structure for `manifest.json` produced during Phase 4 automation rehearsals. The manifest pairs with the rollback bundle and metrics summary so operators can audit run context, guardrail compliance, and planned file changes.

## Schema Overview

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | string | Yes | Semantic version of the manifest schema (`1.0` initial release). |
| `run_id` | string | Yes | Identifier for the automation run (reuse orchestrator slug or timestamp). |
| `timestamp` | string | Yes | ISO-8601 timestamp marking when the manifest was generated (UTC recommended). |
| `targets` | array[string] | Yes | Slugged targets processed during the run. |
| `baseline_sha` | string | Yes | Git commit SHA used as the automation baseline. |
| `dry_run` | boolean | Yes | Indicates whether the run emitted artifacts only (`true`) or applied changes. |
| `operator` | string | No | Optional operator handle responsible for the run. |
| `notes` | string | No | Free-form notes captured by the operator (defaults to empty string). |
| `files` | object | Yes | Grouped file lists keyed by status (`updated`, `skipped`, `conflicted`). Each entry contains `path` and optional `duplicate_groups`. |
| `guardrails` | object | No | Snapshot of guardrail configuration (`max_files_per_run`, `files_considered`, `override_applied`, plus file paths and metadata when available). |
| `metrics_summary_path` | string | Yes | Relative path to the accompanying `metrics_summary.json` written for the same run. |
| `metrics_summary` | object | Yes | Embedded metrics payload following `docs/automation/metrics/metrics_summary_schema.md`. |

### File Entry Structure

Each element in `files.<status>` uses:

```json
{
  "path": "src/module_a.py",
  "duplicate_groups": ["dup-1", "dup-3"]
}
```

- Entries default to an empty `duplicate_groups` array when omitted.
- `updated` records represent files expected to change; `conflicted` capture files that were skipped due to conflicts after pre-flight analysis; `skipped` documents untouched files that remain under review.

### Guardrail Snapshot Structure

```json
{
  "max_files_per_run": 10,
  "files_considered": 3,
  "override_applied": false,
  "config_path": "docs/automation/guardrails/automation_config.yaml",
  "allow_list_source": "docs/automation/guardrails/allowed_targets.yaml",
  "metadata": {"version": "1"}
}
```

- `files_considered` counts every entry across `updated`, `skipped`, and `conflicted` to mirror manifest scope.
- `override_applied` reflects the CLI flag used during the run; include even during dry runs to keep the audit trail complete.
- `metadata` mirrors arbitrary key/value pairs captured from the guardrail configuration header.

## Validation Rules

1. Ensure `files.updated` + `files.conflicted` aligns with `metrics_summary.files_changed`; the CLI enforces parity before writing artifacts.
2. Populate `metrics_summary_path` with the relative filename used in the run directory so bundle consumers can resolve the summary without additional context.
3. Always embed the metrics summary payload rather than linking externally to keep rollback bundles self-contained.
4. Store the manifest alongside the rollback bundle and mirror `latest_automation_manifest.json` at the output root for quick inspection.
5. Bump `schema_version` when adding or renaming top-level fields; append new optional fields under nested objects when possible to preserve backwards compatibility.
