# Progressive Detail Mermaid Viewer — Implementation Checklist

## Phase 0 · Charter & Success Measures

- [x] Reconfirm viewer purpose: deliver progressive wiring diagrams that solve clutter and exploration pain points.
  - Revalidated the charter on 2025-11-10, restating that the viewer exists to tame CommandView complexity by sequencing interconnected diagrams so operators can move from portfolio to function-level insights without losing context; documented the reaffirmation here to keep the implementation plan anchored to the original problem statement.
- [x] Capture success criteria: fast comprehension for contractors, Copilot-ready JSON insights, reduced onboarding time, data-informed refactoring.
  - Documented on 2025-11-10 with the following guardrails: (1) 30-minute onboarding target for contractors refreshing inventory context via the viewer, (2) Copilot agents must be able to harvest normalized JSON slices without re-running producers, (3) backlog refinement cadences use viewer overlays to spot refactoring candidates supported by churn/coverage metrics, and (4) charter success hinges on the viewer reducing manual screenshot digests in duplicate remediation reports; retaining these measures here keeps downstream validation tied to the stated outcomes.
- [x] Log charter and owners in governance docs.
  - Captured in the Mermaid decision log on 2025-11-10, linking the reaffirmed charter and four success guardrails to the Command Center maintainers with GitHub Copilot assisting; this closes the Phase 0 governance loop before resuming pack wiring work.

## Phase 1 · Data Supply & Naming

- [x] Keep generator outputs aligned with commandview naming (`<source_folder>_commandview_YYYYMMDD-HHMM.json`).
  - Verified on 2025-11-10 using the Command Center pipeline outputs produced during the Phase 7 regression run; mirrored artifacts under `.repo_studios/command_center/reports/**` continue to follow the `<slug>_commandview_YYYYMMDD-HHMM.json` pattern as enforced by `generate_commandview_inventory.py` after the 2025-11-06 rename logged in the decision record.
- [x] Format selector labels to surface timestamp freshness (derive display value from the slug’s `YYYYMMDD-HHMM` component).
  - Confirmed on 2025-11-10 that the viewer sidebar renders selector entries as `<slug> (YYYY-MM-DD HH:MM UTC)`, reusing the helper exercised by `.repo_studios/tests/tests_command_center/viewer/test_refresh.py::test_refresh_selector_state_groups_and_deduplicates`; no additional wiring required for Phase 1.
- [x] Ensure `generate_commandview_inventory.py` writes mirrored artifacts only under `.repo_studios/command_center/reports/` for viewer discovery, leaving dynamic copies for agents.
  - Mirrored inventories now hard-block custom `--reports-root` values that escape `.repo_studios/command_center/reports`, keeping the viewer discovery scope static (enforced 2025-11-06).
  - Local agent workflows continue to rely on the co-located `<slug>_index/` folders for dynamic experimentation without impacting the viewer scan.
- [x] Validate inventory payload includes `files[].call_graph` with resolved local/imported/builtin edges.
  - Regression `.repo_studios/tests/tests_producers/test_generate_commandview_inventory.py::test_call_graph_resolves_local_and_imported_calls` (last run 2025-11-09) still passes, confirming the CommandView inventory exports the normalized call graph entries required by downstream packs.
- [x] Document viewer expectations for coverage and churn overlays now that inventory emits `files[].coverage`, `files[].git_churn`, and `statistics.coverage`/`statistics.git_churn` aggregates.
  - Documented on 2025-11-10 that Level 0–2 aggregate nodes surface average coverage and churn deltas in status descriptors, while Quality Metrics heatmaps apply severity colors using `metrics.coverage.executed_ratio` and churn percentiles; viewers should expect sidebar summaries to call out modules breaching <60% coverage or falling into the top 20% churn bucket.
