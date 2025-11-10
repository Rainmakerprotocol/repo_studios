const DEFAULT_VIEW_LABEL = "Quality Metrics · Decorator Usage Map";
const DEFAULT_CENTER_LABEL = "Decorator Usage Map";
const DEFAULT_BUCKET_LIMIT = 8;
const DEFAULT_DECORATOR_LIMIT = 6;
const DEFAULT_POLICY_SAMPLE_LIMIT = 3;

const CLASS_CONFIG = Object.freeze({
  frequent: { className: "decoratorFrequent", fill: "#1f2937", stroke: "#f59e0b", color: "#fff7ed" },
  common: { className: "decoratorCommon", fill: "#0f766e", stroke: "#5eead4", color: "#ecfeff" },
  occasional: { className: "decoratorOccasional", fill: "#1d4ed8", stroke: "#93c5fd", color: "#eff6ff" },
  missing: { className: "decoratorMissing", fill: "#7f1d1d", stroke: "#f87171", color: "#fee2e2" },
});

export function buildDecoratorUsageMapDiagram(functions, options = {}) {
  const functionsMap = toMap(functions);
  if (!functionsMap || functionsMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "No functions recorded in this CommandView artifact.",
    };
  }

  const centerLabel = resolveCenterLabel(options.centerLabel);
  const bucketLimit = resolvePositiveNumber(options.bucketLimit, DEFAULT_BUCKET_LIMIT);
  const decoratorLimit = resolvePositiveNumber(options.decoratorLimit, DEFAULT_DECORATOR_LIMIT);
  const centerId = sanitizeMermaidId(options.centerId ?? "decorator_usage_center");

  const aggregates = collectDecoratorAggregates(functionsMap);
  const policyConfig = resolveDecoratorPolicyConfig(options.policyConfig, options.requiredDecorators);
  const policySampleLimit = resolvePositiveNumber(
    options.policySampleLimit,
    Math.min(bucketLimit, DEFAULT_POLICY_SAMPLE_LIMIT)
  );
  const policyEvaluation = evaluateDecoratorPolicyCompliance(functionsMap, aggregates, policyConfig, {
    sampleLimit: policySampleLimit,
  });
  const lines = ["graph TD"];
  lines.push(`  ${centerId}["${escapeMermaidLabel(centerLabel)}"]`);
  appendClassDefinitions(lines);

  aggregates.decorators.slice(0, decoratorLimit).forEach((decorator, index) => {
    const bucketId = sanitizeMermaidId(`decorator_bucket_${decorator.key}`);
    const labelLines = buildDecoratorBucketLabel(decorator, bucketLimit);
    lines.push(`  ${bucketId}["${escapeMermaidLabel(labelLines.join("\\n"))}"]`);
    lines.push(`  ${centerId} --> ${bucketId}`);

    const classification = classifyDecorator(decorator.count, index);
    const config = CLASS_CONFIG[classification];
    if (config) {
      lines.push(`  class ${bucketId} ${config.className};`);
    }
  });

  if (aggregates.undecorated.functions.length > 0) {
    const bucketId = sanitizeMermaidId("decorator_bucket_none");
    const labelLines = buildUndecoratedBucketLabel(aggregates.undecorated, bucketLimit);
    lines.push(`  ${bucketId}["${escapeMermaidLabel(labelLines.join("\\n"))}"]`);
    lines.push(`  ${centerId} --> ${bucketId}`);
    const missingConfig = CLASS_CONFIG.missing;
    lines.push(`  class ${bucketId} ${missingConfig.className};`);
  }

  const stats = {
    decorated: aggregates.decoratedCount,
    undecorated: aggregates.undecorated.functions.length,
    uniqueDecorators: aggregates.decorators.length,
    topDecorators: aggregates.decorators.slice(0, Math.min(aggregates.decorators.length, 5)).map((decorator) => ({
      name: decorator.label,
      count: decorator.count,
    })),
    requiredDecorators: policyEvaluation.requiredNames,
    missingRequiredDecorators: policyEvaluation.missingNames,
    missingRequiredDetails: policyEvaluation.missingDetails,
  };

  const statusMessage = options.statusMessageFormatter
    ? options.statusMessageFormatter(stats, aggregates.decorators[0], policyEvaluation.missingSummaries)
    : formatDefaultStatus(stats, aggregates.decorators[0], policyEvaluation.missingSummaries);

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    stats,
    policyDetails: policyEvaluation.missingDetails,
  };
}

