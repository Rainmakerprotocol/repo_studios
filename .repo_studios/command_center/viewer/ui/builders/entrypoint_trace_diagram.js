const DEFAULT_VIEW_LABEL = "Code Flow · Entrypoint Trace";
const DEFAULT_MAX_DEPTH = 2;
const DEFAULT_MAX_TOTAL_NODES = 120;

const NODE_STYLE_PALETTE = Object.freeze({
  entrypoint: Object.freeze({ fill: "#0f172a", stroke: "#38bdf8" }),
  downstream: Object.freeze({ fill: "#1f2937", stroke: "#f97316" }),
  external: Object.freeze({ fill: "#111827", stroke: "#a855f7" }),
});

const REASON_DESCRIPTIONS = Object.freeze({
  "main-guard-name-match": "Main guard name match",
  "cli-parser-name-match": "CLI parser name match",
  "main-guard-isolated-call": "Main guard without inbound callers",
  "cli-parser-isolated-call": "CLI parser without inbound callers",
});

export function buildEntrypointTraceDiagram(modules, functions, callGraph, entrypoints, options = {}) {
  const moduleMap = toMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "Module metadata has not been normalized for this CommandView artifact.",
    };
  }

  const functionMap = toMap(functions);
  if (!functionMap || functionMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "Function metadata has not been normalized for this CommandView artifact.",
    };
  }

  const callGraphMap = toMapOfArrays(callGraph);
  if (!callGraphMap || callGraphMap.size === 0) {
    return {
      message: options.missingCallGraphMessage ?? "Call graph data is not available in this CommandView artifact.",
    };
  }

  const entrypointMap = toMap(entrypoints);
  if (!entrypointMap || entrypointMap.size === 0) {
    return {
      message: options.missingEntrypointsMessage ?? "Entrypoint candidates were not detected in this CommandView artifact.",
    };
  }

  const moduleFilter = buildModuleFilter(options.moduleIds);
  const scoped = collectScopedCandidates(entrypointMap, moduleFilter);
  if (scoped.totalCandidates === 0) {
    return {
      message: options.emptyMessage ?? "No entrypoint candidates matched the current scope.",
    };
  }

  const scopeLabel = options.scopeDescription ?? "repository";
  const maxDepth = resolveNumericOption(options.maxDepth, DEFAULT_MAX_DEPTH, 0);
  const maxNodes = resolveNumericOption(options.maxNodes, DEFAULT_MAX_TOTAL_NODES, scoped.totalCandidates);

  const nodeIdMap = new Map();
  const nodeDetails = new Map();
  const orderedNodes = [];
  mermaidIdCounter = 0;
  const lines = ["graph TD"];
  appendClassDefinitions(lines);

  const edgeSet = new Set();
  const edgeLines = [];
  let truncated = false;

  const ensureNode = (functionId, kind, context) => {
    if (!functionId || typeof functionId !== "string") {
      return null;
    }

    const existingId = nodeIdMap.get(functionId);
    if (existingId) {
      const detail = nodeDetails.get(existingId);
      if (detail && kind) {
        addNodeClass(detail, kind, context);
      }
      return existingId;
    }

    const record = functionMap.get(functionId);
    if (!record || typeof record !== "object") {
      return null;
    }

    if (nodeIdMap.size >= maxNodes) {
      truncated = true;
      return null;
    }

    const sanitizedId = sanitizeMermaidId(functionId);
    const detail = createNodeDetail(record, kind, context);
    nodeIdMap.set(functionId, sanitizedId);
    nodeDetails.set(sanitizedId, detail);
    orderedNodes.push({ id: sanitizedId, detail });
    return sanitizedId;
  };

  const moduleEntries = Array.from(scoped.modules.entries()).sort(([leftId], [rightId]) =>
    leftId.localeCompare(rightId)
  );

  moduleEntries.forEach(([moduleId, moduleInfo]) => {
    const candidates = moduleInfo.candidates;
    if (!Array.isArray(candidates)) {
      return;
    }

    candidates.forEach((candidate) => {
      if (!candidate || typeof candidate !== "object" || !candidate.id) {
        return;
      }

      const entryNodeId = ensureNode(candidate.id, "entrypoint", { candidate });
      if (!entryNodeId) {
        return;
      }

      const queue = [{ id: candidate.id, depth: 0 }];
      const visited = new Set([candidate.id]);

      while (queue.length > 0) {
        const current = queue.shift();
        if (!current) {
          continue;
        }
        const sourceId = current.id;
        const depth = current.depth;
        const sanitizedSource = nodeIdMap.get(sourceId);
        if (!sanitizedSource) {
          continue;
        }

        const targets = callGraphMap.get(sourceId) ?? [];
        targets.forEach((targetId) => {
          if (!targetId || visited.has(targetId)) {
            return;
          }
          const targetRecord = functionMap.get(targetId);
          if (!targetRecord) {
            return;
          }

          const sanitizedTarget = ensureNode(targetId, "downstream", { entryModuleId: moduleId });
          if (!sanitizedTarget) {
            return;
          }

          visited.add(targetId);
          const edgeKey = `${sanitizedSource}->${sanitizedTarget}`;
          if (!edgeSet.has(edgeKey)) {
            edgeSet.add(edgeKey);
            edgeLines.push({ source: sanitizedSource, target: sanitizedTarget });
          }

          const nextDepth = depth + 1;
          if (nextDepth <= maxDepth) {
            queue.push({ id: targetId, depth: nextDepth });
          }
        });
      }
    });
  });

  orderedNodes.forEach(({ id, detail }) => {
    lines.push(`  ${id}["${escapeMermaidLabel(detail.label)}"]`);
  });

  orderedNodes.forEach(({ id, detail }) => {
    if (detail.classes.length > 0) {
      lines.push(`  class ${id} ${detail.classes.join(",")};`);
    }
  });

  edgeLines
    .sort((left, right) => {
      if (left.source !== right.source) {
        return left.source.localeCompare(right.source);
      }
      return left.target.localeCompare(right.target);
    })
    .forEach((edge) => {
      lines.push(`  ${edge.source} --> ${edge.target}`);
    });

  const entrypointCount = scoped.totalCandidates;
  const downstreamCount = orderedNodes.filter(({ detail }) => detail.classes.includes("downstream")).length;
  const statusMessage = buildStatusMessage(scopeLabel, entrypointCount, downstreamCount, options.fallbackNotice);

  const statusDetails = buildStatusDetails(scoped.modules, options.fallbackNotice, truncated, maxDepth, maxNodes);

  const stats = {
    scope: scopeLabel,
    entrypoints: entrypointCount,
    downstreamFunctions: downstreamCount,
    edgeCount: edgeLines.length,
    moduleCount: scoped.modules.size,
    maxDepth,
    nodeCount: orderedNodes.length,
    truncated,
  };

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    statusDetails,
    stats,
  };
}

