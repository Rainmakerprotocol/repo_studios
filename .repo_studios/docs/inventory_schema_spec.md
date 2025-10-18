# Inventory Schema Specification

Last updated: 2025-10-17

This document defines the authoritative YAML schema for cataloging Repo Studios assets. The schema is designed for AI-first consumption while remaining understandable to human maintainers.

## 1. Record Structure

Each inventory entry is a YAML mapping with the following top-level fields:

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `id` | string | yes | Stable slug (`<category>.<name>`). Used for cross-references. |
| `name` | string | yes | Human-readable display name. |
| `path` | string | yes | Relative file or directory path within the repo. |
| `asset_kind` | enum | yes | High-level classification (see §2.1). |
| `roles` | list[string] | yes | Functional roles the asset plays (enum values in §2.2). |
| `maturity` | enum | yes | Lifecycle stage (see §2.3). |
| `introduced` | datetime | no | ISO-8601 timestamp indicating when the asset entered the repo. |
| `last_reviewed` | datetime | no | ISO-8601 timestamp of the most recent manual review. |
| `description` | string | yes | Concise explanation of the asset’s purpose. |
| `dependencies` | map | no | Nested metadata captured in §3. |
| `consumers` | list[string] | yes | Parties relying on the asset (enum in §2.4). |
| `status` | enum | yes | Operational state (`active`, `needs_review`, `archived`). |
| `governance_flags` | list[string] | no | Policy annotations (e.g., `pending_migration`, `sensitive`). |
| `artifact_type` | string | yes | File format or artifact type (`py`, `md`, `yaml`, `json`, `tsv`, `log`, etc.). |
| `related_assets` | list[string] | no | IDs of other inventory entries with direct relationships. |
| `tags` | list[string] | no | Free-form labels for filtering/search. |
| `phase_origin` | string | no | Phase or initiative that introduced the asset (e.g., `phase0`, `legacy`). |
| `source_repo` | enum | no | `repo_studios` or `repo_studios_legacy`. |
| `notes` | map | no | Additional context, decisions, or migration notes. |

## 2. Enumerations

### 2.1 Asset kind

- `document`
- `script`
- `report_artifact`
- `test`
- `config`
- `template`
- `data_sample`

### 2.2 Roles

- `orchestrator`
- `summarizer`
- `report_generator`
- `standards`
- `validator`
- `cli`
- `test_case`
- `config_provider`
- `artifact_sample`
- `playbook`

### 2.3 Maturity stages

- `incubating`
- `stable`
- `legacy`
- `deprecated`

### 2.4 Consumers

- `coding_agent`
- `human_developer`
- `ci_pipeline`
- `docs_generator`
- `external_tool`

### 2.5 Status values

- `active`
- `needs_review`
- `archived`

## 3. Dependency Block

```yaml
dependencies:
  internal_paths:
    - .repo_studios_legacy/repo_files/copilot_standards_index.yaml
  external_tools:
    - mypy
  inputs:
    - path: .repo_studios_legacy/repo_reports/health_suite/
      description: Health suite reports consumed for summary generation
```

- `internal_paths` (list[string]): other repo-relative paths the asset relies on.
- `external_tools` (list[string]): CLI tools or binaries required for execution.
- `inputs` (list[map]): structured references to datasets or directories (`path`, `description`).

## 4. Notes Block

```yaml
notes:
  context: Used during migration from legacy scripts.
  decisions:
    - Replaced hard-coded paths with configuration loader.
  blockers:
    - Pending Python 3.12 compatibility work.
```

- `context`: optional narrative background.
- `decisions`: list of recorded changes/decisions.
- `blockers`: outstanding impediments.

## 5. Example Entry

```yaml
- id: scripts.standards_index_cli
  name: Standards Index CLI
  path: .repo_studios_legacy/repo_scripts/standards_index_cli.py
  asset_kind: script
  roles: [cli, orchestrator]
  maturity: stable
  introduced: 2023-11-05T00:00:00Z
  last_reviewed: 2025-09-12T18:00:00Z
  description: CLI wrapper to query the consolidated standards index.
  dependencies:
    internal_paths: [.repo_studios_legacy/repo_files/copilot_standards_index.yaml]
    external_tools: []
    inputs: []
  consumers: [coding_agent, ci_pipeline]
  status: needs_review
  governance_flags: [pending_migration]
  artifact_type: py
  related_assets: [docs.standards_index_schema, scripts.standards_index_diff]
  tags: [standards, inventory, phase1]
  phase_origin: legacy
  source_repo: repo_studios_legacy
  notes:
    context: Adapt paths after migration to .repo_studios/scripts.
```

## 6. Validation Requirements

- Every record must include required fields; missing enumerations should cause validation failure.
- `id` values must be unique and lowercase.
- `path` must reference an existing file/directory when validation runs.
- Date fields must conform to ISO-8601 with timezone indicators.
- `roles`, `maturity`, `consumers`, and `status` must draw from the enumerations above.
- Optional fields may be omitted entirely rather than left blank.

## 7. Future Extensions

- Execution metadata (frequency, scheduling) once automation requirements are clearer.
- Ownership metadata (`maintainer`, `reviewer`) for governance tracking.
- Auto-generated backlinks from reports/tests to the scripts that produced them.

Refer to `_repo_studios/inventory_schema/enums.yaml` for machine-readable enum definitions and to `inventory_entry_template.yaml` for authoring new records.
