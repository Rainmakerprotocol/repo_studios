# IO Effects Diagram View Spec

**Status:** Controls wired (2025-11-12)

## Goal

Surface module-level functions that interact with the filesystem, environment, or network so operators can trace stateful side effects alongside the emerging State Effects pack.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `functions[]` | Module normalization (`createModuleRecord()`) records the function identifiers defined in each module so the view can scope IO summaries without re-reading raw payloads. |
| `state.normalizedData.functions` (Map) | `id`, `moduleId`, `name`, `ioEffects` (`activeFlags`, booleans) | Function normalization (`createFunctionRecord()` + `normalizeIoEffects()`) produces deterministic IO effect flags (`reads`, `writes`, `env`, `network`) and the pre-sorted `activeFlags` list consumed by the builder. |
| View scope selections | `rootId`, `domainId`, `moduleId`, `functionId` | `buildIoEffectsViewDefinition()` filters function IDs by active selection and applies repository fallbacks when scoped regions lack IO metadata. |

## Transformations

1. Build per-module summaries that associate each function with the IO effect flags it raises, respecting any scoped allow list.
2. Aggregate module/function counts, total effect flags, per-category breakdowns, and leaderboards for status messaging.
3. Emit module subgraphs where function nodes connect to effect category nodes (Reads, Writes, Env, Network) with consistent styling.
4. Append scope-aware fallback notices when the active selection carries no IO metadata while still surfacing repository-level context.

## Mermaid Output Structure

```
graph TD
  classDef module fill:#0f172a,stroke:#38bdf8,color:#f8fafc;
  classDef effect fill:#1f2937,stroke:#f97316,color:#ffedd5;
  classDef function fill:#111827,stroke:#60a5fa,color:#dbeafe;
  linkStyle default stroke:#94a3b8,stroke-width:1.5px;
  subgraph module_alpha.io["alpha.io"]
    effect_1["Reads Files · 1 function"]
    effect_2["Writes Files · 2 functions"]
    function_1["load\n→ reads, writes"]
    function_2["save\n→ writes"]
  end
  subgraph module_beta.net["beta.net"]
    effect_3["Network Calls · 1 function"]
    function_3["ping\n→ network"]
  end
  function_1 --> effect_1
  function_1 --> effect_2
  function_2 --> effect_2
  function_3 --> effect_3
```

Each module forms a subgraph. Effect category nodes display the number of functions triggering that flag, and function nodes list the flags they exercise to keep per-module context compact.

## Implementation References

- Normalization helper `normalizeIoEffects()` lives in `.repo_studios/command_center/viewer/ui/viewer.js`, ensuring every function carries deterministic IO metadata.
- View wiring `buildIoEffectsViewDefinition()` sits in the same module and mirrors the global-state scope logic with IO-specific fallbacks.
- Diagram generation resides in `.repo_studios/command_center/viewer/ui/builders/io_effects_diagram.js`, which assembles module summaries, Mermaid definitions, and status payloads.

## Verification & Hardening

- Builder regression `.repo_studios/tests/tests_command_center/viewer/test_io_effects_diagram_view.py` locks Mermaid output, stats, empty-state messaging, and fallback notices.
- View-definition regression `.repo_studios/tests/tests_command_center/viewer/test_io_effects_view_definition.py` confirms scope handling and repository fallbacks inside the viewer wiring.
- Normalization coverage piggybacks on existing `createFunctionRecord()` tests, with IO-specific assertions to follow once Exception Flow wiring lands.

## Future Enhancements

- Stitch IO effect summaries into the upcoming State Effects coexistence harness once the Exception Flow view is implemented.
- Extend the builder to surface file path samples or environment variable names when producers emit granular metadata.
- Layer severity scoring (e.g., writes vs. reads) into the status panel to prioritise remediation focus.
