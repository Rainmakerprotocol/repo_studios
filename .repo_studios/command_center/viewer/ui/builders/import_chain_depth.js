const DEFAULT_VIEW_LABEL = "Coupling Insight · Import Chain Depth";
const DEPTH_CLASS_DEFINITIONS = Object.freeze([
  "classDef depthBase fill:#0f172a,stroke:#38bdf8,color:#f8fafc,stroke-width:1.5px",
  "classDef depthCaution fill:#78350f,stroke:#f59e0b,color:#fef3c7,stroke-width:2px",
  "classDef depthAlert fill:#7f1d1d,stroke:#f87171,color:#fee2e2,stroke-width:2.5px",
  "classDef depthFocus stroke:#22d3ee,stroke-width:3px,color:#e0f2fe",
  "classDef stdlibNode fill:#1f2937,stroke:#10b981,color:#ecfdf5,stroke-dasharray:5 3,stroke-width:1.5px",
]);

const DEPTH_THRESHOLDS = Object.freeze({
  caution: 3,
  alert: 5,
});

const MAX_DEEPEST_SAMPLE = 5;
const MAX_UNREACHABLE_SAMPLE = 12;

export function buildImportChainDepthDiagram(modules, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const focusSet = createFocusSet(options.focusModules);

  const {
    standardLibraryImports,
    internalDependencies,
    importersByModule,
    unresolvedTargets,
  } = collectImportGraph(moduleMap);

  if (standardLibraryImports.size === 0) {
    return {
      message: options.missingStandardLibraryMessage ?? "Standard library imports are not recorded for this selection.",
    };
  }

  const depthResult = computeDepthAssignments({
    moduleMap,
    standardLibraryImports,
    importersByModule,
  });

  if (depthResult.depthByModule.size === 0) {
    return {
      message: options.emptyMessage ?? "No import chains connect standard library modules to local modules for this selection.",
    };
  }

  const allowedModules = resolveAllowedModules({
    focusSet,
    depthByModule: depthResult.depthByModule,
    internalDependencies,
  });

  const moduleEntries = buildModuleEntries({
    moduleMap,
    depthByModule: depthResult.depthByModule,
    standardLibraryImports,
    internalDependencies,
    predecessor: depthResult.predecessor,
    allowedModules,
  });

  if (moduleEntries.length === 0) {
    return {
      message: options.emptyMessage ?? "No import chain depth data matched this selection.",
    };
  }

  const { lines, nodeLookup, standardLibraryNodes } = buildMermaidDefinition({
    moduleEntries,
    focusSet,
  });

  buildStandardLibraryNodes({
    lines,
    standardLibraryNodes,
    moduleEntries,
  });

  buildMermaidEdges({
    lines,
    nodeLookup,
    moduleEntries,
    standardLibraryNodes,
    internalDependencies,
    depthByModule: depthResult.depthByModule,
  });

  const stats = buildStatsSnapshot({
    moduleEntries,
    standardLibraryImports,
    depthByModule: depthResult.depthByModule,
    unresolvedTargets,
    unreachableModules: depthResult.unreachableModules,
  });

  const scopeDescription = normalizeString(options.scopeDescription) ?? "repository";
  let statusMessage = buildStatusMessage({
    scopeDescription,
    stats,
  });

  const fallbackNotice = normalizeString(options.fallbackNotice);
  if (fallbackNotice) {
    statusMessage = `${statusMessage} ${fallbackNotice}`.trim();
  }

  const statusDetails = buildStatusDetails({
    stats,
    fallbackNotice,
  });

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    statusDetails,
    stats,
  };
}

function collectImportGraph(moduleMap) {
  const standardLibraryImports = new Map();
  const internalDependencies = new Map();
  const importersByModule = new Map();
  const unresolvedTargets = new Set();

  moduleMap.forEach((record, moduleId) => {
    if (!record || typeof record !== "object") {
      return;
    }

    const importEdges = Array.isArray(record.importEdges) ? record.importEdges : [];
    const stdSet = new Set();
    const internalSet = new Set();

    importEdges.forEach((edge) => {
      if (!edge || typeof edge !== "object") {
        return;
      }
      const category = normalizeKey(edge.category ?? edge.classification);
      const targetId = normalizeString(edge.target ?? edge.module ?? edge.name ?? null);

      if (category === "standard_library" && targetId) {
        stdSet.add(targetId);
        return;
      }

      if (category !== "internal") {
        return;
      }

      const resolvedTarget = resolveInternalTarget(targetId, moduleMap);
      if (resolvedTarget) {
        internalSet.add(resolvedTarget);
        if (!importersByModule.has(resolvedTarget)) {
          importersByModule.set(resolvedTarget, new Set());
        }
        importersByModule.get(resolvedTarget).add(moduleId);
      } else if (targetId) {
        unresolvedTargets.add(targetId);
      }
    });

    if (stdSet.size > 0) {
      standardLibraryImports.set(moduleId, stdSet);
    }
    if (internalSet.size > 0) {
      internalDependencies.set(moduleId, internalSet);
    }
  });

  moduleMap.forEach((_record, moduleId) => {
    if (!importersByModule.has(moduleId)) {
      importersByModule.set(moduleId, new Set());
    }
    if (!internalDependencies.has(moduleId)) {
      internalDependencies.set(moduleId, new Set());
    }
  });

  return {
    standardLibraryImports,
    internalDependencies,
    importersByModule,
    unresolvedTargets,
  };
}

