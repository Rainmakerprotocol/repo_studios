# Inventory Payload Migration Notes

_Last updated: 2025-11-06_

## Purpose

Outline the adjustments downstream tools must make to consume the enriched
inventory payload emitted by `.repo_studios/command_center/scripts/producers/generate_commandview_inventory.py`.
These notes ensure commandview packs, aggregators, and analytics pipelines stay
aligned while coverage and git churn metadata settle in.

## New Payload Elements

- `files[].coverage` — executed/missing line sets, context breakdowns, counts,
  and line-rate summaries populated when `--coverage-json` inputs are provided.
- `files[].git_churn` — commit counts, additions, deletions, net changes, and
  latest commit metadata derived from `git log --follow --numstat`.
- `statistics.coverage` and `statistics.git_churn` — aggregate line metrics and
  churn rollups across the targeted slice.
- Expanded function/class blocks:
  - `cyclomatic_complexity`, `type_hint_coverage`, `docstring_quality`.
  - `used_globals`, `io_effects`, `raises`, `logging_calls`, `decorators`.
  - `calls`, `call_graph`, `callback_registrations`, `unused_imports`,
    `unreachable_functions` for richer visualization.

## Required Consumer Actions

1. **CommandView renderers**
   - Accept optional `coverage`/`git_churn` metadata; default to zeroed overlays
     when absent.
   - Wire pack templates (Risk & Assurance, Quality Metrics) to read the new
     aggregate statistics.
2. **Aggregators and Summaries**
   - Update JSON parsing helpers to tolerate new keys without throwing when data
     is missing (e.g., repositories with no git history).
   - Cascade churn totals into risk scoring where applicable.
3. **Testing harnesses**
   - Refresh fixtures to include representative coverage/churn frames.
   - Guard against nondeterministic git output by stubbing timestamps when
     comparing golden files.
4. **Ops / Orchestrators**
   - Ensure execution environments provide git binaries and coverage artifacts
     before invoking the producer.
   - Capture warnings emitted when churn cannot be collected so pipelines can
     surface actionable alerts.

## Backward Compatibility

- Schema version remains additive; existing consumers that ignore the new keys
  continue to function.
- Coverage and churn blocks only appear when inputs are present—renderers must
  handle `None` gracefully.
- CLI contracts stay stable outside of the optional `--coverage-json` flag.

## Next Steps

- Mirror these notes into viewer documentation once commandview naming lands.
- Decide on long-term schema version bump (v3) when commandview renaming and new
  artifact naming conventions are adopted.
- Capture sample payload slices for documentation and testing purposes.
