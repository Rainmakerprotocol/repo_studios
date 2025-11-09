const DEFAULT_VIEW_LABEL = "Health · Function Inventory Overview";

export function buildFunctionInventoryOverviewDiagram(modules, functions, options = {}) {
  const moduleMap = toMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const functionMap = toMap(functions);
  const stats = summarizeInventoryStats(moduleMap, functionMap);

  const centralId = sanitizeMermaidId("inventory_overview");
  const docNodeId = sanitizeMermaidId("inventory_docstrings");
  const typeNodeId = sanitizeMermaidId("inventory_type_hints");
  const todoNodeId = sanitizeMermaidId("inventory_todo_hotspots");

  const lines = ["graph TD"];
  const centralLabel = buildCentralLabel(stats);
  lines.push(`  ${centralId}["${escapeMermaidLabel(centralLabel)}"]`);

  const docLabel = buildDocstringLabel(stats);
  lines.push(`  ${docNodeId}["${escapeMermaidLabel(docLabel)}"]`);
  lines.push(`  ${centralId} --> ${docNodeId}`);

  const typeLabel = buildTypeCoverageLabel(stats);
  lines.push(`  ${typeNodeId}["${escapeMermaidLabel(typeLabel)}"]`);
  lines.push(`  ${centralId} --> ${typeNodeId}`);

  const todoLabel = buildTodoLabel(stats);
  lines.push(`  ${todoNodeId}["${escapeMermaidLabel(todoLabel)}"]`);
  lines.push(`  ${centralId} --> ${todoNodeId}`);

  stats.topRoots.forEach((entry) => {
    const rootId = sanitizeMermaidId(`inventory_root_${entry.root}`);
    const rootLabel = `${entry.root}\nModules: ${entry.moduleCount}`;
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

  const viewLabel = options.viewLabel ?? DEFAULT_VIEW_LABEL;
  const statusMessage = buildStatusMessage(stats);

  return {
    definition: lines.join("\n"),
    label: viewLabel,
    statusMessage,
    stats,
  };
}

function summarizeInventoryStats(moduleMap, functionMap) {
  const stats = {
    moduleCount: moduleMap.size,
    functionCount: functionMap ? functionMap.size : 0,
    docstringTotal: 0,
    docstringWith: 0,
    typeCoverageSamples: 0,
    typeCoverageTotal: 0,
    todoFunctionCount: 0,
    topRoots: [],
  };

  if (functionMap && functionMap.size > 0) {
    functionMap.forEach((fn) => {
      stats.docstringTotal += 1;
      if (hasDocstring(fn?.docstringQuality)) {
        stats.docstringWith += 1;
      }

      const typeCoverage = Number(fn?.typeHintCoverage ?? fn?.annotationCoverage);
      if (Number.isFinite(typeCoverage)) {
        stats.typeCoverageTotal += typeCoverage;
        stats.typeCoverageSamples += 1;
      }

      const todoTags = Number(fn?.todoTags ?? 0);
      if (Number.isFinite(todoTags) && todoTags > 0) {
        stats.todoFunctionCount += 1;
      }
    });
  }

  stats.docstringPercent = stats.docstringTotal > 0 ? stats.docstringWith / stats.docstringTotal : null;
  stats.averageTypeCoverage = stats.typeCoverageSamples > 0 ? stats.typeCoverageTotal / stats.typeCoverageSamples : null;

  const rootCounts = new Map();
  moduleMap.forEach((moduleRecord) => {
    const moduleId = moduleRecord?.moduleId ?? moduleRecord?.id ?? "root";
    const root = deriveRootSegment(moduleId);
    rootCounts.set(root, (rootCounts.get(root) ?? 0) + 1);
  });

  stats.topRoots = Array.from(rootCounts.entries())
    .map(([root, moduleCount]) => ({ root, moduleCount }))
    .sort((a, b) => b.moduleCount - a.moduleCount)
    .slice(0, 5);

  return stats;
}

function buildCentralLabel(stats) {
  return `Inventory Overview\nModules: ${stats.moduleCount}\nFunctions: ${stats.functionCount}`;
}

function buildDocstringLabel(stats) {
  const lines = ["Docstrings", `With: ${stats.docstringWith}`];
  const missing = stats.docstringTotal - stats.docstringWith;
  if (missing > 0) {
    lines.push(`Missing: ${missing}`);
  }
  return lines.join("\n");
}

function buildTypeCoverageLabel(stats) {
  const lines = ["Type Hints", `Tracked: ${stats.typeCoverageSamples}`];
  if (stats.averageTypeCoverage !== null) {
    lines.push(`Average: ${formatCoveragePercent(stats.averageTypeCoverage)}`);
  }
  return lines.join("\n");
}

function buildTodoLabel(stats) {
  return `TODO Hotspots\nFunctions flagged: ${stats.todoFunctionCount}`;
}

function buildStatusMessage(stats) {
  return `Rendered Function Inventory Overview (modules ${stats.moduleCount}, functions ${stats.functionCount}).`;
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

function hasDocstring(docstringQuality) {
  if (!docstringQuality || typeof docstringQuality !== "object") {
    return false;
  }
  if (docstringQuality.exists === true) {
    return true;
  }
  if (docstringQuality.has_docstring === true || docstringQuality.present === true) {
    return true;
  }
  return docstringQuality.status === "present";
}

function deriveRootSegment(moduleId) {
  if (!moduleId || typeof moduleId !== "string") {
    return "root";
  }
  const sanitized = moduleId.replace(/\//g, ".");
  const [root] = sanitized.split(".");
  return root || "root";
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

export const __test__ = {
  summarizeInventoryStats,
  hasDocstring,
  deriveRootSegment,
  sanitizeMermaidId,
  escapeMermaidLabel,
  formatCoveragePercent,
};
