# Test Coverage Mapping View Spec

**Status:** Controls wired with targeted regression coverage (2025-11-13)

## Goal

Surface where automated tests touch the codebase by connecting modules, representative low-coverage functions, and the tests exercising them. The view helps auditors spot modules lacking tests, highlight partially covered functions, and prioritize remediation work across the Risk & Assurance pack.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `functions`, `coverageSignals.imports`, `coverageSignals.has_matches` | Supplies module metadata, test import hints, and coverage signal flags captured during normalization. |
| `state.normalizedData.functions` (Map) | `id`, `name`, `moduleId`, `metrics.coverage`, `metrics.lineCount` | Provides per-function coverage ratios and size metrics for highlighting low performers. |
| Scope helper (`resolveTestCoverageScope`) | `rootId`, `domainId`, `moduleId`, `levels` | Determines which modules participate based on the active zoom selection and falls back to repository scope when telemetry is missing. |
| View options | `moduleLimit`, `functionLimit`, `centerLabel`, `scopeDescription`, `fallbackNotice` | Optional overrides supplied by the viewer definition; defaults cap visible modules at six and low-coverage functions at five per module. |

## Transformations

1. Normalize incoming module/function collections into Maps to eliminate array/object ambiguity.
2. For each module, collect function records and derive coverage buckets (`covered`, `partial`, `uncovered`, `unknown`) using coverage thresholds (≥0.85 strong, ≥0.75 caution, ≥0.60 alert).
3. Extract test metadata from module `coverageSignals` (imports + boolean flags) to flag modules with associated suites even when coverage metrics are incomplete.
4. Rank modules by severity (uncovered first, then partial, then coverage gaps) and truncate to the configured module limit.
5. Within each module, select highlight candidates (uncovered/partial/unknown functions) up to the `functionLimit`, capturing coverage percentages and line counts for node labels.
6. Build stats payload summarizing module counts, uncovered/partial function totals, shared thresholds, and overall coverage averages to drive status messaging.
7. Compose Mermaid nodes: a central hub, module nodes (with coverage/test summaries), optional test nodes linking to modules, and function nodes branching from modules. Apply class definitions to align with Risk & Assurance styling (alert/caution/strong/unknown tiers).

## Mermaid Output Structure

```
graph TD
  coverage_center["Test Coverage · scope"]
  module_alpha_core["alpha.core\nCoverage 62%\nFunctions 3 (covered 1, partial 1, uncovered 1, unknown 0)\nTests tests.test_alpha, tests.integration.alpha_suite"]
  coverage_center --> module_alpha_core
  test_tests_test_alpha["Test · tests.test_alpha"]
  test_tests_test_alpha -.-> module_alpha_core
  alpha_core__partial["partial\nCoverage 62%\nLOC 20"]
  module_alpha_core --> alpha_core__partial
  class module_alpha_core moduleCaution;
  class test_tests_test_alpha testNode;
  class alpha_core__partial functionPartial;
```

Module nodes aggregate coverage/test summaries, test nodes use dashed edges, and function nodes display representative low-coverage samples.

## Implementation References

- Builder: `buildTestCoverageMappingDiagram()` in `.repo_studios/command_center/viewer/ui/builders/test_coverage_mapping.js`.
- Viewer wiring: `buildTestCoverageMappingViewDefinition()` and `resolveTestCoverageScope()` within `.repo_studios/command_center/viewer/ui/viewer.js` gate availability on `requirements: ["inventoryBasics", "coverage"]` and apply repository fallbacks.
- Styling: Class definitions (`moduleAlert`, `moduleCaution`, `moduleStrong`, `moduleUnknown`, `functionUncovered`, etc.) reside alongside the builder to maintain consistent Risk & Assurance theming.

## Verification & Hardening

- Builder regression: `.repo_studios/tests/tests_command_center/viewer/test_test_coverage_mapping_view.py` validates empty states, Mermaid generation, stats snapshots, and determinism.
- Viewer wiring regression: `.repo_studios/tests/tests_command_center/viewer/test_test_coverage_mapping_view_definition.py` covers scope fallbacks, repository overrides, and coverage telemetry detection via `moduleHasCoverageTelemetry`.
- Scope helper exports through `viewer.__test__` enable future harnesses (e.g., pack-level coexistence) without duplicating viewer internals.

## Future Enhancements

- Add pack-level coexistence regression once Git Churn and Dead Code views are wired, ensuring toggles preserve definitions and status payloads.
- Thread coverage history or delta metrics into module labels when producers emit trend data.
- Surface test flakiness or failure rate overlays by ingesting future screening artifacts.
- Expose quick filters for modules lacking tests to drive remediation tickets directly from the viewer sidebar.
