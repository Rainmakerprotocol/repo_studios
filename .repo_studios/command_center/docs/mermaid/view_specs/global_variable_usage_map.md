# Global Variable Usage Map View Spec

**Status:** Controls wired (2025-11-11)

## Goal

Surface module-level global variables and the functions that reference them so operators can quickly spot hidden couplings, implicit state, and potential refactoring targets before expanding to broader side-effect views.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `globals[]` (`name`, `valueKind`, `lineno`), `functions[]` | Module normalization (`createModuleRecord()` + `normalizeModuleGlobals()`) ensures each module exposes a de-duplicated, sorted list of declared globals alongside the functions defined in that module. |
| `state.normalizedData.functions` (Map) | `id`, `moduleId`, `name`, `usedGlobals[]` | Function normalization (`createFunctionRecord()` + `normalizeUsedGlobals()`) captures every global referenced by the function with deterministic ordering. |
| View scope selections | `rootId`, `domainId`, `moduleId`, `functionId` | Used by `buildGlobalVariableUsageViewDefinition()` to determine focused function, module, domain, or repository fallbacks. |

## Transformations

1. Build per-module summaries that map declared globals to the set of local functions referencing them, respecting any allow list scoped by the active view selection.
2. Derive aggregate counts (modules, globals, functions, references) plus top-module and top-global leaderboards for status messaging.
3. Generate Mermaid subgraphs per module where functions point to the globals they touch, including class assignments for styling.
4. Apply scope-aware fallbacks when the active selection lacks global usage, surfacing repository-level diagrams with explicit notices.

## Mermaid Output Structure

```
graph TD
  classDef module fill:#0f172a,stroke:#38bdf8,color:#f8fafc;
  classDef global fill:#1f2937,stroke:#facc15,color:#fef08a;
  classDef function fill:#111827,stroke:#60a5fa,color:#dbeafe;
  linkStyle default stroke:#94a3b8,stroke-width:1.5px;
  subgraph module_alpha.config["alpha.config"]
    global_1["SETTINGS (dict) line 5"]
    global_2["FLAG (bool) line 12"]
    function_1["load\n→ SETTINGS"]
    function_2["toggle\n→ 2 globals"]
  end
  subgraph module_beta.feature["beta.feature"]
    global_3["LIMIT (int) line 8"]
    function_3["check\n→ LIMIT"]
  end
  function_1 --> global_1
  function_2 --> global_1
  function_2 --> global_2
  function_3 --> global_3
```

Each module forms a subgraph, functions appear as nodes with a suffix highlighting the globals they touch, and edges represent individual global references.

## Implementation References

- Normalization helpers `normalizeModuleGlobals()` and `normalizeUsedGlobals()` live in `.repo_studios/command_center/viewer/ui/viewer.js` and hydrate module/function records during CommandView ingestion.
- View wiring `buildGlobalVariableUsageViewDefinition()` resides in the same file, resolving scope selections, fallbacks, and builder options.
- Diagram generation is handled by `.repo_studios/command_center/viewer/ui/builders/global_variable_usage_map.js`, which assembles module summaries, Mermaid definitions, stats, and status messaging.

## Verification & Hardening

- Builder regression `.repo_studios/tests/tests_command_center/viewer/test_global_variable_usage_map_view.py` validates Mermaid output, stats, empty-state messaging, and fallback notices.
- View-definition regression `.repo_studios/tests/tests_command_center/viewer/test_global_variable_usage_view_definition.py` confirms scope handling, repository fallbacks, and stat propagation through the viewer wiring.
- Normalization coverage for globals and used-globals flows through existing viewer tests that exercise `createModuleRecord()`/`createFunctionRecord()`; additional targeted cases will be added alongside future State Effects views.

## Future Enhancements

- Layer IO effects and exception metadata onto the same module summary once subsequent State Effects views land, enabling richer status cards.
- Extend scope allow lists to support cross-module global usage once producers emit provenance for imported globals.
- Add diff mode to highlight newly introduced or removed global references between CommandView snapshots.
