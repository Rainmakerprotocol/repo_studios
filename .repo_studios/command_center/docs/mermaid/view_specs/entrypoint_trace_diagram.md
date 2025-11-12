````markdown
# Entrypoint Trace Diagram View Spec

**Status:** Prototype wired (2025-11-11)

## Goal

Visualize how repository entrypoints (command-line interfaces, pipeline drivers, bootstrap routines) expand into the call graph so operators can audit onboarding flows, ensure orchestration logic remains focused, and trace downstream dependencies without manually reading modules guarded by `__main__` blocks.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `entrypoints.hasMainGuard`, `entrypoints.cliParser`, `entrypoints.candidates`, `functions`, `moduleId` | Module records now surface normalized entrypoint metadata plus the curated candidate list used to seed the trace. |
| `state.normalizedData.functions` (Map) | `id`, `name`, `moduleId`, `calls` | Supplies function definitions and outbound call targets for traversal beyond the entrypoint candidates. |
| `state.normalizedData.callGraph.functions` (Map) | `sourceId -> [targetId, ...]` | Call graph adjacency list required to expand the trace and compute downstream depth. |
| `state.normalizedData.entrypoints` (Map) | `moduleId`, `candidates[]`, `hasMainGuard`, `cliParser` | Convenience index for quick access to entrypoint summaries without scanning every module. |
| View scope selections | `rootId`, `domainId`, `moduleId` | Enables filtered traces (e.g., orchestrator-only) while falling back to repository-wide candidates when scoped modules lack entrypoints. |

## Transformations

1. Seed candidate entrypoints per module by combining producer flags (`has_main_guard`, `cli_parser`), naming heuristics (`main`, `run`, `*_entrypoint`, etc.), and call-graph isolation checks to highlight top-level orchestrators.
2. Build inbound call index so functions without upstream callers can be promoted when `__main__` guards exist but names deviate from standard patterns.
3. Sort candidates by outbound call volume, reason tag, and alphabetically to provide deterministic ordering and emphasize orchestrators with broader fan-out.
4. Expose candidate metadata on module records (`entrypoints.candidates`) and surface a repository-level index (`state.normalizedData.entrypoints`) for fast lookup from builders.
5. Preserve heuristic reason codes (`main-guard-name-match`, `cli-parser-name-match`, `*-isolated-call`) so the diagram and status messaging can explain why a function was treated as an entrypoint.

## Mermaid Output Structure

```
graph TD
  classDef entrypoint fill:#0f172a,stroke:#38bdf8,color:#f8fafc;
  classDef downstream fill:#1f2937,stroke:#f97316,color:#f8fafc;
  entry_alpha_main["alpha.runner::main\nmain-guard-name-match\nOutbound: 3"]
  entry_alpha_main --> downstream_alpha_setup["alpha.runner::setup_context"]
  entry_alpha_main --> downstream_alpha_execute["alpha.runner::execute_pipeline"]
  downstream_alpha_execute --> downstream_alpha_finalize["alpha.runner::finalize"]
```

The builder renders entrypoints with distinct styling, annotates reason codes, and expands reachable functions while respecting scope filters.

## Implementation References

- Normalization helper `normalizeEntrypointSignals()` in `.repo_studios/command_center/viewer/ui/viewer.js` standardizes producer flags before heuristics run.
- `populateEntrypointCandidates()` (same module) computes candidate lists, inbound counts, outbound counts, and reason codes while updating module records.
- Entry-point summary index returned as `state.normalizedData.entrypoints` provides module-level snapshots for builders.
- Call graph data structures originated from the CommandView producer and were already leveraged by the Function Call Graph view, ensuring consistency across Code Flow pack diagrams.

## Verification & Hardening

- Regression `.repo_studios/tests/tests_command_center/viewer/test_entrypoint_data_normalization.py` validates heuristic coverage, candidate ordering, and metadata surfaces for both main-guard and CLI-driven modules.
- Regression `.repo_studios/tests/tests_command_center/viewer/test_entrypoint_trace_view.py` locks builder output, scope-aware fallback messaging, and deterministic status details.
- Coexistence coverage in `.repo_studios/tests/tests_command_center/viewer/test_code_flow_multi_view_coexistence.py` now exercises Function Call Graph ↔ Entrypoint Trace toggles to guarantee stable definitions.
- Existing call graph normalization remains unchanged, and the entrypoint index piggybacks on the same Map structures tested by `test_function_call_graph_view.py`.

## Future Enhancements

- Allow builders to expand beyond the first hop by layering depth limits and cycle detection tailored to entrypoint exploration.
- Thread CLI argument metadata (once producers emit parsed signatures) into the candidate nodes for richer operational context.
- Introduce diff mode comparing entrypoint fans across CommandView snapshots to catch unexpected pipeline drift.
````
