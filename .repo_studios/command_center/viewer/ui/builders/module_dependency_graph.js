const DEFAULT_VIEW_LABEL = "Dependency · Module Dependency Graph";
const DEFAULT_COUPLING_LIMIT = 5;
const DEFAULT_IMPORTER_LIMIT = 5;

const NODE_STYLE = Object.freeze({
  base: { fill: "#0f172a", stroke: "#38bdf8", color: "#f8fafc" },
  caution: { fill: "#1f2937", stroke: "#facc15", color: "#f8fafc" },
  alert: { fill: "#7f1d1d", stroke: "#f87171", color: "#fee2e2" },
  orphan: { fill: "#111827", stroke: "#94a3b8", color: "#e2e8f0" },
});

const DEPENDENCY_THRESHOLDS = Object.freeze({
  cautionStatements: 8,
  alertStatements: 16,
  cautionUnused: 1,
  alertUnused: 3,
});

export function buildModuleDependencyGraphDiagram(modules, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const { edges, statsByModule, unusedEdgeCount } = collectDependencyData(moduleMap);

  const nodeEntries = Array.from(moduleMap.entries())
    .map(([moduleId, moduleRecord]) => {
      const stats = statsByModule.get(moduleId) ?? createEmptyModuleStats(moduleId, moduleRecord);
      return { moduleId, record: moduleRecord, stats };
    })
    .sort((left, right) => left.moduleId.localeCompare(right.moduleId));

  const orphans = nodeEntries
    .filter((entry) => entry.stats.outgoingEdges + entry.stats.incomingEdges === 0)
    .map((entry) => entry.moduleId);

  const lines = ["graph LR"];
  lines.push(`  classDef module fill:${NODE_STYLE.base.fill},stroke:${NODE_STYLE.base.stroke},color:${NODE_STYLE.base.color},stroke-width:1.5px;`);
  lines.push(`  classDef moduleCaution fill:${NODE_STYLE.caution.fill},stroke:${NODE_STYLE.caution.stroke},color:${NODE_STYLE.caution.color},stroke-width:2px;`);
  lines.push(`  classDef moduleAlert fill:${NODE_STYLE.alert.fill},stroke:${NODE_STYLE.alert.stroke},color:${NODE_STYLE.alert.color},stroke-width:2.5px;`);
  lines.push(`  classDef moduleOrphan fill:${NODE_STYLE.orphan.fill},stroke:${NODE_STYLE.orphan.stroke},color:${NODE_STYLE.orphan.color},stroke-width:1.5px;`);

  const nodeIds = new Map();
  nodeEntries.forEach((entry) => {
    const sanitizedId = sanitizeMermaidId(entry.moduleId);
    nodeIds.set(entry.moduleId, sanitizedId);
    lines.push(`  ${sanitizedId}["${escapeMermaidLabel(formatModuleLabel(entry.record, entry.stats))}"]`);
    lines.push(`  class ${sanitizedId} ${resolveModuleClass(entry.stats)};`);
  });

  edges.forEach((edge) => {
    const sourceId = nodeIds.get(edge.source);
    const targetId = nodeIds.get(edge.target);
    if (!sourceId || !targetId) {
      return;
    }
    const label = formatEdgeLabel(edge);
    lines.push(`  ${sourceId} -->|${escapeMermaidLabel(label)}| ${targetId}`);
  });

  const moduleCount = moduleMap.size;
  const edgeCount = edges.length;
  const scopeLabel = resolveScopeLabel(options.rootId, options.domainId);

  const stats = buildStatsSnapshot({
    moduleCount,
    edgeCount,
    unusedEdgeCount,
    statsByModule,
    edges,
    orphans,
    dependencySummaries: options.dependencySummaries,
    couplingLimit: options.couplingLimit ?? DEFAULT_COUPLING_LIMIT,
    importerLimit: options.importerLimit ?? DEFAULT_IMPORTER_LIMIT,
  });

  const statusMessage = buildStatusMessage({
    scopeLabel,
    moduleCount,
    edgeCount,
    unusedEdgeCount,
    orphans,
    stats,
  });

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    stats,
    statusDetails: buildStatusDetails(stats),
  };
}

