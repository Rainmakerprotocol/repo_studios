import { buildScreeningTimelineDiagram } from "./builders/screening_signal_timeline.js";

console.log('[viewer.js] Script loading started');

const DEFAULT_REPORTS_BASE_URL = "/.repo_studios/command_center/reports/";
const ABSOLUTE_URL_PATTERN = /^[a-zA-Z][a-zA-Z0-9+\-.]*:\/\//;
const SUPPORTED_INVENTORY_SCHEMA_VERSIONS = new Set([2]);

console.log('[viewer.js] Constants defined, DEFAULT_REPORTS_BASE_URL:', DEFAULT_REPORTS_BASE_URL);
const LEVEL_DEFINITIONS = [
  { value: "level0", label: "Level 0 - Overview" },
  { value: "level1", label: "Level 1 - Domain" },
  { value: "level2", label: "Level 2 - Module" },
  { value: "level3", label: "Level 3 - Functions" },
  { value: "level4", label: "Level 4 - Neighborhood" },
];

const VIEW_PACKS = Object.freeze([
  {
    id: "health",
    title: "Health Pack",
    views: [
      {
        id: "function_inventory_overview",
        label: "Function Inventory Overview",
        filename: "function_inventory_overview.mmd",
        description:
          "Summarizes per-module function counts, docstring coverage, and annotation ratios for quick health checks.",
        status: "prototype",
        builder: "functionInventoryOverview",
        requirements: ["inventoryBasics", "docstringQuality", "typeCoverage"],
      },
      {
        id: "screening_signal_timeline",
        label: "Screening Signal Timeline",
        filename: "screening_signal_timeline.mmd",
        description:
          "Timeline outlining when screening scores crossed thresholds to support release planning discussions.",
        status: "prototype",
        builder: "screeningSignalTimelineView",
        requirements: ["screeningHistory"],
      },
    ],
  },
  {
    id: "dependency",
    title: "Dependency Pack",
    views: [
      {
        id: "module_dependency_graph",
        label: "Module Dependency Graph",
        filename: "module_dependency_graph.mmd",
        description:
          "Import dependency graph to highlight hotspots, orphan modules, and cross-module coupling.",
        status: "planned",
      },
      {
        id: "export_contract_matrix",
        label: "Export Contract Matrix",
        filename: "export_contract_matrix.mmd",
        description:
          "Class diagram portraying public exports by type so API boundaries stay visible during reviews.",
        status: "planned",
      },
      {
        id: "circular_import_detection",
        label: "Circular Import Detection",
        filename: "circular_import_detection.mmd",
        description:
          "Graph emphasizing import cycles that could trigger module loading issues.",
        status: "planned",
      },
      {
        id: "layer_architecture_validation",
        label: "Layer Architecture Validation",
        filename: "layer_architecture_validation.mmd",
        description:
          "Layered diagram validating Producers → Consumers → Aggregators → Orchestrators → Summarizers wiring.",
        status: "planned",
        note: "Requires a maintained tier map in the renderer to classify modules correctly.",
      },
      {
        id: "external_vs_internal_dependency_map",
        label: "External vs Internal Dependency Map",
        filename: "external_vs_internal_dependency_map.mmd",
        description:
          "Dependency map separating standard library, third-party, and internal modules to surface external attack surfaces.",
        status: "planned",
        note: "Depends on dependency classification buckets emitted by the inventory.",
      },
    ],
  },
  {
    id: "event-dynamics",
    title: "Event Dynamics Pack",
    views: [
      {
        id: "callback_registration_map",
        label: "Callback Registration Map",
        filename: "callback_registration_map.mmd",
        description:
          "Diagram tracing detected callback registrations to their emitters for reviewing event-driven surfaces.",
        status: "planned",
      },
      {
        id: "dynamic_code_watchlist",
        label: "Dynamic Code Watchlist",
        filename: "dynamic_code_watchlist.mmd",
        description:
          "Block diagram flagging modules where dynamic execution occurs so auditors can follow up quickly.",
        status: "planned",
      },
    ],
  },
  {
    id: "code-flow",
    title: "Code Flow Pack",
    views: [
      {
        id: "function_call_graph",
        label: "Function Call Graph",
        filename: "function_call_graph.mmd",
        description:
          "Directed graph showing which functions call each other for runtime path exploration.",
        status: "prototype",
        note: "Leans on inter-function call graph edges from the inventory.",
        builder: "functionCallGraphView",
        requirements: ["callGraph"],
      },
      {
        id: "entrypoint_trace_diagram",
        label: "Entrypoint Trace Diagram",
        filename: "entrypoint_trace_diagram.mmd",
        description:
          "Flow diagram expanding from CLI entrypoints (e.g., run or main) to reachable functions.",
        status: "planned",
        note: "Requires curated entrypoint definitions plus call graph traversal.",
      },
      {
        id: "class_inheritance_hierarchy",
        label: "Class Inheritance Hierarchy",
        filename: "class_inheritance_hierarchy.mmd",
        description:
          "Class diagram showing inheritance relationships to surface base/derived structures.",
        status: "planned",
        note: "Builds on recorded base class metadata in the inventory.",
      },
      {
        id: "method_call_chain",
        label: "Method Call Chain",
        filename: "method_call_chain.mmd",
        description:
          "Sequence diagram highlighting chained object method calls for delegate tracing.",
        status: "planned",
        note: "Needs richer bound-method tracing from the call graph resolver.",
      },
    ],
  },
  {
    id: "state-effects",
    title: "State Effects Pack",
    views: [
      {
        id: "global_variable_usage_map",
        label: "Global Variable Usage Map",
        filename: "global_variable_usage_map.mmd",
        description:
          "Diagram linking functions to global variables they read or write to highlight shared state.",
        status: "planned",
      },
      {
        id: "io_effects_diagram",
        label: "IO Effects Diagram",
        filename: "io_effects_diagram.mmd",
        description:
          "Annotated graph mapping functions to file, network, or environment interactions.",
        status: "planned",
      },
      {
        id: "exception_flow_map",
        label: "Exception Flow Map",
        filename: "exception_flow_map.mmd",
        description:
          "Visualization of which functions raise which exceptions to follow error propagation paths.",
        status: "planned",
      },
    ],
  },
  {
    id: "quality-metrics",
    title: "Quality Metrics Pack",
    views: [
      {
        id: "complexity_heatmap",
        label: "Complexity Heatmap",
        filename: "complexity_heatmap.mmd",
        description:
          "Heatmap coloring functions by derived complexity scores to spotlight hard-to-maintain code.",
        status: "planned",
      },
      {
        id: "logging_flow",
        label: "Logging Flow",
        filename: "logging_flow.mmd",
        description:
          "Diagram showing which functions emit logs at which levels to evaluate observability coverage.",
        status: "planned",
      },
      {
        id: "decorator_usage_map",
        label: "Decorator Usage Map",
        filename: "decorator_usage_map.mmd",
        description:
          "Graph clustering functions by decorator usage for quick annotation audits.",
        status: "planned",
      },
      {
        id: "public_vs_private_api",
        label: "Public vs Private API",
        filename: "public_vs_private_api.mmd",
        description:
          "Interface map contrasting externally exposed functions and classes with internal helpers.",
        status: "planned",
      },
      {
        id: "cyclomatic_complexity_map",
        label: "Cyclomatic Complexity Map",
        filename: "cyclomatic_complexity_map.mmd",
        description:
          "Visualization using McCabe complexity scores attached to functions in the inventory.",
        status: "planned",
        note: "Depends on cyclomatic complexity values emitted during inventory generation.",
      },
      {
        id: "type_coverage_map",
        label: "Type Coverage Map",
        filename: "type_coverage_map.mmd",
        description:
          "Chart highlighting which functions include type hints based on recorded annotation ratios.",
        status: "prototype",
        builder: "typeCoverageMapView",
        requirements: ["typeCoverage"],
      },
      {
        id: "documentation_coverage_map",
        label: "Documentation Coverage Map",
        filename: "documentation_coverage_map.mmd",
        description:
          "Diagram portraying docstring presence and quality scores for knowledge sharing readiness.",
        status: "planned",
      },
    ],
  },
  {
    id: "coupling-insight",
    title: "Coupling Insight Pack",
    views: [
      {
        id: "cross_module_function_references",
        label: "Cross-Module Function References",
        filename: "cross_module_function_references.mmd",
        description:
          "Edge map showing when functions in one file call functions in another to expose coupling.",
        status: "planned",
        note: "Requires function-to-module association from the call graph data.",
      },
      {
        id: "import_chain_depth",
        label: "Import Chain Depth",
        filename: "import_chain_depth.mmd",
        description:
          "Layered view illustrating import hop counts from standard library to local modules.",
        status: "planned",
        note: "Builds on dependency classification buckets and depth calculations during rendering.",
      },
    ],
  },
  {
    id: "risk-assurance",
    title: "Risk & Assurance Pack",
    views: [
      {
        id: "test_coverage_mapping",
        label: "Test Coverage Mapping",
        filename: "test_coverage_mapping.mmd",
        description:
          "Graph connecting tests to exercised functions for coverage validation.",
        status: "planned",
        note: "Requires coverage artifacts (e.g., coverage.json) mapped to inventory modules.",
      },
      {
        id: "git_churn_risk_map",
        label: "Git Churn Risk Map",
        filename: "git_churn_risk_map.mmd",
        description:
          "Risk heatmap combining git change frequency with complexity signals.",
        status: "planned",
        note: "Needs git churn metrics plus scoring guidance to drive risk colors.",
      },
      {
        id: "dead_code_detection",
        label: "Dead Code Detection",
        filename: "dead_code_detection.mmd",
        description:
          "Diagram isolating functions never invoked alongside unused imports for remediation planning.",
        status: "planned",
        note: "Depends on call graph coverage and unused symbol analysis in the inventory.",
      },
    ],
  },
]);

const VIEW_BUILDERS = Object.freeze({
  functionCallGraphView: buildFunctionCallGraphViewDefinition,
  functionInventoryOverview: buildFunctionInventoryOverviewViewDefinition,
  typeCoverageMapView: buildTypeCoverageMapViewDefinition,
  screeningSignalTimelineView: buildScreeningSignalTimelineViewDefinition,
});

function getViewPackById(packId) {
  if (!packId) {
    return null;
  }
  return VIEW_PACKS.find((pack) => pack.id === packId) ?? null;
}

function getViewMetadata(packId, viewId) {
  if (!packId || !viewId) {
    return null;
  }
  const pack = getViewPackById(packId);
  if (!pack) {
    return null;
  }
  const view = pack.views.find((candidate) => candidate.id === viewId) ?? null;
  if (!view) {
    return null;
  }
  return { pack, view };
}

function evaluateViewAvailability(view) {
  if (!view) {
    return { available: false, reason: "View definition not found." };
  }

  if (!state.activeOption || !state.normalizedData) {
    return {
      available: false,
      reason: "Load a CommandView artifact to enable view packs.",
    };
  }

  const builderKey = view.builder ?? view.id;
  const builder = typeof builderKey === "string" ? VIEW_BUILDERS[builderKey] : null;
  if (typeof builder !== "function") {
    return {
      available: false,
      reason: view.note ?? "View wiring pending implementation.",
    };
  }

  const requirementIssue = findViewRequirementIssue(view.requirements ?? []);
  if (requirementIssue) {
    return { available: false, reason: requirementIssue };
  }

  return { available: true, builder };
}

function findViewRequirementIssue(requirements) {
  if (!Array.isArray(requirements) || requirements.length === 0) {
    return null;
  }

  for (const requirement of requirements) {
    switch (requirement) {
      case "inventoryBasics": {
        const modules = state.normalizedData?.modules;
        const functions = state.normalizedData?.functions;
        if (!(modules instanceof Map) || modules.size === 0) {
          return "CommandView inventory has no modules to summarize.";
        }
        if (!(functions instanceof Map) || functions.size === 0) {
          return "CommandView inventory has no functions to summarize.";
        }
        break;
      }
      case "docstringQuality": {
        const functions = state.normalizedData?.functions;
        if (!(functions instanceof Map) || functions.size === 0) {
          return "Docstring metrics are unavailable because no functions were normalized.";
        }
        const hasDocData = Array.from(functions.values()).some((fn) => fn && typeof fn.docstringQuality === "object");
        if (!hasDocData) {
          return "Docstring quality metrics are not available in this CommandView artifact.";
        }
        break;
      }
      case "typeCoverage": {
        const functions = state.normalizedData?.functions;
        if (!(functions instanceof Map) || functions.size === 0) {
          return "Type hint coverage data is unavailable because no functions were normalized.";
        }
        const hasTypeCoverage = Array.from(functions.values()).some((fn) => {
          const coverage = fn?.typeHintCoverage ?? fn?.annotationCoverage;
          const numeric = Number(coverage);
          return Number.isFinite(numeric);
        });
        if (!hasTypeCoverage) {
          return "Type hint coverage metrics are not available in this CommandView artifact.";
        }
        break;
      }
      case "callGraph": {
        const callGraph = state.normalizedData?.callGraph?.functions;
        if (!(callGraph instanceof Map) || callGraph.size === 0) {
          return "Call graph data is not available in this CommandView artifact.";
        }
        break;
      }
      case "coverage": {
        const modulesWithCoverage = state.normalizedData?.metrics?.modules;
        if (!(modulesWithCoverage instanceof Map) || modulesWithCoverage.size === 0) {
          return "Coverage metrics are not available in this CommandView artifact.";
        }
        break;
      }
      case "gitChurn": {
        const modulesWithChurn = state.normalizedData?.metrics?.modules;
        if (!(modulesWithChurn instanceof Map) || modulesWithChurn.size === 0) {
          return "Git churn metrics are not available in this CommandView artifact.";
        }
        break;
      }
      case "screeningHistory": {
        const history = state.normalizedData?.screeningHistory ?? null;
        if (!history) {
          return "Screening history data is not available in this CommandView artifact.";
        }
        if (!Array.isArray(history.events)) {
          return "Screening history events are missing from this CommandView artifact.";
        }
        break;
      }
      default:
        return `Requirement ${requirement} is not satisfied yet.`;
    }
  }

  return null;
}

const LEVEL_NODE_THRESHOLD = 50;
const COMPLEXITY_THRESHOLDS = {
  caution: 10,
  alert: 15,
};
const COVERAGE_THRESHOLDS = {
  strong: 0.85,
  caution: 0.75,
  alert: 0.6,
};
const AGGREGATE_FUNCTION_THRESHOLDS = {
  caution: 50,
  alert: 100,
  critical: 200,
};

const NODE_STYLE_PALETTE = Object.freeze({
  aggregate: {
    baseFill: "#1f2933",
    baseStroke: "#94a3b8",
    cautionFill: "#78350f",
    cautionStroke: "#f59e0b",
    alertFill: "#7f1d1d",
    alertStroke: "#f97316",
    criticalFill: "#450a0a",
    criticalStroke: "#f87171",
  },
  function: {
    baseFill: "#0f172a",
    baseStroke: "#38bdf8",
    focusFill: "#1d4ed8",
    focusStroke: "#93c5fd",
    cautionFill: "#78350f",
    cautionStroke: "#f59e0b",
    alertFill: "#7f1d1d",
    alertStroke: "#f87171",
    strongStroke: "#22c55e",
    weakStroke: "#f97316",
    alertCoverageStroke: "#ef4444",
  },
});

