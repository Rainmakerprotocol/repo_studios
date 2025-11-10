# Module Dependency Graph View Spec

`````markdown

**Status:** Multi-view coexistence verified with regression coverage (2025-11-10)

## Goal

Render internal module-to-module import relationships so operators can pinpoint tightly coupled files, unused imports, and isolated modules before refactoring. The diagram highlights high-volume importers, surfaces unused statements, and keeps orphan modules visible even when they have no edges.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `importEdges`, `functions`, `moduleId`, `id` | Supplies normalized import metadata, function counts, and identifiers for each module. |
| `state.normalizedData.metrics.modules` (Map, optional) | `coverageSignals`, `gitChurn`, `lineCount` | Reserved for future overlay hints; not required for the initial wiring. |
| View scope selections | `rootId`, `domainId` | Passed through for status context; current implementation renders the full dependency map regardless of scope but labels the snapshot with the active selection. |
| Dependency summaries | `moduleRecord.dependencySummary` | Aggregates third-party and standard-library usage for status descriptors. |

## Transformations

1. Normalize inbound module structures into a `Map` to guarantee deterministic iteration order.
2. Collapse raw `importEdges` into internal adjacency by aggregating statement counts, function usage, and unused flags per `(source, target)` pair.
3. Track module-level statistics (incoming/outgoing edges, unused counts, distinct targets) to drive severity styling and status metrics.
4. Collect external dependency tallies from `dependencySummary` buckets to note third-party and standard-library reach.
5. Generate Mermaid-safe node identifiers, classify modules (base/caution/alert/orphan), and emit `graph LR` node definitions with multiline labels reflecting counts.
6. Append labelled edges that display import statements, function usage, and unused counts for each internal relationship.
7. Build status details (stat summary, top couplings list, external dependency list, orphan pills) and compose a contextual status message incorporating scope, module totals, and unused import counts.

## Mermaid Output Structure

```
graph LR
  classDef module ...
  classDef moduleCaution ...
  classDef moduleAlert ...
  classDef moduleOrphan ...
  alpha_core["alpha.core\nFunctions 5\nOut 3 (4) · In 1 (2)\nUnused imports 1"]
  class alpha_core moduleCaution;
  alpha_core -->|2 imports\n1 unused| beta_helpers
```

Nodes adopt class-based styling (base/caution/alert/orphan) and labelled edges include statement counts plus function usage hints. The layout keeps left-to-right flow to emphasize dependency direction.

## Implementation References

- Builder: `buildModuleDependencyGraphDiagram()` in `.repo_studios/command_center/viewer/ui/builders/module_dependency_graph.js`.
- View wiring: `buildModuleDependencyGraphViewDefinition()` in `.repo_studios/command_center/viewer/ui/viewer.js`, registered under `moduleDependencyGraphView`.
- Availability gating: `findViewRequirementIssue()` now recognizes the `moduleDependencies` requirement by verifying normalized `importEdges` presence.

## Verification & Hardening

- Normalization coverage in `.repo_studios/tests/tests_command_center/viewer/test_dependency_data_normalization.py` confirms import graph edges are sanitized into module records.
- Builder regression in `.repo_studios/tests/tests_command_center/viewer/test_module_dependency_graph_view.py` asserts Mermaid output, stats snapshot, and descriptor content.
- Coexistence regression in `.repo_studios/tests/tests_command_center/viewer/test_dependency_pack_multi_view_coexistence.py` verifies repeated renders alongside the Function Call Graph remain deterministic.
- Status descriptors render through existing list/stat-summary/pill components so no new CSS hooks are required.

## Future Enhancements

- Respect active root/domain filters by trimming the diagram to selected scopes while retaining dependent modules that cross boundaries.
- Blend module-level churn and coverage signals into labels once those metrics are exposed in the builder options.
- Surface unused import samples directly in status details for faster remediation queues.
- Provide toggleable aggregation to collapse dependencies at the domain level when the module graph exceeds readability thresholds.
`````
