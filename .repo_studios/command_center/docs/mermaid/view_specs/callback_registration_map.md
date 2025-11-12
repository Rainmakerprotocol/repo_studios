````markdown
# Callback Registration Map View Spec

**Status:** Multi-view coexistence verified (2025-11-11)

## Goal

Trace where modules register callbacks, listeners, and handlers so operators can audit event-driven coupling, confirm expected emitters, and identify orphaned or risky targets before drilling into Code Flow views.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `callbackRegistrations`, `moduleId`, `packageName` | Module-level aggregation lists each registration with emitter function, target metadata, and source location. |
| `state.normalizedData.functions` (Map) | `callbackRegistrations`, `moduleId`, `id` | Provides finer-grained view of which functions participate in registrations for drill-down stats. |
| CommandView payload (`files[].callback_registrations`) | `expression`, `method`, `kind`, `root`, `module`, `resolved`, `target`, `target_kind`, `target_via`, `lineno`, `function` | Producer-level schema captured during normalization; function-level entries omit `function` until aggregated at module scope. |
| View scope selections | `rootId`, `domainId`, `moduleId` | Required for future filtering so the diagram can focus on specific packages or modules when controls arrive. |

## Transformations

1. Normalize callback registration entries, trimming expression strings, lower-casing methods, and preserving resolved module paths so builders can group by emitter or target.
2. Deduplicate registrations using the producer heuristics (`expression`, `target`, `targetVia`, `lineno`) while retaining emitter-qualified names for module-level aggregation.
3. Build lookups that map target identifiers back to modules/functions once builder wiring lands, enabling Mermaid node creation for emitters and receivers.
4. Capture registration counts per module and per target kind (e.g., attribute vs. name) to drive status messaging and highlight unusual patterns.
5. Prepare metadata to flag registrations lacking resolved targets so builders can annotate potential dead wiring.

## Mermaid Output Structure (planned)

```
graph TD
  classDef emitter fill:#1f2937,stroke:#38bdf8,color:#f8fafc;
  classDef target fill:#0f172a,stroke:#f97316,color:#f8fafc;
  alpha_callbacks_register_handlers["alpha.callbacks::register_handlers\nregister_callback() @42"]
  beta_handlers_handle_event["beta.handlers.handle_event"]
  alpha_callbacks_register_handlers -->|callback| beta_handlers_handle_event
```

Emitters will appear as nodes labelled with function name and registration method, while edges point to targets with annotations showing the registration channel (e.g., `callback`, `listener`). Styling distinguishes emitter vs. target roles.

## Implementation References

- Normalization helper `normalizeCallbackRegistrations()` in `.repo_studios/command_center/viewer/ui/viewer.js` hydrates both module and function records.
- Module ingestion leverages `createModuleRecord()` to surface `callbackRegistrations` alongside dependency and export metadata.
- Function-level normalization flows through `createFunctionRecord()` so upcoming builders can reason about emitters without re-parsing raw payloads.
- Viewer wiring delegates to `buildCallbackRegistrationMapViewDefinition()` which scopes selections, applies repository fallbacks, and invokes the dedicated builder.
- Diagram generation lives in `.repo_studios/command_center/viewer/ui/builders/callback_registration_map.js`, emitting emitter and target nodes plus status summaries.

## Verification & Hardening

- New regression `.repo_studios/tests/tests_command_center/viewer/test_callback_data_normalization.py` asserts that module/function records expose sanitized callback metadata (method casing, resolved modules, targets, source locations).
- Builder regression `.repo_studios/tests/tests_command_center/viewer/test_callback_registration_map_view.py` validates Mermaid output, stats snapshots, and repository fallbacks for the Event Dynamics view.
- Coexistence regression `.repo_studios/tests/tests_command_center/viewer/test_event_dynamics_multi_view_coexistence.py::test_callback_registration_map_coexists_with_function_call_graph_view` confirms Event Dynamics toggles preserve definitions, status messaging, and stats alongside the Function Call Graph view.
- Producer extraction already deduplicates registrations via `_collect_callback_registrations()` in `generate_commandview_inventory.py`, ensuring normalization receives stable input.
- Existing CommandView fixtures retain `callback_registrations` coverage, keeping inventory schema alignment intact.

## Future Enhancements

- When controls are wired, compute target grouping (e.g., event bus vs. timer) and emit Mermaid subgraphs to spotlight high-churn emitters.
- Overlay screening severity once event-driven risk metrics become available.
- Integrate diff mode to highlight newly added or removed registrations between CommandView snapshots.
````