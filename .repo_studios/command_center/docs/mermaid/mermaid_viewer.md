# Progressive Detail Mermaid Viewer — Implementation Checklist

## Phase 0 · Charter & Success Measures

- [ ] Reconfirm viewer purpose: deliver progressive wiring diagrams that solve clutter and exploration pain points.
- [ ] Capture success criteria: fast comprehension for contractors, Copilot-ready JSON insights, reduced onboarding time, data-informed refactoring.
- [ ] Log charter and owners in governance docs.

## Phase 1 · Data Supply & Naming

- [ ] Keep generator outputs aligned with commandview naming (`<source_folder>_commandview_YYYYMMDD-HHMM.json`).
- [ ] Format selector labels to surface timestamp freshness (derive display value from the slug’s `YYYYMMDD-HHMM` component).
- [ ] Ensure `generate_function_inventory.py` (future `generate_commandview_inventory.py`) writes mirrored artifacts only under `.repo_studios/command_center/reports/` for viewer discovery, leaving dynamic copies for agents.
- [ ] Validate inventory payload includes `files[].call_graph` with resolved local/imported/builtin edges.
- [ ] Document viewer expectations for coverage and churn overlays now that inventory emits `files[].coverage`, `files[].git_churn`, and `statistics.coverage`/`statistics.git_churn` aggregates.
- [ ] Confirm dependency summaries, callbacks, IO effects, logging, globals, and docstring metadata remain intact for downstream packs.

## Phase 2 · Discovery & Refresh Pipeline

- [ ] Build selector bootstrapper that scans the static reports tree only, filtering JSON that matches the `*_commandview_YYYYMMDD-HHMM.json` slug.
- [ ] Populate selector entries with source folder + timestamp so users can judge freshness at a glance.
- [ ] Implement refresh button that re-runs discovery, updates selector options, and preserves active context when possible.
- [ ] Ensure refresh routine deduplicates by slug to avoid double-listing static vs dynamic artifacts.
- [ ] Document refresh workflow in README and add make/CLI recipe to regenerate inventories before viewer launch.

## Phase 3 · Viewer Core (HTML/JS Shell)

- [ ] Scaffold single-page HTML that loads Mermaid.js from CDN and initializes viewer state.
- [ ] Implement JSON loader (local file or static host) that ingests both inventory and screening payloads.
- [ ] Normalize data model on load: module registry, function registry, call graph index, metrics cache.
- [ ] Guard against duplicate fetch and handle schema-version gating.

## Phase 4 · Level-of-Detail Engine

- [ ] Auto-detect hierarchy depth from module paths to define zoom levels (root, domain, module, function, neighborhood).
- [ ] Configure five canonical levels:
  - [ ] Level 0 Overview — root packages with aggregated import edges.
  - [ ] Level 1 Domain — second-level groupings with cross-domain imports.
  - [ ] Level 2 File — modules with file-to-file imports.
  - [ ] Level 3 Functions — per-module call graph with metrics badges.
  - [ ] Level 4 Detail — focal function plus immediate neighbors and annotations.
- [ ] Maintain thresholds (≈50 nodes) that trigger suggestions to zoom deeper.

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

Status note (2025-11-05): Document reformatted into actionable checklist and ready for phased execution.
