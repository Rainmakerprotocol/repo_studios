const DEFAULT_VIEW_LABEL = "Dependency · Export Contract Matrix";
const MAX_REEXPORT_DETAILS = 10;
const MAX_MISSING_DETAILS = 10;

const SYMBOL_STYLES = Object.freeze({
  function: { fill: "#0f172a", stroke: "#38bdf8", color: "#f8fafc" },
  class: { fill: "#1f2937", stroke: "#a855f7", color: "#f5f3ff" },
  global: { fill: "#1e293b", stroke: "#6366f1", color: "#e0e7ff" },
  reexport: { fill: "#0f172a", stroke: "#22d3ee", color: "#ecfeff" },
  missing: { fill: "#7f1d1d", stroke: "#f87171", color: "#fee2e2" },
  dynamic: { fill: "#78350f", stroke: "#facc15", color: "#fff7ed" },
  unknown: { fill: "#111827", stroke: "#94a3b8", color: "#e2e8f0" },
});

const SYMBOL_CLASS_NAMES = Object.freeze({
  function: "exportFunction",
  class: "exportClass",
  global: "exportGlobal",
  reexport: "exportReexport",
  missing: "exportMissing",
  dynamic: "exportDynamic",
  unknown: "exportUnknown",
});

export function buildExportContractMatrixDiagram(modules, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  mermaidIdCounter = 0;

  const moduleEntries = Array.from(moduleMap.entries())
    .map(([moduleId, record]) => createModuleExportEntry(moduleId, record))
    .filter(Boolean);

  if (moduleEntries.length === 0) {
    return {
      message: options.emptyContractsMessage ?? "Export contract metadata is not available in this CommandView artifact.",
    };
  }

  moduleEntries.sort((left, right) => left.moduleId.localeCompare(right.moduleId));

  const lines = ["graph TD"];
  lines.push(...buildClassDefinitions());

  moduleEntries.forEach((entry) => {
    const moduleNodeId = sanitizeMermaidId(`${entry.moduleId}_exports_group`);
    const moduleLabel = escapeMermaidLabel(formatModuleLabel(entry));
    lines.push(`  subgraph ${moduleNodeId}["${moduleLabel}"]`);

    entry.symbols.forEach((symbol, index) => {
      const nodeId = sanitizeMermaidId(`${entry.moduleId}_${symbol.symbolKey}_${index}`);
      lines.push(`    ${nodeId}["${escapeMermaidLabel(symbol.label)}"]`);
      lines.push(`    class ${nodeId} ${symbol.className};`);
    });

    if (entry.dynamicPlaceholder) {
      const placeholderId = sanitizeMermaidId(`${entry.moduleId}_dynamic_contract`);
      lines.push(`    ${placeholderId}["${escapeMermaidLabel(entry.dynamicPlaceholder.label)}"]`);
      lines.push(`    class ${placeholderId} ${SYMBOL_CLASS_NAMES.dynamic};`);
    }

    lines.push("  end");
  });

  const stats = buildStatsSnapshot(moduleEntries);
  const scopeLabel = resolveScopeLabel(options.rootId, options.domainId);
  const statusMessage = buildStatusMessage(stats, scopeLabel);

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    stats,
    statusDetails: buildStatusDetails(stats),
  };
}

function buildClassDefinitions() {
  return Object.entries(SYMBOL_STYLES).map(([kind, style]) =>
    `  classDef ${SYMBOL_CLASS_NAMES[kind]} fill:${style.fill},stroke:${style.stroke},color:${style.color},stroke-width:1.5px;`
  );
}

