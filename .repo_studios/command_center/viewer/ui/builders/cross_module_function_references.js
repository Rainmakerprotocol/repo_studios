const DEFAULT_VIEW_LABEL = "Coupling Insight · Cross-Module Function References";
const MODULE_CLASS_DEFINITIONS = Object.freeze([
  "classDef moduleBase fill:#0f172a,stroke:#38bdf8,color:#f8fafc",
  "classDef moduleCaution fill:#78350f,stroke:#f59e0b,color:#fef3c7",
  "classDef moduleAlert fill:#7f1d1d,stroke:#f87171,color:#fee2e2",
  "classDef moduleFocus stroke:#22d3ee,stroke-width:3px,color:#e0f2fe",
]);

const COUPLING_THRESHOLDS = Object.freeze({
  caution: 5,
  alert: 10,
});

export function buildCrossModuleFunctionReferencesDiagram(modules, functions, callGraph, options = {}) {
  const moduleMap = toMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const functionMap = toMap(functions);
  if (!functionMap || functionMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "No function records available to analyze cross-module references.",
    };
  }

  const callGraphMap = toMapOfArrays(callGraph);
  if (!callGraphMap || callGraphMap.size === 0) {
    return {
      message: options.missingCallGraphMessage ?? "Call graph edges are not present in this CommandView artifact.",
    };
  }

  const focusSet = createFocusSet(options.focusModules);
  const couplingData = collectCouplingData(moduleMap, functionMap, callGraphMap);
  let edges = couplingData.edges;

  if (focusSet && focusSet.size > 0) {
    edges = edges.filter((entry) => focusSet.has(entry.sourceModule) || focusSet.has(entry.targetModule));
  }

  const modulesWithEdges = new Set();
  edges.forEach((entry) => {
    modulesWithEdges.add(entry.sourceModule);
    modulesWithEdges.add(entry.targetModule);
  });

  if (modulesWithEdges.size === 0) {
    return {
      message: options.emptyMessage ?? "No cross-module function references recorded for this selection.",
    };
  }

  const moduleEntries = Array.from(modulesWithEdges)
    .map((moduleId) => couplingData.modules.get(moduleId) ?? createEmptyModuleStats(moduleId))
    .filter(Boolean)
    .sort((left, right) => {
      const leftTotal = left.outboundCalls + left.inboundCalls;
      const rightTotal = right.outboundCalls + right.inboundCalls;
      if (rightTotal !== leftTotal) {
        return rightTotal - leftTotal;
      }
      if (right.outboundTargets.size !== left.outboundTargets.size) {
        return right.outboundTargets.size - left.outboundTargets.size;
      }
      if (right.inboundSources.size !== left.inboundSources.size) {
        return right.inboundSources.size - left.inboundSources.size;
      }
      return left.moduleId.localeCompare(right.moduleId);
    });

  const sortedEdges = edges
    .slice()
    .sort((left, right) => {
      if (right.callCount !== left.callCount) {
        return right.callCount - left.callCount;
      }
      if (left.sourceModule !== right.sourceModule) {
        return left.sourceModule.localeCompare(right.sourceModule);
      }
      return left.targetModule.localeCompare(right.targetModule);
    });

  const lines = ["graph LR"];
  MODULE_CLASS_DEFINITIONS.forEach((definition) => lines.push(`  ${definition}`));

  const nodeIdMap = new Map();
  moduleEntries.forEach((stats) => {
    const nodeId = sanitizeMermaidId(stats.moduleId);
    nodeIdMap.set(stats.moduleId, nodeId);
    const label = buildModuleLabel(stats);
    lines.push(`  ${nodeId}["${escapeMermaidLabel(label)}"]`);

    const classes = [classifyModuleCoupling(stats)];
    if (focusSet && focusSet.has(stats.moduleId)) {
      classes.push("moduleFocus");
    }
    lines.push(`  class ${nodeId} ${classes.join(",")};`);
  });

  const edgeLines = [];
  sortedEdges.forEach((entry) => {
    const sourceId = nodeIdMap.get(entry.sourceModule);
    const targetId = nodeIdMap.get(entry.targetModule);
    if (!sourceId || !targetId) {
      return;
    }
    const label = buildEdgeLabel(entry);
    edgeLines.push(`  ${sourceId} -->|${escapeMermaidLabel(label)}| ${targetId}`);
  });

  edgeLines.forEach((line) => lines.push(line));

  const stats = buildStatsSnapshot(moduleEntries, sortedEdges);
  const scopeDescription = normalizeString(options.scopeDescription) ?? "repository";
  let statusMessage = buildStatusMessage(stats, scopeDescription);
  let statusDetails = buildStatusDetails(stats);

  const fallbackNotice = normalizeString(options.fallbackNotice);
  if (fallbackNotice) {
    statusMessage = `${statusMessage} ${fallbackNotice}`.trim();
    statusDetails = [
      {
        type: "info",
        title: "Scope fallback applied",
        description: fallbackNotice,
      },
      ...statusDetails,
    ];
  }

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    statusDetails,
    stats,
  };
}