- [x] Confirm dependency summaries, callbacks, IO effects, logging, globals, and docstring metadata remain intact for downstream packs.
  - Spot-checked 2025-11-10 using the sample CommandView payload and verified existing regressions (`.repo_studios/tests/tests_producers/test_generate_commandview_inventory.py::test_function_metadata_persists_effects_and_decorators`, `::test_inventory_generates_structured_output`, and `::test_inventory_records_class_bases`) to ensure these fields stay populated for viewer normalization.

## Phase 2 · Discovery & Refresh Pipeline

- [x] Build selector bootstrapper that scans the static reports tree only, filtering JSON that matches the `*_commandview_YYYYMMDD-HHMM.json` slug.
  - Added `build_commandview_selector.py` in the libraries staging area, producing structured payloads (`slug`, `timestamp`, `display_name`, paths) for viewer selection and ignoring screening artifacts.
  - Selector payload exports underpin the upcoming refresh routine; entries are sorted by slug then timestamp so the UI lists the freshest CommandView inventories first.
- [x] Populate selector entries with source folder + timestamp so users can judge freshness at a glance.
  - Selector options now reuse the CommandView display label (`<slug> (YYYY-MM-DD HH:MM UTC)`) so freshness stays visible, covered by `.repo_studios/tests/tests_command_center/viewer/test_refresh.py::test_refresh_selector_state_groups_and_deduplicates` (completed 2025-11-06 by GitHub Copilot).
- [x] Implement refresh button that re-runs discovery, updates selector options, and preserves active context when possible.
  - Added viewer helper `refresh_selector_with_context` that rehydrates selector state, preserves previously active relative paths, falls back to slug, and defaults to the freshest entry when nothing matches; covered by `.repo_studios/tests/tests_command_center/viewer/test_refresh.py::test_refresh_selector_with_context_preserves_relative_path` and `::test_refresh_selector_with_context_falls_back_to_slug` (completed 2025-11-06 by GitHub Copilot).
- [x] Ensure refresh routine deduplicates by slug to avoid double-listing static vs dynamic artifacts.
  - Refresh grouping collapses duplicate relative paths before sorting, with regression coverage in `.repo_studios/tests/tests_command_center/viewer/test_refresh.py::test_refresh_selector_state_groups_and_deduplicates` (completed 2025-11-06 by GitHub Copilot).
- [x] Document refresh workflow in README and add make/CLI recipe to regenerate inventories before viewer launch.
  - Refresh operations now documented in the new "Refresh Workflow" section below, including `make -C .repo_studios command-center COMMAND_CENTER_TARGET=.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py` guidance and manual CLI fallback; operators are pointed to `refresh_selector_with_context` for backend reuse (completed 2025-11-06 by GitHub Copilot).

## Phase 3 · Viewer Core (HTML/JS Shell)

- [x] Scaffold single-page HTML that loads Mermaid.js from CDN and initializes viewer state.
  - Added `.repo_studios/command_center/viewer/ui/index.html`, `viewer.css`, and `viewer.js` providing a single-page shell wired to Mermaid.js with placeholder state initialisation (completed 2025-11-06 by GitHub Copilot).
- [x] Implement JSON loader (local file or static host) that ingests both inventory and screening payloads.
  - Viewer shell now fetches CommandView inventory JSON plus the paired `_commandview_screening_` summary from the static reports mirror (configurable via `window.viewerConfig.reportsBaseUrl`), persisting payloads in memory and hardening error handling when a screening artifact is absent; demo entry points at `scripts_commandview_20251105-2049.json` to exercise the loader (completed 2025-11-06 by GitHub Copilot).
- [x] Normalize data model on load: module registry, function registry, call graph index, metrics cache.
  - Viewer loader now derives module/function registries, call graph indices (runtime + screening edges), and metrics caches when fetching CommandView JSON; normalized data lives in `state.normalizedData` for upcoming LOD rendering (completed 2025-11-06 by GitHub Copilot).
