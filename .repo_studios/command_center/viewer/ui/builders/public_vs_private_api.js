const DEFAULT_VIEW_LABEL = "Quality Metrics · Public vs Private API";
const DEFAULT_MODULE_LIMIT = 12;
const DEFAULT_SYMBOL_LIMIT = 6;
const DEFAULT_REEXPORT_LIMIT = 6;
const DEFAULT_MISSING_LIMIT = 6;

const CATEGORY_CONFIG = Object.freeze({
  exported: { title: "Declared Exports", className: "exported", noun: "exported symbol" },
  implicit: { title: "Implicit Public", className: "implicit", noun: "implicit symbol" },
  internal: { title: "Internal Helpers", className: "internal", noun: "internal helper" },
  private: { title: "Private Helpers", className: "private", noun: "private helper" },
});

const SYMBOL_TYPE_ORDER = Object.freeze({
  function: 0,
  class: 1,
  global: 2,
});

const CLASS_DEFINITIONS = Object.freeze([
  "classDef moduleHub fill:#0b1120,stroke:#94a3b8,color:#e2e8f0",
  "classDef summary fill:#111827,stroke:#64748b,color:#e2e8f0",
  "classDef exported fill:#0f172a,stroke:#38bdf8,color:#e0f2fe",
  "classDef implicit fill:#1f2937,stroke:#22d3ee,color:#f0fdfa",
  "classDef internal fill:#1f2937,stroke:#facc15,color:#fef9c3",
  "classDef private fill:#111827,stroke:#f87171,color:#fee2e2",
  "classDef reexport fill:#0f172a,stroke:#a5b4fc,color:#ede9fe",
  "classDef missing fill:#78350f,stroke:#facc15,color:#fef3c7",
]);

export function buildPublicVsPrivateApiDiagram(modules, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const limits = {
    moduleLimit: resolvePositiveNumber(options.moduleLimit, DEFAULT_MODULE_LIMIT),
    symbolLimit: resolvePositiveNumber(options.symbolLimit, DEFAULT_SYMBOL_LIMIT),
    reexportLimit: resolvePositiveNumber(options.reexportLimit, DEFAULT_REEXPORT_LIMIT),
    missingLimit: resolvePositiveNumber(options.missingLimit, DEFAULT_MISSING_LIMIT),
  };

  const entries = [];
  moduleMap.forEach((record, moduleId) => {
    const entry = createModuleApiEntry(moduleId, record, limits);
    if (entry) {
      entries.push(entry);
    }
  });

  if (entries.length === 0) {
    return {
      message: options.emptyMessage ?? "Public vs Private API surface metadata is unavailable for this selection.",
    };
  }

  entries.sort((left, right) => {
    const implicitDiff = right.categories.implicit.counts.total - left.categories.implicit.counts.total;
    if (implicitDiff !== 0) {
      return implicitDiff;
    }
    const exportedDiff = right.categories.exported.counts.total - left.categories.exported.counts.total;
    if (exportedDiff !== 0) {
      return exportedDiff;
    }
    return left.moduleId.localeCompare(right.moduleId);
  });

  const totalModules = entries.length;
  const displayEntries = entries.slice(0, limits.moduleLimit);
  const hiddenModules = Math.max(0, totalModules - displayEntries.length);

  const lines = ["graph LR"];
  appendClassDefinitions(lines);

  displayEntries.forEach((entry) => {
    appendModuleSection(lines, entry);
  });

  const stats = buildStats(entries, displayEntries.length, totalModules, hiddenModules);
  const scopeDescription = normalizeString(options.scopeDescription) ?? "repository";
  let statusMessage = buildStatusMessage(stats, scopeDescription, hiddenModules);
  const statusDetails = buildStatusDetails(stats, hiddenModules);

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
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    stats,
    statusDetails,
  };
}