function collectCouplingData(moduleMap, functionMap, callGraphMap) {
  const moduleStats = new Map();
  const edges = new Map();

  const ensureModuleStats = (moduleId) => {
    let stats = moduleStats.get(moduleId);
    if (!stats) {
      stats = createEmptyModuleStats(moduleId);
      moduleStats.set(moduleId, stats);
    }
    return stats;
  };

  callGraphMap.forEach((targets, sourceFunctionId) => {
    const sourceRecord = functionMap.get(sourceFunctionId);
    if (!sourceRecord || !sourceRecord.moduleId || !moduleMap.has(sourceRecord.moduleId)) {
      return;
    }

    const sourceModule = sourceRecord.moduleId;
    const uniqueTargets = Array.isArray(targets) ? Array.from(new Set(targets)) : [];

    uniqueTargets.forEach((targetFunctionId) => {
      const targetRecord = functionMap.get(targetFunctionId);
      if (!targetRecord || !targetRecord.moduleId || !moduleMap.has(targetRecord.moduleId)) {
        return;
      }
      const targetModule = targetRecord.moduleId;
      if (targetModule === sourceModule) {
        return;
      }

      const edgeKey = `${sourceModule}->${targetModule}`;
      let entry = edges.get(edgeKey);
      if (!entry) {
        entry = {
          key: edgeKey,
          sourceModule,
          targetModule,
          callPairs: new Set(),
          callCount: 0,
          sourceFunctions: new Set(),
          targetFunctions: new Set(),
        };
        edges.set(edgeKey, entry);
      }

      const pairKey = `${sourceFunctionId}->${targetFunctionId}`;
      if (entry.callPairs.has(pairKey)) {
        return;
      }

      entry.callPairs.add(pairKey);
      entry.callCount += 1;
      entry.sourceFunctions.add(sourceFunctionId);
      entry.targetFunctions.add(targetFunctionId);

      const sourceStats = ensureModuleStats(sourceModule);
      const targetStats = ensureModuleStats(targetModule);
      sourceStats.outboundCalls += 1;
      sourceStats.outboundTargets.add(targetModule);
      sourceStats.outboundFunctions.add(sourceFunctionId);
      targetStats.inboundCalls += 1;
      targetStats.inboundSources.add(sourceModule);
      targetStats.inboundFunctions.add(targetFunctionId);
    });
  });

  return {
    modules: moduleStats,
    edges: Array.from(edges.values()),
  };
}

