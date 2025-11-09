const DEFAULT_CENTER_LABEL = "Function Scope";

export function resolveFunctionScope(data, context = {}) {
  const functionsMap = ensureMap(data?.functions);
  if (!functionsMap || functionsMap.size === 0) {
    return {
      message: resolveMessage(
        context.messageOverrides,
        "missingFunctions",
        context.missingFunctionsMessage ?? "No functions recorded in this CommandView artifact.",
        {}
      ),
      functions: null,
    };
  }

  const modulesMap = ensureMap(data?.modules);
  const neighborhoods = ensureMap(data?.neighborhoods);
  const selections = context?.selections ?? {};
  const currentLevel = context?.currentLevel ?? "level0";
  const messageOverrides = context?.messageOverrides ?? {};

  const baseLabel = typeof context?.centerLabelBase === "string" && context.centerLabelBase.trim().length > 0
    ? context.centerLabelBase.trim()
    : DEFAULT_CENTER_LABEL;

  const pipeline = buildResolverPipeline(currentLevel, context);
  for (const resolver of pipeline) {
    const scope = resolver({ functionsMap, modulesMap, neighborhoods, selections, baseLabel, messageOverrides });
    if (!scope) {
      continue;
    }
    if (scope.functions instanceof Map) {
      if (scope.functions.size > 0) {
        return normalizeScope(scope, baseLabel, context);
      }
      if (scope.emptyMessage) {
        return normalizeScope(scope, baseLabel, context);
      }
    } else if (scope.message) {
      return scope;
    }
  }

  return normalizeScope({
    functions: functionsMap,
    centerLabel: `${baseLabel}`,
    statusContext: null,
  }, baseLabel, context);
}

function buildResolverPipeline(levelKey, context) {
  const chain = [];
  switch (levelKey) {
    case "level4":
      chain.push(resolveFunctionNeighborhoodScope);
      chain.push(resolveModuleScope);
      chain.push(resolveDomainScope);
      chain.push(resolveRootScope);
      break;
    case "level3":
    case "level2":
      chain.push(resolveModuleScope);
      chain.push(resolveDomainScope);
      chain.push(resolveRootScope);
      break;
    case "level1":
      chain.push(resolveDomainScope);
      chain.push(resolveRootScope);
      break;
    default:
      chain.push(resolveRootScope);
      break;
  }
  chain.push(resolveRepositoryScope);
  return chain;
}

function resolveFunctionNeighborhoodScope(context) {
  const functionId = context.selections?.functionId;
  const neighborhoods = context.neighborhoods;
  const functionsMap = context.functionsMap;
  if (!functionId || !(neighborhoods instanceof Map)) {
    return null;
  }
  const detail = neighborhoods.get(functionId);
  if (!detail) {
    return null;
  }

  const ids = new Set();
  ids.add(functionId);
  if (Array.isArray(detail.neighbors)) {
    detail.neighbors.forEach((neighbor) => {
      if (!neighbor) {
        return;
      }
      if (typeof neighbor === "object" && neighbor.id) {
        ids.add(neighbor.id);
      } else if (typeof neighbor === "string") {
        ids.add(neighbor);
      }
    });
  }

  const subset = cloneSubset(functionsMap, Array.from(ids));
  const focusName = detail.focus?.name ?? functionId;
  const centerLabel = `${context.baseLabel}\nFunction: ${focusName}`;
  const statusContext = `function neighborhood around ${focusName}`;
  const scope = {
    functions: subset,
    centerLabel,
    statusContext,
  };
  if (subset.size === 0) {
    scope.emptyMessage = resolveMessage(
      context.messageOverrides,
      "neighborhoodEmpty",
      `Function ${focusName} has no metrics recorded for this scope.`,
      { focusName }
    );
  }
  return scope;
}

function resolveModuleScope(context) {
  const moduleId = context.selections?.moduleId;
  const modulesMap = context.modulesMap;
  const functionsMap = context.functionsMap;
  if (!moduleId || !(modulesMap instanceof Map)) {
    return null;
  }
  const moduleRecord = modulesMap.get(moduleId);
  const functionIds = Array.isArray(moduleRecord?.functions) ? moduleRecord.functions : [];
  const subset = cloneSubset(functionsMap, functionIds);
  const centerLabel = `${context.baseLabel}\nModule: ${moduleId}`;
  const statusContext = `module ${moduleId}`;
  const scope = {
    functions: subset,
    centerLabel,
    statusContext,
  };
  if (!moduleRecord) {
    scope.emptyMessage = resolveMessage(
      context.messageOverrides,
      "moduleMissing",
      `Module ${moduleId} is not present in normalized data.`,
      { moduleId }
    );
  } else if (subset.size === 0) {
    scope.emptyMessage = resolveMessage(
      context.messageOverrides,
      "moduleEmpty",
      `Module ${moduleId} has no functions recorded for this scope.`,
      { moduleId }
    );
  }
  return scope;
}

