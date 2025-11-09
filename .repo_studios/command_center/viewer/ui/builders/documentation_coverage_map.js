const DEFAULT_VIEW_LABEL = "Quality Metrics · Documentation Coverage Map";
const DEFAULT_CENTER_LABEL = "Documentation Coverage Map";
const DEFAULT_BUCKET_LIMIT = 8;

const BUCKET_CONFIGS = Object.freeze([
  { key: "documented", title: "Documented", className: "docDocumented", fill: "#166534", stroke: "#22c55e", color: "#ecfdf5" },
  { key: "missing", title: "Missing", className: "docMissing", fill: "#7f1d1d", stroke: "#f87171", color: "#fee2e2" },
  { key: "unknown", title: "Unknown", className: "docUnknown", fill: "#4b5563", stroke: "#cbd5f5", color: "#f1f5f9" },
]);

export function buildDocumentationCoverageMapDiagram(functions, options = {}) {
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
  const centerId = sanitizeMermaidId(options.centerId ?? "documentation_coverage_center");

  const buckets = {
    documented: [],
    missing: [],
    unknown: [],
  };

  functionsMap.forEach((fn, key) => {
    const docQuality = extractDocstringQuality(fn);
    const entry = {
      id: key ?? null,
      name: extractFunctionName(fn, key),
      moduleId: fn?.moduleId ?? null,
      docStatus: docQuality.status,
    };

    if (docQuality.state === "documented") {
      buckets.documented.push(entry);
    } else if (docQuality.state === "missing") {
      buckets.missing.push(entry);
    } else {
      buckets.unknown.push(entry);
    }
  });

  const lines = ["graph TD"];
  lines.push(`  ${centerId}["${escapeMermaidLabel(centerLabel)}"]`);

  BUCKET_CONFIGS.forEach((config) => {
    const entries = buckets[config.key] ?? [];
    const nodeId = sanitizeMermaidId(`documentation_bucket_${config.key}`);
    const count = entries.length;

    const formattedEntries = entries
      .slice(0, bucketLimit)
      .map((entry) => {
        const statusSuffix = entry.docStatus ? ` · ${entry.docStatus}` : "";
        const moduleSuffix = entry.moduleId ? ` · ${entry.moduleId}` : "";
        return `${entry.name}${statusSuffix}${moduleSuffix}`;
      });

    const labelLines = buildBucketLabel(config.title, count, formattedEntries, bucketLimit);
    lines.push(`  ${nodeId}["${escapeMermaidLabel(labelLines.join("\\n"))}"]`);
    lines.push(`  ${centerId} --> ${nodeId}`);
    lines.push(`  classDef ${config.className} fill:${config.fill},stroke:${config.stroke},color:${config.color};`);
    lines.push(`  class ${nodeId} ${config.className};`);
  });

  const resultLabel = options.viewLabel ?? DEFAULT_VIEW_LABEL;
  const stats = {
    documented: buckets.documented.length,
    missing: buckets.missing.length,
    unknown: buckets.unknown.length,
  };

  const statusMessage = options.statusMessageFormatter
    ? options.statusMessageFormatter(stats)
    : `Rendered Documentation Coverage Map (documented ${stats.documented}, missing ${stats.missing}, unknown ${stats.unknown}).`;

  return {
    definition: lines.join("\n"),
    label: resultLabel,
    statusMessage,
    stats,
  };
}

function extractDocstringQuality(fn) {
  if (!fn || typeof fn !== "object") {
    return { state: "unknown", status: null };
  }
  const doc = fn.docstringQuality ?? fn.docstring_quality ?? null;
  if (!doc || typeof doc !== "object") {
    return { state: "unknown", status: null };
  }
  if (doc.exists === true) {
    return { state: "documented", status: doc.status ?? "present" };
  }
  if (doc.exists === false) {
    return { state: "missing", status: doc.status ?? "missing" };
  }
  if (typeof doc.status === "string" && doc.status.trim().length > 0) {
    const normalized = doc.status.trim().toLowerCase();
    if (normalized === "present" || normalized === "exists") {
      return { state: "documented", status: doc.status };
    }
    if (normalized === "missing" || normalized === "absent") {
      return { state: "missing", status: doc.status };
    }
    return { state: "unknown", status: doc.status };
  }
  return { state: "unknown", status: null };
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

export const __test__ = {
  buildBucketLabel,
  extractDocstringQuality,
  extractFunctionName,
  resolveBucketLimit,
  toMap,
  sanitizeMermaidId,
  escapeMermaidLabel,
};
