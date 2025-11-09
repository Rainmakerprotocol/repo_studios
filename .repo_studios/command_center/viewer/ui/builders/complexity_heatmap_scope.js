import { resolveFunctionScope } from "./function_scope.js";

const DEFAULT_CENTER_LABEL = "Complexity Heatmap";

export function resolveComplexityHeatmapScope(data, context = {}) {
  return resolveFunctionScope(data, {
    ...context,
    centerLabelBase: DEFAULT_CENTER_LABEL,
    missingFunctionsMessage: "No complexity metrics recorded in this CommandView artifact.",
    messageOverrides: {
      ...context.messageOverrides,
      moduleEmpty: ({ moduleId }) => `Module ${moduleId} has no complexity metrics recorded for this scope.`,
      moduleMissing: ({ moduleId }) => `Module ${moduleId} is not present in normalized data.`,
      domainEmpty: ({ domainId }) => `Domain ${domainId} has no complexity metrics recorded for this scope.`,
      domainMissingModules: ({ domainId }) => `Domain ${domainId} has no modules recorded for this scope.`,
      rootEmpty: ({ rootId }) => `Root ${rootId} has no complexity metrics recorded for this scope.`,
      rootMissingModules: ({ rootId }) => `Root ${rootId} has no modules recorded for this scope.`,
      neighborhoodEmpty: ({ focusName }) => `Function ${focusName} has no complexity metrics recorded.`,
    },
  });
}

export const __test__ = {
  resolveComplexityHeatmapScope,
};
