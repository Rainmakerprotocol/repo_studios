const DEFAULT_VIEW_LABEL = "Event Dynamics · Callback Registration Map";

export function buildCallbackRegistrationMapDiagram(modules, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "Module metadata has not been normalized for this CommandView artifact.",
    };
  }

  const summary = collectRegistrations(moduleMap);
  if (summary.registrations === 0) {
    return {
      message: options.emptyMessage ?? "No callback registrations recorded for this CommandView artifact.",
    };
  }

  const stats = buildStats(summary);

  mermaidIdCounter = 0;

  const lines = ["graph TD"];
  appendClassDefinitions(lines);

  const emitterNodes = buildEmitterNodes(summary.emitters);
  const targetNodes = buildTargetNodes(summary.targets);

  const emitterNodeMap = new Map();
  emitterNodes.forEach((node) => {
    emitterNodeMap.set(node.key, node);
    lines.push(`  ${node.nodeId}["${escapeMermaidLabel(node.label)}"]`);
    lines.push(`  class ${node.nodeId} emitter;`);
  });

  const targetNodeMap = new Map();
  targetNodes.forEach((node) => {
    targetNodeMap.set(node.key, node);
    lines.push(`  ${node.nodeId}["${escapeMermaidLabel(node.label)}"]`);
    lines.push(`  class ${node.nodeId} ${node.classes.join(" ")};`);
  });

  const edges = Array.from(summary.edges.values()).sort((left, right) => {
    if (left.emitterKey === right.emitterKey) {
      if (left.targetKey === right.targetKey) {
        return left.channel.localeCompare(right.channel);
      }
      return left.targetKey.localeCompare(right.targetKey);
    }
    return left.emitterKey.localeCompare(right.emitterKey);
  });

  edges.forEach((edge) => {
    const emitterNode = emitterNodeMap.get(edge.emitterKey);
    const targetNode = targetNodeMap.get(edge.targetKey);
    if (!emitterNode || !targetNode) {
      return;
    }
    const label = edge.count > 1 ? `${edge.channel} (${edge.count})` : edge.channel;
    lines.push(`  ${emitterNode.nodeId} -->|${escapeMermaidLabel(label)}| ${targetNode.nodeId}`);
  });

  let statusMessage = buildStatusMessage(stats, options.scopeDescription ?? "repository");
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
    statusDetails,
    stats,
  };
}

function collectRegistrations(moduleMap) {
  const modules = new Map();
  const emitters = new Map();
  const targets = new Map();
  const edges = new Map();

  let registrations = 0;
  let unresolvedTargets = 0;

  const targetKindCounts = new Map();
  const channelCounts = new Map();

  const sequence = { value: 0 };

  moduleMap.forEach((moduleRecord, moduleId) => {
    const callbacks = Array.isArray(moduleRecord?.callbackRegistrations)
      ? moduleRecord.callbackRegistrations
      : [];

    if (callbacks.length === 0) {
      return;
    }

    const moduleSummary = {
      moduleId,
      registrations: 0,
      unresolved: 0,
      emitters: new Set(),
      targetKinds: new Map(),
    };
    modules.set(moduleId, moduleSummary);

    callbacks.forEach((registration) => {
      if (!registration || typeof registration !== "object") {
        return;
      }

      const emitterKey = resolveEmitterKey(moduleId, registration);
      if (!emitterKey) {
        return;
      }

      const targetKey = resolveTargetKey(registration, moduleId, sequence);
      if (!targetKey) {
        return;
      }

      const channel = resolveChannelLabel(registration);
      const targetKind = normalizeTargetKind(registration.targetKind);

      registrations += 1;

      const emitterEntry = ensureEmitterEntry(emitters, emitterKey, moduleId, registration);
      emitterEntry.registrations += 1;
      emitterEntry.targets.add(targetKey);
      emitterEntry.channels.add(channel);
      if (registration.method) {
        const normalizedMethod = normalizeString(registration.method);
        if (normalizedMethod) {
          emitterEntry.methods.set(normalizedMethod, (emitterEntry.methods.get(normalizedMethod) ?? 0) + 1);
        }
      }
      if (registration.lineno !== undefined && registration.lineno !== null) {
        const line = Number(registration.lineno);
        if (Number.isFinite(line)) {
          emitterEntry.lines.add(line);
        }
      }

      const targetEntry = ensureTargetEntry(targets, targetKey, registration);
      targetEntry.registrations += 1;
      targetEntry.modules.add(moduleId);
      targetEntry.via.set(channel, (targetEntry.via.get(channel) ?? 0) + 1);

      targetKindCounts.set(targetKind, (targetKindCounts.get(targetKind) ?? 0) + 1);
      channelCounts.set(channel, (channelCounts.get(channel) ?? 0) + 1);

      moduleSummary.registrations += 1;
      moduleSummary.emitters.add(emitterKey);
      moduleSummary.targetKinds.set(targetKind, (moduleSummary.targetKinds.get(targetKind) ?? 0) + 1);

      if (!(registration.target || registration.resolved)) {
        targetEntry.unresolved = true;
        moduleSummary.unresolved += 1;
        unresolvedTargets += 1;
      }

      const edgeKey = `${emitterKey}->${targetKey}::${channel}`;
      const edgeEntry = edges.get(edgeKey) ?? {
        emitterKey,
        targetKey,
        channel,
        count: 0,
      };
      edgeEntry.count += 1;
      edges.set(edgeKey, edgeEntry);
    });
  });

  return {
    modules,
    emitters,
    targets,
    edges,
    registrations,
    unresolvedTargets,
    targetKindCounts,
    channelCounts,
  };
}

