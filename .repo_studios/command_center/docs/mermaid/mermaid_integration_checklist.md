# Mermaid Integration Checklist (Draft)

## Candidate Mermaid Packs Derived From `generate_function_inventory.py`

- **Health Pack**
  1. `function_inventory_overview.mmd` — flowchart summarizing per-module function counts, docstring coverage, and annotation ratios for a quick health read.
  2. `screening_signal_timeline.mmd` — timeline chart outlining when screening scores crossed thresholds, supporting release planning discussions.
- **Dependency Pack**
  3. `module_dependency_graph.mmd` — import dependency graph showing which files import which files to highlight hotspots and orphan modules (data available via dependency summaries).
  4. `export_contract_matrix.mmd` — class diagram portraying public exports and their categories (functions, classes) to validate API boundaries.
  5. `circular_import_detection.mmd` — graph emphasizing import cycles that could cause module loading issues; cycles can be derived from the existing dependency graph output.
  6. `layer_architecture_validation.mmd` — layered diagram validating Producers → Consumers → Aggregators → Orchestrators → Summarizers wiring; relies on file paths already present in inventory, plus a static tier map in the renderer.
  7. `external_vs_internal_dependency_map.mmd` — dependency map separating standard library, third-party, and local modules to surface external attack surfaces. *Needs inventory enhancement: extend `dependency_summary` in `generate_function_inventory.py` to emit counts keyed by `standard_library`, `third_party`, and `internal` modules before this view is viable.*
- **Event Dynamics Pack**
  8. `callback_registration_map.mmd` — sequence or state-style diagram tracing detected callback registrations to their emitters for reviewing event-driven surfaces.
  9. `dynamic_code_watchlist.mmd` — block diagram flagging modules where dynamic execution was detected, linking to the responsible constructs for audit follow-up.
- **Code Flow Pack**
  10. `function_call_graph.mmd` — directed graph of which functions call which functions; *requires new inventory emission capturing inter-function call data during AST walk.*
  11. `entrypoint_trace_diagram.mmd` — flow diagram expanding from CLI entrypoints (e.g., `main()` or `run()`) to all reachable functions; *depends on the same call graph data plus a curated list of entrypoint functions.*
  12. `class_inheritance_hierarchy.mmd` — class diagram showing inheritance relationships; *needs inventory augmentation to list base classes per class definition.*
  13. `method_call_chain.mmd` — sequence diagram highlighting object method call chains (Object.method1 → Object.method2 → Object.method3); *requires richer call tracing including bound method targets not currently tracked in the inventory.*
- **State Effects Pack**
  14. `global_variable_usage_map.mmd` — bipartite or flow diagram showing which functions read or write specific globals, leveraging the existing `used_globals` signals to surface shared state.
  15. `io_effects_diagram.mmd` — annotated graph mapping functions to file/network/environment interactions, driven by the `io_effects` metadata already emitted by the inventory.
  16. `exception_flow_map.mmd` — flow visualization of which functions raise which exceptions, using the existing `raises` collection to highlight error propagation paths.
- **Quality Metrics Pack**
  17. `complexity_heatmap.mmd` — heatmap-style visualization coloring functions by derived complexity scores (combine `line_count`, branch counts, and call counts already available in the inventory).
  18. `logging_flow.mmd` — diagram showing which functions emit logs at which levels, powered by the existing `logging_calls` dataset to gauge observability coverage.
  19. `decorator_usage_map.mmd` — graph clustering functions by decorator usage (`@dataclass`, `@property`, etc.), leveraging the decorator metadata already captured during AST analysis.
  20. `public_vs_private_api.mmd` — interface map contrasting externally exposed functions/classes versus internal helpers using the `is_private` signal for API surface assessment.
  21. `cyclomatic_complexity_map.mmd` — visualization using industry-standard McCabe complexity; *needs inventory enhancement to calculate and emit `cyclomatic_complexity` per function within `generate_function_inventory.py`.*
  22. `type_coverage_map.mmd` — chart highlighting which functions include type hints, using the existing annotation ratio metrics to surface gaps in static typing adoption.
  23. `documentation_coverage_map.mmd` — diagram portraying docstring presence and quality scores, leveraging the docstring coverage data already emitted in the screening summary.
- **Coupling Insight Pack**
  24. `cross_module_function_references.mmd` — edge map showing when functions in one file call functions in another, highlighting inter-module coupling; *requires the planned function call graph data plus module association for each node.*
  25. `import_chain_depth.mmd` — layered view illustrating import hop counts from the standard library through third-party packages into project modules; *once dependency classification enhancement (standard_library vs third_party vs internal) lands, derive depth metrics during rendering.*
- **Risk & Assurance Pack**
  26. `test_coverage_mapping.mmd` — bipartite graph connecting tests in `tests/` to exercised functions; *requires new cross-artifact mapping (e.g., ingest coverage.json) because the inventory alone does not record test relationships.*
  27. `git_churn_risk_map.mmd` — risk heatmap combining git change frequency with complexity signals; *needs integration with git history metrics (e.g., `git log --stat`) before visualization is possible.*
  28. `dead_code_detection.mmd` — diagram isolating functions never invoked and unused imports; *depends on the future call graph emission plus additional usage analysis to mark unreachable code paths.*

## Draft Checklist Spine

