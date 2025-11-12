const DEFAULT_VIEW_LABEL = "Code Flow · Method Call Chain";
const DEFAULT_MAX_DEPTH = 4;
const DEFAULT_MAX_BRANCH = 4;

export function buildMethodCallChainDiagram(modules, functions, callGraph, options = {}) {
  const moduleMap = toMap(modules);
  if (!moduleMap || moduleMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "Module metadata has not been normalized for this CommandView artifact.",
    };
  }

  const functionMap = toMap(functions);
  if (!functionMap || functionMap.size === 0) {
    return {
      message: options.missingFunctionsMessage ?? "No function records are available to build method call chains.",
    };
  }

  const callGraphMap = toMapOfArrays(callGraph);
  if (!callGraphMap || callGraphMap.size === 0) {
    return {
      message: options.missingCallGraphMessage ?? "Call graph edges are not present in this CommandView artifact.",
    };
  }

  const allowedFunctionIds = buildNormalizedIdSet(options.allowedFunctionIds);
  const methodIndex = buildMethodIndex(functionMap, allowedFunctionIds);
  if (methodIndex.size === 0) {
    return {
      message: options.missingMethodsMessage ?? "No class methods were detected in this scope.",
    };
  }

  const startingMethodId = determineStartingMethodId({
    methodIndex,
    preferredFunctionId: options.focusFunctionId,
    allowedFunctionIds,
    moduleId: options.moduleId,
    moduleMap,
  });

  if (!startingMethodId || !methodIndex.has(startingMethodId)) {
    return {
      message: options.unresolvedFocusMessage ?? "Unable to identify a starting method for the call chain.",
    };
  }

  const traversalOptions = {
    maxDepth: normalizePositiveInteger(options.maxDepth, DEFAULT_MAX_DEPTH),
    maxBranch: normalizePositiveInteger(options.maxBranch, DEFAULT_MAX_BRANCH),
  };

  const chain = buildMethodChain(startingMethodId, callGraphMap, methodIndex, allowedFunctionIds, traversalOptions);
  if (chain.edges.length === 0) {
    const descriptor = methodIndex.get(startingMethodId)?.descriptor;
    const methodLabel = descriptor ? descriptor.fullDisplayName : startingMethodId;
    return {
      message:
        options.emptyChainMessage ?? `No chained method calls were recorded for ${methodLabel}.`,
    };
  }

  const participants = buildParticipants(chain.methods, methodIndex);
  const participantsByClass = new Map(participants.map((entry) => [entry.classKey, entry]));

  const lines = ["sequenceDiagram", "autonumber"];
  participants.forEach((participant) => {
    lines.push(
      `  participant ${participant.id} as ${escapeMermaidLabel(`${participant.className}\n(${participant.moduleId})`)}`
    );
  });

  const startDescriptor = methodIndex.get(startingMethodId)?.descriptor ?? null;
  if (startDescriptor) {
    const owner = participantsByClass.get(startDescriptor.classKey);
    if (owner) {
      lines.push(
        `  Note over ${owner.id}: ${escapeMermaidLabel(`Start ${startDescriptor.displayName}`)}`
      );
    }
  }

  chain.edges.forEach((edge) => {
    const sourceDescriptor = methodIndex.get(edge.sourceId)?.descriptor;
    const targetDescriptor = methodIndex.get(edge.targetId)?.descriptor;
    if (!sourceDescriptor || !targetDescriptor) {
      return;
    }
    const sourceParticipant = participantsByClass.get(sourceDescriptor.classKey);
    const targetParticipant = participantsByClass.get(targetDescriptor.classKey);
    if (!sourceParticipant || !targetParticipant) {
      return;
    }
    const arrow = sourceParticipant.id === targetParticipant.id ? "-->>" : "->>";
    const label = `${sourceDescriptor.methodName}() → ${targetDescriptor.methodName}()`;
    lines.push(
      `  ${sourceParticipant.id} ${arrow} ${targetParticipant.id}: ${escapeMermaidLabel(label)}`
    );
  });

  const scopeDescription = options.scopeDescription ?? "repository";
  const stats = {
    startMethod: startDescriptor?.fullDisplayName ?? startingMethodId,
    methodCount: chain.methods.size,
    classCount: participants.length,
    depth: chain.depth,
    edgeCount: chain.edges.length,
    moduleCount: countModules(chain.methods, methodIndex),
    truncated: chain.truncated,
  };

  const statusMessage = buildStatusMessage(scopeDescription, stats, options.fallbackNotice);
  const statusDetails = buildStatusDetails({
    stats,
    chain,
    methodIndex,
    scopeDescription,
    fallbackNotice: options.fallbackNotice,
  });

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    statusDetails,
    stats,
  };
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
    candidate.forEach((entry, index) => {
      if (!entry || typeof entry !== "object") {
        return;
      }
      const key = entry.id ?? entry.moduleId ?? entry.module_id ?? String(index);
      map.set(key, entry);
    });
    return map;
  }
  if (typeof candidate === "object") {
    const map = new Map();
    Object.entries(candidate).forEach(([key, value]) => {
      map.set(key, value);
    });
    return map;
  }
  return null;
}

