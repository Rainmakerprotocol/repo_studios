# Repo Studios Script Layout

This directory houses the active automation suite for Repo Studios. Scripts are grouped by the role they play in the data and automation pipeline so coding agents can locate the right tool quickly.

## Category Map

- `collectors/` – raw data generators that produce baseline logs, metrics, or snapshots for downstream processing.
- `processors/` – transformation layers that reshape collector outputs into normalized datasets.
- `reporters/` – presentation builders that compose multi-section reports or artifacts for humans and agents.
- `orchestrators/` – entry points that coordinate suites of collectors, processors, and reporters.
- `utilities/` – ad-hoc maintenance helpers or one-off scripts that do not feed standard pipelines.
- `docops/` – documentation maintenance scripts including standards extraction, summarization, and index refreshers.
- `inventory/` – catalog automation that keeps Repo Studios inventory schemas and views synchronized.

## Operating Notes

- Each category will ship with a local README describing expected inputs, outputs, run cadence, and ownership.
- When relocating scripts from `.repo_studios_legacy/`, record the origin and new path in `manifest/scripts_manifest.yaml` so we can audit the migration.
- Log-producing scripts should import the shared `prune_logs` helper (to be introduced) to quietly cap history to the freshest records.
- Orchestrators that previously lived in legacy Make targets will be renamed with the `studio-` prefix as part of the rewiring phase.

## Immediate TODOs

- Populate each category folder with the migrated legacy scripts and update their module headers with the new namespace.
- Author category-specific READMEs once the first script lands in each folder.
- Draft the reusable `prune_logs` helper under `utilities/` and retrofit log-heavy scripts during migration.
