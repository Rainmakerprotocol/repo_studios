const DEFAULT_VIEW_LABEL = "State Effects · Exception Flow Map";

let mermaidIdCounter = 0;

export function buildExceptionFlowMapDiagram(modules, functions, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "Module metadata has not been normalized for this CommandView artifact.",
    };
  }

  const functionMap = toFunctionMap(functions);
  if (!functionMap || functionMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "Function metadata has not been normalized for this CommandView artifact.",
    };
  }

  const allowedFunctionIds = toNormalizedIdSet(options.allowedFunctionIds);
  const summary = collectExceptionFlowSummary(moduleMap, functionMap, allowedFunctionIds);
  if (summary.modules.length === 0 || summary.raiseCount === 0) {
    return {
      message: options.emptyMessage ?? "No exceptions were recorded in this CommandView artifact.",
    };
  }

  mermaidIdCounter = 0;

  const lines = ["graph TD"];
  appendClassDefinitions(lines);
  const nodeLookup = new Map();
  appendModuleSubgraphs(lines, summary, nodeLookup);
  appendExceptionEdges(lines, summary, nodeLookup);

  const stats = {
    modules: summary.moduleCount,
    functions: summary.functionCount,
    exceptions: summary.exceptionCount,
    raiseEvents: summary.raiseCount,
    topModules: summary.topModules,
    topExceptions: summary.topExceptions,
    topFunctions: summary.topFunctions,
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

function collectExceptionFlowSummary(moduleMap, functionMap, allowedFunctionIds) {
  const allowList = allowedFunctionIds instanceof Set && allowedFunctionIds.size > 0 ? allowedFunctionIds : null;
  const modules = new Map();
  const exceptionTotals = new Map();
  const distinctExceptionKeys = new Set();

  function ensureModuleEntry(moduleId) {
    if (!modules.has(moduleId)) {
      modules.set(moduleId, {
        moduleId,
        functions: new Map(),
        exceptions: new Map(),
        edges: [],
        raiseCount: 0,
      });
    }
    return modules.get(moduleId);
  }

  function ensureFunctionEntry(moduleEntry, functionId, functionRecord) {
    if (!moduleEntry.functions.has(functionId)) {
      const displayName = typeof functionRecord?.name === "string" && functionRecord.name.length > 0
        ? functionRecord.name
        : functionId;
      moduleEntry.functions.set(functionId, {
        id: functionId,
        displayName,
        exceptions: [],
      });
    }
    return moduleEntry.functions.get(functionId);
  }

  function ensureExceptionEntry(moduleEntry, exceptionKey, exceptionRecord) {
    if (!moduleEntry.exceptions.has(exceptionKey)) {
      moduleEntry.exceptions.set(exceptionKey, {
        key: exceptionKey,
        type: exceptionRecord.type ?? exceptionRecord.qualifiedName ?? exceptionKey,
        message: exceptionRecord.message ?? null,
        qualifiedName: exceptionRecord.qualifiedName ?? null,
        module: exceptionRecord.module ?? null,
        lineno: exceptionRecord.lineno ?? null,
        functions: new Set(),
      });
    }
    return moduleEntry.exceptions.get(exceptionKey);
  }

  function buildExceptionKey(exceptionRecord) {
    const type = typeof exceptionRecord?.type === "string" ? exceptionRecord.type : exceptionRecord?.qualifiedName;
    const message = typeof exceptionRecord?.message === "string" ? exceptionRecord.message : null;
    return `${type ?? "unknown"}|${message ?? ""}`;
  }

  function buildFunctionExceptionDescriptor(exceptionEntry) {
    if (!exceptionEntry || typeof exceptionEntry !== "object") {
      return "Exception";
    }
    const base = exceptionEntry.type ?? exceptionEntry.key ?? "Exception";
    if (exceptionEntry.message) {
      return `${base} (${exceptionEntry.message})`;
    }
    return base;
  }

  functionMap.forEach((functionRecord, functionId) => {
    if (allowList && !allowList.has(functionId)) {
      return;
    }
    if (!functionRecord || typeof functionRecord !== "object") {
      return;
    }
    const raised = Array.isArray(functionRecord.raisedExceptions) ? functionRecord.raisedExceptions : [];
    if (raised.length === 0) {
      return;
    }
    const moduleId = typeof functionRecord.moduleId === "string" ? functionRecord.moduleId : null;
    if (!moduleId || !moduleMap.has(moduleId)) {
      return;
    }

    const moduleEntry = ensureModuleEntry(moduleId);
    const functionEntry = ensureFunctionEntry(moduleEntry, functionId, functionRecord);

    raised.forEach((exceptionRecord) => {
      if (!exceptionRecord || typeof exceptionRecord !== "object") {
        return;
      }
      const exceptionKey = buildExceptionKey(exceptionRecord);
      if (!exceptionKey) {
        return;
      }
      const exceptionEntry = ensureExceptionEntry(moduleEntry, exceptionKey, exceptionRecord);
      if (!functionEntry.exceptions.some((item) => item.key === exceptionKey)) {
        functionEntry.exceptions.push({
          key: exceptionKey,
          label: buildFunctionExceptionDescriptor(exceptionEntry),
        });
      }
      exceptionEntry.functions.add(functionId);
      moduleEntry.edges.push({ functionId, exceptionKey });
      moduleEntry.raiseCount += 1;

      distinctExceptionKeys.add(exceptionKey);
      if (!exceptionTotals.has(exceptionKey)) {
        exceptionTotals.set(exceptionKey, {
          key: exceptionKey,
          type: exceptionEntry.type,
          message: exceptionEntry.message,
          modules: new Set(),
          functions: new Set(),
        });
      }
      const totals = exceptionTotals.get(exceptionKey);
      totals.modules.add(moduleId);
      totals.functions.add(functionId);
    });
  });

  const modulesWithExceptions = Array.from(modules.values())
    .filter((entry) => entry.edges.length > 0)
    .map((entry) => {
      entry.functions.forEach((fnEntry) => {
        fnEntry.exceptions.sort((left, right) => {
          const leftLabel = left?.label ?? "";
          const rightLabel = right?.label ?? "";
          if (leftLabel !== rightLabel) {
            return leftLabel.localeCompare(rightLabel);
          }
          const leftKey = left?.key ?? "";
          const rightKey = right?.key ?? "";
          return leftKey.localeCompare(rightKey);
        });
      });
      const functions = Array.from(entry.functions.values()).sort((left, right) => {
        if (right.exceptions.length !== left.exceptions.length) {
          return right.exceptions.length - left.exceptions.length;
        }
        if (left.displayName !== right.displayName) {
          return left.displayName.localeCompare(right.displayName);
        }
        return left.id.localeCompare(right.id);
      });
      const exceptions = Array.from(entry.exceptions.values()).sort((left, right) => {
        const leftCount = left.functions.size;
        const rightCount = right.functions.size;
        if (rightCount !== leftCount) {
          return rightCount - leftCount;
        }
        const leftType = left.type ?? "";
        const rightType = right.type ?? "";
        if (leftType !== rightType) {
          return leftType.localeCompare(rightType);
        }
        const leftMessage = left.message ?? "";
        const rightMessage = right.message ?? "";
        return leftMessage.localeCompare(rightMessage);
      });
      const edges = entry.edges
        .map((edge) => ({ functionId: edge.functionId, exceptionKey: edge.exceptionKey }))
        .sort((left, right) => {
          if (left.functionId !== right.functionId) {
            return left.functionId.localeCompare(right.functionId);
          }
          return left.exceptionKey.localeCompare(right.exceptionKey);
        });
      return {
        moduleId: entry.moduleId,
        functions,
        exceptions,
        edges,
        raiseCount: entry.raiseCount,
      };
    })
    .sort((left, right) => left.moduleId.localeCompare(right.moduleId));

  let moduleCount = 0;
  let functionCount = 0;
  let raiseCount = 0;
  const topModules = [];
  const topFunctions = [];

  modulesWithExceptions.forEach((moduleEntry) => {
    moduleCount += 1;
    functionCount += moduleEntry.functions.length;
    raiseCount += moduleEntry.raiseCount;

    topModules.push({
      moduleId: moduleEntry.moduleId,
      raiseEvents: moduleEntry.raiseCount,
      functionCount: moduleEntry.functions.length,
      distinctExceptions: moduleEntry.exceptions.length,
    });

    moduleEntry.functions.forEach((functionEntry) => {
      topFunctions.push({
        functionId: functionEntry.id,
        moduleId: moduleEntry.moduleId,
        displayName: functionEntry.displayName,
        exceptionCount: functionEntry.exceptions.length,
      });
    });
  });

  topModules.sort((left, right) => {
    if (right.raiseEvents !== left.raiseEvents) {
      return right.raiseEvents - left.raiseEvents;
    }
    if (right.functionCount !== left.functionCount) {
      return right.functionCount - left.functionCount;
    }
    return left.moduleId.localeCompare(right.moduleId);
  });

  topFunctions.sort((left, right) => {
    if (right.exceptionCount !== left.exceptionCount) {
      return right.exceptionCount - left.exceptionCount;
    }
    if (left.moduleId !== right.moduleId) {
      return left.moduleId.localeCompare(right.moduleId);
    }
    return left.displayName.localeCompare(right.displayName);
  });

  const topExceptions = Array.from(exceptionTotals.values())
    .map((entry) => ({
      key: entry.key,
      type: entry.type ?? entry.key,
      message: entry.message ?? null,
      functionCount: entry.functions.size,
      moduleCount: entry.modules.size,
    }))
    .sort((left, right) => {
      if (right.functionCount !== left.functionCount) {
        return right.functionCount - left.functionCount;
      }
      if (right.moduleCount !== left.moduleCount) {
        return right.moduleCount - left.moduleCount;
      }
      if (left.type !== right.type) {
        return left.type.localeCompare(right.type);
      }
      const leftMessage = left.message ?? "";
      const rightMessage = right.message ?? "";
      return leftMessage.localeCompare(rightMessage);
    });

  return {
    modules: modulesWithExceptions,
    moduleCount,
    functionCount,
    exceptionCount: distinctExceptionKeys.size,
    raiseCount,
    topModules: topModules.slice(0, 10),
    topExceptions: topExceptions.slice(0, 10),
    topFunctions: topFunctions.slice(0, 10),
  };
}

function appendClassDefinitions(lines) {
  lines.push("  classDef module fill:#0f172a,stroke:#38bdf8,color:#f8fafc;");
  lines.push("  classDef exception fill:#1f2937,stroke:#f87171,color:#fee2e2;");
  lines.push("  classDef function fill:#111827,stroke:#60a5fa,color:#dbeafe;");
  lines.push("  linkStyle default stroke:#94a3b8,stroke-width:1.5px;");
}

function appendModuleSubgraphs(lines, summary, nodeLookup) {
  summary.modules.forEach((moduleEntry) => {
    const subgraphId = sanitizeMermaidId(`module_${moduleEntry.moduleId}`);
    lines.push(`  subgraph ${subgraphId}["${escapeMermaidLabel(moduleEntry.moduleId)}"]`);

    moduleEntry.exceptions.forEach((exceptionEntry) => {
      const nodeId = nextMermaidId("exception");
      nodeLookup.set(`exception:${moduleEntry.moduleId}:${exceptionEntry.key}`, nodeId);
      lines.push(`    ${nodeId}["${escapeMermaidLabel(formatExceptionLabel(exceptionEntry))}"]`);
      lines.push(`    class ${nodeId} exception;`);
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

function appendExceptionEdges(lines, summary, nodeLookup) {
  summary.modules.forEach((moduleEntry) => {
    moduleEntry.edges.forEach((edge) => {
      const sourceNode = nodeLookup.get(`function:${moduleEntry.moduleId}:${edge.functionId}`);
      const targetNode = nodeLookup.get(`exception:${moduleEntry.moduleId}:${edge.exceptionKey}`);
      if (!sourceNode || !targetNode) {
        return;
      }
      lines.push(`  ${sourceNode} --> ${targetNode}`);
    });
  });
}

function formatExceptionLabel(exceptionEntry) {
  const base = exceptionEntry.type ?? "Unknown Exception";
  const suffixCount = exceptionEntry.functions.size;
  const suffix = `${suffixCount} raiser${suffixCount === 1 ? "" : "s"}`;
  if (exceptionEntry.message) {
    return `${base} · ${suffix}\n\"${exceptionEntry.message}\"`;
  }
  return `${base} · ${suffix}`;
}

function formatFunctionLabel(functionEntry) {
  if (!Array.isArray(functionEntry.exceptions) || functionEntry.exceptions.length === 0) {
    return functionEntry.displayName;
  }
  if (functionEntry.exceptions.length === 1) {
    return `${functionEntry.displayName}\n→ ${functionEntry.exceptions[0].label}`;
  }
  const labels = functionEntry.exceptions.map((item) => item.label);
  const descriptor = labels.length <= 2 ? labels.join(", ") : `${labels.slice(0, 2).join(", ")}, …`;
  return `${functionEntry.displayName}\n→ ${descriptor}`;
}

function buildStatusMessage(stats, scopeLabel) {
  const modulesText = `${stats.modules} module${stats.modules === 1 ? "" : "s"}`;
  const functionsText = `${stats.functions} function${stats.functions === 1 ? "" : "s"}`;
  const exceptionsText = `${stats.exceptions} exception${stats.exceptions === 1 ? "" : "s"}`;
  const raisesText = `${stats.raiseEvents} raise event${stats.raiseEvents === 1 ? "" : "s"}`;
  return `Rendered Exception Flow Map for ${scopeLabel} (${modulesText}, ${functionsText}, ${exceptionsText}, ${raisesText}).`;
}

function buildStatusDetails(stats) {
  const details = [
    {
      type: "stat-summary",
      title: "Exception Flow Snapshot",
      items: [
        { label: "Modules", value: String(stats.modules) },
        { label: "Functions", value: String(stats.functions) },
        { label: "Exceptions", value: String(stats.exceptions) },
        { label: "Raise Events", value: String(stats.raiseEvents) },
      ],
    },
  ];

  if (stats.topModules.length > 0) {
    details.push({
      type: "list",
      title: "Top Modules",
      description: "Modules generating the highest volume of exception raises.",
      items: stats.topModules.map((entry) => ({
        header: entry.moduleId,
        body: `${entry.raiseEvents} raise${entry.raiseEvents === 1 ? "" : "s"} across ${entry.functionCount} function${entry.functionCount === 1 ? "" : "s"}`,
      })),
    });
  }

  if (stats.topExceptions.length > 0) {
    details.push({
      type: "list",
      title: "Top Exceptions",
      description: "Exceptions raised across multiple modules or functions.",
      items: stats.topExceptions.map((entry) => ({
        header: entry.type,
        body: `${entry.functionCount} function${entry.functionCount === 1 ? "" : "s"} across ${entry.moduleCount} module${entry.moduleCount === 1 ? "" : "s"}`,
      })),
    });
  }

  if (stats.topFunctions.length > 0) {
    details.push({
      type: "list",
      title: "Top Functions",
      description: "Functions raising multiple exception types.",
      items: stats.topFunctions.map((entry) => ({
        header: `${entry.moduleId} · ${entry.displayName}`,
        body: `${entry.exceptionCount} exception${entry.exceptionCount === 1 ? "" : "s"}`,
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
  collectExceptionFlowSummary,
  buildStatusMessage,
  buildStatusDetails,
  sanitizeMermaidId,
  escapeMermaidLabel,
};
