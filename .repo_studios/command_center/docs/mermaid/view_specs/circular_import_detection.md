# Circular Import Detection View Spec

**Status:** Controls wired with scoped Tarjan builder and coexistence coverage (2025-11-10)

## Goal

Surface import cycles between project modules so operators can quickly spot chains that risk initialization failures, implicit side effects, or brittle refactor points. The diagram should group strongly connected modules, highlight cycle length and severity, and provide status guidance when the inventory reports no cycles for the selected scope.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `packageName`, `importEdges[]`, `dependencySummary` | `importEdges` supplies fine-grained import targets, categories, aliases, and call-site metadata. `dependencySummary.graphs.imports` mirrors the producer summary (module-level import edges) and stays stable even when selected modules lack normalized import detail. |
| `moduleRecord.dependencySummary.graphs.imports[]` | `source`, `target` | Pre-aggregated module import graph emitted by CommandView producers. Each entry is a `[source, target]` pair representing module-level dependencies; suitable for SCC detection without re-deriving from file-level details. |
| `moduleRecord.dependencySummary.violations.cycles` | boolean | Signals whether the producer previously flagged cycle violations for the module. Used to seed severity messaging when the diagram discovers cycles.
| `state.levelSelections` | `rootId`, `domainId`, `moduleId` | Viewer selection governs scope; when scoped nodes yield no cycles, the renderer should fall back to repository-wide analysis with a clear notice. |

## Transformations

1. Merge module-level imports from `dependencySummary.graphs.imports` and `importEdges` into a unified directed graph keyed by module ID.
2. Run strongly connected component detection (Tarjan/Kosaraju) to locate cycles with >1 node or self-loops (`module -> module`).
3. Collapse each component into a cycle group, preserving ordered paths (e.g., `alpha.core → beta.helpers → gamma.utils → alpha.core`).
4. Compute per-cycle metadata: length, distinct packages, whether any edge category is `third_party`, and whether underlying modules have `violations.cycles` flagged.
5. Build status aggregates summarizing cycle counts by length (2-node, 3–5 node, >5) and flag modules participating in multiple cycles.
6. Expose fallback messaging when the scoped selection contains no cycles but repository-level data does, appending the message to `statusDetails`.

## Mermaid Output Structure

```mermaid
graph TD
  subgraph Cycle 1 (length 3)
    alpha.core --> beta.helpers
    beta.helpers --> gamma.utils
    gamma.utils --> alpha.core
  end
  subgraph Cycle 2 (self-loop)
    delta.loader --> delta.loader
  end
  class alpha.core cycleAnchor
  class beta.helpers cycleParticipant
  class gamma.utils cycleParticipant
  class delta.loader selfLoop
```

Cycles render as subgraphs named by rank (Cycle 1, Cycle 2, ...). Nodes include CSS classes for anchors (first node in the ordered path), participants, and self-loops so styling can emphasize severity or frequency. Edges remain directed, maintaining readability for longer chains.

## Implementation References

- `buildModuleImportEdges()` in `viewer/ui/viewer.js` normalizes per-module import edges with target modules, alias info, and unused flags.
- `dependencySummary.graphs.imports` derives from `_collect_dependency_summary()` in `generate_commandview_inventory.py`, providing repository-wide module import adjacency.
- Viewer state helpers (`state.levelSelections`) already drive scope filtering for other Dependency pack views and can be reused to guard cycle analysis.

## Verification & Hardening

- Node-backed regression `.repo_studios/tests/tests_command_center/viewer/test_circular_import_detection_view.py::test_circular_import_detection_is_deterministic` asserts stable Mermaid output and status messaging across repeated builder invocations and mixed cycle shapes.
- Coexistence regression `.repo_studios/tests/tests_command_center/viewer/test_circular_import_detection_view.py::test_circular_import_detection_coexists_with_dependency_view` verifies toggling between the cycle diagram and module dependency graph preserves cached state and status text.
- Builder fallbacks thread an info descriptor into status details when scoped selections produce no cycles yet repository analysis does, ensuring operators understand why repository-wide results appear.

## Future Enhancements

- Thread churn and coverage overlays into cycle summaries to prioritize risky components.
- Highlight edges that traverse package boundaries or violate intended layer boundaries (e.g., Summarizers importing Producers).
- Surface remediation tips or direct links to offending modules within the Command Center sidebar once contextual panels are available.
