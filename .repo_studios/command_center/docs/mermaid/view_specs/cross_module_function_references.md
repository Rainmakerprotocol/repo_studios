# Cross-Module Function References View Spec

````markdown

**Status:** Multi-view coexistence verified with regression coverage (2025-11-12)

## Goal

Highlight inter-module coupling by visualising function calls that cross module boundaries. The diagram helps operators and reviewers pinpoint hotspots where modules depend on each other, quantify the direction and volume of those interactions, and prioritise refactoring or boundary hardening.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `functions` | Establishes available modules and associates function identifiers with each module. |
| `state.normalizedData.functions` (Map) | `moduleId` | Resolves the owning module for every function node referenced in the call graph. |
| `state.normalizedData.callGraph.functions` (Map) | `sourceId -> [targetIds]` | Supplies the normalized call graph emitted by the CommandView inventory (schema v2) so cross-module edges can be derived. |
| View scope selections | `rootId`, `domainId`, `moduleId` | Used to focus on a specific module, domain, or root package. When a scoped selection yields no coupling edges the view falls back to a repository-wide snapshot with an info notice. |

## Transformations

1. Convert module, function, and call graph payloads into deterministic `Map` structures for ordered iteration.
2. Walk the call graph and collect unique `(source function → target function)` edges where the owning modules differ. Deduplicate per function pair to avoid inflating counts.
3. Aggregate module-level statistics capturing outbound/inbound call counts, distinct partner modules, and participating function counts; classify modules into base/caution/alert tiers using configurable thresholds (≥10 total cross-module calls triggers alert styling, ≥5 triggers caution styling).
4. Filter aggregated edges against scoped selections when the operator is focused on a domain or module, retaining edges where either endpoint matches the focus set.
5. Generate Mermaid-safe node identifiers, compose multiline node labels showing outbound and inbound summaries, and render directional edges labelled with call and function participation counts.
6. Build status metadata (stat summary, top couplings, top outbound modules, top inbound modules) and compose a contextual status message that includes module, edge, and call counts. Apply scope fallback notices when repository-level data is shown in place of an empty scoped selection.

## Mermaid Output Structure

```
graph LR
  classDef moduleBase fill:#0f172a,stroke:#38bdf8,color:#f8fafc
  classDef moduleCaution fill:#78350f,stroke:#f59e0b,color:#fef3c7
  classDef moduleAlert fill:#7f1d1d,stroke:#f87171,color:#fee2e2
  classDef moduleFocus stroke:#22d3ee,stroke-width:3px,color:#e0f2fe
  alpha_core["alpha.core\n3 outbound calls → 2 modules\n1 inbound call ← 1 module"]
  class alpha_core moduleCaution;
  beta_utils["beta.utils\n1 outbound call → 0 modules\n3 inbound calls ← 2 modules"]
  class beta_utils moduleAlert;
  alpha_core -->|2 calls\n1 src → 1 dest| beta_utils
```

Nodes reflect module-level coupling intensity. Labels include outbound and inbound summaries, while edges display call counts and participating function spans. Scoped selections add a `moduleFocus` stroke class to highlight targeted modules.

## Implementation References

- Builder: `buildCrossModuleFunctionReferencesDiagram()` in `.repo_studios/command_center/viewer/ui/builders/cross_module_function_references.js`.
- View wiring: `buildCrossModuleFunctionReferencesViewDefinition()` in `.repo_studios/command_center/viewer/ui/viewer.js`, registered under `crossModuleFunctionReferencesView` within the Coupling Insight pack.
- Availability gating: `findViewRequirementIssue()` leverages existing `inventoryBasics` and `callGraph` checks to ensure normalized modules, functions, and call graph edges are present before enabling the view.

## Verification & Hardening

- Builder regression: `.repo_studios/tests/tests_command_center/viewer/test_cross_module_function_references_view.py` validates Mermaid output, stats snapshots, scope filtering behaviour, and empty-state messaging.
- Multi-view coexistence: `.repo_studios/tests/tests_command_center/viewer/test_coupling_pack_multi_view_coexistence.py` exercises the coupling view alongside the Function Call Graph builder to guarantee deterministic definitions across repeated toggles.
- The builder exports `__test__` hooks for helper-level coverage should deeper unit testing be required during future refactors.

## Future Enhancements

- Introduce threshold configuration (via viewer options or settings) so teams can tune caution/alert cut-offs to repository size.
- Blend churn and coverage overlays into node labels once those metrics are threaded into module stats.
- Add optional grouping that collapses modules to domain-level aggregates when the coupling graph becomes dense.
- Surface remediation cues in status details (e.g., highlight bidirectional couplings or long call chains spanning multiple modules).
````