- [x] Guard against duplicate fetch and handle schema-version gating.
  - Viewer caches CommandView payloads per slug/path/timestamp to avoid redundant network requests and validates `schema_version` (currently 2) before normalization, surfacing clear errors when mismatched (completed 2025-11-06 by GitHub Copilot).

## Phase 4 · Level-of-Detail Engine

- [x] Auto-detect hierarchy depth from module paths to define zoom levels (root, domain, module, function, neighborhood).
  - Normalization now emits hierarchy metadata covering root packages, domains, modules, functions, and neighborhood adjacency, providing counts and adjacency lists for subsequent zoom workflows (completed 2025-11-06 by GitHub Copilot).
- [x] Configure five canonical levels:
  - [x] Level 0 Overview — root packages with aggregated import edges.
  - [x] Level 1 Domain — second-level groupings with cross-domain imports.
  - [x] Level 2 File — modules with file-to-file imports.
  - [x] Level 3 Functions — per-module call graph with metrics badges.
  - [x] Level 4 Detail — focal function plus immediate neighbors and annotations.
  - Normalization now produces `state.normalizedData.levels` (Level 0–4) with node/edge aggregates, module call graphs, and function neighborhood snapshots derived from runtime + screening edges (completed 2025-11-06 by GitHub Copilot).
- [x] Wire level selector UI to render the precomputed Level 0-4 slices.
  - Zoom controls now expose Level buttons and context-specific sidebars that swap aggregated root/domain/module graphs, per-module call graphs, and function neighborhood views using cached normalization data (completed 2025-11-06 by GitHub Copilot).
- [x] Maintain thresholds (≈50 nodes) that trigger suggestions to zoom deeper.
  - Viewer now tallies node counts per level and surfaces zoom guidance whenever a diagram exceeds 50 nodes, nudging operators toward deeper levels to reduce clutter (completed 2025-11-06 by GitHub Copilot).

## Phase 5 · Interaction Model

- [x] Implement breadcrumb navigation (e.g., Overview > pkg > module > function).
  - Viewer now renders a breadcrumb rail above the diagram, showing the active root/domain/module/function selections with clickable segments to jump between levels (completed 2025-11-06 by GitHub Copilot).
- [x] Support node click to drill down and breadcrumb/back control to zoom out.
  - Diagram nodes now register click/keyboard handlers that promote the selected root/domain/module/function and advance to the next level, while breadcrumb segments remain clickable for zooming up the hierarchy (completed 2025-11-06 by GitHub Copilot).
- [x] Persist zoom state during refresh when underlying data permits.
  - Viewer caches the active level and hierarchy selections per CommandView artifact (keyed by slug and relative path) and reapplies them after refresh, falling back gracefully if nodes disappear (completed 2025-11-06 by GitHub Copilot).
- [x] Apply color and edge styles (e.g., red for high complexity, dotted for call edges) sourced from inventory metrics.
  - Level 0–2 aggregates now highlight large function clusters with escalating fills/strokes, while Level 3–4 function nodes adopt focus, complexity, and coverage-driven colors and stroke widths; aggregate import edges render with dotted connectors to reinforce their summary nature (completed 2025-11-06 by GitHub Copilot).

## Phase 6 · Rendering & Temp Artifact Strategy

- [x] Generate Mermaid definitions in memory; do not persist `.mmd` files to disk by default.
  - Viewer now caches the active Mermaid definition in `state.diagramDefinition` for in-memory reuse while clearing it whenever diagrams reset or loads fail, avoiding any filesystem writes (completed 2025-11-07 by GitHub Copilot).
- [x] If temporary `.mmd` artifacts are needed for debugging, place them under a dedicated cache directory and overwrite on reuse.
  - Added `.repo_studios/command_center/viewer/cache/` with an ignored `.mmd` policy plus `write_mermaid_cache.py` CLI that overwrites `debug_preview.mmd` (or a sanitized name) on each invocation, purges diagrams older than 24 hours, and caps cache size at five files (completed 2025-11-07 by GitHub Copilot).
