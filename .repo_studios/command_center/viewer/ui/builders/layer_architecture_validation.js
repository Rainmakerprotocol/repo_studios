const DEFAULT_VIEW_LABEL = "Dependency · Layer Architecture Validation";

const NODE_CLASS_NAMES = Object.freeze({
  standard: "layerNode",
  violation: "layerNodeViolation",
  unclassified: "layerNodeUnclassified",
});

const EDGE_LABELS = Object.freeze({
  peer: "peer",
  forward: "forward",
  backward: "backward",
  skip: "skip",
  unclassified: "unclassified",
});

export function buildLayerArchitectureValidationDiagram(modules, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const evaluateTransition = typeof options.evaluateLayerTransition === "function" ? options.evaluateLayerTransition : null;
  if (!evaluateTransition) {
    return {
      message: options.missingEvaluatorMessage ?? "Layer adjacency evaluation is unavailable for this CommandView artifact.",
    };
  }

  mermaidIdCounter = 0;

  const scopeLabel = options.scopeDescription ?? resolveScopeLabel(options.rootId, options.domainId, options.moduleId);
  const fallbackNotice = normalizeString(options.fallbackNotice);

  const {
    orderedBuckets,
    nodeLookup,
    totalModules,
    unclassifiedModules,
  } = collectLayerBuckets(moduleMap);

  if (totalModules === 0) {
    return {
      message: options.emptyTierMessage ?? "No modules matched the layer classification rules for this scope.",
    };
  }

  const edgeResult = collectLayerEdges(moduleMap, nodeLookup, evaluateTransition);
  const definitionLines = buildMermaidDefinition(orderedBuckets, nodeLookup, edgeResult.edges, edgeResult.violationModules);

  const stats = buildStatsSnapshot({
    scopeLabel,
    totalModules,
    tierCount: orderedBuckets.length,
    orderedBuckets,
    edges: edgeResult.edges,
    violations: edgeResult.violations,
    violationModules: edgeResult.violationModules,
    unclassifiedModules,
    unresolvedTargets: edgeResult.unresolvedTargets,
    layerWarnings: edgeResult.layerWarnings,
  });

  let statusMessage = buildStatusMessage(stats);
  if (fallbackNotice) {
    statusMessage = `${statusMessage} ${fallbackNotice}`.trim();
  }

  const statusDetails = buildStatusDetails(stats, fallbackNotice);

  return {
    definition: definitionLines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    stats,
    statusDetails,
  };
}

function collectLayerBuckets(moduleMap) {
  const bucketsById = new Map();
  const nodeLookup = new Map();
  const unclassifiedModules = [];
  let totalModules = 0;

  moduleMap.forEach((record, moduleId) => {
    if (!record || typeof record !== "object" || !normalizeString(moduleId)) {
      return;
    }
    totalModules += 1;
    const layer = normalizeLayerInfo(record);
    if (layer.isUnclassified) {
      unclassifiedModules.push(moduleId);
    }

    let bucket = bucketsById.get(layer.id);
    if (!bucket) {
      bucket = {
        id: layer.id,
        label: layer.label,
        index: layer.index,
        modules: [],
      };
      bucketsById.set(layer.id, bucket);
    }

    const node = {
      moduleId,
      sanitizedId: sanitizeMermaidId(moduleId),
      label: formatModuleLabel(moduleId, record),
      layerId: layer.id,
      layerLabel: layer.label,
      layerIndex: layer.index,
      isUnclassified: layer.isUnclassified,
    };
    bucket.modules.push(node);
    nodeLookup.set(moduleId, node);
  });

  const orderedBuckets = Array.from(bucketsById.values())
    .sort((left, right) => {
      if (left.index === right.index) {
        return left.id.localeCompare(right.id);
      }
      return left.index - right.index;
    })
    .map((bucket) => {
      bucket.modules.sort((a, b) => a.moduleId.localeCompare(b.moduleId));
      return bucket;
    });

  return { orderedBuckets, nodeLookup, totalModules, unclassifiedModules };
}

