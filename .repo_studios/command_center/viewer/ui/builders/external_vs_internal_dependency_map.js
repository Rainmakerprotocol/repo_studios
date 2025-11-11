const DEFAULT_VIEW_LABEL = "Dependency · External vs Internal Dependency Map";
const EXTERNAL_CATEGORY_PRIORITY = ["third_party", "standard_library", "unknown"];

const MODULE_CLASS_DEFS = Object.freeze({
  internal: "moduleInternal",
  external: "moduleExternalDominant",
  neutral: "moduleNeutral",
});

const CATEGORY_CLASS_DEFS = Object.freeze({
  third_party: "externalThirdParty",
  standard_library: "externalStandardLibrary",
  unknown: "externalUnknown",
});

export function buildExternalVsInternalDependencyMapDiagram(modules, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  mermaidIdCounter = 0;

  const externalRegistry = new Map();
  const entries = [];

  moduleMap.forEach((record, moduleId) => {
    const entry = createModuleEntry(moduleId, record, moduleMap, externalRegistry);
    if (entry) {
      entries.push(entry);
    }
  });

  if (entries.length === 0) {
    return {
      message: options.emptyModulesMessage ?? "Dependency mix metadata is not available in this CommandView artifact.",
    };
  }

  entries.sort((left, right) => left.moduleId.localeCompare(right.moduleId));

  const lines = ["graph TD"];
  appendClassDefinitions(lines);

  const moduleNodeIds = new Map();
  entries.forEach((entry) => {
    const nodeId = sanitizeMermaidId(entry.moduleId);
    moduleNodeIds.set(entry.moduleId, nodeId);
    lines.push(`  ${nodeId}["${escapeMermaidLabel(entry.label)}"]`);
    lines.push(`  class ${nodeId} ${entry.className};`);
  });

  const externalEntries = Array.from(externalRegistry.values()).sort((left, right) => {
    if (left.packageName === right.packageName) {
      return left.category.localeCompare(right.category);
    }
    return left.packageName.localeCompare(right.packageName);
  });

  const externalNodeIds = new Map();
  externalEntries.forEach((entry) => {
    const nodeId = sanitizeMermaidId(`external_${entry.category}_${entry.packageName}`);
    externalNodeIds.set(entry.key, nodeId);
    lines.push(`  ${nodeId}["${escapeMermaidLabel(formatExternalNodeLabel(entry))}"]`);
    lines.push(`  class ${nodeId} ${resolveExternalClass(entry.category)};`);
  });

  entries.forEach((entry) => {
    const sourceId = moduleNodeIds.get(entry.moduleId);
    if (!sourceId) {
      return;
    }

    entry.internalConnections.forEach((details, targetId) => {
      const targetNodeId = moduleNodeIds.get(targetId);
      if (!targetNodeId) {
        return;
      }
      const label = formatInternalEdgeLabel(details);
      lines.push(`  ${sourceId} -->|${escapeMermaidLabel(label)}| ${targetNodeId}`);
    });

    entry.externalConnections.forEach((details) => {
      const externalId = externalNodeIds.get(details.key);
      if (!externalId) {
        return;
      }
      const label = formatExternalEdgeLabel(details);
      lines.push(`  ${sourceId} -.->|${escapeMermaidLabel(label)}| ${externalId}`);
    });
  });

  const stats = buildStatsSnapshot(entries, externalEntries);
  const scopeLabel = options.scopeDescription ?? resolveScopeLabel(options.rootId, options.domainId, options.moduleId);
  let statusMessage = buildStatusMessage(stats, scopeLabel);
  let statusDetails = buildStatusDetails(stats);

  if (options.fallbackNotice) {
    statusMessage = `${statusMessage} ${options.fallbackNotice}`.trim();
    statusDetails = [
      {
        type: "info",
        title: "Scope fallback applied",
        description: options.fallbackNotice,
      },
      ...statusDetails,
    ];
  }

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    stats,
    statusDetails,
  };
}