1. Confirm the latest inventory and screening JSON artifacts (target and central mirrors) are in place.
2. Select the `.mmd` variant(s) required for the review cycle and capture input parameters.
3. Transform the relevant JSON metrics into Mermaid-ready node and edge sets.
4. Render the Mermaid diagram locally for visual inspection.
5. Store the generated `.mmd` file alongside the run metadata for traceability.
6. Log outstanding visualization gaps for the next refinement pass.

## Open Items for Future Passes

- Validate whether additional metrics (complexity, TODO density) should inform future Mermaid views.
- Decide on naming conventions and retention policy for generated `.mmd` artifacts.
- Determine automation touchpoints within the Command Center orchestrators to produce diagrams on demand.
- Capture review cadence and stakeholder sign-off requirements before integrating into the formal checklist.

---

*This draft seeds exploration of Mermaid capacity. We will iterate on structure, acceptance criteria, and automation hooks before formalizing the integration checklist.*

## Producer Enhancements Checklist

- [x] Add dependency classification buckets (`standard_library`, `third_party`, `internal`) to the `dependency_summary` output. *(Completed 2025-11-05: `_dependency_category` now emits `internal`, `standard_library`, `third_party`, and the summary seeds `DEPENDENCY_SUMMARY_BUCKETS` for consistent reporting.)*
- [x] Emit inter-function call edges during the AST walk for each module. *(Completed 2025-11-05: `_build_call_graph()` now emits per-module `call_graph` blocks with resolved local/imported/builtin edges, and regression coverage lives in `.repo_studios/tests/tests_producers/test_generate_function_inventory.py::test_call_graph_resolves_local_and_imported_calls`.)*
  - Past: Serialized `call_graph.edges` with resolution metadata (`local_function`, `local_method`, `imported`, `builtin`) and exposed summaries for downstream viewers.
  - Present: Monitoring downstream consumers while we prep base-class capture to unlock richer path visualizations.
  - Future: Feed the viewer adapters once commandview artifacts adopt the new slug and reference schema version 2+.
- [ ] Record base classes for every class definition in the analysis payload. *(Diff hint: extend class visitor logic to serialize `node.bases` via `_safe_unparse`.)*
- [ ] Capture method-to-method call chains including bound method targets. *(Diff hint: resolve attribute calls (`ast.Attribute`) to owning class/function before storing in the call graph structure.)*
  - [ ] Sub-step: Extend resolver to follow chained attributes (e.g., `self.service.run`) once service-object discovery is defined.
- [ ] Compute cyclomatic complexity per function and attach as `cyclomatic_complexity`. *(Diff hint: add a helper that counts decision points (`if`, `for`, `while`, `try`, `and`, `or`) and integrate within function analysis.)*
- [ ] Surface per-function type hint coverage (already collected ratios) in a dedicated field for visualization. *(Diff hint: ensure `annotation_ratio` is propagated in the serialized JSON; no structural change needed.)*
- [ ] Surface docstring quality metrics alongside coverage data for downstream rendering. *(Diff hint: confirm `docstring_quality` block is part of each function record; export if missing.)*
- [ ] Persist `used_globals`, `io_effects`, `raises`, `logging_calls`, and decorator metadata in consistent top-level keys for consumption. *(Diff hint: revisit serialization to guarantee these collections are emitted unaltered.)*
- [ ] Capture unused imports and unreachable functions to support dead code mapping. *(Diff hint: integrate the planned call graph with per-module symbol tables to flag never-invoked functions and orphaned imports.)*
- [ ] Integrate optional coverage artifacts (e.g., `coverage.json`) to map tests to functions. *(Diff hint: add CLI flag to ingest external coverage data and merge into the serialized inventory structure.)*
- [ ] Thread git churn metrics into the inventory (lines changed, commit frequency). *(Diff hint: introduce a post-processing step that shells out to `git log --stat` and summarizes per-file churn stats.)*
- [ ] Add accompanying unit and integration tests under `.repo_studios/tests/tests_command_center/producers` to cover each new data field and confirm JSON schema stability.
- [ ] Update developer documentation (e.g., `.repo_studios/command_center/docs/` and relevant READMEs) describing new metrics, file naming, and expected consumer behaviour.
- [ ] Record migration notes outlining how downstream tools should adapt to the enriched inventory payload.
- **CommandView Transition (Planned)**
  - [ ] Adopt the new artifact naming pattern `<source_folder>_commandview_YYYYMMDD-HHMM.json` for both target and mirrored outputs. *(Diff hint: update `write_report_artifacts()` invocation in `generate_function_inventory.py` to build filenames with the new slug.)*
  - [ ] Rename `generate_function_inventory.py` to `generate_commandview_inventory.py` and update all imports, CLI entry points, Makefile targets, and orchestrator references accordingly. *(Diff hint: adjust module path exports and ensure tests import the new module name.)*
  - [ ] Limit viewer discovery scope to `.repo_studios/command_center/reports/**` while retaining dynamic artifacts for local agent workflows. *(Diff hint: document the scope in the viewer README and ensure automation respects the static directory boundary.)*
  - [ ] Create regression tests ensuring both static and dynamic output locations remain synchronized post-renaming.
  - [ ] Update orchestration and developer docs to reference the new commandview terminology and filename convention.