function collectDependencyData(moduleMap) {
  const edges = [];
  const statsByModule = new Map();
  let unusedEdgeCount = 0;

  const ensureStats = (moduleId) => {
    let stats = statsByModule.get(moduleId);
    if (!stats) {
      const record = moduleMap.get(moduleId);
      stats = createEmptyModuleStats(moduleId, record);
      statsByModule.set(moduleId, stats);
    }
    return stats;
  };

  moduleMap.forEach((moduleRecord, moduleId) => {
    const importEdges = Array.isArray(moduleRecord?.importEdges) ? moduleRecord.importEdges : [];
    const aggregated = new Map();

    importEdges.forEach((edge) => {
      if (!edge || typeof edge !== "object") {
        return;
      }
      if ((edge.category ?? "internal") !== "internal") {
        return;
      }
      const target = resolveInternalTarget(edge.target, moduleMap);
      if (!target) {
        ensureStats(moduleId).unresolvedTargets.add(edge.target ?? "");
        return;
      }
      const bucket = aggregated.get(target) ?? { statements: 0, unused: 0, functions: new Set() };
      bucket.statements += 1;
      if (edge.unused) {
        bucket.unused += 1;
      }
      if (Array.isArray(edge.functions)) {
        edge.functions.forEach((fn) => {
          if (typeof fn === "string" && fn.trim().length > 0) {
            bucket.functions.add(fn.trim());
          }
        });
      }
      aggregated.set(target, bucket);
    });

    aggregated.forEach((details, targetId) => {
      const sourceStats = ensureStats(moduleId);
      const targetStats = ensureStats(targetId);

      sourceStats.outgoingEdges += 1;
      sourceStats.outgoingStatements += details.statements;
      sourceStats.outgoingUnused += details.unused;
      sourceStats.targets.add(targetId);
      sourceStats.functionsTouched += details.functions.size;

      targetStats.incomingEdges += 1;
      targetStats.incomingStatements += details.statements;
      targetStats.sources.add(moduleId);

      edges.push({
        source: moduleId,
        target: targetId,
        statements: details.statements,
        unused: details.unused,
        functions: details.functions.size,
      });

      unusedEdgeCount += details.unused;
    });
  });

  moduleMap.forEach((_record, moduleId) => {
    ensureStats(moduleId);
  });

  edges.sort((left, right) => {
    if (left.source === right.source) {
      return left.target.localeCompare(right.target);
    }
    return left.source.localeCompare(right.source);
  });

  return { edges, statsByModule, unusedEdgeCount };
}

function buildStatsSnapshot(payload) {
  const topImporters = computeTopImporters(payload.statsByModule, payload.importerLimit);
  const topCouplings = computeTopCouplings(payload.edges, payload.couplingLimit);
  const externalDependencies = summarizeExternalDependencies(payload.dependencySummaries);

  return {
    modules: payload.moduleCount,
    edges: payload.edgeCount,
    unusedEdges: payload.unusedEdgeCount,
    orphans: payload.orphans,
    topImporters,
    topCouplings,
    externalDependencies,
  };
}

function computeTopImporters(statsByModule, limit) {
  const entries = Array.from(statsByModule.values())
    .filter((entry) => entry.outgoingEdges > 0)
    .map((entry) => ({
      moduleId: entry.moduleId,
      outgoingEdges: entry.outgoingEdges,
      outgoingStatements: entry.outgoingStatements,
      outgoingUnused: entry.outgoingUnused,
      targets: Array.from(entry.targets).sort((a, b) => a.localeCompare(b)),
    }))
    .sort((left, right) => {
      if (right.outgoingStatements !== left.outgoingStatements) {
        return right.outgoingStatements - left.outgoingStatements;
      }
      if (right.outgoingEdges !== left.outgoingEdges) {
        return right.outgoingEdges - left.outgoingEdges;
      }
      return left.moduleId.localeCompare(right.moduleId);
    });

  if (!Number.isFinite(limit) || limit <= 0) {
    return entries;
  }
  return entries.slice(0, Math.max(1, Math.floor(limit)));
}

function computeTopCouplings(edges, limit) {
  const ranked = edges
    .slice()
    .sort((left, right) => {
      if (right.statements !== left.statements) {
        return right.statements - left.statements;
      }
      if (right.functions !== left.functions) {
        return right.functions - left.functions;
      }
      if (right.unused !== left.unused) {
        return right.unused - left.unused;
      }
      if (left.source !== right.source) {
        return left.source.localeCompare(right.source);
      }
      return left.target.localeCompare(right.target);
    });

  if (!Number.isFinite(limit) || limit <= 0) {
    return ranked;
  }
  return ranked.slice(0, Math.max(1, Math.floor(limit)));
}