const payloadCache = new Map();

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
  levelSelections: {
    rootId: null,
    domainId: null,
    moduleId: null,
    functionId: null,
  },
  renderInteractions: new Map(),
  activeViews: [],
  activeViewIndex: -1,
  zoom: {
    scale: 1,
    translateX: 0,
    translateY: 0,
    isPanning: false,
    startX: 0,
    startY: 0,
  },
  sidebar: {
    width: 300,
    isResizing: false,
    startX: 0,
    startWidth: 0,
  },
};

const selectionMemory = new Map();

const headerUi = {
  refreshButton: null,
  exportButton: null,
};

const levelUi = {
  buttons: new Map(),
  sidebar: null,
};

const breadcrumbUi = {
  container: null,
};

const packUi = {
  container: null,
};

const viewTabsUi = {
  container: null,
};

function resetRenderInteractions() {
  state.renderInteractions.clear();
}

function registerRenderInteraction(elementId, handler) {
  if (!elementId || typeof handler !== "function") {
    return;
  }
  state.renderInteractions.set(elementId, handler);
}

function updateExportButtonState() {
  if (!headerUi.exportButton) {
    headerUi.exportButton = document.getElementById("export-button");
  }
  const button = headerUi.exportButton;
  if (!button) {
    return;
  }
  const hasDefinition = typeof state.diagramDefinition === "string" && state.diagramDefinition.trim().length > 0;
  button.disabled = !hasDefinition;
}

function buildMemoryKeys(option) {
  if (!option) {
    return [];
  }
  const keys = [];
  const relativePath = option.relative_path ?? option.path ?? null;
  if (relativePath) {
    keys.push(`path:${relativePath}`);
  }
  const slug = option.slug ?? null;
  if (slug) {
    keys.push(`slug:${slug}`);
  }
  return keys;
}

function persistActiveSelectionMemory() {
  if (!state.activeOption || !state.levels) {
    return;
  }

  const keys = buildMemoryKeys(state.activeOption);
  if (keys.length === 0) {
    return;
  }

  const memory = {
    currentLevel: state.currentLevel,
    selections: {
      rootId: state.levelSelections.rootId,
      domainId: state.levelSelections.domainId,
      moduleId: state.levelSelections.moduleId,
      functionId: state.levelSelections.functionId,
    },
  };

  keys.forEach((key) => {
    selectionMemory.set(key, memory);
  });
}

function restoreSelectionMemory(option) {
  if (!option) {
    return;
  }
  const keys = buildMemoryKeys(option);
  let memory = null;
  for (const key of keys) {
    const stored = selectionMemory.get(key);
    if (stored) {
      memory = stored;
      break;
    }
  }
  if (!memory) {
    return;
  }

  if (memory.selections) {
    if (memory.selections.rootId) {
      state.levelSelections.rootId = memory.selections.rootId;
    }
    if (memory.selections.domainId) {
      state.levelSelections.domainId = memory.selections.domainId;
    }
    if (memory.selections.moduleId) {
      state.levelSelections.moduleId = memory.selections.moduleId;
    }
    if (memory.selections.functionId) {
      state.levelSelections.functionId = memory.selections.functionId;
    }
  }

  if (memory.currentLevel) {
    state.currentLevel = memory.currentLevel;
  }
}

function getViewerConfig() {
  return window.viewerConfig ?? {};
}

function ensureTrailingSlash(value) {
  return value.endsWith("/") ? value : `${value}/`;
}

function resolveReportsBaseUrl() {
  const { reportsBaseUrl } = getViewerConfig();
  const base = reportsBaseUrl && typeof reportsBaseUrl === "string" && reportsBaseUrl.trim().length > 0
    ? reportsBaseUrl.trim()
    : DEFAULT_REPORTS_BASE_URL;

  if (/\.json$/i.test(base)) {
    const lastSlash = base.lastIndexOf("/");
    return lastSlash >= 0 ? ensureTrailingSlash(base.slice(0, lastSlash)) : "";
  }

  return ensureTrailingSlash(base);
}

function buildArtifactUrl(relativePath) {
  if (!relativePath) {
    throw new Error("Relative path is required to load artifacts");
  }
  if (ABSOLUTE_URL_PATTERN.test(relativePath) || relativePath.startsWith("/")) {
    return relativePath;
  }
  const base = resolveReportsBaseUrl();
  return `${base}${relativePath}`;
}

function sanitizeFilenameSegment(value, fallback) {
  const base = typeof value === "string" && value.trim().length > 0 ? value.trim().toLowerCase() : fallback;
  const sanitized = base.replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "");
  return sanitized || fallback;
}

function buildDiagramExportFilename() {
  const slug = sanitizeFilenameSegment(state.activeOption?.slug ?? state.activeOption?.label ?? "commandview", "commandview");
  const activeViewDescriptor = Array.isArray(state.activeViews) && state.activeViewIndex >= 0
    ? state.activeViews[state.activeViewIndex]
    : null;
  const mode = activeViewDescriptor?.viewId ?? state.currentLevel ?? "level";
  const level = sanitizeFilenameSegment(mode, "level");
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  return `${slug}-${level}-${timestamp}.mmd`;
}

function deriveScreeningRelativePath(relativePath) {
  const screeningPath = relativePath.replace(
    /_commandview_(\d{8}-\d{4})\.json$/,
    "_commandview_screening_$1.json"
  );
  if (screeningPath === relativePath) {
    throw new Error(`Unable to derive screening payload path for ${relativePath}`);
  }
  return screeningPath;
}

function clearDiagram() {
  const container = document.getElementById("diagram");
  if (container) {
    container.innerHTML = "";
  }
  state.diagramDefinition = null;
  updateExportButtonState();
}

function initializeMermaid() {
  if (!window.mermaid) {
    throw new Error("Mermaid library failed to load");
  }
  window.mermaid.initialize({ startOnLoad: false, theme: "dark" });
}

function updateStatus(message) {
  const panel = document.getElementById("status-panel");
  if (panel) {
    panel.textContent = message;
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-cache" });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

async function loadCommandViewPayloads(option) {
  console.log("[loadCommandViewPayloads] Loading option:", option);
  const cacheKey = buildCacheKey(option);
  const cached = payloadCache.get(cacheKey);
  if (cached) {
    console.log("[loadCommandViewPayloads] Using cached data");
    state.inventoryPayload = cached.inventory;
    state.screeningPayload = cached.screening;
    state.inventoryUrl = cached.inventoryUrl;
    state.screeningUrl = cached.screeningUrl;
    state.normalizedData = cached.normalized;
    state.levels = cached.levels ?? cached.normalized?.levels ?? null;
    return cached;
  }

  state.inventoryPayload = null;
  state.screeningPayload = null;
  state.inventoryUrl = null;
  state.screeningUrl = null;
  state.normalizedData = null;

  const inventoryUrl = buildArtifactUrl(option.relative_path);
  const screeningRelativePath = deriveScreeningRelativePath(option.relative_path);
  const screeningUrl = buildArtifactUrl(screeningRelativePath);

  console.log("[loadCommandViewPayloads] Inventory URL:", inventoryUrl);
  console.log("[loadCommandViewPayloads] Screening URL:", screeningUrl);

  const [inventory, screening] = await Promise.all([
    fetchJson(inventoryUrl),
    fetchJson(screeningUrl).catch((error) => {
      console.warn("[loadCommandViewPayloads] Screening payload load failed", error);
      return null;
    }),
  ]);

  console.log("[loadCommandViewPayloads] Inventory loaded, files:", inventory?.files?.length);

  validateInventorySchema(inventory);

  state.inventoryPayload = inventory;
  state.inventoryUrl = inventoryUrl;
  state.screeningPayload = screening;
  state.screeningUrl = screening ? screeningUrl : null;
  state.normalizedData = normalizeCommandViewData(inventory, screening);
  state.levels = state.normalizedData.levels ?? null;

  const record = {
    inventory,
    screening,
    inventoryUrl,
    screeningUrl: screening ? screeningUrl : null,
    normalized: state.normalizedData,
    hierarchy: state.normalizedData.hierarchy,
    levels: state.levels,
  };

  payloadCache.set(cacheKey, record);

  return record;
}

function buildCacheKey(option) {
  const slug = option?.slug ?? "unknown";
  const path = option?.relative_path ?? "";
  const timestamp = option?.timestamp ?? option?.label ?? "";
  return `${slug}|${path}|${timestamp}`;
}

function normalizeCommandViewData(inventory, screening) {
  if (!inventory || typeof inventory !== "object") {
    throw new Error("Inventory payload is missing or invalid");
  }

  const files = Array.isArray(inventory.files) ? inventory.files : [];
  const modules = new Map();
  const functions = new Map();
  const functionCallGraph = new Map();
  const screeningHistory = buildScreeningHistory(screening);

  files.forEach((file) => {
    const moduleRecord = createModuleRecord(file);
    if (!moduleRecord) {
      return;
    }
    modules.set(moduleRecord.id, moduleRecord);

    const functionIds = [];
    const functionEntries = Array.isArray(file.functions) ? file.functions : [];
    functionEntries.forEach((fn) => {
      const functionRecord = createFunctionRecord(fn, moduleRecord.id);
      if (!functionRecord) {
        return;
      }
      functionIds.push(functionRecord.id);
      functions.set(functionRecord.id, functionRecord);
      functionCallGraph.set(functionRecord.id, functionRecord.calls);
    });
    moduleRecord.functions = functionIds;
  });

  const callGraph = {
    functions: functionCallGraph,
    screening: buildScreeningCallIndex(screening),
  };

  const metrics = buildMetricsCache(inventory, modules, functions, screening);
  const hierarchy = buildHierarchyMetadata(modules, functions, callGraph);
  const levels = buildViewLevels(modules, functions, hierarchy, callGraph);

  return {
    modules,
    functions,
    callGraph,
    metrics,
    hierarchy,
    levels,
    screeningHistory,
  };
}

function createModuleRecord(file) {
  if (!file || typeof file !== "object") {
    return null;
  }

  const moduleId = file.module_id || file.relative_path || file.path;
  if (!moduleId) {
    return null;
  }

  return {
    id: moduleId,
    moduleId,
    relativePath: file.relative_path ?? null,
    absolutePath: file.path ?? null,
    packageName: typeof moduleId === "string" ? moduleId.split(".")[0] : null,
    callGraphSummary: file.call_graph?.summary ?? null,
    dependencySummary: file.dependency_summary ?? null,
    coverageSignals: file.coverage_signals ?? null,
    gitChurn: file.git_churn ?? null,
    lineCount: file.line_count ?? null,
    functions: [],
  };
}

function createFunctionRecord(fn, moduleId) {
  if (!fn || typeof fn !== "object") {
    return null;
  }

  const fallbackName = fn.name || "anonymous";
  const functionId = fn.qualified_name || (moduleId ? `${moduleId}::${fallbackName}` : null);
  if (!functionId) {
    return null;
  }

  const calls = Array.isArray(fn.calls)
    ? fn.calls
        .map((call) => call?.callee || call?.qualified_name || call?.attribute || null)
        .filter(Boolean)
    : [];

  return {
    id: functionId,
    name: fn.name ?? functionId,
    moduleId,
    lineno: fn.line ?? fn.lineno ?? null,
    signature: fn.signature ?? null,
    returnsKind: fn.returns_kind ?? null,
    cyclomaticComplexity: fn.cyclomatic_complexity ?? null,
    typeHintCoverage: fn.type_hint_coverage ?? null,
    annotationCoverage: fn.annotation_quality?.coverage ?? null,
    docstringQuality: fn.docstring_quality ?? null,
    todoTags: fn.todo_tags ?? 0,
    localsSummary: fn.locals_summary ?? null,
    metrics: {
      coverage: fn.coverage ?? null,
      lineCount: fn.line_count ?? null,
    },
    calls,
  };
}

function buildScreeningCallIndex(screening) {
  if (!screening || typeof screening !== "object") {
    return new Map();
  }

  const edges = screening.graphs?.calls;
  if (!Array.isArray(edges)) {
    return new Map();
  }

  const index = new Map();
  edges.forEach((edge) => {
    if (!Array.isArray(edge) || edge.length < 2) {
      return;
    }
    const [source, target] = edge;
    if (!source || !target) {
      return;
    }
    const existing = index.get(source) ?? [];
    if (!existing.includes(target)) {
      existing.push(target);
      index.set(source, existing);
    }
  });
  return index;
}

function buildScreeningHistory(screening) {
  if (!screening || typeof screening !== "object") {
    return {
      events: [],
      packs: new Map(),
      latest: null,
    };
  }

  const historyEntries = Array.isArray(screening.score_history) ? [...screening.score_history] : [];
  if (historyEntries.length === 0 && screening.score_snapshot && typeof screening.score_snapshot === "object") {
    historyEntries.push(screening.score_snapshot);
  }
  const events = [];
  const packs = new Map();

  historyEntries.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }

    const timestamp = typeof entry.timestamp === "string" ? entry.timestamp : null;
    const context = typeof entry.context === "object" && entry.context !== null ? entry.context : {};
    const packEntries = Array.isArray(entry.packs) ? entry.packs : [];

    packEntries.forEach((pack) => {
      if (!pack || typeof pack !== "object") {
        return;
      }

      const packId = typeof pack.id === "string" && pack.id.trim() ? pack.id : null;
      const packLabel = typeof pack.label === "string" && pack.label.trim() ? pack.label : null;
      let scoreValue = null;
      if (pack.score !== null && pack.score !== undefined && pack.score !== "") {
        const numericScore = Number(pack.score);
        if (Number.isFinite(numericScore)) {
          scoreValue = numericScore;
        }
      }
      const severity = typeof pack.severity === "string" ? pack.severity : "unknown";
      const thresholds = typeof pack.thresholds === "object" && pack.thresholds !== null ? pack.thresholds : {};
      let warning = null;
      if (thresholds.warning !== null && thresholds.warning !== undefined && thresholds.warning !== "") {
        const warningThreshold = Number(thresholds.warning);
        if (Number.isFinite(warningThreshold)) {
          warning = warningThreshold;
        }
      }
      let failure = null;
      if (thresholds.failure !== null && thresholds.failure !== undefined && thresholds.failure !== "") {
        const failureThreshold = Number(thresholds.failure);
        if (Number.isFinite(failureThreshold)) {
          failure = failureThreshold;
        }
      }

      const event = {
        timestamp,
        packId,
        packLabel,
        severity,
        score: scoreValue,
        thresholds: {
          warning,
          failure,
        },
        context,
        metrics: typeof pack.metrics === "object" && pack.metrics !== null ? pack.metrics : {},
      };

      events.push(event);

      const key = packId ?? packLabel ?? "unknown";
      const bucket = packs.get(key) ?? [];
      bucket.push(event);
      packs.set(key, bucket);
    });
  });

  events.sort((left, right) => {
    const leftTimestamp = left.timestamp ?? "";
    const rightTimestamp = right.timestamp ?? "";
    return leftTimestamp.localeCompare(rightTimestamp);
  });

  packs.forEach((bucket, key) => {
    bucket.sort((left, right) => {
      const leftTimestamp = left.timestamp ?? "";
      const rightTimestamp = right.timestamp ?? "";
      return leftTimestamp.localeCompare(rightTimestamp);
    });
    packs.set(key, bucket);
  });

  return {
    events,
    packs,
    latest: events.length > 0 ? events[events.length - 1] : null,
  };
}

