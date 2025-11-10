# Logging Flow View Spec

**Status:** Data slice documented and normalized (2025-11-09)

## Goal

Surface how logging statements propagate through the codebase so maintainers can gauge observability coverage, highlight logging hot spots, and verify that critical code paths emit the expected log levels.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.functions` (Map) | `loggingCalls`, `moduleId`, `name`, `id`, `lineno`, `signature`, `metrics.lineCount` | Primary function catalogue supplying call-level logging metadata, ownership, and supplemental detail for diagram labels. |
| `state.normalizedData.modules` (Map) | `moduleId`, `functions` | Provides per-module groupings to cluster logging events where needed. |
| `state.normalizedData.screeningHistory` (object) | `events[].severity`, `events[].timestamp`, `events[].packId`, `events[].packLabel` | Optional telemetry giving recent screening severities so the view can flag error streaks alongside logging coverage. |
| View options | `bucketLimit`, `viewLabel`, `centerLabel` | Optional overrides for diagram sizing and labeling applied by the viewer definition. |

### Upstream Guarantees

- `generate_commandview_inventory.py` already emits `logging_calls` for every function/method; regression coverage lives in `.repo_studios/tests/tests_producers/test_generate_function_inventory.py::test_function_metadata_persists_effects_and_decorators`.
- Normalization now preserves the logging metadata via `createFunctionRecord()` in `viewer.js`, exposing a sanitized `loggingCalls` array for downstream transforms.

## Transformations (Planned)

1. Normalize the scoped function set to a deterministic `Map` using the shared scope helpers.
2. Aggregate logging events by level (`debug`, `info`, `warning`, `error`, `exception`, etc.) and optionally by module to surface hot spots.
3. Build Mermaid nodes that summarize log levels per function (e.g., list of emitted levels, counts, representative line numbers) with overflow grouping when item limits are exceeded.
4. Optionally render module-level clusters showing functions sorted by highest severity or frequency, reusing severity-driven palette variants.
5. Compute stats for total logging emitters, functions without logging, top modules by log density, and counts per log level to inform status messaging.
6. Derive screening telemetry (latest severity, streak length, recent warning/critical counts) from the optional screening history and thread the summary into diagram status messages and stats.

## Implementation References

- Function normalization lives in `.repo_studios/command_center/viewer/ui/viewer.js` (`createFunctionRecord` + `normalizeLoggingCalls`) and now exports sanitized logging metadata for viewer consumption.
- Inventory extraction logic resides in `.repo_studios/command_center/scripts/producers/generate_commandview_inventory.py`, which hydrates `logging_calls` during AST traversal.
- Future builder module will follow the existing Quality Metrics pattern under `viewer/ui/builders/`.

## Verification & Hardening

- Producer regression coverage: `.repo_studios/tests/tests_producers/test_generate_function_inventory.py::test_function_metadata_persists_effects_and_decorators` asserts logging calls are captured at the inventory layer.
- Viewer smoke manual check: `state.normalizedData.functions.get(<functionId>).loggingCalls` now yields normalized `{ level, lineno, message?, logger? }` entries.
- Follow-up: add Node-based regression once the builder lands to exercise logging aggregation and Mermaid output. *(Completed 2025-11-09 — covered by `.repo_studios/tests/tests_command_center/viewer/test_logging_flow_view.py` and the shared Quality Metrics coexistence harness.)*
- Screening telemetry regression: `.repo_studios/tests/tests_command_center/viewer/test_logging_flow_view.py::test_logging_flow_renders_mermaid_definition` now injects sample screening events and asserts the builder surfaces severity streaks in stats and status messaging.

## Future Enhancements

- Extend normalization to capture logging call arguments (message templates, structured payloads) once upstream emits richer data.
- Feed churn or error-rate overlays into the logging view to prioritize noisy modules.
- Surface absence warnings for modules without logging coverage to guide instrumentation efforts.
- Enrich screening overlays with pack-level tooltips that link recent failures to the corresponding logging buckets.
