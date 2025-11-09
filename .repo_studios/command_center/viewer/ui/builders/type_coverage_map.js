const DEFAULT_VIEW_LABEL = "Quality Metrics · Type Coverage Map";
const DEFAULT_CENTER_LABEL = "Type Coverage Map";
const DEFAULT_BUCKET_LIMIT = 8;

const BUCKET_CONFIGS = Object.freeze([
  { key: "strong", title: "Strong >= 80%", className: "typeStrong", fill: "#166534", stroke: "#22c55e", color: "#ecfdf5" },
  { key: "moderate", title: "Moderate 50-79%", className: "typeModerate", fill: "#1f2937", stroke: "#60a5fa", color: "#e0f2fe" },
  { key: "weak", title: "Weak < 50%", className: "typeWeak", fill: "#7f1d1d", stroke: "#f87171", color: "#fee2e2" },
  { key: "unknown", title: "Unknown", className: "typeUnknown", fill: "#4b5563", stroke: "#cbd5f5", color: "#f1f5f9" },
]);

export function buildTypeCoverageMapDiagram(functions, options = {}) {
  const functionsMap = toMap(functions);
  if (!functionsMap || functionsMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "No functions recorded in this CommandView artifact.",
    };
  }

  const bucketLimit = resolveBucketLimit(options.bucketLimit);
  const centerLabel = typeof options.centerLabel === "string" && options.centerLabel.trim().length > 0
    ? options.centerLabel.trim()
    : DEFAULT_CENTER_LABEL;
  const centerId = sanitizeMermaidId(options.centerId ?? "type_coverage_center");

  const buckets = {
    strong: [],
    moderate: [],
    weak: [],
    unknown: [],
  };

  functionsMap.forEach((fn, key) => {
    const coverageValue = extractCoverage(fn);
    const entry = {
      id: key ?? null,
      name: extractFunctionName(fn, key),
      moduleId: fn?.moduleId ?? null,
      coverage: coverageValue,
    };

    if (!Number.isFinite(coverageValue)) {
      buckets.unknown.push(entry);
    } else if (coverageValue >= 0.8) {
      buckets.strong.push(entry);
    } else if (coverageValue >= 0.5) {
      buckets.moderate.push(entry);
    } else {
      buckets.weak.push(entry);
    }
  });

  const lines = ["graph TD"];
  lines.push(`  ${centerId}["${escapeMermaidLabel(centerLabel)}"]`);

  BUCKET_CONFIGS.forEach((config) => {
    const entries = buckets[config.key] ?? [];
    const nodeId = sanitizeMermaidId(`type_bucket_${config.key}`);
    const count = entries.length;

    const formattedEntries = entries
      .slice(0, bucketLimit)
      .map((entry) => {
        const coverageText = Number.isFinite(entry.coverage) ? formatCoveragePercent(entry.coverage) : "-";
        const moduleSuffix = entry.moduleId ? ` · ${entry.moduleId}` : "";
        return `${entry.name} (${coverageText})${moduleSuffix}`;
      });

  const labelLines = buildBucketLabel(config.title, count, formattedEntries, bucketLimit);
    lines.push(`  ${nodeId}["${escapeMermaidLabel(labelLines.join("\\n"))}"]`);
    lines.push(`  ${centerId} --> ${nodeId}`);
    lines.push(`  classDef ${config.className} fill:${config.fill},stroke:${config.stroke},color:${config.color};`);
    lines.push(`  class ${nodeId} ${config.className};`);
  });

  const resultLabel = options.viewLabel ?? DEFAULT_VIEW_LABEL;
  const stats = {
    strong: buckets.strong.length,
    moderate: buckets.moderate.length,
    weak: buckets.weak.length,
    unknown: buckets.unknown.length,
  };

  const statusMessage = options.statusMessageFormatter
    ? options.statusMessageFormatter(stats)
    : `Rendered Type Coverage Map (strong ${stats.strong}, moderate ${stats.moderate}, weak ${stats.weak}, unknown ${stats.unknown}).`;

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

function extractCoverage(fn) {
  if (!fn || typeof fn !== "object") {
    return Number.NaN;
  }
  const direct = fn.typeHintCoverage ?? fn.annotationCoverage ?? fn.coverage;
  const metricCoverage = fn.metrics?.coverage;
  const value = direct ?? metricCoverage;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : Number.NaN;
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
  buildBucketLabel,
  extractCoverage,
  extractFunctionName,
  resolveBucketLimit,
  toMap,
  sanitizeMermaidId,
  escapeMermaidLabel,
  formatCoveragePercent,
};
