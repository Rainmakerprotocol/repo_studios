````markdown
# Function Call Graph View Spec

**Status:** Multi-view coexistence verified with regression coverage (2025-11-09)

## Goal

Render per-module call graphs so operators can trace interactions between functions inside a selected CommandView artifact. The diagram highlights the active module, preserves focus signaling for the selected function, and keeps node styling consistent with the viewer's Level 3 function palette.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `functions`, `moduleId`, `id` | Establishes which functions belong to each module and provides fallback identifiers when selections are missing. |
| `state.normalizedData.functions` (Map) | `name`, `moduleId`, `metrics.lineCount`, `metrics.coverage`, `coverage`, `docstringQuality` | Supplies labels and metric overlays for each function node (line count, coverage, module hint). |
| `state.normalizedData.callGraph.functions` (Map) | adjacency list of function edges | Drives intra-module edge construction; entries outside the active module are ignored. |
| Level selection state | `moduleId`, `functionId` | Determines the active module and optional focus function, defaulting to the first module when no selection exists. |

## Transformations

1. Normalize incoming Maps/objects/arrays into `Map` instances for modules, functions, and call graph edges.
2. Resolve the active module by reusing the selection helper and falling back to the first module key when the selection is missing or stale.
3. Build the local function set for the module and ensure each function has a corresponding node entry.
4. Generate unique Mermaid-safe IDs with `sanitizeMermaidId()` while preserving focus vs. non-focus membership for styling.
5. Traverse the module call graph to create deduplicated intra-module edges only (cross-module edges are discarded for this view).
6. Emit Mermaid class definitions for local and focus nodes using the shared function palette, then append node declarations and edges.
7. Summarize node and edge counts for status messaging and return the assembled diagram definition alongside bookkeeping metadata.

## Mermaid Output Structure

```
graph TD
  <function nodes declared>
  classDef local ...
  classDef focus ...
  node_a --> node_b
  class node_a local;
  class node_focus focus;
```

Nodes belonging to the active module use the `local` class, while the selected (focus) function adopts the `focus` styling. The diagram remains scoped to a single module to avoid overwhelming call graphs.

## Implementation References

- Builder: `buildFunctionCallGraphDiagram()` in `.repo_studios/command_center/viewer/ui/builders/function_call_graph.js`, consumed by `buildFunctionCallGraphViewDefinition()` in `.repo_studios/command_center/viewer/ui/viewer.js`.
- Styling: Function palette constants embedded in the builder keep coloring aligned with Level 3 function views.
- Availability gating: The sidebar packs mark the view as available once the normalized payload exposes `callGraph.functions` data for the selected artifact.

## Verification & Hardening

- Builder regression coverage lives in `.repo_studios/tests/tests_command_center/viewer/test_function_call_graph_view.py`, asserting error messaging, Mermaid output structure, and deterministic renders across repeated calls.
- Multi-view coexistence is guarded by `.repo_studios/tests/tests_command_center/viewer/test_code_flow_multi_view_coexistence.py`, confirming the call graph builder can be invoked between Health pack renders without mutating shared state.
- Sanitization helpers ensure all node IDs are Mermaid-safe and deterministic, preventing collisions across repeated renders.

## Future Enhancements

- Incorporate cross-module edge previews when the Dependency pack wiring lands, optionally dimming external calls rather than dropping them entirely.
- Surface additional metrics (cyclomatic complexity, churn) in node labels once normalization threads those values through `state.normalizedData.functions` consistently.
- Extend focus handling to highlight inbound edges from other modules once the view supports optional neighborhood overlays.
````