function buildStatsSnapshot(moduleEntries, edges) {
  const moduleCount = moduleEntries.length;
  const edgeCount = edges.length;
  const totalCalls = edges.reduce((acc, entry) => acc + entry.callCount, 0);

  const topCouplings = edges
    .slice()
    .sort((left, right) => {
      if (right.callCount !== left.callCount) {
        return right.callCount - left.callCount;
      }
      if (left.sourceModule !== right.sourceModule) {
        return left.sourceModule.localeCompare(right.sourceModule);
      }
      return left.targetModule.localeCompare(right.targetModule);
    })
    .slice(0, 10)
    .map((entry) => ({
      sourceModule: entry.sourceModule,
      targetModule: entry.targetModule,
      calls: entry.callCount,
      sourceFunctions: entry.sourceFunctions.size,
      targetFunctions: entry.targetFunctions.size,
    }));

  const topOutboundModules = moduleEntries
    .slice()
    .sort((left, right) => {
      if (right.outboundCalls !== left.outboundCalls) {
        return right.outboundCalls - left.outboundCalls;
      }
      if (right.outboundTargets.size !== left.outboundTargets.size) {
        return right.outboundTargets.size - left.outboundTargets.size;
      }
      return left.moduleId.localeCompare(right.moduleId);
    })
    .slice(0, 10)
    .map((stats) => ({
      moduleId: stats.moduleId,
      outboundCalls: stats.outboundCalls,
      outboundTargets: stats.outboundTargets.size,
    }));

  const topInboundModules = moduleEntries
    .slice()
    .sort((left, right) => {
      if (right.inboundCalls !== left.inboundCalls) {
        return right.inboundCalls - left.inboundCalls;
      }
      if (right.inboundSources.size !== left.inboundSources.size) {
        return right.inboundSources.size - left.inboundSources.size;
      }
      return left.moduleId.localeCompare(right.moduleId);
    })
    .slice(0, 10)
    .map((stats) => ({
      moduleId: stats.moduleId,
      inboundCalls: stats.inboundCalls,
      inboundSources: stats.inboundSources.size,
    }));

  return {
    modules: moduleCount,
    modulesWithCoupling: moduleCount,
    crossModuleEdges: edgeCount,
    crossModuleCalls: totalCalls,
    topCouplings,
    topOutboundModules,
    topInboundModules,
  };
}

function buildStatusMessage(stats, scopeDescription) {
  const callLabel = formatPlural(stats.crossModuleCalls, "cross-module call");
  return `Rendered Cross-Module Function References for ${scopeDescription} (${stats.modulesWithCoupling} modules, ${stats.crossModuleEdges} edges, ${callLabel}).`;
}

function buildStatusDetails(stats) {
  const details = [
    {
      type: "stat-summary",
      title: "Coupling Snapshot",
      items: [
        { label: "Modules", value: String(stats.modulesWithCoupling ?? 0) },
        { label: "Cross-Module Edges", value: String(stats.crossModuleEdges ?? 0) },
        { label: "Cross-Module Calls", value: String(stats.crossModuleCalls ?? 0) },
      ],
    },
  ];

  if (Array.isArray(stats.topCouplings) && stats.topCouplings.length > 0) {
    details.push({
      type: "list",
      title: "Top Cross-Module Couplings",
      description: "Edges ordered by cross-module call counts.",
      items: stats.topCouplings.slice(0, 5).map((entry) => ({
        header: `${entry.sourceModule} → ${entry.targetModule}`,
        body: `${entry.calls} ${formatPlural(entry.calls, "call")} across ${formatPlural(entry.sourceFunctions, "source function")} into ${formatPlural(entry.targetFunctions, "target function")}.`,
        badges: [],
      })),
    });
  }

  if (Array.isArray(stats.topOutboundModules) && stats.topOutboundModules.length > 0) {
    details.push({
      type: "list",
      title: "Top Outbound Modules",
      description: "Modules invoking the most cross-module functions.",
      items: stats.topOutboundModules.slice(0, 5).map((entry) => ({
        header: entry.moduleId,
        body: `${entry.outboundCalls} ${formatPlural(entry.outboundCalls, "call")} touching ${formatPlural(entry.outboundTargets, "target module")}.`,
        badges: [],
      })),
    });
  }

  if (Array.isArray(stats.topInboundModules) && stats.topInboundModules.length > 0) {
    details.push({
      type: "list",
      title: "Top Inbound Modules",
      description: "Modules receiving the most cross-module calls.",
      items: stats.topInboundModules.slice(0, 5).map((entry) => ({
        header: entry.moduleId,
        body: `${entry.inboundCalls} ${formatPlural(entry.inboundCalls, "call")} sourced from ${formatPlural(entry.inboundSources, "inbound module")}.`,
        badges: [],
      })),
    });
  }

  return details;
}