function collectDecoratorAggregates(functionsMap) {
  const decoratorMap = new Map();
  const undecorated = { functions: [] };
  let decoratedCount = 0;

  functionsMap.forEach((fn, functionId) => {
    const decorators = Array.isArray(fn?.decorators) ? fn.decorators : [];
    const detailed = Array.isArray(fn?.decoratorsDetailed) ? fn.decoratorsDetailed : [];
    const functionInfo = {
      id: functionId ?? fn?.id ?? null,
      name: typeof fn?.name === "string" && fn.name.trim().length > 0 ? fn.name.trim() : functionId ?? "anonymous",
      moduleId: typeof fn?.moduleId === "string" ? fn.moduleId : null,
      detailed,
    };

    const uniqueDecorators = new Set();
    decorators.forEach((name) => {
      const normalized = normalizeString(name);
      if (!normalized || uniqueDecorators.has(normalized)) {
        return;
      }
      uniqueDecorators.add(normalized);

      const aggregate = decoratorMap.get(normalized) ?? {
        key: normalizeKey(normalized),
        label: normalized,
        count: 0,
        functions: [],
      };
      aggregate.count += 1;
      aggregate.functions.push({ ...functionInfo });
      decoratorMap.set(normalized, aggregate);
    });

    if (uniqueDecorators.size === 0) {
      undecorated.functions.push(functionInfo);
    } else {
      decoratedCount += 1;
    }
  });

  const decorators = Array.from(decoratorMap.values()).sort((a, b) => {
    if (b.count !== a.count) {
      return b.count - a.count;
    }
    return a.label.localeCompare(b.label);
  });

  return {
    decorators,
    undecorated,
    decoratedCount,
  };
}

function buildDecoratorBucketLabel(decorator, bucketLimit) {
  const lines = [decorator.label, `Functions: ${decorator.count}`];
  const entries = decorator.functions.slice(0, bucketLimit).map((fn) => formatFunctionEntry(fn));
  lines.push(...(entries.length > 0 ? entries : ["No functions recorded"]));
  if (decorator.count > entries.length) {
    lines.push(`+${decorator.count - entries.length} more`);
  }
  return lines;
}

function buildUndecoratedBucketLabel(undecorated, bucketLimit) {
  const lines = ["Undecorated", `Functions: ${undecorated.functions.length}`];
  const entries = undecorated.functions.slice(0, bucketLimit).map((fn) => formatFunctionEntry(fn));
  lines.push(...(entries.length > 0 ? entries : ["None recorded"]));
  if (undecorated.functions.length > entries.length) {
    lines.push(`+${undecorated.functions.length - entries.length} more`);
  }
  return lines;
}

function classifyDecorator(count, index) {
  if (count >= 5) {
    return "frequent";
  }
  if (count >= 2) {
    return "common";
  }
  if (index === 0) {
    return "common";
  }
  return "occasional";
}

function formatFunctionEntry(fn) {
  const moduleSuffix = fn.moduleId ? ` · ${fn.moduleId}` : "";
  return `${fn.name}${moduleSuffix}`;
}

function resolveCenterLabel(centerLabel) {
  if (typeof centerLabel === "string" && centerLabel.trim().length > 0) {
    return centerLabel.trim();
  }
  return DEFAULT_CENTER_LABEL;
}

function resolvePositiveNumber(value, fallback) {
  if (!Number.isFinite(Number(value))) {
    return fallback;
  }
  const numeric = Math.floor(Number(value));
  return numeric > 0 ? numeric : fallback;
}

function normalizeString(value) {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }
  return null;
}

function normalizeKey(value) {
  return value.replace(/[^a-zA-Z0-9_]+/g, "_").toLowerCase();
}

function resolveRequiredDecorators(value) {
  const map = new Map();
  collectDecoratorRequirements(map, value);
  return Array.from(map.values());
}

