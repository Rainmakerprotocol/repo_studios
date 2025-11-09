const DEFAULT_VIEW_LABEL = "Quality Metrics · Logging Flow";
const DEFAULT_CENTER_LABEL = "Logging Flow Overview";
const DEFAULT_BUCKET_LIMIT = 8;
const DEFAULT_MODULE_AGGREGATE_LIMIT = 5;

const CANONICAL_LEVEL_ORDER = Object.freeze(["critical", "error", "warning", "info", "debug", "unknown"]);
const BUCKET_CONFIGS = Object.freeze([
  { key: "critical", title: "Critical", className: "logCritical", fill: "#450a0a", stroke: "#f87171", color: "#fee2e2" },
  { key: "error", title: "Error", className: "logError", fill: "#7f1d1d", stroke: "#fca5a5", color: "#fee2e2" },
  { key: "warning", title: "Warning", className: "logWarning", fill: "#9a3412", stroke: "#f97316", color: "#fff7ed" },
  { key: "info", title: "Info", className: "logInfo", fill: "#1d4ed8", stroke: "#93c5fd", color: "#eff6ff" },
  { key: "debug", title: "Debug", className: "logDebug", fill: "#0369a1", stroke: "#67e8f9", color: "#ecfeff" },
  { key: "unknown", title: "Unknown", className: "logUnknown", fill: "#4b5563", stroke: "#cbd5f5", color: "#f8fafc" },
  { key: "silent", title: "No Logging", className: "logSilent", fill: "#111827", stroke: "#9ca3af", color: "#e5e7eb" },
]);

const LEVEL_ALIASES = Object.freeze({
  critical: "critical",
  fatal: "critical",
  crit: "critical",
  error: "error",
  err: "error",
  exception: "error",
  warning: "warning",
  warn: "warning",
  wng: "warning",
  info: "info",
  notice: "info",
  informational: "info",
  debug: "debug",
  trace: "debug",
  verbose: "debug",
  notset: "unknown",
  unknown: "unknown",
});

const LEVEL_SEVERITY = Object.freeze({
  critical: 5,
  error: 4,
  warning: 3,
  info: 2,
  debug: 1,
  unknown: 0,
  silent: -1,
});

export function buildLoggingFlowDiagram(functions, options = {}) {
  const functionsMap = toMap(functions);
  if (!functionsMap || functionsMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "No functions recorded in this CommandView artifact.",
    };
  }

  const bucketLimit = resolveBucketLimit(options.bucketLimit);
  const moduleAggregateLimit = resolveAggregateLimit(options.moduleAggregateLimit);
  const centerLabel = typeof options.centerLabel === "string" && options.centerLabel.trim().length > 0
    ? options.centerLabel.trim()
    : DEFAULT_CENTER_LABEL;
  const centerId = sanitizeMermaidId(options.centerId ?? "logging_flow_center");

  const levelEventCounts = createLevelEventCounter();
  const buckets = createBucketRegistry();
  const moduleSummaries = new Map();

  let emitterCount = 0;

  functionsMap.forEach((fn, key) => {
    const entry = buildFunctionLoggingEntry(fn, key, levelEventCounts);
    const bucketKey = entry.bucketKey;

    if (!buckets[bucketKey]) {
      buckets[bucketKey] = [];
    }
    buckets[bucketKey].push(entry);

    if (entry.hasLogs) {
      emitterCount += 1;
      updateModuleSummary(moduleSummaries, entry);
    }
  });

  const lines = ["graph TD"];
  lines.push(`  ${centerId}["${escapeMermaidLabel(centerLabel)}"]`);

  BUCKET_CONFIGS.forEach((config) => {
    const entries = buckets[config.key] ?? [];
    const nodeId = sanitizeMermaidId(`logging_bucket_${config.key}`);
    const count = entries.length;

    const formattedEntries = entries
      .slice(0, bucketLimit)
      .map((entry) => formatFunctionEntry(entry));

    const labelLines = buildBucketLabel(config.title, count, formattedEntries, bucketLimit);
    lines.push(`  ${nodeId}["${escapeMermaidLabel(labelLines.join("\\n"))}"]`);
    lines.push(`  ${centerId} --> ${nodeId}`);
    lines.push(`  classDef ${config.className} fill:${config.fill},stroke:${config.stroke},color:${config.color};`);
    lines.push(`  class ${nodeId} ${config.className};`);
  });

  const stats = buildStatsSnapshot({
    buckets,
    emitterCount,
    levelEventCounts,
    moduleSummaries,
    moduleAggregateLimit,
  });

  const statusMessage = options.statusMessageFormatter
    ? options.statusMessageFormatter(stats)
    : formatDefaultStatus(stats);

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    stats,
  };
}