function buildStatusMessage(scopeLabel, entrypointCount, downstreamCount, fallbackNotice) {
  const entrypointText = `${entrypointCount} entrypoint${entrypointCount === 1 ? "" : "s"}`;
  const downstreamText = `${downstreamCount} downstream function${downstreamCount === 1 ? "" : "s"}`;
  const base = `Rendered Entrypoint Trace for ${scopeLabel} (${entrypointText}, ${downstreamText}).`;
  if (fallbackNotice) {
    return `${base} ${fallbackNotice}`.trim();
  }
  return base;
}

function buildStatusDetails(modules, fallbackNotice, truncated, maxDepth, maxNodes) {
  const items = [];
  modules.forEach((moduleInfo, moduleId) => {
    const candidates = Array.isArray(moduleInfo.candidates) ? moduleInfo.candidates : [];
    candidates.forEach((candidate) => {
      if (!candidate || typeof candidate !== "object") {
        return;
      }
      const label = `${moduleId} :: ${candidate.name ?? candidate.id}`;
      const reason = formatReason(candidate.reason);
      const outbound = Number.isFinite(Number(candidate.outboundCount)) ? Number(candidate.outboundCount) : 0;
      const inbound = Number.isFinite(Number(candidate.inboundCount)) ? Number(candidate.inboundCount) : 0;
      const details = [`Reason: ${reason}`, `Outbound: ${outbound}`, `Inbound: ${inbound}`];
      items.push({ label, value: details.join(" · ") });
    });
  });

  items.sort((left, right) => {
    if (left.label !== right.label) {
      return left.label.localeCompare(right.label);
    }
    return left.value.localeCompare(right.value);
  });

  const details = [
    {
      type: "list",
      title: "Entrypoint Candidates",
      description: "Reason codes derive from main-guard and CLI parser heuristics.",
      items,
    },
  ];

  if (fallbackNotice) {
    details.unshift({
      type: "info",
      title: "Scope fallback applied",
      description: fallbackNotice,
    });
  }

  if (truncated) {
    details.push({
      type: "warning",
      title: "Trace truncated",
      description: `Trace limited to depth ${maxDepth} and ${maxNodes} nodes to maintain readability.`,
    });
  }

  return details;
}

function formatReason(reason) {
  if (!reason || typeof reason !== "string") {
    return "Heuristic match";
  }
  return REASON_DESCRIPTIONS[reason] ?? reason.replace(/[-_]/g, " ");
}

