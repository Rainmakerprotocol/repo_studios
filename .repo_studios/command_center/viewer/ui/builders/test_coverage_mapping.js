const DEFAULT_VIEW_LABEL = "Risk & Assurance · Test Coverage Mapping";
const DEFAULT_CENTER_LABEL = "Test Coverage Mapping";
const DEFAULT_MODULE_LIMIT = 6;
const DEFAULT_FUNCTION_LIMIT = 5;
const COVERAGE_THRESHOLDS = Object.freeze({
  strong: 0.85,
  caution: 0.75,
  alert: 0.6,
});

export function buildTestCoverageMappingDiagram(modules, functions, options = {}) {
  const modulesMap = toMap(modules);
  if (!modulesMap || modulesMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const functionsMap = toMap(functions) ?? new Map();
  const moduleSummaries = buildModuleSummaries(modulesMap, functionsMap);
  if (moduleSummaries.length === 0) {
    return {
      message: options.emptyMessage ?? "No coverage signals recorded for the selected scope.",
    };
  }

  const moduleLimit = resolvePositiveInteger(options.moduleLimit, DEFAULT_MODULE_LIMIT);
  const functionLimit = resolvePositiveInteger(options.functionLimit, DEFAULT_FUNCTION_LIMIT);
  const selectedSummaries = moduleSummaries.slice(0, moduleLimit);

  resetMermaidIdCounter();
  const lines = ["graph TD"];
  appendClassDefinitions(lines);

  const centerLabelRaw = typeof options.centerLabel === "string" && options.centerLabel.trim().length > 0
    ? options.centerLabel.trim()
    : DEFAULT_CENTER_LABEL;
  const centerId = sanitizeMermaidId(options.centerId ?? "test_coverage_center");
  lines.push(`  ${centerId}["${escapeMermaidLabel(centerLabelRaw)}"]`);

  const seenTests = new Map();
  const seenNodes = new Set([centerId]);

  selectedSummaries.forEach((summary) => {
    const moduleNodeId = sanitizeMermaidId(`module_${summary.moduleId}`);
    const displayedFunctions = selectFunctionsForDisplay(summary, functionLimit);
    summary.displayedFunctions = displayedFunctions;
    const hiddenFunctionCount = Math.max(summary.highlightCandidates.length - displayedFunctions.length, 0);

    if (!seenNodes.has(moduleNodeId)) {
      const labelLines = buildModuleLabel(summary, hiddenFunctionCount);
      lines.push(`  ${moduleNodeId}["${escapeMermaidLabel(labelLines.join("\\n"))}"]`);
      seenNodes.add(moduleNodeId);
    }
    lines.push(`  ${centerId} --> ${moduleNodeId}`);
    lines.push(`  class ${moduleNodeId} ${resolveModuleClass(summary)};`);

    summary.tests.forEach((testName) => {
      const testNodeId = sanitizeMermaidId(`test_${testName}`);
      if (!seenNodes.has(testNodeId)) {
        lines.push(`  ${testNodeId}["${escapeMermaidLabel(buildTestLabel(testName))}"]`);
        lines.push(`  class ${testNodeId} testNode;`);
        seenNodes.add(testNodeId);
      }
      lines.push(`  ${testNodeId} -.-> ${moduleNodeId}`);
      seenTests.set(testNodeId, testName);
    });

    displayedFunctions.forEach((fn) => {
      const functionNodeId = sanitizeMermaidId(fn.id ?? `${summary.moduleId}_${fn.name}`);
      if (!seenNodes.has(functionNodeId)) {
        lines.push(`  ${functionNodeId}["${escapeMermaidLabel(buildFunctionLabel(fn))}"]`);
        lines.push(`  class ${functionNodeId} ${resolveFunctionClass(fn)};`);
        seenNodes.add(functionNodeId);
      }
      lines.push(`  ${moduleNodeId} --> ${functionNodeId}`);
    });
  });

  const stats = buildStatsSnapshot({
    allSummaries: moduleSummaries,
    displayedSummaries: selectedSummaries,
    uniqueTestCount: seenTests.size,
    moduleLimit,
    functionLimit,
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

function buildModuleSummaries(modulesMap, functionsMap) {
  const summaries = [];
  modulesMap.forEach((moduleRecord, identifier) => {
    const summary = createModuleSummary(identifier, moduleRecord, functionsMap);
    if (summary) {
      summaries.push(summary);
    }
  });
  summaries.sort(compareModuleSummaries);
  return summaries;
}

function createModuleSummary(identifier, moduleRecord, functionsMap) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return null;
  }

  const displayName = moduleRecord.moduleId ?? identifier;
  const functionIds = Array.isArray(moduleRecord.functions) ? moduleRecord.functions : [];
  const functionEntries = [];

  functionIds.forEach((functionId) => {
    const fn = functionsMap instanceof Map ? functionsMap.get(functionId) : null;
    if (!fn || typeof fn !== "object") {
      return;
    }
    const coverage = resolveCoverageValueFromFunction(fn);
    const bucket = classifyFunctionCoverage(coverage);
    functionEntries.push({
      id: fn.id ?? functionId,
      name: extractFunctionName(fn, functionId),
      moduleId: fn.moduleId ?? moduleRecord.moduleId ?? identifier,
      coverage,
      bucket,
      lineCount: resolveLineCount(fn),
    });
  });

  const coverageSignals = moduleRecord.coverageSignals ?? null;
  const tests = extractTests(coverageSignals);
  const hasTestSignal = coverageSignals?.has_matches === true;

  const hasCoverageMetrics = functionEntries.some((entry) => entry.coverage !== null);
  const hasTests = tests.length > 0 || hasTestSignal;

  if (!hasCoverageMetrics && !hasTests) {
    return null;
  }

  const coverageValues = functionEntries
    .filter((entry) => entry.coverage !== null)
    .map((entry) => entry.coverage);
  const coverageAverage = coverageValues.length > 0
    ? coverageValues.reduce((sum, value) => sum + value, 0) / coverageValues.length
    : null;

  const totals = {
    total: functionEntries.length,
    covered: 0,
    partial: 0,
    uncovered: 0,
    unknown: 0,
  };
  functionEntries.forEach((entry) => {
    totals[entry.bucket] += 1;
  });

  const highlightCandidates = functionEntries
    .filter((entry) => entry.bucket === "uncovered" || entry.bucket === "partial" || entry.bucket === "unknown")
    .sort((left, right) => {
      const leftValue = left.coverage ?? -1;
      const rightValue = right.coverage ?? -1;
      if (leftValue !== rightValue) {
        return leftValue - rightValue;
      }
      return left.name.localeCompare(right.name);
    });

  return {
    moduleId: identifier,
    displayName,
    functions: functionEntries,
    highlightCandidates,
    coverageAverage,
    totals,
    tests,
    hasTestSignal,
    coverageSignals,
    displayedFunctions: [],
  };
}

function compareModuleSummaries(left, right) {
  const leftRank = resolveModuleSeverityRank(left);
  const rightRank = resolveModuleSeverityRank(right);
  if (leftRank !== rightRank) {
    return leftRank - rightRank;
  }
  const leftCoverage = Number.isFinite(left?.coverageAverage) ? left.coverageAverage : 2;
  const rightCoverage = Number.isFinite(right?.coverageAverage) ? right.coverageAverage : 2;
  if (leftCoverage !== rightCoverage) {
    return leftCoverage - rightCoverage;
  }
  return (left?.moduleId ?? "").localeCompare(right?.moduleId ?? "");
}

function resolveModuleSeverityRank(summary) {
  if (!summary) {
    return 5;
  }
  if (summary.totals.uncovered > 0) {
    return 0;
  }
  if (summary.totals.partial > 0) {
    return 1;
  }
  if (summary.coverageAverage === null) {
    return summary.tests.length > 0 || summary.hasTestSignal ? 2 : 4;
  }
  if (summary.coverageAverage < COVERAGE_THRESHOLDS.alert) {
    return 0;
  }
  if (summary.coverageAverage < COVERAGE_THRESHOLDS.caution) {
    return 1;
  }
  if (summary.coverageAverage >= COVERAGE_THRESHOLDS.strong) {
    return 3;
  }
  return 2;
}

function selectFunctionsForDisplay(summary, limit) {
  const boundedLimit = resolvePositiveInteger(limit, DEFAULT_FUNCTION_LIMIT);
  if (!Array.isArray(summary?.highlightCandidates) || summary.highlightCandidates.length === 0) {
    return [];
  }
  return summary.highlightCandidates.slice(0, boundedLimit);
}

function buildModuleLabel(summary, hiddenFunctionCount) {
  const lines = [];
  const displayName = summary.displayName ?? summary.moduleId;
  lines.push(displayName);
  const coverageLine = summary.coverageAverage !== null
    ? `Coverage ${formatCoveragePercent(summary.coverageAverage)}`
    : "Coverage unknown";
  lines.push(coverageLine);
  lines.push(
    `Functions ${summary.totals.total} (covered ${summary.totals.covered}, partial ${summary.totals.partial}, uncovered ${summary.totals.uncovered}, unknown ${summary.totals.unknown})`
  );
  if (summary.tests.length > 0) {
    lines.push(`Tests ${formatList(summary.tests, 3)}`);
  } else if (summary.hasTestSignal) {
    lines.push("Tests signals detected");
  } else {
    lines.push("Tests none recorded");
  }
  if (hiddenFunctionCount > 0) {
    lines.push(`Additional low coverage functions +${hiddenFunctionCount}`);
  }
  return lines;
}

function buildFunctionLabel(fn) {
  const parts = [fn.name ?? fn.id ?? "anonymous"];
  if (fn.coverage !== null) {
    parts.push(`Coverage ${formatCoveragePercent(fn.coverage)}`);
  } else {
    parts.push("Coverage unknown");
  }
  if (Number.isFinite(fn.lineCount)) {
    parts.push(`LOC ${fn.lineCount}`);
  }
  return parts.join("\n");
}

function buildTestLabel(testName) {
  return `Test · ${testName}`;
}

function resolveModuleClass(summary) {
  if (!summary) {
    return "moduleBase";
  }
  if (summary.totals.uncovered > 0) {
    return "moduleAlert";
  }
  if (summary.totals.partial > 0) {
    return "moduleCaution";
  }
  if (summary.coverageAverage === null) {
    return summary.tests.length > 0 || summary.hasTestSignal ? "moduleCaution" : "moduleUnknown";
  }
  if (summary.coverageAverage < COVERAGE_THRESHOLDS.alert) {
    return "moduleAlert";
  }
  if (summary.coverageAverage < COVERAGE_THRESHOLDS.caution) {
    return "moduleCaution";
  }
  if (summary.coverageAverage >= COVERAGE_THRESHOLDS.strong) {
    return "moduleStrong";
  }
  return "moduleBase";
}

function resolveFunctionClass(fn) {
  switch (fn.bucket) {
    case "uncovered":
      return "functionUncovered";
    case "partial":
      return "functionPartial";
    case "covered":
      return "functionCovered";
    default:
      return "functionUnknown";
  }
}

function buildStatsSnapshot(payload) {
  const allSummaries = Array.isArray(payload.allSummaries) ? payload.allSummaries : [];
  const displayedSummaries = Array.isArray(payload.displayedSummaries) ? payload.displayedSummaries : [];
  const moduleLimit = resolvePositiveInteger(payload.moduleLimit, DEFAULT_MODULE_LIMIT);
  const functionLimit = resolvePositiveInteger(payload.functionLimit, DEFAULT_FUNCTION_LIMIT);

  let uncovered = 0;
  let partial = 0;
  let unknown = 0;
  let coverageSum = 0;
  let coverageCount = 0;

  allSummaries.forEach((summary) => {
    uncovered += summary.totals.uncovered;
    partial += summary.totals.partial;
    unknown += summary.totals.unknown;
    summary.functions.forEach((fn) => {
      if (fn.coverage !== null) {
        coverageSum += fn.coverage;
        coverageCount += 1;
      }
    });
  });

  const modulesWithTests = displayedSummaries.filter((summary) => summary.tests.length > 0 || summary.hasTestSignal).length;
  const modulesWithoutTests = displayedSummaries.filter((summary) => summary.tests.length === 0 && !summary.hasTestSignal).length;
  const displayedFunctions = displayedSummaries.reduce((acc, summary) => acc + (summary.displayedFunctions?.length ?? 0), 0);

  return {
    moduleCount: allSummaries.length,
    displayedModules: displayedSummaries.length,
    moduleLimit,
    uncoveredFunctions: uncovered,
    partialFunctions: partial,
    unknownFunctions: unknown,
    coverageAverage: coverageCount > 0 ? coverageSum / coverageCount : null,
    modulesWithoutTests,
    displayedFunctions,
    functionLimit,
    thresholds: { ...COVERAGE_THRESHOLDS },
    tests: {
      total: Number.isFinite(payload.uniqueTestCount) ? payload.uniqueTestCount : 0,
      modulesWithTests,
      modulesWithoutTests,
    },
  };
}

function buildStatusMessage(stats, options) {
  const scope = typeof options?.scopeDescription === "string" && options.scopeDescription.trim().length > 0
    ? ` for ${options.scopeDescription.trim()}`
    : "";
  const coveragePercent = Number.isFinite(stats.coverageAverage)
    ? `${Math.round(stats.coverageAverage * 100)}%`
    : "unknown";
  const notes = [];
  if (stats.modulesWithoutTests > 0) {
    notes.push(`modules without tests ${stats.modulesWithoutTests}`);
  }
  if (stats.unknownFunctions > 0) {
    notes.push(`unknown coverage ${stats.unknownFunctions}`);
  }
  const noteSuffix = notes.length > 0 ? `, ${notes.join(", ")}` : "";
  let message = `Rendered Test Coverage Mapping${scope} (modules ${stats.displayedModules}/${stats.moduleCount}, tests ${stats.tests.total}, uncovered ${stats.uncoveredFunctions}, partial ${stats.partialFunctions}, coverage ${coveragePercent}${noteSuffix}).`;
  if (options?.fallbackNotice) {
    message = `${message} ${options.fallbackNotice}`;
  }
  return message;
}

function buildStatusDetail(summary) {
  const displayed = Array.isArray(summary.displayedFunctions) ? summary.displayedFunctions : [];
  return {
    type: "module-summary",
    title: summary.displayName ?? summary.moduleId,
    coverageAverage: summary.coverageAverage,
    totalFunctions: summary.totals.total,
    covered: summary.totals.covered,
    partial: summary.totals.partial,
    uncovered: summary.totals.uncovered,
    unknown: summary.totals.unknown,
    testCount: summary.tests.length,
    hasTestSignal: summary.hasTestSignal,
    tests: summary.tests.slice(0, 5),
    displayedFunctions: displayed.map((fn) => ({
      id: fn.id,
      name: fn.name,
      coverage: fn.coverage,
      bucket: fn.bucket,
    })),
    hiddenFunctionCount: Math.max(summary.highlightCandidates.length - displayed.length, 0),
  };
}

function appendClassDefinitions(lines) {
  lines.push("  classDef moduleBase fill:#0f172a,stroke:#94a3b8,color:#f8fafc,stroke-width:1.5px;");
  lines.push("  classDef moduleStrong fill:#0f172a,stroke:#38bdf8,color:#e0f2fe,stroke-width:2px;");
  lines.push("  classDef moduleCaution fill:#78350f,stroke:#f59e0b,color:#fff7ed,stroke-width:2px;");
  lines.push("  classDef moduleAlert fill:#7f1d1d,stroke:#f87171,color:#fee2e2,stroke-width:2.5px;");
  lines.push("  classDef moduleUnknown fill:#1f2937,stroke:#6b7280,color:#f9fafb,stroke-width:1.5px;");
  lines.push("  classDef testNode fill:#0c4a6e,stroke:#38bdf8,color:#e0f2fe,stroke-width:1.5px;");
  lines.push("  classDef functionCovered fill:#166534,stroke:#22c55e,color:#ecfdf5,stroke-width:1.5px;");
  lines.push("  classDef functionPartial fill:#9a3412,stroke:#f97316,color:#fff7ed,stroke-width:1.5px;");
  lines.push("  classDef functionUncovered fill:#7f1d1d,stroke:#f87171,color:#fee2e2,stroke-width:1.5px;");
  lines.push("  classDef functionUnknown fill:#374151,stroke:#9ca3af,color:#f9fafb,stroke-width:1.5px;");
}

function extractTests(coverageSignals) {
  if (!coverageSignals || typeof coverageSignals !== "object") {
    return [];
  }
  const imports = Array.isArray(coverageSignals.imports) ? coverageSignals.imports : [];
  const normalized = imports
    .map((entry) => (typeof entry === "string" ? entry.trim() : ""))
    .filter((entry) => entry.length > 0);
  return Array.from(new Set(normalized));
}

function formatList(values, limit) {
  if (!Array.isArray(values) || values.length === 0) {
    return "";
  }
  const boundedLimit = Math.max(1, resolvePositiveInteger(limit, 3));
  const sample = values.slice(0, boundedLimit);
  let label = sample.join(", ");
  const remaining = values.length - sample.length;
  if (remaining > 0) {
    label += `, +${remaining} more`;
  }
  return label;
}

function resolveLineCount(fn) {
  if (Number.isFinite(fn?.lineCount)) {
    return Number(fn.lineCount);
  }
  if (Number.isFinite(fn?.metrics?.lineCount)) {
    return Number(fn.metrics.lineCount);
  }
  return null;
}

function resolveCoverageValueFromFunction(fn) {
  if (!fn || typeof fn !== "object") {
    return null;
  }
  if (Number.isFinite(fn.metrics?.coverage)) {
    return normalizeCoverageValue(fn.metrics.coverage);
  }
  if (Number.isFinite(fn.coverage)) {
    return normalizeCoverageValue(fn.coverage);
  }
  return null;
}

function normalizeCoverageValue(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return null;
  }
  if (numeric <= 0) {
    return 0;
  }
  if (numeric > 1) {
    if (numeric <= 100) {
      return Math.min(1, Math.max(0, numeric / 100));
    }
    return Math.min(1, Math.max(0, numeric));
  }
  return Math.min(1, Math.max(0, numeric));
}

function classifyFunctionCoverage(value) {
  if (!Number.isFinite(value)) {
    return "unknown";
  }
  if (value <= 0) {
    return "uncovered";
  }
  if (value >= 0.99) {
    return "covered";
  }
  return "partial";
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

function resolvePositiveInteger(value, fallback) {
  if (!Number.isFinite(Number(value))) {
    return fallback;
  }
  const numeric = Math.floor(Number(value));
  return numeric > 0 ? numeric : fallback;
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

function extractFunctionName(fn, fallbackId) {
  if (fn && typeof fn === "object") {
    if (typeof fn.name === "string" && fn.name.trim().length > 0) {
      return fn.name.trim();
    }
    if (typeof fn.id === "string" && fn.id.trim().length > 0) {
      return fn.id.trim();
    }
  }
  if (typeof fallbackId === "string" && fallbackId.trim().length > 0) {
    return fallbackId.trim();
  }
  return "anonymous";
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

function resetMermaidIdCounter() {
  mermaidIdCounter = 0;
}

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

export const __test__ = {
  normalizeCoverageValue,
  classifyFunctionCoverage,
  resolveModuleClass,
  resolveFunctionClass,
  buildModuleSummariesForTest(modules, functions) {
    const modulesMap = toMap(modules);
    const functionsMap = toMap(functions) ?? new Map();
    return buildModuleSummaries(modulesMap, functionsMap);
  },
  buildStatusMessage,
  buildModuleLabel,
  buildFunctionLabel,
  formatCoveragePercent,
};