function collectDecoratorRequirements(map, value) {
  if (!value) {
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((entry) => collectDecoratorRequirements(map, entry));
    return;
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    addDecoratorRequirement(map, value);
    return;
  }
  if (typeof value !== "object") {
    return;
  }

  if (Array.isArray(value.required)) {
    collectDecoratorRequirements(map, value.required);
  } else if (typeof value.required === "string") {
    collectDecoratorRequirements(map, [value.required]);
  }

  if (Array.isArray(value.names)) {
    collectDecoratorRequirements(map, value.names);
  }
  if (Array.isArray(value.decorators)) {
    collectDecoratorRequirements(map, value.decorators);
  }

  if (typeof value.name === "string") {
    addDecoratorRequirement(map, value.name);
  }
  if (typeof value.decorator === "string") {
    addDecoratorRequirement(map, value.decorator);
  }
  if (typeof value.id === "string") {
    addDecoratorRequirement(map, value.id);
  }
}

function addDecoratorRequirement(map, value) {
  const normalized = normalizeString(value);
  if (!normalized) {
    return;
  }
  const key = normalizeKey(normalized);
  if (!map.has(key)) {
    map.set(key, { label: normalized, key });
  }
}

function resolveDecoratorPolicyConfig(policyConfig, legacyRequired) {
  const globalMap = new Map();
  const moduleMap = new Map();
  const rootMap = new Map();
  const domainMap = new Map();

  const mergeGlobal = (value) => {
    resolveRequiredDecorators(value).forEach((entry) => {
      if (!globalMap.has(entry.key)) {
        globalMap.set(entry.key, entry);
      }
    });
  };

  const mergeScoped = (targetMap, scopeId, value) => {
    const scopeLabel = normalizeString(scopeId);
    if (!scopeLabel) {
      return;
    }
    const entries = resolveRequiredDecorators(value);
    if (entries.length === 0) {
      return;
    }
    const existing = targetMap.get(scopeLabel) ?? new Map();
    entries.forEach((entry) => {
      if (!existing.has(entry.key)) {
        existing.set(entry.key, entry);
      }
    });
    targetMap.set(scopeLabel, existing);
  };

  const mergePolicySource = (source) => {
    if (!source) {
      return;
    }
    if (typeof source === "string" || typeof source === "number" || typeof source === "boolean") {
      mergeGlobal(source);
      return;
    }
    if (Array.isArray(source)) {
      source.forEach((entry) => mergePolicySource(entry));
      return;
    }
    if (typeof source !== "object") {
      return;
    }

    mergeGlobal(source.global);
    mergeGlobal(source.required);
    mergeGlobal(source.requiredDecorators);
    mergeGlobal(source.decorators);
    mergeGlobal(source.names);

    const moduleSource =
      source.modules ?? source.module ?? source.byModule ?? source.perModule ?? source.moduleRequirements;
    if (moduleSource && typeof moduleSource === "object") {
      Object.entries(moduleSource).forEach(([moduleId, value]) => {
        mergeScoped(moduleMap, moduleId, value);
      });
    }

    const rootSource = source.roots ?? source.root ?? source.byRoot ?? source.perRoot;
    if (rootSource && typeof rootSource === "object") {
      Object.entries(rootSource).forEach(([rootId, value]) => {
        mergeScoped(rootMap, rootId, value);
      });
    }

    const domainSource = source.domains ?? source.domain ?? source.byDomain ?? source.perDomain;
    if (domainSource && typeof domainSource === "object") {
      Object.entries(domainSource).forEach(([domainId, value]) => {
        mergeScoped(domainMap, domainId, value);
      });
    }

    if (source.scopes && typeof source.scopes === "object") {
      Object.values(source.scopes).forEach((scopeConfig) => {
        if (!scopeConfig || typeof scopeConfig !== "object") {
          return;
        }
        const target = scopeConfig.target ?? scopeConfig.id ?? scopeConfig.scope ?? null;
        const scopeType = scopeConfig.type ?? scopeConfig.scopeType ?? null;
        const requirements =
          scopeConfig.required ?? scopeConfig.decorators ?? scopeConfig.names ?? scopeConfig.values ?? scopeConfig.list;
        if (!target) {
          return;
        }
        switch (scopeType) {
          case "module":
          case "modules":
            mergeScoped(moduleMap, target, requirements ?? scopeConfig);
            break;
          case "root":
          case "roots":
            mergeScoped(rootMap, target, requirements ?? scopeConfig);
            break;
          case "domain":
          case "domains":
            mergeScoped(domainMap, target, requirements ?? scopeConfig);
            break;
          default:
            mergeGlobal(requirements ?? scopeConfig);
            break;
        }
      });
    }
  };

  mergeGlobal(legacyRequired);
  mergePolicySource(policyConfig);

  return {
    global: Array.from(globalMap.values()),
    perModule: convertRequirementMapToObject(moduleMap),
    perRoot: convertRequirementMapToObject(rootMap),
    perDomain: convertRequirementMapToObject(domainMap),
  };
}