function summarizeExternalDependencies(dependencySummaries) {
  if (!(dependencySummaries instanceof Map) || dependencySummaries.size === 0) {
    return [];
  }

  const tallies = new Map();
  dependencySummaries.forEach((summary) => {
    if (!summary || typeof summary !== "object") {
      return;
    }
    Object.entries(summary).forEach(([category, payload]) => {
      if (category === "internal") {
        return;
      }
      const count = resolveSummaryCount(payload);
      if (count <= 0) {
        return;
      }
      tallies.set(category, (tallies.get(category) ?? 0) + count);
    });
  });

  return Array.from(tallies.entries())
    .map(([category, count]) => ({ category, count }))
    .sort((left, right) => {
      if (right.count !== left.count) {
        return right.count - left.count;
      }
      return left.category.localeCompare(right.category);
    });
}

function resolveSummaryCount(entry) {
  if (!entry || typeof entry !== "object") {
    return 0;
  }
  if (Number.isFinite(entry.count)) {
    return Number(entry.count);
  }
  if (Array.isArray(entry.modules)) {
    return entry.modules.length;
  }
  return 0;
}

function buildStatusMessage(payload) {
  const suffixParts = [];
  if (payload.unusedEdgeCount > 0) {
    suffixParts.push(`${payload.unusedEdgeCount} unused import${payload.unusedEdgeCount === 1 ? "" : "s"}`);
  }
  if (Array.isArray(payload.stats.topImporters) && payload.stats.topImporters.length > 0) {
    const top = payload.stats.topImporters[0];
    suffixParts.push(`top importer ${top.moduleId} (${top.outgoingStatements} statements)`);
  }
  if (payload.orphans.length > 0) {
    const sample = payload.orphans.slice(0, 3).join(", ");
    const overflow = payload.orphans.length > 3 ? ` (+${payload.orphans.length - 3})` : "";
    suffixParts.push(`orphans ${sample}${overflow}`);
  }
  const suffix = suffixParts.length > 0 ? `; ${suffixParts.join("; ")}` : "";
  return `Rendered Module Dependency Graph for ${payload.scopeLabel} (${payload.moduleCount} modules, ${payload.edgeCount} edges${suffix}).`;
}

function buildStatusDetails(stats) {
  const descriptors = [];

  descriptors.push({
    type: "stat-summary",
    title: "Dependency Snapshot",
    items: buildStatSummaryItems(stats),
  });

  if (Array.isArray(stats.topCouplings) && stats.topCouplings.length > 0) {
    descriptors.push({
      type: "list",
      title: "Top Module Couplings",
      description: "Highest-volume internal import relationships.",
      items: stats.topCouplings.map((edge) => ({
        header: `${edge.source} → ${edge.target}`,
        body: formatCouplingBody(edge),
        badges: edge.unused > 0 ? [`${edge.unused} unused`] : [],
      })),
    });
  }

  if (Array.isArray(stats.externalDependencies) && stats.externalDependencies.length > 0) {
    descriptors.push({
      type: "list",
      title: "External Dependency Buckets",
      description: "Aggregated unique modules imported outside the repository.",
      items: stats.externalDependencies.map((entry) => ({
        header: formatDependencyCategory(entry.category),
        body: `${entry.count} module${entry.count === 1 ? "" : "s"}`,
      })),
    });
  }

  if (Array.isArray(stats.orphans) && stats.orphans.length > 0) {
    descriptors.push({
      type: "pill-list",
      title: "Isolated Modules",
      description: "No internal imports or dependents recorded.",
      items: stats.orphans.slice(0, 10),
    });
  }

  return descriptors;
}

function buildStatSummaryItems(stats) {
  const items = [
    { label: "Modules", value: String(stats.modules ?? 0) },
    { label: "Edges", value: String(stats.edges ?? 0) },
    { label: "Unused Imports", value: String(stats.unusedEdges ?? 0) },
  ];

  if (Array.isArray(stats.topImporters) && stats.topImporters.length > 0) {
    const top = stats.topImporters[0];
    const hintParts = [`statements ${top.outgoingStatements}`];
    if (top.outgoingUnused > 0) {
      hintParts.push(`unused ${top.outgoingUnused}`);
    }
    if (Array.isArray(top.targets) && top.targets.length > 0) {
      hintParts.push(`targets ${top.targets.slice(0, 3).join(", " )}${top.targets.length > 3 ? "…" : ""}`);
    }
    items.push({
      label: "Top Importer",
      value: top.moduleId,
      hint: hintParts.join(" · "),
    });
  } else {
    items.push({ label: "Top Importer", value: "None" });
  }

  return items;
}

