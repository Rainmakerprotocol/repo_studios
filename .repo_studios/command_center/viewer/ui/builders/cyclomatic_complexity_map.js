const DEFAULT_VIEW_LABEL = "Quality Metrics · Cyclomatic Complexity Map";
const DEFAULT_MODULE_LIMIT = 12;
const DEFAULT_FUNCTION_LIMIT = 6;
const DEFAULT_THRESHOLDS = Object.freeze({ low: 4, moderate: 9, high: 14 });
const DEFAULT_COVERAGE_THRESHOLD = 0.6;

const BUCKET_ORDER = Object.freeze(["extreme", "high", "moderate", "low", "unknown"]);
const BUCKET_METADATA = Object.freeze({
  extreme: {
    key: "extreme",
    title: "Extreme Complexity",
    className: "complexityExtreme",
    summaryLabel: "Extreme",
  },
  high: {
    key: "high",
    title: "High Complexity",
    className: "complexityHigh",
    summaryLabel: "High",
  },
  moderate: {
    key: "moderate",
    title: "Moderate Complexity",
    className: "complexityModerate",
    summaryLabel: "Moderate",
  },
  low: {
    key: "low",
    title: "Low Complexity",
    className: "complexityLow",
    summaryLabel: "Low",
  },
  unknown: {
    key: "unknown",
    title: "Unknown",
    className: "complexityUnknown",
    summaryLabel: "Unknown",
  },
});

const CLASS_DEFINITIONS = Object.freeze([
  "classDef moduleSummary fill:#0b1120,stroke:#94a3b8,color:#e2e8f0",
  "classDef bucketHub fill:#111827,stroke:#64748b,color:#e2e8f0",
  "classDef complexityExtreme fill:#450a0a,stroke:#fca5a5,color:#fee2e2",
  "classDef complexityHigh fill:#7f1d1d,stroke:#f87171,color:#fee2e2",
  "classDef complexityModerate fill:#b45309,stroke:#fbbf24,color:#fffbeb",
  "classDef complexityLow fill:#166534,stroke:#22c55e,color:#ecfdf5",
  "classDef complexityUnknown fill:#374151,stroke:#9ca3af,color:#f3f4f6",
]);

let mermaidIdCounter = 0;

export function buildCyclomaticComplexityMapDiagram(functions, options = {}) {
  const functionsMap = toMap(functions);
  if (!functionsMap || functionsMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "No complexity metrics recorded in this CommandView artifact.",
    };
  }

  mermaidIdCounter = 0;

  const thresholds = resolveThresholds(options.severityThresholds);
  const moduleLimit = resolvePositiveInteger(options.moduleLimit, DEFAULT_MODULE_LIMIT);
  const functionLimit = resolvePositiveInteger(options.functionLimit, DEFAULT_FUNCTION_LIMIT);
  const coverageThreshold = resolveCoverageThreshold(options.coverageRiskThreshold);
  const modulesMap = toMap(options.modules);

  const moduleEntries = new Map();
  functionsMap.forEach((fn, key) => {
    if (!fn || typeof fn !== "object") {
      return;
    }
    const moduleId = normalizeString(fn.moduleId ?? fn.module_id) || "(unknown module)";
    const entry = getOrCreateModuleEntry(moduleEntries, moduleId, modulesMap, coverageThreshold);
    addFunctionToModule(entry, key, fn, thresholds, coverageThreshold);
  });

  const entries = Array.from(moduleEntries.values()).filter((entry) => entry.totalFunctions > 0);
  if (entries.length === 0) {
    return {
      message: options.emptyMessage ?? "No complexity metrics recorded for this selection.",
    };
  }

  entries.forEach((entry) => finalizeModuleEntry(entry, functionLimit));

  entries.sort((left, right) => compareModuleEntries(left, right));

  const totalModules = entries.length;
  const displayEntries = entries.slice(0, moduleLimit);
  const hiddenModules = Math.max(0, totalModules - displayEntries.length);

  const lines = ["graph TD"];
  appendClassDefinitions(lines);

  displayEntries.forEach((entry) => {
    appendModuleSection(lines, entry);
  });

  const totals = aggregateTotals(entries);
  totals.displayedModules = displayEntries.length;
  totals.hiddenModules = hiddenModules;
  const scopeDescription = normalizeString(options.scopeDescription) || "repository";
  let statusMessage = buildStatusMessage(totals, scopeDescription, displayEntries.length, hiddenModules);
  const statusDetails = buildStatusDetails(displayEntries, totals.coverageThreshold);

  const fallbackNotice = normalizeString(options.fallbackNotice);
  if (fallbackNotice) {
    statusMessage = `${statusMessage} ${fallbackNotice}`.trim();
    statusDetails.unshift({
      type: "info",
      title: "Scope fallback applied",
      description: fallbackNotice,
    });
  }

  return {
    definition: lines.join("\n"),
    label: options.viewLabel || DEFAULT_VIEW_LABEL,
    statusMessage,
    statusDetails,
    stats: totals,
  };
}