function createModuleEntry(moduleId, record, moduleMap, externalRegistry) {
  if (!moduleId || typeof moduleId !== "string") {
    return null;
  }

  const moduleRecord = typeof record === "object" && record !== null ? record : {};
  const importEdges = Array.isArray(moduleRecord.importEdges) ? moduleRecord.importEdges : [];

  const internalConnections = new Map();
  const externalConnections = new Map();

  let externalUnused = 0;
  let externalAliasCount = 0;

  importEdges.forEach((edge) => {
    if (!edge || typeof edge !== "object") {
      return;
    }

    const category = normalizeCategory(edge.category);
    const target = normalizeString(edge.target);
    if (!category || !target) {
      return;
    }

    if (category === "internal") {
      const resolvedTarget = resolveInternalTarget(target, moduleMap) ?? target;
      const bucket = internalConnections.get(resolvedTarget) ?? {
        statements: 0,
        unused: 0,
        functions: new Set(),
      };
      bucket.statements += 1;
      if (edge.unused) {
        bucket.unused += 1;
      }
      if (Array.isArray(edge.functions)) {
        edge.functions.forEach((fn) => {
          const normalizedFn = normalizeString(fn);
          if (normalizedFn) {
            bucket.functions.add(normalizedFn);
          }
        });
      }
      internalConnections.set(resolvedTarget, bucket);
      return;
    }

    const packageName = resolveExternalPackageName(category, target);
    if (!packageName) {
      return;
    }
    const key = `${category}::${packageName}`;
    const connection = externalConnections.get(key) ?? {
      key,
      category,
      packageName,
      statements: 0,
      unused: 0,
      functions: new Set(),
      aliases: new Set(),
    };
    connection.statements += 1;
    if (edge.unused) {
      connection.unused += 1;
      externalUnused += 1;
    }
    if (Array.isArray(edge.functions)) {
      edge.functions.forEach((fn) => {
        const normalizedFn = normalizeString(fn);
        if (normalizedFn) {
          connection.functions.add(normalizedFn);
        }
      });
    }
    if (Array.isArray(edge.via)) {
      edge.via.forEach((alias) => {
        const normalizedAlias = normalizeString(alias);
        if (normalizedAlias) {
          connection.aliases.add(normalizedAlias);
          externalAliasCount += 1;
        }
      });
    }
    externalConnections.set(key, connection);

    let registryEntry = externalRegistry.get(key);
    if (!registryEntry) {
      registryEntry = {
        key,
        category,
        packageName,
        modules: new Set(),
        statements: 0,
        unused: 0,
      };
      externalRegistry.set(key, registryEntry);
    }
    registryEntry.modules.add(moduleId);
    registryEntry.statements += 1;
    if (edge.unused) {
      registryEntry.unused += 1;
    }
  });

  const internalCount = internalConnections.size;
  const externalCount = externalConnections.size;
  const totalConnections = internalCount + externalCount;

  let className = MODULE_CLASS_DEFS.internal;
  if (externalCount > internalCount) {
    className = MODULE_CLASS_DEFS.external;
  } else if (totalConnections === 0) {
    className = MODULE_CLASS_DEFS.neutral;
  }

  const label = formatModuleLabel(moduleId, {
    internalCount,
    externalCount,
    externalUnused,
  });

  return {
    moduleId,
    label,
    className,
    internalConnections,
    externalConnections,
    internalCount,
    externalCount,
    externalUnused,
    externalAliasCount,
  };
}

function buildStatsSnapshot(entries, externalEntries) {
  const internalTargets = new Set();
  let unusedExternalImports = 0;
  let aliasUsage = 0;
  const modulesDominatedByExternal = [];

  entries.forEach((entry) => {
    entry.internalConnections.forEach((_details, targetId) => {
      internalTargets.add(targetId);
    });
    unusedExternalImports += entry.externalUnused;
    aliasUsage += entry.externalAliasCount;
    if (entry.externalCount > entry.internalCount) {
      modulesDominatedByExternal.push({
        moduleId: entry.moduleId,
        internalCount: entry.internalCount,
        externalCount: entry.externalCount,
        unusedExternalImports: entry.externalUnused,
      });
    }
  });

  modulesDominatedByExternal.sort((left, right) => {
    const leftDelta = left.externalCount - left.internalCount;
    const rightDelta = right.externalCount - right.internalCount;
    if (rightDelta !== leftDelta) {
      return rightDelta - leftDelta;
    }
    if (right.externalCount !== left.externalCount) {
      return right.externalCount - left.externalCount;
    }
    return left.moduleId.localeCompare(right.moduleId);
  });

  const categoryBreakdown = new Map();
  const topExternalPackages = externalEntries.map((entry) => {
    const bucket = categoryBreakdown.get(entry.category) ?? {
      category: entry.category,
      packages: 0,
      statements: 0,
      modules: new Set(),
      unused: 0,
    };
    bucket.packages += 1;
    bucket.statements += entry.statements;
    entry.modules.forEach((moduleId) => bucket.modules.add(moduleId));
    bucket.unused += entry.unused;
    categoryBreakdown.set(entry.category, bucket);

    return {
      packageName: entry.packageName,
      category: entry.category,
      moduleCount: entry.modules.size,
      statements: entry.statements,
      unused: entry.unused,
    };
  });

  topExternalPackages.sort((left, right) => {
    if (right.statements !== left.statements) {
      return right.statements - left.statements;
    }
    if (right.moduleCount !== left.moduleCount) {
      return right.moduleCount - left.moduleCount;
    }
    if (left.packageName === right.packageName) {
      return left.category.localeCompare(right.category);
    }
    return left.packageName.localeCompare(right.packageName);
  });

  const categoryEntries = Array.from(categoryBreakdown.values()).map((entry) => ({
    category: entry.category,
    packages: entry.packages,
    statements: entry.statements,
    modules: entry.modules.size,
    unused: entry.unused,
  }));

  categoryEntries.sort((left, right) => {
    if (right.statements !== left.statements) {
      return right.statements - left.statements;
    }
    return left.category.localeCompare(right.category);
  });

  return {
    modules: entries.length,
    internalTargets: internalTargets.size,
    externalPackages: externalEntries.length,
    unusedExternalImports,
    aliasUsage,
    modulesDominatedByExternal,
    topExternalPackages,
    categoryBreakdown: categoryEntries,
  };
}

