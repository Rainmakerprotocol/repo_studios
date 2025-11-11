const DEFAULT_VIEW_LABEL = "Dependency · Circular Import Detection";
const MAX_LIST_ITEMS = 10;

const NODE_STYLES = Object.freeze({
  anchor: { fill: "#0f172a", stroke: "#f97316", color: "#f8fafc" },
  participant: { fill: "#1f2937", stroke: "#38bdf8", color: "#f8fafc" },
  selfLoop: { fill: "#7f1d1d", stroke: "#f87171", color: "#fee2e2" },
});

export function buildCircularImportDetectionDiagram(modules, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const adjacency = buildAdjacency(moduleMap);
  const cycleComponents = findCycleComponents(adjacency);

  if (cycleComponents.length === 0) {
    return {
      message:
        options.emptyCyclesMessage ??
        `No circular imports detected for ${options.scopeDescription ?? "repository"}.`,
    };
  }

  const stats = buildStatsSnapshot({ moduleMap, cycles: cycleComponents });

  const lines = ["graph TD"];
  lines.push(
    `  classDef cycleAnchor fill:${NODE_STYLES.anchor.fill},stroke:${NODE_STYLES.anchor.stroke},color:${NODE_STYLES.anchor.color},stroke-width:2.5px;`,
  );
  lines.push(
    `  classDef cycleParticipant fill:${NODE_STYLES.participant.fill},stroke:${NODE_STYLES.participant.stroke},color:${NODE_STYLES.participant.color},stroke-width:2px;`,
  );
  lines.push(
    `  classDef cycleSelfLoop fill:${NODE_STYLES.selfLoop.fill},stroke:${NODE_STYLES.selfLoop.stroke},color:${NODE_STYLES.selfLoop.color},stroke-width:2.5px;`,
  );

  const nodeIdMap = new Map();

  cycleComponents.forEach((component, index) => {
    const cycleLabel = `Cycle ${index + 1} (length ${component.nodes.length})`;
    const subgraphId = sanitizeMermaidId(`cycle_${index + 1}`);
    lines.push(`  subgraph ${subgraphId} [${escapeMermaidLabel(cycleLabel)}]`);

    component.nodes.forEach((moduleId, nodeIndex) => {
      const sanitized = ensureNodeId(nodeIdMap, moduleId);
      const label = escapeMermaidLabel(moduleId);
      lines.push(`    ${sanitized}["${label}"]`);
      const className = resolveNodeClass(component, nodeIndex);
      lines.push(`    class ${sanitized} ${className};`);
    });

    component.edges.forEach((edge) => {
      const sourceId = ensureNodeId(nodeIdMap, edge.source);
      const targetId = ensureNodeId(nodeIdMap, edge.target);
      lines.push(`    ${sourceId} --> ${targetId}`);
    });

    lines.push("  end");
  });

  const scopeLabel = options.scopeDescription ?? "repository";
  const statusMessage = buildStatusMessage(stats, scopeLabel);
  const statusDetails = buildStatusDetails(stats, options.fallbackNotice);

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    stats,
    statusDetails,
  };
}

function buildAdjacency(moduleMap) {
  const adjacency = new Map();
  moduleMap.forEach((moduleRecord, moduleId) => {
    const importEdges = Array.isArray(moduleRecord?.importEdges) ? moduleRecord.importEdges : [];
    const targets = new Set();
    let hasSelfLoop = false;

    importEdges.forEach((edge) => {
      if (!edge || typeof edge !== "object") {
        return;
      }
      const target = resolveInternalTarget(normalizeString(edge.target ?? edge.module ?? null), moduleMap);
      if (!target) {
        return;
      }
      if (target === moduleId) {
        hasSelfLoop = true;
        return;
      }
      targets.add(target);
    });

    adjacency.set(moduleId, { targets, hasSelfLoop });
  });

  moduleMap.forEach((_record, moduleId) => {
    if (!adjacency.has(moduleId)) {
      adjacency.set(moduleId, { targets: new Set(), hasSelfLoop: false });
    }
  });

  return adjacency;
}