function getOrCreateModuleEntry(moduleEntries, moduleId, modulesMap, coverageThreshold) {
  if (moduleEntries.has(moduleId)) {
    return moduleEntries.get(moduleId);
  }

  const moduleRecord = modulesMap && modulesMap instanceof Map ? modulesMap.get(moduleId) : null;
  const entry = {
    moduleId,
    moduleLabel: moduleRecord?.moduleLabel || moduleRecord?.module_id || moduleId,
    counts: createSeverityCounter(),
    buckets: createModuleBuckets(),
    totalFunctions: 0,
    complexitySum: 0,
    complexityCount: 0,
    maxComplexity: Number.NEGATIVE_INFINITY,
    coverageSum: 0,
    coverageCount: 0,
    coverageBelowThreshold: 0,
    coverageThreshold,
    moduleRecord,
    topFunctions: [],
  };
  moduleEntries.set(moduleId, entry);
  return entry;
}

function createSeverityCounter() {
  return {
    extreme: 0,
    high: 0,
    moderate: 0,
    low: 0,
    unknown: 0,
  };
}

function createModuleBuckets() {
  const buckets = {};
  BUCKET_ORDER.forEach((bucketKey) => {
    buckets[bucketKey] = {
      key: bucketKey,
      title: BUCKET_METADATA[bucketKey].title,
      className: BUCKET_METADATA[bucketKey].className,
      items: [],
      displayItems: [],
      extraCount: 0,
    };
  });
  return buckets;
}

function addFunctionToModule(entry, functionId, fn, thresholds, coverageThreshold) {
  const complexityValue = extractComplexity(fn);
  const bucketKey = resolveBucket(complexityValue, thresholds);
  const coverageValue = extractCoverage(fn);
  const lineCount = extractLineCount(fn);
  const name = extractFunctionName(fn, functionId);

  entry.totalFunctions += 1;
  if (Number.isFinite(complexityValue)) {
    entry.complexitySum += complexityValue;
    entry.complexityCount += 1;
    if (complexityValue > entry.maxComplexity) {
      entry.maxComplexity = complexityValue;
    }
  }
  if (Number.isFinite(coverageValue)) {
    entry.coverageSum += coverageValue;
    entry.coverageCount += 1;
    if (coverageValue < coverageThreshold) {
      entry.coverageBelowThreshold += 1;
    }
  }

  entry.counts[bucketKey] += 1;

  entry.buckets[bucketKey].items.push({
    id: functionId,
    name,
    moduleId: entry.moduleId,
    complexity: complexityValue,
    coverage: coverageValue,
    lineCount,
  });

  entry.topFunctions.push({
    id: functionId,
    name,
    complexity: complexityValue,
    moduleId: entry.moduleId,
  });
}

function finalizeModuleEntry(entry, functionLimit) {
  BUCKET_ORDER.forEach((bucketKey) => {
    const bucket = entry.buckets[bucketKey];
    bucket.items.sort((left, right) => compareByComplexity(right, left));
    bucket.displayItems = bucket.items.slice(0, functionLimit);
    bucket.extraCount = Math.max(0, bucket.items.length - bucket.displayItems.length);
  });

  entry.topFunctions.sort((left, right) => compareByComplexity(right, left));
  entry.topFunctions = entry.topFunctions.slice(0, 3);

  if (entry.maxComplexity === Number.NEGATIVE_INFINITY) {
    entry.maxComplexity = null;
  }

  entry.averageComplexity = entry.complexityCount > 0 ? entry.complexitySum / entry.complexityCount : null;
  entry.coverageAverage = entry.coverageCount > 0 ? entry.coverageSum / entry.coverageCount : null;
}

function compareModuleEntries(left, right) {
  const extremeDiff = right.counts.extreme - left.counts.extreme;
  if (extremeDiff !== 0) {
    return extremeDiff;
  }
  const highDiff = right.counts.high - left.counts.high;
  if (highDiff !== 0) {
    return highDiff;
  }
  const avgLeft = Number.isFinite(left.averageComplexity) ? left.averageComplexity : -1;
  const avgRight = Number.isFinite(right.averageComplexity) ? right.averageComplexity : -1;
  const avgDiff = avgRight - avgLeft;
  if (avgDiff !== 0) {
    return avgDiff > 0 ? 1 : -1;
  }
  const maxLeft = Number.isFinite(left.maxComplexity) ? left.maxComplexity : -1;
  const maxRight = Number.isFinite(right.maxComplexity) ? right.maxComplexity : -1;
  if (maxRight !== maxLeft) {
    return maxRight > maxLeft ? 1 : -1;
  }
  return left.moduleId.localeCompare(right.moduleId);
}