function appendModuleSection(lines, entry) {
  const groupId = sanitizeMermaidId(`${entry.moduleId}_group`);
  lines.push(`  subgraph ${groupId}["${escapeMermaidLabel(buildModuleLabel(entry))}"]`);
  lines.push("    direction LR");

  const moduleHubId = sanitizeMermaidId(`${entry.moduleId}_hub`);
  lines.push(`    ${moduleHubId}["${escapeMermaidLabel(buildModuleHubLabel(entry))}"]`);
  lines.push(`    class ${moduleHubId} moduleHub;`);

  const publicLane = appendLane(lines, {
    indent: "    ",
    moduleId: entry.moduleId,
    laneKey: "public",
    laneLabel: "Public Surface",
    hubLabel: buildLaneHubLabel(entry, "public"),
    categoryKeys: ["exported", "implicit"],
    entry,
  });

  const internalLane = appendLane(lines, {
    indent: "    ",
    moduleId: entry.moduleId,
    laneKey: "internal",
    laneLabel: "Internal Surface",
    hubLabel: buildLaneHubLabel(entry, "internal"),
    categoryKeys: ["internal", "private"],
    entry,
  });

  lines.push(`    ${moduleHubId} --> ${publicLane.hubId}`);
  lines.push(`    ${moduleHubId} -.-> ${internalLane.hubId}`);

  appendMissingNodes(lines, entry, moduleHubId, "    ");

  lines.push("  end");
}

function appendLane(lines, context) {
  const { indent, moduleId, laneKey, laneLabel, hubLabel, categoryKeys, entry } = context;
  const groupId = sanitizeMermaidId(`${moduleId}_${laneKey}_lane`);
  const hubId = sanitizeMermaidId(`${moduleId}_${laneKey}_hub`);

  lines.push(`${indent}subgraph ${groupId}["${escapeMermaidLabel(laneLabel)}"]`);
  lines.push(`${indent}  direction TB`);
  lines.push(`${indent}  ${hubId}["${escapeMermaidLabel(hubLabel)}"]`);
  lines.push(`${indent}  class ${hubId} summary;`);

  const categoryIndent = `${indent}  `;
  categoryKeys.forEach((categoryKey) => {
    const bucket = entry.categories[categoryKey];
    if (!bucket) {
      return;
    }
    appendCategoryNode(lines, {
      indent: categoryIndent,
      moduleId,
      bucket,
      parentHubId: hubId,
      entry,
    });
  });

  lines.push(`${indent}end`);

  return { groupId, hubId };
}

function appendCategoryNode(lines, context) {
  const { indent, moduleId, bucket, parentHubId, entry } = context;
  const nodeId = sanitizeMermaidId(`${moduleId}_${bucket.key}_bucket`);

  lines.push(`${indent}${nodeId}["${escapeMermaidLabel(buildCategoryLabel(bucket))}"]`);
  lines.push(`${indent}class ${nodeId} ${bucket.className};`);
  lines.push(`${indent}${parentHubId} --> ${nodeId}`);

  bucket.displayItems.forEach((symbol, index) => {
    const symbolId = sanitizeMermaidId(`${moduleId}_${bucket.key}_${index}`);
    lines.push(`${indent}${symbolId}["${escapeMermaidLabel(formatSymbolLabel(symbol))}"]`);
    lines.push(`${indent}class ${symbolId} ${bucket.className};`);
    lines.push(`${indent}${nodeId} --> ${symbolId}`);
  });

  if (bucket.extraCount > 0) {
    const overflowId = sanitizeMermaidId(`${moduleId}_${bucket.key}_more`);
    lines.push(`${indent}${overflowId}["${escapeMermaidLabel(formatOverflowLabel(bucket.extraCount, bucket.noun))}"]`);
    lines.push(`${indent}class ${overflowId} ${bucket.className};`);
    lines.push(`${indent}${nodeId} --> ${overflowId}`);
  }

  if (bucket.key === "exported") {
    appendReexports(lines, {
      indent,
      moduleId,
      parentNodeId: nodeId,
      entry,
    });
  }
}