function computeDepthAssignments(payload) {
  const depthByModule = new Map();
  const predecessor = new Map();
  const queue = [];

  const starters = Array.from(payload.standardLibraryImports.keys()).sort((a, b) => a.localeCompare(b));
  starters.forEach((moduleId) => {
    depthByModule.set(moduleId, 1);
    predecessor.set(moduleId, null);
    queue.push(moduleId);
  });

  while (queue.length > 0) {
    const current = queue.shift();
    const currentDepth = depthByModule.get(current);
    if (!Number.isFinite(currentDepth)) {
      continue;
    }

    const importers = payload.importersByModule.get(current);
    if (!importers || importers.size === 0) {
      continue;
    }

    const orderedImporters = Array.from(importers).sort((a, b) => a.localeCompare(b));
    orderedImporters.forEach((importerId) => {
      if (!payload.moduleMap.has(importerId)) {
        return;
      }
      const candidateDepth = currentDepth + 1;
      const existingDepth = depthByModule.get(importerId);
      if (existingDepth === undefined || candidateDepth < existingDepth) {
        depthByModule.set(importerId, candidateDepth);
        predecessor.set(importerId, current);
        queue.push(importerId);
      } else if (candidateDepth === existingDepth) {
        const currentPredecessor = predecessor.get(importerId);
        if (!currentPredecessor || current.localeCompare(currentPredecessor) < 0) {
          predecessor.set(importerId, current);
        }
      }
    });
  }

  const unreachableModules = [];
  payload.moduleMap.forEach((_record, moduleId) => {
    if (!depthByModule.has(moduleId)) {
      unreachableModules.push(moduleId);
    }
  });
  unreachableModules.sort((a, b) => a.localeCompare(b));

  return { depthByModule, predecessor, unreachableModules };
}

function resolveAllowedModules(payload) {
  if (!payload.focusSet || payload.focusSet.size === 0) {
    return null;
  }

  const allowed = new Set();
  const queue = [];

  payload.focusSet.forEach((moduleId) => {
    if (payload.depthByModule.has(moduleId)) {
      allowed.add(moduleId);
      queue.push(moduleId);
    }
  });

  while (queue.length > 0) {
    const moduleId = queue.shift();
    const dependencies = payload.internalDependencies.get(moduleId) ?? new Set();
    dependencies.forEach((depId) => {
      if (!payload.depthByModule.has(depId)) {
        return;
      }
      if (allowed.has(depId)) {
        return;
      }
      if (!isDepthPredecessor(payload.depthByModule, moduleId, depId)) {
        return;
      }
      allowed.add(depId);
      queue.push(depId);
    });
  }

  return allowed;
}

function isDepthPredecessor(depthByModule, moduleId, dependencyId) {
  const moduleDepth = depthByModule.get(moduleId);
  const dependencyDepth = depthByModule.get(dependencyId);
  if (!Number.isFinite(moduleDepth) || !Number.isFinite(dependencyDepth)) {
    return false;
  }
  return dependencyDepth < moduleDepth;
}