function convertRequirementMapToObject(map) {
  const result = {};
  map.forEach((entryMap, key) => {
    const entries = Array.from(entryMap.values());
    if (entries.length > 0) {
      result[key] = entries;
    }
  });
  return result;
}

function evaluateDecoratorPolicyCompliance(functionsMap, aggregates, policyConfig, options = {}) {
  const sampleLimit = Number.isFinite(Number(options.sampleLimit)) && Number(options.sampleLimit) > 0
    ? Math.floor(Number(options.sampleLimit))
    : DEFAULT_POLICY_SAMPLE_LIMIT;

  const functionsList = [];
  const functionsByModule = new Map();
  const functionsByRoot = new Map();
  const functionsByDomain = new Map();
  const decoratorPresence = new Set(
    Array.isArray(aggregates?.decorators)
      ? aggregates.decorators.map((decorator) => decorator.key).filter((key) => typeof key === "string")
      : []
  );

  functionsMap.forEach((fn, functionId) => {
    const moduleId = typeof fn?.moduleId === "string" ? fn.moduleId : null;
    const functionName = typeof fn?.name === "string" && fn.name.trim().length > 0 ? fn.name.trim() : functionId;
    const decoratorNames = Array.isArray(fn?.decorators) ? fn.decorators : [];
    const decoratorKeys = new Set();
    decoratorNames.forEach((name) => {
      const normalized = normalizeString(name);
      if (!normalized) {
        return;
      }
      const key = normalizeKey(normalized);
      decoratorKeys.add(key);
      decoratorPresence.add(key);
    });

    const record = {
      id: functionId,
      name: functionName,
      moduleId,
      decoratorKeys,
    };

    functionsList.push(record);
    if (moduleId) {
      addFunctionToGroup(functionsByModule, moduleId, record);
      const rootId = deriveRootSegment(moduleId);
      if (rootId) {
        addFunctionToGroup(functionsByRoot, rootId, record);
      }
      const domainId = deriveDomainId(moduleId);
      if (domainId) {
        addFunctionToGroup(functionsByDomain, domainId, record);
      }
    }
  });

  const requiredNameMap = new Map();
  const missingNameMap = new Map();
  const missingDetails = [];
  const missingSummaries = [];

  const recordMissing = (entry, scope, target, samples) => {
    if (!missingNameMap.has(entry.key)) {
      missingNameMap.set(entry.key, entry.label);
    }
    missingDetails.push({
      decorator: entry.label,
      scope,
      target: target ?? null,
      samples: samples.map((fn) => ({ id: fn.id, name: fn.name, moduleId: fn.moduleId ?? null })),
    });
    const summary = scope === "global" || !target ? entry.label : `${entry.label} (${scope} ${target})`;
    missingSummaries.push(summary);
  };

  policyConfig.global.forEach((entry) => {
    if (!requiredNameMap.has(entry.key)) {
      requiredNameMap.set(entry.key, entry.label);
    }
    if (!decoratorPresence.has(entry.key)) {
      const samples = collectSampleFunctions(functionsList, entry.key, sampleLimit);
      recordMissing(entry, "global", null, samples);
    }
  });

  const evaluateScoped = (groupsMap, scopedConfig, scopeType) => {
    if (!scopedConfig || typeof scopedConfig !== "object") {
      return;
    }
    Object.entries(scopedConfig).forEach(([scopeId, entries]) => {
      const scopeLabel = normalizeString(scopeId);
      if (!scopeLabel) {
        return;
      }
      const requirementEntries = Array.isArray(entries) ? entries : [];
      const groupFunctions = groupsMap.get(scopeLabel) ?? [];
      if (groupFunctions.length === 0) {
        return;
      }
      requirementEntries.forEach((entry) => {
        if (!requiredNameMap.has(entry.key)) {
          requiredNameMap.set(entry.key, entry.label);
        }
        const hasDecorator = groupFunctions.some((fn) => fn.decoratorKeys.has(entry.key));
        if (!hasDecorator) {
          const samples = collectSampleFunctions(groupFunctions, entry.key, sampleLimit);
          recordMissing(entry, scopeType, scopeLabel, samples);
        }
      });
    });
  };

  evaluateScoped(functionsByModule, policyConfig.perModule, "module");
  evaluateScoped(functionsByRoot, policyConfig.perRoot, "root");
  evaluateScoped(functionsByDomain, policyConfig.perDomain, "domain");

  return {
    requiredNames: Array.from(requiredNameMap.values()),
    missingNames: Array.from(missingNameMap.values()),
    missingDetails,
    missingSummaries,
  };
}

