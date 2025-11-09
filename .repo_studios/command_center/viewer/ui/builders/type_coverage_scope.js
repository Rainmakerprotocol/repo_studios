import { resolveFunctionScope } from "./function_scope.js";

const DEFAULT_CENTER_LABEL = "Type Coverage Map";

export function resolveTypeCoverageScope(data, context = {}) {
  return resolveFunctionScope(data, {
    ...context,
    centerLabelBase: DEFAULT_CENTER_LABEL,
    missingFunctionsMessage: "No functions recorded in this CommandView artifact.",
    messageOverrides: {
      ...context.messageOverrides,
      moduleEmpty: ({ moduleId }) => `Module ${moduleId} has no functions recorded for type coverage.`,
      moduleMissing: ({ moduleId }) => `Module ${moduleId} is not present in normalized data.`,
      domainEmpty: ({ domainId }) => `Domain ${domainId} has no functions recorded for type coverage.`,
      domainMissingModules: ({ domainId }) => `Domain ${domainId} has no modules recorded for type coverage.`,
      rootEmpty: ({ rootId }) => `Root ${rootId} has no functions recorded for type coverage.`,
      rootMissingModules: ({ rootId }) => `Root ${rootId} has no modules recorded for type coverage.`,
      neighborhoodEmpty: ({ focusName }) => `Function ${focusName} has no type coverage metrics recorded.`,
    },
  });
}

export const __test__ = {
  resolveTypeCoverageScope,
};