function buildModuleEntries(payload) {
  const entries = [];
  const standardLibraryCache = new Map();

  payload.depthByModule.forEach((depth, moduleId) => {
    if (!Number.isFinite(depth)) {
      return;
    }
    if (payload.allowedModules && !payload.allowedModules.has(moduleId)) {
      return;
    }

    const record = payload.moduleMap.get(moduleId) ?? {};
    const directStandardLibraries = payload.standardLibraryImports.get(moduleId) ?? new Set();
    const standardLibraries = resolveStandardLibraries({
      moduleId,
      depth,
      internalDependencies: payload.internalDependencies,
      depthByModule: payload.depthByModule,
      standardLibraryImports: payload.standardLibraryImports,
      cache: standardLibraryCache,
    });

    const chain = buildChainTrace({
      moduleId,
      predecessor: payload.predecessor,
      standardLibraryImports: payload.standardLibraryImports,
    });

    entries.push({
      moduleId,
      record,
      depth,
      directStandardLibraries,
      standardLibraries,
      chain,
    });
  });

  entries.sort((left, right) => {
    if (left.depth !== right.depth) {
      return left.depth - right.depth;
    }
    return left.moduleId.localeCompare(right.moduleId);
  });

  return entries;
}

function resolveStandardLibraries(payload) {
  if (payload.cache.has(payload.moduleId)) {
    return payload.cache.get(payload.moduleId);
  }

  const libs = new Set(payload.standardLibraryImports.get(payload.moduleId) ?? []);
  const dependencies = payload.internalDependencies.get(payload.moduleId) ?? new Set();
  const moduleDepth = payload.depth;

  dependencies.forEach((dependencyId) => {
    const dependencyDepth = payload.depthByModule.get(dependencyId);
    if (!Number.isFinite(dependencyDepth)) {
      return;
    }
    if (dependencyDepth >= moduleDepth) {
      return;
    }
    const upstream = resolveStandardLibraries({
      moduleId: dependencyId,
      depth: dependencyDepth,
      internalDependencies: payload.internalDependencies,
      depthByModule: payload.depthByModule,
      standardLibraryImports: payload.standardLibraryImports,
      cache: payload.cache,
    });
    upstream.forEach((value) => libs.add(value));
  });

  payload.cache.set(payload.moduleId, libs);
  return libs;
}

function buildChainTrace(payload) {
  const chain = [];
  let current = payload.moduleId;
  const visited = new Set();

  while (current && !visited.has(current)) {
    chain.unshift(current);
    visited.add(current);
    const parent = payload.predecessor.get(current) ?? null;
    if (!parent) {
      break;
    }
    current = parent;
  }

  if (chain.length === 0) {
    return [];
  }

  const firstModule = chain[0];
  const stdSet = payload.standardLibraryImports.get(firstModule) ?? new Set();
  const stdSources = Array.from(stdSet).sort((a, b) => a.localeCompare(b));
  if (stdSources.length === 0) {
    return chain;
  }
  return [...stdSources.slice(0, 1), ...chain];
}

function buildMermaidDefinition(payload) {
  const lines = ["graph TD"];
  DEPTH_CLASS_DEFINITIONS.forEach((definition) => lines.push(`  ${definition}`));

  const nodeLookup = new Map();
  const standardLibraryNodes = new Map();

  payload.moduleEntries.forEach((entry) => {
    const nodeId = sanitizeMermaidId(entry.moduleId);
    nodeLookup.set(entry.moduleId, nodeId);

    const label = buildModuleLabel(entry);
    lines.push(`  ${nodeId}["${escapeMermaidLabel(label)}"]`);

    const classes = [resolveDepthClass(entry.depth)];
    if (payload.focusSet && payload.focusSet.has(entry.moduleId)) {
      classes.push("depthFocus");
    }
    lines.push(`  class ${nodeId} ${classes.join(",")};`);

    entry.directStandardLibraries.forEach((lib) => {
      if (!standardLibraryNodes.has(lib)) {
        standardLibraryNodes.set(lib, sanitizeMermaidId(`stdlib_${lib}`));
      }
    });
  });

  return { lines, nodeLookup, standardLibraryNodes };
}

function buildStandardLibraryNodes(payload) {
  payload.standardLibraryNodes.forEach((nodeId, libraryName) => {
    const label = `std · ${libraryName}`;
    payload.lines.push(`  ${nodeId}["${escapeMermaidLabel(label)}"]`);
    payload.lines.push(`  class ${nodeId} stdlibNode;`);
  });
}