function buildFunctionLoggingEntry(fn, fallbackId, levelEventCounts) {
  const loggingCalls = normalizeLoggingCalls(fn?.loggingCalls ?? fn?.logging_calls);
  const levelCounts = new Map();
  const lineNumbers = new Set();
  const loggerNames = new Set();

  loggingCalls.forEach((call) => {
    const canonicalLevel = call.level ?? "unknown";
    levelCounts.set(canonicalLevel, (levelCounts.get(canonicalLevel) ?? 0) + 1);
    if (Number.isFinite(call.lineno)) {
      lineNumbers.add(call.lineno);
    }
    if (call.logger) {
      loggerNames.add(call.logger);
    }
    if (levelEventCounts[canonicalLevel] !== undefined) {
      levelEventCounts[canonicalLevel] += 1;
    } else {
      levelEventCounts.unknown += 1;
    }
  });

  const hasLogs = loggingCalls.length > 0;
  const bucketKey = hasLogs ? determineBucketKey(levelCounts) : "silent";
  const severity = LEVEL_SEVERITY[bucketKey] ?? LEVEL_SEVERITY.unknown;

  return {
    id: typeof fn?.id === "string" ? fn.id : fallbackId ?? null,
    name: extractFunctionName(fn, fallbackId),
    moduleId: fn?.moduleId ?? fn?.module_id ?? null,
    callCount: loggingCalls.length,
    levelCounts: mapToObject(levelCounts),
    levelSummary: formatLevelSummary(levelCounts),
    bucketKey,
    severity,
    hasLogs,
    lineNumbers: Array.from(lineNumbers),
    loggerNames: Array.from(loggerNames),
  };
}

function updateModuleSummary(moduleSummaries, entry) {
  if (!entry || !entry.moduleId) {
    return;
  }
  let summary = moduleSummaries.get(entry.moduleId);
  if (!summary) {
    summary = {
      moduleId: entry.moduleId,
      callCount: 0,
      emitters: new Set(),
      levelCounts: createLevelEventCounter(),
      highestLevel: null,
    };
    moduleSummaries.set(entry.moduleId, summary);
  }
  summary.callCount += entry.callCount;
  summary.emitters.add(entry.id ?? entry.name ?? "anonymous");
  summary.highestLevel = resolveHigherSeverity(summary.highestLevel, entry.bucketKey);
  Object.keys(entry.levelCounts).forEach((key) => {
    if (summary.levelCounts[key] === undefined) {
      summary.levelCounts[key] = 0;
    }
    summary.levelCounts[key] += entry.levelCounts[key];
  });
}

function buildStatsSnapshot(payload) {
  const bucketCounts = BUCKET_CONFIGS.reduce((acc, config) => {
    acc[config.key] = (payload.buckets[config.key] ?? []).length;
    return acc;
  }, {});

  const moduleAggregates = finalizeModuleAggregates(payload.moduleSummaries, payload.moduleAggregateLimit);

  return {
    emitters: payload.emitterCount,
    silent: bucketCounts.silent ?? 0,
    bucketCounts,
    events: { ...payload.levelEventCounts },
    topModules: moduleAggregates,
  };
}

function resolveHigherSeverity(previous, incoming) {
  if (!incoming) {
    return previous ?? null;
  }
  if (!previous) {
    return incoming;
  }
  const current = LEVEL_SEVERITY[previous] ?? LEVEL_SEVERITY.unknown;
  const next = LEVEL_SEVERITY[incoming] ?? LEVEL_SEVERITY.unknown;
  return next > current ? incoming : previous;
}