function toMapOfArrays(candidate) {
  if (!candidate) {
    return null;
  }
  if (candidate instanceof Map) {
    return candidate;
  }
  if (Array.isArray(candidate)) {
    const map = new Map();
    candidate.forEach((entry) => {
      if (!Array.isArray(entry) || entry.length < 2) {
        return;
      }
      const [sourceId, targetsRaw] = entry;
      if (!sourceId) {
        return;
      }
      const list = Array.isArray(targetsRaw)
        ? targetsRaw
        : targetsRaw instanceof Set
        ? Array.from(targetsRaw)
        : [];
      map.set(sourceId, list);
    });
    return map;
  }
  if (typeof candidate === "object") {
    const map = new Map();
    Object.entries(candidate).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        map.set(key, value);
      } else if (value instanceof Set) {
        map.set(key, Array.from(value));
      }
    });
    return map;
  }
  return null;
}

function buildNormalizedIdSet(candidate) {
  if (!candidate) {
    return null;
  }
  if (candidate instanceof Set) {
    const normalized = Array.from(candidate).filter((value) => typeof value === "string" && value.length > 0);
    return normalized.length > 0 ? new Set(normalized) : null;
  }
  if (Array.isArray(candidate)) {
    const normalized = candidate.filter((value) => typeof value === "string" && value.length > 0);
    return normalized.length > 0 ? new Set(normalized) : null;
  }
  return null;
}

function buildMethodIndex(functionMap, allowedFunctionIds) {
  const index = new Map();
  const allowList = allowedFunctionIds instanceof Set && allowedFunctionIds.size > 0 ? allowedFunctionIds : null;
  functionMap.forEach((record, functionId) => {
    if (typeof functionId !== "string" || functionId.length === 0) {
      return;
    }
    if (allowList && !allowList.has(functionId)) {
      return;
    }
    const descriptor = parseMethodDescriptor(functionId);
    if (!descriptor) {
      return;
    }
    index.set(functionId, { record, descriptor });
  });
  return index;
}

function parseMethodDescriptor(functionId) {
  if (typeof functionId !== "string" || functionId.length === 0) {
    return null;
  }
  const separatorIndex = functionId.indexOf("::");
  if (separatorIndex < 0) {
    return null;
  }
  const moduleId = functionId.slice(0, separatorIndex);
  const remainder = functionId.slice(separatorIndex + 2);
  const dotIndex = remainder.indexOf(".");
  if (dotIndex < 0) {
    return null;
  }
  const className = remainder.slice(0, dotIndex);
  const methodName = remainder.slice(dotIndex + 1);
  if (!className || !methodName) {
    return null;
  }
  const classKey = `${moduleId}.${className}`;
  return {
    functionId,
    moduleId,
    className,
    methodName,
    classKey,
    displayName: `${className}.${methodName}`,
    fullDisplayName: `${moduleId} :: ${className}.${methodName}`,
  };
}

function determineStartingMethodId({ methodIndex, preferredFunctionId, allowedFunctionIds, moduleId, moduleMap }) {
  if (preferredFunctionId && methodIndex.has(preferredFunctionId)) {
    return preferredFunctionId;
  }

  const allowList = allowedFunctionIds instanceof Set && allowedFunctionIds.size > 0 ? allowedFunctionIds : null;
  if (allowList) {
    for (const candidateId of allowList) {
      if (methodIndex.has(candidateId)) {
        return candidateId;
      }
    }
  }

  if (moduleId && moduleMap instanceof Map && moduleMap.has(moduleId)) {
    const moduleRecord = moduleMap.get(moduleId);
    const moduleFunctions = Array.isArray(moduleRecord?.functions) ? moduleRecord.functions : [];
    for (const fnId of moduleFunctions) {
      if (methodIndex.has(fnId)) {
        return fnId;
      }
    }
  }

  const iterator = methodIndex.keys();
  const first = iterator.next();
  return first.done ? null : first.value;
}

function normalizePositiveInteger(candidate, fallback) {
  const numeric = Number(candidate);
  if (Number.isFinite(numeric) && numeric > 0) {
    return Math.floor(numeric);
  }
  return fallback;
}