function buildMermaidEdges(payload) {
  const stdEdges = [];
  payload.moduleEntries.forEach((entry) => {
    const targetId = payload.nodeLookup.get(entry.moduleId);
    if (!targetId) {
      return;
    }

    const libs = Array.from(entry.directStandardLibraries).sort((a, b) => a.localeCompare(b));
    libs.forEach((lib) => {
      const stdId = payload.standardLibraryNodes.get(lib);
      if (!stdId) {
        return;
      }
      stdEdges.push({ source: stdId, target: targetId });
    });
  });

  stdEdges
    .sort((left, right) => {
      if (left.source === right.source) {
        return left.target.localeCompare(right.target);
      }
      return left.source.localeCompare(right.source);
    })
    .forEach((edge) => {
      payload.lines.push(`  ${edge.source} --> ${edge.target}`);
    });

  const internalEdges = [];
  payload.moduleEntries.forEach((entry) => {
    const importerId = payload.nodeLookup.get(entry.moduleId);
    if (!importerId) {
      return;
    }
    const dependencies = payload.internalDependencies.get(entry.moduleId) ?? new Set();
    dependencies.forEach((dependencyId) => {
      const dependencyNode = payload.nodeLookup.get(dependencyId);
      if (!dependencyNode) {
        return;
      }
      const importerDepth = payload.depthByModule.get(entry.moduleId);
      const dependencyDepth = payload.depthByModule.get(dependencyId);
      if (!Number.isFinite(importerDepth) || !Number.isFinite(dependencyDepth)) {
        return;
      }
      if (dependencyDepth + 1 !== importerDepth) {
        return;
      }
      internalEdges.push({ source: dependencyNode, target: importerId });
    });
  });

  internalEdges
    .sort((left, right) => {
      if (left.source === right.source) {
        return left.target.localeCompare(right.target);
      }
      return left.source.localeCompare(right.source);
    })
    .forEach((edge) => {
      payload.lines.push(`  ${edge.source} --> ${edge.target}`);
    });
}

function buildModuleLabel(entry) {
  const parts = [entry.moduleId];
  parts.push(`Depth ${entry.depth}`);

  const totalStd = entry.standardLibraries.size;
  const directStd = entry.directStandardLibraries.size;
  parts.push(`Standard libs ${totalStd}`);
  if (directStd > 0) {
    parts.push(`Direct stdlib ${directStd}`);
  }

  if (Array.isArray(entry.chain) && entry.chain.length > 1) {
    const preview = entry.chain.slice(0, 4).join(" -> ");
    parts.push(preview + (entry.chain.length > 4 ? " -> ..." : ""));
  }

  return parts.join("\n");
}

function resolveDepthClass(depth) {
  if (!Number.isFinite(depth)) {
    return "depthBase";
  }
  if (depth >= DEPTH_THRESHOLDS.alert) {
    return "depthAlert";
  }
  if (depth >= DEPTH_THRESHOLDS.caution) {
    return "depthCaution";
  }
  return "depthBase";
}

function buildStatsSnapshot(payload) {
  const depthBuckets = new Map();
  let maxDepth = 0;

  payload.moduleEntries.forEach((entry) => {
    maxDepth = Math.max(maxDepth, entry.depth);
    const bucket = depthBuckets.get(entry.depth) ?? 0;
    depthBuckets.set(entry.depth, bucket + 1);
  });

  const sortedBuckets = Array.from(depthBuckets.entries())
    .sort((left, right) => left[0] - right[0])
    .map(([depth, count]) => ({ depth, count }));

  const deepestModules = payload.moduleEntries
    .slice()
    .sort((left, right) => {
      if (right.depth !== left.depth) {
        return right.depth - left.depth;
      }
      return left.moduleId.localeCompare(right.moduleId);
    })
    .slice(0, MAX_DEEPEST_SAMPLE)
    .map((entry) => ({
      moduleId: entry.moduleId,
      depth: entry.depth,
      chain: Array.isArray(entry.chain) ? entry.chain.join(" -> ") : null,
    }));

  const uniqueStandardLibraries = new Set();
  payload.moduleEntries.forEach((entry) => {
    entry.standardLibraries.forEach((lib) => uniqueStandardLibraries.add(lib));
  });

  const unreachableModules = Array.isArray(payload.unreachableModules)
    ? payload.unreachableModules.slice(0, MAX_UNREACHABLE_SAMPLE)
    : [];

  return {
    modulesInChain: payload.moduleEntries.length,
    maxDepth,
    depthBuckets: sortedBuckets,
    uniqueStandardLibraryCount: uniqueStandardLibraries.size,
    unreachableCount: Array.isArray(payload.unreachableModules) ? payload.unreachableModules.length : 0,
    unreachableSample: unreachableModules,
    unresolvedTargetCount: payload.unresolvedTargets.size,
    deepestModules,
  };
}

function buildStatusMessage(payload) {
  const distribution = payload.stats.depthBuckets.map((entry) => `${entry.depth}:${entry.count}`).join(", ");
  const unreachableSuffix = payload.stats.unreachableCount > 0
    ? `, ${payload.stats.unreachableCount} unreachable`
    : "";
  return `Rendered Import Chain Depth for ${payload.scopeDescription} (${payload.stats.modulesInChain} modules, depth range 1-${payload.stats.maxDepth}${unreachableSuffix}; buckets ${distribution || "none"}).`;
}