function createNodeDetail(record, kind, context) {
  if (kind === "entrypoint") {
    const candidate = context?.candidate ?? null;
    const reason = candidate ? formatReason(candidate.reason) : "Entrypoint";
    const outbound = Number.isFinite(Number(candidate?.outboundCount)) ? Number(candidate.outboundCount) : 0;
    const inbound = Number.isFinite(Number(candidate?.inboundCount)) ? Number(candidate.inboundCount) : 0;
    const lines = [record.moduleId ?? record.id ?? "module", record.name ?? record.id ?? "entrypoint", reason];
    lines.push(`Outbound: ${outbound}`);
    lines.push(`Inbound: ${inbound}`);
    return {
      classes: ["entrypoint"],
      label: lines.join("\n"),
      moduleId: record.moduleId ?? null,
    };
  }

  const entryModuleId = context?.entryModuleId ?? null;
  const isExternal = Boolean(entryModuleId && record.moduleId && record.moduleId !== entryModuleId);
  const lines = [record.name ?? record.id ?? "function"];
  if (record.moduleId) {
    lines.push(record.moduleId);
  }
  if (record.metrics && Number.isFinite(Number(record.metrics?.coverage))) {
    const coverage = Number(record.metrics.coverage);
    lines.push(`Coverage: ${formatCoveragePercent(coverage)}`);
  }
  if (record.metrics && Number.isFinite(Number(record.metrics?.cyclomaticComplexity))) {
    const complexity = Number(record.metrics.cyclomaticComplexity);
    lines.push(`Complexity: ${complexity}`);
  }
  return {
    classes: isExternal ? ["downstream", "external"] : ["downstream"],
    label: lines.join("\n"),
    moduleId: record.moduleId ?? null,
  };
}

function addNodeClass(detail, kind, context) {
  if (!detail || !Array.isArray(detail.classes)) {
    return;
  }
  if (kind === "downstream") {
    const entryModuleId = context?.entryModuleId ?? null;
    const nodeModuleId = detail.moduleId ?? null;
    const isExternal = Boolean(entryModuleId && nodeModuleId && entryModuleId !== nodeModuleId);
    if (!detail.classes.includes("downstream")) {
      detail.classes.push("downstream");
    }
    if (isExternal) {
      if (!detail.classes.includes("external")) {
        detail.classes.push("external");
      }
    }
    return;
  }
  if (!detail.classes.includes(kind)) {
    detail.classes.push(kind);
  }
}

function collectScopedCandidates(entrypointMap, moduleFilter) {
  const modules = new Map();
  let totalCandidates = 0;

  entrypointMap.forEach((value, moduleId) => {
    if (moduleFilter && !moduleFilter.has(moduleId)) {
      return;
    }
    const candidates = Array.isArray(value?.candidates) ? value.candidates.filter((candidate) => candidate?.id) : [];
    if (candidates.length === 0) {
      return;
    }
    modules.set(moduleId, {
      moduleId: value?.moduleId ?? moduleId,
      candidates: candidates.slice(),
    });
    totalCandidates += candidates.length;
  });

  return { modules, totalCandidates };
}

function buildModuleFilter(candidate) {
  if (!candidate) {
    return null;
  }
  if (candidate instanceof Set) {
    return candidate;
  }
  if (Array.isArray(candidate)) {
    return new Set(candidate);
  }
  return null;
}

function appendClassDefinitions(lines) {
  lines.push(
    `  classDef entrypoint fill:${NODE_STYLE_PALETTE.entrypoint.fill},stroke:${NODE_STYLE_PALETTE.entrypoint.stroke},color:#f8fafc;`
  );
  lines.push(
    `  classDef downstream fill:${NODE_STYLE_PALETTE.downstream.fill},stroke:${NODE_STYLE_PALETTE.downstream.stroke},color:#f8fafc;`
  );
  lines.push(
    `  classDef external fill:${NODE_STYLE_PALETTE.external.fill},stroke:${NODE_STYLE_PALETTE.external.stroke},color:#f8fafc;`
  );
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

function resolveNumericOption(candidate, defaultValue, minimum) {
  if (!Number.isFinite(Number(candidate))) {
    return defaultValue;
  }
  const numeric = Number(candidate);
  if (minimum !== undefined && numeric < minimum) {
    return minimum;
  }
  return numeric;
}

export const __test__ = {
  toMap,
  toMapOfArrays,
  sanitizeMermaidId,
  escapeMermaidLabel,
  formatCoveragePercent,
  formatReason,
  collectScopedCandidates,
};
