const DEFAULT_VIEW_LABEL = "Event Dynamics · Dynamic Code Watchlist";

const FLAG_LABELS = Object.freeze({
  exec: "exec()",
  dynamicImport: "dynamic import",
  metaclass: "metaclass",
  globalsMutation: "globals mutation",
});

const MODULE_FLAG_CLASS_MAP = Object.freeze({
  exec: "moduleExec",
  dynamicImport: "moduleDynamicImport",
  metaclass: "moduleMetaclass",
  globalsMutation: "moduleGlobalsMutation",
});

const FLAG_NODE_CLASS_MAP = Object.freeze({
  exec: "flagExec",
  dynamicImport: "flagDynamicImport",
  metaclass: "flagMetaclass",
  globalsMutation: "flagGlobalsMutation",
});

let mermaidIdCounter = 0;

export function buildDynamicCodeWatchlistDiagram(modules, options = {}) {
  const moduleMap = toModuleMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message:
        options.missingModulesMessage ?? "Module metadata has not been normalized for this CommandView artifact.",
    };
  }

  const summary = collectDynamicCodeSummary(moduleMap);
  if (summary.flaggedModuleCount === 0) {
    return {
      message: options.emptyMessage ?? "No dynamic code signals recorded for this CommandView artifact.",
    };
  }

  const stats = buildStats(summary);

  mermaidIdCounter = 0;

  const lines = ["graph TD"];
  appendClassDefinitions(lines);

  const moduleNodes = buildModuleNodes(summary.modules);
  const flagNodes = buildFlagNodes(summary.flagTotals);
  const eventNodes = buildEventNodes(summary.eventKindTotals);

  const flagNodeMap = new Map(flagNodes.map((node) => [node.key, node]));
  const eventNodeMap = new Map(eventNodes.map((node) => [node.key, node]));

  moduleNodes.forEach((node) => {
    lines.push(`  ${node.nodeId}["${escapeMermaidLabel(node.label)}"]`);
    lines.push(`  class ${node.nodeId} ${node.classes.join(",")};`);
  });

  flagNodes.forEach((node) => {
    lines.push(`  ${node.nodeId}["${escapeMermaidLabel(node.label)}"]`);
    lines.push(`  class ${node.nodeId} ${node.classes.join(",")};`);
  });

  eventNodes.forEach((node) => {
    lines.push(`  ${node.nodeId}["${escapeMermaidLabel(node.label)}"]`);
    lines.push(`  class ${node.nodeId} ${node.classes.join(",")};`);
  });

  moduleNodes.forEach((moduleNode) => {
    moduleNode.flags.forEach((flagKey) => {
      const target = flagNodeMap.get(flagKey);
      if (!target) {
        return;
      }
      lines.push(
        `  ${moduleNode.nodeId} -->|${escapeMermaidLabel(formatFlagLabel(flagKey))}| ${target.nodeId}`
      );
    });

    moduleNode.eventKinds.forEach((count, kind) => {
      const target = eventNodeMap.get(kind);
      if (!target) {
        return;
      }
      const labelBase = formatEventKindLabel(kind);
      const label = count > 1 ? `${labelBase} (${count})` : labelBase;
      lines.push(`  ${moduleNode.nodeId} -->|${escapeMermaidLabel(label)}| ${target.nodeId}`);
    });
  });

  const scopeLabel = options.scopeDescription ?? "repository";
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
    statusDetails,
    stats,
  };
}

function collectDynamicCodeSummary(moduleMap) {
  const summary = {
    modules: new Map(),
    flagTotals: new Map(),
    eventKindTotals: new Map(),
    flaggedModuleCount: 0,
    totalEvents: 0,
    flagTriggerTotal: 0,
  };

  moduleMap.forEach((moduleRecord, moduleId) => {
    const dynamic = moduleRecord?.dynamicCode;
    if (!dynamic || dynamic.hasDynamic !== true) {
      return;
    }

    const flagsList = Array.isArray(dynamic.activeFlags) ? dynamic.activeFlags.slice() : [];
    const flagSet = new Set(flagsList);

    const events = Array.isArray(dynamic.events) ? dynamic.events : [];
    const eventKinds = new Map();
    events.forEach((event) => {
      const kind = event?.kind ?? "unknown";
      eventKinds.set(kind, (eventKinds.get(kind) ?? 0) + 1);

      let kindEntry = summary.eventKindTotals.get(kind);
      if (!kindEntry) {
        kindEntry = { count: 0, modules: new Map() };
        summary.eventKindTotals.set(kind, kindEntry);
      }
      kindEntry.count += 1;
      kindEntry.modules.set(moduleId, (kindEntry.modules.get(moduleId) ?? 0) + 1);
    });

    if (flagSet.size === 0 && eventKinds.size === 0) {
      return;
    }

    summary.modules.set(moduleId, {
      moduleId,
      flags: flagsList,
      eventKinds,
      eventCount: events.length,
    });

    summary.flaggedModuleCount += 1;
    summary.totalEvents += events.length;

    flagSet.forEach((flagKey) => {
      let modulesSet = summary.flagTotals.get(flagKey);
      if (!modulesSet) {
        modulesSet = new Set();
        summary.flagTotals.set(flagKey, modulesSet);
      }
      if (!modulesSet.has(moduleId)) {
        modulesSet.add(moduleId);
        summary.flagTriggerTotal += 1;
      }
    });
  });

  return summary;
}