function collectLayerEdges(moduleMap, nodeLookup, evaluateTransition) {
  const edges = [];
  const violations = [];
  const violationModules = new Set();
  const unresolvedTargets = new Set();
  const layerWarnings = [];
  const seenWarnings = new Set();

  moduleMap.forEach((record, moduleId) => {
    if (!record || typeof record !== "object") {
      return;
    }

    const warning = resolveLayerViolationHint(record?.dependencySummary?.violations?.layers);
    if (warning) {
      const key = `${moduleId}::warning`;
      if (!seenWarnings.has(key)) {
        layerWarnings.push({ moduleId, detail: warning });
        seenWarnings.add(key);
      }
    }

    const importEdges = Array.isArray(record.importEdges) ? record.importEdges : [];
    importEdges.forEach((edge) => {
      if (!edge || typeof edge !== "object") {
        return;
      }
      const category = normalizeKey(edge.category ?? edge.classification);
      if (category !== "internal") {
        return;
      }
      const targetId = normalizeString(edge.target ?? edge.module ?? edge.name ?? null);
      if (!targetId) {
        return;
      }

      const sourceNode = nodeLookup.get(moduleId);
      if (!sourceNode) {
        return;
      }

      const targetNode = nodeLookup.get(targetId);
      if (!targetNode) {
        unresolvedTargets.add(targetId);
        return;
      }

      const sourceRecord = moduleMap.get(moduleId) ?? null;
      const targetRecord = moduleMap.get(targetId) ?? null;
      const sourceLayer = normalizeLayerInfo(sourceRecord);
      const targetLayer = normalizeLayerInfo(targetRecord);

      const evaluation = evaluateTransition(sourceLayer.id, targetLayer.id) ?? {};
      const classification = normalizeClassification(evaluation.classification, sourceLayer, targetLayer);
      const allowed = evaluation.allowed !== false;
      const reason = normalizeString(evaluation.reason) ?? defaultReason(classification, allowed, sourceLayer, targetLayer);

      const edgeInfo = {
        sourceId: moduleId,
        targetId,
        sourceLayer,
        targetLayer,
        classification,
        allowed,
        reason,
        unused: edge.unused === true,
      };
      edges.push(edgeInfo);

      if (!allowed) {
        violations.push(edgeInfo);
        violationModules.add(moduleId);
        violationModules.add(targetId);
      }
    });
  });

  edges.sort((left, right) => {
    if (left.sourceId === right.sourceId) {
      if (left.targetId === right.targetId) {
        return left.classification.localeCompare(right.classification);
      }
      return left.targetId.localeCompare(right.targetId);
    }
    return left.sourceId.localeCompare(right.sourceId);
  });

  return { edges, violations, violationModules, unresolvedTargets, layerWarnings };
}

function buildMermaidDefinition(orderedBuckets, nodeLookup, edges, violationModules) {
  const lines = ["graph LR"];
  lines.push("  classDef layerNode fill:#0f172a,stroke:#38bdf8,color:#f8fafc,stroke-width:1.5px;");
  lines.push("  classDef layerNodeViolation fill:#7f1d1d,stroke:#f87171,color:#fee2e2,stroke-width:2.5px;");
  lines.push("  classDef layerNodeUnclassified fill:#1f2937,stroke:#f97316,color:#ffedd5,stroke-width:2px;");

  orderedBuckets.forEach((bucket) => {
    const subgraphId = sanitizeMermaidId(`layer_${bucket.id}`);
    lines.push(`  subgraph ${subgraphId}["${escapeMermaidLabel(formatLayerTitle(bucket))}"]`);
    bucket.modules.forEach((node) => {
      lines.push(`    ${node.sanitizedId}["${escapeMermaidLabel(node.label)}"]`);
    });
    lines.push("  end");
  });

  orderedBuckets.forEach((bucket) => {
    bucket.modules.forEach((node) => {
      const className = violationModules.has(node.moduleId)
        ? NODE_CLASS_NAMES.violation
        : node.isUnclassified
          ? NODE_CLASS_NAMES.unclassified
          : NODE_CLASS_NAMES.standard;
      lines.push(`  class ${node.sanitizedId} ${className};`);
    });
  });

  edges.forEach((edge) => {
    const sourceNode = nodeLookup.get(edge.sourceId);
    const targetNode = nodeLookup.get(edge.targetId);
    if (!sourceNode || !targetNode) {
      return;
    }
    const connector = resolveConnector(edge);
    const labelKey = EDGE_LABELS[edge.classification] ?? edge.classification ?? "";
    const labelSegment = labelKey ? `|${escapeMermaidLabel(labelKey)}|` : "";
    lines.push(`  ${sourceNode.sanitizedId} ${connector}${labelSegment} ${targetNode.sanitizedId}`);
  });

  return lines;
}