function resolveDomainScope(context) {
  const domainId = context.selections?.domainId;
  const modulesMap = context.modulesMap;
  const functionsMap = context.functionsMap;
  if (!domainId || !(modulesMap instanceof Map)) {
    return null;
  }

  const collected = [];
  let matched = false;
  modulesMap.forEach((moduleRecord) => {
    if (!moduleRecord || typeof moduleRecord.moduleId !== "string") {
      return;
    }
    if (deriveDomainId(moduleRecord.moduleId) === domainId) {
      matched = true;
      const functionIds = Array.isArray(moduleRecord.functions) ? moduleRecord.functions : [];
      functionIds.forEach((fnId) => {
        collected.push(fnId);
      });
    }
  });

  const subset = cloneSubset(functionsMap, collected);
  const centerLabel = `${context.baseLabel}\nDomain: ${domainId}`;
  const statusContext = `domain ${domainId}`;
  const scope = {
    functions: subset,
    centerLabel,
    statusContext,
  };
  if (!matched) {
    scope.emptyMessage = resolveMessage(
      context.messageOverrides,
      "domainMissingModules",
      `Domain ${domainId} has no modules recorded for this scope.`,
      { domainId }
    );
  } else if (subset.size === 0) {
    scope.emptyMessage = resolveMessage(
      context.messageOverrides,
      "domainEmpty",
      `Domain ${domainId} has no functions recorded for this scope.`,
      { domainId }
    );
  }
  return scope;
}

function resolveRootScope(context) {
  const rootId = context.selections?.rootId;
  const modulesMap = context.modulesMap;
  const functionsMap = context.functionsMap;
  if (!rootId || !(modulesMap instanceof Map)) {
    return null;
  }

  const collected = [];
  let matched = false;
  modulesMap.forEach((moduleRecord) => {
    if (!moduleRecord || typeof moduleRecord.moduleId !== "string") {
      return;
    }
    if (deriveRootSegment(moduleRecord.moduleId) === rootId) {
      matched = true;
      const functionIds = Array.isArray(moduleRecord.functions) ? moduleRecord.functions : [];
      functionIds.forEach((fnId) => {
        collected.push(fnId);
      });
    }
  });

  const subset = cloneSubset(functionsMap, collected);
  const centerLabel = `${context.baseLabel}\nRoot: ${rootId}`;
  const statusContext = `root ${rootId}`;
  const scope = {
    functions: subset,
    centerLabel,
    statusContext,
  };
  if (!matched) {
    scope.emptyMessage = resolveMessage(
      context.messageOverrides,
      "rootMissingModules",
      `Root ${rootId} has no modules recorded for this scope.`,
      { rootId }
    );
  } else if (subset.size === 0) {
    scope.emptyMessage = resolveMessage(
      context.messageOverrides,
      "rootEmpty",
      `Root ${rootId} has no functions recorded for this scope.`,
      { rootId }
    );
  }
  return scope;
}

function resolveRepositoryScope(context) {
  return {
    functions: context.functionsMap,
    centerLabel: context.baseLabel,
    statusContext: null,
  };
}

function cloneSubset(functionsMap, ids) {
  const subset = new Map();
  if (!Array.isArray(ids)) {
    return subset;
  }
  ids.forEach((id) => {
    if (functionsMap.has(id)) {
      subset.set(id, functionsMap.get(id));
    }
  });
  return subset;
}

function ensureMap(value) {
  if (value instanceof Map) {
    return value;
  }
  return null;
}

function deriveRootSegment(moduleId) {
  if (!moduleId || typeof moduleId !== "string") {
    return "root";
  }
  const sanitized = moduleId.replace(/\//g, ".");
  const [root] = sanitized.split(".");
  return root || "root";
}

function deriveDomainId(moduleId) {
  if (!moduleId || typeof moduleId !== "string") {
    return "root";
  }
  const segments = moduleId.replace(/\//g, ".").split(".");
  if (segments.length >= 2) {
    return `${segments[0]}.${segments[1]}`;
  }
  return segments[0] ?? "root";
}

function normalizeScope(scope, baseLabel, context) {
  return {
    functions: scope.functions,
    centerLabel: scope.centerLabel ?? baseLabel,
    statusContext: scope.statusContext ?? null,
    emptyMessage: scope.emptyMessage,
    message: scope.message ?? null,
    missingFunctionsMessage: context.missingFunctionsMessage ?? null,
  };
}

function resolveMessage(overrides, key, fallback, payload) {
  const messageOverrides = overrides ?? {};
  const override = messageOverrides[key];
  if (override === undefined) {
    return fallback;
  }
  if (typeof override === "function") {
    try {
      const result = override({ ...payload });
      return typeof result === "string" && result.trim().length > 0 ? result : fallback;
    } catch (_err) {
      return fallback;
    }
  }
  if (typeof override === "string" && override.trim().length > 0) {
    return override;
  }
  return fallback;
}

export const __test__ = {
  resolveFunctionNeighborhoodScope,
  resolveModuleScope,
  resolveDomainScope,
  resolveRootScope,
  resolveRepositoryScope,
  cloneSubset,
  deriveRootSegment,
  deriveDomainId,
  normalizeScope,
  resolveMessage,
};
