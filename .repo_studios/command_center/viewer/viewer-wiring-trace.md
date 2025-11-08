# Command Center Viewer - Wiring Trace Report

**Generated**: 2025-11-07
**Status**: ✅ All systems properly wired

---

## Executive Summary

The viewer load path from HTML bootstrap through data normalization and rendering has been revalidated against the current `viewer/ui` sources. Configuration defaults, selector discovery, artifact loading, and rendering all operate as documented. Additional notes capture the in-memory caching layer and selection memory introduced in the latest revisions.

---

## 1. Initialization Flow ✅

### 1.1 HTML Structure (`viewer/ui/index.html`)

- ✅ `#selector-list` - CommandView artifact selector
- ✅ `#level-controls` - Container for zoom level controls
- ✅ `#level-buttons` - Group of level toggle buttons
- ✅ `#level-sidebar` - Level-specific navigation list
- ✅ `#view-pack-container` - View pack button grid
- ✅ `#view-tabs` - Dynamic tab strip for active views
- ✅ `#breadcrumb` - Zoom breadcrumb display
- ✅ `#diagram-container` and `#diagram` - Mermaid render target
- ✅ `#status-panel` - Status and error messaging surface
- ✅ `#refresh-button` - Selector regeneration trigger
- ✅ `#export-button` - Mermaid export trigger (initially disabled)
- ✅ Inline `window.viewerConfig` block primes `reportsBaseUrl`
- ✅ `viewer.js` is loaded as an ES module after config is set

### 1.2 Bootstrap Sequence (`viewer.js` · `bootstrap`)

```javascript
async function bootstrap() {
  initializeMermaid();
  initializeLevelControls();
  initializeBreadcrumb();
  renderViewTabs();
  renderViewPacks();
  wireRefresh();
  wireExport();
  updateStatus("Loading selector data...");
  await refreshSelectorData();
}
```

- Runs immediately when the DOM is ready
- Ensures UI scaffolding exists before any network activity
- Surfaces bootstrap failures via console logging and status panel messaging

---

## 2. Configuration & Path Resolution ✅

### 2.1 Configuration Chain

`window.viewerConfig` → `getViewerConfig()` → `resolveReportsBaseUrl()` → `buildArtifactUrl()`

- Honors a caller-provided `reportsBaseUrl`; otherwise uses `DEFAULT_REPORTS_BASE_URL`
- Accepts absolute URLs and JSON endpoints, trimming to the directory when necessary
- Normalizes trailing slashes to avoid malformed fetch URLs
- Throws on missing relative paths to prevent silent failures

### 2.2 Selector URL Building (`buildSelectorUrl`)

- Accepts explicit JSON endpoints or directory roots and appends `selector.json`
- Returns `null` when inputs are empty to allow demo fallback
- Shares trailing slash handling logic with artifact builders

---

## 3. Data Loading Pipeline ✅

### 3.1 Selector Fetch (`refreshSelectorData`)

```
refreshSelectorData()
  -> derive selector endpoint from config or default reports base
  -> log config, endpoint, and resolved URL
  -> fetch selector JSON with `cache: "no-cache"`
  -> validate payload shape (`entries` must be an array)
  -> call setEntries() and update status panel
  -> on failure: log error, optionally fall back to bootstrapDemoPayload()
```

- Status panel reflects fetch progress and any HTTP errors
- Demo payload keeps UI operable during local development or offline use

### 3.2 Artifact Fetch (`selectOption` → `loadCommandViewPayloads`)

```
selectOption(option)
  -> log selected option metadata
  -> call loadCommandViewPayloads(option)
  -> update state inventory/screening URLs and payloads
  -> normalize data and rebuild UI scaffolding
```

- `loadCommandViewPayloads` resolves relative paths through `buildArtifactUrl`
- Fetches inventory and optional screening JSON in parallel
- Validates `schema_version` against supported versions before proceeding
- Normalizes module/function records, call graphs, metrics, and hierarchy data
- Seeds level definitions and caches the result for fast back-and-forth navigation

---

## 4. User Interaction Wiring ✅

- **Refresh button** (`wireRefresh`) disables during refresh, awaits `refreshSelectorData`, and restores state regardless of success
- **Export button** (`wireExport`) invokes `exportCurrentDiagram()` and is enabled only when `state.diagramDefinition` is populated
- **Selector list** (`renderSelector`) creates buttons per option, stores metadata via `data-*` attributes, and highlights the active choice
- **Level controls** (`initializeLevelControls` → `setLevel`) manage availability, sync button state, and rerender the sidebar and breadcrumbs
- **View pack buttons** (`renderViewPacks`) respect requirement checks from `evaluateViewAvailability`, attach interactions, and expose guidance text when disabled
- **View tabs** (`renderViewTabs`) provide tab selection plus close buttons that call `removeActiveView`

---

## 5. Diagram Rendering Pipeline ✅