function buildStats(summary) {
  const topEmitters = Array.from(summary.emitters.values())
    .map((entry) => ({
      name: entry.functionName ?? entry.key,
      moduleId: entry.moduleId,
      registrations: entry.registrations,
      targets: entry.targets.size,
      channels: Array.from(entry.channels.values()),
    }))
    .sort((left, right) => {
      if (right.registrations !== left.registrations) {
        return right.registrations - left.registrations;
      }
      if (left.moduleId === right.moduleId) {
        return left.name.localeCompare(right.name);
      }
      return left.moduleId.localeCompare(right.moduleId);
    })
    .slice(0, 10);

  const moduleBreakdown = Array.from(summary.modules.values())
    .map((entry) => ({
      moduleId: entry.moduleId,
      registrations: entry.registrations,
      emitters: entry.emitters.size,
      unresolved: entry.unresolved,
      targetKinds: countsToArray(entry.targetKinds, formatTargetKindLabel),
    }))
    .sort((left, right) => {
      if (right.registrations !== left.registrations) {
        return right.registrations - left.registrations;
      }
      return left.moduleId.localeCompare(right.moduleId);
    });

  return {
    modules: summary.modules.size,
    emitters: summary.emitters.size,
    targets: summary.targets.size,
    registrations: summary.registrations,
    unresolvedTargets: summary.unresolvedTargets,
    targetKindBreakdown: countsToArray(summary.targetKindCounts, formatTargetKindLabel),
    channelBreakdown: countsToArray(summary.channelCounts, formatChannelLabel),
    topEmitters,
    moduleBreakdown,
  };
}

function buildEmitterNodes(emitterRegistry) {
  return Array.from(emitterRegistry.entries())
    .map(([key, entry]) => {
      const nodeId = sanitizeMermaidId(`emitter_${key}`);
      return {
        key,
        nodeId,
        label: buildEmitterLabel(entry),
      };
    })
    .sort((left, right) => {
      if (left.label === right.label) {
        return left.nodeId.localeCompare(right.nodeId);
      }
      return left.label.localeCompare(right.label);
    });
}

function buildTargetNodes(targetRegistry) {
  return Array.from(targetRegistry.entries())
    .map(([key, entry]) => {
      const nodeId = sanitizeMermaidId(`target_${key}`);
      const classes = ["target"];
      if (entry.unresolved) {
        classes.push("unresolved");
      }
      return {
        key,
        nodeId,
        label: buildTargetLabel(entry),
        classes,
      };
    })
    .sort((left, right) => {
      if (left.label === right.label) {
        return left.nodeId.localeCompare(right.nodeId);
      }
      return left.label.localeCompare(right.label);
    });
}

function buildEmitterLabel(entry) {
  const lines = [entry.functionName ?? entry.key];

  const methodSummary = buildMethodSummary(entry.methods);
  if (methodSummary) {
    lines.push(methodSummary);
  }

  const lineSummary = buildLineSummary(entry.lines);
  if (lineSummary) {
    lines.push(lineSummary);
  }

  lines.push(`Targets: ${entry.targets.size}`);
  lines.push(`Registrations: ${entry.registrations}`);

  return lines.join("\n");
}