function buildStatusDetails(payload) {
  const items = [
    {
      type: "stat-summary",
      title: "Import Depth Snapshot",
      items: [
        { label: "Modules", value: String(payload.stats.modulesInChain ?? 0) },
        { label: "Max Depth", value: String(payload.stats.maxDepth ?? 0) },
        { label: "Stdlib Modules", value: String(payload.stats.uniqueStandardLibraryCount ?? 0) },
        { label: "Unreachable", value: String(payload.stats.unreachableCount ?? 0) },
      ],
    },
  ];

  if (payload.fallbackNotice) {
    items.push({
      type: "info",
      title: "Scope fallback applied",
      description: payload.fallbackNotice,
    });
  }

  if (Array.isArray(payload.stats.depthBuckets) && payload.stats.depthBuckets.length > 0) {
    items.push({
      type: "list",
      title: "Depth Distribution",
      description: "Modules grouped by minimal hop count from a standard library import.",
      items: payload.stats.depthBuckets.map((entry) => ({
        header: `Depth ${entry.depth}`,
        body: `${entry.count} module${entry.count === 1 ? "" : "s"}`,
        badges: [],
      })),
    });
  }

  if (Array.isArray(payload.stats.deepestModules) && payload.stats.deepestModules.length > 0) {
    items.push({
      type: "list",
      title: "Deepest Modules",
      description: "Longest chains from the standard library into repository modules.",
      items: payload.stats.deepestModules.map((entry) => ({
        header: `${entry.moduleId} (depth ${entry.depth})`,
        body: entry.chain ? entry.chain : "",
        badges: [],
      })),
    });
  }

  if (Array.isArray(payload.stats.unreachableSample) && payload.stats.unreachableSample.length > 0) {
    items.push({
      type: "pill-list",
      title: "No Stdlib Path",
      description: "Modules without a recorded chain back to the standard library.",
      items: payload.stats.unreachableSample,
    });
  }

  if (Number.isFinite(payload.stats.unresolvedTargetCount) && payload.stats.unresolvedTargetCount > 0) {
    items.push({
      type: "note",
      title: "Unresolved Imports",
      description: `${payload.stats.unresolvedTargetCount} internal import target${payload.stats.unresolvedTargetCount === 1 ? " was" : "s were"} not resolved to normalized modules.`,
    });
  }

  return items;
}

function createFocusSet(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Set) {
    return value.size > 0 ? value : null;
  }
  if (Array.isArray(value)) {
    const entries = value
      .map((item) => (typeof item === "string" ? item : null))
      .filter(Boolean);
    return entries.length > 0 ? new Set(entries) : null;
  }
  if (typeof value === "string" && value.trim().length > 0) {
    return new Set([value.trim()]);
  }
  return null;
}

function toModuleMap(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Map) {
    return value;
  }
  if (Array.isArray(value)) {
    const map = new Map();
    value.forEach((entry) => {
      if (!entry || typeof entry !== "object") {
        return;
      }
      const key = entry.id ?? entry.moduleId ?? entry.module_id ?? null;
      if (key) {
        map.set(key, entry);
      }
    });
    return map;
  }
  if (typeof value === "object") {
    const map = new Map();
    Object.entries(value).forEach(([key, entry]) => {
      map.set(key, entry);
    });
    return map;
  }
  return null;
}

function resolveInternalTarget(target, moduleMap) {
  if (!target || typeof target !== "string") {
    return null;
  }
  let candidate = target.replace(/\//g, ".").replace(/^\.+/, "");
  if (moduleMap.has(candidate)) {
    return candidate;
  }
  const segments = candidate.split(".");
  while (segments.length > 1) {
    segments.pop();
    const probe = segments.join(".");
    if (moduleMap.has(probe)) {
      return probe;
    }
  }
  return null;
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

function escapeMermaidLabel(value) {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value)
    .replace(/\\/g, "\\\\")
    .replace(/"/g, "'")
    .replace(/\n/g, "<br/>");
}

function normalizeString(value) {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function normalizeKey(value) {
  if (typeof value !== "string") {
    return null;
  }
  return value.trim().toLowerCase();
}

export const __test__ = {
  toModuleMap,
  collectImportGraph,
  computeDepthAssignments,
  resolveStandardLibraries,
  buildModuleLabel,
};