- `renderCurrentLevel()` picks between zoom rendering and active view rendering
- Active views delegate to dedicated builders; zoom views generate Mermaid definitions directly
- `renderActiveView()` updates status messaging before and after Mermaid rendering
- `renderDiagram()` wraps `window.mermaid.render`, inserts SVG output, and guards against runtime errors
- `attachRenderInteractions()` wires click and keyboard handlers for any registered element IDs
- `updateExportButtonState()` mirrors diagram availability so exports stay in sync

---

## 6. State Management ✅

```javascript
const state = {
  entries: [],
  activeOption: null,
  inventoryPayload: null,
  screeningPayload: null,
  inventoryUrl: null,
  screeningUrl: null,
  normalizedData: null,
  levels: null,
  currentLevel: "level0",
  diagramDefinition: null,
  levelSelections: { rootId: null, domainId: null, moduleId: null, functionId: null },
  renderInteractions: new Map(),
  activeViews: [],
  activeViewIndex: -1,
};
```

- `setEntries()` resets views, restores selection memory, and refreshes UI when the entry list changes
- Level selections cascade through `renderLevelSidebar`, `renderBreadcrumb`, and `renderCurrentLevel`
- Diagram and export state stay synchronized via `state.diagramDefinition` and `updateExportButtonState`

---

## 7. Caching & Selection Memory ✅

- `payloadCache` stores the normalized inventory, screening data, and derived levels keyed by slug, path, and timestamp
- Cached results short-circuit network requests inside `loadCommandViewPayloads`
- `selectionMemory` retains level selections for the active artifact to improve UX when data reloads
- `persistActiveSelectionMemory()` records the current level hierarchy before entries change
- `restoreSelectionMemory()` reapplies remembered selections when an option is revisited within the session
- Both caches are in-memory maps scoped to the current browser session, ensuring fresh data after reloads

---

## 8. Logging & Debugging ✅

- Selector refresh logs configuration, endpoints, response status, and payload sizes
- Entry population logs the computed next selection and ensures no silent drops
- Artifact loading logs URLs, fetch results, and file counts
- Mermaid failures surface as console errors and status-panel messages
- Missing DOM nodes result in explicit console warnings to aid markup troubleshooting

---

## 9. Critical Path Verification ✅

### Path 1: Initial Load

```
Page load → bootstrap() → refreshSelectorData() → setEntries() → selectOption() → loadCommandViewPayloads() → normalizeCommandViewData() → renderCurrentLevel()
```

### Path 2: User Selects Artifact

```
Button click → selectOption() → loadCommandViewPayloads() → updateLevelButtonsState() → renderLevelSidebar() → renderCurrentLevel()
```

### Path 3: User Changes Zoom Level

```
Level button → setLevel() → updateLevelButtonsState() → renderLevelSidebar() → renderCurrentLevel() → renderDiagram()
```

### Path 4: User Opens View Pack

```
View pack button → selectView() → renderViewPacks() → renderViewTabs() → renderCurrentLevel() → renderActiveView()
```

### Path 5: User Refreshes Selector

```
Refresh button → refreshSelectorData() → setEntries() → selectOption(next) → loadCommandViewPayloads() → renderCurrentLevel()
```

---

## 10. Potential Issues & Mitigations ✅

- **Missing selector.json** → Demo payload fallback keeps UI responsive and surfaces message in the status panel
- **Artifact fetch failures** → Try/catch around payload load displays errors, logs stack traces, and preserves previous state
- **Schema mismatches** → `validateInventorySchema()` rejects unsupported versions with descriptive messages
- **Mermaid failures** → Renderer exceptions are caught, logged, and reported through UI messaging
- **Markup drift** → Guard clauses log missing DOM nodes so regressions are easy to spot

---

## 11. Dependencies ✅

- External: Mermaid.js v10 from CDN, standard ES module support
- Internal: Generated `selector.json`, CommandView inventory JSON, optional screening JSON, and the viewer utility scripts (`generate_selector.py`, `serve_viewer.py`, `refresh.py`)

---

## 12. File Structure Verification ✅

```
.repo_studios/command_center/
├── reports/
│   ├── selector.json
│   └── index_scan/<slugged>/.../_commandview_YYYYMMDD-HHMM.json
└── viewer/
    ├── ui/
    │   ├── index.html
    │   ├── viewer.css
    │   ├── viewer.js
    │   └── diagnostic.html
    ├── generate_selector.py
    ├── refresh.py
    ├── serve_viewer.py
    └── TROUBLESHOOTING.md
```

---

## 13. Conclusion ✅

- ✅ HTML scaffolding aligns with expected IDs and ARIA attributes
- ✅ JavaScript wiring covers initialization, data fetch, UI updates, and error handling
- ✅ Caching layers and selection memory operate as designed without persisting stale state across reloads
- ✅ Logging provides full visibility for bootstrap, fetch, and render stages
- ✅ Supporting CLI tooling generates the selector manifest consumed by the UI

**Next diagnostic steps**

1. Hard refresh the browser (`Ctrl+F5`) to clear any cached assets
2. Open developer tools to confirm selector and artifact fetches return HTTP 200
3. Use `diagnostic.html` for automated sanity checks if rendering issues reappear