function buildStats(summary) {
  const flagBreakdown = buildFlagBreakdown(summary.flagTotals);
  const eventKindBreakdown = buildEventKindBreakdown(summary.eventKindTotals);
  const topModules = buildTopModules(summary.modules);

  return {
    modules: summary.flaggedModuleCount,
    eventCount: summary.totalEvents,
    flagTriggerCount: summary.flagTriggerTotal,
    flagTypes: summary.flagTotals.size,
    flagBreakdown,
    eventKindBreakdown,
    topModules,
  };
}

function buildModuleNodes(moduleEntries) {
  return Array.from(moduleEntries.values())
    .map((entry) => {
      const nodeId = nextMermaidId("module");
      const classes = new Set(["module"]);
      entry.flags.forEach((flagKey) => {
        const className = MODULE_FLAG_CLASS_MAP[flagKey];
        if (className) {
          classes.add(className);
        }
      });

      const flagSummary = entry.flags.length > 0
        ? entry.flags.map((flagKey) => formatFlagLabel(flagKey)).join(", ")
        : "None";
      const labelLines = [
        entry.moduleId,
        `Flags: ${flagSummary}`,
        `Events: ${entry.eventCount}`,
      ];

      if (entry.eventKinds.size > 0) {
        const topKinds = Array.from(entry.eventKinds.entries())
          .sort((left, right) => {
            if (right[1] !== left[1]) {
              return right[1] - left[1];
            }
            return formatEventKindLabel(left[0]).localeCompare(formatEventKindLabel(right[0]));
          })
          .slice(0, 3)
          .map(([kind, count]) => `${formatEventKindLabel(kind)} (${count})`);
        labelLines.push(`Kinds: ${topKinds.join(", ")}`);
      }

      return {
        moduleId: entry.moduleId,
        nodeId,
        label: labelLines.join("\n"),
        classes: Array.from(classes),
        flags: entry.flags,
        eventKinds: entry.eventKinds,
      };
    })
    .sort((left, right) => left.moduleId.localeCompare(right.moduleId));
}

function buildFlagNodes(flagTotals) {
  return Array.from(flagTotals.entries())
    .map(([flagKey, modulesSet]) => {
      const nodeId = nextMermaidId(`flag_${flagKey}`);
      const count = modulesSet.size;
      const modulesList = Array.from(modulesSet).sort((a, b) => a.localeCompare(b));
      const labelLines = [
        formatFlagLabel(flagKey),
        `Modules: ${count}`,
      ];

      return {
        key: flagKey,
        nodeId,
        label: labelLines.join("\n"),
        classes: buildFlagNodeClasses(flagKey),
        count,
        modules: modulesList,
      };
    })
    .sort((left, right) => {
      if (right.count !== left.count) {
        return right.count - left.count;
      }
      return formatFlagLabel(left.key).localeCompare(formatFlagLabel(right.key));
    });
}

function buildEventNodes(eventTotals) {
  return Array.from(eventTotals.entries())
    .map(([kind, info]) => {
      const nodeId = nextMermaidId(`event_${kind}`);
      const labelLines = [
        formatEventKindLabel(kind),
        `Events: ${info.count}`,
      ];
      const modulesList = Array.from(info.modules.entries())
        .sort((left, right) => {
          if (right[1] !== left[1]) {
            return right[1] - left[1];
          }
          return left[0].localeCompare(right[0]);
        })
        .map(([moduleId, count]) => `${moduleId} (${count})`);
      if (modulesList.length > 0) {
        labelLines.push(`Top Modules: ${modulesList.slice(0, 3).join(", ")}`);
      }

      return {
        key: kind,
        nodeId,
        label: labelLines.join("\n"),
        classes: ["event"],
        count: info.count,
      };
    })
    .sort((left, right) => {
      if (right.count !== left.count) {
        return right.count - left.count;
      }
      return left.label.localeCompare(right.label);
    });
}

function buildFlagNodeClasses(flagKey) {
  const classes = ["flag"];
  const specific = FLAG_NODE_CLASS_MAP[flagKey];
  if (specific) {
    classes.push(specific);
  }
  return classes;
}

function buildFlagBreakdown(flagTotals) {
  return Array.from(flagTotals.entries())
    .map(([flagKey, modulesSet]) => ({
      key: flagKey,
      label: formatFlagLabel(flagKey),
      count: modulesSet.size,
      modules: Array.from(modulesSet).sort((a, b) => a.localeCompare(b)),
    }))
    .sort((left, right) => {
      if (right.count !== left.count) {
        return right.count - left.count;
      }
      return left.label.localeCompare(right.label);
    });
}