function buildTargetLabel(entry) {
  const base = entry.target ?? entry.resolved ?? entry.expression ?? "Unresolved target";
  const lines = [base];

  if (entry.kind && entry.kind !== "unspecified") {
    lines.push(`Kind: ${formatTargetKindLabel(entry.kind)}`);
  }

  lines.push(`Registrations: ${entry.registrations}`);
  lines.push(`Emitters: ${entry.modules.size}`);

  if (entry.unresolved) {
    lines.push("Unresolved target");
  }

  return lines.join("\n");
}

function buildMethodSummary(methods) {
  if (!(methods instanceof Map) || methods.size === 0) {
    return null;
  }

  const sorted = Array.from(methods.entries()).sort((left, right) => {
    if (right[1] !== left[1]) {
      return right[1] - left[1];
    }
    return left[0].localeCompare(right[0]);
  });

  const [primaryName, primaryCount] = sorted[0];
  let summary = `${formatMethod(primaryName)}${primaryCount > 1 ? ` x${primaryCount}` : ""}`;
  if (sorted.length > 1) {
    summary = `${summary} (+${sorted.length - 1} more)`;
  }
  return `Method: ${summary}`;
}

function buildLineSummary(lines) {
  if (!(lines instanceof Set) || lines.size === 0) {
    return null;
  }
  const sorted = Array.from(lines)
    .filter((value) => Number.isFinite(value))
    .sort((left, right) => left - right);
  if (sorted.length === 0) {
    return null;
  }
  const formatted = sorted.slice(0, 3).map((value) => `@${value}`);
  if (sorted.length > 3) {
    formatted.push(`+${sorted.length - 3} more`);
  }
  return `Lines: ${formatted.join(", ")}`;
}

function buildStatusMessage(stats, scopeLabel) {
  const unresolvedSuffix = stats.unresolvedTargets > 0
    ? `; ${stats.unresolvedTargets} unresolved target${stats.unresolvedTargets === 1 ? "" : "s"}`
    : "";
  return `Rendered Callback Registration Map for ${scopeLabel} (${stats.emitters} emitter${stats.emitters === 1 ? "" : "s"}, ${stats.targets} target${stats.targets === 1 ? "" : "s"}, ${stats.registrations} registration${stats.registrations === 1 ? "" : "s"}${unresolvedSuffix}).`;
}

function buildStatusDetails(stats) {
  const details = [
    {
      type: "stat-summary",
      title: "Callback Snapshot",
      items: [
        { label: "Modules", value: String(stats.modules) },
        { label: "Emitters", value: String(stats.emitters) },
        { label: "Targets", value: String(stats.targets) },
        { label: "Registrations", value: String(stats.registrations) },
        { label: "Unresolved Targets", value: String(stats.unresolvedTargets) },
      ],
    },
  ];

  if (stats.channelBreakdown.length > 0) {
    details.push({
      type: "list",
      title: "Registration Channels",
      description: "Invocation mechanisms recorded for callbacks.",
      items: stats.channelBreakdown.slice(0, 10).map((entry) => ({
        header: entry.label,
        body: `${entry.count} registration${entry.count === 1 ? "" : "s"}`,
      })),
    });
  }

  if (stats.targetKindBreakdown.length > 0) {
    details.push({
      type: "list",
      title: "Target Kind Breakdown",
      description: "Classification emitted by the CommandView inventory for callback targets.",
      items: stats.targetKindBreakdown.map((entry) => ({
        header: entry.label,
        body: `${entry.count} registration${entry.count === 1 ? "" : "s"}`,
      })),
    });
  }

  if (stats.topEmitters.length > 0) {
    details.push({
      type: "list",
      title: "Top Emitters",
      description: "Functions registering the most callbacks in the current scope.",
      items: stats.topEmitters.map((entry) => ({
        header: entry.name,
        body: `${entry.registrations} registration${entry.registrations === 1 ? "" : "s"} targeting ${entry.targets} destination${entry.targets === 1 ? "" : "s"}.`,
        badges: [entry.moduleId, ...entry.channels.slice(0, 3)],
      })),
    });
  }

  const modulesWithRegistrations = stats.moduleBreakdown.filter((entry) => entry.registrations > 0);
  if (modulesWithRegistrations.length > 0) {
    details.push({
      type: "list",
      title: "Module Coverage",
      description: "Modules contributing callback registrations in the current scope.",
      items: modulesWithRegistrations.slice(0, 10).map((entry) => ({
        header: entry.moduleId,
        body: `${entry.registrations} registration${entry.registrations === 1 ? "" : "s"} from ${entry.emitters} emitter${entry.emitters === 1 ? "" : "s"}.`,
        badges: entry.unresolved > 0 ? [`${entry.unresolved} unresolved`] : [],
      })),
    });
  }

  if (stats.unresolvedTargets > 0) {
    details.push({
      type: "info",
      title: "Unresolved targets detected",
      description: `${stats.unresolvedTargets} registration${stats.unresolvedTargets === 1 ? "" : "s"} lack resolved target metadata.`,
    });
  }

  return details;
}