function buildMetricsCache(inventory, modules, functions, screening) {
  const moduleMetrics = new Map();
  modules.forEach((moduleRecord, moduleId) => {
    moduleMetrics.set(moduleId, {
      gitChurn: moduleRecord.gitChurn ?? null,
      coverageSignals: moduleRecord.coverageSignals ?? null,
      lineCount: moduleRecord.lineCount ?? null,
    });
  });

  const functionMetrics = new Map();
  functions.forEach((functionRecord, functionId) => {
    functionMetrics.set(functionId, {
      complexity: functionRecord.cyclomaticComplexity ?? null,
      coverage: functionRecord.metrics.coverage ?? null,
      lineCount: functionRecord.metrics.lineCount ?? null,
      todoTags: functionRecord.todoTags ?? 0,
    });
  });

  return {
    repository: inventory?.statistics ?? {},
    modules: moduleMetrics,
    functions: functionMetrics,
    screening: screening?.statistics ?? screening?.summary ?? {},
  };
}

function validateInventorySchema(inventory) {
  const version = inventory?.schema_version;
  if (typeof version !== "number") {
    throw new Error("CommandView inventory is missing schema_version.");
  }
  if (!SUPPORTED_INVENTORY_SCHEMA_VERSIONS.has(version)) {
    throw new Error(`Unsupported CommandView schema_version ${version}.`);
  }
}

function buildHierarchyMetadata(modules, functions, callGraph) {
  const rootBuckets = new Map();
  const domainBuckets = new Map();

  modules.forEach((moduleRecord) => {
    const root = deriveRootSegment(moduleRecord.moduleId);
    const domain = deriveDomainId(moduleRecord.moduleId);
    const moduleFunctions = moduleRecord.functions ?? [];

    const rootBucket = rootBuckets.get(root) ?? createHierarchyBucket(root, null);
    appendModuleData(rootBucket, moduleRecord.id, moduleFunctions);
    rootBuckets.set(root, rootBucket);

    const domainBucket = domainBuckets.get(domain) ?? createHierarchyBucket(domain, root);
    appendModuleData(domainBucket, moduleRecord.id, moduleFunctions);
    domainBuckets.set(domain, domainBucket);
  });

  const moduleNodes = Array.from(modules.values()).map((moduleRecord) => ({
    id: moduleRecord.id,
    moduleId: moduleRecord.moduleId,
    relativePath: moduleRecord.relativePath,
    packageName: moduleRecord.packageName,
    domainId: deriveDomainId(moduleRecord.moduleId),
    functionCount: moduleRecord.functions?.length ?? 0,
  }));

  const functionNodes = Array.from(functions.values()).map((functionRecord) => ({
    id: functionRecord.id,
    moduleId: functionRecord.moduleId,
    name: functionRecord.name,
    metrics: functionRecord.metrics,
  }));

  const neighborhood = new Map();
  const runtimeEdges = callGraph.functions ?? new Map();
  const screeningEdges = callGraph.screening ?? new Map();
  functions.forEach((_functionRecord, functionId) => {
    const adjacency = new Set();
    (runtimeEdges.get(functionId) ?? []).forEach((target) => adjacency.add(target));
    (screeningEdges.get(functionId) ?? []).forEach((target) => adjacency.add(target));
    neighborhood.set(functionId, Array.from(adjacency));
  });

  return {
    root: serializeHierarchyBuckets(rootBuckets),
    domain: serializeHierarchyBuckets(domainBuckets),
    module: moduleNodes.sort((a, b) => a.id.localeCompare(b.id)),
    function: functionNodes.sort((a, b) => a.id.localeCompare(b.id)),
    neighborhood,
  };
}

function createHierarchyBucket(id, parentId) {
  return {
    id,
    parentId,
    modules: new Set(),
    functions: new Set(),
  };
}

function appendModuleData(bucket, moduleId, functionIds) {
  bucket.modules.add(moduleId);
  functionIds.forEach((fnId) => bucket.functions.add(fnId));
}

function serializeHierarchyBuckets(buckets) {
  return Array.from(buckets.values())
    .map((bucket) => ({
      id: bucket.id,
      parentId: bucket.parentId,
      moduleCount: bucket.modules.size,
      functionCount: bucket.functions.size,
    }))
    .sort((a, b) => a.id.localeCompare(b.id));
}

