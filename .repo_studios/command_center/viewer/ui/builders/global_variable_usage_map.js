const DEFAULT_VIEW_LABEL = "State Effects · Global Variable Usage Map";

let mermaidIdCounter = 0;

export function buildGlobalVariableUsageMapDiagram(modules, functions, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message:
        options.missingModulesMessage ?? "Module metadata has not been normalized for this CommandView artifact.",
    };
  }

  const functionMap = toFunctionMap(functions);
  if (!functionMap || functionMap.size === 0) {
    return {
      message:
        options.missingFunctionsMessage ?? "Function metadata has not been normalized for this CommandView artifact.",
    };
  }

  const allowedFunctionIds = toNormalizedIdSet(options.allowedFunctionIds);
  const summary = collectGlobalUsageSummary(moduleMap, functionMap, allowedFunctionIds);
  if (summary.modules.length === 0 || summary.usageCount === 0) {
    return {
      message: options.emptyMessage ?? "No global variable usage was detected in this CommandView artifact.",
    };
  }

  mermaidIdCounter = 0;

  const lines = ["graph TD"];
  appendClassDefinitions(lines);
  const nodeLookup = new Map();
  appendModuleSubgraphs(lines, summary, nodeLookup);
  appendUsageEdges(lines, summary, nodeLookup);

  const stats = {
    modules: summary.moduleCount,
    globals: summary.globalCount,
    functions: summary.functionCount,
    usageCount: summary.usageCount,
    topModules: summary.topModules,
    topGlobals: summary.topGlobals,
  };

  const scopeLabel = options.scopeDescription ?? "repository";
  let statusMessage = buildStatusMessage(stats, scopeLabel);
  let statusDetails = buildStatusDetails(stats);

  if (options.fallbackNotice) {
    statusMessage = `${statusMessage} ${options.fallbackNotice}`.trim();
    statusDetails = [
      {
        type: "info",
        title: "Scope fallback applied",
        description: options.fallbackNotice,
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

function toModuleMap(candidate) {
  if (!candidate) {
    return null;
  }
  if (candidate instanceof Map) {
    return candidate;
  }
  if (Array.isArray(candidate)) {
    const map = new Map();
    candidate.forEach((entry, index) => {
      if (!entry || typeof entry !== "object") {
        return;
      }
      const key = typeof entry.moduleId === "string" ? entry.moduleId : typeof entry.id === "string" ? entry.id : String(index);
      map.set(key, entry);
    });
    return map;
  }
  if (typeof candidate === "object") {
    const map = new Map();
    Object.entries(candidate).forEach(([key, value]) => {
      map.set(key, value);
    });
    return map;
  }
  return null;
}

function toFunctionMap(candidate) {
  if (!candidate) {
    return null;
  }
  if (candidate instanceof Map) {
    return candidate;
  }
  if (Array.isArray(candidate)) {
    const map = new Map();
    candidate.forEach((entry, index) => {
      if (!entry || typeof entry !== "object") {
        return;
      }
      const key = typeof entry.id === "string" ? entry.id : String(index);
      map.set(key, entry);
    });
    return map;
  }
  if (typeof candidate === "object") {
    const map = new Map();
    Object.entries(candidate).forEach(([key, value]) => {
      map.set(key, value);
    });
    return map;
  }
  return null;
}

function toNormalizedIdSet(candidate) {
  if (!candidate) {
    return null;
  }
  if (candidate instanceof Set) {
    const normalized = Array.from(candidate).filter((value) => typeof value === "string" && value.length > 0);
    return normalized.length > 0 ? new Set(normalized) : null;
  }
  if (Array.isArray(candidate)) {
    const normalized = candidate.filter((value) => typeof value === "string" && value.length > 0);
    return normalized.length > 0 ? new Set(normalized) : null;
  }
  return null;
}

function collectGlobalUsageSummary(moduleMap, functionMap, allowedFunctionIds) {
  const allowList = allowedFunctionIds instanceof Set && allowedFunctionIds.size > 0 ? allowedFunctionIds : null;
  const modules = new Map();

  function ensureModuleEntry(moduleId, moduleRecord) {
    if (!modules.has(moduleId)) {
      modules.set(moduleId, {
        moduleId,
        globals: new Map(),
        functions: new Map(),
        edges: [],
        usageCount: 0,
      });
    }
    const entry = modules.get(moduleId);
    entry.moduleRecord = moduleRecord;
    return entry;
  }

  function ensureFunctionEntry(moduleEntry, functionId, functionRecord) {
    if (!moduleEntry.functions.has(functionId)) {
      const displayName = typeof functionRecord?.name === "string" && functionRecord.name.length > 0
        ? functionRecord.name
        : functionId;
      moduleEntry.functions.set(functionId, {
        id: functionId,
        displayName,
        globals: new Set(),
      });
    }
    return moduleEntry.functions.get(functionId);
  }

  function ensureGlobalEntry(moduleEntry, moduleRecord, globalName) {
    if (!moduleEntry.globals.has(globalName)) {
      const metadata = findModuleGlobalMetadata(moduleRecord, globalName);
      moduleEntry.globals.set(globalName, {
        name: globalName,
        valueKind: metadata?.valueKind ?? metadata?.value_kind ?? metadata?.kind ?? "unknown",
        lineno: metadata?.lineno ?? metadata?.line ?? metadata?.lineNumber ?? null,
        functions: new Set(),
      });
    }
    return moduleEntry.globals.get(globalName);
  }

  functionMap.forEach((functionRecord, functionId) => {
    if (allowList && !allowList.has(functionId)) {
      return;
    }
    if (!functionRecord || typeof functionRecord !== "object") {
      return;
    }
    const usedGlobals = Array.isArray(functionRecord.usedGlobals) ? functionRecord.usedGlobals : [];
    if (usedGlobals.length === 0) {
      return;
    }
    const moduleId = typeof functionRecord.moduleId === "string" ? functionRecord.moduleId : null;
    if (!moduleId || !moduleMap.has(moduleId)) {
      return;
    }
    const moduleRecord = moduleMap.get(moduleId);
    const moduleEntry = ensureModuleEntry(moduleId, moduleRecord);
    const functionEntry = ensureFunctionEntry(moduleEntry, functionId, functionRecord);

    usedGlobals.forEach((globalNameRaw) => {
      const globalName = typeof globalNameRaw === "string" ? globalNameRaw : null;
      if (!globalName) {
        return;
      }
      if (functionEntry.globals.has(globalName)) {
        return;
      }
      functionEntry.globals.add(globalName);

      const globalEntry = ensureGlobalEntry(moduleEntry, moduleRecord, globalName);
      globalEntry.functions.add(functionId);

      moduleEntry.edges.push({
        functionId,
        globalName,
      });
      moduleEntry.usageCount += 1;
    });
  });

  const modulesWithUsage = Array.from(modules.values())
    .filter((entry) => entry.edges.length > 0)
    .map((entry) => {
      const functions = Array.from(entry.functions.values()).sort((left, right) => {
        if (left.displayName !== right.displayName) {
          return left.displayName.localeCompare(right.displayName);
        }
        return left.id.localeCompare(right.id);
      });
      const globals = Array.from(entry.globals.values()).sort((left, right) => {
        if (left.name !== right.name) {
          return left.name.localeCompare(right.name);
        }
        const leftLine = Number.isFinite(Number(left.lineno)) ? Number(left.lineno) : Number.MAX_SAFE_INTEGER;
        const rightLine = Number.isFinite(Number(right.lineno)) ? Number(right.lineno) : Number.MAX_SAFE_INTEGER;
        if (leftLine !== rightLine) {
          return leftLine - rightLine;
        }
        return 0;
      });
      const edges = entry.edges
        .map((edge) => ({
          functionId: edge.functionId,
          globalName: edge.globalName,
        }))
        .sort((left, right) => {
          if (left.functionId !== right.functionId) {
            return left.functionId.localeCompare(right.functionId);
          }
          return left.globalName.localeCompare(right.globalName);
        });
      return {
        moduleId: entry.moduleId,
        globals,
        functions,
        edges,
        usageCount: entry.usageCount,
      };
    })
    .sort((left, right) => left.moduleId.localeCompare(right.moduleId));

  let moduleCount = 0;
  let globalCount = 0;
  let functionCount = 0;
  let usageCount = 0;
  const topModules = [];
  const topGlobals = [];

  modulesWithUsage.forEach((moduleEntry) => {
    moduleCount += 1;
    globalCount += moduleEntry.globals.length;
    functionCount += moduleEntry.functions.length;
    usageCount += moduleEntry.usageCount;

    topModules.push({
      moduleId: moduleEntry.moduleId,
      usageCount: moduleEntry.usageCount,
      functionCount: moduleEntry.functions.length,
    });

    moduleEntry.globals.forEach((globalEntry) => {
      topGlobals.push({
        moduleId: moduleEntry.moduleId,
        name: globalEntry.name,
        usageCount: globalEntry.functions.size,
        valueKind: globalEntry.valueKind ?? "unknown",
      });
    });
  });

  topModules.sort((left, right) => {
    if (right.usageCount !== left.usageCount) {
      return right.usageCount - left.usageCount;
    }
    if (right.functionCount !== left.functionCount) {
      return right.functionCount - left.functionCount;
    }
    return left.moduleId.localeCompare(right.moduleId);
  });

  topGlobals.sort((left, right) => {
    if (right.usageCount !== left.usageCount) {
      return right.usageCount - left.usageCount;
    }
    if (left.moduleId !== right.moduleId) {
      return left.moduleId.localeCompare(right.moduleId);
    }
    return left.name.localeCompare(right.name);
  });

  return {
    modules: modulesWithUsage,
    moduleCount,
    globalCount,
    functionCount,
    usageCount,
    topModules: topModules.slice(0, 10),
    topGlobals: topGlobals.slice(0, 10),
  };
}

function findModuleGlobalMetadata(moduleRecord, globalName) {
  const globals = Array.isArray(moduleRecord?.globals) ? moduleRecord.globals : [];
  for (const entry of globals) {
    if (!entry || typeof entry !== "object") {
      continue;
    }
    if (typeof entry.name === "string" && entry.name === globalName) {
      return {
        valueKind: entry.valueKind ?? entry.value_kind ?? entry.kind ?? null,
        lineno: entry.lineno ?? entry.line ?? entry.line_number ?? null,
      };
    }
  }
  return null;
}

function appendClassDefinitions(lines) {
  lines.push("  classDef module fill:#0f172a,stroke:#38bdf8,color:#f8fafc;");
  lines.push("  classDef global fill:#1f2937,stroke:#facc15,color:#fef08a;");
  lines.push("  classDef function fill:#111827,stroke:#60a5fa,color:#dbeafe;");
  lines.push("  linkStyle default stroke:#94a3b8,stroke-width:1.5px;");
}

function appendModuleSubgraphs(lines, summary, nodeLookup) {
  summary.modules.forEach((moduleEntry) => {
    const subgraphId = sanitizeMermaidId(`module_${moduleEntry.moduleId}`);
    lines.push(`  subgraph ${subgraphId}["${escapeMermaidLabel(moduleEntry.moduleId)}"]`);

    moduleEntry.globals.forEach((globalEntry) => {
      const nodeId = nextMermaidId("global");
      nodeLookup.set(`global:${moduleEntry.moduleId}:${globalEntry.name}`, nodeId);
      lines.push(`    ${nodeId}["${escapeMermaidLabel(formatGlobalLabel(globalEntry))}"]`);
      lines.push(`    class ${nodeId} global;`);
    });

    moduleEntry.functions.forEach((functionEntry) => {
      const nodeId = nextMermaidId("function");
      nodeLookup.set(`function:${moduleEntry.moduleId}:${functionEntry.id}`, nodeId);
      lines.push(`    ${nodeId}["${escapeMermaidLabel(formatFunctionLabel(functionEntry))}"]`);
      lines.push(`    class ${nodeId} function;`);
    });

    lines.push("  end");
  });
}

function appendUsageEdges(lines, summary, nodeLookup) {
  summary.modules.forEach((moduleEntry) => {
    moduleEntry.edges.forEach((edge) => {
      const sourceNode = nodeLookup.get(`function:${moduleEntry.moduleId}:${edge.functionId}`);
      const targetNode = nodeLookup.get(`global:${moduleEntry.moduleId}:${edge.globalName}`);
      if (!sourceNode || !targetNode) {
        return;
      }
      lines.push(`  ${sourceNode} --> ${targetNode}`);
    });
  });
}

function formatGlobalLabel(globalEntry) {
  const parts = [globalEntry.name];
  if (globalEntry.valueKind && globalEntry.valueKind !== "unknown") {
    parts.push(`(${globalEntry.valueKind})`);
  }
  if (Number.isFinite(Number(globalEntry.lineno))) {
    parts.push(`line ${Number(globalEntry.lineno)}`);
  }
  return parts.join(" ");
}

function formatFunctionLabel(functionEntry) {
  const globals = Array.from(functionEntry.globals);
  if (globals.length === 0) {
    return functionEntry.displayName;
  }
  const suffix = globals.length === 1 ? globals[0] : `${globals.length} globals`;
  return `${functionEntry.displayName}\n→ ${suffix}`;
}

function buildStatusMessage(stats, scopeLabel) {
  const modulesText = `${stats.modules} module${stats.modules === 1 ? "" : "s"}`;
  const globalsText = `${stats.globals} global${stats.globals === 1 ? "" : "s"}`;
  const functionsText = `${stats.functions} function${stats.functions === 1 ? "" : "s"}`;
  const referencesText = `${stats.usageCount} reference${stats.usageCount === 1 ? "" : "s"}`;
  return `Rendered Global Variable Usage Map for ${scopeLabel} (${modulesText}, ${globalsText}, ${functionsText}, ${referencesText}).`;
}

function buildStatusDetails(stats) {
  const details = [
    {
      type: "stat-summary",
      title: "Global Usage Snapshot",
      items: [
        { label: "Modules", value: String(stats.modules) },
        { label: "Globals", value: String(stats.globals) },
        { label: "Functions", value: String(stats.functions) },
        { label: "References", value: String(stats.usageCount) },
      ],
    },
  ];

  if (stats.topModules.length > 0) {
    details.push({
      type: "list",
      title: "Top Modules",
      description: "Modules with the highest volume of global references.",
      items: stats.topModules.map((entry) => ({
        header: entry.moduleId,
        body: `${entry.usageCount} reference${entry.usageCount === 1 ? "" : "s"} across ${entry.functionCount} function${entry.functionCount === 1 ? "" : "s"}`,
      })),
    });
  }

  if (stats.topGlobals.length > 0) {
    details.push({
      type: "list",
      title: "Top Globals",
      description: "Global variables referenced by the largest number of functions.",
      items: stats.topGlobals.map((entry) => ({
        header: `${entry.moduleId} · ${entry.name}`,
        body: `${entry.usageCount} function${entry.usageCount === 1 ? "" : "s"}${entry.valueKind && entry.valueKind !== "unknown" ? ` (${entry.valueKind})` : ""}`,
      })),
    });
  }

  return details;
}

function sanitizeMermaidId(value) {
  const base = typeof value === "string" ? value : String(value ?? "node");
  let sanitized = base.replace(/[^a-zA-Z0-9_]/g, "_");
  if (!sanitized) {
    sanitized = "node";
  }
  if (/^[0-9]/.test(sanitized)) {
    sanitized = `n_${sanitized}`;
  }
  return sanitized;
}

function nextMermaidId(prefix) {
  mermaidIdCounter += 1;
  const base = typeof prefix === "string" && prefix.length > 0 ? prefix : "node";
  return `${sanitizeMermaidId(base)}_${mermaidIdCounter}`;
}

function escapeMermaidLabel(value) {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value)
    .replace(/\\/g, "\\\\")
    .replace(/"/g, "\'")
    .replace(/`/g, "\'");
}

export const __test__ = {
  collectGlobalUsageSummary,
  buildStatusMessage,
  buildStatusDetails,
  sanitizeMermaidId,
  escapeMermaidLabel,
};
