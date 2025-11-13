const DEFAULT_VIEW_LABEL = "Risk & Assurance · Dead Code Detection";
const DEFAULT_CENTER_LABEL = "Dead Code Detection";
const DEFAULT_MODULE_LIMIT = 8;
const DEFAULT_FUNCTION_LIMIT = 5;
const DEFAULT_IMPORT_LIMIT = 4;

export function buildDeadCodeDetectionDiagram(modules, options = {}) {
  const modulesMap = toMap(modules);
  if (!modulesMap || modulesMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const summaries = buildModuleSummaries(modulesMap);
  if (summaries.length === 0) {
    return {
      message: options.emptyMessage ?? "No dead code signals recorded for the selected scope.",
    };
  }

  summaries.sort(compareModuleSummaries);

  const moduleLimit = resolvePositiveInteger(options.moduleLimit, DEFAULT_MODULE_LIMIT);
  const functionLimit = resolvePositiveInteger(options.functionLimit, DEFAULT_FUNCTION_LIMIT);
  const importLimit = resolvePositiveInteger(options.importLimit, DEFAULT_IMPORT_LIMIT);
  const selectedSummaries = summaries.slice(0, moduleLimit);

  resetMermaidIdCounter();
  const lines = ["graph TD"];
  appendClassDefinitions(lines);

  const centerLabelRaw = typeof options.centerLabel === "string" && options.centerLabel.trim().length > 0
    ? options.centerLabel.trim()
    : DEFAULT_CENTER_LABEL;
  const centerId = sanitizeMermaidId(options.centerId ?? "dead_code_center");
  lines.push(`  ${centerId}["${escapeMermaidLabel(centerLabelRaw)}"]`);

  const seenNodes = new Set([centerId]);
  const displayedFunctionsTotal = { count: 0 };
  const displayedImportsTotal = { count: 0 };

  selectedSummaries.forEach((summary) => {
    const moduleNodeId = sanitizeMermaidId(`module_${summary.moduleId}`);
    const displayedFunctions = selectHighlightFunctions(summary, functionLimit);
    const displayedImports = selectHighlightImports(summary, importLimit);
    summary.displayedFunctions = displayedFunctions;
    summary.displayedImports = displayedImports;
    summary.hiddenFunctionCount = Math.max(summary.unreachableCount - displayedFunctions.length, 0);
    summary.hiddenImportCount = Math.max(summary.unusedImportCount - displayedImports.length, 0);

    if (!seenNodes.has(moduleNodeId)) {
      lines.push(`  ${moduleNodeId}["${escapeMermaidLabel(buildModuleLabel(summary))}"]`);
      lines.push(`  class ${moduleNodeId} ${resolveSeverityClass(summary.severity)};`);
      seenNodes.add(moduleNodeId);
    }

    lines.push(`  ${centerId} --> ${moduleNodeId}`);

    displayedFunctions.forEach((fn) => {
      const functionNodeId = sanitizeMermaidId(fn.nodeId ?? `function_${fn.qualifiedName ?? fn.name ?? fn.moduleId}`);
      if (!seenNodes.has(functionNodeId)) {
        lines.push(`  ${functionNodeId}["${escapeMermaidLabel(buildFunctionLabel(fn))}"]`);
        lines.push(`  class ${functionNodeId} deadFunction;`);
        seenNodes.add(functionNodeId);
      }
      lines.push(`  ${moduleNodeId} --> ${functionNodeId}`);
    });

    displayedImports.forEach((imp) => {
      const importNodeId = sanitizeMermaidId(imp.nodeId ?? `import_${imp.target ?? imp.importedAs ?? summary.moduleId}`);
      if (!seenNodes.has(importNodeId)) {
        lines.push(`  ${importNodeId}["${escapeMermaidLabel(buildImportLabel(imp))}"]`);
        lines.push(`  class ${importNodeId} deadImport;`);
        seenNodes.add(importNodeId);
      }
      lines.push(`  ${moduleNodeId} -.-> ${importNodeId}`);
    });

    displayedFunctionsTotal.count += displayedFunctions.length;
    displayedImportsTotal.count += displayedImports.length;
  });

  const stats = buildStatsSnapshot({
    allSummaries: summaries,
    displayedSummaries: selectedSummaries,
    moduleLimit,
    functionLimit,
    importLimit,
    displayedFunctionsTotal: displayedFunctionsTotal.count,
    displayedImportsTotal: displayedImportsTotal.count,
  });

  const statusMessage = buildStatusMessage(stats, {
    scopeDescription: options.scopeDescription,
    fallbackNotice: options.fallbackNotice,
  });

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    statusDetails: selectedSummaries.map((summary) => buildStatusDetail(summary)),
    stats,
  };
}