function aggregateTotals(entries) {
  const totals = {
    totalModules: entries.length,
    displayedModules: 0,
    hiddenModules: 0,
    extreme: 0,
    high: 0,
    moderate: 0,
    low: 0,
    unknown: 0,
    maxComplexity: null,
    averageComplexity: null,
    coverageAverage: null,
    coverageBelowThreshold: 0,
    coverageThreshold: entries.length > 0 ? entries[0].coverageThreshold : DEFAULT_COVERAGE_THRESHOLD,
    topModules: [],
  };

  let complexitySum = 0;
  let complexityCount = 0;
  let coverageSum = 0;
  let coverageCount = 0;
  let maxComplexity = Number.NEGATIVE_INFINITY;

  entries.forEach((entry) => {
    totals.extreme += entry.counts.extreme;
    totals.high += entry.counts.high;
    totals.moderate += entry.counts.moderate;
    totals.low += entry.counts.low;
    totals.unknown += entry.counts.unknown;
    totals.coverageBelowThreshold += entry.coverageBelowThreshold;

    if (Number.isFinite(entry.maxComplexity) && entry.maxComplexity > maxComplexity) {
      maxComplexity = entry.maxComplexity;
    }

    if (Number.isFinite(entry.averageComplexity)) {
      complexitySum += entry.averageComplexity;
      complexityCount += 1;
    }

    if (Number.isFinite(entry.coverageAverage)) {
      coverageSum += entry.coverageAverage;
      coverageCount += 1;
    }

    totals.topModules.push({
      moduleId: entry.moduleId,
      extreme: entry.counts.extreme,
      high: entry.counts.high,
      averageComplexity: entry.averageComplexity,
      maxComplexity: entry.maxComplexity,
    });
  });

  if (complexityCount > 0) {
    totals.averageComplexity = complexitySum / complexityCount;
  }
  if (coverageCount > 0) {
    totals.coverageAverage = coverageSum / coverageCount;
  }
  if (maxComplexity !== Number.NEGATIVE_INFINITY) {
    totals.maxComplexity = maxComplexity;
  }

  totals.topModules.sort((left, right) => {
    if (right.extreme !== left.extreme) {
      return right.extreme - left.extreme;
    }
    if (right.high !== left.high) {
      return right.high - left.high;
    }
    const avgLeft = Number.isFinite(left.averageComplexity) ? left.averageComplexity : -1;
    const avgRight = Number.isFinite(right.averageComplexity) ? right.averageComplexity : -1;
    if (avgRight !== avgLeft) {
      return avgRight > avgLeft ? 1 : -1;
    }
    return left.moduleId.localeCompare(right.moduleId);
  });

  return totals;
}

function buildStatusMessage(stats, scopeDescription, displayedModules, hiddenModules) {
  const maxSnippet = Number.isFinite(stats.maxComplexity)
    ? `, max complexity ${formatComplexity(stats.maxComplexity)}`
    : "";
  const modulesSnippet = hiddenModules > 0
    ? `${displayedModules} modules (+${hiddenModules} more)`
    : `${displayedModules} modules`;
  return `Rendered Cyclomatic Complexity Map for ${scopeDescription} (extreme ${stats.extreme}, high ${stats.high}, moderate ${stats.moderate}, low ${stats.low}, unknown ${stats.unknown}${maxSnippet}; ${modulesSnippet}).`;
}

function buildStatusDetails(displayEntries, coverageThreshold) {
  if (!Array.isArray(displayEntries) || displayEntries.length === 0) {
    return [];
  }
  return displayEntries.slice(0, 3).map((entry) => {
    const severity = entry.counts.extreme > 0 || entry.counts.high > 2 ? "warning" : "stat-summary";
    const topFunction = entry.topFunctions.length > 0 ? entry.topFunctions[0] : null;
    const coverageSnippet = Number.isFinite(entry.coverageAverage)
      ? `Avg coverage ${formatCoveragePercent(entry.coverageAverage)}${entry.coverageBelowThreshold > 0 ? `, ${entry.coverageBelowThreshold} below ${Math.round(coverageThreshold * 100)}%` : ""}`
      : null;
    const complexitySnippet = Number.isFinite(entry.averageComplexity)
      ? `Avg CC ${formatComplexity(entry.averageComplexity)}`
      : null;
    const topSnippet = topFunction && Number.isFinite(topFunction.complexity)
      ? `Top: ${topFunction.name} (CC ${formatComplexity(topFunction.complexity)})`
      : null;
    const parts = [complexitySnippet, coverageSnippet, topSnippet].filter(Boolean);
    return {
      type: severity,
      title: entry.moduleLabel,
      description: parts.length > 0
        ? parts.join(" · ")
        : "No complexity metrics recorded for this module.",
    };
  });
}

