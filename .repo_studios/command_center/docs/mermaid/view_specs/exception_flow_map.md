# Exception Flow Map View Spec

**Status:** Controls wired (2025-11-11)

## Goal

Highlight where functions raise exceptions so operators can quickly spot unstable modules, understand shared failure modes, and prioritize remediation as part of the State Effects pack.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `functions[]` | Module normalization (`createModuleRecord()`) records function identifiers per module to scope exception summaries without re-reading raw payloads. |
| `state.normalizedData.functions` (Map) | `id`, `moduleId`, `name`, `raisedExceptions[]` | Function normalization (`createFunctionRecord()` + `normalizeRaisedExceptions()`) emits structured exception descriptors (type, message, qualified name, lineno) with duplicate suppression and stable ordering. |
| View scope selections | `rootId`, `domainId`, `moduleId`, `functionId` | `buildExceptionFlowViewDefinition()` filters eligible function IDs by active selection, applies repository fallbacks, and threads scope labels/fallback notices into status messaging. |

## Transformations

1. Filter normalized function records to those with `raisedExceptions`, respecting scope allow lists from level selections.
2. Aggregate module-level summaries that track function-to-exception edges, per-module raise counts, and distinct exception descriptors.
3. Rank top modules, functions, and exception types for status panels (limited to 10 entries each) while computing module/function/exception totals.
4. Emit Mermaid subgraphs per module: function nodes connect to exception nodes, and labels include frequent raisers plus formatted exception details.
5. Attach scope-aware fallback notices when scoped selections contain no exceptions, surfacing repository-wide context instead of rendering an empty diagram.

## Mermaid Output Structure

```
graph TD
  classDef module fill:#0f172a,stroke:#38bdf8,color:#f8fafc;
  classDef exception fill:#1f2937,stroke:#f87171,color:#fee2e2;
  classDef function fill:#111827,stroke:#60a5fa,color:#dbeafe;
  linkStyle default stroke:#94a3b8,stroke-width:1.5px;
  subgraph module_alpha.errors["alpha.errors"]
    exception_1["ValueError · 2 raisers\n\"bad state\""]
    exception_2["IOError · 1 raiser"]
    exception_4["RuntimeError · 1 raiser\n\"persist failed\""]
    function_1["load\n→ ValueError, IOError"]
    function_2["save\n→ RuntimeError"]
  end
  subgraph module_beta.handlers["beta.handlers"]
    exception_3["ValueError · 1 raiser\n\"bad state\""]
    function_3["handle\n→ ValueError"]
  end
  function_1 --> exception_1
  function_1 --> exception_2
  function_2 --> exception_4
  function_3 --> exception_3
```

Each module forms a subgraph with function nodes connected to the exceptions they raise. Exception labels include the number of raisers and, when available, a trimmed message to keep hotspots readable. Function labels list up to two exception descriptors before eliding with an ellipsis.

## Implementation References

- Normalization helper `normalizeRaisedExceptions()` lives in `.repo_studios/command_center/viewer/ui/viewer.js`, producing deduplicated exception descriptors with inferred types/messages and stable sorting for downstream builders.
- View wiring `buildExceptionFlowViewDefinition()` resides in the same module, resolving scoped function allow lists, applying repository fallbacks, and delegating diagram construction to the builder.
- Diagram generation is handled by `.repo_studios/command_center/viewer/ui/builders/exception_flow_map.js`, which assembles module summaries, Mermaid definitions, status payloads, and leaderboard metadata.

## Verification & Hardening

- Builder regression `.repo_studios/tests/tests_command_center/viewer/test_exception_flow_map_view.py` locks diagram output, stats, empty-state messaging, and fallback notices.
- View-definition regression `.repo_studios/tests/tests_command_center/viewer/test_exception_flow_view_definition.py` confirms scoped rendering, repository fallbacks, and status payloads exposed through the viewer test API.
- Exception normalization indirectly covered by the tests above; dedicated normalization assertions can be added alongside future producer schema updates to guard inferred labels.

## Future Enhancements

- Blend severity signals (e.g., recent screening failures) into status panels once producers emit richer exception metadata.
- Surface timeline links to screening summaries when recurring exceptions share module/function context.
- Extend the upcoming State Effects coexistence harness to include Exception Flow alongside Global Variable Usage and IO Effects views.
