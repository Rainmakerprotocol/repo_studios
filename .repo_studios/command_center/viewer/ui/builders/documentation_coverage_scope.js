import { resolveFunctionScope } from "./function_scope.js";

const DEFAULT_CENTER_LABEL = "Documentation Coverage Map";

export function resolveDocumentationCoverageScope(data, context = {}) {
  return resolveFunctionScope(data, {
    ...context,
    centerLabelBase: DEFAULT_CENTER_LABEL,
    missingFunctionsMessage: "No functions recorded in this CommandView artifact.",
    messageOverrides: {
      ...context.messageOverrides,
      moduleEmpty: ({ moduleId }) => `Module ${moduleId} has no functions recorded for documentation coverage.`,
      domainEmpty: ({ domainId }) => `Domain ${domainId} has no functions recorded for documentation coverage.`,
      domainMissingModules: ({ domainId }) => `Domain ${domainId} has no modules recorded for documentation coverage.`,
      rootEmpty: ({ rootId }) => `Root ${rootId} has no functions recorded for documentation coverage.`,
      rootMissingModules: ({ rootId }) => `Root ${rootId} has no modules recorded for documentation coverage.`,
      neighborhoodEmpty: ({ focusName }) => `Function ${focusName} has no documentation metrics recorded.`,
    },
  });
}

export const __test__ = {
  resolveDocumentationCoverageScope,
};

