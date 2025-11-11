``````markdown
# External vs Internal Dependency Map View Spec

`````markdown

**Status:** Controls wired; multi-view coexistence verified (2025-11-11)

## Goal

Highlight how each module balances internal CommandView dependencies against third-party and standard-library usage so operators can spot boundary violations, missing abstractions, and over-reliance on external packages before remediation work begins.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `packageName`, `importEdges`, `dependencySummary` | Supplies normalized import metadata, owning package hints, and per-category dependency tallies for each module. |
| Module import edges | `category`, `target`, `unused`, `functions`, `via` | Categories distinguish internal vs external dependencies; function usage and alias details drive status messaging and pill lists. |
| View scope selections | `rootId`, `domainId`, `moduleId` | Used to tailor status messages and filter modules once controls are wired. |
| Normalized screening metrics (optional) | `metrics.modules.gitChurn`, `metrics.modules.coverageSignals` | Reserved for future overlays that correlate risky external usage with volatility and coverage gaps. |

## Transformations

1. Flatten each module's normalized `importEdges` into category buckets (`internal`, `third_party`, `standard_library`, `unknown`) while tracking unused imports and alias usage.
2. Summarize totals per module (distinct internal targets, distinct external packages, unused statement counts) using `dependencySummary` to avoid recomputing aggregates.
3. Determine focus state by comparing internal vs external weights (for example flagging modules where external imports outnumber internal CommandView references).
4. Assemble Mermaid-safe node identifiers labelled with module name, internal/external counts, and unused import tallies.
5. Emit subgraphs or edge descriptors that group internal targets separately from external packages so boundary violations stand out in the rendered diagram.
6. Build status details that list top external packages, risky modules per scope, and any unused external imports worth pruning.

## Mermaid Output Structure

```
graph TD
  classDef internal fill:#0f172a,stroke:#38bdf8,color:#f8fafc;
  classDef external fill:#1f2937,stroke:#f97316,color:#f8fafc;
  scripts_consumers_enrich_inventory["scripts.consumers.enrich_inventory\nInternal: 2 modules\nExternal: 3 packages\nUnused: 1"]
  class scripts_consumers_enrich_inventory external;
  scripts_constructors_generate_inventory --> scripts_consumers_enrich_inventory
  scripts_consumers_enrich_inventory -->|pandas|
```

Nodes carry summary stats while edges distinguish internal modules from external package names; styling flips emphasis when external usage dominates.

## Implementation References

- Builder: `buildExternalVsInternalDependencyMapDiagram()` under `.repo_studios/command_center/viewer/ui/builders/` renders the diagram.
- View wiring: `buildExternalVsInternalDependencyMapViewDefinition()` is registered in `.repo_studios/command_center/viewer/ui/viewer.js` to hydrate Dependency pack controls.
- Requirement gating: `findViewRequirementIssue()` reuses the existing `moduleDependencies` bucket so availability checks stay consistent across Dependency pack views.

## Verification & Hardening

- Normalization coverage: `.repo_studios/tests/tests_command_center/viewer/test_external_dependency_data_normalization.py` validates that module records expose categorized import edges and dependency summaries required for the view.
- Builder coverage: `.repo_studios/tests/tests_command_center/viewer/test_external_vs_internal_dependency_map_view.py` exercises diagram output, scope fallback, and determinism; coexistence with other dependency views is guarded by `.repo_studios/tests/tests_command_center/viewer/test_dependency_pack_multi_view_coexistence.py`.
- Producer coverage: `_dependency_category()` and `_summarize_dependency_categories()` in `generate_commandview_inventory.py` already classify imports and aggregate category counts.

## Future Enhancements

- Incorporate churn and coverage overlays to prioritize risky external hot spots.
- Surface license metadata for third-party packages when inventories begin capturing SPDX identifiers.
- Offer filters that collapse well-known third-party buckets (e.g., AWS SDKs) for clutter-free reviews.
- Support diff mode to show how dependency mix shifts between successive CommandView snapshots.
`````

``````