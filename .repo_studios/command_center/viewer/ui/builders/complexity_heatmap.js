const DEFAULT_VIEW_LABEL = "Quality Metrics · Complexity Heatmap";
const DEFAULT_CENTER_LABEL = "Complexity Heatmap";
const DEFAULT_BUCKET_LIMIT = 8;
const DEFAULT_MODULE_AGGREGATE_LIMIT = 3;
const DEFAULT_THRESHOLDS = Object.freeze({ low: 4, moderate: 9, high: 14 });
const DEFAULT_COVERAGE_RISK_THRESHOLD = 0.6;

const BUCKET_CONFIGS = Object.freeze([
  { key: "extreme", title: "Extreme", className: "complexityExtreme", fill: "#450a0a", stroke: "#fca5a5", color: "#fee2e2" },
  { key: "high", title: "High", className: "complexityHigh", fill: "#7f1d1d", stroke: "#f87171", color: "#fee2e2" },
  { key: "moderate", title: "Moderate", className: "complexityModerate", fill: "#b45309", stroke: "#fbbf24", color: "#fffbeb" },
  { key: "low", title: "Low", className: "complexityLow", fill: "#166534", stroke: "#22c55e", color: "#ecfdf5" },
  { key: "unknown", title: "Unknown", className: "complexityUnknown", fill: "#4b5563", stroke: "#cbd5f5", color: "#f1f5f9" },
]);