function createModuleExportEntry(moduleId, moduleRecord) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return null;
  }

  const summary = normalizeExportSummary(moduleRecord.exportSummary);
  if (!summary) {
    return null;
  }

  const normalizedSymbols = summary.resolved.map((symbol) => normalizeResolvedSymbol(symbol, moduleId)).filter(Boolean);

  const hasDeclaredSymbols = summary.counts.declared > 0 || normalizedSymbols.length > 0;
  const hasDynamicOnly = summary.dynamic && !hasDeclaredSymbols;
  if (!hasDeclaredSymbols && !hasDynamicOnly) {
    return null;
  }

  const symbols = normalizedSymbols.map((symbol) => ({
    symbol,
    symbolKey: symbol.symbolKey,
    label: formatSymbolNodeLabel(symbol),
    className: SYMBOL_CLASS_NAMES[symbol.kind] ?? SYMBOL_CLASS_NAMES.unknown,
    kind: symbol.kind,
  }));

  const dynamicPlaceholder = hasDynamicOnly
    ? {
        label: "Dynamic __all__\n(mutated at runtime)",
      }
    : null;

  return {
    moduleId,
    summary,
    symbols,
    dynamicPlaceholder,
  };
}

function normalizeExportSummary(summary) {
  if (!summary || typeof summary !== "object") {
    return null;
  }

  const declared = uniqueNormalizedStringList(summary.declared ?? summary.symbols ?? []);
  const missing = uniqueNormalizedStringList(summary.missing ?? []);
  const counts = normalizeCounts(summary.counts);
  const resolved = Array.isArray(summary.resolved) ? summary.resolved : [];

  return {
    declared,
    missing,
    counts,
    resolved,
    dynamic: summary.dynamic === true,
    hasDeclared: summary.hasDeclared === true || declared.length > 0,
  };
}

function normalizeResolvedSymbol(entry, moduleId) {
  if (!entry || typeof entry !== "object") {
    return null;
  }

  const symbolName = normalizeString(entry.symbol ?? entry.name ?? null);
  if (!symbolName) {
    return null;
  }

  const kind = resolveSymbolKind(entry);
  const origin = normalizeString(entry.origin) ?? (kind === "reexport" ? "reexport" : "local");
  const sourceModule = normalizeString(entry.sourceModule ?? entry.source_module ?? null);
  const sourceName = normalizeString(entry.sourceName ?? entry.source_name ?? null);

  return {
    symbol: symbolName,
    symbolKey: `${symbolName}_${kind}_${origin}_${sourceModule ?? "local"}`,
    kind,
    origin,
    moduleId,
    defined: entry.defined === true,
    valueKind: normalizeString(entry.valueKind ?? entry.value_kind ?? null),
    lineno: normalizeLineNumber(entry.lineno ?? entry.line ?? null),
    signature: normalizeString(entry.signature ?? null),
    docstringQuality: entry.docstringQuality ?? entry.docstring_quality ?? null,
    functionId: normalizeString(entry.functionId ?? entry.function_id ?? null),
    classQualifiedName: normalizeString(entry.classQualifiedName ?? entry.class_qualified_name ?? null),
    sourceModule,
    sourceName,
    sourceQualifiedName: normalizeString(entry.sourceQualifiedName ?? entry.source_qualified_name ?? null),
    sourceImportKind: normalizeString(entry.sourceImportKind ?? entry.source_import_kind ?? null),
    sourceLevel: normalizeLineNumber(entry.sourceLevel ?? entry.source_level ?? null),
  };
}

function resolveSymbolKind(entry) {
  const rawKind = normalizeString(entry.kind);
  if (rawKind && SYMBOL_CLASS_NAMES[rawKind]) {
    return rawKind;
  }
  if (entry.defined === false || rawKind === "missing") {
    return "missing";
  }
  if (normalizeString(entry.origin) === "reexport") {
    return "reexport";
  }
  return "unknown";
}

function formatModuleLabel(entry) {
  const parts = [entry.moduleId];
  const declaredCount = entry.summary.counts.declared;
  parts.push(`Exports ${declaredCount}`);
  if (entry.summary.counts.missing > 0) {
    parts.push(`${entry.summary.counts.missing} missing`);
  }
  if (entry.summary.dynamic) {
    parts.push("Dynamic __all__");
  }
  return parts.join("\n");
}