function deriveRootSegment(moduleId) {
  if (!moduleId || typeof moduleId !== "string") {
    return "root";
  }
  const sanitized = moduleId.replace(/\//g, ".");
  const [root] = sanitized.split(".");
  return root || "root";
}

function deriveDomainId(moduleId) {
  if (!moduleId || typeof moduleId !== "string") {
    return "root";
  }
  const segments = moduleId.replace(/\//g, ".").split(".");
  if (segments.length >= 2) {
    return `${segments[0]}.${segments[1]}`;
  }
  return segments[0] ?? "root";
}

function buildViewLevels(modules, functions, hierarchy, callGraph) {
  const level0 = buildRootLevel(hierarchy, functions, callGraph);
  const level1 = buildDomainLevel(hierarchy, functions, callGraph);
  const level2 = buildModuleLevel(modules, functions, callGraph);
  const level3 = buildFunctionLevelGraphs(modules, functions, callGraph);
  const level4 = buildNeighborhoodDetail(functions, hierarchy.neighborhood);
  return { level0, level1, level2, level3, level4 };
}

function buildRootLevel(hierarchy, functions, callGraph) {
  const nodes = hierarchy.root.map((bucket) => ({
    id: bucket.id,
    moduleCount: bucket.moduleCount,
    functionCount: bucket.functionCount,
  }));
  const edges = aggregateEdges(functions, callGraph, deriveRootSegment);
  return { nodes, edges };
}

function buildDomainLevel(hierarchy, functions, callGraph) {
  const nodes = hierarchy.domain.map((bucket) => ({
    id: bucket.id,
    parentId: bucket.parentId ?? null,
    moduleCount: bucket.moduleCount,
    functionCount: bucket.functionCount,
  }));
  const edges = aggregateEdges(functions, callGraph, deriveDomainId);
  return { nodes, edges };
}

function buildModuleLevel(modules, functions, callGraph) {
  const nodes = Array.from(modules.values())
    .map((moduleRecord) => ({
      id: moduleRecord.id,
      packageName: moduleRecord.packageName,
      functionCount: moduleRecord.functions?.length ?? 0,
      domainId: deriveDomainId(moduleRecord.moduleId),
      rootId: deriveRootSegment(moduleRecord.moduleId),
    }))
    .sort((a, b) => a.id.localeCompare(b.id));
  const edges = aggregateModuleEdges(functions, callGraph);
  return { nodes, edges };
}

function buildFunctionLevelGraphs(modules, functions, callGraph) {
  const moduleGraphs = new Map();
  const adjacency = callGraph.functions ?? new Map();
  modules.forEach((moduleRecord) => {
    const fnIds = moduleRecord.functions ?? [];
    const fnSet = new Set(fnIds);
    const nodes = fnIds
      .map((fnId) => functions.get(fnId))
      .filter(Boolean)
      .map((fn) => ({
        id: fn.id,
        name: fn.name,
        metrics: fn.metrics,
        complexity: fn.cyclomaticComplexity ?? null,
        coverage: fn.metrics?.coverage ?? null,
      }))
      .sort((a, b) => a.id.localeCompare(b.id));
    const edges = [];
    fnIds.forEach((fnId) => {
      const targets = adjacency.get(fnId) ?? [];
      targets.forEach((targetId) => {
        if (fnSet.has(targetId)) {
          edges.push({ source: fnId, target: targetId });
        }
      });
    });
    moduleGraphs.set(moduleRecord.id, { nodes, edges });
  });
  return moduleGraphs;
}

function buildNeighborhoodDetail(functions, neighborhood) {
  const detail = new Map();
  functions.forEach((functionRecord, functionId) => {
    const neighbors = neighborhood.get(functionId) ?? [];
    detail.set(functionId, {
      focus: {
        id: functionRecord.id,
        moduleId: functionRecord.moduleId,
        name: functionRecord.name,
        metrics: functionRecord.metrics,
        complexity: functionRecord.cyclomaticComplexity ?? null,
        coverage: functionRecord.metrics?.coverage ?? null,
      },
      neighbors: neighbors
        .map((neighborId) => functions.get(neighborId))
        .filter(Boolean)
        .map((fn) => ({
          id: fn.id,
          moduleId: fn.moduleId,
          name: fn.name,
          metrics: fn.metrics,
          complexity: fn.cyclomaticComplexity ?? null,
          coverage: fn.metrics?.coverage ?? null,
        })),
    });
  });
  return detail;
}

function aggregateEdges(functions, callGraph, groupingFn) {
  const moduleByFunction = new Map();
  functions.forEach((fn) => {
    moduleByFunction.set(fn.id, fn.moduleId);
  });
  const adjacency = callGraph.functions ?? new Map();
  const counts = new Map();
  adjacency.forEach((targets, sourceId) => {
    const sourceModule = moduleByFunction.get(sourceId);
    if (!sourceModule) {
      return;
    }
    const sourceGroup = groupingFn(sourceModule);
    targets.forEach((targetId) => {
      const targetModule = moduleByFunction.get(targetId);
      if (!targetModule) {
        return;
      }
      const targetGroup = groupingFn(targetModule);
      const key = `${sourceGroup}->${targetGroup}`;
      const count = counts.get(key) ?? 0;
      counts.set(key, count + 1);
    });
  });
  return Array.from(counts.entries()).map(([key, weight]) => {
    const [source, target] = key.split("->");
    return { source, target, weight };
  });
}

function aggregateModuleEdges(functions, callGraph) {
  const moduleByFunction = new Map();
  functions.forEach((fn) => {
    moduleByFunction.set(fn.id, fn.moduleId);
  });
  const adjacency = callGraph.functions ?? new Map();
  const counts = new Map();
  adjacency.forEach((targets, sourceId) => {
    const sourceModule = moduleByFunction.get(sourceId);
    if (!sourceModule) {
      return;
    }
    targets.forEach((targetId) => {
      const targetModule = moduleByFunction.get(targetId);
      if (!targetModule) {
        return;
      }
      const key = `${sourceModule}->${targetModule}`;
      const count = counts.get(key) ?? 0;
      counts.set(key, count + 1);
    });
  });
  return Array.from(counts.entries()).map(([key, weight]) => {
    const [source, target] = key.split("->");
    return { source, target, weight };
  });
}

function initializeLevelControls() {
  const buttonsContainer = document.getElementById("level-buttons");
  const sidebar = document.getElementById("level-sidebar");
  if (!buttonsContainer || !sidebar) {
    return;
  }

  levelUi.buttons.clear();
  buttonsContainer.innerHTML = "";

  LEVEL_DEFINITIONS.forEach((definition) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.level = definition.value;
    button.textContent = definition.label;
    button.addEventListener("click", () => {
      setLevel(definition.value);
    });
    levelUi.buttons.set(definition.value, button);
    buttonsContainer.appendChild(button);
  });

  levelUi.sidebar = sidebar;
  updateLevelButtonsState();
  renderLevelSidebar();
}

function updateLevelButtonsState() {
  levelUi.buttons.forEach((button, levelKey) => {
    const available = isLevelAvailable(levelKey);
    button.disabled = !available;
    button.classList.toggle("active", state.currentLevel === levelKey);
  });
}

function isLevelAvailable(levelKey) {
  if (!state.levels) {
    return false;
  }

  switch (levelKey) {
    case "level0":
    case "level1":
    case "level2": {
      const nodes = state.levels[levelKey]?.nodes ?? [];
      return Array.isArray(nodes) && nodes.length > 0;
    }
    case "level3":
      return state.levels.level3 instanceof Map && state.levels.level3.size > 0;
    case "level4":
      return state.levels.level4 instanceof Map && state.levels.level4.size > 0;
    default:
      return false;
  }
}

function ensureCurrentLevelIsAvailable() {
  if (isLevelAvailable(state.currentLevel)) {
    return;
  }
  const fallback = LEVEL_DEFINITIONS.find((definition) => isLevelAvailable(definition.value));
  state.currentLevel = fallback?.value ?? "level0";
}

function getLevelDefinition(levelKey) {
  return LEVEL_DEFINITIONS.find((definition) => definition.value === levelKey) ?? null;
}

function getLevelNodeCount(levelKey) {
  if (!state.levels) {
    return 0;
  }

  switch (levelKey) {
    case "level0":
    case "level1":
    case "level2": {
      const nodes = state.levels[levelKey]?.nodes ?? [];
      return Array.isArray(nodes) ? nodes.length : 0;
    }
    case "level3": {
      const moduleId = state.levelSelections.moduleId;
      const moduleGraphs = state.levels.level3 instanceof Map ? state.levels.level3 : null;
      const moduleGraph = moduleId && moduleGraphs ? moduleGraphs.get(moduleId) : null;
      const nodes = moduleGraph?.nodes ?? [];
      return Array.isArray(nodes) ? nodes.length : 0;
    }
    case "level4": {
      const functionId = state.levelSelections.functionId;
      const neighborhoods = state.levels.level4 instanceof Map ? state.levels.level4 : null;
      const detail = functionId && neighborhoods ? neighborhoods.get(functionId) : null;
      if (!detail) {
        return 0;
      }
      const neighbors = Array.isArray(detail.neighbors) ? detail.neighbors.length : 0;
      return 1 + neighbors;
    }
    default:
      return 0;
  }
}

function buildZoomSuggestion(levelKey, nodeCount) {
  if (!Number.isFinite(nodeCount) || nodeCount <= LEVEL_NODE_THRESHOLD) {
    return null;
  }

  switch (levelKey) {
    case "level0":
      return "Consider zooming to Level 1 to narrow the view.";
    case "level1":
      return "Consider zooming to Level 2 to explore modules.";
    case "level2":
      return "Consider zooming to Level 3 for function-level detail.";
    case "level3":
      return "Consider zooming to Level 4 to isolate a single function.";
    default:
      return null;
  }
}

function setLevel(levelKey) {
  if (!levelKey || !isLevelAvailable(levelKey)) {
    return;
  }

  if (Array.isArray(state.activeViews) && state.activeViews.length > 0) {
    clearActiveViewSelection({ suppressStatus: true });
  }

  if (state.currentLevel !== levelKey) {
    state.currentLevel = levelKey;
  }

  updateLevelButtonsState();
  renderLevelSidebar();
  renderBreadcrumb();
  void renderCurrentLevel();
}

function setLevelWithFallback(preferredLevel, fallbackLevels = []) {
  if (preferredLevel && isLevelAvailable(preferredLevel)) {
    setLevel(preferredLevel);
    return;
  }

  for (const levelKey of fallbackLevels) {
    if (isLevelAvailable(levelKey)) {
      setLevel(levelKey);
      return;
    }
  }

  ensureCurrentLevelIsAvailable();
  updateLevelButtonsState();
  renderLevelSidebar();
  renderBreadcrumb();
  void renderCurrentLevel();
}

function drillDownFromRoot(rootId) {
  if (!rootId) {
    return;
  }
  setRootSelection(rootId);
  setLevelWithFallback("level1", ["level2", "level3", "level4", "level0"]);
}

function drillDownFromDomain(domainId, parentId) {
  if (!domainId) {
    return;
  }
  if (parentId) {
    state.levelSelections.rootId = parentId;
  }
  setDomainSelection(domainId);
  setLevelWithFallback("level2", ["level3", "level4", "level1"]);
}

function drillDownFromModule(moduleId) {
  if (!moduleId) {
    return;
  }
  setModuleSelection(moduleId);
  setLevelWithFallback("level3", ["level4", "level2"]);
}

function drillDownFromFunction(functionId, moduleId) {
  if (!functionId) {
    return;
  }
  setFunctionSelection(functionId, moduleId);
  setLevelWithFallback("level4", ["level3"]);
}

function renderLevelSidebar() {
  if (!levelUi.sidebar) {
    levelUi.sidebar = document.getElementById("level-sidebar");
  }
  const sidebar = levelUi.sidebar;
  if (!sidebar) {
    return;
  }

  const options = collectSidebarEntries();
  sidebar.innerHTML = "";

  if (options.length === 0) {
    const item = document.createElement("li");
    item.classList.add("sidebar-empty");
    item.textContent = state.levels
      ? "This level has no data to display."
      : "Select a CommandView artifact to enable zoom levels.";
    sidebar.appendChild(item);
    return;
  }

  options.forEach((option) => {
    const item = document.createElement("li");
    if (option.message) {
      item.classList.add("sidebar-empty");
      item.textContent = option.message;
      sidebar.appendChild(item);
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.textContent = option.label;
    button.disabled = option.disabled ?? false;
    if (option.active) {
      button.classList.add("selected");
    }
    button.addEventListener("click", () => {
      applySidebarSelection(option.id);
    });
    item.appendChild(button);
    sidebar.appendChild(item);
  });
}

function initializeBreadcrumb() {
  breadcrumbUi.container = document.getElementById("breadcrumb");
  renderBreadcrumb();
}

function renderBreadcrumb() {
  if (!breadcrumbUi.container) {
    breadcrumbUi.container = document.getElementById("breadcrumb");
  }
  const container = breadcrumbUi.container;
  if (!container) {
    return;
  }

  const entries = collectBreadcrumbEntries();
  container.innerHTML = "";

  if (entries.length === 0) {
    const placeholder = document.createElement("span");
    placeholder.classList.add("breadcrumb-empty");
    placeholder.textContent = state.activeOption
      ? "Breadcrumb data unavailable for this selection."
      : "Select a CommandView artifact to begin.";
    container.appendChild(placeholder);
    return;
  }

  entries.forEach((entry, index) => {
    if (index > 0) {
      const separator = document.createElement("span");
      separator.classList.add("breadcrumb-separator");
      separator.textContent = ">";
      container.appendChild(separator);
    }

    if (entry.clickable) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = entry.label;
      button.addEventListener("click", () => {
        setLevel(entry.targetLevel);
      });
      container.appendChild(button);
      return;
    }

    const span = document.createElement("span");
    span.textContent = entry.label;
    if (entry.active) {
      span.classList.add("breadcrumb-current");
      span.setAttribute("aria-current", "page");
    } else {
      span.setAttribute("aria-current", "false");
    }
    container.appendChild(span);
  });
}

function collectBreadcrumbEntries() {
  if (!state.activeOption || !state.levels) {
    return [];
  }

  const entries = [];
  const currentLevel = state.currentLevel;

  const rootEntry = buildAggregateBreadcrumbEntry("level0", state.levelSelections.rootId, {
    active: currentLevel === "level0",
    targetLevel: "level0",
  });
  if (rootEntry) {
    entries.push(rootEntry);
  }

  if (state.levelSelections.domainId) {
    const domainEntry = buildAggregateBreadcrumbEntry("level1", state.levelSelections.domainId, {
      active: currentLevel === "level1",
      targetLevel: "level1",
    });
    if (domainEntry) {
      entries.push(domainEntry);
    }
  }

  const moduleEntry = buildModuleBreadcrumbEntry(state.levelSelections.moduleId, {
    active: currentLevel === "level2" || currentLevel === "level3",
  });
  if (moduleEntry) {
    entries.push(moduleEntry);
  }

  const functionEntry = buildFunctionBreadcrumbEntry(state.levelSelections.functionId, {
    active: currentLevel === "level4",
  });
  if (functionEntry) {
    entries.push(functionEntry);
  }

  return entries;
}

function buildAggregateBreadcrumbEntry(levelKey, nodeId, options) {
  const node = resolveAggregateNode(levelKey, nodeId);
  const label = formatBreadcrumbLabel(levelKey, node);
  if (!label) {
    return null;
  }

  const isAvailable = isLevelAvailable(levelKey);
  const active = options.active ?? false;
  const targetLevel = options.targetLevel ?? levelKey;

  return {
    label,
    targetLevel,
    active,
    clickable: isAvailable && !active,
  };
}

function buildModuleBreadcrumbEntry(moduleId, options) {
  if (!moduleId) {
    return null;
  }
  const node = resolveModuleNode(moduleId);
  const label = formatBreadcrumbLabel("level2", node);
  if (!label) {
    return null;
  }

  const targetLevel = isLevelAvailable("level3") ? "level3" : "level2";
  const active = options.active ?? false;

  const canNavigate = isLevelAvailable(targetLevel) && !active;
  return {
    label,
    targetLevel,
    active,
    clickable: canNavigate,
  };
}

function buildFunctionBreadcrumbEntry(functionId, options) {
  if (!functionId || !isLevelAvailable("level4")) {
    return null;
  }
  const record = resolveFunctionRecord(functionId);
  const label = formatBreadcrumbLabel("level4", record);
  if (!label) {
    return null;
  }

  const active = options.active ?? false;
  return {
    label,
    targetLevel: "level4",
    active,
    clickable: !active,
  };
}

function findMatchingOption(entries, previousOption) {
  if (!previousOption || !Array.isArray(entries)) {
    return null;
  }

  const relativePath = previousOption.relative_path ?? null;
  if (relativePath) {
    const matchByPath = findOptionByPredicate(entries, (option) => option.relative_path === relativePath);
    if (matchByPath) {
      return matchByPath;
    }
  }

  const slug = previousOption.slug ?? null;
  if (slug) {
    const matchBySlug = findOptionByPredicate(entries, (option) => option.slug === slug);
    if (matchBySlug) {
      return matchBySlug;
    }
  }

  return null;
}

function findOptionByPredicate(entries, predicate) {
  for (const entry of entries) {
    if (!entry || !Array.isArray(entry.options)) {
      continue;
    }
    for (const option of entry.options) {
      if (predicate(option ?? {})) {
        return option;
      }
    }
  }
  return null;
}

function resolveAggregateNode(levelKey, nodeId) {
  if (!state.levels || !nodeId) {
    return null;
  }
  const nodes = state.levels[levelKey]?.nodes ?? [];
  if (!Array.isArray(nodes)) {
    return null;
  }
  return nodes.find((node) => node.id === nodeId) ?? null;
}

function resolveModuleNode(moduleId) {
  if (!state.levels || !moduleId) {
    return null;
  }
  const nodes = state.levels.level2?.nodes ?? [];
  if (!Array.isArray(nodes)) {
    return null;
  }
  return nodes.find((node) => node.id === moduleId) ?? null;
}

function resolveFunctionRecord(functionId) {
  if (!state.normalizedData || !functionId) {
    return null;
  }
  const functionsMap = state.normalizedData.functions;
  if (functionsMap instanceof Map) {
    return functionsMap.get(functionId) ?? null;
  }
  return null;
}

function formatBreadcrumbLabel(levelKey, node) {
  if (!node) {
    switch (levelKey) {
      case "level0":
        return "Overview";
      case "level1":
        return "Domain";
      case "level2":
      case "level3":
        return "Module";
      case "level4":
        return "Function";
      default:
        return null;
    }
  }

  switch (levelKey) {
    case "level0":
    case "level1":
      return node.id ?? null;
    case "level2":
    case "level3":
      return node.id ?? null;
    case "level4":
      return node.name ?? node.id ?? null;
    default:
      return null;
  }
}

function collectSidebarEntries() {
  if (!state.levels) {
    return [];
  }

  switch (state.currentLevel) {
    case "level0": {
      const nodes = state.levels.level0?.nodes ?? [];
      return nodes.map((node) => ({
        id: node.id,
        label: formatAggregateLabel(node),
        active: state.levelSelections.rootId === node.id,
      }));
    }
    case "level1": {
      const nodes = state.levels.level1?.nodes ?? [];
      return nodes.map((node) => ({
        id: node.id,
        label: formatAggregateLabel(node),
        active: state.levelSelections.domainId === node.id,
      }));
    }
    case "level2": {
      const nodes = state.levels.level2?.nodes ?? [];
      return nodes.map((node) => ({
        id: node.id,
        label: formatModuleLabel(node),
        active: state.levelSelections.moduleId === node.id,
      }));
    }
    case "level3": {
      const nodes = state.levels.level2?.nodes ?? [];
      if (!Array.isArray(nodes) || nodes.length === 0) {
        return [{ message: "No modules recorded in this CommandView payload." }];
      }
      return nodes.map((node) => ({
        id: node.id,
        label: formatModuleLabel(node),
        active: state.levelSelections.moduleId === node.id,
      }));
    }
    case "level4": {
      const moduleId = state.levelSelections.moduleId;
      if (!moduleId) {
        return [{ message: "Select a module at Level 3 to inspect function neighborhoods." }];
      }
      const moduleGraphs = state.levels.level3 instanceof Map ? state.levels.level3 : null;
      const moduleGraph = moduleGraphs?.get(moduleId) ?? null;
      const nodes = moduleGraph?.nodes ?? [];
      if (!Array.isArray(nodes) || nodes.length === 0) {
        return [{ message: "Selected module has no functions recorded." }];
      }
      return nodes.map((node) => ({
        id: node.id,
        label: formatFunctionSidebarLabel(node),
        active: state.levelSelections.functionId === node.id,
      }));
    }
    default:
      return [];
  }
}

function formatAggregateLabel(node) {
  const modules = typeof node.moduleCount === "number" ? node.moduleCount : 0;
  const functions = typeof node.functionCount === "number" ? node.functionCount : 0;
  return `${node.id}\n${modules} modules, ${functions} functions`;
}

function formatModuleLabel(node) {
  const functions = typeof node.functionCount === "number" ? node.functionCount : 0;
  return `${node.id}\n${functions} functions`;
}

function formatFunctionSidebarLabel(node) {
  const parts = [node.name ?? node.id];
  const metrics = node.metrics ?? {};
  if (typeof metrics.lineCount === "number") {
    parts.push(`LOC ${metrics.lineCount}`);
  }
  if (typeof metrics.coverage === "number") {
    parts.push(`Cov ${formatCoveragePercent(metrics.coverage)}`);
  }
  return parts.join(" | ");
}

function applySidebarSelection(targetId) {
  if (!targetId) {
    return;
  }

  const changed = setLevelSelectionValue(state.currentLevel, targetId);
  if (!changed) {
    return;
  }

  synchronizeSelections();
  renderLevelSidebar();
  renderBreadcrumb();
  void renderCurrentLevel();
}

function getSelectionKeyForLevel(levelKey) {
  switch (levelKey) {
    case "level0":
      return "rootId";
    case "level1":
      return "domainId";
    case "level2":
    case "level3":
      return "moduleId";
    case "level4":
      return "functionId";
    default:
      return null;
  }
}

function setLevelSelectionValue(levelKey, targetId) {
  const selectionKey = getSelectionKeyForLevel(levelKey);
  if (!selectionKey) {
    return false;
  }

  if (state.levelSelections[selectionKey] === targetId) {
    return false;
  }

  state.levelSelections[selectionKey] = targetId;
  return true;
}

function synchronizeSelections() {
  if (!state.levels) {
    state.levelSelections.rootId = null;
    state.levelSelections.domainId = null;
    state.levelSelections.moduleId = null;
    state.levelSelections.functionId = null;
    return;
  }

  const level0Ids = (state.levels.level0?.nodes ?? []).map((node) => node.id);
  const level1Ids = (state.levels.level1?.nodes ?? []).map((node) => node.id);
  const moduleIds = (state.levels.level2?.nodes ?? []).map((node) => node.id);

  state.levelSelections.rootId = ensureSelectionInSet(state.levelSelections.rootId, level0Ids);
  state.levelSelections.domainId = ensureSelectionInSet(state.levelSelections.domainId, level1Ids);
  ensureDomainSelectionForRoot(state.levelSelections.rootId);
  state.levelSelections.moduleId = ensureSelectionInSet(state.levelSelections.moduleId, moduleIds);
  ensureModuleSelectionForDomain(state.levelSelections.domainId);

  ensureFunctionSelection();
}

function ensureFunctionSelection() {
  const moduleId = state.levelSelections.moduleId;
  const moduleGraphs = state.levels?.level3 instanceof Map ? state.levels.level3 : null;
  const moduleGraph = moduleId && moduleGraphs ? moduleGraphs.get(moduleId) : null;
  const functionIds = moduleGraph?.nodes?.map((node) => node.id) ?? [];
  state.levelSelections.functionId = ensureSelectionInSet(state.levelSelections.functionId, functionIds);
}

function ensureSelectionInSet(currentId, candidates) {
  if (!Array.isArray(candidates) || candidates.length === 0) {
    return null;
  }
  if (currentId && candidates.includes(currentId)) {
    return currentId;
  }
  return candidates[0];
}

function ensureDomainSelectionForRoot(rootId) {
  const domainNodes = Array.isArray(state.levels?.level1?.nodes) ? state.levels.level1.nodes : [];
  if (domainNodes.length === 0) {
    state.levelSelections.domainId = null;
    return;
  }

  const matching = typeof rootId === "string"
    ? domainNodes.filter((node) => node.parentId === rootId)
    : domainNodes;

  if (matching.length === 0) {
    if (!domainNodes.some((node) => node.id === state.levelSelections.domainId)) {
      state.levelSelections.domainId = domainNodes[0].id;
    }
    return;
  }

  if (!matching.some((node) => node.id === state.levelSelections.domainId)) {
    state.levelSelections.domainId = matching[0].id;
  }
}

function ensureModuleSelectionForDomain(domainId) {
  const moduleNodes = Array.isArray(state.levels?.level2?.nodes) ? state.levels.level2.nodes : [];
  if (moduleNodes.length === 0) {
    state.levelSelections.moduleId = null;
    return;
  }

  const matching = typeof domainId === "string"
    ? moduleNodes.filter((node) => node.domainId === domainId)
    : moduleNodes;

  if (matching.length === 0) {
    if (!moduleNodes.some((node) => node.id === state.levelSelections.moduleId)) {
      state.levelSelections.moduleId = moduleNodes[0].id;
    }
    return;
  }

  if (!matching.some((node) => node.id === state.levelSelections.moduleId)) {
    state.levelSelections.moduleId = matching[0].id;
  }
}

function getDomainNodeById(domainId) {
  if (!domainId || !Array.isArray(state.levels?.level1?.nodes)) {
    return null;
  }
  return state.levels.level1.nodes.find((node) => node.id === domainId) ?? null;
}

function getModuleNodeById(moduleId) {
  if (!moduleId || !Array.isArray(state.levels?.level2?.nodes)) {
    return null;
  }
  return state.levels.level2.nodes.find((node) => node.id === moduleId) ?? null;
}

function setRootSelection(rootId) {
  if (!rootId) {
    return;
  }
  state.levelSelections.rootId = rootId;
  ensureDomainSelectionForRoot(rootId);
  ensureModuleSelectionForDomain(state.levelSelections.domainId);
  ensureFunctionSelection();
}

function setDomainSelection(domainId) {
  if (!domainId) {
    return;
  }
  const domainNode = getDomainNodeById(domainId);
  if (domainNode?.parentId) {
    state.levelSelections.rootId = domainNode.parentId;
  }
  state.levelSelections.domainId = domainId;
  ensureDomainSelectionForRoot(state.levelSelections.rootId);
  ensureModuleSelectionForDomain(state.levelSelections.domainId);
  ensureFunctionSelection();
}

function setModuleSelection(moduleId) {
  if (!moduleId) {
    return;
  }
  const moduleNode = getModuleNodeById(moduleId);
  if (moduleNode?.rootId) {
    state.levelSelections.rootId = moduleNode.rootId;
  }
  if (moduleNode?.domainId) {
    state.levelSelections.domainId = moduleNode.domainId;
  }
  ensureDomainSelectionForRoot(state.levelSelections.rootId);
  state.levelSelections.moduleId = moduleId;
  ensureModuleSelectionForDomain(state.levelSelections.domainId);
  ensureFunctionSelection();
}

function setFunctionSelection(functionId, moduleId) {
  if (moduleId) {
    setModuleSelection(moduleId);
  }
  if (functionId) {
    state.levelSelections.functionId = functionId;
  }
  ensureFunctionSelection();
}

function buildMermaidDefinition(levelKey) {
  if (!state.levels) {
    return null;
  }

  switch (levelKey) {
    case "level0":
      return buildAggregateMermaid(
        state.levels.level0,
        (node) => formatAggregateLabel(node),
        (node, sanitizedId) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromRoot(node.id);
          });
        },
        (node, sanitizedId) => buildAggregateNodeStyle("level0", node, sanitizedId),
        (edge, source, target, label) => formatDottedEdge(edge, source, target, label)
      );
    case "level1":
      return buildAggregateMermaid(
        state.levels.level1,
        (node) => formatAggregateLabel(node),
        (node, sanitizedId) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromDomain(node.id, node.parentId ?? null);
          });
        },
        (node, sanitizedId) => buildAggregateNodeStyle("level1", node, sanitizedId),
        (edge, source, target, label) => formatDottedEdge(edge, source, target, label)
      );
    case "level2":
      return buildAggregateMermaid(
        state.levels.level2,
        (node) => formatModuleLabel(node),
        (node, sanitizedId) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromModule(node.id);
          });
        },
        (node, sanitizedId) => buildAggregateNodeStyle("level2", node, sanitizedId)
      );
    case "level3": {
      const moduleId = state.levelSelections.moduleId;
      const moduleGraphs = state.levels.level3 instanceof Map ? state.levels.level3 : null;
      const moduleGraph = moduleId && moduleGraphs ? moduleGraphs.get(moduleId) : null;
      if (!moduleId || !moduleGraph) {
        return null;
      }
      return buildModuleFunctionsMermaid(
        moduleId,
        moduleGraph,
        (node, sanitizedId) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromFunction(node.id, moduleId);
          });
        },
        (node, sanitizedId, isFocus) => buildFunctionNodeStyle(node, sanitizedId, isFocus)
      );
    }
    case "level4": {
      const functionId = state.levelSelections.functionId;
      const neighborhoods = state.levels.level4 instanceof Map ? state.levels.level4 : null;
      const detail = functionId && neighborhoods ? neighborhoods.get(functionId) : null;
      if (!detail) {
        return null;
      }
      return buildFunctionNeighborhoodMermaid(
        detail,
        (node, sanitizedId, isFocus) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromFunction(node.id, node.moduleId ?? null);
          });
        },
        (node, sanitizedId, isFocus) => buildFunctionNodeStyle(node, sanitizedId, isFocus)
      );
    }
    default:
      return null;
  }
}

function buildFunctionCallGraphViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modules = normalized.modules instanceof Map ? normalized.modules : null;
  const functionsMap = normalized.functions instanceof Map ? normalized.functions : null;
  const callGraph = normalized.callGraph?.functions instanceof Map ? normalized.callGraph.functions : null;

  if (!modules || modules.size === 0) {
    return { message: "No modules recorded in this CommandView artifact." };
  }

  if (!functionsMap || functionsMap.size === 0) {
    return { message: "No function records available to build a call graph." };
  }

  if (!callGraph || callGraph.size === 0) {
    return { message: "Call graph edges are not present in this CommandView artifact." };
  }

  let moduleId = state.levelSelections.moduleId;
  if (!moduleId || !modules.has(moduleId)) {
    const iterator = modules.keys();
    const firstKey = iterator.next();
    moduleId = !firstKey.done ? firstKey.value : null;
  }

  if (!moduleId || !modules.has(moduleId)) {
    return { message: "Select a module to render the function call graph view." };
  }

  const moduleRecord = modules.get(moduleId);
  const localFunctionIds = Array.isArray(moduleRecord?.functions) ? moduleRecord.functions : [];
  if (localFunctionIds.length === 0) {
    return { message: `Module ${moduleId} has no functions recorded in the CommandView inventory.` };
  }

  const localSet = new Set(localFunctionIds);
  const nodeIdMap = new Map();
  const nodeLines = [];
  const edgeSet = new Set();
  const edgeLines = [];
  const localNodeIds = new Set();
  const focusNodeIds = new Set();
  const focusFunctionId = state.levelSelections.functionId;

  const ensureNode = (functionId) => {
    if (nodeIdMap.has(functionId)) {
      return nodeIdMap.get(functionId);
    }
    const record = functionsMap.get(functionId);
    if (!record) {
      return null;
    }
    const sanitizedId = sanitizeMermaidId(functionId);
    nodeIdMap.set(functionId, sanitizedId);
    const isFocus = focusFunctionId === functionId;
    nodeLines.push({
      id: sanitizedId,
      label: formatFunctionNodeLabel(record, isFocus),
      isFocus,
    });
    if (isFocus) {
      focusNodeIds.add(sanitizedId);
    } else {
      localNodeIds.add(sanitizedId);
    }
    return sanitizedId;
  };

  localFunctionIds.forEach((functionId) => {
    ensureNode(functionId);
  });

  localFunctionIds.forEach((sourceId) => {
    const sanitizedSource = ensureNode(sourceId);
    if (!sanitizedSource) {
      return;
    }
    const targets = callGraph.get(sourceId) ?? [];
    targets.forEach((targetId) => {
      if (!localSet.has(targetId)) {
        return;
      }
      const sanitizedTarget = ensureNode(targetId);
      if (!sanitizedTarget) {
        return;
      }
      const edgeKey = `${sanitizedSource}->${sanitizedTarget}`;
      if (edgeSet.has(edgeKey)) {
        return;
      }
      edgeSet.add(edgeKey);
      edgeLines.push({ source: sanitizedSource, target: sanitizedTarget });
    });
  });

  const palette = NODE_STYLE_PALETTE.function;
  const lines = [
    "graph TD",
    `  classDef local fill:${palette.baseFill},stroke:${palette.baseStroke},color:#f8fafc;`,
    `  classDef focus fill:${palette.focusFill},stroke:${palette.focusStroke},color:#f8fafc;`,
  ];

  nodeLines.forEach((node) => {
    lines.push(`  ${node.id}["${escapeMermaidLabel(node.label)}"]`);
  });

  edgeLines.forEach((edge) => {
    lines.push(`  ${edge.source} --> ${edge.target}`);
  });

  if (localNodeIds.size > 0) {
    lines.push(`  class ${Array.from(localNodeIds).join(",")} local;`);
  }
  if (focusNodeIds.size > 0) {
    lines.push(`  class ${Array.from(focusNodeIds).join(",")} focus;`);
  }

  const nodeCount = nodeLines.length;
  const edgeCount = edgeLines.length;
  const label = `${moduleId} · Function Call Graph`;
  const statusMessage = edgeCount > 0
    ? `Rendered Function Call Graph for ${moduleId} (${nodeCount} functions, ${edgeCount} edges).`
    : `Rendered Function Call Graph for ${moduleId}; no intra-module call edges recorded.`;

  return {
    definition: lines.join("\n"),
    label,
    statusMessage,
  };
}

function buildFunctionInventoryOverviewViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modules = normalized.modules instanceof Map ? normalized.modules : null;
  const functionsMap = normalized.functions instanceof Map ? normalized.functions : null;

  if (!modules || modules.size === 0) {
    return { message: "No modules recorded in this CommandView artifact." };
  }

  const moduleCount = modules.size;
  const functionCount = functionsMap ? functionsMap.size : 0;

  let docstringTotal = 0;
  let docstringWith = 0;
  let typeCoverageTotal = 0;
  let typeCoverageSamples = 0;
  let todoFunctionCount = 0;

  if (functionsMap) {
    functionsMap.forEach((fn) => {
      docstringTotal += 1;
      const docQuality = fn?.docstringQuality ?? null;
      const hasDoc = Boolean(
        docQuality &&
        (docQuality.exists === true || docQuality.has_docstring === true || docQuality.present === true || docQuality.status === "present")
      );
      if (hasDoc) {
        docstringWith += 1;
      }

      const typeCoverage = Number(fn?.typeHintCoverage ?? fn?.annotationCoverage);
      if (Number.isFinite(typeCoverage)) {
        typeCoverageTotal += typeCoverage;
        typeCoverageSamples += 1;
      }

      const todoTags = Number(fn?.todoTags ?? 0);
      if (Number.isFinite(todoTags) && todoTags > 0) {
        todoFunctionCount += 1;
      }
    });
  }

  const docstringPercent = docstringTotal > 0 ? docstringWith / docstringTotal : null;
  const averageTypeCoverage = typeCoverageSamples > 0 ? typeCoverageTotal / typeCoverageSamples : null;

  const rootCounts = new Map();
  modules.forEach((moduleRecord) => {
    const moduleId = moduleRecord?.moduleId ?? moduleRecord?.id ?? "root";
    const root = deriveRootSegment(moduleId);
    rootCounts.set(root, (rootCounts.get(root) ?? 0) + 1);
  });
  const topRoots = Array.from(rootCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const lines = ["graph TD"];
  const centralLabel = `Inventory Overview\nModules: ${moduleCount}\nFunctions: ${functionCount}`;
  const centralId = sanitizeMermaidId("inventory_overview");
  lines.push(`  ${centralId}["${escapeMermaidLabel(centralLabel)}"]`);

  const docLabelLines = [`Docstrings`, `With: ${docstringWith}`];
  if (docstringTotal > docstringWith) {
    docLabelLines.push(`Missing: ${docstringTotal - docstringWith}`);
  }
  const docNodeId = sanitizeMermaidId("inventory_docstrings");
  lines.push(`  ${docNodeId}["${escapeMermaidLabel(docLabelLines.join("\\n"))}"]`);
  lines.push(`  ${centralId} --> ${docNodeId}`);

  const typeLines = ["Type Hints", `Tracked: ${typeCoverageSamples}`];
  if (Number.isFinite(averageTypeCoverage)) {
    typeLines.push(`Average: ${formatCoveragePercent(averageTypeCoverage)}`);
  }
  const typeNodeId = sanitizeMermaidId("inventory_type_hints");
  lines.push(`  ${typeNodeId}["${escapeMermaidLabel(typeLines.join("\\n"))}"]`);
  lines.push(`  ${centralId} --> ${typeNodeId}`);

  const todoNodeId = sanitizeMermaidId("inventory_todo_hotspots");
  const todoLabel = `TODO Hotspots\nFunctions flagged: ${todoFunctionCount}`;
  lines.push(`  ${todoNodeId}["${escapeMermaidLabel(todoLabel)}"]`);
  lines.push(`  ${centralId} --> ${todoNodeId}`);

  topRoots.forEach(([root, count]) => {
    const rootId = sanitizeMermaidId(`inventory_root_${root}`);
    const rootLabel = `${root}\nModules: ${count}`;
    lines.push(`  ${rootId}["${escapeMermaidLabel(rootLabel)}"]`);
    lines.push(`  ${centralId} --> ${rootId}`);
  });

  const docClass = sanitizeMermaidId("class_doc");
  const typeClass = sanitizeMermaidId("class_type");
  const todoClass = sanitizeMermaidId("class_todo");
  lines.push(`  classDef ${docClass} fill:#1d4ed8,stroke:#93c5fd,color:#eff6ff;`);
  lines.push(`  classDef ${typeClass} fill:#0f766e,stroke:#5eead4,color:#ecfeff;`);
  lines.push(`  classDef ${todoClass} fill:#7f1d1d,stroke:#fca5a5,color:#fee2e2;`);
  lines.push(`  class ${docNodeId} ${docClass};`);
  lines.push(`  class ${typeNodeId} ${typeClass};`);
  lines.push(`  class ${todoNodeId} ${todoClass};`);

  const statusMessage = `Rendered Function Inventory Overview (modules ${moduleCount}, functions ${functionCount}).`;

  return {
    definition: lines.join("\n"),
    label: "Health · Function Inventory Overview",
    statusMessage,
  };
}

function buildScreeningSignalTimelineViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized || !normalized.screeningHistory) {
    return { message: "Screening history has not been loaded for this CommandView artifact." };
  }

  const artifactLabel = state.activeOption?.label ?? state.activeOption?.slug ?? "CommandView Artifact";
  const result = buildScreeningTimelineDiagram(normalized.screeningHistory, { artifactLabel });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Screening Signal Timeline diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
  };
}

function buildTypeCoverageMapViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const functionsMap = normalized.functions instanceof Map ? normalized.functions : null;
  if (!functionsMap || functionsMap.size === 0) {
    return { message: "No functions recorded in this CommandView artifact." };
  }

  const buckets = {
    strong: [],
    moderate: [],
    weak: [],
    unknown: [],
  };

  const BUCKET_LIMIT = 8;

  functionsMap.forEach((fn) => {
    const coverage = Number(fn?.typeHintCoverage ?? fn?.annotationCoverage);
    const entry = {
      name: fn?.name ?? fn?.id ?? "anonymous",
      moduleId: fn?.moduleId ?? null,
      coverage,
    };

    if (!Number.isFinite(coverage)) {
      buckets.unknown.push(entry);
      return;
    }
    if (coverage >= 0.8) {
      buckets.strong.push(entry);
    } else if (coverage >= 0.5) {
      buckets.moderate.push(entry);
    } else {
      buckets.weak.push(entry);
    }
  });

  const lines = ["graph TD"];
  const centerId = sanitizeMermaidId("type_coverage_center");
  lines.push(`  ${centerId}["${escapeMermaidLabel("Type Coverage Map")}"]`);

  const bucketConfigs = [
    { key: "strong", title: "Strong ≥ 80%", className: "typeStrong", fill: "#166534", stroke: "#22c55e", color: "#ecfdf5" },
    { key: "moderate", title: "Moderate 50-79%", className: "typeModerate", fill: "#1f2937", stroke: "#60a5fa", color: "#e0f2fe" },
    { key: "weak", title: "Weak < 50%", className: "typeWeak", fill: "#7f1d1d", stroke: "#f87171", color: "#fee2e2" },
    { key: "unknown", title: "Unknown", className: "typeUnknown", fill: "#4b5563", stroke: "#cbd5f5", color: "#f1f5f9" },
  ];

  bucketConfigs.forEach((config) => {
    const entries = buckets[config.key] ?? [];
    const nodeId = sanitizeMermaidId(`type_bucket_${config.key}`);
    const count = entries.length;

    const formattedEntries = entries
      .slice(0, BUCKET_LIMIT)
      .map((entry) => {
        const coverageText = Number.isFinite(entry.coverage) ? formatCoveragePercent(entry.coverage) : "-";
        const moduleSuffix = entry.moduleId ? ` · ${entry.moduleId}` : "";
        return `${entry.name} (${coverageText})${moduleSuffix}`;
      });

    let labelLines = [`${config.title}`, `Functions: ${count}`];
    if (formattedEntries.length > 0) {
      labelLines = labelLines.concat(formattedEntries);
      if (count > formattedEntries.length) {
        labelLines.push(`+${count - formattedEntries.length} more`);
      }
    } else {
      labelLines.push("None recorded");
    }

    lines.push(`  ${nodeId}["${escapeMermaidLabel(labelLines.join("\\n"))}"]`);
    lines.push(`  ${centerId} --> ${nodeId}`);
    lines.push(
      `  classDef ${config.className} fill:${config.fill},stroke:${config.stroke},color:${config.color};`
    );
    lines.push(`  class ${nodeId} ${config.className};`);
  });

  const statusMessage = `Rendered Type Coverage Map (strong ${buckets.strong.length}, moderate ${buckets.moderate.length}, weak ${buckets.weak.length}, unknown ${buckets.unknown.length}).`;

  return {
    definition: lines.join("\n"),
    label: "Quality Metrics · Type Coverage Map",
    statusMessage,
  };
}

function buildAggregateMermaid(levelData, labelFactory, onNode, styleFactory, edgeFormatter) {
  if (!levelData || !Array.isArray(levelData.nodes) || levelData.nodes.length === 0) {
    return null;
  }

  const lines = ["graph LR"];
  const idMap = new Map();

  levelData.nodes.forEach((node) => {
    const sanitizedId = sanitizeMermaidId(node.id);
    idMap.set(node.id, sanitizedId);
    const label = labelFactory(node);
    lines.push(`  ${sanitizedId}["${escapeMermaidLabel(label)}"]`);
    if (typeof onNode === "function") {
      onNode(node, sanitizedId);
    }
    if (typeof styleFactory === "function") {
      const styleLine = styleFactory(node, sanitizedId);
      if (styleLine) {
        lines.push(styleLine);
      }
    }
  });

  const edges = Array.isArray(levelData.edges) ? levelData.edges : [];
  edges.forEach((edge) => {
    const source = idMap.get(edge.source);
    const target = idMap.get(edge.target);
    if (!source || !target) {
      return;
    }
    const weightLabel = typeof edge.weight === "number" && edge.weight > 1 ? `|${edge.weight}|` : "";
    if (typeof edgeFormatter === "function") {
      const formatted = edgeFormatter(edge, source, target, weightLabel);
      if (formatted) {
        lines.push(formatted);
      }
      return;
    }
    lines.push(`  ${source} -->${weightLabel} ${target}`);
  });

  return lines.join("\n");
}

function buildModuleFunctionsMermaid(moduleId, moduleGraph, onNode, styleFactory, edgeFormatter) {
  if (!moduleGraph || !Array.isArray(moduleGraph.nodes) || moduleGraph.nodes.length === 0) {
    return null;
  }

  const lines = ["graph TD"];
  const idMap = new Map();
  const sanitizedModuleId = sanitizeMermaidId(`module_${moduleId}`);
  lines.push(`  subgraph ${sanitizedModuleId}["${escapeMermaidLabel(moduleId)}"]`);

  moduleGraph.nodes.forEach((node) => {
    const sanitizedId = sanitizeMermaidId(node.id);
    idMap.set(node.id, sanitizedId);
    const label = formatFunctionNodeLabel(node, state.levelSelections.functionId === node.id);
    lines.push(`    ${sanitizedId}["${escapeMermaidLabel(label)}"]`);
    if (typeof onNode === "function") {
      onNode(node, sanitizedId);
    }
    if (typeof styleFactory === "function") {
      const styleLine = styleFactory(node, sanitizedId, state.levelSelections.functionId === node.id);
      if (styleLine) {
        lines.push(styleLine);
      }
    }
  });

  lines.push("  end");

  const edges = Array.isArray(moduleGraph.edges) ? moduleGraph.edges : [];
  edges.forEach((edge) => {
    const source = idMap.get(edge.source);
    const target = idMap.get(edge.target);
    if (!source || !target) {
      return;
    }
    if (typeof edgeFormatter === "function") {
      const formatted = edgeFormatter(edge, source, target);
      if (formatted) {
        lines.push(formatted);
      }
      return;
    }
    lines.push(`  ${source} --> ${target}`);
  });

  return lines.join("\n");
}

function formatFunctionNodeLabel(node, isFocus) {
  const parts = [];
  if (isFocus) {
    parts.push("Focus");
  }
  parts.push(node.name ?? node.id);
  const metrics = node.metrics ?? {};
  const metricParts = [];
  if (typeof metrics.lineCount === "number") {
    metricParts.push(`LOC ${metrics.lineCount}`);
  }
  if (typeof metrics.coverage === "number") {
    metricParts.push(`Cov ${formatCoveragePercent(metrics.coverage)}`);
  }
  if (metricParts.length > 0) {
    parts.push(metricParts.join(" | "));
  }
  if (!isFocus && node.moduleId) {
    parts.push(node.moduleId);
  }
  return parts.join("\n");
}

function buildAggregateNodeStyle(levelKey, node, sanitizedId) {
  const palette = NODE_STYLE_PALETTE.aggregate;
  let fill = palette.baseFill;
  let stroke = palette.baseStroke;
  let strokeWidth = "1.5px";

  const functionCount = typeof node.functionCount === "number" ? node.functionCount : null;
  const severity = classifyAggregateSeverity(functionCount);

  if (severity === "critical") {
    fill = palette.criticalFill;
    stroke = palette.criticalStroke;
    strokeWidth = "3px";
  } else if (severity === "alert") {
    fill = palette.alertFill;
    stroke = palette.alertStroke;
    strokeWidth = "2.5px";
  } else if (severity === "caution") {
    fill = palette.cautionFill;
    stroke = palette.cautionStroke;
    strokeWidth = "2px";
  }

  return `  style ${sanitizedId} fill:${fill},stroke:${stroke},stroke-width:${strokeWidth}`;
}

function buildFunctionNodeStyle(node, sanitizedId, isFocus) {
  const palette = NODE_STYLE_PALETTE.function;
  let fill = isFocus ? palette.focusFill : palette.baseFill;
  let stroke = isFocus ? palette.focusStroke : palette.baseStroke;
  let strokeWidth = isFocus ? "2px" : "1.5px";

  const complexity = resolveComplexityValue(node);
  const complexitySeverity = classifyComplexitySeverity(complexity);
  if (complexitySeverity === "alert") {
    fill = palette.alertFill;
    stroke = palette.alertStroke;
    strokeWidth = "3px";
  } else if (complexitySeverity === "caution") {
    fill = palette.cautionFill;
    stroke = palette.cautionStroke;
    strokeWidth = ensureStrokeWidth(strokeWidth, 2);
  }

  const coverage = resolveCoverageValue(node);
  const coverageClass = classifyCoverageState(coverage);
  if (coverageClass === "strong" && !complexitySeverity) {
    stroke = palette.strongStroke;
  } else if (coverageClass === "caution") {
    stroke = palette.weakStroke;
    strokeWidth = ensureStrokeWidth(strokeWidth, 2);
  } else if (coverageClass === "alert") {
    stroke = palette.alertCoverageStroke;
    strokeWidth = ensureStrokeWidth(strokeWidth, 2.5);
  }

  return `  style ${sanitizedId} fill:${fill},stroke:${stroke},stroke-width:${strokeWidth}`;
}

function classifyAggregateSeverity(functionCount) {
  if (!Number.isFinite(functionCount)) {
    return null;
  }
  if (functionCount >= AGGREGATE_FUNCTION_THRESHOLDS.critical) {
    return "critical";
  }
  if (functionCount >= AGGREGATE_FUNCTION_THRESHOLDS.alert) {
    return "alert";
  }
  if (functionCount >= AGGREGATE_FUNCTION_THRESHOLDS.caution) {
    return "caution";
  }
  return null;
}

function resolveComplexityValue(node) {
  if (Number.isFinite(node?.complexity)) {
    return Number(node.complexity);
  }
  if (Number.isFinite(node?.metrics?.complexity)) {
    return Number(node.metrics.complexity);
  }
  if (Number.isFinite(node?.metrics?.cyclomaticComplexity)) {
    return Number(node.metrics.cyclomaticComplexity);
  }
  return null;
}

function classifyComplexitySeverity(value) {
  if (!Number.isFinite(value)) {
    return null;
  }
  if (value >= COMPLEXITY_THRESHOLDS.alert) {
    return "alert";
  }
  if (value >= COMPLEXITY_THRESHOLDS.caution) {
    return "caution";
  }
  return null;
}

function resolveCoverageValue(node) {
  const metricsCoverage = node?.metrics?.coverage;
  if (Number.isFinite(metricsCoverage)) {
    return Number(metricsCoverage);
  }
  if (Number.isFinite(node?.coverage)) {
    return Number(node.coverage);
  }
  return null;
}

function classifyCoverageState(value) {
  if (!Number.isFinite(value)) {
    return null;
  }
  if (value < COVERAGE_THRESHOLDS.alert) {
    return "alert";
  }
  if (value < COVERAGE_THRESHOLDS.caution) {
    return "caution";
  }
  if (value >= COVERAGE_THRESHOLDS.strong) {
    return "strong";
  }
  return null;
}

function formatDottedEdge(edge, source, target, label) {
  const trimmedLabel = typeof label === "string" ? label.trim() : "";
  if (trimmedLabel) {
    return `  ${source} -. ${trimmedLabel} .-> ${target}`;
  }
  return `  ${source} -.-> ${target}`;
}

function ensureStrokeWidth(currentWidth, minimum) {
  const numeric = Number.parseFloat(typeof currentWidth === "string" ? currentWidth : String(currentWidth ?? ""));
  const safeBase = Number.isFinite(numeric) ? numeric : 0;
  const resolved = Math.max(safeBase, Number(minimum));
  return `${resolved}px`;
}

function buildFunctionNeighborhoodMermaid(detail, onNode, styleFactory, edgeFormatter) {
  if (!detail || !detail.focus) {
    return null;
  }

  const focus = detail.focus;
  const neighbors = Array.isArray(detail.neighbors) ? detail.neighbors : [];
  const lines = ["graph TD"];
  const idMap = new Map();

  const focusId = sanitizeMermaidId(focus.id);
  idMap.set(focus.id, focusId);
  lines.push(`  ${focusId}["${escapeMermaidLabel(formatFunctionNodeLabel(focus, true))}"]`);
  if (typeof onNode === "function") {
    onNode(focus, focusId, true);
  }
  if (typeof styleFactory === "function") {
    const focusStyle = styleFactory(focus, focusId, true);
    if (focusStyle) {
      lines.push(focusStyle);
    }
  }

  if (neighbors.length === 0) {
    const noteId = sanitizeMermaidId(`${focus.id}_note`);
    lines.push(`  ${noteId}["${escapeMermaidLabel("No neighbors recorded")}"]`);
    if (typeof edgeFormatter === "function") {
      const formattedNoteEdge = edgeFormatter({ source: focus.id, target: `${focus.id}_note` }, focusId, noteId);
      if (formattedNoteEdge) {
        lines.push(formattedNoteEdge);
      }
    } else {
      lines.push(`  ${focusId} --> ${noteId}`);
    }
    return lines.join("\n");
  }

  neighbors.forEach((neighbor) => {
    const sanitizedId = sanitizeMermaidId(neighbor.id);
    idMap.set(neighbor.id, sanitizedId);
    lines.push(`  ${sanitizedId}["${escapeMermaidLabel(formatFunctionNodeLabel(neighbor, false))}"]`);
    if (typeof onNode === "function") {
      onNode(neighbor, sanitizedId, false);
    }
    if (typeof styleFactory === "function") {
      const styleLine = styleFactory(neighbor, sanitizedId, false);
      if (styleLine) {
        lines.push(styleLine);
      }
    }
    if (typeof edgeFormatter === "function") {
      const formatted = edgeFormatter({ source: focus.id, target: neighbor.id }, focusId, sanitizedId);
      if (formatted) {
        lines.push(formatted);
      }
    } else {
      lines.push(`  ${focusId} --> ${sanitizedId}`);
    }
  });

  return lines.join("\n");
}

function escapeMermaidLabel(value) {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value)
    .replace(/\\/g, "\\\\")
    .replace(/"/g, "'")
    .replace(/\n/g, "<br/>");
}

let mermaidIdCounter = 0;

function sanitizeMermaidId(value) {
  if (!value || typeof value !== "string") {
    mermaidIdCounter += 1;
    return `node_${mermaidIdCounter}`;
  }
  const sanitized = value.replace(/[^a-zA-Z0-9_]/g, "_");
  if (!sanitized) {
    mermaidIdCounter += 1;
    return `node_${mermaidIdCounter}`;
  }
  if (/^[0-9]/.test(sanitized)) {
    return `n_${sanitized}`;
  }
  return sanitized;
}

function formatCoveragePercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "-";
  }
  if (numeric <= 1) {
    return `${Math.round(numeric * 100)}%`;
  }
  return `${Math.round(numeric)}%`;
}

function seedDefaultSelections() {
  if (!state.levels) {
    state.levelSelections.rootId = null;
    state.levelSelections.domainId = null;
    state.levelSelections.moduleId = null;
    state.levelSelections.functionId = null;
    return;
  }

  const level0Nodes = state.levels.level0?.nodes ?? [];
  const level1Nodes = state.levels.level1?.nodes ?? [];
  const moduleNodes = state.levels.level2?.nodes ?? [];

  state.levelSelections.rootId = level0Nodes[0]?.id ?? null;
  state.levelSelections.domainId = level1Nodes[0]?.id ?? null;
  state.levelSelections.moduleId = moduleNodes[0]?.id ?? null;

  ensureFunctionSelection();
}