function appendReexports(lines, context) {
  const { indent, moduleId, parentNodeId, entry } = context;
  entry.reexports.forEach((reexport, index) => {
    const nodeId = sanitizeMermaidId(`${moduleId}_reexport_${index}`);
    lines.push(`${indent}${nodeId}["${escapeMermaidLabel(formatReexportLabel(reexport))}"]`);
    lines.push(`${indent}class ${nodeId} reexport;`);
    lines.push(`${indent}${parentNodeId} --> ${nodeId}`);
  });

  if (entry.reexportsOverflow > 0) {
    const overflowId = sanitizeMermaidId(`${moduleId}_reexport_more`);
    lines.push(`${indent}${overflowId}["${escapeMermaidLabel(formatOverflowLabel(entry.reexportsOverflow, "re-export"))}"]`);
    lines.push(`${indent}class ${overflowId} reexport;`);
    lines.push(`${indent}${parentNodeId} --> ${overflowId}`);
  }
}

function appendMissingNodes(lines, entry, moduleHubId, indent) {
  entry.missing.forEach((missing, index) => {
    const nodeId = sanitizeMermaidId(`${entry.moduleId}_missing_${index}`);
    lines.push(`${indent}${nodeId}["${escapeMermaidLabel(formatMissingLabel(missing))}"]`);
    lines.push(`${indent}class ${nodeId} missing;`);
    lines.push(`${indent}${moduleHubId} -.-> ${nodeId}`);
  });

  if (entry.missingOverflow > 0) {
    const overflowId = sanitizeMermaidId(`${entry.moduleId}_missing_more`);
    lines.push(`${indent}${overflowId}["${escapeMermaidLabel(formatOverflowLabel(entry.missingOverflow, "missing export"))}"]`);
    lines.push(`${indent}class ${overflowId} missing;`);
    lines.push(`${indent}${moduleHubId} -.-> ${overflowId}`);
  }
}

function appendClassDefinitions(lines) {
  CLASS_DEFINITIONS.forEach((definition) => {
    lines.push(`  ${definition}`);
  });
}

function createModuleApiEntry(moduleId, moduleRecord, limits) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return null;
  }

  const apiSurface = moduleRecord.apiSurface;
  if (!apiSurface || typeof apiSurface !== "object") {
    return null;
  }

  const categories = collectCategoryBuckets(apiSurface, moduleId, limits.symbolLimit);
  const totalSymbols =
    categories.exported.counts.total +
    categories.implicit.counts.total +
    categories.internal.counts.total +
    categories.private.counts.total;

  const reexports = normalizeReexports(Array.isArray(apiSurface.reexports) ? apiSurface.reexports : []);
  const missing = normalizeMissingExports(Array.isArray(apiSurface.missingExports) ? apiSurface.missingExports : []);

  const displayReexports = reexports.slice(0, limits.reexportLimit);
  const displayMissing = missing.slice(0, limits.missingLimit);

  if (totalSymbols === 0 && displayReexports.length === 0 && displayMissing.length === 0) {
    return null;
  }

  const moduleLabel = normalizeString(moduleRecord.moduleId ?? moduleRecord.id ?? moduleId) ?? moduleId;
  const summary = {
    hasDeclaredExports: apiSurface.hasDeclaredExports === true,
    strategy: normalizeStrategy(apiSurface.strategy),
    exportedSymbolCount: Array.isArray(apiSurface.exportedSymbols) ? apiSurface.exportedSymbols.length : 0,
    reexportCount: reexports.length,
    missingCount: missing.length,
    totalSymbols,
  };

  return {
    moduleId,
    moduleLabel,
    summary,
    categories,
    reexports: displayReexports,
    reexportsOverflow: Math.max(0, reexports.length - displayReexports.length),
    missing: displayMissing,
    missingOverflow: Math.max(0, missing.length - displayMissing.length),
  };
}

