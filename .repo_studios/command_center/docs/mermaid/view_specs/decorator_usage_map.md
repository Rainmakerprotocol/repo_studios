# Decorator Usage Map View Spec

**Status:** Data slice documented and normalized (2025-11-09)

## Goal

Cluster functions by decorator usage so maintainers can audit annotation patterns, confirm policy-enforced decorators are present, and spot modules that overuse or lack critical decorators during reviews.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.functions` (Map) | `decorators`, `decoratorsDetailed`, `moduleId`, `name`, `id`, `loggingCalls`, `metrics.lineCount` | Primary catalogue of functions with sanitized decorator metadata and supporting context for labels and summaries. |
| `state.normalizedData.modules` (Map) | `moduleId`, `functions` | Provides per-module groupings so the view can surface decorator patterns by package or module. |
| View options | `bucketLimit`, `viewLabel`, `centerLabel`, `focusDecorator` | Optional overrides that will govern bucket sizing, labeling, and filtering once the builder is wired. |

### Upstream Guarantees

- `generate_commandview_inventory.py` emits `decorators` (string list) and `decorators_detailed` (structured objects) for every function, method, and class; regression coverage lives in `.repo_studios/tests/tests_producers/test_generate_function_inventory.py::test_function_metadata_persists_effects_and_decorators`.
- Viewer normalization now hydrates `decorators` and sanitized `decoratorsDetailed` via `createFunctionRecord()` in `viewer.js`, ensuring the data slice is available to downstream builders without additional parsing.

## Transformations (Planned)

1. Use the shared scope helpers to resolve the active function set (repository, root, domain, module, or neighborhood) before aggregation.
2. Group decorators into buckets by qualified name, policy tag, or configured focus list, counting distinct emitters and total applications per decorator.
3. Derive per-module summaries that highlight hotspots (e.g., modules with the most policy decorators, modules missing expected decorators).
4. Generate Mermaid nodes for top decorators, listing representative functions (with module suffixes) and truncating to the configured bucket limit.
5. Compute supporting stats: number of decorated functions, undecorated functions, top decorators by usage, and modules lacking required annotations.
6. Thread complementary context (e.g., logging emitters, function line counts) into labels so reviewers can prioritize large or high-impact functions when auditing decorators.

## Implementation References

- Normalization: `createFunctionRecord()` plus helper functions (`normalizeDecorators`, `normalizeDecoratorDetails`) in `.repo_studios/command_center/viewer/ui/viewer.js`.
- Inventory extraction: decorator metadata is persisted by `.repo_studios/command_center/scripts/producers/generate_commandview_inventory.py` during AST traversal.
- Upcoming builder: will live in `.repo_studios/command_center/viewer/ui/builders/decorator_usage_map.js`, mirroring existing Quality Metrics patterns.

## Verification & Hardening

- Producer-level regression: `.repo_studios/tests/tests_producers/test_generate_function_inventory.py::test_function_metadata_persists_effects_and_decorators` confirms decorators are captured for functions, classes, and methods.
- Viewer normalization regression: `.repo_studios/tests/tests_command_center/viewer/test_decorator_data_normalization.py::test_create_function_record_normalizes_decorators` verifies sanitized decorator names, arguments, and kwargs are exposed to the UI layer.
- Future builder work will add Node-backed diagram tests once the Mermaid transformer is implemented.

## Future Enhancements

- Capture decorator origin metadata (e.g., internal vs third-party) to allow risk-aware grouping in the diagram.
- Surface decorator argument tooltips so reviewers can inspect policy parameters without leaving the view.
- Introduce policy configuration integration to flag modules missing required decorators or using deprecated annotations.