function determineBucketKey(levelCounts) {
  let selected = "unknown";
  let selectedSeverity = LEVEL_SEVERITY.unknown;
  CANONICAL_LEVEL_ORDER.forEach((level) => {
    const count = levelCounts.get(level) ?? 0;
    if (count > 0) {
      const severity = LEVEL_SEVERITY[level] ?? LEVEL_SEVERITY.unknown;
      if (severity > selectedSeverity) {
        selected = level;
        selectedSeverity = severity;
      }
    }
  });
  return selected;
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

function formatFunctionEntry(entry) {
  const overlays = [];
  if (entry.hasLogs) {
    overlays.push(`Logs: ${entry.callCount}`);
    if (entry.levelSummary) {
      overlays.push(entry.levelSummary);
    }
    const linesOverlay = formatLineOverlay(entry.lineNumbers);
    if (linesOverlay) {
      overlays.push(linesOverlay);
    }
    const loggerOverlay = formatLoggerOverlay(entry.loggerNames);
    if (loggerOverlay) {
      overlays.push(loggerOverlay);
    }
  } else {
    overlays.push("No logs recorded");
  }

  const overlaySuffix = overlays.length > 0 ? ` (${overlays.join(" · ")})` : "";
  const moduleSuffix = entry.moduleId ? ` · ${entry.moduleId}` : "";
  return `${entry.name}${overlaySuffix}${moduleSuffix}`;
}

function formatLevelSummary(levelCounts) {
  if (!(levelCounts instanceof Map) || levelCounts.size === 0) {
    return "";
  }
  const parts = [];
  CANONICAL_LEVEL_ORDER.forEach((level) => {
    const count = levelCounts.get(level) ?? 0;
    if (count > 0) {
      parts.push(`${level.toUpperCase()}×${count}`);
    }
  });
  return parts.length > 0 ? `Levels: ${parts.join(", ")}` : "";
}

function formatLineOverlay(lineNumbers) {
  if (!Array.isArray(lineNumbers) || lineNumbers.length === 0) {
    return "";
  }
  const normalized = Array.from(new Set(lineNumbers.filter((value) => Number.isFinite(value)))).sort((a, b) => a - b);
  if (normalized.length === 0) {
    return "";
  }
  const sample = normalized.slice(0, 3);
  let label = sample.join(", ");
  if (normalized.length > sample.length) {
    label += ` (+${normalized.length - sample.length} more)`;
  }
  return `Lines: ${label}`;
}

function formatLoggerOverlay(loggers) {
  if (!Array.isArray(loggers) || loggers.length === 0) {
    return "";
  }
  const normalized = Array.from(new Set(loggers.filter((value) => typeof value === "string" && value.trim().length > 0)));
  if (normalized.length === 0) {
    return "";
  }
  const sample = normalized.slice(0, 2);
  let label = sample.join(", ");
  if (normalized.length > sample.length) {
    label += ", ...";
  }
  const prefix = normalized.length === 1 ? "Logger" : "Loggers";
  return `${prefix}: ${label}`;
}

function formatDefaultStatus(stats) {
  const emitters = Number.isFinite(stats?.emitters) ? stats.emitters : 0;
  const silent = Number.isFinite(stats?.silent) ? stats.silent : 0;
  const events = stats?.events ?? {};
  const levelParts = CANONICAL_LEVEL_ORDER.map((level) => `${level} ${Number.isFinite(events[level]) ? events[level] : 0}`);
  const topModule = Array.isArray(stats?.topModules) && stats.topModules.length > 0 ? stats.topModules[0] : null;
  const moduleSuffix = topModule ? `; top module ${topModule.moduleId} (${topModule.callCount} calls)` : "";
  return `Rendered Logging Flow (emitters ${emitters}, silent ${silent}, events ${levelParts.join(", ")}${moduleSuffix}).`;
}

function finalizeModuleAggregates(moduleSummaries, limit) {
  if (!(moduleSummaries instanceof Map) || moduleSummaries.size === 0) {
    return [];
  }
  const aggregates = Array.from(moduleSummaries.values())
    .filter((summary) => summary.callCount > 0)
    .map((summary) => ({
      moduleId: summary.moduleId,
      callCount: summary.callCount,
      emitters: summary.emitters.size,
      highestLevel: summary.highestLevel ?? null,
      levelCounts: { ...summary.levelCounts },
    }))
    .sort((a, b) => {
      if (b.callCount !== a.callCount) {
        return b.callCount - a.callCount;
      }
      const severityDelta = (LEVEL_SEVERITY[b.highestLevel ?? "unknown"] ?? 0) - (LEVEL_SEVERITY[a.highestLevel ?? "unknown"] ?? 0);
      if (severityDelta !== 0) {
        return severityDelta;
      }
      return a.moduleId.localeCompare(b.moduleId);
    });

  if (!Number.isFinite(Number(limit)) || limit <= 0) {
    return aggregates;
  }
  return aggregates.slice(0, Math.floor(Number(limit)));
}

function normalizeLoggingCalls(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((call) => {
      if (!call || typeof call !== "object") {
        return null;
      }
      const rawLevel = call.level ?? call.log_level ?? call.levelname ?? call.severity ?? null;
      const level = normalizeLogLevel(rawLevel);
      const linenoRaw = call.lineno ?? call.line ?? call.line_number ?? null;
      const lineno = Number.isFinite(Number(linenoRaw)) ? Number(linenoRaw) : null;
      const message = typeof call.message === "string" && call.message.trim().length > 0 ? call.message.trim() : null;
      const logger = typeof call.logger === "string" && call.logger.trim().length > 0 ? call.logger.trim() : null;
      return {
        level: level ?? "unknown",
        lineno,
        message,
        logger,
      };
    })
    .filter(Boolean);
}

function normalizeLogLevel(value) {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    if (value >= 50) {
      return "critical";
    }
    if (value >= 40) {
      return "error";
    }
    if (value >= 30) {
      return "warning";
    }
    if (value >= 20) {
      return "info";
    }
    if (value >= 10) {
      return "debug";
    }
    return "unknown";
  }
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim().toLowerCase();
  if (!normalized) {
    return null;
  }
  return LEVEL_ALIASES[normalized] ?? null;
}

