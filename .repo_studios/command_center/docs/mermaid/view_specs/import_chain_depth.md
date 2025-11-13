`````markdown
# Import Chain Depth View Spec

````markdown

**Status:** Multi-view coexistence verified with regression coverage (2025-11-12)

## Goal

Visualise the minimal hop count from standard library imports into repository modules so reviewers can spot deep dependency stacks, surface modules without a recorded path to stdlib, and prioritise refactoring for long chains.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `importEdges`, `moduleId`, `functions` | Supplies normalized modules with internal and standard library import metadata plus identifiers for deterministic ordering. |
| View scope selections | `rootId`, `domainId`, `moduleId` | Used to highlight module subsets. When scoped selections return no depth data the builder falls back to a repository-wide snapshot with an info notice. |

## Transformations

1. Normalize module payloads into deterministic `Map` structures and extract import edges grouped by category.
2. Record direct standard library imports per module and build bidirectional internal dependency maps (dependencies and importers) for traversal.
3. Perform a breadth-first search starting from modules that touch the standard library to assign minimal hop depths to downstream modules (following reverse import edges) and capture chain predecessors.
4. Resolve the set of standard library modules reachable for each node by recursively walking upstream dependencies whose depth precedes the current module.
5. Apply focus filtering by retaining only scoped modules plus their upstream dependencies when scope selections are active.
6. Generate a top-down Mermaid diagram with class definitions that flag caution/alert depth tiers, add synthetic stdlib nodes, and render edges from standard library modules through internal dependency chains.
7. Assemble status metadata including depth buckets, deepest modules, unreachable module samples, and unresolved internal targets, then compose a contextual status message.

## Mermaid Output Structure

```
graph TD
  classDef depthBase fill:#0f172a,stroke:#38bdf8,color:#f8fafc,stroke-width:1.5px
  classDef depthCaution fill:#78350f,stroke:#f59e0b,color:#fef3c7,stroke-width:2px
  classDef depthAlert fill:#7f1d1d,stroke:#f87171,color:#fee2e2,stroke-width:2.5px
  classDef depthFocus stroke:#22d3ee,stroke-width:3px,color:#e0f2fe
  classDef stdlibNode fill:#1f2937,stroke:#10b981,color:#ecfdf5,stroke-dasharray:5 3,stroke-width:1.5px
  stdlib_os["std · os"]
  class stdlib_os stdlibNode;
  alpha_core["alpha.core\nDepth 1\nStandard libs 1\nDirect stdlib 1"]
  class alpha_core depthBase;
  beta_utils["beta.utils\nDepth 2\nStandard libs 1"]
  class beta_utils depthCaution;
  stdlib_os --> alpha_core
  alpha_core --> beta_utils
```

Stdlib nodes represent direct imports while module nodes are layered by depth. Depth ≥3 receives the caution style, depth ≥5 receives alert styling, and scoped modules add a focus stroke. Edges flow from dependencies to dependents, making the overall chain easy to scan from top to bottom.

## Implementation References

- Builder: `buildImportChainDepthDiagram()` in `.repo_studios/command_center/viewer/ui/builders/import_chain_depth.js`.
- View wiring: `buildImportChainDepthViewDefinition()` in `.repo_studios/command_center/viewer/ui/viewer.js`, registered under `importChainDepthView` within the Coupling Insight pack.
- Availability gating: `findViewRequirementIssue()` reuses the `inventoryBasics` check to ensure normalized module metadata is loaded before enabling the view.

## Verification & Hardening

- Builder regression: `.repo_studios/tests/tests_command_center/viewer/test_import_chain_depth_view.py` covers Mermaid output, stats snapshots, focus filtering, and empty-state messaging.
- Multi-view coexistence: `.repo_studios/tests/tests_command_center/viewer/test_coupling_pack_multi_view_coexistence.py` executes the import chain depth builder alongside the cross-module references and function call graph diagrams to ensure deterministic definitions across repeated toggles.
- Helper exports: the builder exposes `__test__` hooks for import graph normalization, depth assignment, and label generation to support deeper unit coverage during future refactors.

## Future Enhancements

- Surface optional thresholds so teams can tune caution/alert depth tiers per repository size.
- Overlay complementary metrics (e.g., file churn, coverage) directly onto depth nodes once those data points are available in normalization.
- Provide end-to-end chain exports listing the full stdlib-to-module path for long chains beyond the preview shown in status details.
- Distinguish third-party chains by optionally treating `category: "third_party"` imports as additional entry points.
````

`````