function findCycleComponents(adjacency) {
  const indexMap = new Map();
  const lowLinkMap = new Map();
  const onStack = new Set();
  const stack = [];
  let index = 0;
  const components = [];

  const nodes = Array.from(adjacency.keys()).sort((a, b) => a.localeCompare(b));

  const strongConnect = (node) => {
    indexMap.set(node, index);
    lowLinkMap.set(node, index);
    index += 1;
    stack.push(node);
    onStack.add(node);

    const adjacencyEntry = adjacency.get(node);
    const neighbors = adjacencyEntry ? Array.from(adjacencyEntry.targets).sort((a, b) => a.localeCompare(b)) : [];

    neighbors.forEach((neighbor) => {
      if (!indexMap.has(neighbor)) {
        strongConnect(neighbor);
        const neighborLow = lowLinkMap.get(neighbor);
        const currentLow = lowLinkMap.get(node);
        lowLinkMap.set(node, Math.min(currentLow, neighborLow));
      } else if (onStack.has(neighbor)) {
        const neighborIndex = indexMap.get(neighbor);
        const currentLow = lowLinkMap.get(node);
        lowLinkMap.set(node, Math.min(currentLow, neighborIndex));
      }
    });

    if (lowLinkMap.get(node) === indexMap.get(node)) {
      const componentNodes = [];
      let componentSelfLoop = adjacencyEntry?.hasSelfLoop === true;
      let popped;
      do {
        popped = stack.pop();
        onStack.delete(popped);
        componentNodes.push(popped);
        if (adjacency.get(popped)?.hasSelfLoop) {
          componentSelfLoop = true;
        }
      } while (popped !== node);

      componentNodes.sort((a, b) => a.localeCompare(b));

      const qualifies = componentNodes.length > 1 || (componentNodes.length === 1 && componentSelfLoop);
      if (!qualifies) {
        return;
      }

      const nodeSet = new Set(componentNodes);
      const edges = [];
      let observedSelfLoop = false;

      componentNodes.forEach((source) => {
        const entry = adjacency.get(source);
        if (!entry) {
          return;
        }
        if (entry.hasSelfLoop && nodeSet.has(source)) {
          edges.push({ source, target: source });
          observedSelfLoop = true;
        }
        entry.targets.forEach((target) => {
          if (nodeSet.has(target)) {
            edges.push({ source, target });
          }
        });
      });

      edges.sort((left, right) => {
        if (left.source === right.source) {
          return left.target.localeCompare(right.target);
        }
        return left.source.localeCompare(right.source);
      });

      const packages = new Set();
      componentNodes.forEach((moduleId) => {
        const pkg = moduleId.split(".")[0] ?? moduleId;
        if (pkg) {
          packages.add(pkg);
        }
      });

      components.push({
        nodes: componentNodes,
        edges,
        hasSelfLoop: observedSelfLoop || componentSelfLoop,
        packages: Array.from(packages).sort((a, b) => a.localeCompare(b)),
      });
    }
  };

  nodes.forEach((node) => {
    if (!indexMap.has(node)) {
      strongConnect(node);
    }
  });

  components.sort((left, right) => {
    if (right.nodes.length !== left.nodes.length) {
      return right.nodes.length - left.nodes.length;
    }
    const leftKey = left.nodes.join("->");
    const rightKey = right.nodes.join("->");
    return leftKey.localeCompare(rightKey);
  });

  return components;
}

function buildStatsSnapshot(payload) {
  const participating = new Set();
  let maxLength = 0;
  let selfLoops = 0;
  let twoNode = 0;
  let medium = 0;
  let large = 0;

  const cycles = payload.cycles.map((cycle, index) => {
    cycle.nodes.forEach((node) => participating.add(node));
    maxLength = Math.max(maxLength, cycle.nodes.length);
    if (cycle.nodes.length === 1) {
      selfLoops += 1;
    } else if (cycle.nodes.length === 2) {
      twoNode += 1;
    } else if (cycle.nodes.length <= 5) {
      medium += 1;
    } else {
      large += 1;
    }

    return {
      id: index + 1,
      label: `Cycle ${index + 1}`,
      nodes: cycle.nodes,
      edges: cycle.edges.length,
      length: cycle.nodes.length,
      hasSelfLoop: cycle.hasSelfLoop,
      packages: cycle.packages,
    };
  });

  return {
    scopedModules: payload.moduleMap.size,
    cycleCount: payload.cycles.length,
    participatingModules: participating.size,
    maxLength,
    buckets: {
      selfLoops,
      twoNode,
      medium,
      large,
    },
    cycles,
  };
}