function buildStatsSnapshot(payload) {
  const violationBreakdown = payload.violations.reduce(
    (acc, edge) => {
      const key = edge.classification ?? "unknown";
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    },
    { backward: 0, skip: 0, forward: 0, peer: 0, unclassified: 0, unknown: 0 }
  );

  const tierDetails = payload.orderedBuckets.map((bucket) => ({
    id: bucket.id,
    label: bucket.label,
    index: bucket.index,
    moduleCount: bucket.modules.length,
    sampleModules: bucket.modules.slice(0, 5).map((node) => node.moduleId),
  }));

  return {
    scope: payload.scopeLabel ?? "repository",
    modules: payload.totalModules,
    tiers: payload.tierCount,
    violationEdges: payload.violations.length,
    violationBreakdown,
    unclassifiedModules: payload.unclassifiedModules,
    unresolvedTargets: Array.from(payload.unresolvedTargets ?? []),
    layerWarnings: payload.layerWarnings ?? [],
    tierDetails,
    violations: payload.violations,
  };
}

function buildStatusMessage(stats) {
  const suffixParts = [];
  if (stats.violationEdges > 0) {
    suffixParts.push(`${stats.violationEdges} violation edge${stats.violationEdges === 1 ? "" : "s"}`);
  } else {
    suffixParts.push("no adjacency violations");
  }
  if (stats.unclassifiedModules.length > 0) {
    suffixParts.push(`${stats.unclassifiedModules.length} unclassified module${stats.unclassifiedModules.length === 1 ? "" : "s"}`);
  }
  if (stats.unresolvedTargets.length > 0) {
    suffixParts.push(`${stats.unresolvedTargets.length} out-of-scope target${stats.unresolvedTargets.length === 1 ? "" : "s"}`);
  }
  const suffix = suffixParts.length > 0 ? `; ${suffixParts.join("; ")}` : "";
  return `Rendered Layer Architecture Validation for ${stats.scope} (${stats.modules} module${stats.modules === 1 ? "" : "s"} across ${stats.tiers} tier${stats.tiers === 1 ? "" : "s"}${suffix}).`;
}

function buildStatusDetails(stats, fallbackNotice) {
  const details = [];

  if (fallbackNotice) {
    details.push({
      type: "info",
      title: "Scope fallback applied",
      description: fallbackNotice,
    });
  }

  details.push({
    type: "stat-summary",
    title: "Layer Snapshot",
    items: [
      { label: "Modules", value: String(stats.modules ?? 0) },
      { label: "Tiers", value: String(stats.tiers ?? 0) },
      { label: "Violation Edges", value: String(stats.violationEdges ?? 0) },
      { label: "Unclassified Modules", value: String(stats.unclassifiedModules.length ?? 0) },
    ],
  });

  if (stats.violationEdges > 0) {
    details.push({
      type: "list",
      title: "Adjacency Violations",
      description: "Edges breaching default layer policy.",
      items: stats.violations.map((edge) => ({
        header: `${edge.sourceId} → ${edge.targetId}`,
        body: edge.reason,
        badges: buildViolationBadges(edge),
      })),
    });
  }

  if (stats.layerWarnings.length > 0) {
    details.push({
      type: "list",
      title: "Inventory Warnings",
      description: "Producer inventory flagged these modules for layer issues.",
      items: stats.layerWarnings.map((entry) => ({
        header: entry.moduleId,
        body: entry.detail,
      })),
    });
  }

  if (stats.unclassifiedModules.length > 0) {
    details.push({
      type: "pill-list",
      title: "Unclassified Modules",
      description: "Modules that did not match the default tier map.",
      items: stats.unclassifiedModules.slice(0, 15),
    });
  }

  if (stats.unresolvedTargets.length > 0) {
    details.push({
      type: "pill-list",
      title: "Out-of-scope Imports",
      description: "Targets referenced by scoped modules but missing from this selection.",
      items: stats.unresolvedTargets.slice(0, 15),
    });
  }

  if (Array.isArray(stats.tierDetails) && stats.tierDetails.length > 0) {
    details.push({
      type: "list",
      title: "Tier Coverage",
      description: "Module distribution per layer.",
      items: stats.tierDetails.map((tier) => ({
        header: tier.label,
        body: `${tier.moduleCount} module${tier.moduleCount === 1 ? "" : "s"}`,
        badges: tier.sampleModules.slice(0, 3),
      })),
    });
  }

  return details;
}