function buildModuleSummaries(modulesMap) {
  const summaries = [];
  modulesMap.forEach((moduleRecord, identifier) => {
    const summary = createModuleSummary(identifier, moduleRecord);
    if (summary) {
      summaries.push(summary);
    }
  });
  return summaries;
}

function createModuleSummary(identifier, moduleRecord) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return null;
  }

  const unreachable = Array.isArray(moduleRecord.unreachableFunctions)
    ? moduleRecord.unreachableFunctions
        .filter((entry) => entry && typeof entry === "object")
        .map((entry) => normalizeUnreachableFunction(entry, moduleRecord.moduleId ?? identifier))
        .filter((entry) => entry !== null)
    : [];

  const unused = Array.isArray(moduleRecord.unusedImports)
    ? moduleRecord.unusedImports
        .filter((entry) => entry && typeof entry === "object")
        .map((entry) => normalizeUnusedImport(entry))
        .filter((entry) => entry !== null)
    : [];

  const unreachableCount = unreachable.length;
  const unusedCount = unused.length;

  if (unreachableCount === 0 && unusedCount === 0) {
    return null;
  }

  unreachable.sort(compareUnreachableFunctions);
  unused.sort(compareUnusedImports);

  const totalSignals = unreachableCount + unusedCount;
  const severity = classifySeverity({
    unreachableCount,
    unusedCount,
    totalSignals,
  });

  return {
    moduleId: identifier,
    displayName: moduleRecord.moduleId ?? identifier,
    unreachable,
    unused,
    unreachableCount,
    unusedImportCount: unusedCount,
    totalSignals,
    severity,
    displayedFunctions: [],
    displayedImports: [],
    hiddenFunctionCount: 0,
    hiddenImportCount: 0,
  };
}

function compareModuleSummaries(left, right) {
  const rank = {
    critical: 0,
    high: 1,
    moderate: 2,
    observed: 3,
    clean: 4,
  };
  const leftRank = rank[left?.severity] ?? 5;
  const rightRank = rank[right?.severity] ?? 5;
  if (leftRank !== rightRank) {
    return leftRank - rightRank;
  }
  if ((right?.totalSignals ?? 0) !== (left?.totalSignals ?? 0)) {
    return (right?.totalSignals ?? 0) - (left?.totalSignals ?? 0);
  }
  if ((right?.unreachableCount ?? 0) !== (left?.unreachableCount ?? 0)) {
    return (right?.unreachableCount ?? 0) - (left?.unreachableCount ?? 0);
  }
  return (left?.moduleId ?? "").localeCompare(right?.moduleId ?? "");
}

function classifySeverity(payload) {
  const unreachable = Number.isFinite(payload?.unreachableCount) ? payload.unreachableCount : 0;
  const unused = Number.isFinite(payload?.unusedCount) ? payload.unusedCount : 0;
  const total = Number.isFinite(payload?.totalSignals) ? payload.totalSignals : unreachable + unused;

  if (unreachable >= 5 || total >= 8) {
    return "critical";
  }
  if (unreachable >= 3 || unused >= 6 || total >= 5) {
    return "high";
  }
  if (unreachable >= 1 || unused >= 3) {
    return "moderate";
  }
  if (unused > 0) {
    return "observed";
  }
  return "clean";
}