function appendModuleSection(lines, entry) {
  const groupId = sanitizeMermaidId(`${entry.moduleId}_group`);
  const hubId = sanitizeMermaidId(`${entry.moduleId}_hub`);
  lines.push(`  subgraph ${groupId}["${escapeMermaidLabel(buildModuleLabel(entry))}"]`);
  lines.push("    direction TB");
  lines.push(`    ${hubId}["${escapeMermaidLabel(buildModuleHubLabel(entry))}"]`);
  lines.push(`    class ${hubId} moduleSummary;`);

  BUCKET_ORDER.forEach((bucketKey) => {
    appendBucket(lines, entry, bucketKey, hubId);
  });

  lines.push("  end");
}

function buildModuleLabel(entry) {
  const severityLine = `Extreme ${entry.counts.extreme} · High ${entry.counts.high} · Moderate ${entry.counts.moderate} · Low ${entry.counts.low} · Unknown ${entry.counts.unknown}`;
  return `${entry.moduleLabel}\n${severityLine}`;
}

function buildModuleHubLabel(entry) {
  const parts = [`Functions ${entry.totalFunctions}`];
  if (Number.isFinite(entry.averageComplexity)) {
    parts.push(`Avg CC ${formatComplexity(entry.averageComplexity)}`);
  }
  if (Number.isFinite(entry.maxComplexity)) {
    parts.push(`Max CC ${formatComplexity(entry.maxComplexity)}`);
  }
  if (Number.isFinite(entry.coverageAverage)) {
    parts.push(`Avg Cov ${formatCoveragePercent(entry.coverageAverage)}`);
  }
  return parts.join(" · ") || "Summary";
}

function appendBucket(lines, entry, bucketKey, parentHubId) {
  const bucket = entry.buckets[bucketKey];
  if (!bucket || bucket.items.length === 0) {
    return;
  }
  const bucketId = sanitizeMermaidId(`${entry.moduleId}_${bucketKey}_bucket`);
  lines.push(`    ${bucketId}["${escapeMermaidLabel(buildBucketLabel(bucket, entry.counts[bucketKey]))}"]`);
  lines.push(`    class ${bucketId} bucketHub;`);
  lines.push(`    ${parentHubId} --> ${bucketId}`);
  bucket.displayItems.forEach((item, index) => {
    const nodeId = sanitizeMermaidId(`${entry.moduleId}_${bucketKey}_${index}`);
    lines.push(`    ${nodeId}["${escapeMermaidLabel(buildFunctionLabel(item))}"]`);
    lines.push(`    class ${nodeId} ${bucket.className};`);
    lines.push(`    ${bucketId} --> ${nodeId}`);
  });
  if (bucket.extraCount > 0) {
    const extraId = sanitizeMermaidId(`${entry.moduleId}_${bucketKey}_more`);
    lines.push(`    ${extraId}["${escapeMermaidLabel(formatOverflowLabel(bucket.extraCount, bucketKey))}"]`);
    lines.push(`    class ${extraId} ${bucket.className};`);
    lines.push(`    ${bucketId} --> ${extraId}`);
  }
}

function buildBucketLabel(bucket, count) {
  return `${bucket.title}\nFunctions ${count}`;
}

function buildFunctionLabel(item) {
  const overlays = [];
  if (Number.isFinite(item.complexity)) {
    overlays.push(`CC ${formatComplexity(item.complexity)}`);
  }
  if (Number.isFinite(item.coverage)) {
    overlays.push(`Cov ${formatCoveragePercent(item.coverage)}`);
  }
  if (Number.isFinite(item.lineCount)) {
    overlays.push(`Lines ${item.lineCount}`);
  }
  const overlayText = overlays.length > 0 ? `\n${overlays.join(" · ")}` : "";
  return `${item.name}${overlayText}`;
}

function formatOverflowLabel(extraCount, bucketKey) {
  const meta = BUCKET_METADATA[bucketKey];
  const noun = meta ? meta.summaryLabel.toLowerCase() : "items";
  return `+${extraCount} more ${noun}`;
}

