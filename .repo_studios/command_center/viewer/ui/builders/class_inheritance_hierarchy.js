const DEFAULT_VIEW_LABEL = "Code Flow · Class Inheritance Hierarchy";

const NODE_STYLE_PALETTE = Object.freeze({
  local: Object.freeze({ fill: "#0f172a", stroke: "#38bdf8" }),
  project: Object.freeze({ fill: "#1f2937", stroke: "#22c55e" }),
  external: Object.freeze({ fill: "#111827", stroke: "#f97316" }),
  builtin: Object.freeze({ fill: "#111827", stroke: "#a855f7" }),
  placeholder: Object.freeze({ fill: "#101827", stroke: "#94a3b8" }),
});

export function buildClassInheritanceHierarchyDiagram(classes, options = {}) {
  const classMap = toMap(classes);
  if (!classMap || classMap.size === 0) {
    return {
      message: options.emptyMessage ?? "Class inheritance metadata is not available in this scope.",
    };
  }

  const primaryIds = buildIdSet(options.primaryClassIds).filter((classId) => classMap.has(classId));
  const primarySet = new Set(primaryIds);

  const derivedLookup = buildDerivedLookup(classMap);

  const nodeEntries = [];
  const classNodeIds = new Map();

  classMap.forEach((record, classId) => {
    if (!record || typeof record !== "object" || !classId) {
      return;
    }
    const nodeId = sanitizeMermaidId(classId);
    classNodeIds.set(classId, nodeId);
    nodeEntries.push({
      nodeId,
      classes: buildClassNodeClasses(classId, primarySet),
      label: buildClassLabel(record, derivedLookup.get(classId) ?? new Set(), classMap),
      sortKey: classId,
    });
  });

  nodeEntries.sort((left, right) => left.sortKey.localeCompare(right.sortKey));

  const placeholderNodes = new Map();
  const edges = [];
  let externalBaseReferences = 0;
  let builtinBaseReferences = 0;

  classMap.forEach((record, classId) => {
    const sourceId = classNodeIds.get(classId);
    if (!sourceId) {
      return;
    }
    const resolvedBases = Array.isArray(record?.resolvedBases) ? record.resolvedBases : [];
    resolvedBases.forEach((base) => {
      if (!base || typeof base !== "object") {
        return;
      }
      const matchType = base.matchType ?? "external";
      if (base.classId && classNodeIds.has(base.classId)) {
        const targetId = classNodeIds.get(base.classId);
        if (targetId && targetId !== sourceId) {
          edges.push({ source: sourceId, target: targetId, style: "solid", sortKey: `${sourceId}->${targetId}` });
        }
        return;
      }

      const placeholder = ensurePlaceholderNode(base, placeholderNodes);
      if (!placeholder) {
        return;
      }

      if (matchType === "external" || matchType === "unknown") {
        externalBaseReferences += 1;
      } else if (matchType === "builtin") {
        builtinBaseReferences += 1;
      }

      edges.push({ source: sourceId, target: placeholder.nodeId, style: "dashed", sortKey: `${sourceId}->${placeholder.nodeId}` });
    });
  });

  const placeholderEntries = Array.from(placeholderNodes.values()).sort((left, right) =>
    left.sortKey.localeCompare(right.sortKey)
  );

  const lines = ["graph TD"];
  appendClassDefinitions(lines);

  nodeEntries.forEach((entry) => {
    lines.push(`  ${entry.nodeId}["${escapeMermaidLabel(entry.label)}"]`);
  });
  placeholderEntries.forEach((entry) => {
    lines.push(`  ${entry.nodeId}["${escapeMermaidLabel(entry.label)}"]`);
  });

  nodeEntries.forEach((entry) => {
    if (entry.classes.length > 0) {
      lines.push(`  class ${entry.nodeId} ${entry.classes.join(",")};`);
    }
  });
  placeholderEntries.forEach((entry) => {
    if (entry.classes.length > 0) {
      lines.push(`  class ${entry.nodeId} ${entry.classes.join(",")};`);
    }
  });

  edges
    .sort((left, right) => left.sortKey.localeCompare(right.sortKey))
    .forEach((edge) => {
      const connector = edge.style === "dashed" ? "-.->" : "-->";
      lines.push(`  ${edge.source} ${connector} ${edge.target}`);
    });

  const scopeDescription = options.scopeDescription ?? "repository";
  const stats = buildStats(classMap, derivedLookup, edges.length, placeholderEntries.length, externalBaseReferences, builtinBaseReferences);

  const statusMessage = buildStatusMessage(scopeDescription, stats, options.fallbackNotice);
  const statusDetails = buildStatusDetails({
    scopeDescription,
    fallbackNotice: options.fallbackNotice,
    placeholderEntries,
    primarySet,
    classMap,
  });

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    statusDetails,
    stats,
  };
}

