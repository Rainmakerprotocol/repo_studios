# generate_code_doc_churn_report Planning Notes

## Objective

- Surface source paths with recent churn that lack matching documentation updates so editors can
  target missing change logs, upgrade guides, or doc refreshes.
- Produce structured artifacts (JSON + Markdown + TSV) that capture the discrepancy, including git
  metadata for reproducibility.
- Feed downstream consumers/aggregators (for example `aggregate_docs_health_signals.py`) that
  combine churn, anchor health, and undocumented logic warnings.

## Implementation Status (2025-11-25)

- ✅ Producer implementation landed at `.repo_studios/scripts/producers/generate_code_doc_churn_report.py`
  with retention, markdownlint exemptions, doc/anchor enrichment, and structured artifacts.
- ✅ Pytest coverage in `.repo_studios/tests/tests_producers/test_generate_code_doc_churn_report.py`
  exercises churn-without-docs, churn-with-docs, and allowlist flows using temporary git repos.
- ✅ Automation doc published at `.repo_studios/docs/automation/generate_code_doc_churn_report.md`
  summarizing inputs, outputs, lint exceptions, and usage.
- ✅ Script catalog updated (`script_inventory_architecture.md`) to reflect remediation completion.
- 🔄 Follow-ups: consider CI wiring for the new Make target, wire aggregator
  (`aggregate_docs_health_signals.py`) now that the undocumented-logic producer is live, and
  monitor doc-index schema changes that may require enrichment tweaks.

## Primary Inputs

- Git history for a configurable window (default 14 days) scoped to tracked files (`git log --name-status`).
- Documentation inventory from `generate_doc_index.py` (owners, canonical doc paths) for cross-referencing.
- Anchor inventory (`generate_anchor_inventory.py`) to verify anchor coverage as contextual metadata.
- Optional allowlist of repos or paths that are intentionally doc-less.

## Proposed CLI Interface

```shell
python -m .repo_studios.scripts.producers.generate_code_doc_churn_report \
  --repo-root . \
  --git-window "14 days" \
  --doc-index .repo_studios/reports/producer_reports/doc_index/latest_doc_index.json \
  --anchor-inventory .repo_studios/reports/producer_reports/healthview/anchor_inventory \
  --output-dir .repo_studios/reports/producer_reports/code_doc_churn_reports \
  --artifacts-to-keep 5 \
  --log-level INFO
```

## Artifact Plan

- Timestamped directory `code_doc_churn-YYYY-MM-DD_HHMM/` containing:
  - `report.json`: structured payload with git stats, flagged files, doc matches, suggested owners.
  - `report.md`: prioritized Markdown brief (top churn-without-doc directories, affected owners).
  - `churn.tsv`: tabular view for quick spreadsheet import.
  - `bundle_summary.json`: counts for orchestration health checks.
- Latest pointers: `latest_report.json`, `latest_report.md`, `latest_churn.tsv`, `latest_bundle_summary.json`.
- Retention default: 5 runs, configurable via `--artifacts-to-keep`.

## Detection Heuristics

1. Collect commit list within the git window (optionally filtered by branch/tag).
1. Separate code-touching paths (Python/TypeScript/CSS/etc.) from documentation paths (`docs/`,
  `.repo_studios/docs/`, `README.md` siblings).
1. Group by logical module (for example, top-level package directory) and accumulate churn metrics
  (commits, authors, LOC delta via `git diff --stat`).
1. Determine whether each module recorded doc edits in the same window:
   - Direct doc file touches under `docs/`.
   - Markdown/MDX updates in the module directory.
   - Updates flagged in `doc_index` (timestamp comparison) if available.
1. Flag modules lacking doc edits; enrich with owner metadata (from doc index) and anchor stats
  (from anchor inventory) to guide remediation.
1. Allow manual allowlist (CLI `--doc-allowlist` file) to skip legacy modules.

## Logging & Provenance

- Log total commits examined, distinct modules touched, modules lacking docs, allowlist hits.
- Record git window boundaries, HEAD commit, and whether history truncated by CLI filters.

## Testing Strategy

- Unit tests under `tests/tests_producers/test_generate_code_doc_churn_report.py` using temp git
  repositories populated via fixtures.
- Scenarios:
  - Code churn with matching doc updates (should not flag).
  - Code churn without doc updates (should flag with counts).
  - Allowlisted module (should skip).
  - Empty window (no artifacts flagged, still emit summary).

## Documentation Tasks

- Author automation guide at `.repo_studios/docs/automation/generate_code_doc_churn_report.md`
  (usage, inputs, outputs, testing).
- Update `script_inventory_architecture.md` once implementation lands (convert "planned" fields to
  actual wiring).

## Outstanding Questions

- How should we treat auto-generated docs (for example, diagrams)? Consider configuration to
  include additional directories.
- Should we compute per-owner rollups for aggregator compatibility?
- Do we need to expose git revision filters (e.g., `--since-commit`) in addition to the time window?

## Next Steps

1. Evaluate Make/CI wiring options so the producer can run in pipeline contexts, promoting the new
  make target once dependencies are available.
1. Coordinate with aggregators (for example, `aggregate_docs_health_signals.py`) to ingest the
  churn artifacts once complementary producers land.
1. Monitor doc-index schema changes and adjust enrichment fields if upstream formats shift.
