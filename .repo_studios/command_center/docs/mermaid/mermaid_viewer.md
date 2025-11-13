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
    - Future: Fold the Health pack coexistence harness into UI-level smoke tests once additional packs land, extend the same coexistence coverage to Code Flow views, and add a Risk & Assurance pack harness once Git Churn and Dead Code diagrams wire up alongside Test Coverage Mapping.
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
    - [x] Controls wired (C) — Viewer delegates Export Contract Matrix tab activations to `buildExportContractMatrixViewDefinition()` which applies scope filters, propagates fallback notices, and renders Mermaid diagrams via `ui/builders/export_contract_matrix.js` (2025-11-10, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Updated regression `.repo_studios/tests/tests_command_center/viewer/test_dependency_pack_multi_view_coexistence.py::test_export_contract_matrix_coexists_with_dependency_view` confirms repeated toggles between the export matrix and module dependency diagrams preserve definitions, status messaging, and stats (2025-11-10, GitHub Copilot).
    - Past: Hardened module normalization to expose `exportSummary` (declared symbols, counts, provenance), removed the invalid Mermaid `classDef` block after the renderer rejection surfaced, and authored the view spec detailing inputs, transformations, and status messaging, backed by Node-based regression `.repo_studios/tests/tests_command_center/viewer/test_export_contract_data_normalization.py` (2025-11-10, GitHub Copilot).
    - Present: Dependency pack controls now expose the Export Contract Matrix with scope-aware fallback messaging, deterministic builder output, and coexistence coverage ensuring dependency and export diagrams stay stable during toggles; tests stub builder logging to keep regressions noise-free (2025-11-10, GitHub Copilot).
  - Future: Layer churn/coverage overlays onto export status descriptors, surface re-export provenance links within the viewer sidebar, and add tooltip drill-down once sidebar detail panes arrive.
  - `circular_import_detection.mmd`
    - [x] Data slice ready (D) — Documented the circular import data contract in `view_specs/circular_import_detection.md`, outlining how `dependencySummary.graphs.imports` and normalized `importEdges` feed SCC analysis with scope-aware fallbacks (2025-11-10, GitHub Copilot).
    - [x] Controls wired (C) — Viewer delegates Circular Import Detection rendering to `buildCircularImportDetectionViewDefinition()` which scopes modules via level selections, applies Tarjan SCC analysis, and triggers repository fallback messaging when scoped cycles are absent (2025-11-10, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Regression `.repo_studios/tests/tests_command_center/viewer/test_circular_import_detection_view.py::test_circular_import_detection_coexists_with_dependency_view` confirms repeated toggles between the cycle diagram and Module Dependency Graph remain deterministic (2025-11-10, GitHub Copilot).
    - Past: Captured module-level graph requirements, defined Tarjan/Kosaraju-driven cycle derivation, and noted status/fallback expectations in the new view spec (2025-11-10, GitHub Copilot).
    - Present: Dependency pack cycles render through the dedicated builder with scoped filtering, fallback notices, and deterministic stats powering the viewer sidebar; coexistence coverage now guards interactions with the dependency graph.
    - Future: Layer churn or coverage overlays onto cycle stats, surface per-cycle remediation guidance in status details, and explore exporting cycle definitions for duplicate remediation workflows.
  - `layer_architecture_validation.mmd`
    - [x] Data slice ready (D) — Documented the layer validation data contract in `view_specs/layer_architecture_validation.md` and normalized module records with `layerTier`, `layerLabel`, and `layerIndex` metadata derived from the static tier map (2025-11-10, GitHub Copilot).
    - [x] Controls wired (C) — Viewer delegates the Layer Architecture Validation tab to `buildLayerArchitectureValidationViewDefinition()` which injects `evaluateLayerTransition` and threads fallback notices when scoped selections lack coverage (2025-11-11, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Regression `.repo_studios/tests/tests_command_center/viewer/test_dependency_pack_multi_view_coexistence.py::test_layer_architecture_validation_coexists_with_dependency_view` guards repeated toggles with the Module Dependency Graph and Export Contract Matrix (2025-11-11, GitHub Copilot).
    - Past: Captured the Producers → Consumers → Aggregators → Orchestrators → Summarizers requirements, added regression coverage that locks the tier classifier for canonical script paths, and implemented the layered builder/stat blocks in `ui/builders/layer_architecture_validation.js` with documentation updates to `view_specs/layer_architecture_validation.md` (2025-11-10 to 2025-11-11, GitHub Copilot).
    - Present: Dependency pack controls render tiered Mermaid diagrams that highlight adjacency violations, surface stats/warnings, and reuse repository fallbacks while coexistence tests keep dependency views stable.
    - Future: Extend tier summaries with churn/coverage overlays, add remediation guidance to status details, and document operator overrides for custom adjacency policies.
  - `external_vs_internal_dependency_map.mmd`
    - [x] Data slice ready (D) — Documented the dependency mix contract in `view_specs/external_vs_internal_dependency_map.md` and confirmed normalized module records expose categorized `importEdges` plus per-bucket `dependencySummary` counts (2025-11-11, GitHub Copilot).
    - [x] Controls wired (C) — Viewer now delegates to `buildExternalVsInternalDependencyMapViewDefinition()` which scopes selections, applies repository fallbacks, and renders diagrams through `buildExternalVsInternalDependencyMapDiagram()` (2025-11-11, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Added Node-backed regression `.repo_studios/tests/tests_command_center/viewer/test_external_vs_internal_dependency_map_view.py` plus Dependency pack coexistence coverage `.repo_studios/tests/tests_command_center/viewer/test_dependency_pack_multi_view_coexistence.py::test_external_dependency_map_coexists_with_dependency_view` to ensure toggling with the Module Dependency Graph remains stable (2025-11-11, GitHub Copilot).
    - Past: Authored the data slice spec, extended normalization coverage for dependency categories, and prepared the wiring plan for the new builder (2025-11-11, GitHub Copilot).
    - Present: Dependency pack controls render the External vs Internal Dependency Map with deterministic builder output, scope-aware fallbacks, and coexistence tests guarding repeated toggles with other dependency views.
    - Future: Overlay churn/coverage signals on the dependency mix, surface license metadata for third-party buckets, and explore diff mode once successive CommandView snapshots are compared.
- **Event Dynamics Pack**
  - `callback_registration_map.mmd`
    - [x] Data slice ready (D) — Captured the callback registration schema, normalized module/function records via `normalizeCallbackRegistrations()`, and documented the contract in `view_specs/callback_registration_map.md` with regression coverage (2025-11-11, GitHub Copilot).
    - [x] Controls wired (C) — Viewer wiring now delegates to `buildCallbackRegistrationMapViewDefinition()` which scopes selections, applies repository fallbacks, and renders diagrams via `ui/builders/callback_registration_map.js`, with regression coverage in `.repo_studios/tests/tests_command_center/viewer/test_callback_registration_map_view.py` (2025-11-11, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Regression `.repo_studios/tests/tests_command_center/viewer/test_event_dynamics_multi_view_coexistence.py::test_callback_registration_map_coexists_with_function_call_graph_view` confirms toggling between the Callback Registration Map and Function Call Graph views preserves definitions, status messaging, and stats (2025-11-11, GitHub Copilot).
    - Past: Documented the callback registration data slice, exposed sanitized emitters/targets through viewer normalization, and added regression coverage to lock the schema (2025-11-11, GitHub Copilot).
    - Present: Event Dynamics controls render the Callback Registration Map with scope-aware fallbacks, emitter/target stats, deterministic builder output, and coexistence coverage guarding toggles alongside the Function Call Graph view.
    - Future: Extend the Event Dynamics coexistence harness as additional views (e.g., Dynamic Code Watchlist) land and layer risk overlays (e.g., unresolved target alerts) once supplemental metrics arrive.
  - `dynamic_code_watchlist.mmd`
    - [x] Data slice ready (D) — Documented the dynamic code normalization contract in `view_specs/dynamic_code_watchlist.md` and exposed `normalizeDynamicCode()` outputs on module/function records (2025-11-11, GitHub Copilot).
    - [x] Controls wired (C) — Viewer toggles now delegate to `buildDynamicCodeWatchlistViewDefinition()` which scopes selections, applies repository fallbacks, and renders diagrams via `ui/builders/dynamic_code_watchlist.js` (2025-11-11, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Regression `.repo_studios/tests/tests_command_center/viewer/test_event_dynamics_multi_view_coexistence.py::test_dynamic_code_watchlist_coexists_with_callback_registration_map` guards toggles between Dynamic Code Watchlist and Callback Registration Map views (2025-11-11, GitHub Copilot).
    - Past: Captured the dynamic code watchlist data slice, normalized flag/event payloads, and authored the view spec alongside Node-backed regression coverage (2025-11-11, GitHub Copilot).
    - Present: Event Dynamics controls render the Dynamic Code Watchlist with scope-aware fallbacks, stats summaries, and deterministic builder output backed by `ui/builders/dynamic_code_watchlist.js`.
    - Future: Extend Event Dynamics regressions as new views arrive, add severity overlays for risky patterns, and surface remediation cues once producer metrics land.
- **Code Flow Pack**
  - `function_call_graph.mmd`
    - [x] Data slice ready
    - [x] Controls wired
    - [x] Multi-view coexistence verified (M) — Node-backed regression at `.repo_studios/tests/tests_command_center/viewer/test_code_flow_multi_view_coexistence.py` confirms the call graph builder holds state when toggling with Health pack views (2025-11-09, GitHub Copilot).
    - Past: Extracted the call graph diagrammer into `ui/builders/function_call_graph.js` and documented the data slice contract in `view_specs/function_call_graph.md` (2025-11-09, GitHub Copilot).
    - Present: Viewer delegates the Code Flow tab to the shared builder, with deterministic output covered by `.repo_studios/tests/tests_command_center/viewer/test_function_call_graph_view.py` plus the multi-view harness above.
    - Future: Expand the Code Flow regression harness once entrypoint trace and method call chain diagrams arrive so inter-pack coexistence remains guarded.
  - `entrypoint_trace_diagram.mmd`
    - [x] Data slice ready (D) — Documented the entrypoint trace contract in `view_specs/entrypoint_trace_diagram.md` and extended normalization to surface `entrypoints.candidates` plus a repository index (2025-11-11, GitHub Copilot).
    - [x] Controls wired (C) — Viewer wiring now routes Entrypoint Trace toggles through `buildEntrypointTraceDiagramViewDefinition()`, rendering curated candidates with scope-aware fallbacks and repository messaging (2025-11-11, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Updated regression `.repo_studios/tests/tests_command_center/viewer/test_code_flow_multi_view_coexistence.py` ensures Function Call Graph ↔ Entrypoint Trace toggles preserve deterministic definitions and status messaging (2025-11-11, GitHub Copilot).
    - Past: Added entrypoint heuristics that combine main-guard and CLI-parser signals, populated module-level candidate lists, and authored regression coverage `.repo_studios/tests/tests_command_center/viewer/test_entrypoint_data_normalization.py` (2025-11-11, GitHub Copilot).
    - Present: Entrypoint Trace builder renders repository and scoped views with fallback notices, deterministic status details, and Node-backed regression coverage `.repo_studios/tests/tests_command_center/viewer/test_entrypoint_trace_view.py` alongside the refreshed coexistence harness.
    - Future: Expand traversal depth controls, surface CLI argument metadata once producers emit signatures, and introduce diff mode comparing entrypoint fan-out across CommandView snapshots.
  - `class_inheritance_hierarchy.mmd`
    - [x] Data slice ready (D) — Class normalization captures bases, resolved relationships, and module counts; documented in `view_specs/class_inheritance_hierarchy.md` (2025-11-11, GitHub Copilot).
    - [x] Controls wired (C) — Viewer wiring invokes `buildClassInheritanceHierarchyViewDefinition()` which scopes selections, applies repository fallbacks, and renders diagrams via `ui/builders/class_inheritance_hierarchy.js` (2025-11-11, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Extended `.repo_studios/tests/tests_command_center/viewer/test_code_flow_multi_view_coexistence.py` exercises Class Inheritance alongside Function Call Graph, Entrypoint Trace, and Health pack views (2025-11-11, GitHub Copilot).
    - Past: Authored the data slice contract, normalized class metadata with inheritance indexes, and added Node-backed regression coverage for data and builder correctness (2025-11-11, GitHub Copilot).
    - Present: Wiring now renders scoped hierarchies with fallback messaging; regression suite spans builder (`test_class_inheritance_hierarchy_view.py`) and view-definition (`test_class_inheritance_view_definition.py`) coverage plus updated coexistence safeguards (2025-11-11, GitHub Copilot).
    - Future: Layer smell/coverage overlays onto inheritance stats, surface diff mode across CommandView snapshots, and expose quick filters for mixins or external base hotspots before promoting beyond prototype.
  - `method_call_chain.mmd`
    - [x] Data slice ready (D) — Documented the class-method chain contract in `view_specs/method_call_chain.md`; builder derives method descriptors from normalized function IDs and reuses the existing call graph map plus scope-aware allow lists (2025-11-11, GitHub Copilot).
    - [x] Controls wired (C) — Viewer delegates the Method Call Chain tab to `buildMethodCallChainViewDefinition()` which validates method availability, applies repository fallbacks, and renders participant stats/status details via `buildMethodCallChainDiagram()` (2025-11-11, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Extended `.repo_studios/tests/tests_command_center/viewer/test_code_flow_multi_view_coexistence.py` to exercise Method Call Chain toggles alongside Function Call Graph, Entrypoint Trace, Class Inheritance, and Health pack views with deterministic definitions (2025-11-11, GitHub Copilot).
    - Past: Extracted the sequence-diagram builder in `ui/builders/method_call_chain.js`, implementing BFS traversal with depth/branch caps, participant aggregation, and fallback messaging for unresolved method scopes (2025-11-11, GitHub Copilot).
    - Present: Viewer controls surface class-method chains with stats/states guarded by Node-backed regressions (`test_method_call_chain_view.py`, `test_method_call_chain_view_definition.py`) and the refreshed coexistence harness (2025-11-11, GitHub Copilot).
    - Future: Layer async/await annotations, highlight recursive edges, and expose per-hop metrics (coverage/churn) once producers emit the supplemental fields.
- **State Effects Pack**
  - `global_variable_usage_map.mmd`
    - [x] Data slice ready (D) — Normalization now exposes module-level globals via `normalizeModuleGlobals()` and function `usedGlobals` sets via `normalizeUsedGlobals()`, documented in the new spec `view_specs/global_variable_usage_map.md`.
    - [x] Controls wired (C) — Viewer wiring delegates to `buildGlobalVariableUsageViewDefinition()` and renders module subgraphs through `ui/builders/global_variable_usage_map.js`, including scope-aware fallbacks and status summaries.
    - [x] Multi-view coexistence verified (M) — Regression `.repo_studios/tests/tests_command_center/viewer/test_state_effects_multi_view_coexistence.py::test_global_variable_usage_map_coexists_with_io_effects_diagram` confirms the view stays stable while toggling across State Effects diagrams.
    - Past: Captured the global usage data contract and staged normalization helpers for modules/functions while wiring the State Effects pack buttons.
    - Present: Global Variable Usage Map renders module subgraphs with repository fallbacks; Node-backed regressions `test_global_variable_usage_map_view.py`, `test_global_variable_usage_view_definition.py`, and the new coexistence suite keep deterministic output and cross-view toggles guarded.
    - Future: Layer exception-driven annotations onto global usage stats once pack overlays arrive.
  - `io_effects_diagram.mmd`
    - [x] Data slice ready (D) — Documented the IO effects contract in `view_specs/io_effects_diagram.md` and added `normalizeIoEffects()` so every function record ships deterministic filesystem/env/network flags (2025-11-12, GitHub Copilot).
    - [x] Controls wired (C) — Viewer wiring now delegates to `buildIoEffectsViewDefinition()` which scopes selections, applies repository fallbacks, and renders diagrams via `ui/builders/io_effects_diagram.js` (2025-11-12, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Regression `.repo_studios/tests/tests_command_center/viewer/test_state_effects_multi_view_coexistence.py::test_exception_flow_map_coexists_with_io_effects_diagram` keeps IO Effects toggles stable alongside the other State Effects views.
    - Past: Captured IO effect normalization requirements, staged flag summaries in function records, and drafted the builder outline prior to wiring (2025-11-12, GitHub Copilot).
    - Present: IO Effects Diagram highlights per-module side effects with stats/fallbacks guarded by Node-backed regressions `test_io_effects_diagram_view.py`, `test_io_effects_view_definition.py`, and the new coexistence harness.
    - Future: Add effect severity overlays once producers emit richer metadata and extend the coexistence suite when State Effects expands.
  - `exception_flow_map.mmd`
    - [x] Data slice ready (D) — Documented the exception flow contract in `view_specs/exception_flow_map.md` and extended normalization via `normalizeRaisedExceptions()` so function records expose deduplicated, structured exception descriptors (2025-11-11, GitHub Copilot).
    - [x] Controls wired (C) — Viewer wiring now routes to `buildExceptionFlowViewDefinition()` which scopes exception-aware function IDs, applies repository fallbacks, and renders diagrams through `ui/builders/exception_flow_map.js` with deterministic status payloads (2025-11-11, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Regression `.repo_studios/tests/tests_command_center/viewer/test_state_effects_multi_view_coexistence.py::test_exception_flow_map_coexists_with_global_variable_usage_map` verifies the Exception Flow Map maintains definitions and status messaging alongside its State Effects peers.
    - Past: Added exception normalization, authored the Exception Flow Map builder, and created the new view spec plus Node-backed regression coverage (`test_exception_flow_map_view.py`, `test_exception_flow_view_definition.py`) to lock diagrams and scope fallbacks (2025-11-11, GitHub Copilot).
    - Present: Exception Flow Map renders module subgraphs with raiser counts, scoped fallback messaging, status leaderboards, and coexistence coverage shared with the State Effects harness.
    - Future: Surface severity overlays once producer screening metadata arrives and extend the harness when additional State Effects diagrams (e.g., state mutation timelines) land.
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
    - [x] Data slice ready (D) — Documented the API exposure contract in `view_specs/public_vs_private_api.md` and normalized module records via `buildModuleApiSurface()` so functions, classes, globals, and re-exports carry explicit exposure categories (2025-11-12, GitHub Copilot).
    - [x] Controls wired (C)
    - [x] Multi-view coexistence verified (M)
    - Past: Captured export classification requirements, added API surface normalization, and staged the builder wiring plan prior to UI integration.
    - Present: Quality Metrics controls now delegate to `buildPublicVsPrivateApiViewDefinition()` with rendering handled by `ui/builders/public_vs_private_api.js`; passing regressions `.repo_studios/tests/tests_command_center/viewer/test_public_private_api_view.py`, `test_public_private_api_view_definition.py`, and `test_quality_metrics_multi_view_coexistence.py` (pytest run 2025-11-12 via `.venv/Scripts/python.exe -m pytest`).
    - Future: Extend status messaging with policy alerts for implicit APIs, layer coverage/type-hint overlays into the stats panel, and explore diff mode once successive CommandView snapshots are compared.
  - `cyclomatic_complexity_map.mmd`
    - [x] Data slice ready (D) — Documented the complexity map data contract in `view_specs/cyclomatic_complexity_map.md` and confirmed normalized function records expose `cyclomaticComplexity`, coverage, and line counts (2025-11-12, GitHub Copilot).
    - [x] Controls wired (C) — Viewer routes Cyclomatic Complexity Map toggles through `buildCyclomaticComplexityMapViewDefinition()` and renders aggregated module buckets via `ui/builders/cyclomatic_complexity_map.js`, including scope-aware fallbacks and status details (2025-11-12, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Extended `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py` to exercise repeated Cyclomatic Complexity Map toggles alongside the other Quality Metrics views with deterministic output (2025-11-12, GitHub Copilot).
    - Past: Captured the per-function complexity data slice and cited producer regression coverage guarding cyclomatic metrics plus the viewer normalization helper that surfaces them.
    - Present: Node-backed regressions (`test_cyclomatic_complexity_map_view.py`, `test_quality_metrics_multi_view_coexistence.py`) lock diagram definitions, stats, and status payloads while the viewer exposes module severity summaries and coverage thresholds.
    - Future: Layer churn overlays into bucket labels, surface repository baseline comparisons in status messaging, and explore diff snapshots once successive inventories are available.
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
    - [x] Data slice ready (D)
    - [x] Controls wired (C)
    - [x] Multi-view coexistence verified (M)
    - Past: Documented the cross-module coupling data contract and aggregated call graph edges into module-level stats via the new builder module (2025-11-12, GitHub Copilot).
    - Present: Coupling Insight controls now delegate to `buildCrossModuleFunctionReferencesViewDefinition()` which scopes selections, applies fallback notices, and renders deterministic diagrams backed by Node regression coverage.
    - Future: Layer churn/coverage overlays into node labels and expose threshold configuration once additional metrics land in normalization.
  - `import_chain_depth.mmd`
    - [x] Data slice ready (D)
    - [x] Controls wired (C)
    - [x] Multi-view coexistence verified (M)
    - Past: Normalized import edges now feed a breadth-first depth assignment that starts from stdlib touchpoints and records chain predecessors (2025-11-12, GitHub Copilot).
    - Present: The Import Chain Depth view highlights scoped selections, threads deterministic stats (depth buckets, deepest chains, unreachable modules), and renders stdlib nodes alongside depth-tier styling.
    - Future: Introduce configurable depth thresholds and optional third-party entry points once dependency metadata expands beyond stdlib/internal categories.
- **Risk & Assurance Pack**
  - `test_coverage_mapping.mmd`
    - [x] Data slice ready (D) — Coverage signals (`coverage_signals.imports`, `coverage_signals.has_matches`) and per-function coverage metrics now flow through `createModuleRecord()` / `createFunctionRecord()`, captured in the new spec `view_specs/test_coverage_mapping.md` (2025-11-13, GitHub Copilot).
    - [x] Controls wired (C) — Viewer delegates the Risk & Assurance toggle to `buildTestCoverageMappingViewDefinition()` which scopes via `resolveTestCoverageScope()`, threads repository fallbacks, and renders diagrams through `ui/builders/test_coverage_mapping.js`; regression coverage lives in `.repo_studios/tests/tests_command_center/viewer/test_test_coverage_mapping_view.py` and `test_test_coverage_mapping_view_definition.py` (2025-11-13, GitHub Copilot).
  - [ ] Multi-view coexistence verified (M) — Pending dedicated Risk & Assurance coexistence harness; will add regression once Git Churn and Dead Code diagrams are wired.
  - `git_churn_risk_map.mmd`
    - [x] Data slice ready (D) — Documented churn metrics contract in `view_specs/git_churn_risk_map.md`, confirming normalized modules expose `gitChurn` blocks and `statistics.git_churn` aggregates (2025-11-13, GitHub Copilot).
    - [x] Controls wired (C) — Viewer delegates to `buildGitChurnRiskMapViewDefinition()` which scopes selections via the new git churn resolver, threads repository baselines, and renders diagrams through `ui/builders/git_churn_risk_map.js` with deterministic status payloads (2025-11-13, GitHub Copilot).
    - [ ] Multi-view coexistence verified
  - `dead_code_detection.mmd`
    - [x] Data slice ready (D) — Normalization now surfaces `unusedImports` and `unreachableFunctions` via `normalizeUnusedImports()` / `normalizeUnreachableFunctions()` with regression coverage in `.repo_studios/tests/tests_command_center/viewer/test_dead_code_data_normalization.py` (2025-11-13, GitHub Copilot).
    - [x] Controls wired (C) — Viewer delegates to `buildDeadCodeDetectionViewDefinition()` which applies scope-aware fallbacks and renders diagrams through `ui/builders/dead_code_detection.js`; behavior locked by `.repo_studios/tests/tests_command_center/viewer/test_dead_code_detection_view_definition.py` (2025-11-13, GitHub Copilot).
    - [x] Multi-view coexistence verified (M) — Added Risk & Assurance harness `.repo_studios/tests/tests_command_center/viewer/test_risk_assurance_multi_view_coexistence.py` covering Test Coverage Mapping, Git Churn Risk Map, and Dead Code Detection toggles (2025-11-13, GitHub Copilot).

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

Status note (2025-11-12): Selector payload now surfaces slug+timestamp labels, deduplicates static mirrors, backend refresh helpers preserve active context, the HTML shell with Mermaid wiring is live, JSON loader plus normalization populate registries/caches, duplicate fetch/schema gating keeps loads deterministic, hierarchy metadata and Level 0-4 data slices are ready for rendering, level node thresholds now prompt deeper zoom when diagrams exceed 50 nodes, breadcrumb/navigation interactions keep zoom flows snappy, refresh cycles now restore the prior zoom level whenever the slug persists, the viewer applies metrics-driven node/edge styling across levels, Mermaid definitions stay in-memory via `state.diagramDefinition` with no default `.mmd` output, debugging exports route through `.repo_studios/command_center/viewer/cache/write_mermaid_cache.py` with 24-hour TTL and five-file retention, the UI now offers an `Export .mmd` button for on-demand downloads, the sidebar lists all 28 curated view packs, the Health pack Function Inventory Overview and Screening Signal Timeline views are selectable from the sidebar and render via their shared builder modules and regression harnesses, the Code Flow · Function Call Graph view now relies on the dedicated builder module with Node-backed regression plus multi-view coexistence coverage guarding Health ↔ Code Flow toggles, the Code Flow Entrypoint Trace view now renders curated candidates with scope-aware fallbacks via its dedicated builder and participates in the refreshed coexistence harness, the Code Flow Class Inheritance Hierarchy view now renders scoped diagrams with repository fallbacks, ships regression coverage (`test_class_inheritance_hierarchy_view.py`, `test_class_inheritance_view_definition.py`), and participates in the same coexistence harness, the Code Flow Method Call Chain view now renders sequence diagrams for class-focused call chains with repository fallbacks, deterministic builder/view-definition regressions, and coexistence coverage guarding toggles with other Code Flow and Health pack views, the Dependency pack Module Dependency Graph renders from normalized import edges with alias preservation and coexists alongside the Function Call Graph, the Circular Import Detection view now executes through its Tarjan-based builder with scope-aware fallbacks and coexistence coverage guarding toggles with the dependency graph, the Layer Architecture Validation view now highlights adjacency violations via its dedicated builder and participates in the Dependency pack coexistence suite, the Export Contract Matrix view now routes through its dedicated builder with scope-aware fallback messaging and coexistence coverage guarding Dependency pack toggles, the Quality Metrics pack includes Type Coverage and Documentation Coverage builders with deterministic tests, zoom-aware scope filtering, and coexistence coverage guarding intra-pack toggles, the Decorator Usage Map now threads required-annotation alerts into status messaging alongside dedicated regressions and updated Quality Metrics coexistence coverage, the Public vs Private API view now renders via `ui/builders/public_vs_private_api.js` with viewer wiring, Node-backed builder regressions, and inclusion in the refreshed Quality Metrics coexistence suite, the Event Dynamics Callback Registration Map now participates in a dedicated coexistence harness ensuring toggles with the Function Call Graph remain stable, the Dynamic Code Watchlist reuses the same harness with scope-aware fallback messaging to display repository-level signals when scoped selections lack events, the State Effects Global Variable Usage Map now renders module-level subgraphs with repository fallbacks and participates in the shared State Effects coexistence harness (`.repo_studios/tests/tests_command_center/viewer/test_state_effects_multi_view_coexistence.py`), the State Effects IO Effects Diagram now surfaces per-module filesystem, environment, and network flags with deterministic status messaging while sharing the same harness, the State Effects Exception Flow Map renders scoped module subgraphs with status leaderboards backed by the new pack-level coexistence coverage, and the Coupling Insight Cross-Module Function References view now renders module coupling diagrams with scope-aware fallbacks plus dedicated regression coverage.
Additionally, the Risk & Assurance Test Coverage Mapping view now renders through `buildTestCoverageMappingViewDefinition()` with scope-aware fallbacks, deterministic builder output, and targeted regressions (`test_test_coverage_mapping_view.py`, `test_test_coverage_mapping_view_definition.py`); the Git Churn Risk Map view now shares the pack via `buildGitChurnRiskMapViewDefinition()`, repository-baseline normalization, and Node-backed regressions (`test_git_churn_risk_map_view.py`, `test_git_churn_risk_map_view_definition.py`); and the new Dead Code Detection diagram runs through `buildDeadCodeDetectionViewDefinition()` with supporting regressions (`test_dead_code_detection_view.py`, `test_dead_code_detection_view_definition.py`). Risk & Assurance coexistence coverage now lives in `.repo_studios/tests/tests_command_center/viewer/test_risk_assurance_multi_view_coexistence.py`, confirming all three pack views toggle without state drift. The Coupling Insight Import Chain Depth view charts stdlib-to-module hop chains with deterministic depth stats, fallback messaging, and coexistence coverage. Pack overlays and advanced rendering remain upcoming (future).

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