function selectHighlightFunctions(summary, limit) {
  const boundedLimit = resolvePositiveInteger(limit, DEFAULT_FUNCTION_LIMIT);
  if (!Array.isArray(summary?.unreachable) || summary.unreachable.length === 0) {
    return [];
  }
  return summary.unreachable.slice(0, boundedLimit);
}

function selectHighlightImports(summary, limit) {
  const boundedLimit = resolvePositiveInteger(limit, DEFAULT_IMPORT_LIMIT);
  if (!Array.isArray(summary?.unused) || summary.unused.length === 0) {
    return [];
  }
  return summary.unused.slice(0, boundedLimit);
}

function buildModuleLabel(summary) {
  const lines = [];
  const name = summary.displayName ?? summary.moduleId;
  lines.push(name);
  lines.push(`Severity ${formatSeverityLabel(summary.severity)}`);
  lines.push(`Unreachable ${summary.unreachableCount}`);
  lines.push(`Unused imports ${summary.unusedImportCount}`);
  if (summary.displayedFunctions.length > 0) {
    lines.push(`Example functions ${formatList(summary.displayedFunctions.map((fn) => fn.name ?? fn.qualifiedName), 3)}`);
  }
  if (summary.displayedImports.length > 0) {
    lines.push(`Example imports ${formatList(summary.displayedImports.map((imp) => imp.displayName), 3)}`);
  }
  if (summary.hiddenFunctionCount > 0) {
    lines.push(`Additional unreachable +${summary.hiddenFunctionCount}`);
  }
  if (summary.hiddenImportCount > 0) {
    lines.push(`Additional unused imports +${summary.hiddenImportCount}`);
  }
  return lines.join("\n");
}

function buildFunctionLabel(fn) {
  const parts = [fn.name ?? fn.qualifiedName ?? "anonymous"];
  if (fn.parentClass) {
    parts.push(`Class ${fn.parentClass}`);
  }
  if (Number.isFinite(fn.lineno) && fn.lineno > 0) {
    parts.push(`Line ${fn.lineno}`);
  }
  return parts.join("\n");
}

function buildImportLabel(imp) {
  const parts = [];
  const alias = imp.importedAs ?? null;
  const target = imp.target ?? null;
  if (alias && target && alias !== target) {
    parts.push(`${alias} → ${target}`);
  } else if (alias) {
    parts.push(alias);
  } else if (target) {
    parts.push(target);
  } else {
    parts.push("Unused import");
  }
  if (imp.module) {
    parts.push(`from ${imp.module}`);
  }
  if (Number.isFinite(imp.lineno) && imp.lineno > 0) {
    parts.push(`Line ${imp.lineno}`);
  }
  return parts.join("\n");
}

function buildStatsSnapshot(payload) {
  const allSummaries = Array.isArray(payload?.allSummaries) ? payload.allSummaries : [];
  const displayedSummaries = Array.isArray(payload?.displayedSummaries) ? payload.displayedSummaries : [];
  const moduleLimit = resolvePositiveInteger(payload?.moduleLimit, DEFAULT_MODULE_LIMIT);
  const functionLimit = resolvePositiveInteger(payload?.functionLimit, DEFAULT_FUNCTION_LIMIT);
  const importLimit = resolvePositiveInteger(payload?.importLimit, DEFAULT_IMPORT_LIMIT);

  const severityCounts = {
    critical: 0,
    high: 0,
    moderate: 0,
    observed: 0,
    clean: 0,
  };

  let totalUnreachable = 0;
  let totalUnused = 0;

  allSummaries.forEach((summary) => {
    totalUnreachable += summary.unreachableCount;
    totalUnused += summary.unusedImportCount;
    severityCounts[summary.severity] = (severityCounts[summary.severity] ?? 0) + 1;
  });

  return {
    moduleCount: allSummaries.length,
    displayedModules: displayedSummaries.length,
    moduleLimit,
    unreachableFunctions: totalUnreachable,
    unusedImports: totalUnused,
    displayedFunctions: Number.isFinite(payload?.displayedFunctionsTotal) ? payload.displayedFunctionsTotal : displayedSummaries.reduce((acc, summary) => acc + (summary.displayedFunctions?.length ?? 0), 0),
    displayedImports: Number.isFinite(payload?.displayedImportsTotal) ? payload.displayedImportsTotal : displayedSummaries.reduce((acc, summary) => acc + (summary.displayedImports?.length ?? 0), 0),
    functionLimit,
    importLimit,
    ...severityCounts,
  };
}