function buildStatusMessage(stats, scopeLabel) {
  const suffixParts = [];
  if (Array.isArray(stats.modulesDominatedByExternal) && stats.modulesDominatedByExternal.length > 0) {
    suffixParts.push(`${stats.modulesDominatedByExternal.length} module${stats.modulesDominatedByExternal.length === 1 ? "" : "s"} dominated by external imports`);
  }
  if (stats.unusedExternalImports > 0) {
    suffixParts.push(`${stats.unusedExternalImports} unused external import${stats.unusedExternalImports === 1 ? "" : "s"}`);
  }
  const suffix = suffixParts.length > 0 ? `; ${suffixParts.join("; ")}` : "";
  return `Rendered External vs Internal Dependency Map for ${scopeLabel} (${stats.modules} modules, ${stats.internalTargets} internal links, ${stats.externalPackages} external packages${suffix}).`;
}

function buildStatusDetails(stats) {
  const descriptors = [];

  descriptors.push({
    type: "stat-summary",
    title: "Dependency Mix Snapshot",
    items: [
      { label: "Modules", value: String(stats.modules ?? 0) },
      { label: "Internal Targets", value: String(stats.internalTargets ?? 0) },
      { label: "External Packages", value: String(stats.externalPackages ?? 0) },
      { label: "Unused External Imports", value: String(stats.unusedExternalImports ?? 0) },
      { label: "Alias Usage", value: String(stats.aliasUsage ?? 0) },
    ],
  });

  if (Array.isArray(stats.modulesDominatedByExternal) && stats.modulesDominatedByExternal.length > 0) {
    descriptors.push({
      type: "list",
      title: "Modules Dominated by External Imports",
      description: "External packages outnumber internal module dependencies.",
      items: stats.modulesDominatedByExternal.slice(0, 10).map((entry) => ({
        header: entry.moduleId,
        body: formatModuleDominanceBody(entry),
        badges: entry.unusedExternalImports > 0 ? [
          `${entry.unusedExternalImports} unused`,
        ] : [],
      })),
    });
  }

  if (Array.isArray(stats.topExternalPackages) && stats.topExternalPackages.length > 0) {
    descriptors.push({
      type: "list",
      title: "Top External Packages",
      description: "Packages imported most frequently across modules.",
      items: stats.topExternalPackages.slice(0, 10).map((entry) => ({
        header: `${formatCategoryLabel(entry.category)} · ${entry.packageName}`,
        body: `${entry.statements} import${entry.statements === 1 ? "" : "s"} across ${entry.moduleCount} module${entry.moduleCount === 1 ? "" : "s"}`,
        badges: entry.unused > 0 ? [`${entry.unused} unused`] : [],
      })),
    });
  }

  if (Array.isArray(stats.categoryBreakdown) && stats.categoryBreakdown.length > 0) {
    descriptors.push({
      type: "list",
      title: "External Category Breakdown",
      description: "Unique packages and import totals per category.",
      items: stats.categoryBreakdown.map((entry) => ({
        header: formatCategoryLabel(entry.category),
        body: `${entry.packages} package${entry.packages === 1 ? "" : "s"} · ${entry.statements} import${entry.statements === 1 ? "" : "s"} across ${entry.modules} module${entry.modules === 1 ? "" : "s"}`,
        badges: entry.unused > 0 ? [`${entry.unused} unused`] : [],
      })),
    });
  }

  return descriptors;
}