function createLevelEventCounter() {
  const counters = {};
  CANONICAL_LEVEL_ORDER.forEach((level) => {
    counters[level] = 0;
  });
  return counters;
}

function createBucketRegistry() {
  return BUCKET_CONFIGS.reduce((acc, config) => {
    acc[config.key] = [];
    return acc;
  }, {});
}

function resolveBucketLimit(value) {
  if (!Number.isFinite(Number(value))) {
    return DEFAULT_BUCKET_LIMIT;
  }
  const numeric = Math.floor(Number(value));
  return numeric >= 0 ? numeric : DEFAULT_BUCKET_LIMIT;
}

function resolveAggregateLimit(value) {
  if (!Number.isFinite(Number(value))) {
    return DEFAULT_MODULE_AGGREGATE_LIMIT;
  }
  const numeric = Math.floor(Number(value));
  return numeric > 0 ? numeric : DEFAULT_MODULE_AGGREGATE_LIMIT;
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

function mapToObject(map) {
  const result = {};
  if (!(map instanceof Map)) {
    return result;
  }
  map.forEach((value, key) => {
    result[key] = value;
  });
  return result;
}

export const __test__ = {
  buildFunctionLoggingEntry,
  buildStatsSnapshot,
  determineBucketKey,
  finalizeModuleAggregates,
  formatFunctionEntry,
  formatLevelSummary,
  formatLineOverlay,
  normalizeLogLevel,
  normalizeLoggingCalls,
  resolveAggregateLimit,
  resolveBucketLimit,
  sanitizeMermaidId,
  escapeMermaidLabel,
  createLevelEventCounter,
  createBucketRegistry,
};