function buildStatusMessage(stats, options) {
  const scope = typeof options?.scopeDescription === "string" && options.scopeDescription.trim().length > 0
    ? ` for ${options.scopeDescription.trim()}`
    : "";
  let message = `Rendered Dead Code Detection${scope} (modules ${stats.displayedModules}/${stats.moduleCount}, unreachable ${formatNumber(stats.unreachableFunctions)}, unused imports ${formatNumber(stats.unusedImports)}, critical ${formatNumber(stats.critical)}, high ${formatNumber(stats.high)}).`;
  if (options?.fallbackNotice) {
    message = `${message} ${options.fallbackNotice}`;
  }
  return message;
}

function buildStatusDetail(summary) {
  return {
    type: "module-summary",
    title: summary.displayName ?? summary.moduleId,
    severity: summary.severity,
    unreachableCount: summary.unreachableCount,
    unusedImportCount: summary.unusedImportCount,
    highlightedFunctions: summary.displayedFunctions.map((fn) => ({
      name: fn.name,
      qualifiedName: fn.qualifiedName,
      parentClass: fn.parentClass,
      lineno: fn.lineno,
      kind: fn.kind,
    })),
    highlightedImports: summary.displayedImports.map((imp) => ({
      target: imp.target,
      importedAs: imp.importedAs,
      module: imp.module,
      lineno: imp.lineno,
      kind: imp.kind,
    })),
    additionalFunctions: summary.hiddenFunctionCount,
    additionalImports: summary.hiddenImportCount,
  };
}

function normalizeUnreachableFunction(entry, moduleId) {
  const name = sanitizeIdentifier(entry.name ?? entry.qualifiedName ?? entry.id ?? null);
  const qualifiedName = sanitizeIdentifier(entry.qualifiedName ?? entry.name ?? null);
  const lineno = normalizeLineNumber(entry.lineno ?? entry.line ?? entry.line_number ?? null);
  if (!name && !qualifiedName) {
    return null;
  }
  return {
    name: name ?? qualifiedName ?? "anonymous",
    qualifiedName: qualifiedName ?? name ?? "anonymous",
    parentClass: sanitizeIdentifier(entry.parent_class ?? entry.parentClass ?? null),
    kind: sanitizeIdentifier(entry.kind ?? entry.type ?? "function") ?? "function",
    lineno,
    moduleId,
    nodeId: `unreachable_${qualifiedName ?? name}`,
  };
}

function normalizeUnusedImport(entry) {
  const target = sanitizeIdentifier(entry.target ?? entry.symbol ?? entry.name ?? null);
  const moduleName = sanitizeIdentifier(entry.module ?? null);
  const importedAs = sanitizeIdentifier(entry.imported_as ?? entry.importedAs ?? entry.alias ?? null);
  const lineno = normalizeLineNumber(entry.lineno ?? entry.line ?? entry.line_number ?? null);
  if (!target && !importedAs) {
    return null;
  }
  const displayName = importedAs && target && importedAs !== target ? `${importedAs} → ${target}` : importedAs ?? target ?? "unused";
  return {
    target: target ?? importedAs,
    module: moduleName,
    importedAs,
    displayName,
    lineno,
    kind: sanitizeIdentifier(entry.kind ?? entry.import_kind ?? "import") ?? "import",
    nodeId: `unused_${importedAs ?? target ?? Math.random().toString(36).slice(2)}`,
  };
}

function compareUnreachableFunctions(left, right) {
  const leftLine = Number.isFinite(left?.lineno) ? left.lineno : Number.MAX_SAFE_INTEGER;
  const rightLine = Number.isFinite(right?.lineno) ? right.lineno : Number.MAX_SAFE_INTEGER;
  if (leftLine !== rightLine) {
    return leftLine - rightLine;
  }
  return (left?.qualifiedName ?? left?.name ?? "").localeCompare(right?.qualifiedName ?? right?.name ?? "");
}