function appendClassDefinitions(lines) {
  lines.push("  classDef moduleInternal fill:#0f172a,stroke:#38bdf8,color:#f8fafc,stroke-width:1.5px;");
  lines.push("  classDef moduleExternalDominant fill:#1f2937,stroke:#f97316,color:#fef3c7,stroke-width:2px;");
  lines.push("  classDef moduleNeutral fill:#111827,stroke:#94a3b8,color:#e2e8f0,stroke-width:1px;");
  lines.push("  classDef externalThirdParty fill:#1f2937,stroke:#f97316,color:#fef3c7,stroke-width:1.5px;");
  lines.push("  classDef externalStandardLibrary fill:#022c22,stroke:#34d399,color:#d1fae5,stroke-width:1.5px;");
  lines.push("  classDef externalUnknown fill:#1f2937,stroke:#94a3b8,color:#e2e8f0,stroke-width:1.5px;");
}

function formatModuleLabel(moduleId, stats) {
  const parts = [moduleId];
  parts.push(`Internal: ${stats.internalCount} module${stats.internalCount === 1 ? "" : "s"}`);
  parts.push(`External: ${stats.externalCount} package${stats.externalCount === 1 ? "" : "s"}`);
  if (stats.externalUnused > 0) {
    parts.push(`Unused external: ${stats.externalUnused}`);
  }
  return parts.join("\n");
}

function formatModuleDominanceBody(entry) {
  const parts = [
    `external ${entry.externalCount}`,
    `internal ${entry.internalCount}`,
  ];
  if (entry.unusedExternalImports > 0) {
    parts.push(`unused ${entry.unusedExternalImports}`);
  }
  return parts.join(" · ");
}

function formatExternalNodeLabel(entry) {
  const moduleCount = entry.modules.size;
  const parts = [entry.packageName];
  parts.push(`${formatCategoryLabel(entry.category)} · ${moduleCount} module${moduleCount === 1 ? "" : "s"}`);
  if (entry.unused > 0) {
    parts.push(`Unused: ${entry.unused}`);
  }
  return parts.join("\n");
}

function formatInternalEdgeLabel(details) {
  const parts = [`internal ${details.statements}`];
  if (details.unused > 0) {
    parts.push(`${details.unused} unused`);
  }
  if (details.functions.size > 0) {
    parts.push(`${details.functions.size} function${details.functions.size === 1 ? "" : "s"}`);
  }
  return parts.join(" · ");
}

function formatExternalEdgeLabel(details) {
  const parts = [`${formatCategoryLabel(details.category)} ${details.statements}`];
  if (details.unused > 0) {
    parts.push(`${details.unused} unused`);
  }
  if (details.functions.size > 0) {
    parts.push(`${details.functions.size} function${details.functions.size === 1 ? "" : "s"}`);
  }
  if (details.aliases.size > 0) {
    parts.push(`${details.aliases.size} alias${details.aliases.size === 1 ? "" : "es"}`);
  }
  return parts.join(" · ");
}

function resolveExternalClass(category) {
  return CATEGORY_CLASS_DEFS[category] ?? CATEGORY_CLASS_DEFS.unknown;
}

function resolveScopeLabel(rootId, domainId, moduleId) {
  if (moduleId && typeof moduleId === "string") {
    return moduleId;
  }
  if (domainId && typeof domainId === "string") {
    return `domain ${domainId}`;
  }
  if (rootId && typeof rootId === "string") {
    return `root ${rootId}`;
  }
  return "repository";
}

function resolveExternalPackageName(category, target) {
  const normalized = normalizeString(target);
  if (!normalized) {
    return null;
  }
  const base = normalized.split("::")[0];
  const firstSegment = base.split("/")[0].split(".")[0];
  if (!firstSegment) {
    return null;
  }
  return firstSegment;
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

function normalizeCategory(category) {
  const normalized = normalizeString(category);
  if (!normalized) {
    return "unknown";
  }
  if (normalized === "internal") {
    return "internal";
  }
  if (EXTERNAL_CATEGORY_PRIORITY.includes(normalized)) {
    return normalized;
  }
  return "unknown";
}

function normalizeString(value) {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
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

function formatCategoryLabel(category) {
  if (!category || typeof category !== "string") {
    return "Unknown";
  }
  return category
    .split(/[_-]/g)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
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

export const __test__ = {
  createModuleEntry,
  buildStatsSnapshot,
  buildStatusDetails,
  formatExternalEdgeLabel,
  formatInternalEdgeLabel,
  formatModuleLabel,
  resolveExternalPackageName,
  toModuleMap,
};