function buildModuleLabel(stats) {
  const outboundDetails = `${stats.outboundCalls} ${formatPlural(stats.outboundCalls, "outbound call")} → ${stats.outboundTargets.size} ${formatPlural(stats.outboundTargets.size, "module")}`;
  const inboundDetails = `${stats.inboundCalls} ${formatPlural(stats.inboundCalls, "inbound call")} ← ${stats.inboundSources.size} ${formatPlural(stats.inboundSources.size, "module")}`;
  return `${stats.moduleId}\n${outboundDetails}\n${inboundDetails}`;
}

function buildEdgeLabel(entry) {
  const callLabel = `${entry.callCount} ${formatPlural(entry.callCount, "call")}`;
  const functionLabel = `${entry.sourceFunctions.size} src → ${entry.targetFunctions.size} dest`;
  return `${callLabel}\n${functionLabel}`;
}

function classifyModuleCoupling(stats) {
  const totalCalls = stats.outboundCalls + stats.inboundCalls;
  if (totalCalls >= COUPLING_THRESHOLDS.alert) {
    return "moduleAlert";
  }
  if (totalCalls >= COUPLING_THRESHOLDS.caution) {
    return "moduleCaution";
  }
  return "moduleBase";
}

function createEmptyModuleStats(moduleId) {
  return {
    moduleId,
    outboundCalls: 0,
    inboundCalls: 0,
    outboundTargets: new Set(),
    inboundSources: new Set(),
    outboundFunctions: new Set(),
    inboundFunctions: new Set(),
  };
}

function createFocusSet(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Set) {
    return value.size > 0 ? value : null;
  }
  if (Array.isArray(value)) {
    const entries = value.map((item) => (typeof item === "string" ? item : null)).filter(Boolean);
    return entries.length > 0 ? new Set(entries) : null;
  }
  return null;
}

function toMap(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Map) {
    return value;
  }
  if (Array.isArray(value)) {
    const map = new Map();
    value.forEach((entry, index) => {
      if (!entry || typeof entry !== "object") {
        return;
      }
      const key = entry.id ?? entry.moduleId ?? entry.module_id ?? String(index);
      map.set(key, entry);
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

function toMapOfArrays(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Map) {
    return value;
  }
  if (Array.isArray(value)) {
    const map = new Map();
    value.forEach((entry) => {
      if (!Array.isArray(entry) || entry.length < 2) {
        return;
      }
      const [source, target] = entry;
      if (!source || !target) {
        return;
      }
      const list = map.get(source) ?? [];
      list.push(target);
      map.set(source, list);
    });
    return map;
  }
  if (typeof value === "object") {
    const map = new Map();
    Object.entries(value).forEach(([key, entry]) => {
      if (Array.isArray(entry)) {
        map.set(key, entry);
      }
    });
    return map;
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

function formatPlural(count, noun) {
  const suffix = count === 1 ? "" : "s";
  return `${count} ${noun}${suffix}`;
}

export const __test__ = {
  collectCouplingData,
  classifyModuleCoupling,
  createEmptyModuleStats,
  buildEdgeLabel,
  formatPlural,
  toMap,
  toMapOfArrays,
};
