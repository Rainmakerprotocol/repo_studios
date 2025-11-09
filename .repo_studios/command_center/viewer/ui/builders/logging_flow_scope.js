import { resolveFunctionScope } from "./function_scope.js";

const DEFAULT_CENTER_LABEL = "Logging Flow";

export function resolveLoggingFlowScope(data, context = {}) {
  return resolveFunctionScope(data, {
    ...context,
    centerLabelBase: DEFAULT_CENTER_LABEL,
    missingFunctionsMessage: "No functions recorded in this CommandView artifact.",
    messageOverrides: {
      ...context.messageOverrides,
      moduleEmpty: ({ moduleId }) => `Module ${moduleId} has no logging events recorded for this scope.`,
      moduleMissing: ({ moduleId }) => `Module ${moduleId} is not present in normalized data.`,
      domainEmpty: ({ domainId }) => `Domain ${domainId} has no logging events recorded for this scope.`,
      domainMissingModules: ({ domainId }) => `Domain ${domainId} has no modules recorded for this scope.`,
      rootEmpty: ({ rootId }) => `Root ${rootId} has no logging events recorded for this scope.`,
      rootMissingModules: ({ rootId }) => `Root ${rootId} has no modules recorded for this scope.`,
      neighborhoodEmpty: ({ focusName }) => `Function ${focusName} has no logging events recorded for this scope.`,
    },
  });
}

export const __test__ = {
  resolveLoggingFlowScope,
};