- [x] Implement eviction/expiry policy to prevent stale temp views after refresh runs.
  - Cache helper now enforces a configurable TTL (default 24h) and trims to five most recent diagrams so old previews expire automatically (completed 2025-11-07 by GitHub Copilot).
- [x] Add export button that writes the currently rendered Mermaid definition (`.mmd`) to disk on demand (image export remains optional).
  - Header now exposes an `Export .mmd` control that bundles the active slug, level, and timestamp into a sanitized filename and triggers a client-side download using the cached Mermaid definition (completed 2025-11-07 by GitHub Copilot).

## Phase 7 · Selector Views & Packs

- [x] Expose sidebar list of the 28 candidate views curated in the integration checklist, grouped by pack (Health, Dependency, Code Flow, etc.).
- [ ] For each view:
  - [ ] Define required data slice and transforms.
    - [x] Code Flow · Function Call Graph consumes module-level call graph edges via the new view pack prototype.
  - [ ] Wire viewer controls to trigger view-specific Mermaid generation.
    - [x] Code Flow · Function Call Graph buttons toggle a module-scoped call graph diagram without reloading JSON.
  - [ ] Ensure multiple views can coexist (tabbed or multi-panel) without reloading JSON.
- [x] Map Code Flow pack to newly emitted call graph edges.

### View Pack Readiness Tracker

Every pass against a view pack should explicitly update the three shared attributes:

- **D · Data slice ready** — upstream artifacts emit the required fields and normalization paths are documented.
- **C · Controls wired** — sidebar/tab wiring is live so operators can render the view without reloading data.
- **M · Multi-view coexistence & regression** — manual verification + automated coverage ensure toggling between views preserves state and definitions.

