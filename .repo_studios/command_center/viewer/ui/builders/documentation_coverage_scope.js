const DEFAULT_CENTER_LABEL = "Documentation Coverage Map";

export function resolveDocumentationCoverageScope(data, context) {
  const functionsMap = ensureMap(data?.functions);
  if (!functionsMap || functionsMap.size === 0) {
    return {
      message: "No functions recorded in this CommandView artifact.",
      functions: null,
    };
  }

  const modulesMap = ensureMap(data?.modules);
  const neighborhoods = ensureMap(data?.neighborhoods);
  const selections = context?.selections ?? {};
  const currentLevel = context?.currentLevel ?? "level0";

  const pipeline = buildResolverPipeline(currentLevel);
  for (const resolver of pipeline) {
    const scope = resolver({ functionsMap, modulesMap, neighborhoods, selections });
    if (!scope) {
      continue;
    }
    if (scope.functions instanceof Map) {
      if (scope.functions.size > 0) {
        return normalizeScope(scope);
      }
      if (scope.emptyMessage) {
        return normalizeScope(scope);
      }
    } else if (scope.message) {
      return scope;
    }
  }

  return normalizeScope({
    functions: functionsMap,
    centerLabel: DEFAULT_CENTER_LABEL,
    statusContext: null,
  });
}

function buildResolverPipeline(levelKey) {
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

  const ids = [];
  ids.push(functionId);
  if (Array.isArray(detail.neighbors)) {
    detail.neighbors.forEach((neighbor) => {
      if (neighbor && typeof neighbor === "object" && neighbor.id) {
        ids.push(neighbor.id);
      } else if (typeof neighbor === "string") {
        ids.push(neighbor);
      }
    });
  }

  const subset = cloneSubset(functionsMap, ids);
  const focusName = detail.focus?.name ?? functionId;
  const centerLabel = `${DEFAULT_CENTER_LABEL}\nFunction: ${focusName}`;
  const statusContext = `function neighborhood around ${focusName}`;
  const scope = {
    functions: subset,
    centerLabel,
    statusContext,
  };
  if (subset.size === 0) {
    scope.emptyMessage = `Function ${focusName} has no documentation metrics recorded.`;
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
  const centerLabel = `${DEFAULT_CENTER_LABEL}\nModule: ${moduleId}`;
  const statusContext = `module ${moduleId}`;
  const scope = {
    functions: subset,
    centerLabel,
    statusContext,
  };
  if (!moduleRecord) {
    scope.emptyMessage = `Module ${moduleId} is not present in normalized data.`;
  } else if (subset.size === 0) {
    scope.emptyMessage = `Module ${moduleId} has no functions recorded for documentation coverage.`;
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
  const centerLabel = `${DEFAULT_CENTER_LABEL}\nDomain: ${domainId}`;
  const statusContext = `domain ${domainId}`;
  const scope = {
    functions: subset,
    centerLabel,
    statusContext,
  };
  if (!matched) {
    scope.emptyMessage = `Domain ${domainId} has no modules recorded for documentation coverage.`;
  } else if (subset.size === 0) {
    scope.emptyMessage = `Domain ${domainId} has no functions recorded for documentation coverage.`;
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
  const centerLabel = `${DEFAULT_CENTER_LABEL}\nRoot: ${rootId}`;
  const statusContext = `root ${rootId}`;
  const scope = {
    functions: subset,
    centerLabel,
    statusContext,
  };
  if (!matched) {
    scope.emptyMessage = `Root ${rootId} has no modules recorded for documentation coverage.`;
  } else if (subset.size === 0) {
    scope.emptyMessage = `Root ${rootId} has no functions recorded for documentation coverage.`;
  }
  return scope;
}

function resolveRepositoryScope(context) {
  const functionsMap = context.functionsMap;
  return {
    functions: functionsMap,
    centerLabel: DEFAULT_CENTER_LABEL,
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

function normalizeScope(scope) {
  return {
    functions: scope.functions,
    centerLabel: scope.centerLabel ?? DEFAULT_CENTER_LABEL,
    statusContext: scope.statusContext ?? null,
    emptyMessage: scope.emptyMessage,
    message: scope.message ?? null,
  };
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
};