function collectCategoryBuckets(apiSurface, moduleId, symbolLimit) {
  const buckets = {};
  Object.entries(CATEGORY_CONFIG).forEach(([key, config]) => {
    buckets[key] = {
      key,
      title: config.title,
      className: config.className,
      noun: config.noun,
      items: [],
      displayItems: [],
      extraCount: 0,
      counts: {
        total: 0,
        functions: 0,
        classes: 0,
        globals: 0,
      },
    };
  });

  const addSymbol = (item, symbolType) => {
    if (!item || typeof item !== "object") {
      return;
    }
    const categoryKey = normalizeCategoryKey(item.category);
    const bucket = buckets[categoryKey];
    if (!bucket) {
      return;
    }
    const symbol = normalizeApiSymbol(item, symbolType, moduleId);
    bucket.items.push(symbol);
    bucket.counts.total += 1;
    if (symbolType === "function") {
      bucket.counts.functions += 1;
    } else if (symbolType === "class") {
      bucket.counts.classes += 1;
    } else if (symbolType === "global") {
      bucket.counts.globals += 1;
    }
  };

  const functionPublic = Array.isArray(apiSurface.functions?.public) ? apiSurface.functions.public : [];
  functionPublic.forEach((fn) => addSymbol(fn, "function"));
  const functionInternal = Array.isArray(apiSurface.functions?.internal) ? apiSurface.functions.internal : [];
  functionInternal.forEach((fn) => addSymbol(fn, "function"));

  const classPublic = Array.isArray(apiSurface.classes?.public) ? apiSurface.classes.public : [];
  classPublic.forEach((cls) => addSymbol(cls, "class"));
  const classInternal = Array.isArray(apiSurface.classes?.internal) ? apiSurface.classes.internal : [];
  classInternal.forEach((cls) => addSymbol(cls, "class"));

  const globalPublic = Array.isArray(apiSurface.globals?.public) ? apiSurface.globals.public : [];
  globalPublic.forEach((globalEntry) => addSymbol(globalEntry, "global"));
  const globalInternal = Array.isArray(apiSurface.globals?.internal) ? apiSurface.globals.internal : [];
  globalInternal.forEach((globalEntry) => addSymbol(globalEntry, "global"));

  Object.values(buckets).forEach((bucket) => {
    bucket.items.sort(compareSymbols);
    bucket.displayItems = bucket.items.slice(0, symbolLimit);
    bucket.extraCount = Math.max(0, bucket.items.length - bucket.displayItems.length);
  });

  return buckets;
}

function normalizeApiSymbol(item, symbolType, moduleId) {
  const rawName = normalizeString(item.name ?? item.id ?? null);
  const name = rawName ?? `${symbolType}`;
  const category = normalizeCategoryKey(item.category);
  return {
    id: item.id ?? `${moduleId}::${name}`,
    name,
    symbolType,
    category,
    coverage: toNullableNumber(item.coverage),
    typeHintCoverage: toNullableNumber(item.typeHintCoverage),
    docstringQuality: item.docstringQuality ?? null,
    methodCount: symbolType === "class" ? toNullableInteger(item.methodCount) : null,
    valueKind: symbolType === "global" ? normalizeString(item.valueKind) : null,
    lineno: toNullableInteger(item.lineno),
  };
}

function normalizeReexports(entries) {
  if (!Array.isArray(entries)) {
    return [];
  }
  return entries
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const symbol = normalizeString(entry.symbol);
      if (!symbol) {
        return null;
      }
      return {
        symbol,
        sourceModule: normalizeString(entry.sourceModule ?? entry.source_module ?? null),
        sourceName: normalizeString(entry.sourceName ?? entry.source_name ?? null),
        sourceQualifiedName: normalizeString(entry.sourceQualifiedName ?? entry.source_qualified_name ?? null),
        lineno: toNullableInteger(entry.lineno),
      };
    })
    .filter(Boolean)
    .sort((left, right) => {
      if (left.symbol !== right.symbol) {
        return left.symbol.localeCompare(right.symbol);
      }
      return (left.sourceModule ?? "").localeCompare(right.sourceModule ?? "");
    });
}