- **Health Pack**
  - `function_inventory_overview.mmd`
    - [x] Data slice ready (D) — Documented input mapping and Mermaid transform in `view_specs/function_inventory_overview.md`; hardened builder docstring detection to respect `docstring_quality.exists` (2025-11-08, GitHub Copilot).
    - [x] Controls wired (C) — Sidebar button now routes through `buildFunctionInventoryOverviewDiagram` with live wiring in `viewer.js`, and regression coverage asserts the builder output using the shared Node harness (2025-11-08, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Cross-view regression at `.repo_studios/tests/tests_command_center/viewer/test_health_pack_multi_view_coexistence.py::test_health_pack_builders_coexist_without_state_reset` confirms toggling between Health pack views preserves definitions and status messaging (2025-11-09, GitHub Copilot).
    - Past: Captured the Function Inventory Overview data slice contract and aligned viewer builder logic with the CommandView schema (2025-11-08, GitHub Copilot).
    - Present: Controls expose the overview in the Health pack, with builder logic housed in `ui/builders/function_inventory_overview.js` and regression coverage (builder + coexistence) exercising the wiring.
    - Future: Fold the Health pack coexistence harness into UI-level smoke tests once additional packs land, and extend the same coexistence coverage to Code Flow views.
  - `screening_signal_timeline.mmd`
    - [x] Data slice ready (D) — Screening summary now emits `score_snapshot` + `score_history` blocks from the CommandView producer, unblocking timeline normalization (2025-11-08, GitHub Copilot).
      - Past: Drafted the data contract and identified the missing `score_history` export in CommandView screening payloads.
    - Present: Health pack controls now surface the timeline tab, render docstring coverage slices from normalized history, and coexist with the Code Flow call graph tab without resetting state (validated 2025-11-08 by GitHub Copilot).
  - Future: Expand multi-view regression coverage beyond the Health pack so Dependency and Code Flow packs receive the same treatment as their builders arrive.
    - [x] Instrument screening history emission for timeline view — Added docstring coverage scoring with severity thresholds to the screening artifact (`score_snapshot` ➔ `score_history`) so Health pack timelines can hydrate (2025-11-08, GitHub Copilot).
    - [x] Controls wired (C) — Health pack controls now expose the timeline view tab and surface informative status messaging even when no screening events are present (2025-11-08, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Verified via manual viewer toggles and covered by `.repo_studios/tests/tests_command_center/viewer/test_screening_signal_timeline_view.py::test_screening_timeline_definition_is_stable_across_repeated_calls` to ensure repeated renders keep timeline state intact (2025-11-08, GitHub Copilot).
- **Dependency Pack**
  - `module_dependency_graph.mmd`
    - [x] Data slice ready (D) — Normalized module import edges now flow through `createModuleRecord()` and the dedicated view spec (`view_specs/module_dependency_graph.md`) documents adjacency aggregation, severity thresholds, and status descriptors (2025-11-10, GitHub Copilot).
    - [x] Controls wired (C) — Viewer wiring delegates to `buildModuleDependencyGraphViewDefinition()` which renders Mermaid diagrams via `ui/builders/module_dependency_graph.js`, gating availability on `moduleDependencies` and surfacing stats/status panels (2025-11-10, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Regression suite `.repo_studios/tests/tests_command_center/viewer/test_dependency_pack_multi_view_coexistence.py` keeps dependency and call graph views stable across toggles with deterministic builder output (2025-11-10, GitHub Copilot).
    - Past: Hardened module import normalization to preserve alias metadata, aggregated dependency summaries in the builder, and captured transformation details in `view_specs/module_dependency_graph.md` (2025-11-10, GitHub Copilot).
    - Present: Dependency controls render status-rich diagrams backed by `buildModuleDependencyGraphDiagram()`, with Node-backed regressions (`test_dependency_data_normalization.py`, `test_module_dependency_graph_view.py`) and coexistence coverage confirming stability after the latest alias hardening.
    - Future: Respect scope filters for large repositories, expose module-level churn overlays, and add quick filters for unused imports before promoting the view beyond prototype.
  - `export_contract_matrix.mmd`
    - [x] Data slice ready (D) — Captured the export contract data contract in `view_specs/export_contract_matrix.md` and normalized module records through `buildModuleExportSummary()` so `__all__` symbols classify as local definitions, re-exports, or missing entries with provenance (2025-11-10, GitHub Copilot).
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
    - Past: Hardened module normalization to expose `exportSummary` (declared symbols, counts, provenance) and authored the view spec detailing inputs, transformations, and Mermaid structure, backed by Node-based regression `.repo_studios/tests/tests_command_center/viewer/test_export_contract_data_normalization.py` (2025-11-10, GitHub Copilot).
    - Present: Dependency pack data slice now surfaces alias-preserving export summaries with counts for local vs re-exported symbols; wiring remains pending before operators can render the matrix from the sidebar.
  - Future: Wire viewer controls to a dedicated export contract matrix builder, add coexistence coverage alongside the Module Dependency Graph, and layer churn/coverage overlays onto export status descriptors.
  - `circular_import_detection.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `layer_architecture_validation.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `external_vs_internal_dependency_map.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
- **Event Dynamics Pack**
  - `callback_registration_map.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `dynamic_code_watchlist.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
- **Code Flow Pack**
  - `function_call_graph.mmd`
    - [x] Data slice ready
    - [x] Controls wired
    - [x] Multi-view coexistence verified (M) — Node-backed regression at `.repo_studios/tests/tests_command_center/viewer/test_code_flow_multi_view_coexistence.py` confirms the call graph builder holds state when toggling with Health pack views (2025-11-09, GitHub Copilot).
    - Past: Extracted the call graph diagrammer into `ui/builders/function_call_graph.js` and documented the data slice contract in `view_specs/function_call_graph.md` (2025-11-09, GitHub Copilot).
    - Present: Viewer delegates the Code Flow tab to the shared builder, with deterministic output covered by `.repo_studios/tests/tests_command_center/viewer/test_function_call_graph_view.py` plus the multi-view harness above.
    - Future: Expand the Code Flow regression harness once entrypoint trace and method call chain diagrams arrive so inter-pack coexistence remains guarded.
  - `entrypoint_trace_diagram.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `class_inheritance_hierarchy.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `method_call_chain.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
- **State Effects Pack**
  - `global_variable_usage_map.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `io_effects_diagram.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `exception_flow_map.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
- **Quality Metrics Pack**
  - `complexity_heatmap.mmd`
    - [x] Data slice ready (D) — Complexity metrics (`cyclomatic_complexity`, `metrics.complexity`, `metrics.line_count`) documented in `view_specs/complexity_heatmap.md`, confirming normalized function records expose the required inputs (2025-11-09, GitHub Copilot).
    - [x] Controls wired (C) — Viewer delegates to `buildComplexityHeatmapDiagram()` with `resolveComplexityHeatmapScope()` providing zoom-aware filtering (2025-11-09, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Regression `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py` now exercises Complexity, Type, and Documentation toggles without definition drift (2025-11-09, GitHub Copilot).
    - Past: Captured the complexity heatmap data contract and linked upstream producer coverage that guards cyclomatic metrics (2025-11-09, GitHub Copilot).
  - Present: Builder module `ui/builders/complexity_heatmap.js` now emits severity buckets with churn/coverage overlays, module hotspot stats, scoped helper coverage, and Node-backed regression (`test_complexity_heatmap_view.py`, `test_complexity_heatmap_scope.py`).
  - Future: Thread hotspot summaries into the Command Center sidebar and add tooltip details for line counts, churn history, and coverage trends.
  - `logging_flow.mmd`
    - [x] Data slice ready (D) — Documented logging call normalization in `view_specs/logging_flow.md`, confirming normalized function records expose sanitized `loggingCalls` entries for downstream builders (2025-11-09, GitHub Copilot).
    - [x] Controls wired (C) — Viewer delegates the Logging Flow tab to `buildLoggingFlowViewDefinition()` which scopes via `resolveLoggingFlowScope()` and renders `buildLoggingFlowDiagram()` overlays for severity buckets, line numbers, and logger summaries (2025-11-09, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Node-backed regression `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py` now exercises Logging Flow alongside Type, Documentation, and Complexity views; builder output covered by `.repo_studios/tests/tests_command_center/viewer/test_logging_flow_view.py` with scope filtering guarded in `.repo_studios/tests/tests_command_center/viewer/test_logging_flow_scope.py` (2025-11-09, GitHub Copilot).
    - Past: Captured the logging flow data contract and tied it to normalized function records in the new view spec before wiring UI controls (2025-11-09, GitHub Copilot).
    - Present: Logging Flow buckets aggregate emitters by highest severity, surface per-level event counts, and summarize top modules with call totals and emitter counts for observability auditing.
    - Future: Layer screening insights (e.g., recent error bursts) onto the logging buckets and extend status messaging with alerts for roots or domains lacking emitters.
  - `decorator_usage_map.mmd`
    - [x] Data slice ready (D) — Viewer normalization now exposes sanitized decorator names and detailed argument metadata via `createFunctionRecord()` so downstream builders can group functions without re-reading raw inventory structures (2025-11-09, GitHub Copilot).
    - [x] Controls wired (C) — Quality Metrics controls now delegate to `buildDecoratorUsageMapViewDefinition()` backed by `buildDecoratorUsageMapDiagram()` plus `resolveDecoratorUsageScope()`, with regression coverage in `.repo_studios/tests/tests_command_center/viewer/test_decorator_usage_map_view.py` and `.repo_studios/tests/tests_command_center/viewer/test_decorator_usage_scope.py` (2025-11-10, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Extended `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py` to include the Decorator Usage Map builder, confirming repeated toggles preserve definitions, status messaging, and stats alongside existing Quality Metrics views (2025-11-10, GitHub Copilot).
    - Past: Documented the decorator usage data slice and confirmed inventory exports in `.repo_studios/command_center/docs/mermaid/view_specs/decorator_usage_map.md`, extending viewer normalization to hydrate `decorators`/`decoratorsDetailed` (2025-11-09, GitHub Copilot).
  - Present: Decorator metadata now powers the wired Quality Metrics tab through `ui/builders/decorator_usage_map.js` and `ui/builders/decorator_usage_scope.js`, with deterministic Node-backed builders scoped by the new tests above, coexistence guaranteed via the refreshed Quality Metrics regression, and normalization guarded by `.repo_studios/tests/tests_command_center/viewer/test_decorator_data_normalization.py`.
  - Future: Expand policy coverage by surfacing module-level gap summaries and integrating decorator policy metadata once other packs consume decorator signals.
  - `public_vs_private_api.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `cyclomatic_complexity_map.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `type_coverage_map.mmd`
    - [x] Data slice ready (D) — Coverage ratios (`type_hint_coverage`, `annotation_coverage`, `metrics.coverage`) documented in the new `view_specs/type_coverage_map.md` and confirmed available in normalized function records (2025-11-09, GitHub Copilot).
    - [x] Controls wired (C) — Viewer delegates to `buildTypeCoverageMapDiagram()` with the shared builder module, now filtered by `ui/builders/type_coverage_scope.js`, and exposes the Quality Metrics tab without reloading JSON (2025-11-09, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Updated regression `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py` confirms Type Coverage and Documentation Coverage views alternate without definition or status drift (2025-11-09, GitHub Copilot).
    - Past: Captured the Type Coverage Map contract and extracted builder logic to `ui/builders/type_coverage_map.js` (2025-11-09, GitHub Copilot).
  - Present: Node-backed tests guard deterministic builder output in `.repo_studios/tests/tests_command_center/viewer/test_type_coverage_map_view.py`, zoom scoping in `.repo_studios/tests/tests_command_center/viewer/test_type_coverage_scope.py`, and coexistence alongside Complexity/Documentation in the shared Quality Metrics harness.
    - Future: Extend the map to surface coverage percentages per module and blend churn signals once additional metrics arrive in normalization.
  - `documentation_coverage_map.mmd`
    - [x] Data slice ready (D) — Documented docstring quality status mapping in `view_specs/documentation_coverage_map.md`, reusing normalized `docstringQuality` blocks emitted by the inventory (2025-11-09, GitHub Copilot).
    - [x] Controls wired (C) — Viewer registers `buildDocumentationCoverageMapDiagram()` and wires the Quality Metrics sidebar to render the diagram without reloading payloads (2025-11-09, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Regression `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py` exercises repeated toggles between Type Coverage and Documentation Coverage tabs while preserving state and stats (2025-11-09, GitHub Copilot).
    - Past: Drafted the view spec, aligned builder inputs with normalized docstring quality metadata, and extracted reusable helpers in `ui/builders/documentation_coverage_map.js` (2025-11-09, GitHub Copilot).
    - Present: Deterministic builder output covered by `.repo_studios/tests/tests_command_center/viewer/test_documentation_coverage_map_view.py`, zoom-aware scope filtering validated via `.repo_studios/tests/tests_command_center/viewer/test_documentation_coverage_scope.py`, and coexistence protection maintained in the shared Quality Metrics harness.
    - Future: Enrich labels with docstring freshness timestamps and extend stats to surface stale documentation severity once normalization exposes the fields.
- **Coupling Insight Pack**
  - `cross_module_function_references.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `import_chain_depth.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
- **Risk & Assurance Pack**
  - `test_coverage_mapping.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `git_churn_risk_map.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified
  - `dead_code_detection.mmd`
    - [ ] Data slice ready
    - [ ] Controls wired
    - [ ] Multi-view coexistence verified

## Phase 8 · UX Enhancements

- [ ] Add metrics-driven overlays (line count, complexity, IO effects) at relevant zoom levels.
- [ ] Provide node count warnings when thresholds exceeded.
- [ ] Offer optional search input to jump to module/function.
- [ ] Consider URL parameters for sharing current zoom state.
- [ ] Confirm selector, refresh, and export interactions are reflected in UI smoke tests and documented operator notes.

## Phase 9 · Extension Hooks

- [ ] Design API surface for future features: side-by-side comparisons, live refresh on file change, metric filters, path tracing, static export.
- [ ] Keep architecture modular so packs can add transforms without touching core rendering.

## Phase 10 · Quality & Governance

- [ ] Write unit tests for data loaders, selector filters, and zoom computations.
- [ ] Create integration smoke test that loads sample inventory and renders each pack once.
- [ ] Document operator playbook covering refresh command, troubleshooting, and artifact retention.
- [ ] Track outstanding gaps (e.g., cyclomatic complexity, coverage overlays) in the integration checklist backlog.

---

Status note (2025-11-10): Selector payload now surfaces slug+timestamp labels, deduplicates static mirrors, backend refresh helpers preserve active context, the HTML shell with Mermaid wiring is live, JSON loader plus normalization populate registries/caches, duplicate fetch/schema gating keeps loads deterministic, hierarchy metadata and Level 0-4 data slices are ready for rendering, level node thresholds now prompt deeper zoom when diagrams exceed 50 nodes, breadcrumb/navigation interactions keep zoom flows snappy, refresh cycles now restore the prior zoom level whenever the slug persists, the viewer applies metrics-driven node/edge styling across levels, Mermaid definitions stay in-memory via `state.diagramDefinition` with no default `.mmd` output, debugging exports route through `.repo_studios/command_center/viewer/cache/write_mermaid_cache.py` with 24-hour TTL and five-file retention, the UI now offers an `Export .mmd` button for on-demand downloads, the sidebar lists all 28 curated view packs, the Health pack Function Inventory Overview and Screening Signal Timeline views are selectable from the sidebar and render via their shared builder modules and regression harnesses, the Code Flow · Function Call Graph view now relies on the dedicated builder module with Node-backed regression plus multi-view coexistence coverage guarding Health ↔ Code Flow toggles, the Dependency pack Module Dependency Graph now renders from normalized import edges with alias preservation and coexists alongside the Function Call Graph, the Export Contract Matrix data slice is documented with alias-aware `exportSummary` metadata awaiting UI wiring, the Quality Metrics pack includes Type Coverage and Documentation Coverage builders with deterministic tests, zoom-aware scope filtering, and coexistence coverage guarding intra-pack toggles, and the Decorator Usage Map now threads required-annotation alerts into status messaging alongside dedicated regressions and updated Quality Metrics coexistence coverage. Pack overlays and advanced rendering remain upcoming (future).

## Viewer Shell Assets

- `index.html`: Hosts the viewer container, refresh trigger, and selector scaffold tied to Mermaid.js.
- `viewer.css`: Provides baseline theming for the dark-mode layout used during prototyping.
- `viewer.js`: Initialises Mermaid, seeds demo selector data, and renders placeholder diagrams until real loaders arrive.

## Refresh Workflow

1. **Regenerate CommandView artifacts** (present):

    - Preferred: `make -C .repo_studios command-center COMMAND_CENTER_TARGET=.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py PYTHON=.venv/Scripts/python.exe -- --repo-root . --log-level INFO`.
    - Direct CLI: `C:/Users/genet/repo_studios/.venv/Scripts/python.exe .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py .repo_studios/command_center/scripts --repo-root . --log-level INFO`.

2. **Invoke viewer refresh backend** (present):call `refresh_selector_with_context(repo_root, active_relative_path=..., active_slug=...)` to rebuild selector state while preserving operator context.

3. **Launch UI prototype** (future): upcoming HTML shell will call the helper to hydrate controls; document updates will follow once the UI wiring step completes.