export function buildComplexityHeatmapDiagram(functions, options = {}) {
  const functionsMap = toMap(functions);
  const moduleMetricsMap = toMap(options.moduleMetrics);
  if (!functionsMap || functionsMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "No complexity metrics recorded in this CommandView artifact.",
    };
  }

  const bucketLimit = resolveBucketLimit(options.bucketLimit);
  const thresholds = resolveThresholds(options.severityThresholds);
  const moduleAggregateLimit = resolveAggregateLimit(options.moduleAggregateLimit);
  const coverageRiskThreshold = resolveCoverageRiskThreshold(options.coverageRiskThreshold);
  const centerLabel = typeof options.centerLabel === "string" && options.centerLabel.trim().length > 0
    ? options.centerLabel.trim()
    : DEFAULT_CENTER_LABEL;
  const centerId = sanitizeMermaidId(options.centerId ?? "complexity_heatmap_center");

  const buckets = {
    extreme: [],
    high: [],
    moderate: [],
    low: [],
    unknown: [],
  };

  let maxComplexity = Number.NEGATIVE_INFINITY;
  const moduleSummaries = new Map();
  const coverageAccumulator = createCoverageAccumulator(coverageRiskThreshold);

  functionsMap.forEach((fn, key) => {
    const complexityValue = extractComplexity(fn);
    const coverageValue = extractCoverage(fn);
    const moduleId = fn?.moduleId ?? null;
    const moduleMetrics = moduleId && moduleMetricsMap ? moduleMetricsMap.get(moduleId) ?? null : null;
    const moduleChurn = normalizeModuleChurn(moduleMetrics);

    const entry = {
      id: key ?? null,
      name: extractFunctionName(fn, key),
      moduleId,
      complexity: complexityValue,
      lineCount: extractLineCount(fn),
      coverage: coverageValue,
      moduleChurn,
    };

    if (Number.isFinite(complexityValue)) {
      if (complexityValue > maxComplexity) {
        maxComplexity = complexityValue;
      }
      const bucketKey = resolveBucketKey(complexityValue, thresholds);
      buckets[bucketKey].push(entry);
      updateModuleSummary(moduleSummaries, bucketKey, entry, moduleMetrics);
    } else {
      buckets.unknown.push(entry);
      updateModuleSummary(moduleSummaries, "unknown", entry, moduleMetrics);
    }

    if (Number.isFinite(coverageValue)) {
      coverageAccumulator.total += coverageValue;
      coverageAccumulator.count += 1;
      if (coverageValue < coverageAccumulator.threshold) {
        coverageAccumulator.belowThreshold += 1;
      }
      coverageAccumulator.max = Math.max(coverageAccumulator.max, coverageValue);
      coverageAccumulator.min = Math.min(coverageAccumulator.min, coverageValue);
      if (entry.moduleId) {
        const summary = moduleSummaries.get(entry.moduleId);
        if (summary) {
          summary.coverageSum += coverageValue;
          summary.coverageCount += 1;
        }
      }
    }
  });

  if (maxComplexity === Number.NEGATIVE_INFINITY) {
    maxComplexity = null;
  }

  const lines = ["graph TD"];
  lines.push(`  ${centerId}["${escapeMermaidLabel(centerLabel)}"]`);

  BUCKET_CONFIGS.forEach((config) => {
    const entries = buckets[config.key] ?? [];
    const nodeId = sanitizeMermaidId(`complexity_bucket_${config.key}`);
    const count = entries.length;

    const formattedEntries = entries
      .slice(0, bucketLimit)
      .map((entry) => {
        const overlays = [];
        overlays.push(Number.isFinite(entry.complexity) ? `Cx: ${formatComplexity(entry.complexity)}` : "Cx: -");
        if (Number.isFinite(entry.lineCount)) {
          overlays.push(`Lines: ${entry.lineCount}`);
        }
        if (Number.isFinite(entry.coverage)) {
          overlays.push(`Cov: ${formatCoveragePercent(entry.coverage)}`);
        }
        const churnOverlay = formatChurnOverlay(entry.moduleChurn);
        if (churnOverlay) {
          overlays.push(churnOverlay);
        }
        const moduleSuffix = entry.moduleId ? ` · ${entry.moduleId}` : "";
        return `${entry.name} (${overlays.join(" · ")})${moduleSuffix}`;
      });

    const labelLines = buildBucketLabel(config.title, count, formattedEntries, bucketLimit);
    lines.push(`  ${nodeId}["${escapeMermaidLabel(labelLines.join("\\n"))}"]`);
    lines.push(`  ${centerId} --> ${nodeId}`);
    lines.push(`  classDef ${config.className} fill:${config.fill},stroke:${config.stroke},color:${config.color};`);
    lines.push(`  class ${nodeId} ${config.className};`);
  });

  const resultLabel = options.viewLabel ?? DEFAULT_VIEW_LABEL;
  const stats = {
    extreme: buckets.extreme.length,
    high: buckets.high.length,
    moderate: buckets.moderate.length,
    low: buckets.low.length,
    unknown: buckets.unknown.length,
    maxComplexity,
    coverage: finalizeCoverageStats(coverageAccumulator),
    moduleAggregates: finalizeModuleAggregates(moduleSummaries, moduleAggregateLimit),
  };

  const statusMessage = options.statusMessageFormatter
    ? options.statusMessageFormatter(stats)
    : formatDefaultStatusMessage(stats);

  return {
    definition: lines.join("\n"),
    label: resultLabel,
    statusMessage,
    stats,
  };
}

function resolveBucketLimit(value) {
  if (!Number.isFinite(Number(value))) {
    return DEFAULT_BUCKET_LIMIT;
  }
  const numeric = Math.floor(Number(value));
  return numeric > 0 ? numeric : DEFAULT_BUCKET_LIMIT;
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

function resolveAggregateLimit(value) {
  if (!Number.isFinite(Number(value))) {
    return DEFAULT_MODULE_AGGREGATE_LIMIT;
  }
  const numeric = Math.floor(Number(value));
  return numeric > 0 ? numeric : DEFAULT_MODULE_AGGREGATE_LIMIT;
}

function resolveCoverageRiskThreshold(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0 || numeric >= 1) {
    return DEFAULT_COVERAGE_RISK_THRESHOLD;
  }
  return numeric;
}

function buildBucketLabel(title, count, entries, bucketLimit) {
  const label = [title, `Functions: ${count}`];
  if (entries.length > 0) {
    label.push(...entries);
    if (count > entries.length) {
      label.push(`+${count - entries.length} more`);
    }
  } else {
    label.push(bucketLimit === 0 ? "No capacity configured" : "None recorded");
  }
  return label;
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
  const direct = fn.metrics?.coverage ?? fn.coverage ?? fn.typeHintCoverage ?? fn.annotationCoverage;
  const numeric = Number(direct);
  return Number.isFinite(numeric) ? numeric : Number.NaN;
}