function compareUnusedImports(left, right) {
  const leftLine = Number.isFinite(left?.lineno) ? left.lineno : Number.MAX_SAFE_INTEGER;
  const rightLine = Number.isFinite(right?.lineno) ? right.lineno : Number.MAX_SAFE_INTEGER;
  if (leftLine !== rightLine) {
    return leftLine - rightLine;
  }
  return (left?.displayName ?? "").localeCompare(right?.displayName ?? "");
}

function appendClassDefinitions(lines) {
  lines.push("  classDef deadCritical fill:#7f1d1d,stroke:#fca5a5,color:#fee2e2,stroke-width:2.4px;");
  lines.push("  classDef deadHigh fill:#78350f,stroke:#f97316,color:#fff7ed,stroke-width:2.1px;");
  lines.push("  classDef deadModerate fill:#1f2937,stroke:#facc15,color:#fef3c7,stroke-width:1.8px;");
  lines.push("  classDef deadObserved fill:#0f172a,stroke:#38bdf8,color:#e0f2fe,stroke-width:1.5px;");
  lines.push("  classDef deadClean fill:#0f172a,stroke:#4ade80,color:#dcfce7,stroke-width:1.3px;");
  lines.push("  classDef deadFunction fill:#0f172a,stroke:#f97316,color:#fed7aa,stroke-width:1.4px;");
  lines.push("  classDef deadImport fill:#0f172a,stroke:#38bdf8,color:#bae6fd,stroke-width:1.2px,stroke-dasharray:4 2;");
}

function resolveSeverityClass(severity) {
  switch (severity) {
    case "critical":
      return "deadCritical";
    case "high":
      return "deadHigh";
    case "moderate":
      return "deadModerate";
    case "observed":
      return "deadObserved";
    default:
      return "deadClean";
  }
}

function normalizeLineNumber(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return null;
  }
  return Math.floor(numeric);
}

function sanitizeIdentifier(value) {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

let mermaidIdCounter = 0;

function resetMermaidIdCounter() {
  mermaidIdCounter = 0;
}

function sanitizeMermaidId(value) {
  if (typeof value !== "string" || value.trim().length === 0) {
    mermaidIdCounter += 1;
    return `dead_code_${mermaidIdCounter}`;
  }
  const trimmed = value.trim();
  return trimmed.replace(/[^a-zA-Z0-9_]/g, "_");
}

function escapeMermaidLabel(label) {
  if (typeof label !== "string") {
    return "";
  }
  return label
    .replace(/"/g, '\\"')
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\|/g, "\\|")
    .replace(/\{/g, "\\{")
    .replace(/\}/g, "\\}");
}

function toMap(value) {
  if (value instanceof Map) {
    return value;
  }
  if (Array.isArray(value)) {
    return new Map(value);
  }
  if (value && typeof value === "object") {
    return new Map(Object.entries(value));
  }
  return null;
}

function resolvePositiveInteger(candidate, fallback) {
  const numeric = Number(candidate);
  if (Number.isFinite(numeric) && numeric > 0) {
    return Math.floor(numeric);
  }
  return fallback;
}

function formatSeverityLabel(severity) {
  switch (severity) {
    case "critical":
      return "Critical";
    case "high":
      return "High";
    case "moderate":
      return "Moderate";
    case "observed":
      return "Observed";
    default:
      return "Clean";
  }
}

function formatList(values, limit) {
  if (!Array.isArray(values) || values.length === 0) {
    return "none";
  }
  const boundedLimit = resolvePositiveInteger(limit, 3);
  if (values.length <= boundedLimit) {
    return values.join(", ");
  }
  const slice = values.slice(0, boundedLimit).join(", ");
  return `${slice}, +${values.length - boundedLimit}`;
}

function formatNumber(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "0";
  }
  if (numeric === 0) {
    return "0";
  }
  if (numeric >= 1000) {
    return numeric.toLocaleString("en-US");
  }
  return `${numeric}`;
}