function normalizeMissingExports(entries) {
  if (!Array.isArray(entries)) {
    return [];
  }
  return entries
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const symbol = normalizeString(entry.symbol);
      if (!symbol) {
        return null;
      }
      const kind = normalizeString(entry.kind ?? (entry.defined === false ? "missing" : null)) ?? "unknown";
      return {
        symbol,
        kind,
      };
    })
    .filter(Boolean)
    .sort((left, right) => left.symbol.localeCompare(right.symbol));
}

function buildModuleLabel(entry) {
  return entry.moduleLabel;
}

function buildModuleHubLabel(entry) {
  const lines = [entry.moduleLabel];
  lines.push(entry.summary.hasDeclaredExports ? "Strategy: __all__" : "Strategy: implicit");
  lines.push(`Declared symbols: ${entry.summary.exportedSymbolCount}`);
  if (entry.summary.reexportCount > 0) {
    lines.push(`Re-exports: ${entry.summary.reexportCount}`);
  }
  if (entry.summary.missingCount > 0) {
    lines.push(`Missing exports: ${entry.summary.missingCount}`);
  }
  lines.push(`Total symbols: ${entry.summary.totalSymbols}`);
  return lines.join("\n");
}

function buildLaneHubLabel(entry, laneKey) {
  if (laneKey === "public") {
    const declared = entry.categories.exported.counts.total;
    const implicit = entry.categories.implicit.counts.total;
    return `Declared: ${declared}\nImplicit: ${implicit}`;
  }
  const internal = entry.categories.internal.counts.total;
  const privateCount = entry.categories.private.counts.total;
  return `Internal: ${internal}\nPrivate: ${privateCount}`;
}

function buildCategoryLabel(bucket) {
  const lines = [`${bucket.title} (${bucket.counts.total})`];
  const breakdown = [];
  if (bucket.counts.functions > 0) {
    breakdown.push(`${bucket.counts.functions} function${bucket.counts.functions === 1 ? "" : "s"}`);
  }
  if (bucket.counts.classes > 0) {
    breakdown.push(`${bucket.counts.classes} class${bucket.counts.classes === 1 ? "" : "es"}`);
  }
  if (bucket.counts.globals > 0) {
    breakdown.push(`${bucket.counts.globals} global${bucket.counts.globals === 1 ? "" : "s"}`);
  }
  if (breakdown.length === 0) {
    lines.push("None recorded");
  } else {
    lines.push(breakdown.join(", "));
  }
  return lines.join("\n");
}

function formatSymbolLabel(symbol) {
  const lines = [symbol.name];
  lines.push(`${capitalize(symbol.symbolType)} · ${formatCategoryDescriptor(symbol.category)}`);
  if (symbol.coverage !== null) {
    lines.push(`Coverage ${formatPercent(symbol.coverage)}`);
  }
  if (symbol.typeHintCoverage !== null) {
    lines.push(`Typing ${formatPercent(symbol.typeHintCoverage)}`);
  }
  if (symbol.symbolType === "class" && symbol.methodCount !== null) {
    lines.push(`${symbol.methodCount} method${symbol.methodCount === 1 ? "" : "s"}`);
  }
  if (symbol.symbolType === "global" && symbol.valueKind) {
    lines.push(symbol.valueKind);
  }
  if (symbol.lineno !== null) {
    lines.push(`Line ${symbol.lineno}`);
  }
  return lines.join("\n");
}

function formatReexportLabel(reexport) {
  const lines = [reexport.symbol];
  if (reexport.sourceModule && reexport.sourceName) {
    lines.push(`from ${reexport.sourceModule}.${reexport.sourceName}`);
  } else if (reexport.sourceModule) {
    lines.push(`from ${reexport.sourceModule}`);
  }
  if (reexport.lineno !== null) {
    lines.push(`Line ${reexport.lineno}`);
  }
  return lines.join("\n");
}