function formatCouplingBody(edge) {
  const parts = [`${edge.statements} import${edge.statements === 1 ? "" : "s"}`];
  if (edge.functions > 0) {
    parts.push(`${edge.functions} function${edge.functions === 1 ? "" : "s"} use`);
  }
  return parts.join(" · ");
}

function formatDependencyCategory(category) {
  if (!category || typeof category !== "string") {
    return "Unknown";
  }
  const normalized = category.replace(/[_-]+/g, " ").trim();
  if (!normalized) {
    return "Unknown";
  }
  return normalized
    .split(/\s+/)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function formatModuleLabel(record, stats) {
  const moduleId = record?.moduleId ?? record?.id ?? "module";
  const functionCount = Number.isFinite(stats.functionCount) ? stats.functionCount : 0;
  const outgoing = stats.outgoingEdges;
  const outgoingStatements = stats.outgoingStatements;
  const incoming = stats.incomingEdges;
  const incomingStatements = stats.incomingStatements;
  const unused = stats.outgoingUnused;
  const functionsTouched = stats.functionsTouched;

  const parts = [moduleId];
  parts.push(`Functions ${functionCount}`);
  parts.push(`Out ${outgoing} (${outgoingStatements}) · In ${incoming} (${incomingStatements})`);
  if (unused > 0) {
    parts.push(`Unused imports ${unused}`);
  }
  if (functionsTouched > 0) {
    parts.push(`Functions using ${functionsTouched}`);
  }
  return parts.join("\n");
}

function formatEdgeLabel(edge) {
  const parts = [`${edge.statements} import${edge.statements === 1 ? "" : "s"}`];
  if (edge.functions > 0) {
    parts.push(`${edge.functions} function${edge.functions === 1 ? "" : "s"} use`);
  }
  if (edge.unused > 0) {
    parts.push(`${edge.unused} unused`);
  }
  return parts.join("\n");
}

function resolveModuleClass(stats) {
  if (stats.outgoingEdges + stats.incomingEdges === 0) {
    return "moduleOrphan";
  }
  if (
    stats.outgoingStatements >= DEPENDENCY_THRESHOLDS.alertStatements ||
    stats.outgoingUnused >= DEPENDENCY_THRESHOLDS.alertUnused
  ) {
    return "moduleAlert";
  }
  if (
    stats.outgoingStatements >= DEPENDENCY_THRESHOLDS.cautionStatements ||
    stats.outgoingUnused >= DEPENDENCY_THRESHOLDS.cautionUnused
  ) {
    return "moduleCaution";
  }
  return "module";
}

function resolveScopeLabel(rootId, domainId) {
  if (domainId && typeof domainId === "string") {
    return `domain ${domainId}`;
  }
  if (rootId && typeof rootId === "string") {
    return `root ${rootId}`;
  }
  return "repository";
}

function resolveInternalTarget(target, moduleMap) {
  if (!target || typeof target !== "string") {
    return null;
  }
  let candidate = target.replace(/\//g, ".").replace(/^\.+/, "");
  if (moduleMap.has(candidate)) {
    return candidate;
  }
  const segments = candidate.split(".");
  while (segments.length > 1) {
    segments.pop();
    const probe = segments.join(".");
    if (moduleMap.has(probe)) {
      return probe;
    }
  }
  return null;
}

function createEmptyModuleStats(moduleId, moduleRecord) {
  const functionIds = Array.isArray(moduleRecord?.functions)
    ? moduleRecord.functions
    : moduleRecord?.functions instanceof Set
      ? Array.from(moduleRecord.functions)
      : [];
  return {
    moduleId,
    functionCount: functionIds.length,
    outgoingEdges: 0,
    outgoingStatements: 0,
    outgoingUnused: 0,
    incomingEdges: 0,
    incomingStatements: 0,
    targets: new Set(),
    sources: new Set(),
    unresolvedTargets: new Set(),
    functionsTouched: 0,
  };
}

function toModuleMap(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Map) {
    return value;
  }
  if (Array.isArray(value)) {
    const map = new Map();
    value.forEach((entry) => {
      if (!entry || typeof entry !== "object") {
        return;
      }
      const key = entry.id ?? entry.moduleId ?? entry.module_id ?? null;
      if (key) {
        map.set(key, entry);
      }
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
  toModuleMap,
  collectDependencyData,
  resolveInternalTarget,
  formatModuleLabel,
  formatEdgeLabel,
};
