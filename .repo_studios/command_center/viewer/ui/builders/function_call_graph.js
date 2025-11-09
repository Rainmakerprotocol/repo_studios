const DEFAULT_VIEW_LABEL = "Code Flow · Function Call Graph";

export function buildFunctionCallGraphDiagram(modules, functions, callGraph, options = {}) {
  const moduleMap = toMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const functionMap = toMap(functions);
  if (!functionMap || functionMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "No function records available to build a call graph.",
    };
  }

  const callGraphMap = toMapOfArrays(callGraph);
  if (!callGraphMap || callGraphMap.size === 0) {
    return {
      message: options.missingEdgesMessage ?? "Call graph edges are not present in this CommandView artifact.",
    };
  }

  let moduleId = options.moduleId;
  if (!moduleId || !moduleMap.has(moduleId)) {
    const iterator = moduleMap.keys();
    const firstKey = iterator.next();
    moduleId = !firstKey.done ? firstKey.value : null;
  }

  if (!moduleId || !moduleMap.has(moduleId)) {
    return {
      message: options.missingModuleSelectionMessage ?? "Select a module to render the function call graph view.",
    };
  }

  const moduleRecord = moduleMap.get(moduleId);
  const moduleFunctions = Array.isArray(moduleRecord?.functions) ? moduleRecord.functions : [];
  if (moduleFunctions.length === 0) {
    return {
      message: options.emptyModuleMessage ?? `Module ${moduleId} has no functions recorded in the CommandView inventory.`,
    };
  }

  const focusFunctionId = options.focusFunctionId;
  const localSet = new Set(moduleFunctions);
  const nodeIdMap = new Map();
  const nodeLines = [];
  const localNodeIds = new Set();
  const focusNodeIds = new Set();

  const ensureNode = (functionId) => {
    if (nodeIdMap.has(functionId)) {
      return nodeIdMap.get(functionId);
    }
    const record = functionMap.get(functionId);
    if (!record) {
      return null;
    }
    const sanitizedId = sanitizeMermaidId(functionId);
    nodeIdMap.set(functionId, sanitizedId);
    const isFocus = focusFunctionId === functionId;
    const label = formatFunctionNodeLabel(record, { isFocus });
    nodeLines.push({ id: sanitizedId, label, isFocus });
    if (isFocus) {
      focusNodeIds.add(sanitizedId);
    } else {
      localNodeIds.add(sanitizedId);
    }
    return sanitizedId;
  };

  moduleFunctions.forEach((fnId) => {
    ensureNode(fnId);
  });

  const edgeSet = new Set();
  const edgeLines = [];
  moduleFunctions.forEach((sourceId) => {
    const sanitizedSource = ensureNode(sourceId);
    if (!sanitizedSource) {
      return;
    }
    const targets = callGraphMap.get(sourceId) ?? [];
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

  const lines = [
    "graph TD",
    `  classDef local fill:${NODE_STYLE_PALETTE.function.baseFill},stroke:${NODE_STYLE_PALETTE.function.baseStroke},color:#f8fafc;`,
    `  classDef focus fill:${NODE_STYLE_PALETTE.function.focusFill},stroke:${NODE_STYLE_PALETTE.function.focusStroke},color:#f8fafc;`,
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
  const viewLabel = options.viewLabel ?? DEFAULT_VIEW_LABEL;
  const label = `${moduleId} · Function Call Graph`;
  const statusMessage = edgeCount > 0
    ? `Rendered Function Call Graph for ${moduleId} (${nodeCount} functions, ${edgeCount} edges).`
    : `Rendered Function Call Graph for ${moduleId}; no intra-module call edges recorded.`;

  return {
    definition: lines.join("\n"),
    label: viewLabel,
    statusMessage,
    moduleId,
    nodeCount,
    edgeCount,
  };
}

function formatFunctionNodeLabel(record, options = {}) {
  const isFocus = options.isFocus === true;
  const parts = [];
  if (isFocus) {
    parts.push("Focus");
  }
  parts.push(record?.name ?? record?.id ?? "anonymous");

  const metrics = record?.metrics ?? {};
  const metricParts = [];
  if (Number.isFinite(Number(metrics.lineCount))) {
    metricParts.push(`LOC ${Number(metrics.lineCount)}`);
  }
  const coverage = metrics.coverage ?? record?.coverage;
  if (Number.isFinite(Number(coverage))) {
    metricParts.push(`Cov ${formatCoveragePercent(coverage)}`);
  }
  if (metricParts.length > 0) {
    parts.push(metricParts.join(" | "));
  }
  if (!isFocus && record?.moduleId) {
    parts.push(record.moduleId);
  }
  return parts.join("\n");
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

const NODE_STYLE_PALETTE = Object.freeze({
  function: {
    baseFill: "#0f172a",
    baseStroke: "#38bdf8",
    focusFill: "#1d4ed8",
    focusStroke: "#93c5fd",
  },
});

export const __test__ = {
  toMap,
  toMapOfArrays,
  sanitizeMermaidId,
  escapeMermaidLabel,
  formatCoveragePercent,
  formatFunctionNodeLabel,
};
