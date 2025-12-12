# Report Naming Standards

This document defines the uniform naming scheme for all artifacts stored under
`.repo_studios/command_center/reports/`. New automation, orchestrators, and
helpers MUST emit bundles that follow this structure. Legacy directories remain
in place until the migration plan retires or reshapes them, but they are treated
as grandfathered exceptions and should not expand further.

## Core Principle: Positional Encoding

**The filesystem structure IS a self-documenting schema.** Each position in the
path hierarchy encodes specific metadata, enabling scripts and AI agents to
classify reports by path parsing alone—no file I/O required.

**Path Contract:**
```
<reports_root>/<viewer_slug>/<topic>/<timestamp>/<artifact>
               └─Position 1─┘ └Pos 2┘ └─Pos 3──┘ └─Pos 4─┘
```

- **Position 1 (Viewer)**: Consumer context—who/what uses this data
- **Position 2 (Topic)**: Subject/scope—what aspect of the system
- **Position 3 (Timestamp)**: Temporal identifier—when it was generated (UTC)
- **Position 4 (Artifact)**: Content role—what the file contains

This positional encoding reduces cognitive load for all consumers (humans, scripts,
AI agents) and mirrors the database schema for seamless dual-write integration.

## Naming Convention Index

Every artifact path is composed of exactly four positional segments:

| Segment | Purpose | Format | Example |
| --- | --- | --- | --- |
| `<viewer_slug>` | Primary viewer tab or surface | kebab/underscore lowercase slug | `healthview` |
| `<topic>` | Topic or orchestration scope | kebab/underscore lowercase slug | `test_execution_telemetry` |
| `<timestamp>` | UTC run identifier | `YYYYMMDD-HHMM` | `20251129-2102` |
| `<artifact_role>.<ext>` | Artifact role and file extension | see table below | `manifest.json` |

Example manifest location:

```
.repo_studios/command_center/reports/healthview/test_execution_telemetry/20251129-2102/manifest.json
```

Additional directories beneath the timestamp are not allowed. The timestamp is
removed from filenames; the directory hierarchy captures run identity.

**Timestamp Format Contract:** YYYYMMDD-HHMM (UTC, 24-hour, minute precision)

- Sortable lexicographically (string sort = chronological sort)
- Human-readable (no Unix timestamps)
- No special characters requiring escaping
- Consistent 13-character length

**Why positional encoding matters:**
- Zero file I/O to determine viewer, topic, or timestamp

- Glob patterns become semantic queries: `healthview/*/20251211-*`
- Database columns mirror path positions for seamless integration
- Scripts parse paths uniformly via centralized helpers

## Artifact Role Registry

| Artifact Role | Description | Allowed Extensions |
| --- | --- | --- |
| `manifest` | Machine-readable manifest that enumerates bundle contents | `.json` |
| `summary` | Human-friendly Markdown summary | `.md`, `.json` |
| `matrix` | Duplicate/coverage matrices or tabular outputs | `.json`, `.csv`, `.tsv` |
| `telemetry` | Timing, sizing, or runtime measurements | `.json` |
| `report` | Narrative report distinct from summary | `.md`, `.json` |
| `metrics` | Aggregated metric payloads | `.json`, `.md` |

Future roles should be appended here before adoption so the audit tooling can be
kept in sync.

## Viewer Slug Registry

| Viewer Slug | Surface | Purpose |
| --- | --- | --- |
| `healthview` | Health monitoring dashboard | System wellness for autonomous diagnostics |
| `commandview` | Command Center operations | Developer-facing operational views |
| `rawview` | Raw diagnostic captures | Unprocessed data for debugging |
| `jarvis` | Agentic operations console | Agent-to-agent coordination (future) |
| `vscode` | VS Code embedded viewer | IDE integration (future) |

**Viewer Selection Logic:** Choose based on PURPOSE (who consumes), not TIER
(who produces). A producer can emit to multiple viewers if different consumers
need different perspectives on the same data.

Additional slugs must remain lowercase ASCII and be registered here before
usage.

## Grandfathered Artifacts

Existing directories such as `index_scan/`, `duplicates_scan/`, and any files or
folders containing `latest` prefixes are considered grandfathered until
explicitly migrated. No new automation should extend those paths. The audit
utility flags these items so we can track progress toward full compliance.

## Audit Utility Specification

Use `.repo_studios/command_center/scripts/utilities/reports_naming_audit.py` to
measure conformance. Key CLI options:

- `--reports-root`: scan root (defaults to `.repo_studios/command_center/reports`).
- `--output-dir`: destination for audit artifacts (JSON + Markdown). Defaults to
  `<reports-root>/reports_naming_audit/<timestamp>`.
- `--json-output` / `--markdown-output`: override individual output paths.
- `--artifact-roles`: custom artifact filenames when extending the registry.
- `--allowed-viewers`: restrict acceptable viewer slugs; defaults to the
  registry table above.
- `--ignore-prefix`: skip legacy prefixes (can be passed multiple times).
- `--fail-threshold`: maximum allowed violations before the process exits with
  status 1 (default: 0).
- `--log-level`: standard logging verbosity control.

Outputs include:

- `summary.json`: machine-readable counts, issue breakdowns, and `latest`
  alias references.
- `summary.md`: human-readable report suitable for viewer ingestion.

## Compliance Expectations

- New artifacts MUST adhere to the schema immediately.
- Helpers such as `write_report_artifacts` will be updated to emit the approved
  layout; custom scripts should follow the same structure.
- `latest_*` aliases are deprecated. Remove them as orchestrators, producers,
  consumers, and summarizers are refreshed.
- Audit runs are wired into documentation and reporting orchestrators. Violations
  over the configured threshold block the pipeline until resolved or deliberately
  grandfathered via `--ignore-prefix`.

## Change Management

- Update this document whenever viewer slugs or artifact roles are added.
- Reference this document in onboarding, README pointers, and automation plans
  so contributors and agents align on the canonical structure.
- Migration status is tracked via the audit summaries and the orchestrator
  implementation plan.