function buildStatusMessage(stats, scopeLabel) {
  const cycleDescriptor = `${stats.cycleCount} import cycle${stats.cycleCount === 1 ? "" : "s"}`;
  const modulesDescriptor = `${stats.participatingModules} module${stats.participatingModules === 1 ? "" : "s"}`;
  const bucketHints = [];
  if (stats.buckets.large > 0) {
    bucketHints.push(`${stats.buckets.large} large`);
  }
  if (stats.buckets.medium > 0) {
    bucketHints.push(`${stats.buckets.medium} mid-sized`);
  }
  if (stats.buckets.twoNode > 0) {
    bucketHints.push(`${stats.buckets.twoNode} pairs`);
  }
  if (stats.buckets.selfLoops > 0) {
    bucketHints.push(`${stats.buckets.selfLoops} self-loop${stats.buckets.selfLoops === 1 ? "" : "s"}`);
  }
  const bucketSuffix = bucketHints.length > 0 ? `; ${bucketHints.join(", ")}` : "";
  return `Detected ${cycleDescriptor} within ${scopeLabel} (scanned ${stats.scopedModules} modules; ${modulesDescriptor} involved${bucketSuffix}).`;
}

function buildStatusDetails(stats, fallbackNotice) {
  const descriptors = [];

  if (fallbackNotice) {
    descriptors.push({
      type: "info",
      title: "Scope fallback applied",
      description: fallbackNotice,
    });
  }

  descriptors.push({
    type: "stat-summary",
    title: "Cycle Snapshot",
    items: [
      { label: "Cycles", value: String(stats.cycleCount) },
      { label: "Modules In Scope", value: String(stats.scopedModules) },
      { label: "Modules In Cycles", value: String(stats.participatingModules) },
      { label: "Max Length", value: String(stats.maxLength) },
    ],
  });

  const bucketItems = [];
  if (stats.buckets.selfLoops > 0) {
    bucketItems.push(`Self loops (${stats.buckets.selfLoops})`);
  }
  if (stats.buckets.twoNode > 0) {
    bucketItems.push(`Pairs (${stats.buckets.twoNode})`);
  }
  if (stats.buckets.medium > 0) {
    bucketItems.push(`Length 3–5 (${stats.buckets.medium})`);
  }
  if (stats.buckets.large > 0) {
    bucketItems.push(`Length >5 (${stats.buckets.large})`);
  }
  if (bucketItems.length > 0) {
    descriptors.push({
      type: "pill-list",
      title: "Cycle Size Buckets",
      description: "Distribution of cycle lengths in the current scope.",
      items: bucketItems,
    });
  }

  const listItems = stats.cycles.slice(0, MAX_LIST_ITEMS).map((cycle) => ({
    header: `${cycle.label} · ${cycle.length} module${cycle.length === 1 ? "" : "s"}`,
    body: formatCycleBody(cycle),
    badges: cycle.hasSelfLoop ? ["self-loop"] : [],
  }));

  descriptors.push({
    type: "list",
    title: "Cycle Breakdown",
    description: "Strongly connected module groups forming import loops.",
    items: listItems,
  });

  if (stats.cycles.length > MAX_LIST_ITEMS) {
    const remaining = stats.cycles.length - MAX_LIST_ITEMS;
    descriptors.push({
      type: "info",
      title: "Additional cycles truncated",
      description: `${remaining} further cycle${remaining === 1 ? "" : "s"} omitted for brevity.`,
    });
  }

  return descriptors;
}

function formatCycleBody(cycle) {
  const nodeSequence = cycle.nodes.join(" → ");
  const packageHint = cycle.packages.length > 1 ? `across ${cycle.packages.length} packages` : cycle.packages[0] ?? "";
  const edgeHint = `${cycle.edges} edge${cycle.edges === 1 ? "" : "s"}`;
  const hints = [edgeHint];
  if (packageHint) {
    hints.push(packageHint);
  }
  return `${nodeSequence}\n${hints.join(" · ")}`;
}

function resolveNodeClass(component, nodeIndex) {
  if (component.nodes.length === 1) {
    return component.hasSelfLoop ? "cycleSelfLoop" : "cycleParticipant";
  }
  return nodeIndex === 0 ? "cycleAnchor" : "cycleParticipant";
}

function ensureNodeId(map, moduleId) {
  if (map.has(moduleId)) {
    return map.get(moduleId);
  }
  const sanitized = sanitizeMermaidId(moduleId);
  map.set(moduleId, sanitized);
  return sanitized;
}

function resolveInternalTarget(target, moduleMap) {
  if (!target) {
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

export const __test__ = {
  buildAdjacency,
  findCycleComponents,
  buildStatsSnapshot,
  buildStatusMessage,
  buildStatusDetails,
  resolveNodeClass,
  resolveInternalTarget,
  sanitizeMermaidId,
};