function formatMissingLabel(missing) {
  const lines = [missing.symbol];
  lines.push(`Declared as ${missing.kind}`);
  return lines.join("\n");
}

function buildStats(entries, visibleModules, totalModules, hiddenModules) {
  const stats = {
    totalModules,
    visibleModules,
    hiddenModules,
    exported: 0,
    implicit: 0,
    internal: 0,
    private: 0,
    reexports: 0,
    missing: 0,
    modulesWithImplicit: [],
    modulesWithoutDeclaredExports: [],
    modulesWithMissingExports: [],
  };

  entries.forEach((entry) => {
    stats.exported += entry.categories.exported.counts.total;
    stats.implicit += entry.categories.implicit.counts.total;
    stats.internal += entry.categories.internal.counts.total;
    stats.private += entry.categories.private.counts.total;
    stats.reexports += entry.summary.reexportCount;
    stats.missing += entry.summary.missingCount;

    if (!entry.summary.hasDeclaredExports) {
      stats.modulesWithoutDeclaredExports.push(entry.moduleId);
    }

    if (entry.categories.implicit.counts.total > 0) {
      stats.modulesWithImplicit.push({
        moduleId: entry.moduleId,
        count: entry.categories.implicit.counts.total,
        samples: entry.categories.implicit.items.slice(0, 5).map((symbol) => symbol.name),
      });
    }

    if (entry.summary.missingCount > 0) {
      stats.modulesWithMissingExports.push({
        moduleId: entry.moduleId,
        count: entry.summary.missingCount,
        symbols: entry.missing.slice(0, 5).map((missing) => missing.symbol),
      });
    }
  });

  stats.modulesWithoutDeclaredExports.sort((a, b) => a.localeCompare(b));
  stats.modulesWithImplicit.sort((left, right) => right.count - left.count || left.moduleId.localeCompare(right.moduleId));
  stats.modulesWithMissingExports.sort((left, right) => right.count - left.count || left.moduleId.localeCompare(right.moduleId));

  return stats;
}

function buildStatusMessage(stats, scopeDescription, hiddenModules) {
  const segments = [
    `${stats.visibleModules} of ${stats.totalModules} module${stats.totalModules === 1 ? "" : "s"} displayed`,
    `${stats.exported} exported`,
    `${stats.implicit} implicit`,
    `${stats.internal} internal`,
    `${stats.private} private`,
  ];
  if (stats.reexports > 0) {
    segments.push(`${stats.reexports} re-export${stats.reexports === 1 ? "" : "s"}`);
  }
  if (stats.missing > 0) {
    segments.push(`${stats.missing} missing export${stats.missing === 1 ? "" : "s"}`);
  }
  if (stats.modulesWithoutDeclaredExports.length > 0) {
    segments.push(`${stats.modulesWithoutDeclaredExports.length} without __all__`);
  }
  if (hiddenModules > 0) {
    segments.push(`${hiddenModules} hidden`);
  }
  return `Rendered Public vs Private API Map for ${scopeDescription} (${segments.join(", ")}).`;
}