function buildMethodChain(startingMethodId, callGraph, methodIndex, allowedFunctionIds, options) {
  const allowList = allowedFunctionIds instanceof Set && allowedFunctionIds.size > 0 ? allowedFunctionIds : null;
  const methods = new Set([startingMethodId]);
  const edges = [];
  const queue = [{ id: startingMethodId, depth: 0 }];
  const visited = new Set([startingMethodId]);
  let depth = 0;
  let truncated = false;

  while (queue.length > 0) {
    const current = queue.shift();
    const currentId = current.id;
    depth = Math.max(depth, current.depth);
    if (current.depth >= options.maxDepth) {
      continue;
    }
    const rawTargets = callGraph.get(currentId);
    const targets = Array.isArray(rawTargets)
      ? rawTargets
      : rawTargets instanceof Set
      ? Array.from(rawTargets)
      : [];

    const filteredTargets = targets
      .filter((targetId) => {
        if (!methodIndex.has(targetId)) {
          return false;
        }
        if (allowList && !allowList.has(targetId)) {
          return false;
        }
        return true;
      })
      .sort((left, right) => left.localeCompare(right));

    if (filteredTargets.length > options.maxBranch) {
      truncated = true;
    }

    filteredTargets.slice(0, options.maxBranch).forEach((targetId) => {
      edges.push({ sourceId: currentId, targetId, depth: current.depth + 1 });
      methods.add(targetId);
      if (!visited.has(targetId)) {
        visited.add(targetId);
        queue.push({ id: targetId, depth: current.depth + 1 });
      }
    });
  }

  return {
    methods,
    edges,
    depth,
    truncated,
  };
}

function buildParticipants(methodIds, methodIndex) {
  const participants = new Map();
  methodIds.forEach((methodId) => {
    const entry = methodIndex.get(methodId);
    if (!entry) {
      return;
    }
    const { descriptor } = entry;
    const existing = participants.get(descriptor.classKey);
    if (existing) {
      existing.methods.add(methodId);
      return;
    }
    participants.set(descriptor.classKey, {
      id: sanitizeParticipantId(descriptor.classKey),
      classKey: descriptor.classKey,
      className: descriptor.className,
      moduleId: descriptor.moduleId,
      methods: new Set([methodId]),
    });
  });
  return Array.from(participants.values()).sort((left, right) => left.classKey.localeCompare(right.classKey));
}

function sanitizeParticipantId(identifier) {
  const base = typeof identifier === "string" ? identifier : String(identifier ?? "participant");
  let sanitized = base.replace(/[^a-zA-Z0-9_]/g, "_");
  if (!sanitized) {
    sanitized = "participant";
  }
  if (/^[0-9]/.test(sanitized)) {
    sanitized = `p_${sanitized}`;
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

function countModules(methodIds, methodIndex) {
  const modules = new Set();
  methodIds.forEach((methodId) => {
    const entry = methodIndex.get(methodId);
    const moduleId = entry?.descriptor?.moduleId;
    if (moduleId) {
      modules.add(moduleId);
    }
  });
  return modules.size;
}

function buildStatusMessage(scopeDescription, stats, fallbackNotice) {
  const base = `Rendered Method Call Chain for ${scopeDescription} (${stats.methodCount} methods, ${stats.classCount} classes, depth ${stats.depth}).`;
  if (!fallbackNotice) {
    return base;
  }
  return `${base} ${fallbackNotice}`.trim();
}

function buildStatusDetails({ stats, chain, methodIndex, scopeDescription, fallbackNotice }) {
  const details = [];

  if (fallbackNotice) {
    details.push({
      type: "info",
      title: "Scope fallback applied",
      description: fallbackNotice,
    });
  }

  if (chain.truncated) {
    details.push({
      type: "info",
      title: "Chain truncated",
      description: "Displayed call chain limited to avoid sequence diagram overload.",
    });
  }

  const stepItems = chain.edges.map((edge, index) => {
    const sourceDescriptor = methodIndex.get(edge.sourceId)?.descriptor;
    const targetDescriptor = methodIndex.get(edge.targetId)?.descriptor;
    return {
      label: `Step ${index + 1}`,
      value: `${sourceDescriptor?.displayName ?? edge.sourceId} → ${targetDescriptor?.displayName ?? edge.targetId}`,
    };
  });

  if (stepItems.length > 0) {
    details.push({
      type: "list",
      title: "Call Chain",
      description: `Depth ${stats.depth}; start ${stats.startMethod}`,
      items: stepItems,
    });
  }

  const participantItems = buildParticipantItems(chain.methods, methodIndex);
  if (participantItems.length > 0) {
    details.push({
      type: "list",
      title: "Participants",
      description: `Classes involved in ${scopeDescription} selection.`,
      items: participantItems,
    });
  }

  return details;
}

function buildParticipantItems(methodIds, methodIndex) {
  const classes = new Map();
  methodIds.forEach((methodId) => {
    const entry = methodIndex.get(methodId);
    if (!entry) {
      return;
    }
    const { descriptor } = entry;
    const classEntry = classes.get(descriptor.classKey) ?? {
      className: descriptor.className,
      moduleId: descriptor.moduleId,
      methods: new Set(),
    };
    classEntry.methods.add(descriptor.methodName);
    classes.set(descriptor.classKey, classEntry);
  });

  return Array.from(classes.values())
    .map((info) => ({
      label: `${info.className} (${info.moduleId})`,
      value: `Methods: ${Array.from(info.methods).sort().join(", ")}`,
    }))
    .sort((left, right) => left.label.localeCompare(right.label));
}

export const __test__ = {
  parseMethodDescriptor,
  buildMethodIndex,
  buildMethodChain,
  sanitizeParticipantId,
  escapeMermaidLabel,
};