function formatSymbolNodeLabel(symbol) {
  const lines = [symbol.symbol];
  switch (symbol.kind) {
    case "function": {
      const signature = symbol.signature ?? null;
      const docstring = symbol.docstringQuality;
      lines.push("function");
      if (signature) {
        lines.push(signature);
      }
      if (docstring && typeof docstring === "object" && docstring.exists === false) {
        lines.push("no docstring");
      }
      break;
    }
    case "class": {
      lines.push("class");
      if (symbol.classQualifiedName) {
        lines.push(symbol.classQualifiedName);
      }
      break;
    }
    case "global": {
      const kind = symbol.valueKind ? `global · ${symbol.valueKind}` : "global";
      lines.push(kind);
      break;
    }
    case "reexport": {
      lines.push("re-export");
      if (symbol.sourceModule && symbol.sourceName) {
        lines.push(`from ${symbol.sourceModule}.${symbol.sourceName}`);
      } else if (symbol.sourceModule) {
        lines.push(`from ${symbol.sourceModule}`);
      }
      break;
    }
    case "missing": {
      lines.push("missing");
      break;
    }
    default: {
      lines.push("symbol");
      break;
    }
  }
  if (symbol.lineno) {
    lines.push(`line ${symbol.lineno}`);
  }
  return lines.join("\n");
}

function buildStatsSnapshot(entries) {
  const totals = {
    modules: entries.length,
    declaredSymbols: 0,
    localSymbols: 0,
    functions: 0,
    classes: 0,
    globals: 0,
    reexports: 0,
    missingSymbols: 0,
    dynamicModules: 0,
  };

  const modulesWithMissing = [];
  const dynamicOnlyModules = [];
  const reexportDetails = [];

  entries.forEach((entry) => {
    const counts = entry.summary.counts;
    totals.declaredSymbols += counts.declared;
    totals.localSymbols += counts.local;
    totals.functions += counts.functions;
    totals.classes += counts.classes;
    totals.globals += counts.globals;
    totals.reexports += counts.reexports;
    totals.missingSymbols += counts.missing;
    if (entry.summary.dynamic) {
      totals.dynamicModules += 1;
      if (!entry.summary.hasDeclared) {
        dynamicOnlyModules.push(entry.moduleId);
      }
    }

    if (counts.missing > 0) {
      modulesWithMissing.push({
        moduleId: entry.moduleId,
        count: counts.missing,
        symbols: entry.symbols.filter((symbol) => symbol.kind === "missing").map((symbol) => symbol.symbol.symbol),
      });
    }

    entry.symbols
      .filter((symbol) => symbol.kind === "reexport")
      .forEach((symbol) => {
        reexportDetails.push({
          moduleId: entry.moduleId,
          symbol: symbol.symbol.symbol,
          sourceModule: symbol.symbol.sourceModule,
          sourceName: symbol.symbol.sourceName,
        });
      });
  });

  modulesWithMissing.sort((left, right) => {
    if (right.count !== left.count) {
      return right.count - left.count;
    }
    return left.moduleId.localeCompare(right.moduleId);
  });

  const topReexports = reexportDetails
    .sort((left, right) => {
      if (left.moduleId !== right.moduleId) {
        return left.moduleId.localeCompare(right.moduleId);
      }
      return left.symbol.localeCompare(right.symbol);
    })
    .slice(0, MAX_REEXPORT_DETAILS);

  return {
    ...totals,
    modulesWithMissing: modulesWithMissing.slice(0, MAX_MISSING_DETAILS),
    dynamicOnlyModules,
    topReexports,
  };
}

function buildStatusMessage(stats, scopeLabel) {
  const suffixParts = [];
  if (stats.reexports > 0) {
    suffixParts.push(`${stats.reexports} re-export${stats.reexports === 1 ? "" : "s"}`);
  }
  if (stats.missingSymbols > 0) {
    suffixParts.push(`${stats.missingSymbols} missing symbol${stats.missingSymbols === 1 ? "" : "s"}`);
  }
  if (stats.dynamicModules > 0) {
    suffixParts.push(`${stats.dynamicModules} dynamic module${stats.dynamicModules === 1 ? "" : "s"}`);
  }
  const suffix = suffixParts.length > 0 ? `; ${suffixParts.join("; ")}` : "";
  return `Rendered Export Contract Matrix for ${scopeLabel} (${stats.modules} module${stats.modules === 1 ? "" : "s"}, ${stats.declaredSymbols} declared symbol${stats.declaredSymbols === 1 ? "" : "s"}${suffix}).`;
}