function buildIdSet(candidate) {
  if (!candidate) {
    return [];
  }
  if (candidate instanceof Set) {
    return Array.from(candidate.values());
  }
  if (Array.isArray(candidate)) {
    return candidate.filter((value) => typeof value === "string" && value.length > 0);
  }
  return [];
}

function buildDerivedLookup(classMap) {
  const lookup = new Map();
  classMap.forEach((record) => {
    const bases = Array.isArray(record?.resolvedBases) ? record.resolvedBases : [];
    bases.forEach((base) => {
      if (!base || typeof base !== "object" || !base.classId || !classMap.has(base.classId)) {
        return;
      }
      const existing = lookup.get(base.classId) ?? new Set();
      existing.add(record.id);
      lookup.set(base.classId, existing);
    });
  });
  return lookup;
}

function buildClassNodeClasses(classId, primarySet) {
  const classes = [];
  if (primarySet.has(classId)) {
    classes.push("local");
  } else {
    classes.push("project");
  }
  return classes;
}

function buildClassLabel(record, derivedSet, classMap) {
  const lines = [];
  const identifier = typeof record?.id === "string" ? record.id : record?.name;
  lines.push(identifier ?? "Class");

  const methodCount = Number.isFinite(Number(record?.methodCount))
    ? Number(record.methodCount)
    : Array.isArray(record?.methods)
    ? record.methods.length
    : 0;
  if (methodCount > 0) {
    lines.push(`Methods: ${methodCount}`);
  }

  const attributeCount = Number.isFinite(Number(record?.attributeCount))
    ? Number(record.attributeCount)
    : Array.isArray(record?.attributes)
    ? record.attributes.length
    : 0;
  if (attributeCount > 0) {
    lines.push(`Attributes: ${attributeCount}`);
  }

  const derivedCount = derivedSet.size;
  if (derivedCount > 0) {
    lines.push(`Derived: ${derivedCount}`);
  }

  const resolvedBases = Array.isArray(record?.resolvedBases) ? record.resolvedBases : [];
  const hasInternalBase = resolvedBases.some((base) => base?.classId && classMap.has(base.classId));
  if (!hasInternalBase) {
    lines.push("Root Class");
  }

  const docstringQuality = record?.docstringQuality;
  if (docstringQuality && typeof docstringQuality === "object" && docstringQuality.exists === false) {
    lines.push("Docstring: missing");
  }

  const codeSmells = Array.isArray(record?.codeSmells) ? record.codeSmells : [];
  if (codeSmells.length > 0) {
    lines.push(`Smells: ${codeSmells.length}`);
  }

  return lines.join("\n");
}

function ensurePlaceholderNode(base, placeholderNodes) {
  const normalized = typeof base?.normalized === "string" ? base.normalized : null;
  const raw = typeof base?.raw === "string" ? base.raw : null;
  const key = `${normalized ?? raw ?? "__unknown"}|${base?.matchType ?? "external"}`;
  if (placeholderNodes.has(key)) {
    return placeholderNodes.get(key);
  }

  const matchType = base?.matchType ?? "external";
  const labelParts = [];
  const displayName = normalized ?? raw ?? "Unknown Base";
  labelParts.push(displayName);
  if (matchType === "builtin") {
    labelParts.push("Builtin Base");
  } else if (matchType === "external") {
    labelParts.push("External Base");
  } else {
    labelParts.push("Unresolved Base");
  }

  const nodeId = sanitizeMermaidId(`placeholder.${key}`);
  const classes = ["placeholder"];
  if (matchType === "builtin") {
    classes.push("builtin");
  } else {
    classes.push("external");
  }

  const entry = {
    nodeId,
    label: labelParts.join("\n"),
    classes,
    sortKey: displayName,
    matchType,
  };
  placeholderNodes.set(key, entry);
  return entry;
}

function buildStats(classMap, derivedLookup, edgeCount, placeholderCount, externalBaseReferences, builtinBaseReferences) {
  let rootClasses = 0;
  let leafClasses = 0;

  classMap.forEach((record, classId) => {
    const resolvedBases = Array.isArray(record?.resolvedBases) ? record.resolvedBases : [];
    const hasInternalBase = resolvedBases.some((base) => base?.classId && classMap.has(base.classId));
    if (!hasInternalBase) {
      rootClasses += 1;
    }

    const derivedSet = derivedLookup.get(classId);
    if (!derivedSet || derivedSet.size === 0) {
      leafClasses += 1;
    }
  });

  return {
    classCount: classMap.size,
    rootClasses,
    leafClasses,
    edgeCount,
    placeholderCount,
    externalBaseReferences,
    builtinBaseReferences,
    moduleCount: countUniqueModules(classMap),
  };
}