async function renderCurrentLevel() {
  if (!state.activeOption) {
    clearDiagram();
    updateStatus("Select a CommandView artifact to render a diagram.");
    return;
  }

  const views = Array.isArray(state.activeViews) ? state.activeViews : [];
  const hasActiveView = views.length > 0 && state.activeViewIndex >= 0 && state.activeViewIndex < views.length;
  if (hasActiveView) {
    const handled = await renderActiveView();
    if (handled) {
      return;
    }
  }

  resetRenderInteractions();
  const definition = buildMermaidDefinition(state.currentLevel);
  const levelDefinition = getLevelDefinition(state.currentLevel);
  const levelLabel = levelDefinition?.label ?? state.currentLevel;

  if (!definition) {
    clearDiagram();
    updateStatus(`${levelLabel} has no data for ${state.activeOption.label}.`);
    return;
  }

  updateStatus(`Rendering ${levelLabel} for ${state.activeOption.label}…`);
  state.diagramDefinition = definition;
  updateExportButtonState();
  const rendered = await renderDiagram(definition);
  if (rendered) {
    const nodeCount = getLevelNodeCount(state.currentLevel);
    const nodeDetail = nodeCount > 0 ? ` (${nodeCount} nodes)` : "";
    const suggestion = buildZoomSuggestion(state.currentLevel, nodeCount);
    const baseMessage = `Rendered ${levelLabel} for ${state.activeOption.label}${nodeDetail}.`;
    updateStatus(suggestion ? `${baseMessage} ${suggestion}` : baseMessage);
  }
}

async function renderActiveView() {
  const views = Array.isArray(state.activeViews) ? state.activeViews : [];
  if (views.length === 0) {
    state.activeViewIndex = -1;
    return false;
  }

  if (state.activeViewIndex < 0 || state.activeViewIndex >= views.length) {
    state.activeViewIndex = views.length - 1;
  }

  const descriptor = views[state.activeViewIndex];
  if (!descriptor) {
    clearActiveViewSelection({ silent: true, suppressStatus: true });
    return false;
  }

  const metadata = getViewMetadata(descriptor.packId, descriptor.viewId);
  if (!metadata) {
    removeActiveView(state.activeViewIndex, { suppressRender: true, suppressStatus: true });
    return state.activeViewIndex >= 0 ? renderActiveView() : false;
  }

  const availability = evaluateViewAvailability(metadata.view);
  if (!availability.available || typeof availability.builder !== "function") {
    clearDiagram();
    state.diagramDefinition = null;
    updateExportButtonState();
    updateStatus(availability.reason ?? `View ${metadata.view.label} is not available for rendering yet.`);
    return true;
  }

  resetRenderInteractions();
  const builderResult = await Promise.resolve(
    availability.builder({
      state,
      pack: metadata.pack,
      view: metadata.view,
      descriptor,
    })
  );

  if (!builderResult || typeof builderResult.definition !== "string" || builderResult.definition.trim().length === 0) {
    clearDiagram();
    const fallbackMessage = builderResult?.message ?? `No diagram available for ${metadata.view.label} yet.`;
    updateStatus(fallbackMessage);
    state.diagramDefinition = null;
    updateExportButtonState();
    return true;
  }

  const label = builderResult.label ?? `${metadata.pack.title} · ${metadata.view.label}`;
  updateStatus(builderResult.preRenderMessage ?? `Rendering ${label}…`);
  state.diagramDefinition = builderResult.definition;
  updateExportButtonState();

  const rendered = await renderDiagram(builderResult.definition);
  if (rendered) {
    const successMessage = builderResult.statusMessage ?? `Rendered ${label}.`;
    updateStatus(successMessage);
  }

  return true;
}

async function renderDiagram(definition) {
  const container = document.getElementById("diagram");
  if (!container || !window.mermaid) {
    return false;
  }

  try {
    const renderKey = `viewer-diagram-${Date.now()}`;
    const { svg } = await window.mermaid.render(renderKey, definition);
    container.innerHTML = svg;
    attachRenderInteractions(container);
    initializeDiagramZoom(container);
    return true;
  } catch (error) {
    console.error("Mermaid render failed", error);
    updateStatus("Unable to render diagram preview (see console for details).");
    return false;
  }
}

function initializeDiagramZoom(container) {
  if (!container) return;

  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  // Reset zoom state when new diagram loads
  state.zoom.scale = 1;
  state.zoom.translateX = 0;
  state.zoom.translateY = 0;

  // Apply initial transform
  applyZoomTransform(svgElement);

  // Remove existing listeners to avoid duplicates
  container.removeEventListener('wheel', handleDiagramWheel);
  container.removeEventListener('mousedown', handleDiagramMouseDown);

  // Add zoom and pan event listeners
  container.addEventListener('wheel', handleDiagramWheel, { passive: false });
  container.addEventListener('mousedown', handleDiagramMouseDown);

  console.log('[initializeDiagramZoom] Zoom controls initialized');
}

function handleDiagramWheel(event) {
  event.preventDefault();
  
  const container = event.currentTarget;
  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  // Get mouse position relative to container
  const rect = container.getBoundingClientRect();
  const mouseX = event.clientX - rect.left;
  const mouseY = event.clientY - rect.top;

  // Calculate zoom delta (negative deltaY = zoom in)
  const zoomDelta = event.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.max(0.1, Math.min(200, state.zoom.scale * zoomDelta));

  // Adjust translation to zoom towards mouse position
  const scaleChange = newScale / state.zoom.scale;
  state.zoom.translateX = mouseX - (mouseX - state.zoom.translateX) * scaleChange;
  state.zoom.translateY = mouseY - (mouseY - state.zoom.translateY) * scaleChange;
  state.zoom.scale = newScale;

  applyZoomTransform(svgElement);
  updateZoomIndicator();
}

function handleDiagramMouseDown(event) {
  // Only pan with left mouse button or when space key is held
  if (event.button !== 0) return;

  const container = event.currentTarget;
  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  // Don't pan if clicking on an interactive element
  if (event.target.classList.contains('diagram-node-action')) {
    return;
  }

  state.zoom.isPanning = true;
  state.zoom.startX = event.clientX - state.zoom.translateX;
  state.zoom.startY = event.clientY - state.zoom.translateY;

  container.style.cursor = 'grabbing';

  const handleMouseMove = (e) => {
    if (!state.zoom.isPanning) return;
    
    state.zoom.translateX = e.clientX - state.zoom.startX;
    state.zoom.translateY = e.clientY - state.zoom.startY;
    
    applyZoomTransform(svgElement);
  };

  const handleMouseUp = () => {
    state.zoom.isPanning = false;
    container.style.cursor = 'grab';
    
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };

  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
}

function applyZoomTransform(svgElement) {
  if (!svgElement) return;
  
  const transform = `translate(${state.zoom.translateX}px, ${state.zoom.translateY}px) scale(${state.zoom.scale})`;
  svgElement.style.transform = transform;
  svgElement.style.transformOrigin = '0 0';
  svgElement.style.transition = 'transform 0.1s ease-out';
}

function updateZoomIndicator() {
  const indicator = document.getElementById('zoom-indicator');
  if (indicator) {
    indicator.textContent = `${Math.round(state.zoom.scale * 100)}%`;
  }
}

function resetDiagramZoom() {
  const container = document.getElementById('diagram');
  if (!container) return;

  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  state.zoom.scale = 1;
  state.zoom.translateX = 0;
  state.zoom.translateY = 0;

  applyZoomTransform(svgElement);
  updateZoomIndicator();
  updateStatus('Zoom reset to 100%');
}

function zoomIn() {
  const container = document.getElementById('diagram');
  if (!container) return;

  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  const rect = container.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  const newScale = Math.min(200, state.zoom.scale * 1.2);
  const scaleChange = newScale / state.zoom.scale;
  
  state.zoom.translateX = centerX - (centerX - state.zoom.translateX) * scaleChange;
  state.zoom.translateY = centerY - (centerY - state.zoom.translateY) * scaleChange;
  state.zoom.scale = newScale;

  applyZoomTransform(svgElement);
  updateZoomIndicator();
}

function zoomOut() {
  const container = document.getElementById('diagram');
  if (!container) return;

  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  const rect = container.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  const newScale = Math.max(0.1, state.zoom.scale * 0.8);
  const scaleChange = newScale / state.zoom.scale;
  
  state.zoom.translateX = centerX - (centerX - state.zoom.translateX) * scaleChange;
  state.zoom.translateY = centerY - (centerY - state.zoom.translateY) * scaleChange;
  state.zoom.scale = newScale;

  applyZoomTransform(svgElement);
  updateZoomIndicator();
}

function attachRenderInteractions(container) {
  if (!container || !(state.renderInteractions instanceof Map)) {
    return;
  }

  state.renderInteractions.forEach((handler, elementId) => {
    const safeId = typeof CSS !== "undefined" && typeof CSS.escape === "function"
      ? CSS.escape(elementId)
      : elementId.replace(/([^a-zA-Z0-9_-])/g, "\\$1");
    const target = container.querySelector(`#${safeId}`);
    if (!target) {
      return;
    }

    const invokeHandler = () => {
      try {
        handler();
      } catch (error) {
        console.error("Diagram interaction handler failed", error);
      }
    };

    const clickListener = (event) => {
      event.preventDefault();
      event.stopPropagation();
      invokeHandler();
    };

    const keyListener = (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        event.stopPropagation();
        invokeHandler();
      }
    };

    target.classList.add("diagram-node-action");
    target.setAttribute("tabindex", "0");
    target.setAttribute("role", "button");
    target.addEventListener("click", clickListener);
    target.addEventListener("keydown", keyListener);
  });
}

function renderViewPacks() {
  if (!packUi.container) {
    packUi.container = document.getElementById("view-pack-container");
  }

  if (!packUi.container) {
    return;
  }

  packUi.container.innerHTML = "";

  const activeViews = Array.isArray(state.activeViews) ? state.activeViews : [];

  VIEW_PACKS.forEach((pack) => {
    const section = document.createElement("section");
    section.className = "view-pack";

    const heading = document.createElement("h3");
    heading.className = "view-pack-heading";
    heading.textContent = pack.title;
    section.appendChild(heading);

    if (pack.description) {
      const packNote = document.createElement("p");
      packNote.className = "view-pack-note";
      packNote.textContent = pack.description;
      section.appendChild(packNote);
    }

    const list = document.createElement("ul");
    list.className = "view-pack-list";

    pack.views.forEach((view) => {
      const item = document.createElement("li");

      const button = document.createElement("button");
      button.type = "button";
      button.className = "view-pack-button";
      button.dataset.packId = pack.id;
      button.dataset.viewId = view.id;
      button.dataset.status = view.status ?? "planned";
      button.dataset.filename = view.filename ?? "";
      button.textContent = view.label;

      const availability = evaluateViewAvailability(view);
      const descriptorIndex = activeViews.findIndex((entry) => entry.packId === pack.id && entry.viewId === view.id);
      const isOpen = descriptorIndex >= 0;
      const isActive = isOpen && state.activeViewIndex === descriptorIndex;
      const canInteract = availability.available || isOpen;

      if (canInteract) {
        button.disabled = false;
        button.title = isOpen
          ? availability.reason
            ? `Open view (requirements pending: ${availability.reason})`
            : "Switch to this view tab."
          : "Select to render this view.";
        button.addEventListener("click", () => {
          selectView(pack.id, view.id);
        });
      } else {
        button.disabled = true;
        button.title = availability.reason ?? view.note ?? "View wiring pending implementation.";
      }

      if (isActive) {
        button.classList.add("selected");
        button.setAttribute("aria-pressed", "true");
      } else if (isOpen) {
        button.classList.add("open");
        button.setAttribute("aria-pressed", "mixed");
      } else {
        button.setAttribute("aria-pressed", "false");
      }

      item.appendChild(button);

      if (view.description) {
        const description = document.createElement("p");
        description.className = "view-pack-note";
        description.textContent = view.description;
        item.appendChild(description);
      }

      if (!availability.available) {
        if (availability.reason) {
          const availabilityNote = document.createElement("p");
          availabilityNote.className = "view-pack-note";
          availabilityNote.textContent = availability.reason;
          item.appendChild(availabilityNote);
        }
        if (view.note) {
          const note = document.createElement("p");
          note.className = "view-pack-note";
          note.textContent = view.note;
          item.appendChild(note);
        }
      } else if (view.note) {
        const note = document.createElement("p");
        note.className = "view-pack-note";
        note.textContent = view.note;
        item.appendChild(note);
      }

      list.appendChild(item);
    });

    section.appendChild(list);
    packUi.container.appendChild(section);
  });
}

function clearActiveViewSelection(options = {}) {
  const { silent = false, suppressStatus = false } = options ?? {};
  const hadSelection = Array.isArray(state.activeViews) && state.activeViews.length > 0;
  state.activeViews = [];
  state.activeViewIndex = -1;
  if (!silent) {
    renderViewPacks();
    renderViewTabs();
  }
  if (hadSelection && !suppressStatus) {
    updateStatus("View selection cleared; returning to zoom levels.");
  }
}

function selectView(packId, viewId) {
  const metadata = getViewMetadata(packId, viewId);
  if (!metadata) {
    updateStatus("Unable to locate the requested view definition.");
    return;
  }

  if (!Array.isArray(state.activeViews)) {
    state.activeViews = [];
  }

  const existingIndex = state.activeViews.findIndex((entry) => entry.packId === packId && entry.viewId === viewId);
  if (existingIndex >= 0) {
    state.activeViewIndex = existingIndex;
    renderViewPacks();
    renderViewTabs();
    updateStatus(`Displaying ${metadata.pack.title} · ${metadata.view.label}.`);
    void renderCurrentLevel();
    return;
  }

  const availability = evaluateViewAvailability(metadata.view);
  if (!availability.available) {
    updateStatus(availability.reason ?? "This view is not available yet.");
    return;
  }

  state.activeViews.push({ packId, viewId });
  state.activeViewIndex = state.activeViews.length - 1;
  renderViewPacks();
  renderViewTabs();
  updateStatus(`Preparing ${metadata.pack.title} · ${metadata.view.label}…`);
  void renderCurrentLevel();
}

function renderViewTabs() {
  if (!viewTabsUi.container) {
    viewTabsUi.container = document.getElementById("view-tabs");
  }

  const container = viewTabsUi.container;
  if (!container) {
    return;
  }

  const views = Array.isArray(state.activeViews) ? state.activeViews : [];
  container.innerHTML = "";
  container.classList.toggle("view-tabs-empty", views.length === 0);
  container.setAttribute("role", "tablist");

  const zoomButton = document.createElement("button");
  zoomButton.type = "button";
  zoomButton.className = "view-tab";
  zoomButton.dataset.tab = "zoom";
  zoomButton.setAttribute("role", "tab");
  zoomButton.textContent = "Zoom Levels";
  const zoomActive = views.length === 0 || state.activeViewIndex === -1;
  if (zoomActive) {
    zoomButton.classList.add("active");
  }
  zoomButton.setAttribute("aria-selected", zoomActive ? "true" : "false");
  zoomButton.addEventListener("click", () => {
    if (state.activeViewIndex !== -1 || views.length > 0) {
      clearActiveViewSelection({ suppressStatus: true });
      renderViewTabs();
      void renderCurrentLevel();
      updateStatus("Switched to zoom levels.");
    }
  });
  container.appendChild(zoomButton);

  views.forEach((descriptor, index) => {
    const metadata = getViewMetadata(descriptor.packId, descriptor.viewId);
    const label = metadata ? `${metadata.pack.title} · ${metadata.view.label}` : `${descriptor.packId} · ${descriptor.viewId}`;

    const wrapper = document.createElement("div");
    wrapper.className = "view-tab-wrapper";
    container.appendChild(wrapper);

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "view-tab";
    trigger.setAttribute("role", "tab");
    trigger.textContent = label;
    const isActive = state.activeViewIndex === index;
    trigger.setAttribute("aria-selected", isActive ? "true" : "false");
    if (isActive) {
      trigger.classList.add("active");
    }
    trigger.addEventListener("click", () => {
      if (state.activeViewIndex === index) {
        return;
      }
      state.activeViewIndex = index;
      renderViewPacks();
      renderViewTabs();
      updateStatus(`Displaying ${label}.`);
      void renderCurrentLevel();
    });
    wrapper.appendChild(trigger);

    const close = document.createElement("button");
    close.type = "button";
    close.className = "view-tab-close";
    close.setAttribute("aria-label", `Close ${label}`);
    close.textContent = "x";
    close.addEventListener("click", (event) => {
      event.stopPropagation();
      removeActiveView(index);
    });
    wrapper.appendChild(close);
  });
}