function buildViolationBadges(edge) {
  const badges = [];
  if (edge.classification) {
    badges.push(capitalize(edge.classification));
  }
  if (edge.sourceLayer && edge.targetLayer) {
    badges.push(`${edge.sourceLayer.label} → ${edge.targetLayer.label}`);
  }
  if (edge.unused) {
    badges.push("unused import");
  }
  return badges;
}

function resolveConnector(edge) {
  if (!edge.allowed) {
    return "--x";
  }
  if (edge.classification === "unclassified") {
    return "-.->";
  }
  return "-->";
}

function formatLayerTitle(bucket) {
  const count = bucket.modules.length;
  return `${bucket.label} (${count} module${count === 1 ? "" : "s"})`;
}

function formatModuleLabel(moduleId, record) {
  const parts = [moduleId];
  const relativePath = normalizeString(record?.relativePath ?? record?.relative_path ?? null);
  if (relativePath && relativePath !== moduleId) {
    parts.push(relativePath);
  }
  return parts.join("\\n");
}

function normalizeLayerInfo(record) {
  const tierId = normalizeKey(record?.layerTier ?? record?.layer_tier) ?? "unclassified";
  const indexRaw = record?.layerIndex ?? record?.layer_index;
  const indexValue = Number(indexRaw);
  const index = Number.isFinite(indexValue) ? indexValue : tierId === "unclassified" ? 99 : 0;
  const labelCandidate = normalizeString(record?.layerLabel ?? record?.layer_label ?? null);
  const label = labelCandidate ?? formatLayerLabelFromId(tierId);
  return {
    id: tierId,
    label,
    index,
    isUnclassified: tierId === "unclassified",
  };
}

function normalizeClassification(value, sourceLayer, targetLayer) {
  const normalized = normalizeKey(value);
  if (normalized) {
    return normalized;
  }
  if (!sourceLayer || !targetLayer) {
    return "unclassified";
  }
  const delta = targetLayer.index - sourceLayer.index;
  if (delta === 0) {
    return "peer";
  }
  if (delta === 1) {
    return "forward";
  }
  if (delta > 1) {
    return "skip";
  }
  return "backward";
}

function defaultReason(classification, allowed, sourceLayer, targetLayer) {
  if (allowed) {
    return `Transition from ${sourceLayer.label} to ${targetLayer.label} permitted by default adjacency rules.`;
  }
  return `Transition from ${sourceLayer.label} to ${targetLayer.label} violates default layer adjacency rules.`;
}

function resolveLayerViolationHint(value) {
  if (!value) {
    return null;
  }
  if (value === true) {
    return "Inventory flagged layer violations for this module.";
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }
  if (Array.isArray(value)) {
    const parts = value
      .map((entry) => normalizeString(entry))
      .filter((entry) => entry)
      .slice(0, 5);
    if (parts.length === 0) {
      return null;
    }
  const suffix = value.length > parts.length ? " ..." : "";
    return `${parts.join(", ")}${suffix}`;
  }
  if (typeof value === "object") {
    try {
      const serialized = JSON.stringify(value);
  return truncate(serialized, 140);
    } catch (error) {
      return "Inventory reported layer violations.";
    }
  }
  return null;
}

function truncate(value, maxLength) {
  if (!value || value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, Math.max(0, maxLength - 1))}...`;
}

function formatLayerLabelFromId(id) {
  if (!id) {
    return "Unclassified";
  }
  return id
    .split(/[_\-]+/)
    .map((segment) => capitalize(segment))
    .join(" ") || "Unclassified";
}

function capitalize(value) {
  const text = normalizeString(value);
  if (!text) {
    return "";
  }
  return text.charAt(0).toUpperCase() + text.slice(1);
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

function normalizeString(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const text = String(value).trim();
  return text.length > 0 ? text : null;
}

function normalizeKey(value) {
  const text = normalizeString(value);
  return text ? text.toLowerCase() : null;
}

function resolveScopeLabel(rootId, domainId, moduleId) {
  const moduleLabel = normalizeString(moduleId);
  if (moduleLabel) {
    return moduleLabel;
  }
  const domainLabel = normalizeString(domainId);
  if (domainLabel) {
    return domainLabel;
  }
  const rootLabel = normalizeString(rootId);
  if (rootLabel) {
    return rootLabel;
  }
  return "repository";
}
