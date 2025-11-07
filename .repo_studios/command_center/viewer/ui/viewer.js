const DEFAULT_REPORTS_BASE_URL = "../../reports/";
const ABSOLUTE_URL_PATTERN = /^[a-zA-Z][a-zA-Z0-9+\-.]*:\/\//;
const SUPPORTED_INVENTORY_SCHEMA_VERSIONS = new Set([2]);
const LEVEL_DEFINITIONS = [
  { value: "level0", label: "Level 0 - Overview" },
  { value: "level1", label: "Level 1 - Domain" },
  { value: "level2", label: "Level 2 - Module" },
  { value: "level3", label: "Level 3 - Functions" },
  { value: "level4", label: "Level 4 - Neighborhood" },
];

const LEVEL_NODE_THRESHOLD = 50;

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
  levelSelections: {
    rootId: null,
    domainId: null,
    moduleId: null,
    functionId: null,
  },
};

const levelUi = {
  buttons: new Map(),
  sidebar: null,
};

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
  const cacheKey = buildCacheKey(option);
  const cached = payloadCache.get(cacheKey);
  if (cached) {
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

  const [inventory, screening] = await Promise.all([
    fetchJson(inventoryUrl),
    fetchJson(screeningUrl).catch((error) => {
      console.warn("Screening payload load failed", error);
      return null;
    }),
  ]);

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
      },
      neighbors: neighbors
        .map((neighborId) => functions.get(neighborId))
        .filter(Boolean)
        .map((fn) => ({
          id: fn.id,
          moduleId: fn.moduleId,
          name: fn.name,
          metrics: fn.metrics,
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

  if (state.currentLevel !== levelKey) {
    state.currentLevel = levelKey;
  }

  updateLevelButtonsState();
  renderLevelSidebar();
  void renderCurrentLevel();
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
  state.levelSelections.moduleId = ensureSelectionInSet(state.levelSelections.moduleId, moduleIds);

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

function buildMermaidDefinition(levelKey) {
  if (!state.levels) {
    return null;
  }

  switch (levelKey) {
    case "level0":
      return buildAggregateMermaid(state.levels.level0, (node) => formatAggregateLabel(node));
    case "level1":
      return buildAggregateMermaid(state.levels.level1, (node) => formatAggregateLabel(node));
    case "level2":
      return buildAggregateMermaid(state.levels.level2, (node) => formatModuleLabel(node));
    case "level3": {
      const moduleId = state.levelSelections.moduleId;
      const moduleGraphs = state.levels.level3 instanceof Map ? state.levels.level3 : null;
      const moduleGraph = moduleId && moduleGraphs ? moduleGraphs.get(moduleId) : null;
      if (!moduleId || !moduleGraph) {
        return null;
      }
      return buildModuleFunctionsMermaid(moduleId, moduleGraph);
    }
    case "level4": {
      const functionId = state.levelSelections.functionId;
      const neighborhoods = state.levels.level4 instanceof Map ? state.levels.level4 : null;
      const detail = functionId && neighborhoods ? neighborhoods.get(functionId) : null;
      if (!detail) {
        return null;
      }
      return buildFunctionNeighborhoodMermaid(detail);
    }
    default:
      return null;
  }
}

function buildAggregateMermaid(levelData, labelFactory) {
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
  });

  const edges = Array.isArray(levelData.edges) ? levelData.edges : [];
  edges.forEach((edge) => {
    const source = idMap.get(edge.source);
    const target = idMap.get(edge.target);
    if (!source || !target) {
      return;
    }
    const weightLabel = typeof edge.weight === "number" && edge.weight > 1 ? `|${edge.weight}|` : "";
    lines.push(`  ${source} -->${weightLabel} ${target}`);
  });

  return lines.join("\n");
}

function buildModuleFunctionsMermaid(moduleId, moduleGraph) {
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
  });

  lines.push("  end");

  const edges = Array.isArray(moduleGraph.edges) ? moduleGraph.edges : [];
  edges.forEach((edge) => {
    const source = idMap.get(edge.source);
    const target = idMap.get(edge.target);
    if (!source || !target) {
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

function buildFunctionNeighborhoodMermaid(detail) {
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

  if (neighbors.length === 0) {
    const noteId = sanitizeMermaidId(`${focus.id}_note`);
    lines.push(`  ${noteId}["${escapeMermaidLabel("No neighbors recorded")}"]`);
    lines.push(`  ${focusId} --> ${noteId}`);
    return lines.join("\n");
  }

  neighbors.forEach((neighbor) => {
    const sanitizedId = sanitizeMermaidId(neighbor.id);
    idMap.set(neighbor.id, sanitizedId);
    lines.push(`  ${sanitizedId}["${escapeMermaidLabel(formatFunctionNodeLabel(neighbor, false))}"]`);
    lines.push(`  ${focusId} --> ${sanitizedId}`);
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

  const definition = buildMermaidDefinition(state.currentLevel);
  const levelDefinition = getLevelDefinition(state.currentLevel);
  const levelLabel = levelDefinition?.label ?? state.currentLevel;

  if (!definition) {
    clearDiagram();
    updateStatus(`${levelLabel} has no data for ${state.activeOption.label}.`);
    return;
  }

  updateStatus(`Rendering ${levelLabel} for ${state.activeOption.label}…`);
  const rendered = await renderDiagram(definition);
  if (rendered) {
    const nodeCount = getLevelNodeCount(state.currentLevel);
    const nodeDetail = nodeCount > 0 ? ` (${nodeCount} nodes)` : "";
    const suggestion = buildZoomSuggestion(state.currentLevel, nodeCount);
    const baseMessage = `Rendered ${levelLabel} for ${state.activeOption.label}${nodeDetail}.`;
    updateStatus(suggestion ? `${baseMessage} ${suggestion}` : baseMessage);
  }
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
    return true;
  } catch (error) {
    console.error("Mermaid render failed", error);
    updateStatus("Unable to render diagram preview (see console for details).");
    return false;
  }
}

function renderSelector() {
  const list = document.getElementById("selector-list");
  if (!list) {
    return;
  }

  list.innerHTML = "";
  state.entries.forEach((entry) => {
    entry.options.forEach((option) => {
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
}

async function selectOption(option) {
  state.activeOption = option;
  renderSelector();
  updateStatus(`Loading ${option.label}…`);
  try {
    const record = await loadCommandViewPayloads(option);
    const loadedSegments = record.screening ? "inventory + screening" : "inventory";
    updateStatus(`Loaded ${option.label} (${loadedSegments}); preparing zoom controls…`);

    seedDefaultSelections();
    synchronizeSelections();
    ensureCurrentLevelIsAvailable();
    updateLevelButtonsState();
    renderLevelSidebar();

    if (record.normalized) {
      console.debug("Normalized CommandView data", record.normalized);
    }

    await renderCurrentLevel();
  } catch (error) {
    console.error("Failed to load CommandView artifacts", error);
    clearDiagram();
    const detail = error instanceof Error ? error.message : String(error);
    updateStatus(`Failed to load ${option.label}; ${detail}`);
  }
}

function wireRefresh() {
  const button = document.getElementById("refresh-button");
  if (!button) {
    return;
  }

  button.addEventListener("click", async () => {
    button.disabled = true;
    updateStatus("Refresh triggered (UI wiring placeholder).");
    try {
      await bootstrapDemoPayload();
    } finally {
      button.disabled = false;
    }
  });
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
  state.entries = Array.isArray(entries) ? entries : [];
  renderSelector();
  const first = state.entries[0]?.options?.[0];
  if (first) {
    void selectOption(first);
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
    updateStatus("No CommandView artifacts available.");
    clearDiagram();
  }
}

function bootstrap() {
  try {
    initializeMermaid();
    initializeLevelControls();
    wireRefresh();
    bootstrapDemoPayload();
  } catch (error) {
    console.error("Viewer bootstrap failed", error);
    updateStatus("Viewer bootstrap failed; check console logs.");
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap);
} else {
  bootstrap();
}
