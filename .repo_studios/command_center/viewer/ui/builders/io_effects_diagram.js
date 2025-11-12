const DEFAULT_VIEW_LABEL = "State Effects · IO Effects Diagram";
const EFFECT_LABELS = Object.freeze({
  reads: "Reads Files",
  writes: "Writes Files",
  env: "Environment Access",
  network: "Network Calls",
});
const EFFECT_ORDER = Object.freeze(["reads", "writes", "env", "network"]);

let mermaidIdCounter = 0;

export function buildIoEffectsDiagram(modules, functions, options = {}) {
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
  const summary = collectIoEffectsSummary(moduleMap, functionMap, allowedFunctionIds);
  if (summary.modules.length === 0 || summary.effectFlagCount === 0) {
    return {
      message: options.emptyMessage ?? "No IO effects were detected in this CommandView artifact.",
    };
  }

  mermaidIdCounter = 0;

  const lines = ["graph TD"];
  appendClassDefinitions(lines);
  const nodeLookup = new Map();
  appendModuleSubgraphs(lines, summary, nodeLookup);
  appendEffectEdges(lines, summary, nodeLookup);

  const stats = {
    modules: summary.moduleCount,
    functions: summary.functionCount,
    effectFlags: summary.effectFlagCount,
    effectBreakdown: summary.effectBreakdown,
    topModules: summary.topModules,
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

function collectIoEffectsSummary(moduleMap, functionMap, allowedFunctionIds) {
  const allowList = allowedFunctionIds instanceof Set && allowedFunctionIds.size > 0 ? allowedFunctionIds : null;
  const modules = new Map();

  function ensureModuleEntry(moduleId) {
    if (!modules.has(moduleId)) {
      modules.set(moduleId, {
        moduleId,
        functions: new Map(),
        effects: new Map(),
        edges: [],
        effectFlagCount: 0,
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
        effects: [],
      });
    }
    return moduleEntry.functions.get(functionId);
  }

  function ensureEffectEntry(moduleEntry, effectKey) {
    if (!moduleEntry.effects.has(effectKey)) {
      moduleEntry.effects.set(effectKey, {
        key: effectKey,
        label: EFFECT_LABELS[effectKey] ?? effectKey,
        functions: new Set(),
      });
    }
    return moduleEntry.effects.get(effectKey);
  }

  function resolveActiveFlags(effectPayload) {
    if (!effectPayload || typeof effectPayload !== "object") {
      return [];
    }
    if (Array.isArray(effectPayload.activeFlags) && effectPayload.activeFlags.length > 0) {
      return effectPayload.activeFlags.filter((flag) => EFFECT_LABELS[flag]);
    }
    const flags = [];
    EFFECT_ORDER.forEach((flag) => {
      if (effectPayload[flag] === true) {
        flags.push(flag);
      }
    });
    return flags;
  }

  functionMap.forEach((functionRecord, functionId) => {
    if (allowList && !allowList.has(functionId)) {
      return;
    }
    if (!functionRecord || typeof functionRecord !== "object") {
      return;
    }
    const effects = functionRecord.ioEffects;
    if (!effects || typeof effects !== "object") {
      return;
    }
    const activeFlags = resolveActiveFlags(effects);
    if (activeFlags.length === 0) {
      return;
    }
    const moduleId = typeof functionRecord.moduleId === "string" ? functionRecord.moduleId : null;
    if (!moduleId || !moduleMap.has(moduleId)) {
      return;
    }
    const moduleEntry = ensureModuleEntry(moduleId);
    const functionEntry = ensureFunctionEntry(moduleEntry, functionId, functionRecord);

    activeFlags.forEach((flag) => {
      if (!EFFECT_LABELS[flag]) {
        return;
      }
      if (!functionEntry.effects.includes(flag)) {
        functionEntry.effects.push(flag);
      }
      const effectEntry = ensureEffectEntry(moduleEntry, flag);
      effectEntry.functions.add(functionId);
      moduleEntry.edges.push({ functionId, effect: flag });
      moduleEntry.effectFlagCount += 1;
    });
  });

  const modulesWithEffects = Array.from(modules.values())
    .filter((entry) => entry.edges.length > 0)
    .map((entry) => {
      entry.functions.forEach((fnEntry) => {
        fnEntry.effects.sort((left, right) => EFFECT_ORDER.indexOf(left) - EFFECT_ORDER.indexOf(right));
      });
      const functions = Array.from(entry.functions.values()).sort((left, right) => {
        if (right.effects.length !== left.effects.length) {
          return right.effects.length - left.effects.length;
        }
        if (left.displayName !== right.displayName) {
          return left.displayName.localeCompare(right.displayName);
        }
        return left.id.localeCompare(right.id);
      });
      const effects = Array.from(entry.effects.values()).sort((left, right) => {
        const rightCount = right.functions.size;
        const leftCount = left.functions.size;
        if (rightCount !== leftCount) {
          return rightCount - leftCount;
        }
        return left.label.localeCompare(right.label);
      });
      const edges = entry.edges
        .map((edge) => ({ functionId: edge.functionId, effect: edge.effect }))
        .sort((left, right) => {
          if (left.functionId !== right.functionId) {
            return left.functionId.localeCompare(right.functionId);
          }
          return left.effect.localeCompare(right.effect);
        });
      return {
        moduleId: entry.moduleId,
        functions,
        effects,
        edges,
        effectFlagCount: entry.effectFlagCount,
      };
    })
    .sort((left, right) => left.moduleId.localeCompare(right.moduleId));

  let moduleCount = 0;
  let functionCount = 0;
  let effectFlagCount = 0;
  const effectBreakdown = EFFECT_ORDER.reduce((acc, key) => {
    acc[key] = 0;
    return acc;
  }, {});
  const topModules = [];
  const topFunctions = [];

  modulesWithEffects.forEach((moduleEntry) => {
    moduleCount += 1;
    functionCount += moduleEntry.functions.length;
    effectFlagCount += moduleEntry.effectFlagCount;

    topModules.push({
      moduleId: moduleEntry.moduleId,
      effectFlags: moduleEntry.effectFlagCount,
      functionCount: moduleEntry.functions.length,
      distinctEffects: moduleEntry.effects.length,
    });

    moduleEntry.effects.forEach((effectEntry) => {
      const count = effectEntry.functions.size;
      if (effectBreakdown[effectEntry.key] !== undefined) {
        effectBreakdown[effectEntry.key] += count;
      }
    });

    moduleEntry.functions.forEach((functionEntry) => {
      topFunctions.push({
        functionId: functionEntry.id,
        moduleId: moduleEntry.moduleId,
        displayName: functionEntry.displayName,
        effects: functionEntry.effects.slice(),
        effectCount: functionEntry.effects.length,
      });
    });
  });

  topModules.sort((left, right) => {
    if (right.effectFlags !== left.effectFlags) {
      return right.effectFlags - left.effectFlags;
    }
    if (right.functionCount !== left.functionCount) {
      return right.functionCount - left.functionCount;
    }
    return left.moduleId.localeCompare(right.moduleId);
  });

  topFunctions.sort((left, right) => {
    if (right.effectCount !== left.effectCount) {
      return right.effectCount - left.effectCount;
    }
    if (left.moduleId !== right.moduleId) {
      return left.moduleId.localeCompare(right.moduleId);
    }
    return left.displayName.localeCompare(right.displayName);
  });

  return {
    modules: modulesWithEffects,
    moduleCount,
    functionCount,
    effectFlagCount,
    effectBreakdown,
    topModules: topModules.slice(0, 10),
    topFunctions: topFunctions.slice(0, 10),
  };
}

function appendClassDefinitions(lines) {
  lines.push("  classDef module fill:#0f172a,stroke:#38bdf8,color:#f8fafc;");
  lines.push("  classDef effect fill:#1f2937,stroke:#f97316,color:#ffedd5;");
  lines.push("  classDef function fill:#111827,stroke:#60a5fa,color:#dbeafe;");
  lines.push("  linkStyle default stroke:#94a3b8,stroke-width:1.5px;");
}

function appendModuleSubgraphs(lines, summary, nodeLookup) {
  summary.modules.forEach((moduleEntry) => {
    const subgraphId = sanitizeMermaidId(`module_${moduleEntry.moduleId}`);
    lines.push(`  subgraph ${subgraphId}["${escapeMermaidLabel(moduleEntry.moduleId)}"]`);

    moduleEntry.effects.forEach((effectEntry) => {
      const nodeId = nextMermaidId(`effect_${effectEntry.key}`);
      nodeLookup.set(`effect:${moduleEntry.moduleId}:${effectEntry.key}`, nodeId);
      lines.push(`    ${nodeId}["${escapeMermaidLabel(formatEffectLabel(effectEntry))}"]`);
      lines.push(`    class ${nodeId} effect;`);
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

function appendEffectEdges(lines, summary, nodeLookup) {
  summary.modules.forEach((moduleEntry) => {
    moduleEntry.edges.forEach((edge) => {
      const sourceNode = nodeLookup.get(`function:${moduleEntry.moduleId}:${edge.functionId}`);
      const targetNode = nodeLookup.get(`effect:${moduleEntry.moduleId}:${edge.effect}`);
      if (!sourceNode || !targetNode) {
        return;
      }
      lines.push(`  ${sourceNode} --> ${targetNode}`);
    });
  });
}

function formatEffectLabel(effectEntry) {
  const count = effectEntry.functions.size;
  const suffix = `${count} function${count === 1 ? "" : "s"}`;
  return `${EFFECT_LABELS[effectEntry.key] ?? effectEntry.key} · ${suffix}`;
}

function formatFunctionLabel(functionEntry) {
  if (!Array.isArray(functionEntry.effects) || functionEntry.effects.length === 0) {
    return functionEntry.displayName;
  }
  const descriptor = functionEntry.effects.join(", ");
  return `${functionEntry.displayName}\n→ ${descriptor}`;
}

function buildStatusMessage(stats, scopeLabel) {
  const modulesText = `${stats.modules} module${stats.modules === 1 ? "" : "s"}`;
  const functionsText = `${stats.functions} function${stats.functions === 1 ? "" : "s"}`;
  const flagsText = `${stats.effectFlags} effect flag${stats.effectFlags === 1 ? "" : "s"}`;
  return `Rendered IO Effects Diagram for ${scopeLabel} (${modulesText}, ${functionsText}, ${flagsText}).`;
}

function buildStatusDetails(stats) {
  const activeCategories = EFFECT_ORDER.filter((key) => (stats.effectBreakdown[key] ?? 0) > 0).length;
  const details = [
    {
      type: "stat-summary",
      title: "IO Effects Snapshot",
      items: [
        { label: "Modules", value: String(stats.modules) },
        { label: "Functions", value: String(stats.functions) },
        { label: "Effect Flags", value: String(stats.effectFlags) },
        { label: "Categories", value: String(activeCategories) },
      ],
    },
  ];

  const breakdownItems = EFFECT_ORDER
    .map((key) => ({ key, count: stats.effectBreakdown[key] ?? 0 }))
    .filter((entry) => entry.count > 0);

  if (breakdownItems.length > 0) {
    details.push({
      type: "list",
      title: "Effect Breakdown",
      description: "Functions grouped by recorded IO side effects.",
      items: breakdownItems.map((entry) => ({
        header: EFFECT_LABELS[entry.key] ?? entry.key,
        body: `${entry.count} function${entry.count === 1 ? "" : "s"}`,
      })),
    });
  }

  if (stats.topModules.length > 0) {
    details.push({
      type: "list",
      title: "Top Modules",
      description: "Modules with the highest volume of IO flags.",
      items: stats.topModules.map((entry) => ({
        header: entry.moduleId,
        body: `${entry.effectFlags} flag${entry.effectFlags === 1 ? "" : "s"} across ${entry.functionCount} function${entry.functionCount === 1 ? "" : "s"}`,
      })),
    });
  }

  if (stats.topFunctions.length > 0) {
    details.push({
      type: "list",
      title: "Top Functions",
      description: "Functions exercising multiple IO effects.",
      items: stats.topFunctions.map((entry) => ({
        header: `${entry.moduleId} · ${entry.displayName}`,
        body: `${entry.effectCount} effect${entry.effectCount === 1 ? "" : "s"} (${entry.effects.join(", ")})`,
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
  collectIoEffectsSummary,
  buildStatusMessage,
  buildStatusDetails,
  sanitizeMermaidId,
  escapeMermaidLabel,
};
