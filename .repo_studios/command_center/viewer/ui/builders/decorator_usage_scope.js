import { resolveFunctionScope } from "./function_scope.js";

const DEFAULT_CENTER_LABEL = "Decorator Usage Map";

export function resolveDecoratorUsageScope(data, context = {}) {
  return resolveFunctionScope(data, {
    ...context,
    centerLabelBase: DEFAULT_CENTER_LABEL,
    missingFunctionsMessage: "No functions recorded in this CommandView artifact.",
    messageOverrides: {
      ...context.messageOverrides,
      moduleEmpty: ({ moduleId }) => `Module ${moduleId} has no decorator usage recorded for this scope.`,
      moduleMissing: ({ moduleId }) => `Module ${moduleId} is not present in normalized data for decorator usage.`,
      domainEmpty: ({ domainId }) => `Domain ${domainId} has no decorator usage recorded for this scope.`,
      domainMissingModules: ({ domainId }) => `Domain ${domainId} has no modules recorded for decorator usage.`,
      rootEmpty: ({ rootId }) => `Root ${rootId} has no decorator usage recorded for this scope.`,
      rootMissingModules: ({ rootId }) => `Root ${rootId} has no modules recorded for decorator usage.`,
      neighborhoodEmpty: ({ focusName }) => `Function ${focusName} has no decorator usage recorded.`,
    },
  });
}

export const __test__ = {
  resolveDecoratorUsageScope,
};