function removeActiveView(index, options = {}) {
  if (!Array.isArray(state.activeViews) || index < 0 || index >= state.activeViews.length) {
    return;
  }

  const { suppressRender = false, suppressStatus = false } = options ?? {};

  state.activeViews.splice(index, 1);
  if (state.activeViews.length === 0) {
    state.activeViewIndex = -1;
  } else if (state.activeViewIndex > index) {
    state.activeViewIndex -= 1;
  } else if (state.activeViewIndex >= state.activeViews.length) {
    state.activeViewIndex = state.activeViews.length - 1;
  } else if (state.activeViewIndex === index) {
    state.activeViewIndex = Math.min(index, state.activeViews.length - 1);
  }

  renderViewPacks();
  renderViewTabs();

  if (suppressRender) {
    return;
  }

  if (state.activeViewIndex >= 0) {
    const descriptor = state.activeViews[state.activeViewIndex];
    const metadata = descriptor ? getViewMetadata(descriptor.packId, descriptor.viewId) : null;
    const label = metadata ? `${metadata.pack.title} · ${metadata.view.label}` : "view";
    if (!suppressStatus) {
      updateStatus(`Closed view; displaying ${label}.`);
    }
    void renderCurrentLevel();
  } else {
    if (!suppressStatus) {
      updateStatus("Closed view; returning to zoom levels.");
    }
    void renderCurrentLevel();
  }
}

function renderSelector() {
  const list = document.getElementById("selector-list");
  console.log("[renderSelector] List element:", list);
  if (!list) {
    console.error("[renderSelector] selector-list element not found!");
    return;
  }

  list.innerHTML = "";
  console.log("[renderSelector] Rendering", state.entries.length, "entries");
  state.entries.forEach((entry) => {
    entry.options.forEach((option) => {
      console.log("[renderSelector] Adding option:", option.label);
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.slug = option.slug;
      button.dataset.relativePath = option.relative_path;
      button.textContent = option.label;
      button.addEventListener("click", () => {
        void selectOption(option);
      });
      if (state.activeOption?.relative_path === option.relative_path) {
        button.classList.add("selected");
      }
      item.appendChild(button);
      list.appendChild(item);
    });
  });
  console.log("[renderSelector] Rendered", list.children.length, "items");
}

async function selectOption(option) {
  console.log("[selectOption] Selecting option:", option);
  persistActiveSelectionMemory();
  clearActiveViewSelection({ silent: true, suppressStatus: true });
  state.activeOption = option;
  state.diagramDefinition = null;
  updateExportButtonState();
  renderSelector();
  updateStatus(`Loading ${option.label}…`);
  try {
    const record = await loadCommandViewPayloads(option);
    const loadedSegments = record.screening ? "inventory + screening" : "inventory";
    updateStatus(`Loaded ${option.label} (${loadedSegments}); preparing zoom controls…`);

    seedDefaultSelections();
    restoreSelectionMemory(option);
    synchronizeSelections();
    ensureCurrentLevelIsAvailable();
    updateLevelButtonsState();
    renderLevelSidebar();
    renderBreadcrumb();
    renderViewPacks();
    renderViewTabs();

    if (record.normalized) {
      console.debug("Normalized CommandView data", record.normalized);
    }

    await renderCurrentLevel();
  } catch (error) {
    console.error("Failed to load CommandView artifacts", error);
    clearDiagram();
    const detail = error instanceof Error ? error.message : String(error);
    updateStatus(`Failed to load ${option.label}; ${detail}`);
    renderViewPacks();
    renderViewTabs();
  }
}

function exportCurrentDiagram() {
  if (!state.diagramDefinition || state.diagramDefinition.trim().length === 0) {
    updateStatus("No diagram available to export yet.");
    updateExportButtonState();
    return;
  }

  const filename = buildDiagramExportFilename();
  const blob = new Blob([state.diagramDefinition], { type: "text/plain" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  updateStatus(`Exported Mermaid definition as ${filename}.`);
}

function wireRefresh() {
  const button = document.getElementById("refresh-button");
  if (!button) {
    return;
  }

  headerUi.refreshButton = button;

  button.addEventListener("click", async () => {
    button.disabled = true;
    updateStatus("Refreshing selector data...");
    try {
      await refreshSelectorData();
    } catch (error) {
      console.error("Refresh failed", error);
      updateStatus(`Refresh failed: ${error.message}`);
    } finally {
      button.disabled = false;
    }
  });
}

function buildSelectorUrl(endpoint) {
  if (!endpoint || typeof endpoint !== "string") {
    return null;
  }

  const trimmed = endpoint.trim();
  if (trimmed.length === 0) {
    return null;
  }

  if (/\.json$/i.test(trimmed)) {
    return trimmed;
  }

  const base = ensureTrailingSlash(trimmed);
  return `${base}selector.json`;
}

async function refreshSelectorData(options = {}) {
  const { allowFallback = true } = options;
  const config = getViewerConfig();
  const selectorEndpoint = config.selectorApiEndpoint || config.reportsBaseUrl || DEFAULT_REPORTS_BASE_URL;
  const selectorUrl = buildSelectorUrl(selectorEndpoint);

  console.log("[refreshSelectorData] Config:", config);
  console.log("[refreshSelectorData] Endpoint:", selectorEndpoint);
  console.log("[refreshSelectorData] Selector URL:", selectorUrl);

  if (!selectorUrl) {
    updateStatus("No selector endpoint configured; using demo data.");
    if (allowFallback) {
      await bootstrapDemoPayload();
    }
    return;
  }

  try {
    updateStatus(`Fetching selector data from ${selectorUrl}...`);
    console.log("[refreshSelectorData] Fetching from:", selectorUrl);
    const response = await fetch(selectorUrl, { cache: "no-cache" });

    console.log("[refreshSelectorData] Response status:", response.status, response.statusText);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const payload = await response.json();
    console.log("[refreshSelectorData] Payload received:", payload);

    if (!payload.entries || !Array.isArray(payload.entries)) {
      throw new Error("Invalid selector payload format");
    }

    console.log("[refreshSelectorData] Setting entries:", payload.entries.length, "groups");
    setEntries(payload.entries);
    updateStatus(`Refreshed selector data (${payload.entries.length} artifact groups loaded).`);
  } catch (error) {
    console.error("[refreshSelectorData] Error:", error);
    if (!allowFallback) {
      throw error;
    }
    updateStatus(`Could not fetch selector data (${error.message}); using demo data.`);
    await bootstrapDemoPayload();
  }
}

function wireExport() {
  const button = document.getElementById("export-button");
  if (!button) {
    return;
  }

  headerUi.exportButton = button;
  button.addEventListener("click", () => {
    exportCurrentDiagram();
  });
  updateExportButtonState();
}

function wireZoomControls() {
  const zoomInBtn = document.getElementById("zoom-in-btn");
  const zoomOutBtn = document.getElementById("zoom-out-btn");
  const zoomResetBtn = document.getElementById("zoom-reset-btn");

  if (zoomInBtn) {
    zoomInBtn.addEventListener("click", () => {
      zoomIn();
    });
  }

  if (zoomOutBtn) {
    zoomOutBtn.addEventListener("click", () => {
      zoomOut();
    });
  }

  if (zoomResetBtn) {
    zoomResetBtn.addEventListener("click", () => {
      resetDiagramZoom();
    });
  }

  console.log('[wireZoomControls] Zoom control buttons wired');
}

function initializeSidebarResize() {
  const resizeHandle = document.getElementById('sidebar-resize-handle');
  const sidebar = document.querySelector('.viewer-sidebar');
  
  if (!resizeHandle || !sidebar) {
    console.warn('[initializeSidebarResize] Resize handle or sidebar not found');
    return;
  }

  // Load saved width from localStorage
  const savedWidth = loadSidebarWidth();
  if (savedWidth) {
    applySidebarWidth(savedWidth);
  }

  resizeHandle.addEventListener('mousedown', handleSidebarMouseDown);
  
  console.log('[initializeSidebarResize] Sidebar resize initialized');
}

function handleSidebarMouseDown(event) {
  event.preventDefault();
  
  const sidebar = document.querySelector('.viewer-sidebar');
  if (!sidebar) return;

  state.sidebar.isResizing = true;
  state.sidebar.startX = event.clientX;
  state.sidebar.startWidth = sidebar.offsetWidth;

  const resizeHandle = document.getElementById('sidebar-resize-handle');
  if (resizeHandle) {
    resizeHandle.classList.add('resizing');
  }

  document.body.classList.add('sidebar-resizing');

  document.addEventListener('mousemove', handleSidebarMouseMove);
  document.addEventListener('mouseup', handleSidebarMouseUp);
}

function handleSidebarMouseMove(event) {
  if (!state.sidebar.isResizing) return;

  const delta = event.clientX - state.sidebar.startX;
  const newWidth = state.sidebar.startWidth + delta;
  
  // Constrain width between min and max
  const constrainedWidth = Math.max(200, Math.min(600, newWidth));
  
  applySidebarWidth(constrainedWidth);
}

function handleSidebarMouseUp() {
  if (!state.sidebar.isResizing) return;

  state.sidebar.isResizing = false;

  const resizeHandle = document.getElementById('sidebar-resize-handle');
  if (resizeHandle) {
    resizeHandle.classList.remove('resizing');
  }

  document.body.classList.remove('sidebar-resizing');

  document.removeEventListener('mousemove', handleSidebarMouseMove);
  document.removeEventListener('mouseup', handleSidebarMouseUp);

  // Save the new width
  saveSidebarWidth(state.sidebar.width);
}

function applySidebarWidth(width) {
  const sidebar = document.querySelector('.viewer-sidebar');
  if (!sidebar) return;

  sidebar.style.width = `${width}px`;
  state.sidebar.width = width;
}

function saveSidebarWidth(width) {
  try {
    localStorage.setItem('viewer-sidebar-width', width.toString());
  } catch (error) {
    console.warn('[saveSidebarWidth] Failed to save sidebar width', error);
  }
}

function loadSidebarWidth() {
  try {
    const saved = localStorage.getItem('viewer-sidebar-width');
    if (saved) {
      const width = parseInt(saved, 10);
      if (!isNaN(width) && width >= 200 && width <= 600) {
        return width;
      }
    }
  } catch (error) {
    console.warn('[loadSidebarWidth] Failed to load sidebar width', error);
  }
  return null;
}

async function bootstrapDemoPayload() {
  const demoPayload = {
    generated_at: new Date().toISOString(),
    entries: [
      {
        slug: "scripts_commandview",
        options: [
          {
            slug: "scripts_commandview",
            label: "scripts_commandview (sample)",
            relative_path:
              "index_scan/repo_studios__command_center__scripts_index/scripts_commandview_20251105-2049.json",
          },
        ],
      },
    ],
  };

  setEntries(demoPayload.entries);
  updateStatus("Demo payload loaded (replace with real selector data).");
}

function setEntries(entries) {
  console.log("[setEntries] Called with entries:", entries);
  persistActiveSelectionMemory();
  clearActiveViewSelection({ silent: true, suppressStatus: true });
  const previousOption = state.activeOption;
  state.entries = Array.isArray(entries) ? entries : [];
  console.log("[setEntries] State entries set to:", state.entries);
  renderSelector();
  const nextOption = findMatchingOption(state.entries, previousOption) ?? state.entries[0]?.options?.[0];
  console.log("[setEntries] Next option to select:", nextOption);
  if (nextOption) {
    void selectOption(nextOption);
  } else {
    state.activeOption = null;
    state.levels = null;
    state.normalizedData = null;
    state.levelSelections.rootId = null;
    state.levelSelections.domainId = null;
    state.levelSelections.moduleId = null;
    state.levelSelections.functionId = null;
    updateLevelButtonsState();
    renderLevelSidebar();
    renderBreadcrumb();
    updateStatus("No CommandView artifacts available.");
    clearDiagram();
    renderViewPacks();
    renderViewTabs();
  }
}

async function bootstrap() {
  console.log('[bootstrap] Starting viewer bootstrap...');
  try {
    console.log('[bootstrap] Step 1: initializeMermaid');
    initializeMermaid();
    console.log('[bootstrap] Step 2: initializeLevelControls');
    initializeLevelControls();
    console.log('[bootstrap] Step 3: initializeBreadcrumb');
    initializeBreadcrumb();
    console.log('[bootstrap] Step 4: renderViewTabs');
    renderViewTabs();
    console.log('[bootstrap] Step 5: renderViewPacks');
    renderViewPacks();
    console.log('[bootstrap] Step 6: wireRefresh');
    wireRefresh();
    console.log('[bootstrap] Step 7: wireExport');
    wireExport();
    console.log('[bootstrap] Step 8: wireZoomControls');
    wireZoomControls();
    console.log('[bootstrap] Step 9: initializeSidebarResize');
    initializeSidebarResize();
    console.log('[bootstrap] Step 10: updateStatus');
    updateStatus("Loading selector data...");
    console.log('[bootstrap] Step 11: refreshSelectorData');
    await refreshSelectorData();
    console.log('[bootstrap] Bootstrap completed successfully');
  } catch (error) {
    console.error("[bootstrap] Viewer bootstrap failed", error);
    updateStatus("Viewer bootstrap failed; check console logs.");
    // Also show error in loading overlay if still visible
    const loading = document.getElementById('loading-overlay');
    if (loading && loading.style.display !== 'none') {
      loading.innerHTML = `
        <div style="text-align: center; max-width: 600px; padding: 20px;">
          <div style="font-size: 24px; margin-bottom: 10px; color: #f48771;">⚠️</div>
          <div style="color: #f48771; font-weight: bold; margin-bottom: 10px;">Bootstrap Failed</div>
          <div style="font-size: 14px; margin-bottom: 10px;">${error.message}</div>
          <div style="font-size: 12px; color: #858585; margin-top: 20px;">
            Check browser console (F12) for details
          </div>
        </div>
      `;
    }
  }
}

console.log('[viewer.js] Setting up bootstrap trigger, readyState:', document.readyState);

if (document.readyState === "loading") {
  console.log('[viewer.js] Document still loading, adding DOMContentLoaded listener');
  document.addEventListener("DOMContentLoaded", () => {
    console.log('[viewer.js] DOMContentLoaded event fired, calling bootstrap');
    void bootstrap();
  });
} else {
  console.log('[viewer.js] Document already loaded, calling bootstrap immediately');
  void bootstrap();
}

console.log('[viewer.js] Script loading completed');