function buildStatusDetails(stats) {
  const descriptors = [];

  descriptors.push({
    type: "stat-summary",
    title: "Export Snapshot",
    items: [
      { label: "Modules", value: String(stats.modules) },
      { label: "Declared Symbols", value: String(stats.declaredSymbols) },
      { label: "Local Symbols", value: String(stats.localSymbols) },
      { label: "Re-exports", value: String(stats.reexports) },
      { label: "Missing Symbols", value: String(stats.missingSymbols) },
      { label: "Dynamic Modules", value: String(stats.dynamicModules) },
    ],
  });

  if (stats.modulesWithMissing.length > 0) {
    descriptors.push({
      type: "list",
      title: "Modules With Missing Exports",
      description: "Declared symbols not resolved locally.",
      items: stats.modulesWithMissing.map((entry) => ({
        header: `${entry.moduleId} (${entry.count})`,
        body: entry.symbols.slice(0, 5).join(", ") || null,
        badges: entry.symbols.length > 5 ? [`+${entry.symbols.length - 5} more`] : [],
      })),
    });
  }

  if (stats.topReexports.length > 0) {
    descriptors.push({
      type: "list",
      title: "Representative Re-exports",
      description: "Sample of symbols forwarded from other modules.",
      items: stats.topReexports.map((entry) => ({
        header: `${entry.moduleId} → ${entry.symbol}`,
        body: entry.sourceModule ? `from ${entry.sourceModule}${entry.sourceName ? `.${entry.sourceName}` : ""}` : null,
      })),
    });
  }

  if (stats.dynamicOnlyModules.length > 0) {
    descriptors.push({
      type: "pill-list",
      title: "Dynamic-only Modules",
      description: "Modules relying solely on runtime __all__ mutations.",
      items: stats.dynamicOnlyModules.sort((a, b) => a.localeCompare(b)),
    });
  }

  return descriptors;
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
      const key = entry.id ?? entry.moduleId ?? entry.module_id ?? null;
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

function uniqueNormalizedStringList(values) {
  if (!Array.isArray(values)) {
    return [];
  }
  const seen = new Set();
  const normalized = [];
  values.forEach((value) => {
    const normalizedValue = normalizeString(value);
    if (!normalizedValue || seen.has(normalizedValue)) {
      return;
    }
    seen.add(normalizedValue);
    normalized.push(normalizedValue);
  });
  return normalized;
}

function normalizeCounts(counts) {
  const base = {
    declared: 0,
    functions: 0,
    classes: 0,
    globals: 0,
    reexports: 0,
    missing: 0,
    local: 0,
  };
  if (!counts || typeof counts !== "object") {
    return base;
  }
  return {
    declared: toNumber(counts.declared, 0),
    functions: toNumber(counts.functions, 0),
    classes: toNumber(counts.classes, 0),
    globals: toNumber(counts.globals, 0),
    reexports: toNumber(counts.reexports, 0),
    missing: toNumber(counts.missing, 0),
    local: toNumber(counts.local, 0),
  };
}

function toNumber(value, fallback) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
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

function normalizeLineNumber(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function resolveScopeLabel(rootId, domainId) {
  if (domainId) {
    return `${domainId}`;
  }
  if (rootId) {
    return `${rootId}`;
  }
  return "repository";
}

export const __test__ = {
  buildClassDefinitions,
  createModuleExportEntry,
  normalizeExportSummary,
  normalizeResolvedSymbol,
  buildStatsSnapshot,
  buildStatusDetails,
  formatModuleLabel,
  formatSymbolNodeLabel,
  toModuleMap,
};
