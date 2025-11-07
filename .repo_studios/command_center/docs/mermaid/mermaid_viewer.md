# Progressive Detail Mermaid Viewer — Implementation Checklist

## Phase 0 · Charter & Success Measures

- [ ] Reconfirm viewer purpose: deliver progressive wiring diagrams that solve clutter and exploration pain points.
- [ ] Capture success criteria: fast comprehension for contractors, Copilot-ready JSON insights, reduced onboarding time, data-informed refactoring.
- [ ] Log charter and owners in governance docs.

## Phase 1 · Data Supply & Naming

- [ ] Keep generator outputs aligned with commandview naming (`<source_folder>_commandview_YYYYMMDD-HHMM.json`).
- [ ] Format selector labels to surface timestamp freshness (derive display value from the slug’s `YYYYMMDD-HHMM` component).
- [x] Ensure `generate_commandview_inventory.py` writes mirrored artifacts only under `.repo_studios/command_center/reports/` for viewer discovery, leaving dynamic copies for agents.
  - Mirrored inventories now hard-block custom `--reports-root` values that escape `.repo_studios/command_center/reports`, keeping the viewer discovery scope static (enforced 2025-11-06).
  - Local agent workflows continue to rely on the co-located `<slug>_index/` folders for dynamic experimentation without impacting the viewer scan.
- [ ] Validate inventory payload includes `files[].call_graph` with resolved local/imported/builtin edges.
- [ ] Document viewer expectations for coverage and churn overlays now that inventory emits `files[].coverage`, `files[].git_churn`, and `statistics.coverage`/`statistics.git_churn` aggregates.
- [ ] Confirm dependency summaries, callbacks, IO effects, logging, globals, and docstring metadata remain intact for downstream packs.

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

- [ ] Implement breadcrumb navigation (e.g., Overview > pkg > module > function).
- [ ] Support node click to drill down and breadcrumb/back control to zoom out.
- [ ] Persist zoom state during refresh when underlying data permits.
- [ ] Apply color and edge styles (e.g., red for high complexity, dotted for call edges) sourced from inventory metrics.

## Phase 6 · Rendering & Temp Artifact Strategy

- [ ] Generate Mermaid definitions in memory; do not persist `.mmd` files to disk by default.
- [ ] If temporary `.mmd` artifacts are needed for debugging, place them under a dedicated cache directory and overwrite on reuse.
- [ ] Implement eviction/expiry policy to prevent stale temp views after refresh runs.
- [ ] Add export button that writes the currently rendered Mermaid definition (`.mmd`) to disk on demand (image export remains optional).

## Phase 7 · Selector Views & Packs

- [ ] Expose sidebar list of the 28 candidate views curated in the integration checklist, grouped by pack (Health, Dependency, Code Flow, etc.).
- [ ] For each view:
  - [ ] Define required data slice and transforms.
  - [ ] Wire viewer controls to trigger view-specific Mermaid generation.
  - [ ] Ensure multiple views can coexist (tabbed or multi-panel) without reloading JSON.
- [ ] Map Code Flow pack to newly emitted call graph edges.

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

Status note (2025-11-06): Selector payload now surfaces slug+timestamp labels, deduplicates static mirrors, backend refresh helpers preserve active context, the HTML shell with Mermaid wiring is live, JSON loader plus normalization populate registries/caches, duplicate fetch/schema gating keeps loads deterministic, hierarchy metadata and Level 0-4 data slices are ready for rendering, and level node thresholds now prompt deeper zoom when diagrams exceed 50 nodes (done). Zoom controls continue rendering Level 0-4 views in-browser while breadcrumb/back navigation remains in design (present). Pack overlays and advanced rendering remain upcoming (future).

## Viewer Shell Assets

- `index.html`: Hosts the viewer container, refresh trigger, and selector scaffold tied to Mermaid.js.
- `viewer.css`: Provides baseline theming for the dark-mode layout used during prototyping.
- `viewer.js`: Initialises Mermaid, seeds demo selector data, and renders placeholder diagrams until real loaders arrive.

## Refresh Workflow

1. **Regenerate CommandView artifacts** (present):
  - Preferred: `make -C .repo_studios command-center COMMAND_CENTER_TARGET=.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py PYTHON=.venv/Scripts/python.exe -- --repo-root . --log-level INFO`.
  - Direct CLI: `C:/Users/genet/repo_studios/.venv/Scripts/python.exe .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py .repo_studios/command_center/scripts --repo-root . --log-level INFO`.
2. **Invoke viewer refresh backend** (present): call `refresh_selector_with_context(repo_root, active_relative_path=..., active_slug=...)` to rebuild selector state while preserving operator context.
3. **Launch UI prototype** (future): upcoming HTML shell will call the helper to hydrate controls; document updates will follow once the UI wiring step completes.