function countUniqueModules(classMap) {
  const modules = new Set();
  classMap.forEach((record) => {
    if (record?.moduleId) {
      modules.add(record.moduleId);
    }
  });
  return modules.size;
}

function buildStatusMessage(scopeDescription, stats, fallbackNotice) {
  const base = `Rendered Class Inheritance Hierarchy for ${scopeDescription} (${stats.classCount} classes, ${stats.rootClasses} roots, ${stats.leafClasses} leaves).`;
  if (!fallbackNotice) {
    return base;
  }
  return `${base} ${fallbackNotice}`.trim();
}

function buildStatusDetails({ scopeDescription, fallbackNotice, placeholderEntries, primarySet, classMap }) {
  const details = [];

  if (fallbackNotice) {
    details.push({
      type: "info",
      title: "Scope fallback applied",
      description: fallbackNotice,
    });
  }

  const moduleItems = buildModuleItems(classMap, primarySet);
  if (moduleItems.length > 0) {
    details.push({
      type: "list",
      title: "Module Distribution",
      description: `Scoped to ${scopeDescription}`,
      items: moduleItems,
    });
  }

  const unresolvedItems = placeholderEntries.map((entry) => ({
    label: entry.sortKey,
    value:
      entry.matchType === "builtin"
        ? "Builtin base referenced by scoped classes"
        : "External base referenced by scoped classes",
  }));

  if (unresolvedItems.length > 0) {
    details.push({
      type: "list",
      title: "Unresolved Bases",
      description: "These bases were not found within the normalized class set.",
      items: unresolvedItems,
    });
  }

  return details;
}

function buildModuleItems(classMap, primarySet) {
  const modules = new Map();
  classMap.forEach((record, classId) => {
    const moduleId = typeof record?.moduleId === "string" ? record.moduleId : "<unknown>";
    const entry = modules.get(moduleId) ?? { total: 0, focused: 0 };
    entry.total += 1;
    if (primarySet.has(classId)) {
      entry.focused += 1;
    }
    modules.set(moduleId, entry);
  });

  return Array.from(modules.entries())
    .map(([moduleId, counts]) => ({
      label: moduleId,
      value: `Classes: ${counts.total}${counts.focused > 0 ? ` · Focused: ${counts.focused}` : ""}`,
    }))
    .sort((left, right) => left.label.localeCompare(right.label));
}

function toMap(candidate) {
  if (!candidate) {
    return null;
  }
  if (candidate instanceof Map) {
    return candidate;
  }
  if (Array.isArray(candidate)) {
    const map = new Map();
    candidate.forEach((entry) => {
      if (!entry || typeof entry !== "object" || typeof entry.id !== "string") {
        return;
      }
      map.set(entry.id, entry);
    });
    return map;
  }
  return null;
}

function sanitizeMermaidId(identifier) {
  const base = typeof identifier === "string" ? identifier : String(identifier ?? "node");
  return base
    .replace(/[^a-zA-Z0-9_]/g, "_")
    .replace(/_{2,}/g, "_")
    .replace(/^_+/, "")
    .replace(/_+$/, "")
    .replace(/^$/, "node");
}

function escapeMermaidLabel(label) {
  if (typeof label !== "string" || label.length === 0) {
    return "";
  }
  return label.replace(/"/g, '\\"');
}

function appendClassDefinitions(lines) {
  lines.push(
    `  classDef local fill:${NODE_STYLE_PALETTE.local.fill},stroke:${NODE_STYLE_PALETTE.local.stroke},color:#f8fafc;`
  );
  lines.push(
    `  classDef project fill:${NODE_STYLE_PALETTE.project.fill},stroke:${NODE_STYLE_PALETTE.project.stroke},color:#f8fafc;`
  );
  lines.push(
    `  classDef external fill:${NODE_STYLE_PALETTE.external.fill},stroke:${NODE_STYLE_PALETTE.external.stroke},color:#f8fafc;`
  );
  lines.push(
    `  classDef builtin fill:${NODE_STYLE_PALETTE.builtin.fill},stroke:${NODE_STYLE_PALETTE.builtin.stroke},color:#f8fafc;`
  );
  lines.push(
    `  classDef placeholder fill:${NODE_STYLE_PALETTE.placeholder.fill},stroke:${NODE_STYLE_PALETTE.placeholder.stroke},color:#f8fafc;`
  );
}