function addFunctionToGroup(map, key, record) {
  const existing = map.get(key) ?? [];
  existing.push(record);
  map.set(key, existing);
}

function collectSampleFunctions(functions, decoratorKey, limit) {
  const max = Number.isFinite(Number(limit)) && Number(limit) > 0 ? Math.floor(Number(limit)) : DEFAULT_POLICY_SAMPLE_LIMIT;
  const samples = [];
  for (const fn of functions ?? []) {
    if (!fn.decoratorKeys.has(decoratorKey)) {
      samples.push({ id: fn.id, name: fn.name, moduleId: fn.moduleId ?? null });
    }
    if (samples.length >= max) {
      break;
    }
  }
  return samples;
}

function deriveRootSegment(moduleId) {
  if (!moduleId || typeof moduleId !== "string") {
    return null;
  }
  const sanitized = moduleId.replace(/\//g, ".");
  const [root] = sanitized.split(".");
  return root || null;
}

function deriveDomainId(moduleId) {
  if (!moduleId || typeof moduleId !== "string") {
    return null;
  }
  const segments = moduleId.replace(/\//g, ".").split(".");
  if (segments.length >= 2) {
    return `${segments[0]}.${segments[1]}`;
  }
  return segments[0] ?? null;
}

let mermaidIdCounter = 0;

function sanitizeMermaidId(value) {
  if (!value || typeof value !== "string") {
    mermaidIdCounter += 1;
    return `decorator_node_${mermaidIdCounter}`;
  }
  const sanitized = value.replace(/[^a-zA-Z0-9_]/g, "_");
  if (!sanitized) {
    mermaidIdCounter += 1;
    return `decorator_node_${mermaidIdCounter}`;
  }
  if (/^[0-9]/.test(sanitized)) {
    return `decorator_${sanitized}`;
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

function appendClassDefinitions(lines) {
  Object.values(CLASS_CONFIG).forEach((config) => {
    lines.push(`  classDef ${config.className} fill:${config.fill},stroke:${config.stroke},color:${config.color};`);
  });
}

function formatDefaultStatus(stats, topDecorator) {
  const segments = [
    `decorated ${stats.decorated}`,
    `undecorated ${stats.undecorated}`,
    `${stats.uniqueDecorators} unique decorators`,
  ];
  if (topDecorator && typeof topDecorator?.label === "string") {
    segments.push(`top ${topDecorator.label} x${topDecorator.count}`);
  } else {
    segments.push("no decorators recorded");
  }
  const missingRequired = Array.isArray(stats?.missingRequiredDecorators)
    ? stats.missingRequiredDecorators.filter((name) => typeof name === "string" && name.length > 0)
    : [];
  if (missingRequired.length > 0) {
    segments.push(`missing required ${missingRequired.join(", ")}`);
  }
  return `Rendered Decorator Usage Map (${segments.join(", ")}).`;
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
      const key = entry.id ?? entry.functionId ?? String(index);
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

export const __test__ = {
  buildDecoratorBucketLabel,
  buildUndecoratedBucketLabel,
  collectDecoratorAggregates,
  classifyDecorator,
  escapeMermaidLabel,
  resolveRequiredDecorators,
  resolveDecoratorPolicyConfig,
  evaluateDecoratorPolicyCompliance,
  appendClassDefinitions,
  resolvePositiveNumber,
  formatDefaultStatus,
  sanitizeMermaidId,
  toMap,
};
