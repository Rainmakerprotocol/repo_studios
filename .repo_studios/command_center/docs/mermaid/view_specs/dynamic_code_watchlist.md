````markdown
# Dynamic Code Watchlist View Spec

**Status:** Multi-view coexistence verified (2025-11-11)

## Goal

Highlight modules that execute dynamic code so operators can prioritize remediation for risky patterns such as `exec()`, runtime imports, metaclass injection, or globals mutation before returning to static dependency analysis.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `dynamicCode` (`hasDynamic`, `flags`, `activeFlags`, `events`, `eventCount`) | Module records expose pre-normalized dynamic code summaries for builders without reprocessing raw payloads. |
| `state.normalizedData.functions` (Map) | `dynamicCode` (`hasDynamic`, `flags`, `events`) | Function records retain the same normalized structure so future drill-down panels can surface emitter-level detail. |
| CommandView payload (`files[].dynamic_code`) | `flags.exec`, `flags.dynamic_import`, `flags.metaclass`, `flags.globals_mutation`, `events[].kind`, `events[].detail`, `events[].lineno` | Raw producer schema normalized by `normalizeDynamicCode()` to align snake_case fields with viewer expectations. |
| View scope selections | `rootId`, `domainId`, `moduleId` | Enables scoped rendering that falls back to repository coverage when no dynamic signals exist in the active selection. |

## Transformations

1. Normalize dynamic code payloads, coercing snake_case flag keys (`dynamic_import`, `globals_mutation`) to camelCase booleans and capturing enabled flags in `activeFlags`.
2. Filter and sort dynamic events by kind, then line number, ensuring deterministic Mermaid output and status summaries.
3. Aggregate flag triggers and event kinds per module to drive status messaging, stats cards, and the watchlist node content.
4. Apply scope-aware filtering using current viewer selections, emitting fallback notices when scoped modules lack dynamic signals but the repository contains them.
5. Produce node-level class assignments so Mermaid styling highlights modules and flag/event hubs with dedicated palettes.

## Mermaid Output Structure

```
graph TD
  classDef module fill:#1f2937,stroke:#f97316,color:#f8fafc;
  classDef flag fill:#0f172a,stroke:#22d3ee,color:#f8fafc;
  classDef event fill:#111827,stroke:#f97316,color:#f8fafc;
  repo_module_alpha["alpha.runtime.loader\nFlags: exec(), dynamic import\nEvents: 3\nKinds: dynamic import (2), exec (1)"]
  flag_exec["exec()\nModules: 1"]
  event_dyn_import["dynamic import\nEvents: 2\nTop Modules: alpha.runtime.loader (2)"]
  repo_module_alpha -->|exec()| flag_exec
  repo_module_alpha -->|dynamic import (2)| event_dyn_import
```

Modules appear on the left with their active flags and event counts, while flag nodes and event-kind hubs summarize cross-module triggers and provide context for remediation.

## Implementation References

- Normalization helper `normalizeDynamicCode()` lives in `.repo_studios/command_center/viewer/ui/viewer.js`, hydrating both module and function records.
- Viewer wiring delegates to `buildDynamicCodeWatchlistViewDefinition()` in the same file, which applies scoped filtering, repository fallbacks, and message handling.
- Diagram generation is implemented in `.repo_studios/command_center/viewer/ui/builders/dynamic_code_watchlist.js`, producing Mermaid definitions, status summaries, and stats blocks.
- Sidebar registration for the Event Dynamics pack lives in `.repo_studios/command_center/viewer/ui/viewer.js` where the `dynamic_code_watchlist` entry declares filename, label, and gating logic.

## Verification & Hardening

- Regression `.repo_studios/tests/tests_command_center/viewer/test_dynamic_code_data_normalization.py` locks the normalized flag and event output, including unknown-kind fallbacks and sorting.
- Builder regression `.repo_studios/tests/tests_command_center/viewer/test_dynamic_code_watchlist_view.py` validates diagram content, stats, fallback handling, and deterministic ordering.
- Coexistence regression `.repo_studios/tests/tests_command_center/viewer/test_event_dynamics_multi_view_coexistence.py` confirms the watchlist toggles cleanly with the Function Call Graph view without losing state.
- Pytest target `-k dynamic_code` guards normalization and builder behaviour in CI and local smoke passes.

## Future Enhancements

- Overlay screening or risk scores once the CommandView pipeline emits severity metrics for dynamic execution hotspots.
- Enrich status panels with per-module remediation guidance (e.g., audit runtime imports, replace `exec()` with safer patterns).
- Introduce diff mode to spotlight newly introduced dynamic code between consecutive CommandView snapshots.
````