function ensureEmitterEntry(registry, key, moduleId, registration) {
  let entry = registry.get(key);
  if (entry) {
    return entry;
  }
  entry = {
    key,
    moduleId,
    functionName: normalizeString(registration.function),
    registrations: 0,
    methods: new Map(),
    lines: new Set(),
    targets: new Set(),
    channels: new Set(),
  };
  registry.set(key, entry);
  return entry;
}

function ensureTargetEntry(registry, key, registration) {
  let entry = registry.get(key);
  if (entry) {
    return entry;
  }
  entry = {
    key,
    target: normalizeString(registration.target),
    resolved: normalizeString(registration.resolved),
    expression: normalizeString(registration.expression),
    kind: normalizeTargetKind(registration.targetKind),
    registrations: 0,
    modules: new Set(),
    via: new Map(),
    unresolved: false,
  };
  registry.set(key, entry);
  return entry;
}

function resolveEmitterKey(moduleId, registration) {
  const functionName = normalizeString(registration.function);
  if (functionName) {
    return functionName;
  }
  const expression = normalizeString(registration.expression);
  if (expression) {
    return moduleId ? `${moduleId}::${expression}` : expression;
  }
  const method = normalizeString(registration.method);
  if (method) {
    return moduleId ? `${moduleId}::${method}` : method;
  }
  return moduleId ? `${moduleId}::callback` : null;
}

function resolveTargetKey(registration, moduleId, sequence) {
  const target = normalizeString(registration.target);
  if (target) {
    return target;
  }
  const resolved = normalizeString(registration.resolved);
  if (resolved) {
    return resolved;
  }
  const expression = normalizeString(registration.expression);
  if (expression) {
    return moduleId ? `${moduleId}::expr::${expression}` : `expr::${expression}`;
  }
  sequence.value += 1;
  return `${moduleId ?? "module"}::unresolved_${sequence.value}`;
}

function resolveChannelLabel(registration) {
  const via = normalizeString(registration.targetVia ?? registration.channel);
  if (via) {
    return via;
  }
  const method = normalizeString(registration.method);
  if (method) {
    return `${method}()`;
  }
  const kind = normalizeString(registration.kind);
  if (kind) {
    return kind;
  }
  return "callback";
}

function normalizeTargetKind(value) {
  const normalized = normalizeString(value);
  return normalized ? normalized.toLowerCase() : "unspecified";
}

function countsToArray(counts, formatter) {
  return Array.from(counts.entries())
    .map(([key, value]) => ({
      key,
      label: formatter ? formatter(key) : key,
      count: value,
    }))
    .sort((left, right) => {
      if (right.count !== left.count) {
        return right.count - left.count;
      }
      return left.label.localeCompare(right.label);
    });
}

function formatTargetKindLabel(value) {
  if (!value || value === "unspecified") {
    return "Unspecified";
  }
  return value
    .split(/[_\.\-]/g)
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
}

function formatChannelLabel(value) {
  if (!value) {
    return "callback";
  }
  if (value.endsWith("()")) {
    return value;
  }
  return value;
}

function formatMethod(value) {
  if (!value) {
    return "callback";
  }
  return value.endsWith("()") ? value : `${value}()`;
}

function normalizeString(value) {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function appendClassDefinitions(lines) {
  lines.push("  classDef emitter fill:#1f2937,stroke:#38bdf8,color:#f8fafc;");
  lines.push("  classDef target fill:#0f172a,stroke:#f97316,color:#f8fafc;");
  lines.push("  classDef unresolved stroke-dasharray: 5 3;");
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
  collectRegistrations,
  buildStats,
  buildEmitterNodes,
  buildTargetNodes,
  buildEmitterLabel,
  buildTargetLabel,
  resolveEmitterKey,
  resolveTargetKey,
  resolveChannelLabel,
  normalizeTargetKind,
  countsToArray,
  formatTargetKindLabel,
  sanitizeMermaidId,
  escapeMermaidLabel,
  toModuleMap,
};