function buildEventKindBreakdown(eventTotals) {
  return Array.from(eventTotals.entries())
    .map(([kind, info]) => ({
      key: kind,
      label: formatEventKindLabel(kind),
      count: info.count,
      modules: Array.from(info.modules.entries())
        .sort((left, right) => {
          if (right[1] !== left[1]) {
            return right[1] - left[1];
          }
          return left[0].localeCompare(right[0]);
        })
        .map(([moduleId, count]) => ({ moduleId, count })),
    }))
    .sort((left, right) => {
      if (right.count !== left.count) {
        return right.count - left.count;
      }
      return left.label.localeCompare(right.label);
    });
}

function buildTopModules(modulesMap) {
  return Array.from(modulesMap.values())
    .map((entry) => ({
      moduleId: entry.moduleId,
      events: entry.eventCount,
      flags: entry.flags,
    }))
    .sort((left, right) => {
      if (right.events !== left.events) {
        return right.events - left.events;
      }
      if (right.flags.length !== left.flags.length) {
        return right.flags.length - left.flags.length;
      }
      return left.moduleId.localeCompare(right.moduleId);
    })
    .slice(0, 10);
}

function buildStatusMessage(stats, scopeLabel) {
  const modulesText = `${stats.modules} module${stats.modules === 1 ? "" : "s"}`;
  const flagsText = `${stats.flagTriggerCount} flag trigger${stats.flagTriggerCount === 1 ? "" : "s"}`;
  const eventsText = `${stats.eventCount} event${stats.eventCount === 1 ? "" : "s"}`;
  return `Rendered Dynamic Code Watchlist for ${scopeLabel} (${modulesText}, ${flagsText}, ${eventsText}).`;
}

function buildStatusDetails(stats) {
  const details = [
    {
      type: "stat-summary",
      title: "Dynamic Code Snapshot",
      items: [
        { label: "Modules", value: String(stats.modules) },
        { label: "Flag Types", value: String(stats.flagTypes) },
        { label: "Flag Triggers", value: String(stats.flagTriggerCount) },
        { label: "Events", value: String(stats.eventCount) },
      ],
    },
  ];

  if (stats.flagBreakdown.length > 0) {
    details.push({
      type: "list",
      title: "Flag Triggers",
      description: "Modules where dynamic execution patterns were detected.",
      items: stats.flagBreakdown.map((entry) => ({
        header: entry.label,
        body: `${entry.count} module${entry.count === 1 ? "" : "s"}`,
      })),
    });
  }

  if (stats.eventKindBreakdown.length > 0) {
    details.push({
      type: "list",
      title: "Event Kind Breakdown",
      description: "Inventory events captured for dynamic execution signals.",
      items: stats.eventKindBreakdown.map((entry) => ({
        header: entry.label,
        body: `${entry.count} event${entry.count === 1 ? "" : "s"}`,
      })),
    });
  }

  if (stats.topModules.length > 0) {
    details.push({
      type: "list",
      title: "Top Modules",
      description: "Modules with the highest concentration of dynamic execution signals.",
      items: stats.topModules.map((entry) => ({
        header: entry.moduleId,
        body: `${entry.events} event${entry.events === 1 ? "" : "s"} · flags: ${
          entry.flags.length > 0 ? entry.flags.map((flag) => formatFlagLabel(flag)).join(", ") : "none"
        }`,
      })),
    });
  }

  return details;
}

function appendClassDefinitions(lines) {
  lines.push("  classDef module fill:#0f172a,stroke:#38bdf8,color:#f8fafc;");
  lines.push("  classDef moduleExec stroke:#ef4444,stroke-width:3px;");
  lines.push("  classDef moduleDynamicImport stroke:#0ea5e9,stroke-width:3px;");
  lines.push("  classDef moduleMetaclass stroke:#c084fc,stroke-width:3px;");
  lines.push("  classDef moduleGlobalsMutation stroke:#f97316,stroke-width:3px;");
  lines.push("  classDef flag fill:#1f2937,stroke:#94a3b8,color:#f8fafc;");
  lines.push("  classDef flagExec fill:#7f1d1d,stroke:#f87171,color:#fef2f2;");
  lines.push("  classDef flagDynamicImport fill:#0f766e,stroke:#34d399,color:#ecfdf5;");
  lines.push("  classDef flagMetaclass fill:#4c1d95,stroke:#c4b5fd,color:#ede9fe;");
  lines.push("  classDef flagGlobalsMutation fill:#78350f,stroke:#f59e0b,color:#fff7ed;");
  lines.push("  classDef event fill:#312e81,stroke:#a855f7,color:#ede9fe;");
}

function formatFlagLabel(flagKey) {
  return FLAG_LABELS[flagKey] ?? flagKey;
}

function formatEventKindLabel(kind) {
  if (!kind) {
    return "Unknown";
  }
  const normalized = String(kind)
    .replace(/[_\s]+/g, " ")
    .trim()
    .toLowerCase();
  if (!normalized) {
    return "Unknown";
  }
  return normalized
    .split(" ")
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
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

function nextMermaidId(prefix) {
  mermaidIdCounter += 1;
  return sanitizeMermaidId(`${prefix}_${mermaidIdCounter}`);
}

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