function extractLineCount(fn) {
  if (!fn || typeof fn !== "object") {
    return Number.NaN;
  }
  const direct = fn.lineCount ?? fn.line_count;
  const metricsValue = fn.metrics?.lineCount ?? fn.metrics?.line_count;
  const value = direct ?? metricsValue;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : Number.NaN;
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

function formatChurnOverlay(churn) {
  if (!churn || typeof churn !== "object") {
    return "";
  }
  const commitCount = toFiniteNumber(
    churn.commitCount ?? churn.commit_count ?? churn.total_commits ?? churn.commits
  );
  const netChanges = toFiniteNumber(churn.netChanges ?? churn.net_changes ?? churn.net);
  if (!Number.isFinite(commitCount) && !Number.isFinite(netChanges)) {
    return "";
  }
  const parts = [];
  if (Number.isFinite(commitCount)) {
    parts.push(`${commitCount}c`);
  }
  if (Number.isFinite(netChanges) && netChanges !== 0) {
    const sign = netChanges > 0 ? "+" : "";
    parts.push(`${sign}${netChanges}`);
  }
  if (parts.length === 0) {
    return "";
  }
  return `Churn: ${parts.join(" ")}`;
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

function formatDefaultStatusMessage(stats) {
  const extreme = typeof stats?.extreme === "number" ? stats.extreme : 0;
  const high = typeof stats?.high === "number" ? stats.high : 0;
  const moderate = typeof stats?.moderate === "number" ? stats.moderate : 0;
  const low = typeof stats?.low === "number" ? stats.low : 0;
  const unknown = typeof stats?.unknown === "number" ? stats.unknown : 0;
  const maxComplexity = Number.isFinite(stats?.maxComplexity) ? stats.maxComplexity : null;
  const maxSuffix = maxComplexity !== null ? `, max complexity ${formatComplexity(maxComplexity)}` : "";
  return `Rendered Complexity Heatmap (extreme ${extreme}, high ${high}, moderate ${moderate}, low ${low}, unknown ${unknown}${maxSuffix}).`;
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

function resolveBucketKey(complexityValue, thresholds) {
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

function normalizeModuleChurn(moduleMetrics) {
  if (!moduleMetrics || typeof moduleMetrics !== "object") {
    return null;
  }
  const churn = typeof moduleMetrics.gitChurn === "object" && moduleMetrics.gitChurn !== null
    ? moduleMetrics.gitChurn
    : moduleMetrics;
  if (!churn || typeof churn !== "object") {
    return null;
  }
  const commitCount = toFiniteNumber(churn.commit_count ?? churn.total_commits ?? churn.commitCount ?? churn.commits);
  const additions = toFiniteNumber(churn.additions ?? churn.total_additions ?? churn.add ?? churn.added);
  const deletions = toFiniteNumber(churn.deletions ?? churn.total_deletions ?? churn.del ?? churn.removed);
  let netChanges = toFiniteNumber(churn.net_changes ?? churn.netChanges ?? churn.net);
  if (!Number.isFinite(netChanges) && Number.isFinite(additions) && Number.isFinite(deletions)) {
    netChanges = additions - deletions;
  }
  if (!Number.isFinite(commitCount) && !Number.isFinite(additions) && !Number.isFinite(deletions) && !Number.isFinite(netChanges)) {
    return null;
  }
  return {
    commitCount: Number.isFinite(commitCount) ? commitCount : null,
    additions: Number.isFinite(additions) ? additions : null,
    deletions: Number.isFinite(deletions) ? deletions : null,
    netChanges: Number.isFinite(netChanges) ? netChanges : null,
  };
}

function updateModuleSummary(moduleSummaries, bucketKey, entry, moduleMetrics) {
  if (!entry.moduleId) {
    return;
  }
  const summary = moduleSummaries.get(entry.moduleId) ?? {
    moduleId: entry.moduleId,
    extreme: 0,
    high: 0,
    moderate: 0,
    low: 0,
    unknown: 0,
    coverageSum: 0,
    coverageCount: 0,
    maxComplexity: Number.NEGATIVE_INFINITY,
    churn: normalizeModuleChurn(moduleMetrics),
  };

  if (!moduleSummaries.has(entry.moduleId)) {
    moduleSummaries.set(entry.moduleId, summary);
  } else if (!summary.churn) {
    summary.churn = normalizeModuleChurn(moduleMetrics);
  }

  if (Number.isFinite(entry.complexity)) {
    summary.maxComplexity = Math.max(summary.maxComplexity, entry.complexity);
  }

  if (typeof summary[bucketKey] === "number") {
    summary[bucketKey] += 1;
  }
}

function finalizeModuleAggregates(moduleSummaries, limit) {
  const aggregates = Array.from(moduleSummaries.values())
    .map((summary) => {
      const hotFunctions = summary.extreme + summary.high;
      return {
        moduleId: summary.moduleId,
        extreme: summary.extreme,
        high: summary.high,
        moderate: summary.moderate,
        low: summary.low,
        unknown: summary.unknown,
        hotFunctions,
        maxComplexity: Number.isFinite(summary.maxComplexity) && summary.maxComplexity > Number.NEGATIVE_INFINITY
          ? summary.maxComplexity
          : null,
        coverageAverage: summary.coverageCount > 0 ? summary.coverageSum / summary.coverageCount : null,
        coverageCount: summary.coverageCount,
        churn: summary.churn ?? null,
      };
    })
    .filter((aggregate) => aggregate.hotFunctions > 0)
    .sort((left, right) => {
      if (right.hotFunctions !== left.hotFunctions) {
        return right.hotFunctions - left.hotFunctions;
      }
      const rightCommits = toFiniteNumber(right.churn?.commitCount);
      const leftCommits = toFiniteNumber(left.churn?.commitCount);
      if (Number.isFinite(rightCommits) && Number.isFinite(leftCommits) && rightCommits !== leftCommits) {
        return rightCommits - leftCommits;
      }
      if (Number.isFinite(right.maxComplexity) && Number.isFinite(left.maxComplexity) && right.maxComplexity !== left.maxComplexity) {
        return right.maxComplexity - left.maxComplexity;
      }
      return left.moduleId.localeCompare(right.moduleId);
    });

  return aggregates.slice(0, limit);
}

function createCoverageAccumulator(threshold) {
  return {
    threshold,
    total: 0,
    count: 0,
    belowThreshold: 0,
    min: Number.POSITIVE_INFINITY,
    max: Number.NEGATIVE_INFINITY,
  };
}

function finalizeCoverageStats(accumulator) {
  if (!accumulator || typeof accumulator !== "object" || accumulator.count === 0) {
    return null;
  }
  const average = accumulator.total / accumulator.count;
  return {
    average,
    count: accumulator.count,
    belowThreshold: accumulator.belowThreshold,
    threshold: accumulator.threshold,
    min: Number.isFinite(accumulator.min) && accumulator.min !== Number.POSITIVE_INFINITY ? accumulator.min : null,
    max: Number.isFinite(accumulator.max) && accumulator.max !== Number.NEGATIVE_INFINITY ? accumulator.max : null,
  };
}

function toFiniteNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : Number.NaN;
}

export const __test__ = {
  resolveBucketLimit,
  resolveThresholds,
  resolveAggregateLimit,
  resolveCoverageRiskThreshold,
  buildBucketLabel,
  extractComplexity,
  extractCoverage,
  extractLineCount,
  formatComplexity,
  formatCoveragePercent,
  formatChurnOverlay,
  extractFunctionName,
  formatDefaultStatusMessage,
  toMap,
  sanitizeMermaidId,
  escapeMermaidLabel,
  resolveBucketKey,
  normalizeModuleChurn,
  updateModuleSummary,
  finalizeModuleAggregates,
  createCoverageAccumulator,
  finalizeCoverageStats,
  toFiniteNumber,
};