function buildStatusDetails(stats, hiddenModules) {
  const details = [];
  const summaryItems = [
    { label: "Modules Displayed", value: `${stats.visibleModules} / ${stats.totalModules}` },
    { label: "Declared Exports", value: String(stats.exported) },
    { label: "Implicit Symbols", value: String(stats.implicit) },
    { label: "Internal Helpers", value: String(stats.internal) },
    { label: "Private Helpers", value: String(stats.private) },
  ];

  if (stats.reexports > 0) {
    summaryItems.push({ label: "Re-exports", value: String(stats.reexports) });
  }
  if (stats.missing > 0) {
    summaryItems.push({ label: "Missing Exports", value: String(stats.missing) });
  }
  if (hiddenModules > 0) {
    summaryItems.push({ label: "Hidden Modules", value: String(hiddenModules) });
  }

  details.push({
    type: "stat-summary",
    title: "API Surface Snapshot",
    items: summaryItems,
  });

  if (stats.modulesWithoutDeclaredExports.length > 0) {
    details.push({
      type: "pill-list",
      title: "Modules Without __all__",
      description: "Modules relying on implicit exports.",
      items: stats.modulesWithoutDeclaredExports.slice(0, 12),
    });
  }

  if (stats.modulesWithImplicit.length > 0) {
    details.push({
      type: "list",
      title: "Implicit Public Symbols",
      description: "Modules exposing non-underscore names without __all__.",
      items: stats.modulesWithImplicit.slice(0, 8).map((entry) => ({
        header: `${entry.moduleId} (${entry.count})`,
        body: entry.samples.join(", ") || null,
        badges: entry.samples.length >= 5 && entry.count > entry.samples.length ? [`+${entry.count - entry.samples.length} more`] : [],
      })),
    });
  }

  if (stats.modulesWithMissingExports.length > 0) {
    details.push({
      type: "list",
      title: "Declared But Missing",
      description: "Symbols declared in __all__ without local definitions.",
      items: stats.modulesWithMissingExports.slice(0, 8).map((entry) => ({
        header: `${entry.moduleId} (${entry.count})`,
        body: entry.symbols.join(", ") || null,
        badges: entry.symbols.length >= 5 && entry.count > entry.symbols.length ? [`+${entry.count - entry.symbols.length} more`] : [],
      })),
    });
  }

  return details;
}

function formatCategoryDescriptor(category) {
  switch (category) {
    case "exported":
      return "declared";
    case "implicit":
      return "implicit";
    case "internal":
      return "internal";
    case "private":
      return "private";
    default:
      return category;
  }
}

function formatOverflowLabel(count, noun) {
  const plural = count === 1 ? noun : `${noun}s`;
  return `+${count} more ${plural}`;
}

function formatPercent(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  if (value <= 1 && value >= 0) {
    return `${Math.round(value * 100)}%`;
  }
  return `${Math.round(value)}%`;
}

function compareSymbols(left, right) {
  const leftOrder = SYMBOL_TYPE_ORDER[left.symbolType] ?? 99;
  const rightOrder = SYMBOL_TYPE_ORDER[right.symbolType] ?? 99;
  if (leftOrder !== rightOrder) {
    return leftOrder - rightOrder;
  }
  if (left.name !== right.name) {
    return left.name.localeCompare(right.name);
  }
  return (left.id ?? "").localeCompare(right.id ?? "");
}

function normalizeStrategy(strategy) {
  const value = normalizeString(strategy);
  return value === "explicit" ? "explicit" : "implicit";
}

function normalizeCategoryKey(category) {
  const value = normalizeString(category);
  if (value === "exported" || value === "implicit" || value === "internal" || value === "private") {
    return value;
  }
  return value === "public" ? "exported" : "internal";
}

function capitalize(text) {
  if (!text || typeof text !== "string") {
    return "";
  }
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function resolvePositiveNumber(value, fallback) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return fallback;
  }
  return Math.floor(numeric);
}

function toNullableNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function toNullableInteger(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.trunc(numeric) : null;
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
  return null;
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

function toModuleMap(value) {
  if (value instanceof Map) {
    return value;
  }
  if (Array.isArray(value)) {
    const map = new Map();
    value.forEach((entry) => {
      if (!entry || typeof entry !== "object") {
        return;
      }
      const key = normalizeString(entry.moduleId ?? entry.id ?? null);
      if (key) {
        map.set(key, entry);
      }
    });
    return map;
  }
  if (value && typeof value === "object") {
    const map = new Map();
    Object.entries(value).forEach(([key, entry]) => {
      map.set(key, entry);
    });
    return map;
  }
  return null;
}

export const __test__ = {
  createModuleApiEntry,
  collectCategoryBuckets,
  buildStats,
  formatSymbolLabel,
  toModuleMap,
};