function resolveThresholds(thresholds) {
  if (!thresholds || typeof thresholds !== "object") {
    return DEFAULT_THRESHOLDS;
  }
  const low = Number(thresholds.low);
  const moderate = Number(thresholds.moderate);
  const high = Number(thresholds.high);
  if (!Number.isFinite(low) || !Number.isFinite(moderate) || !Number.isFinite(high)) {
    return DEFAULT_THRESHOLDS;
  }
  if (!(low <= moderate && moderate <= high)) {
    return DEFAULT_THRESHOLDS;
  }
  return { low, moderate, high };
}

function resolveCoverageThreshold(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0 || numeric >= 1) {
    return DEFAULT_COVERAGE_THRESHOLD;
  }
  return numeric;
}

function resolvePositiveInteger(value, fallback) {
  if (!Number.isFinite(Number(value))) {
    return fallback;
  }
  const numeric = Math.floor(Number(value));
  return numeric > 0 ? numeric : fallback;
}

function resolveBucket(complexityValue, thresholds) {
  if (!Number.isFinite(complexityValue)) {
    return "unknown";
  }
  if (complexityValue > thresholds.high) {
    return "extreme";
  }
  if (complexityValue > thresholds.moderate) {
    return "high";
  }
  if (complexityValue > thresholds.low) {
    return "moderate";
  }
  return "low";
}

function extractComplexity(fn) {
  if (!fn || typeof fn !== "object") {
    return Number.NaN;
  }
  const direct = fn.cyclomaticComplexity ?? fn.cyclomatic_complexity;
  const metricsValue = fn.metrics?.complexity ?? fn.metrics?.cyclomatic_complexity;
  const value = direct ?? metricsValue;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : Number.NaN;
}

function extractCoverage(fn) {
  if (!fn || typeof fn !== "object") {
    return Number.NaN;
  }
  const coverage = fn.metrics?.coverage ?? fn.coverage ?? null;
  const numeric = Number(coverage);
  return Number.isFinite(numeric) ? numeric : Number.NaN;
}

function extractLineCount(fn) {
  if (!fn || typeof fn !== "object") {
    return Number.NaN;
  }
  const raw = fn.metrics?.lineCount ?? fn.metrics?.line_count ?? fn.lineCount ?? fn.line_count;
  const numeric = Number(raw);
  return Number.isFinite(numeric) ? numeric : Number.NaN;
}

function extractFunctionName(fn, fallbackId) {
  if (fn && typeof fn.name === "string" && fn.name.trim().length > 0) {
    return fn.name.trim();
  }
  if (fn && typeof fn.id === "string" && fn.id.trim().length > 0) {
    return fn.id.trim();
  }
  if (typeof fallbackId === "string" && fallbackId.trim().length > 0) {
    return fallbackId.trim();
  }
  return "anonymous";
}

function compareByComplexity(left, right) {
  const leftValue = Number.isFinite(left?.complexity) ? left.complexity : Number.NEGATIVE_INFINITY;
  const rightValue = Number.isFinite(right?.complexity) ? right.complexity : Number.NEGATIVE_INFINITY;
  if (leftValue === rightValue) {
    const leftName = normalizeString(left?.name) || "";
    const rightName = normalizeString(right?.name) || "";
    return leftName.localeCompare(rightName);
  }
  return leftValue - rightValue;
}

function appendClassDefinitions(lines) {
  CLASS_DEFINITIONS.forEach((definition) => {
    lines.push(`  ${definition}`);
  });
}

function toMap(value) {
  if (value instanceof Map) {
    return value;
  }
  if (Array.isArray(value)) {
    const map = new Map();
    value.forEach((item, index) => {
      if (!item || typeof item !== "object") {
        return;
      }
      const key = item.id ?? item.moduleId ?? item.module_id ?? String(index);
      map.set(key, item);
    });
    return map;
  }
  if (value && typeof value === "object") {
    const map = new Map();
    Object.entries(value).forEach(([key, item]) => {
      map.set(key, item);
    });
    return map;
  }
  return null;
}

function sanitizeMermaidId(raw) {
  if (!raw || typeof raw !== "string") {
    mermaidIdCounter += 1;
    return `node_${mermaidIdCounter}`;
  }
  const sanitized = raw.replace(/[^a-zA-Z0-9_]/g, "_");
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

function formatComplexity(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "-";
  }
  return numeric.toFixed(0);
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

function normalizeString(value) {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export const __test__ = {
  resolveBucket,
  resolveThresholds,
  resolveCoverageThreshold,
  buildFunctionLabel,
  buildBucketLabel,
  buildModuleLabel,
};
