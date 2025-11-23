import { buildComplexityHeatmapDiagram } from "./builders/complexity_heatmap.js";
import { buildCyclomaticComplexityMapDiagram } from "./builders/cyclomatic_complexity_map.js";
import { resolveComplexityHeatmapScope } from "./builders/complexity_heatmap_scope.js";
import { buildDecoratorUsageMapDiagram } from "./builders/decorator_usage_map.js";
import { resolveDecoratorUsageScope } from "./builders/decorator_usage_scope.js";
import { buildDocumentationCoverageMapDiagram } from "./builders/documentation_coverage_map.js";
import { resolveDocumentationCoverageScope } from "./builders/documentation_coverage_scope.js";
import { buildExportContractMatrixDiagram } from "./builders/export_contract_matrix.js";
import { buildExternalVsInternalDependencyMapDiagram } from "./builders/external_vs_internal_dependency_map.js";
import { buildCircularImportDetectionDiagram } from "./builders/circular_import_detection.js";
import { buildFunctionCallGraphDiagram } from "./builders/function_call_graph.js";
import { buildFunctionInventoryOverviewDiagram } from "./builders/function_inventory_overview.js";
import { buildScreeningTimelineDiagram } from "./builders/screening_signal_timeline.js";
import { buildLoggingFlowDiagram } from "./builders/logging_flow.js";
import { resolveLoggingFlowScope } from "./builders/logging_flow_scope.js";
import { buildModuleDependencyGraphDiagram } from "./builders/module_dependency_graph.js";
import { buildLayerArchitectureValidationDiagram } from "./builders/layer_architecture_validation.js";
import { buildTypeCoverageMapDiagram } from "./builders/type_coverage_map.js";
import { resolveTypeCoverageScope } from "./builders/type_coverage_scope.js";
import { buildCallbackRegistrationMapDiagram } from "./builders/callback_registration_map.js";
import { buildDynamicCodeWatchlistDiagram } from "./builders/dynamic_code_watchlist.js";
import { buildEntrypointTraceDiagram } from "./builders/entrypoint_trace_diagram.js";
import { buildClassInheritanceHierarchyDiagram } from "./builders/class_inheritance_hierarchy.js";
import { buildMethodCallChainDiagram } from "./builders/method_call_chain.js";
import { buildGlobalVariableUsageMapDiagram } from "./builders/global_variable_usage_map.js";
import { buildIoEffectsDiagram } from "./builders/io_effects_diagram.js";
import { buildExceptionFlowMapDiagram } from "./builders/exception_flow_map.js";
import { buildPublicVsPrivateApiDiagram } from "./builders/public_vs_private_api.js";
import { buildCrossModuleFunctionReferencesDiagram } from "./builders/cross_module_function_references.js";
import { buildImportChainDepthDiagram } from "./builders/import_chain_depth.js";
import { buildTestCoverageMappingDiagram } from "./builders/test_coverage_mapping.js";
import { buildGitChurnRiskMapDiagram } from "./builders/git_churn_risk_map.js";
import { buildDeadCodeDetectionDiagram } from "./builders/dead_code_detection.js";

console.log('[viewer.js] Script loading started');

const DEFAULT_REPORTS_BASE_URL = "/.repo_studios/command_center/reports/";
const ABSOLUTE_URL_PATTERN = /^[a-zA-Z][a-zA-Z0-9+\-.]*:\/\//;
const SUPPORTED_INVENTORY_SCHEMA_VERSIONS = new Set([2]);

console.log('[viewer.js] Constants defined, DEFAULT_REPORTS_BASE_URL:', DEFAULT_REPORTS_BASE_URL);
const LEVEL_DEFINITIONS = [
  { value: "level0", label: "Level 0 - Overview" },
  { value: "level1", label: "Level 1 - Domain" },
  { value: "level2", label: "Level 2 - Module" },
  { value: "level3", label: "Level 3 - Functions" },
  { value: "level4", label: "Level 4 - Neighborhood" },
];

const SCRIPT_LAYER_TIERS = Object.freeze([
  {
    id: "producers",
    label: "Producers",
    index: 0,
    modulePrefixes: ["scripts.producers.", "command_center.scripts.producers."],
    pathFragments: ["/scripts/producers/", "/command_center/scripts/producers/"],
  },
  {
    id: "consumers",
    label: "Consumers",
    index: 1,
    modulePrefixes: ["scripts.consumers.", "command_center.scripts.consumers."],
    pathFragments: ["/scripts/consumers/", "/command_center/scripts/consumers/"],
  },
  {
    id: "aggregators",
    label: "Aggregators",
    index: 2,
    modulePrefixes: ["scripts.aggregators.", "command_center.scripts.aggregators."],
    pathFragments: ["/scripts/aggregators/", "/command_center/scripts/aggregators/"],
  },
  {
    id: "orchestrators",
    label: "Orchestrators",
    index: 3,
    modulePrefixes: ["scripts.orchestrators.", "command_center.scripts.orchestrators."],
    pathFragments: ["/scripts/orchestrators/", "/command_center/scripts/orchestrators/"],
  },
  {
    id: "summarizers",
    label: "Summarizers",
    index: 4,
    modulePrefixes: ["scripts.summarizers.", "command_center.scripts.summarizers."],
    pathFragments: ["/scripts/summarizers/", "/command_center/scripts/summarizers/"],
  },
]);

const SCRIPT_LAYER_UNKNOWN = Object.freeze({ id: "unclassified", label: "Unclassified", index: 99 });

const SCRIPT_LAYER_ADJACENCY_DEFAULTS = Object.freeze({
  producers: Object.freeze({
    allowed: Object.freeze(["producers", "consumers"]),
    peer: "Producers may collaborate on shared ingestion utilities.",
    forward: "Producers feed Consumers with normalized inventories.",
    rationale: "Producers hand off raw data to Consumers while keeping shared utilities within the tier.",
    violations: Object.freeze({
      backward: "Producers should not depend on downstream tiers.",
      skip: "Producers must hand data to Consumers before Aggregators or Orchestrators.",
    }),
  }),
  consumers: Object.freeze({
    allowed: Object.freeze(["consumers", "aggregators"]),
    peer: "Consumers may collaborate on shared enrichments.",
    forward: "Consumers emit refined artifacts to Aggregators.",
    rationale: "Consumers refine producer outputs and pass them to Aggregators.",
    violations: Object.freeze({
      backward: "Consumers should not import Summarizers or Orchestrators.",
      skip: "Consumers must hand off to Aggregators before orchestration layers.",
    }),
  }),
  aggregators: Object.freeze({
    allowed: Object.freeze(["aggregators", "orchestrators"]),
    peer: "Aggregators can compose peer modules for composite analyses.",
    forward: "Aggregators feed Orchestrators with blended insights.",
    rationale: "Aggregators blend consumer outputs before orchestration runs.",
    violations: Object.freeze({
      backward: "Aggregators should not depend on downstream execution tiers beyond Orchestrators.",
      skip: "Aggregators must hand off to Orchestrators before Summarizers.",
    }),
  }),
  orchestrators: Object.freeze({
    allowed: Object.freeze(["orchestrators", "summarizers"]),
    peer: "Orchestrators may reuse orchestration helpers within the tier.",
    forward: "Orchestrators drive Summarizers after running pipelines.",
    rationale: "Orchestrators coordinate pipelines and trigger summarization.",
    violations: Object.freeze({
      backward: "Orchestrators should not depend on downstream tiers outside Summarizers.",
      skip: "Orchestrators must invoke Summarizers without skipping tiers.",
    }),
  }),
  summarizers: Object.freeze({
    allowed: Object.freeze(["summarizers"]),
    peer: "Summarizers may share helper utilities.",
    forward: "Summarizers are terminal endpoints in the pipeline.",
    rationale: "Summarizers produce final narratives and should not feed higher tiers.",
    violations: Object.freeze({
      backward: "Summarizers should not call upstream orchestration or aggregation logic.",
      skip: "Summarizers cannot forward data to additional tiers by design.",
    }),
  }),
});

const SCRIPT_LAYER_INDEX_BY_ID = Object.freeze(
  SCRIPT_LAYER_TIERS.reduce(
    (acc, tier) => {
      acc[tier.id] = tier.index;
      return acc;
    },
    { [SCRIPT_LAYER_UNKNOWN.id]: SCRIPT_LAYER_UNKNOWN.index }
  )
);

const ENTRYPOINT_NAME_HINTS = Object.freeze([
  "main",
  "run",
  "cli",
  "entrypoint",
  "execute",
  "start",
  "bootstrap",
]);

const ENTRYPOINT_SUFFIX_HINTS = Object.freeze([
  "_main",
  "_cli",
  "_entrypoint",
  "_runner",
  "_command",
  "_app",
]);

const ENTRYPOINT_REASON = Object.freeze({
  MAIN_GUARD_NAME: "main-guard-name-match",
  CLI_PARSER_NAME: "cli-parser-name-match",
  MAIN_GUARD_ISOLATED: "main-guard-isolated-call",
  CLI_PARSER_ISOLATED: "cli-parser-isolated-call",
});

const VIEW_PACKS = Object.freeze([
  {
    id: "health",
    title: "Health Pack",
    views: [
      {
        id: "function_inventory_overview",
        label: "Function Inventory Overview",
        filename: "function_inventory_overview.mmd",
        description:
          "Summarizes per-module function counts, docstring coverage, and annotation ratios for quick health checks.",
        status: "prototype",
        builder: "functionInventoryOverview",
        requirements: ["inventoryBasics", "docstringQuality", "typeCoverage"],
      },
      {
        id: "screening_signal_timeline",
        label: "Screening Signal Timeline",
        filename: "screening_signal_timeline.mmd",
        description:
          "Timeline outlining when screening scores crossed thresholds to support release planning discussions.",
        status: "prototype",
        builder: "screeningSignalTimelineView",
        requirements: ["screeningHistory"],
      },
    ],
  },
  {
    id: "dependency",
    title: "Dependency Pack",
    views: [
      {
        id: "module_dependency_graph",
        label: "Module Dependency Graph",
        filename: "module_dependency_graph.mmd",
        description:
          "Import dependency graph to highlight hotspots, orphan modules, and cross-module coupling.",
        status: "prototype",
        builder: "moduleDependencyGraphView",
        requirements: ["moduleDependencies"],
      },
      {
        id: "export_contract_matrix",
        label: "Export Contract Matrix",
        filename: "export_contract_matrix.mmd",
        description:
          "Class diagram portraying public exports by type so API boundaries stay visible during reviews.",
        status: "prototype",
        builder: "exportContractMatrixView",
        requirements: ["moduleExports"],
      },
      {
        id: "circular_import_detection",
        label: "Circular Import Detection",
        filename: "circular_import_detection.mmd",
        description:
          "Graph emphasizing import cycles that could trigger module loading issues.",
        status: "prototype",
        builder: "circularImportDetectionView",
        requirements: ["moduleDependencies"],
      },
      {
        id: "layer_architecture_validation",
        label: "Layer Architecture Validation",
        filename: "layer_architecture_validation.mmd",
        description:
          "Layered diagram validating Producers → Consumers → Aggregators → Orchestrators → Summarizers wiring.",
        status: "prototype",
        builder: "layerArchitectureValidationView",
        requirements: ["moduleDependencies"],
        note: "Highlights default layer adjacency violations using normalized tier metadata.",
      },
      {
        id: "external_vs_internal_dependency_map",
        label: "External vs Internal Dependency Map",
        filename: "external_vs_internal_dependency_map.mmd",
        description:
          "Dependency map separating standard library, third-party, and internal modules to surface external attack surfaces.",
        status: "prototype",
        builder: "externalVsInternalDependencyMapView",
        requirements: ["moduleDependencies"],
        note: "Highlights dependency classification buckets emitted by the inventory to track external exposure.",
      },
    ],
  },
  {
    id: "event-dynamics",
    title: "Event Dynamics Pack",
    views: [
      {
        id: "callback_registration_map",
        label: "Callback Registration Map",
        filename: "callback_registration_map.mmd",
        description:
          "Diagram tracing detected callback registrations to their emitters for reviewing event-driven surfaces.",
        status: "prototype",
        builder: "callbackRegistrationMapView",
        requirements: ["callbackRegistrations"],
        note: "Highlights callback emitters and targets using normalized registration metadata.",
      },
      {
        id: "dynamic_code_watchlist",
        label: "Dynamic Code Watchlist",
        filename: "dynamic_code_watchlist.mmd",
        description:
          "Block diagram flagging modules where dynamic execution occurs so auditors can follow up quickly.",
        status: "prototype",
        builder: "dynamicCodeWatchlistView",
        requirements: ["dynamicCode"],
        note: "Highlights modules with exec/dynamic import/metaclass/globals mutation signals detected during inventory analysis.",
      },
    ],
  },
  {
    id: "code-flow",
    title: "Code Flow Pack",
    views: [
      {
        id: "function_call_graph",
        label: "Function Call Graph",
        filename: "function_call_graph.mmd",
        description:
          "Directed graph showing which functions call each other for runtime path exploration.",
        status: "prototype",
        note: "Leans on inter-function call graph edges from the inventory.",
        builder: "functionCallGraphView",
        requirements: ["callGraph"],
      },
      {
        id: "entrypoint_trace_diagram",
        label: "Entrypoint Trace Diagram",
        filename: "entrypoint_trace_diagram.mmd",
        description:
          "Flow diagram expanding from CLI entrypoints (e.g., run or main) to reachable functions.",
        status: "prototype",
        builder: "entrypointTraceDiagramView",
        requirements: ["callGraph", "entrypoints"],
        note: "Renders curated entrypoint candidates with call graph traversal and scope-aware fallbacks.",
      },
      {
        id: "class_inheritance_hierarchy",
        label: "Class Inheritance Hierarchy",
        filename: "class_inheritance_hierarchy.mmd",
        description:
          "Class diagram showing inheritance relationships to surface base/derived structures.",
        status: "prototype",
        builder: "classInheritanceHierarchyView",
        requirements: ["classInheritance"],
        note: "Builds on recorded base class metadata in the inventory.",
      },
      {
        id: "method_call_chain",
        label: "Method Call Chain",
        filename: "method_call_chain.mmd",
        description:
          "Sequence diagram highlighting chained object method calls for delegate tracing.",
        status: "prototype",
        builder: "methodCallChainView",
        requirements: ["callGraph"],
        note: "Renders chained class method calls using normalized call graph edges with scope-aware fallbacks.",
      },
    ],
  },
  {
    id: "state-effects",
    title: "State Effects Pack",
    views: [
      {
        id: "global_variable_usage_map",
        label: "Global Variable Usage Map",
        filename: "global_variable_usage_map.mmd",
        description:
          "Diagram linking functions to global variables they read or write to highlight shared state.",
        status: "prototype",
        builder: "globalVariableUsageMapView",
        requirements: ["inventoryBasics"],
        note: "Visualizes function-to-global relationships using normalized global declarations and usage metadata.",
      },
      {
        id: "io_effects_diagram",
        label: "IO Effects Diagram",
        filename: "io_effects_diagram.mmd",
        description:
          "Annotated graph mapping functions to file, network, or environment interactions.",
        status: "prototype",
        builder: "ioEffectsDiagramView",
        requirements: ["ioEffects"],
        note: "Highlights per-module functions with IO side effects across filesystem, environment, and network categories.",
      },
      {
        id: "exception_flow_map",
        label: "Exception Flow Map",
        filename: "exception_flow_map.mmd",
        description:
          "Visualization of which functions raise which exceptions to follow error propagation paths.",
        status: "prototype",
        builder: "exceptionFlowMapView",
        requirements: ["exceptionFlow"],
        note: "Highlights per-module exception raises so auditors can trace propagation paths across modules.",
      },
    ],
  },
  {
    id: "quality-metrics",
    title: "Quality Metrics Pack",
    views: [
      {
        id: "complexity_heatmap",
        label: "Complexity Heatmap",
        filename: "complexity_heatmap.mmd",
        description:
          "Heatmap coloring functions by derived complexity scores to spotlight hard-to-maintain code.",
        status: "prototype",
        builder: "complexityHeatmapView",
        requirements: ["complexityMetrics"],
      },
      {
        id: "logging_flow",
        label: "Logging Flow",
        filename: "logging_flow.mmd",
        description:
          "Diagram showing which functions emit logs at which levels to evaluate observability coverage.",
        status: "prototype",
        builder: "loggingFlowView",
        requirements: ["loggingCalls"],
      },
      {
        id: "decorator_usage_map",
        label: "Decorator Usage Map",
        filename: "decorator_usage_map.mmd",
        description:
          "Graph clustering functions by decorator usage for quick annotation audits.",
        status: "prototype",
        builder: "decoratorUsageMapView",
        requirements: ["decoratorMetadata"],
      },
      {
        id: "public_vs_private_api",
        label: "Public vs Private API Map",
        filename: "public_vs_private_api.mmd",
        description:
          "Graph contrasting declared exports with implicit public helpers and private internals to expose API drift.",
        status: "prototype",
        builder: "publicVsPrivateApiView",
        requirements: ["moduleExports"],
        note: "Summarizes normalized API surface metadata including __all__ declarations, implicit exports, and private helpers.",
      },
      {
        id: "cyclomatic_complexity_map",
        label: "Cyclomatic Complexity Map",
        filename: "cyclomatic_complexity_map.mmd",
        description:
          "Visualization using McCabe complexity scores attached to functions in the inventory.",
        status: "prototype",
        builder: "cyclomaticComplexityMapView",
        requirements: ["complexityMetrics"],
        note: "Highlights per-module complexity tiers and surfaces low-coverage hotspots for refactoring triage.",
      },
      {
        id: "type_coverage_map",
        label: "Type Coverage Map",
        filename: "type_coverage_map.mmd",
        description:
          "Chart highlighting which functions include type hints based on recorded annotation ratios.",
        status: "prototype",
        builder: "typeCoverageMapView",
        requirements: ["typeCoverage"],
      },
      {
        id: "documentation_coverage_map",
        label: "Documentation Coverage Map",
        filename: "documentation_coverage_map.mmd",
        description:
          "Diagram portraying docstring presence and quality scores for knowledge sharing readiness.",
        status: "prototype",
        builder: "documentationCoverageMapView",
        requirements: ["docstringQuality"],
      },
    ],
  },
  {
    id: "coupling-insight",
    title: "Coupling Insight Pack",
    views: [
      {
        id: "cross_module_function_references",
        label: "Cross-Module Function References",
        filename: "cross_module_function_references.mmd",
        description:
          "Edge map showing when functions in one file call functions in another to expose coupling.",
        status: "prototype",
        builder: "crossModuleFunctionReferencesView",
        requirements: ["inventoryBasics", "callGraph"],
        note: "Aggregates normalized call graph edges into module-level coupling stats with scope-aware fallbacks.",
      },
      {
        id: "import_chain_depth",
        label: "Import Chain Depth",
        filename: "import_chain_depth.mmd",
        description:
          "Layered view illustrating import hop counts from standard library to local modules.",
        status: "prototype",
        builder: "importChainDepthView",
        requirements: ["inventoryBasics"],
        note: "Derives minimal hop depths from normalized import edges and highlights modules lacking a path back to the standard library.",
      },
    ],
  },
  {
    id: "risk-assurance",
    title: "Risk & Assurance Pack",
    views: [
      {
        id: "test_coverage_mapping",
        label: "Test Coverage Mapping",
        filename: "test_coverage_mapping.mmd",
        description:
          "Graph connecting tests to exercised functions for coverage validation.",
        status: "prototype",
        builder: "testCoverageMappingView",
        requirements: ["inventoryBasics", "coverage"],
        note: "Requires coverage artifacts (e.g., coverage.json) mapped to inventory modules.",
      },
      {
        id: "git_churn_risk_map",
        label: "Git Churn Risk Map",
        filename: "git_churn_risk_map.mmd",
        description:
          "Risk heatmap combining git change frequency with complexity signals.",
        status: "prototype",
        builder: "gitChurnRiskMapView",
        requirements: ["gitChurn"],
        note: "Renders churn severity based on repository baselines when git churn metrics are available.",
      },
      {
        id: "dead_code_detection",
        label: "Dead Code Detection",
        filename: "dead_code_detection.mmd",
        description:
          "Diagram isolating functions never invoked alongside unused imports for remediation planning.",
        status: "prototype",
        builder: "deadCodeDetectionView",
        requirements: ["deadCodeSignals"],
        note: "Surfaces unreachable functions and unused imports captured by the CommandView inventory with scope-aware fallbacks.",
      },
    ],
  },
]);

const VIEW_BUILDERS = Object.freeze({
  callbackRegistrationMapView: buildCallbackRegistrationMapViewDefinition,
  dynamicCodeWatchlistView: buildDynamicCodeWatchlistViewDefinition,
  complexityHeatmapView: buildComplexityHeatmapViewDefinition,
  cyclomaticComplexityMapView: buildCyclomaticComplexityMapViewDefinition,
  decoratorUsageMapView: buildDecoratorUsageMapViewDefinition,
  publicVsPrivateApiView: buildPublicVsPrivateApiViewDefinition,
  documentationCoverageMapView: buildDocumentationCoverageMapViewDefinition,
  loggingFlowView: buildLoggingFlowViewDefinition,
  exportContractMatrixView: buildExportContractMatrixViewDefinition,
  externalVsInternalDependencyMapView: buildExternalVsInternalDependencyMapViewDefinition,
  moduleDependencyGraphView: buildModuleDependencyGraphViewDefinition,
  layerArchitectureValidationView: buildLayerArchitectureValidationViewDefinition,
  circularImportDetectionView: buildCircularImportDetectionViewDefinition,
  functionCallGraphView: buildFunctionCallGraphViewDefinition,
  crossModuleFunctionReferencesView: buildCrossModuleFunctionReferencesViewDefinition,
  importChainDepthView: buildImportChainDepthViewDefinition,
  entrypointTraceDiagramView: buildEntrypointTraceDiagramViewDefinition,
  classInheritanceHierarchyView: buildClassInheritanceHierarchyViewDefinition,
  methodCallChainView: buildMethodCallChainViewDefinition,
  globalVariableUsageMapView: buildGlobalVariableUsageViewDefinition,
  ioEffectsDiagramView: buildIoEffectsViewDefinition,
  exceptionFlowMapView: buildExceptionFlowViewDefinition,
  functionInventoryOverview: buildFunctionInventoryOverviewViewDefinition,
  typeCoverageMapView: buildTypeCoverageMapViewDefinition,
  screeningSignalTimelineView: buildScreeningSignalTimelineViewDefinition,
  testCoverageMappingView: buildTestCoverageMappingViewDefinition,
  gitChurnRiskMapView: buildGitChurnRiskMapViewDefinition,
  deadCodeDetectionView: buildDeadCodeDetectionViewDefinition,
});

function getViewPackById(packId) {
  if (!packId) {
    return null;
  }
  return VIEW_PACKS.find((pack) => pack.id === packId) ?? null;
}

function getViewMetadata(packId, viewId) {
  if (!packId || !viewId) {
    return null;
  }
  const pack = getViewPackById(packId);
  if (!pack) {
    return null;
  }
  const view = pack.views.find((candidate) => candidate.id === viewId) ?? null;
  if (!view) {
    return null;
  }
  return { pack, view };
}

function evaluateViewAvailability(view) {
  if (!view) {
    return { available: false, reason: "View definition not found." };
  }

  if (!state.activeOption || !state.normalizedData) {
    return {
      available: false,
      reason: "Load a CommandView artifact to enable view packs.",
    };
  }

  const builderKey = view.builder ?? view.id;
  const builder = typeof builderKey === "string" ? VIEW_BUILDERS[builderKey] : null;
  if (typeof builder !== "function") {
    return {
      available: false,
      reason: view.note ?? "View wiring pending implementation.",
    };
  }

  const requirementIssue = findViewRequirementIssue(view.requirements ?? []);
  if (requirementIssue) {
    return { available: false, reason: requirementIssue };
  }

  return { available: true, builder };
}

function findViewRequirementIssue(requirements) {
  if (!Array.isArray(requirements) || requirements.length === 0) {
    return null;
  }

  for (const requirement of requirements) {
    switch (requirement) {
      case "inventoryBasics": {
        const modules = state.normalizedData?.modules;
        const functions = state.normalizedData?.functions;
        if (!(modules instanceof Map) || modules.size === 0) {
          return "CommandView inventory has no modules to summarize.";
        }
        if (!(functions instanceof Map) || functions.size === 0) {
          return "CommandView inventory has no functions to summarize.";
        }
        break;
      }
      case "decoratorMetadata": {
        const functions = state.normalizedData?.functions;
        if (!(functions instanceof Map) || functions.size === 0) {
          return "Load a CommandView artifact with normalized functions to inspect decorator usage.";
        }

        let hasDecoratorField = false;
        for (const fn of functions.values()) {
          if (Array.isArray(fn?.decorators) || Array.isArray(fn?.decoratorsDetailed)) {
            hasDecoratorField = true;
            break;
          }
        }

        if (!hasDecoratorField) {
          return "Decorator metadata is unavailable in the loaded artifact.";
        }
        break;
      }
      case "docstringQuality": {
        const functions = state.normalizedData?.functions;
        if (!(functions instanceof Map) || functions.size === 0) {
          return "Docstring metrics are unavailable because no functions were normalized.";
        }
        const hasDocData = Array.from(functions.values()).some((fn) => fn && typeof fn.docstringQuality === "object");
        if (!hasDocData) {
          return "Docstring quality metrics are not available in this CommandView artifact.";
        }
        break;
      }
      case "typeCoverage": {
        const functions = state.normalizedData?.functions;
        if (!(functions instanceof Map) || functions.size === 0) {
          return "Type hint coverage data is unavailable because no functions were normalized.";
        }
        const hasTypeCoverage = Array.from(functions.values()).some((fn) => {
          const coverage = fn?.typeHintCoverage ?? fn?.annotationCoverage;
          const numeric = Number(coverage);
          return Number.isFinite(numeric);
        });
        if (!hasTypeCoverage) {
          return "Type hint coverage metrics are not available in this CommandView artifact.";
        }
        break;
      }
      case "complexityMetrics": {
        const functions = state.normalizedData?.functions;
        if (!(functions instanceof Map) || functions.size === 0) {
          return "Complexity metrics are unavailable because no functions were normalized.";
        }
        const hasComplexity = Array.from(functions.values()).some((fn) => {
          if (!fn || typeof fn !== "object") {
            return false;
          }
          const primary = fn.cyclomaticComplexity ?? fn.cyclomatic_complexity;
          const fallback = fn.metrics?.complexity ?? fn.metrics?.cyclomatic_complexity;
          return Number.isFinite(Number(primary)) || Number.isFinite(Number(fallback));
        });
        if (!hasComplexity) {
          return "Complexity metrics are not available in this CommandView artifact.";
        }
        break;
      }
      case "callGraph": {
        const callGraph = state.normalizedData?.callGraph?.functions;
        if (!(callGraph instanceof Map) || callGraph.size === 0) {
          return "Call graph data is not available in this CommandView artifact.";
        }
        break;
      }
      case "classInheritance": {
        const classes = state.normalizedData?.classes;
        const classMap = classes instanceof Map ? classes : classes ?? null;
        if (!(classMap instanceof Map) || classMap.size === 0) {
          return "Class inheritance metadata is not available in this CommandView artifact.";
        }
        break;
      }
      case "entrypoints": {
        const entrypoints = state.normalizedData?.entrypoints;
        const entrypointMap = entrypoints instanceof Map ? entrypoints : entrypoints ?? null;
        if (!(entrypointMap instanceof Map) || entrypointMap.size === 0) {
          return "Entrypoint candidates are not available in this CommandView artifact.";
        }
        break;
      }
      case "coverage": {
        const modulesWithCoverage = state.normalizedData?.metrics?.modules;
        if (!(modulesWithCoverage instanceof Map) || modulesWithCoverage.size === 0) {
          return "Coverage metrics are not available in this CommandView artifact.";
        }
        break;
      }
      case "gitChurn": {
        const modulesWithChurn = state.normalizedData?.metrics?.modules;
        if (!(modulesWithChurn instanceof Map) || modulesWithChurn.size === 0) {
          return "Git churn metrics are not available in this CommandView artifact.";
        }
        break;
      }
      case "screeningHistory": {
        const history = state.normalizedData?.screeningHistory ?? null;
        if (!history) {
          return "Screening history data is not available in this CommandView artifact.";
        }
        if (!Array.isArray(history.events)) {
          return "Screening history events are missing from this CommandView artifact.";
        }
        break;
      }
      case "moduleDependencies": {
        const modules = state.normalizedData?.modules;
        const moduleMap = modules instanceof Map ? modules : modules ?? null;
        if (!(moduleMap instanceof Map) || moduleMap.size === 0) {
          return "Module dependency data is not available in this CommandView artifact.";
        }
        const hasDependencies = Array.from(moduleMap.values()).some((moduleRecord) =>
          Array.isArray(moduleRecord?.importEdges) && moduleRecord.importEdges.length > 0
        );
        if (!hasDependencies) {
          return "Module dependency metadata is not present in this CommandView artifact.";
        }
        break;
      }
      case "moduleExports": {
        const modules = state.normalizedData?.modules;
        const moduleMap = modules instanceof Map ? modules : modules ?? null;
        if (!(moduleMap instanceof Map) || moduleMap.size === 0) {
          return "Module export data is not available in this CommandView artifact.";
        }
        const hasExportContracts = Array.from(moduleMap.values()).some((moduleRecord) => {
          const summary = moduleRecord?.exportSummary;
          if (!summary || typeof summary !== "object") {
            return false;
          }
          const declared = Array.isArray(summary.declared) ? summary.declared : [];
          const resolved = Array.isArray(summary.resolved) ? summary.resolved : [];
          const dynamic = summary.dynamic === true;
          return declared.length > 0 || resolved.length > 0 || dynamic;
        });
        if (!hasExportContracts) {
          return "Export contract metadata is not present in this CommandView artifact.";
        }
        break;
      }
      case "callbackRegistrations": {
        const modules = state.normalizedData?.modules;
        const moduleMap = modules instanceof Map ? modules : modules ?? null;
        if (!(moduleMap instanceof Map) || moduleMap.size === 0) {
          return "Callback registration metadata is not available in this CommandView artifact.";
        }
        const hasCallbacks = Array.from(moduleMap.values()).some((moduleRecord) =>
          Array.isArray(moduleRecord?.callbackRegistrations) && moduleRecord.callbackRegistrations.length > 0
        );
        if (!hasCallbacks) {
          return "Callback registration metadata is not available in this CommandView artifact.";
        }
        break;
      }
      case "ioEffects": {
        const modules = state.normalizedData?.modules;
        const moduleMap = modules instanceof Map ? modules : modules ?? null;
        if (!(moduleMap instanceof Map) || moduleMap.size === 0) {
          return "Module metadata has not been normalized for this CommandView artifact.";
        }
        const functions = state.normalizedData?.functions;
        const functionMap = functions instanceof Map ? functions : functions ?? null;
        if (!(functionMap instanceof Map) || functionMap.size === 0) {
          return "Function metadata has not been normalized for this CommandView artifact.";
        }
        const hasIoEffects = Array.from(functionMap.values()).some(
          (fn) => fn && typeof fn.ioEffects === "object"
        );
        if (!hasIoEffects) {
          return "IO effects metadata is not available in this CommandView artifact.";
        }
        break;
      }
      case "exceptionFlow": {
        const modules = state.normalizedData?.modules;
        const moduleMap = modules instanceof Map ? modules : modules ?? null;
        if (!(moduleMap instanceof Map) || moduleMap.size === 0) {
          return "Module metadata has not been normalized for this CommandView artifact.";
        }
        const functions = state.normalizedData?.functions;
        const functionMap = functions instanceof Map ? functions : functions ?? null;
        if (!(functionMap instanceof Map) || functionMap.size === 0) {
          return "Function metadata has not been normalized for this CommandView artifact.";
        }
        const hasExceptionData = Array.from(functionMap.values()).some((fn) => {
          if (!fn || typeof fn !== "object") {
            return false;
          }
          const raised = Array.isArray(fn.raisedExceptions) ? fn.raisedExceptions : [];
          return raised.length > 0;
        });
        if (!hasExceptionData) {
          return "Exception flow metadata is not available in this CommandView artifact.";
        }
        break;
      }
      default:
        return `Requirement ${requirement} is not satisfied yet.`;
    }
  }

  return null;
}

const LEVEL_NODE_THRESHOLD = 50;
const COMPLEXITY_THRESHOLDS = {
  caution: 10,
  alert: 15,
};
const COVERAGE_THRESHOLDS = {
  strong: 0.85,
  caution: 0.75,
  alert: 0.6,
};
const AGGREGATE_FUNCTION_THRESHOLDS = {
  caution: 50,
  alert: 100,
  critical: 200,
};

const NODE_STYLE_PALETTE = Object.freeze({
  aggregate: {
    baseFill: "#1f2933",
    baseStroke: "#94a3b8",
    cautionFill: "#78350f",
    cautionStroke: "#f59e0b",
    alertFill: "#7f1d1d",
    alertStroke: "#f97316",
    criticalFill: "#450a0a",
    criticalStroke: "#f87171",
  },
  function: {
    baseFill: "#0f172a",
    baseStroke: "#38bdf8",
    focusFill: "#1d4ed8",
    focusStroke: "#93c5fd",
    cautionFill: "#78350f",
    cautionStroke: "#f59e0b",
    alertFill: "#7f1d1d",
    alertStroke: "#f87171",
    strongStroke: "#22c55e",
    weakStroke: "#f97316",
    alertCoverageStroke: "#ef4444",
  },
});

const payloadCache = new Map();

const state = {
  entries: [],
  activeOption: null,
  inventoryPayload: null,
  screeningPayload: null,
  inventoryUrl: null,
  screeningUrl: null,
  normalizedData: null,
  levels: null,
  currentLevel: "level0",
  diagramDefinition: null,
  levelSelections: {
    rootId: null,
    domainId: null,
    moduleId: null,
    functionId: null,
  },
  renderInteractions: new Map(),
  activeViews: [],
  activeViewIndex: -1,
  zoom: {
    scale: 1,
    translateX: 0,
    translateY: 0,
    isPanning: false,
    startX: 0,
    startY: 0,
  },
  sidebar: {
    width: 300,
    isResizing: false,
    startX: 0,
    startWidth: 0,
  },
  statusPanel: {
    height: 200,
    isResizing: false,
    startY: 0,
    startHeight: 0,
  },
  update: {
    isRunning: false,
    abortController: null,
    cancelEndpoint: null,
    unloadHandler: null,
  },
  statusMessage: "",
  statusDetails: [],
};

const selectionMemory = new Map();

const headerUi = {
  refreshButton: null,
  exportButton: null,
  updateButton: null,
};

const levelUi = {
  buttons: new Map(),
  sidebar: null,
};

const breadcrumbUi = {
  container: null,
};

const packUi = {
  container: null,
};

const viewTabsUi = {
  container: null,
};

function resetRenderInteractions() {
  state.renderInteractions.clear();
}

function registerRenderInteraction(elementId, handler) {
  if (!elementId || typeof handler !== "function") {
    return;
  }
  state.renderInteractions.set(elementId, handler);
}

function updateExportButtonState() {
  if (!headerUi.exportButton) {
    headerUi.exportButton = document.getElementById("export-button");
  }
  const button = headerUi.exportButton;
  if (!button) {
    return;
  }
  const hasDefinition = typeof state.diagramDefinition === "string" && state.diagramDefinition.trim().length > 0;
  button.disabled = !hasDefinition;
}

function getUpdateButton() {
  if (!headerUi.updateButton) {
    headerUi.updateButton = document.getElementById("update-button");
  }
  return headerUi.updateButton;
}

function setUpdateButtonBusy(isBusy) {
  const button = getUpdateButton();
  if (!button) {
    return;
  }

  if (isBusy) {
    if (state.update.isRunning) {
      return;
    }
    state.update.isRunning = true;
    button.disabled = true;
    if (!button.dataset.originalLabel) {
      button.dataset.originalLabel = button.textContent ?? "Update";
    }
    button.textContent = "";
    const spinner = document.createElement("span");
    spinner.className = "viewer-header-spinner";
    spinner.setAttribute("aria-hidden", "true");
    button.appendChild(spinner);
    button.setAttribute("aria-label", "Update in progress");
  } else {
    state.update.isRunning = false;
    button.disabled = false;
    const label = button.dataset.originalLabel ?? "Update";
    button.textContent = label;
    button.removeAttribute("aria-label");
  }
}

async function handleUpdateButtonClick() {
  if (state.update.isRunning) {
    updateStatus("An update is already in progress.", { clearDetails: false });
    return;
  }

  const { start, cancel } = resolveUpdateEndpoints();
  if (!start) {
    updateStatus("Update endpoint is not configured for this viewer instance.");
    return;
  }

  if (!state.activeOption) {
    updateStatus("Select a CommandView artifact before triggering an update.");
    return;
  }

  const inventory = state.inventoryPayload;
  if (!inventory || typeof inventory !== "object") {
    updateStatus("Load the CommandView artifact before triggering an update.");
    return;
  }
  const metadata = inventory.metadata ?? {};
  const folderPath = metadata.folder_path ?? metadata.folderPath ?? null;
  if (!folderPath) {
    updateStatus("Active CommandView metadata does not expose folder_path; refresh the artifact and try again.");
    return;
  }
  const folderLabel = metadata.folder_name ?? metadata.folderName ?? state.activeOption.label ?? folderPath;

  const controller = new AbortController();
  state.update.abortController = controller;
  state.update.cancelEndpoint = cancel;

  setUpdateButtonBusy(true);
  attachUpdateUnloadHandler(controller);

  try {
    updateStatus(`Regenerating CommandView inventory for ${folderLabel}…`);

    const payload = {
      target: folderPath,
      slug: state.activeOption.slug ?? null,
      relative_path: state.activeOption.relative_path ?? null,
      timestamp_iso: state.activeOption.timestamp_iso ?? state.activeOption.timestamp ?? null,
    };

    const response = await fetch(start, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    const rawBody = await response.text();
    let resultPayload = null;
    if (rawBody) {
      try {
        resultPayload = JSON.parse(rawBody);
      } catch (parseError) {
        console.error("[handleUpdateButtonClick] Failed to parse update response", parseError, rawBody);
        throw new Error("Update endpoint returned malformed JSON");
      }
    }

    if (!response.ok) {
      const message = resultPayload?.message ?? `HTTP ${response.status} ${response.statusText}`;
      throw new Error(message);
    }

    const updateResult = resultPayload ?? {};
    if (updateResult.status !== "ok") {
      const message = updateResult.message ?? "Update endpoint returned an unexpected response.";
      throw new Error(message);
    }

    let refreshError = null;
    if (!updateResult.was_cancelled) {
      try {
        await refreshSelectorData({ allowFallback: false });
      } catch (error) {
        refreshError = error;
        console.warn("[handleUpdateButtonClick] Selector refresh failed", error);
      }
    }

    let message;
    const exitCode = typeof updateResult.exit_code === "number" ? updateResult.exit_code : null;
    const duration = typeof updateResult.duration_seconds === "number" ? updateResult.duration_seconds : null;
    const formattedDuration = duration !== null ? formatDuration(duration) : null;

    if (updateResult.was_cancelled) {
      message = formattedDuration
        ? `Update cancelled after ${formattedDuration}.`
        : "Update cancelled.";
    } else if (exitCode === 0) {
      message = formattedDuration
        ? `CommandView inventory regenerated for ${folderLabel} in ${formattedDuration}.`
        : `CommandView inventory regenerated for ${folderLabel}.`;
    } else {
      message = exitCode !== null
        ? `Update completed with errors (exit code ${exitCode}).`
        : "Update completed with errors.";
    }

    if (refreshError) {
      const detail = refreshError instanceof Error ? refreshError.message : String(refreshError);
      message = `${message} Refresh failed: ${detail}`;
    }

    setStatusDetails(buildUpdateStatusDetails(updateResult));
    updateStatus(message, { clearDetails: false });
  } catch (error) {
    if (error && error.name === "AbortError") {
      sendUpdateCancellation("client-abort");
      updateStatus("Update cancelled.");
    } else {
      console.error("Update button handler failed", error);
      updateStatus(`Update failed: ${error?.message ?? error}`);
    }
    setStatusDetails([]);
  } finally {
    detachUpdateUnloadHandler();
    state.update.abortController = null;
    state.update.cancelEndpoint = null;
    setUpdateButtonBusy(false);
  }
}

function buildMemoryKeys(option) {
  if (!option) {
    return [];
  }
  const keys = [];
  const relativePath = option.relative_path ?? option.path ?? null;
  if (relativePath) {
    keys.push(`path:${relativePath}`);
  }
  const slug = option.slug ?? null;
  if (slug) {
    keys.push(`slug:${slug}`);
  }
  return keys;
}

function persistActiveSelectionMemory() {
  if (!state.activeOption || !state.levels) {
    return;
  }

  const keys = buildMemoryKeys(state.activeOption);
  if (keys.length === 0) {
    return;
  }

  const memory = {
    currentLevel: state.currentLevel,
    selections: {
      rootId: state.levelSelections.rootId,
      domainId: state.levelSelections.domainId,
      moduleId: state.levelSelections.moduleId,
      functionId: state.levelSelections.functionId,
    },
    activeViews: state.activeViews.length > 0 ? [...state.activeViews] : null,
    activeViewIndex: state.activeViewIndex >= 0 ? state.activeViewIndex : null,
  };

  keys.forEach((key) => {
    selectionMemory.set(key, memory);
  });
}

function restoreSelectionMemory(option) {
  if (!option) {
    return;
  }
  const keys = buildMemoryKeys(option);
  let memory = null;
  for (const key of keys) {
    const stored = selectionMemory.get(key);
    if (stored) {
      memory = stored;
      break;
    }
  }
  if (!memory) {
    return;
  }

  if (memory.selections) {
    if (memory.selections.rootId) {
      state.levelSelections.rootId = memory.selections.rootId;
    }
    if (memory.selections.domainId) {
      state.levelSelections.domainId = memory.selections.domainId;
    }
    if (memory.selections.moduleId) {
      state.levelSelections.moduleId = memory.selections.moduleId;
    }
    if (memory.selections.functionId) {
      state.levelSelections.functionId = memory.selections.functionId;
    }
  }

  if (memory.currentLevel) {
    state.currentLevel = memory.currentLevel;
  }

  // Restore active view pack selection
  if (memory.activeViews && Array.isArray(memory.activeViews) && memory.activeViews.length > 0) {
    state.activeViews = [...memory.activeViews];
    state.activeViewIndex = memory.activeViewIndex ?? 0;
    console.log("[restoreSelectionMemory] Restored active views:", state.activeViews, "index:", state.activeViewIndex);
  }
}

function getViewerConfig() {
  return window.viewerConfig ?? {};
}

function ensureTrailingSlash(value) {
  return value.endsWith("/") ? value : `${value}/`;
}

function resolveReportsBaseUrl() {
  const { reportsBaseUrl } = getViewerConfig();
  const base = reportsBaseUrl && typeof reportsBaseUrl === "string" && reportsBaseUrl.trim().length > 0
    ? reportsBaseUrl.trim()
    : DEFAULT_REPORTS_BASE_URL;

  if (/\.json$/i.test(base)) {
    const lastSlash = base.lastIndexOf("/");
    return lastSlash >= 0 ? ensureTrailingSlash(base.slice(0, lastSlash)) : "";
  }

  return ensureTrailingSlash(base);
}

function resolveUpdateEndpoints() {
  const config = getViewerConfig() ?? {};
  const start = typeof config.updateApiEndpoint === "string" && config.updateApiEndpoint.trim().length > 0
    ? config.updateApiEndpoint.trim()
    : null;
  const cancel = typeof config.updateCancelEndpoint === "string" && config.updateCancelEndpoint.trim().length > 0
    ? config.updateCancelEndpoint.trim()
    : start
      ? `${start.replace(/\/+$/, "")}/cancel`
      : null;
  return { start, cancel };
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return "unknown duration";
  }
  if (seconds < 1) {
    const millis = Math.round(seconds * 1000);
    return `${millis} ms`;
  }
  if (seconds < 10) {
    return `${seconds.toFixed(2)} s`;
  }
  return `${seconds.toFixed(1)} s`;
}

function attachUpdateUnloadHandler(controller) {
  detachUpdateUnloadHandler();
  if (!controller) {
    return;
  }
  const handler = () => {
    if (!state.update.isRunning) {
      return;
    }
    sendUpdateCancellation("page-unload");
    if (!controller.signal.aborted) {
      controller.abort();
    }
  };
  state.update.unloadHandler = handler;
  window.addEventListener("beforeunload", handler);
}

function detachUpdateUnloadHandler() {
  if (!state.update.unloadHandler) {
    return;
  }
  window.removeEventListener("beforeunload", state.update.unloadHandler);
  state.update.unloadHandler = null;
}

function sendUpdateCancellation(reason = "client-abort") {
  const stored = typeof state.update.cancelEndpoint === "string" && state.update.cancelEndpoint.trim().length > 0
    ? state.update.cancelEndpoint.trim()
    : null;
  const { cancel } = resolveUpdateEndpoints();
  const endpoint = stored ?? cancel;
  if (!endpoint) {
    return;
  }
  const payload = JSON.stringify({ reason });
  try {
    if (navigator.sendBeacon) {
      const blob = new Blob([payload], { type: "application/json" });
      navigator.sendBeacon(endpoint, blob);
    } else {
      void fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true,
      }).catch((error) => {
        console.warn("Update cancellation request failed", error);
      });
    }
  } catch (error) {
    console.warn("Unable to send update cancellation", error);
  }
}

function buildUpdateStatusDetails(result) {
  const descriptors = [];
  const targetRelative = result?.target_relative ?? null;
  if (targetRelative) {
    descriptors.push({
      type: "note",
      title: "Target directory",
      message: targetRelative,
    });
  }

  const selectorError = typeof result?.selector_error === "string" && result.selector_error.trim().length > 0
    ? result.selector_error.trim()
    : null;
  if (selectorError) {
    descriptors.push({
      type: "note",
      title: "Selector refresh",
      message: selectorError,
    });
  } else if (result?.selector_refreshed) {
    descriptors.push({
      type: "note",
      title: "Selector refresh",
      message: "selector.json regenerated.",
    });
  }

  const logs = result?.logs ?? {};
  if (Array.isArray(logs.stdout) && logs.stdout.length > 0) {
    descriptors.push({
      type: "list",
      title: logs.stdout_truncated ? "stdout (tail)" : "stdout",
      description: logs.stdout_truncated ? "Output truncated to the most recent lines." : undefined,
      items: logs.stdout,
    });
  }
  if (Array.isArray(logs.stderr) && logs.stderr.length > 0) {
    descriptors.push({
      type: "list",
      title: logs.stderr_truncated ? "stderr (tail)" : "stderr",
      description: logs.stderr_truncated ? "Errors truncated to the most recent lines." : undefined,
      items: logs.stderr,
    });
  }
  return descriptors;
}

function buildArtifactUrl(relativePath) {
  if (!relativePath) {
    throw new Error("Relative path is required to load artifacts");
  }
  if (ABSOLUTE_URL_PATTERN.test(relativePath) || relativePath.startsWith("/")) {
    return relativePath;
  }
  const base = resolveReportsBaseUrl();
  return `${base}${relativePath}`;
}

function sanitizeFilenameSegment(value, fallback) {
  const base = typeof value === "string" && value.trim().length > 0 ? value.trim().toLowerCase() : fallback;
  const sanitized = base.replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "");
  return sanitized || fallback;
}

function buildDiagramExportFilename() {
  const slug = sanitizeFilenameSegment(state.activeOption?.slug ?? state.activeOption?.label ?? "commandview", "commandview");
  const activeViewDescriptor = Array.isArray(state.activeViews) && state.activeViewIndex >= 0
    ? state.activeViews[state.activeViewIndex]
    : null;
  const mode = activeViewDescriptor?.viewId ?? state.currentLevel ?? "level";
  const level = sanitizeFilenameSegment(mode, "level");
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  return `${slug}-${level}-${timestamp}.mmd`;
}

function deriveScreeningRelativePath(relativePath) {
  const screeningPath = relativePath.replace(
    /_commandview_(\d{8}-\d{4})\.json$/,
    "_commandview_screening_$1.json"
  );
  if (screeningPath === relativePath) {
    throw new Error(`Unable to derive screening payload path for ${relativePath}`);
  }
  return screeningPath;
}

function clearDiagram() {
  const container = document.getElementById("diagram");
  if (container) {
    container.innerHTML = "";
  }
  state.diagramDefinition = null;
  updateExportButtonState();
}

function initializeMermaid() {
  if (!window.mermaid) {
    throw new Error("Mermaid library failed to load");
  }
  window.mermaid.initialize({ startOnLoad: false, theme: "dark" });
}

function updateStatus(message, options = {}) {
  const shouldClearDetails = options.clearDetails !== false;
  state.statusMessage = typeof message === "string" ? message : "";
  if (shouldClearDetails) {
    state.statusDetails = [];
  }
  renderStatusPanel();
}

function setStatusDetails(descriptors) {
  if (Array.isArray(descriptors) && descriptors.length > 0) {
    state.statusDetails = descriptors;
  } else {
    state.statusDetails = [];
  }
  renderStatusPanel();
}

const STATUS_DESCRIPTOR_RENDERERS = Object.freeze({
  note: renderStatusNoteDescriptor,
  list: renderStatusListDescriptor,
  "alert-list": renderStatusListDescriptor,
  "stat-summary": renderStatusMetricDescriptor,
  "metric-list": renderStatusMetricDescriptor,
  "pill-list": renderStatusPillDescriptor,
  "missing-decorator-policy": renderMissingDecoratorPolicyDescriptor,
});

function renderStatusPanel() {
  const panel = document.getElementById("status-panel");
  if (!panel) {
    return;
  }
  panel.innerHTML = "";
  const messageElement = document.createElement("div");
  messageElement.className = "viewer-status-message";
  messageElement.textContent = state.statusMessage || "";
  panel.appendChild(messageElement);

  const descriptors = Array.isArray(state.statusDetails) ? state.statusDetails : [];
  descriptors.forEach((descriptor) => {
    const descriptorElement = renderStatusDescriptor(descriptor);
    if (descriptorElement) {
      panel.appendChild(descriptorElement);
    }
  });
}

function renderStatusDescriptor(descriptor) {
  if (!descriptor || typeof descriptor !== "object") {
    return null;
  }
  const type = typeof descriptor.type === "string" ? descriptor.type : "note";
  const renderer = STATUS_DESCRIPTOR_RENDERERS[type] ?? renderStatusNoteDescriptor;
  try {
    return renderer(descriptor);
  } catch (error) {
    console.warn("Failed to render status descriptor", descriptor, error);
    return null;
  }
}

function renderStatusNoteDescriptor(descriptor) {
  const message = typeof descriptor.message === "string" ? descriptor.message.trim() : "";
  const title = typeof descriptor.title === "string" ? descriptor.title.trim() : "";
  if (!message && !title) {
    return null;
  }
  const container = document.createElement("div");
  container.className = buildStatusSectionClass(descriptor, "status-section-note");
  if (title) {
    appendStatusSectionTitle(container, title);
  }
  if (message) {
    const body = document.createElement("div");
    body.className = "status-note-message";
    body.textContent = message;
    container.appendChild(body);
  }
  return container;
}

function renderStatusListDescriptor(descriptor) {
  const items = normalizeListDescriptorItems(descriptor.items);
  if (items.length === 0) {
    return null;
  }
  const container = document.createElement("div");
  container.className = buildStatusSectionClass(descriptor, "status-section-listing");
  const title = typeof descriptor.title === "string" && descriptor.title.trim().length > 0
    ? descriptor.title.trim()
    : null;
  if (title) {
    appendStatusSectionTitle(container, title);
  }
  appendStatusSectionDescription(container, descriptor);

  const list = document.createElement("ul");
  list.className = "status-section-list";

  items.forEach((item) => {
    const listItem = document.createElement("li");
    listItem.className = "status-section-item";
    if (item.header) {
      const header = document.createElement("div");
      header.className = "status-section-item-header";
      header.textContent = item.header;
      listItem.appendChild(header);
    }
    if (item.body) {
      const subtitle = document.createElement("div");
      subtitle.className = "status-section-item-subtitle";
      subtitle.textContent = item.body;
      listItem.appendChild(subtitle);
    }
    if (item.badges.length > 0) {
      const pillList = document.createElement("div");
      pillList.className = "status-pill-row";
      item.badges.forEach((badgeLabel) => {
        const pill = document.createElement("span");
        pill.className = "status-pill";
        pill.textContent = badgeLabel;
        pillList.appendChild(pill);
      });
      listItem.appendChild(pillList);
    }
    if (item.subitems.length > 0) {
      const sublist = document.createElement("ul");
      sublist.className = "status-section-sublist";
      item.subitems.forEach((entry) => {
        const subItem = document.createElement("li");
        subItem.className = "status-section-subitem";
        subItem.textContent = entry;
        sublist.appendChild(subItem);
      });
      listItem.appendChild(sublist);
    }
    list.appendChild(listItem);
  });

  container.appendChild(list);
  return container;
}

function renderStatusMetricDescriptor(descriptor) {
  const entries = normalizeMetricDescriptorItems(descriptor.items ?? descriptor.entries);
  if (entries.length === 0) {
    return null;
  }
  const container = document.createElement("div");
  container.className = buildStatusSectionClass(descriptor, "status-section-metrics");

  const title = typeof descriptor.title === "string" && descriptor.title.trim().length > 0
    ? descriptor.title.trim()
    : null;
  if (title) {
    appendStatusSectionTitle(container, title);
  }
  appendStatusSectionDescription(container, descriptor);

  const metricContainer = document.createElement("div");
  metricContainer.className = "status-metrics";
  entries.forEach((entry) => {
    const metric = document.createElement("div");
    metric.className = "status-metric";

    const label = document.createElement("div");
    label.className = "status-metric-label";
    label.textContent = entry.label;
    metric.appendChild(label);

    const value = document.createElement("div");
    value.className = "status-metric-value";
    value.textContent = entry.value;
    metric.appendChild(value);

    if (entry.hint) {
      const hint = document.createElement("div");
      hint.className = "status-metric-hint";
      hint.textContent = entry.hint;
      metric.appendChild(hint);
    }

    metricContainer.appendChild(metric);
  });

  container.appendChild(metricContainer);
  return container;
}

function renderStatusPillDescriptor(descriptor) {
  const items = normalizePillDescriptorItems(descriptor.items);
  if (items.length === 0) {
    return null;
  }
  const container = document.createElement("div");
  container.className = buildStatusSectionClass(descriptor, "status-section-pills");

  const title = typeof descriptor.title === "string" && descriptor.title.trim().length > 0
    ? descriptor.title.trim()
    : null;
  if (title) {
    appendStatusSectionTitle(container, title);
  }
  appendStatusSectionDescription(container, descriptor);

  const pills = document.createElement("div");
  pills.className = "status-pill-row";
  items.forEach((item) => {
    const pill = document.createElement("span");
    pill.className = "status-pill";
    pill.textContent = item;
    pills.appendChild(pill);
  });
  container.appendChild(pills);
  return container;
}

function renderMissingDecoratorPolicyDescriptor(descriptor) {
  const items = Array.isArray(descriptor.items) ? descriptor.items : [];
  if (items.length === 0) {
    return null;
  }

  const container = document.createElement("div");
  container.className = buildStatusSectionClass(descriptor, "status-section-policy");
  appendStatusSectionTitle(container, descriptor.title ?? "Missing Decorator Policies");
  appendStatusSectionDescription(container, descriptor);

  const list = document.createElement("ul");
  list.className = "status-section-list";

  items.forEach((item) => {
    if (!item || typeof item !== "object") {
      return;
    }
    const listItem = document.createElement("li");
    listItem.className = "status-section-item";

    const header = document.createElement("div");
    header.className = "status-section-item-header";
    header.textContent = formatDecoratorPolicyDetailHeader(item);
    listItem.appendChild(header);

    const samples = Array.isArray(item.samples)
      ? item.samples.filter((sample) => sample && typeof sample === "object")
      : [];
    if (samples.length > 0) {
      const subtitle = document.createElement("div");
      subtitle.className = "status-section-item-subtitle";
      subtitle.textContent = samples.length === 1 ? "Sample function:" : "Sample functions:";
      listItem.appendChild(subtitle);

      const sublist = document.createElement("ul");
      sublist.className = "status-section-sublist";
      samples.forEach((sample) => {
        const sampleItem = document.createElement("li");
        sampleItem.className = "status-section-subitem";
        sampleItem.textContent = formatDecoratorPolicySample(sample);
        sublist.appendChild(sampleItem);
      });
      listItem.appendChild(sublist);
    } else {
      const subtitle = document.createElement("div");
      subtitle.className = "status-section-item-subtitle";
      subtitle.textContent = "No candidate functions recorded.";
      listItem.appendChild(subtitle);
    }

    list.appendChild(listItem);
  });

  container.appendChild(list);
  return container;
}

function buildStatusSectionClass(descriptor, extraClass) {
  const classes = ["status-section"];
  if (extraClass) {
    classes.push(extraClass);
  }
  const severityClass = resolveStatusSeverityClass(descriptor.severity);
  if (severityClass) {
    classes.push(severityClass);
  }
  return classes.join(" ");
}

function resolveStatusSeverityClass(severity) {
  if (typeof severity !== "string") {
    return "";
  }
  const normalized = severity.trim().toLowerCase();
  switch (normalized) {
    case "info":
      return "status-severity-info";
    case "success":
      return "status-severity-success";
    case "warning":
    case "warn":
      return "status-severity-warning";
    case "error":
    case "alert":
    case "critical":
      return "status-severity-error";
    default:
      return "";
  }
}

function appendStatusSectionTitle(container, title) {
  if (!title) {
    return;
  }
  const heading = document.createElement("div");
  heading.className = "status-section-title";
  heading.textContent = title;
  container.appendChild(heading);
}

function appendStatusSectionDescription(container, descriptor) {
  const description = typeof descriptor.description === "string" ? descriptor.description.trim() : "";
  if (!description) {
    return;
  }
  const paragraph = document.createElement("div");
  paragraph.className = "status-section-description";
  paragraph.textContent = description;
  container.appendChild(paragraph);
}

function normalizeListDescriptorItems(items) {
  if (!Array.isArray(items)) {
    return [];
  }
  return items
    .map((item) => {
      if (typeof item === "string") {
        const value = item.trim();
        return value.length > 0
          ? { header: value, body: null, subitems: [], badges: [] }
          : null;
      }
      if (!item || typeof item !== "object") {
        return null;
      }
      const header =
        typeof item.header === "string" && item.header.trim().length > 0
          ? item.header.trim()
          : typeof item.title === "string" && item.title.trim().length > 0
            ? item.title.trim()
            : typeof item.label === "string" && item.label.trim().length > 0
              ? item.label.trim()
              : null;
      const body =
        typeof item.body === "string" && item.body.trim().length > 0
          ? item.body.trim()
          : typeof item.description === "string" && item.description.trim().length > 0
            ? item.description.trim()
            : null;
      const badges = Array.isArray(item.badges)
        ? item.badges
            .map((badge) => (typeof badge === "string" ? badge.trim() : ""))
            .filter((badge) => badge.length > 0)
        : [];
      const subitems = Array.isArray(item.subitems)
        ? item.subitems
            .map((entry) => (typeof entry === "string" ? entry.trim() : ""))
            .filter((entry) => entry.length > 0)
        : [];
      if (!header && !body && badges.length === 0 && subitems.length === 0) {
        return null;
      }
      return { header, body, badges, subitems };
    })
    .filter(Boolean);
}

function normalizeMetricDescriptorItems(items) {
  if (!Array.isArray(items)) {
    return [];
  }
  return items
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const label = typeof entry.label === "string" && entry.label.trim().length > 0
        ? entry.label.trim()
        : null;
      const value = typeof entry.value === "string" && entry.value.trim().length > 0
        ? entry.value.trim()
        : Number.isFinite(entry.value)
          ? String(entry.value)
          : null;
      const hint = typeof entry.hint === "string" && entry.hint.trim().length > 0 ? entry.hint.trim() : null;
      if (!label || value === null) {
        return null;
      }
      return { label, value, hint };
    })
    .filter(Boolean);
}

function normalizePillDescriptorItems(items) {
  if (!Array.isArray(items)) {
    return [];
  }
  return items
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter((item) => item.length > 0);
}

function formatDecoratorPolicyDetailHeader(detail) {
  const decoratorName = typeof detail?.decorator === "string" && detail.decorator.trim().length > 0
    ? detail.decorator.trim()
    : "Unnamed decorator";
  const scope = typeof detail?.scope === "string" ? detail.scope.trim() : "global";
  const scopeLabel = formatDecoratorPolicyScopeLabel(scope, detail?.target ?? null);
  return `${decoratorName} missing (${scopeLabel})`;
}

function formatDecoratorPolicyScopeLabel(scope, target) {
  const normalizedScope = scope && scope.length > 0 ? scope : "global";
  const normalizedTarget = typeof target === "string" && target.trim().length > 0 ? target.trim() : null;
  if (normalizedScope === "global" || !normalizedTarget) {
    return normalizedScope;
  }
  return `${normalizedScope} ${normalizedTarget}`;
}

function formatDecoratorPolicySample(sample) {
  const name = typeof sample?.name === "string" && sample.name.trim().length > 0
    ? sample.name.trim()
    : typeof sample?.id === "string"
      ? sample.id
      : "function";
  const moduleId = typeof sample?.moduleId === "string" && sample.moduleId.trim().length > 0
    ? sample.moduleId.trim()
    : null;
  return moduleId ? `${name} · ${moduleId}` : name;
}

function normalizeDecoratorPolicyDetails(details) {
  if (!Array.isArray(details)) {
    return [];
  }
  return details
    .map((detail) => {
      if (!detail || typeof detail !== "object") {
        return null;
      }
      const decorator = typeof detail.decorator === "string" && detail.decorator.trim().length > 0
        ? detail.decorator.trim()
        : null;
      if (!decorator) {
        return null;
      }
      const scope = typeof detail.scope === "string" && detail.scope.trim().length > 0 ? detail.scope.trim() : "global";
      const target = typeof detail.target === "string" && detail.target.trim().length > 0 ? detail.target.trim() : null;
      const samples = Array.isArray(detail.samples)
        ? detail.samples
            .map((sample) => {
              if (!sample || typeof sample !== "object") {
                return null;
              }
              const name = typeof sample.name === "string" && sample.name.trim().length > 0 ? sample.name.trim() : null;
              const id = typeof sample.id === "string" && sample.id.trim().length > 0 ? sample.id.trim() : null;
              const fallback = name ?? id ?? "function";
              const moduleId = typeof sample.moduleId === "string" && sample.moduleId.trim().length > 0
                ? sample.moduleId.trim()
                : null;
              return { id: id ?? fallback, name: fallback, moduleId };
            })
            .filter(Boolean)
        : [];

      return {
        decorator,
        scope,
        target,
        samples,
      };
    })
    .filter(Boolean);
}

function deriveBuilderStatusDetails(builderResult) {
  if (!builderResult || typeof builderResult !== "object") {
    return [];
  }
  if (Array.isArray(builderResult.statusDetails) && builderResult.statusDetails.length > 0) {
    return builderResult.statusDetails;
  }

  const rawPolicyDetails = Array.isArray(builderResult.policyDetails)
    ? builderResult.policyDetails
    : Array.isArray(builderResult.stats?.missingRequiredDetails)
      ? builderResult.stats.missingRequiredDetails
      : [];
  const normalized = normalizeDecoratorPolicyDetails(rawPolicyDetails);
  if (normalized.length === 0) {
    return [];
  }
  return [
    {
      type: "missing-decorator-policy",
      title: "Missing Decorator Policies",
      items: normalized,
    },
  ];
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-cache" });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

async function loadCommandViewPayloads(option) {
  console.log("[loadCommandViewPayloads] Loading option:", option);
  const cacheKey = buildCacheKey(option);
  const cached = payloadCache.get(cacheKey);
  if (cached) {
    console.log("[loadCommandViewPayloads] Using cached data");
    state.inventoryPayload = cached.inventory;
    state.screeningPayload = cached.screening;
    state.inventoryUrl = cached.inventoryUrl;
    state.screeningUrl = cached.screeningUrl;
    state.normalizedData = cached.normalized;
    state.levels = cached.levels ?? cached.normalized?.levels ?? null;
    return cached;
  }

  state.inventoryPayload = null;
  state.screeningPayload = null;
  state.inventoryUrl = null;
  state.screeningUrl = null;
  state.normalizedData = null;

  const inventoryUrl = buildArtifactUrl(option.relative_path);
  const screeningRelativePath = deriveScreeningRelativePath(option.relative_path);
  const screeningUrl = buildArtifactUrl(screeningRelativePath);

  console.log("[loadCommandViewPayloads] Inventory URL:", inventoryUrl);
  console.log("[loadCommandViewPayloads] Screening URL:", screeningUrl);

  const [inventory, screening] = await Promise.all([
    fetchJson(inventoryUrl),
    fetchJson(screeningUrl).catch((error) => {
      console.warn("[loadCommandViewPayloads] Screening payload load failed", error);
      return null;
    }),
  ]);

  console.log("[loadCommandViewPayloads] Inventory loaded, files:", inventory?.files?.length);

  validateInventorySchema(inventory);

  state.inventoryPayload = inventory;
  state.inventoryUrl = inventoryUrl;
  state.screeningPayload = screening;
  state.screeningUrl = screening ? screeningUrl : null;
  state.normalizedData = normalizeCommandViewData(inventory, screening);
  state.levels = state.normalizedData.levels ?? null;

  const record = {
    inventory,
    screening,
    inventoryUrl,
    screeningUrl: screening ? screeningUrl : null,
    normalized: state.normalizedData,
    hierarchy: state.normalizedData.hierarchy,
    levels: state.levels,
  };

  payloadCache.set(cacheKey, record);

  return record;
}

function buildCacheKey(option) {
  const slug = option?.slug ?? "unknown";
  const path = option?.relative_path ?? "";
  const timestamp = option?.timestamp ?? option?.label ?? "";
  return `${slug}|${path}|${timestamp}`;
}

function normalizeCommandViewData(inventory, screening) {
  if (!inventory || typeof inventory !== "object") {
    throw new Error("Inventory payload is missing or invalid");
  }

  const files = Array.isArray(inventory.files) ? inventory.files : [];
  const modules = new Map();
  const classes = new Map();
  const functions = new Map();
  const functionCallGraph = new Map();
  const screeningHistory = buildScreeningHistory(screening);

  files.forEach((file) => {
    const moduleRecord = createModuleRecord(file);
    if (!moduleRecord) {
      return;
    }
    modules.set(moduleRecord.id, moduleRecord);

    const classIds = [];
    const classEntries = Array.isArray(file.classes) ? file.classes : [];
    classEntries.forEach((classEntry) => {
      const classRecord = createClassRecord(classEntry, moduleRecord.id);
      if (!classRecord) {
        return;
      }
      classIds.push(classRecord.id);
      classes.set(classRecord.id, classRecord);
    });

    const functionIds = [];
    const functionEntries = Array.isArray(file.functions) ? file.functions : [];
    functionEntries.forEach((fn) => {
      const functionRecord = createFunctionRecord(fn, moduleRecord.id);
      if (!functionRecord) {
        return;
      }
      functionIds.push(functionRecord.id);
      functions.set(functionRecord.id, functionRecord);
      functionCallGraph.set(functionRecord.id, functionRecord.calls);
    });
    moduleRecord.functions = functionIds;
    moduleRecord.classes = classIds;
    moduleRecord.functionCount = functionIds.length;
    moduleRecord.classCount = classIds.length;
    moduleRecord.apiSurface = buildModuleApiSurface(moduleRecord, functions, classes);
  });

  const callGraph = {
    functions: functionCallGraph,
    screening: buildScreeningCallIndex(screening),
  };

  const entrypoints = populateEntrypointCandidates(modules, functions, callGraph);
  resolveClassInheritanceRelationships(classes);
  const classInheritance = buildClassInheritanceIndex(classes);

  const metrics = buildMetricsCache(inventory, modules, functions, screening);
  const hierarchy = buildHierarchyMetadata(modules, functions, callGraph);
  const levels = buildViewLevels(modules, functions, hierarchy, callGraph);

  return {
    modules,
    classes,
    functions,
    callGraph,
    entrypoints,
    classInheritance,
    metrics,
    hierarchy,
    levels,
    screeningHistory,
  };
}

function resolveScriptLayer(moduleId, relativePath, absolutePath) {
  const normalizedModule = typeof moduleId === "string" ? moduleId.toLowerCase() : "";
  const normalizedPaths = [relativePath, absolutePath]
    .map((value) => (typeof value === "string" ? value.replace(/\\/g, "/").toLowerCase() : ""))
    .filter((value) => value.length > 0);

  for (const tier of SCRIPT_LAYER_TIERS) {
    if (tier.modulePrefixes.some((prefix) => normalizedModule.startsWith(prefix))) {
      return { id: tier.id, label: tier.label, index: tier.index };
    }
    if (normalizedPaths.some((path) => tier.pathFragments.some((fragment) => path.includes(fragment)))) {
      return { id: tier.id, label: tier.label, index: tier.index };
    }
  }

  return { id: SCRIPT_LAYER_UNKNOWN.id, label: SCRIPT_LAYER_UNKNOWN.label, index: SCRIPT_LAYER_UNKNOWN.index };
}

function evaluateLayerTransition(sourceLayerId, targetLayerId) {
  const normalizedSource = typeof sourceLayerId === "string" ? sourceLayerId : SCRIPT_LAYER_UNKNOWN.id;
  const normalizedTarget = typeof targetLayerId === "string" ? targetLayerId : SCRIPT_LAYER_UNKNOWN.id;

  if (normalizedSource === SCRIPT_LAYER_UNKNOWN.id || normalizedTarget === SCRIPT_LAYER_UNKNOWN.id) {
    return {
      allowed: true,
      classification: "unclassified",
      reason: "One or both modules are unclassified; defer manual review but do not hard-fail the transition.",
    };
  }

  const sourceIndex = SCRIPT_LAYER_INDEX_BY_ID[normalizedSource] ?? SCRIPT_LAYER_UNKNOWN.index;
  const targetIndex = SCRIPT_LAYER_INDEX_BY_ID[normalizedTarget] ?? SCRIPT_LAYER_UNKNOWN.index;
  const delta = targetIndex - sourceIndex;

  let classification;
  if (delta === 0) {
    classification = "peer";
  } else if (delta === 1) {
    classification = "forward";
  } else if (delta > 1) {
    classification = "skip";
  } else {
    classification = "backward";
  }

  const adjacency = SCRIPT_LAYER_ADJACENCY_DEFAULTS[normalizedSource] ?? null;
  const allowedTargets = Array.isArray(adjacency?.allowed) ? adjacency.allowed : [];
  const allowed = allowedTargets.includes(normalizedTarget);

  let reason;
  if (allowed) {
    if (classification === "peer" && adjacency?.peer) {
      reason = adjacency.peer;
    } else if (classification === "forward" && adjacency?.forward) {
      reason = adjacency.forward;
    } else if (adjacency?.rationale) {
      reason = adjacency.rationale;
    } else {
      reason = "Transition allowed by default layer adjacency rules.";
    }
  } else {
    const violationReasons = adjacency?.violations ?? null;
    if (violationReasons && typeof violationReasons[classification] === "string") {
      reason = violationReasons[classification];
    } else {
      reason = `Transition from ${normalizedSource} to ${normalizedTarget} violates default layer adjacency rules.`;
    }
  }

  return { allowed, classification, reason };
}

function createModuleRecord(file) {
  if (!file || typeof file !== "object") {
    return null;
  }

  const moduleId = file.module_id || file.relative_path || file.path;
  if (!moduleId) {
    return null;
  }

  const layer = resolveScriptLayer(moduleId, file.relative_path ?? null, file.path ?? null);

  return {
    id: moduleId,
    moduleId,
    relativePath: file.relative_path ?? null,
    absolutePath: file.path ?? null,
    packageName: typeof moduleId === "string" ? moduleId.split(".")[0] : null,
    layerTier: layer.id,
    layerLabel: layer.label,
    layerIndex: layer.index,
    callGraphSummary: file.call_graph?.summary ?? null,
    importEdges: buildModuleImportEdges(file.import_graph ?? null),
    exportSummary: buildModuleExportSummary(file, moduleId),
    dependencySummary: file.dependency_summary ?? null,
    coverageSignals: file.coverage_signals ?? null,
    gitChurn: file.git_churn ?? null,
    lineCount: file.line_count ?? null,
    callbackRegistrations: normalizeCallbackRegistrations(
      file.callback_registrations ?? file.callbackRegistrations ?? null,
      { includeFunction: true }
    ),
    dynamicCode: normalizeDynamicCode(file.dynamic_code ?? file.dynamicCode ?? null),
    entrypoints: normalizeEntrypointSignals(file.entrypoints ?? file.entryPoints ?? null),
    globals: normalizeModuleGlobals(file.globals ?? file.module_globals ?? null),
    unusedImports: normalizeUnusedImports(file.unused_imports ?? file.unusedImports ?? null),
    unreachableFunctions: normalizeUnreachableFunctions(
      file.unreachable_functions ?? file.unreachableFunctions ?? null,
      moduleId
    ),
    functions: [],
    classes: [],
  };
}

function buildModuleImportEdges(importGraph) {
  if (!Array.isArray(importGraph)) {
    return [];
  }

  const edges = [];

  importGraph.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }
    const kind = typeof entry.kind === "string" && entry.kind.trim().length > 0 ? entry.kind.trim() : null;
    const moduleName = typeof entry.module === "string" && entry.module.trim().length > 0 ? entry.module.trim() : null;
    const linenoRaw = entry.lineno ?? entry.line ?? entry.line_number ?? null;
    const lineno = Number.isFinite(Number(linenoRaw)) ? Number(linenoRaw) : null;
    const nestedEdges = Array.isArray(entry.edges) ? entry.edges : [];

    nestedEdges.forEach((edge) => {
      if (!edge || typeof edge !== "object") {
        return;
      }

      const target = normalizeString(edge.target ?? edge.module ?? edge.symbol ?? edge.name ?? null);
      if (!target) {
        return;
      }

      const category = normalizeString(edge.category ?? edge.classification) ?? "unknown";
      const functions = Array.isArray(edge.functions)
        ? Array.from(
            new Set(
              edge.functions
                .map((fn) => normalizeString(fn))
                .filter((fn) => typeof fn === "string" && fn.length > 0)
            )
          )
        : [];
      const via = Array.isArray(edge.via)
        ? Array.from(
            new Set(
              edge.via
                .map((alias) => normalizeString(alias))
                .filter((alias) => typeof alias === "string" && alias.length > 0)
            )
          )
        : [];
      let importedAs = normalizeString(edge.imported_as ?? edge.importedAs ?? edge.alias ?? null);
      if (!importedAs && via.length > 0) {
        importedAs = via[0];
      }
      const unused = edge.unused === true;

      edges.push({
        target,
        category,
        importedAs,
        unused,
        functions,
        via,
        kind,
        module: moduleName,
        lineno,
      });
    });
  });

  return edges;
}

function buildModuleExportSummary(file, moduleId) {
  if (!file || typeof file !== "object") {
    return {
      declared: [],
      missing: [],
      dynamic: false,
      lineno: null,
      counts: { declared: 0, functions: 0, classes: 0, globals: 0, reexports: 0, missing: 0, local: 0 },
      resolved: [],
      hasDeclared: false,
    };
  }

  const exportsInfo = typeof file.exports === "object" && file.exports !== null ? file.exports : null;
  const importDetails = Array.isArray(file.imports_detailed) ? file.imports_detailed : [];
  const functions = Array.isArray(file.functions) ? file.functions : [];
  const classes = Array.isArray(file.classes) ? file.classes : [];
  const globals = Array.isArray(file.globals) ? file.globals : [];

  const declaredSymbols = uniqueNormalizedStringList(exportsInfo?.symbols ?? []);
  const missingSymbols = uniqueNormalizedStringList(exportsInfo?.missing ?? []);
  const declaredSet = new Set(declaredSymbols);
  missingSymbols.forEach((symbol) => {
    if (!declaredSet.has(symbol)) {
      declaredSymbols.push(symbol);
      declaredSet.add(symbol);
    }
  });

  const missingSet = new Set(missingSymbols);
  const exposureIndex = buildImportExposureIndex(importDetails);
  const functionIndex = buildFunctionIndex(functions);
  const classIndex = buildClassIndex(classes);
  const globalIndex = buildGlobalIndex(globals);

  const resolved = [];
  const counts = {
    declared: 0,
    functions: 0,
    classes: 0,
    globals: 0,
    reexports: 0,
    missing: 0,
    local: 0,
  };

  declaredSymbols.forEach((symbol) => {
    const resolution = resolveExportSymbol(symbol, {
      moduleId,
      functionIndex,
      classIndex,
      globalIndex,
      exposureIndex,
      missingSet,
    });
    resolved.push(resolution);

    switch (resolution.kind) {
      case "function":
        counts.functions += 1;
        counts.local += 1;
        break;
      case "class":
        counts.classes += 1;
        counts.local += 1;
        break;
      case "global":
        counts.globals += 1;
        counts.local += 1;
        break;
      case "reexport":
        counts.reexports += 1;
        break;
      case "missing":
        counts.missing += 1;
        break;
      default:
        counts.missing += 1;
        break;
    }
  });

  counts.declared = declaredSymbols.length;

  return {
    declared: declaredSymbols,
    missing: missingSymbols,
    dynamic: exportsInfo?.dynamic === true,
    lineno: normalizeLineNumber(exportsInfo?.lineno),
    counts,
    resolved,
    hasDeclared: declaredSymbols.length > 0,
  };
}

function buildModuleApiSurface(moduleRecord, functionsMap, classesMap) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return {
      hasDeclaredExports: false,
      strategy: "implicit",
      exportedSymbols: [],
      functions: { public: [], internal: [] },
      classes: { public: [], internal: [] },
      globals: { public: [], internal: [] },
      reexports: [],
      missingExports: [],
      counts: {
        functions: { public: 0, internal: 0 },
        classes: { public: 0, internal: 0 },
        globals: { public: 0, internal: 0 },
        exported: 0,
        reexports: 0,
        missing: 0,
      },
    };
  }

  const exportSummary = moduleRecord.exportSummary ?? {};
  const resolvedExports = Array.isArray(exportSummary.resolved) ? exportSummary.resolved : [];
  const exportedSymbols = new Set();
  const reexports = [];
  const missingExports = [];

  resolvedExports.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }
    const kind = normalizeString(entry.kind);
    const symbol = normalizeString(entry.symbol);
    if (kind === "function" || kind === "class" || kind === "global") {
      if (symbol) {
        exportedSymbols.add(symbol);
      }
      return;
    }
    if (kind === "reexport") {
      if (symbol) {
        exportedSymbols.add(symbol);
      }
      reexports.push({
        symbol,
        sourceModule: normalizeString(entry.sourceModule ?? entry.source_module ?? null),
        sourceName: normalizeString(entry.sourceName ?? entry.source_name ?? null),
        sourceQualifiedName: normalizeString(entry.sourceQualifiedName ?? entry.source_qualified_name ?? null),
        lineno: normalizeLineNumber(entry.lineno),
      });
      return;
    }
    if (symbol) {
      missingExports.push({
        symbol,
        kind: kind ?? (entry.defined === false ? "missing" : "unknown"),
      });
    }
  });

  reexports.sort((left, right) => {
    const leftSymbol = left.symbol ?? "";
    const rightSymbol = right.symbol ?? "";
    if (leftSymbol !== rightSymbol) {
      return leftSymbol.localeCompare(rightSymbol);
    }
    const leftModule = left.sourceModule ?? "";
    const rightModule = right.sourceModule ?? "";
    if (leftModule !== rightModule) {
      return leftModule.localeCompare(rightModule);
    }
    return 0;
  });

  missingExports.sort((left, right) => {
    const leftSymbol = left.symbol ?? "";
    const rightSymbol = right.symbol ?? "";
    if (leftSymbol !== rightSymbol) {
      return leftSymbol.localeCompare(rightSymbol);
    }
    return 0;
  });

  const useExplicitExports = exportSummary.hasDeclared === true;
  const functionIds = Array.isArray(moduleRecord.functions) ? moduleRecord.functions : [];
  const classIds = Array.isArray(moduleRecord.classes) ? moduleRecord.classes : [];
  const globals = Array.isArray(moduleRecord.globals) ? moduleRecord.globals : [];

  const functionPublic = [];
  const functionInternal = [];
  functionIds.forEach((functionId) => {
    const fn = functionsMap.get(functionId);
    if (!fn || typeof fn !== "object") {
      return;
    }
    const entry = buildApiSurfaceItem({
      id: fn.id,
      name: fn.name,
      lineno: fn.lineno,
      docstringQuality: fn.docstringQuality ?? null,
      coverage: fn.metrics?.coverage ?? null,
      typeHintCoverage: fn.typeHintCoverage ?? null,
      exportedSymbols,
      useExplicitExports,
    });
    if (entry.category === "exported" || entry.category === "implicit") {
      functionPublic.push(entry);
    } else {
      functionInternal.push(entry);
    }
  });

  const classPublic = [];
  const classInternal = [];
  classIds.forEach((classId) => {
    const cls = classesMap.get(classId);
    if (!cls || typeof cls !== "object") {
      return;
    }
    const entry = buildApiSurfaceItem({
      id: cls.id,
      name: cls.name,
      lineno: cls.lineno,
      docstringQuality: cls.docstringQuality ?? null,
      methodCount: cls.methodCount ?? 0,
      exportedSymbols,
      useExplicitExports,
    });
    if (entry.category === "exported" || entry.category === "implicit") {
      classPublic.push(entry);
    } else {
      classInternal.push(entry);
    }
  });

  const globalPublic = [];
  const globalInternal = [];
  globals.forEach((globalEntry) => {
    if (!globalEntry || typeof globalEntry !== "object") {
      return;
    }
    const entry = buildApiSurfaceItem({
      id: moduleRecord.moduleId ? `${moduleRecord.moduleId}::${globalEntry.name}` : globalEntry.name,
      name: globalEntry.name,
      lineno: globalEntry.lineno,
      valueKind: globalEntry.valueKind ?? null,
      exportedSymbols,
      useExplicitExports,
    });
    if (entry.category === "exported" || entry.category === "implicit") {
      globalPublic.push(entry);
    } else {
      globalInternal.push(entry);
    }
  });

  functionPublic.sort((left, right) => left.name.localeCompare(right.name));
  functionInternal.sort((left, right) => left.name.localeCompare(right.name));
  classPublic.sort((left, right) => left.name.localeCompare(right.name));
  classInternal.sort((left, right) => left.name.localeCompare(right.name));
  globalPublic.sort((left, right) => left.name.localeCompare(right.name));
  globalInternal.sort((left, right) => left.name.localeCompare(right.name));

  const counts = {
    functions: {
      public: functionPublic.length,
      internal: functionInternal.length,
    },
    classes: {
      public: classPublic.length,
      internal: classInternal.length,
    },
    globals: {
      public: globalPublic.length,
      internal: globalInternal.length,
    },
    exported: exportedSymbols.size,
    reexports: reexports.length,
    missing: missingExports.length,
  };

  return {
    hasDeclaredExports: useExplicitExports,
    strategy: useExplicitExports ? "explicit" : "implicit",
  exportedSymbols: Array.from(exportedSymbols).sort(compareExportedSymbols),
    functions: {
      public: functionPublic,
      internal: functionInternal,
    },
    classes: {
      public: classPublic,
      internal: classInternal,
    },
    globals: {
      public: globalPublic,
      internal: globalInternal,
    },
    reexports,
    missingExports,
    counts,
  };
}

function compareExportedSymbols(left, right) {
  if (!left && !right) {
    return 0;
  }
  if (!left) {
    return 1;
  }
  if (!right) {
    return -1;
  }

  const leftWeight = getExportSymbolOrderingWeight(left);
  const rightWeight = getExportSymbolOrderingWeight(right);
  if (leftWeight !== rightWeight) {
    return leftWeight - rightWeight;
  }

  const leftLower = left.toLowerCase();
  const rightLower = right.toLowerCase();
  if (leftLower !== rightLower) {
    return leftLower.localeCompare(rightLower);
  }

  return left.localeCompare(right);
}

function getExportSymbolOrderingWeight(symbol) {
  if (!symbol) {
    return 3;
  }
  if (/^[A-Z0-9_]+$/.test(symbol)) {
    return 0;
  }
  if (/^[A-Z][A-Za-z0-9]*$/.test(symbol)) {
    return 1;
  }
  return 2;
}

function buildApiSurfaceItem(options) {
  const {
    id,
    name,
    lineno,
    docstringQuality,
    coverage,
    typeHintCoverage,
    methodCount,
    valueKind,
    exportedSymbols,
    useExplicitExports,
  } = options;

  const normalizedName = normalizeString(name ?? id) ?? null;
  const exported = normalizedName ? exportedSymbols.has(normalizedName) : false;
  const isPrivateName = normalizedName ? normalizedName.startsWith("_") : false;

  let category;
  let reason;
  if (exported) {
    category = "exported";
    reason = "Declared in __all__";
  } else if (isPrivateName) {
    category = "private";
    reason = "Name is prefixed with an underscore.";
  } else if (useExplicitExports) {
    category = "internal";
    reason = "Module defines __all__ and symbol is not exported.";
  } else {
    category = "implicit";
    reason = "Implicitly public because module does not define __all__.";
  }

  return {
    id,
    name: normalizedName ?? (typeof name === "string" ? name : id),
    qualifiedId: id,
    lineno: normalizeLineNumber(lineno),
    docstringQuality: docstringQuality ?? null,
    coverage: coverage ?? null,
    typeHintCoverage: typeHintCoverage ?? null,
    methodCount: typeof methodCount === "number" ? methodCount : null,
    valueKind: valueKind ?? null,
    exported,
    category,
    reason,
  };
}

function uniqueNormalizedStringList(values) {
  if (!Array.isArray(values)) {
    return [];
  }
  const seen = new Set();
  const normalized = [];
  values.forEach((value) => {
    const normalizedValue = normalizeString(value);
    if (!normalizedValue || seen.has(normalizedValue)) {
      return;
    }
    seen.add(normalizedValue);
    normalized.push(normalizedValue);
  });
  return normalized;
}

function normalizeLineNumber(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function buildFunctionIndex(functionEntries) {
  const index = new Map();
  functionEntries.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }
    const name = normalizeString(entry.name);
    if (!name || index.has(name)) {
      return;
    }
    index.set(name, entry);
  });
  return index;
}

function buildClassIndex(classEntries) {
  const index = new Map();
  classEntries.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }
    const name = normalizeString(entry.name);
    if (!name || index.has(name)) {
      return;
    }
    index.set(name, entry);
  });
  return index;
}

function buildGlobalIndex(globalEntries) {
  const index = new Map();
  globalEntries.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }
    const name = normalizeString(entry.name);
    if (!name || index.has(name)) {
      return;
    }
    index.set(name, entry);
  });
  return index;
}

function buildImportExposureIndex(importsDetailed) {
  const index = new Map();
  importsDetailed.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }
    const names = Array.isArray(entry.names) ? entry.names : [];
    const importKind = entry.kind === "from" ? "from" : "import";
    const moduleName = normalizeString(entry.module);
    const lineno = normalizeLineNumber(entry.lineno);
    const levelValue = normalizeLineNumber(entry.level);

    names.forEach((detail) => {
      if (!detail || typeof detail !== "object") {
        return;
      }
      const original = normalizeString(detail.name);
      const alias = normalizeString(detail.asname);
      const exposed = alias ?? original;
      if (!exposed) {
        return;
      }
      let qualified = original;
      if (importKind === "from") {
        qualified = moduleName ? `${moduleName}.${original ?? ""}`.replace(/\.$/, "") : original;
      }
      index.set(exposed, {
        original,
        module: importKind === "from" ? moduleName : original,
        importKind,
        level: Number.isFinite(levelValue) ? levelValue : 0,
        lineno,
        qualified: normalizeString(qualified),
      });
    });
  });
  return index;
}

function buildFunctionIdentifier(functionEntry, moduleId) {
  const qualified = normalizeString(functionEntry?.qualified_name ?? functionEntry?.qualifiedName);
  if (qualified) {
    return qualified;
  }
  const name = normalizeString(functionEntry?.name);
  if (moduleId && name) {
    return `${moduleId}::${name}`;
  }
  return name;
}

function buildClassQualifiedName(classEntry, moduleId) {
  const name = normalizeString(classEntry?.name);
  if (!name) {
    return null;
  }
  return moduleId ? `${moduleId}.${name}` : name;
}

function createClassRecord(classEntry, moduleId) {
  if (!classEntry || typeof classEntry !== "object") {
    return null;
  }

  const qualifiedName = buildClassQualifiedName(classEntry, moduleId);
  if (!qualifiedName) {
    return null;
  }

  const name = normalizeString(classEntry.name) ?? qualifiedName;
  const lineno = normalizeLineNumber(classEntry.line ?? classEntry.lineno);
  const lineCount = normalizeLineNumber(classEntry.line_count ?? classEntry.lineCount);
  const docstring = normalizeString(classEntry.docstring ?? classEntry.docString);
  const docstringQuality = classEntry.docstring_quality ?? classEntry.docstringQuality ?? null;
  const bases = normalizeClassBases(classEntry.bases);
  const decorators = normalizeDecorators(classEntry.decorators);
  const decoratorsDetailed = normalizeDecoratorDetails(
    classEntry.decorators_detailed ?? classEntry.decoratorsDetailed ?? null
  );
  const attributes = normalizeClassAttributes(classEntry.attributes);
  const methods = normalizeClassMethods(classEntry.methods, moduleId, name);
  const codeSmells = classEntry.code_smells ?? classEntry.codeSmells ?? null;

  return {
    id: qualifiedName,
    name,
    moduleId,
    lineno,
    lineCount,
    docstring,
    docstringQuality,
    bases,
    decorators,
    decoratorsDetailed,
    attributes,
    methods,
    methodCount: methods.length,
    attributeCount: attributes.length,
    codeSmells,
    resolvedBases: [],
    derivedClassIds: [],
  };
}

function normalizeClassBases(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((entry) => normalizeString(entry))
    .filter((entry) => typeof entry === "string" && entry.length > 0);
}

function normalizeClassAttributes(entries) {
  if (!Array.isArray(entries)) {
    return [];
  }
  return entries
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const name = normalizeString(entry.name ?? entry.attribute ?? null);
      const lineno = normalizeLineNumber(entry.lineno ?? entry.line ?? null);
      if (!name) {
        return null;
      }
      return { name, lineno };
    })
    .filter(Boolean);
}

function normalizeClassMethods(entries, moduleId, className) {
  if (!Array.isArray(entries)) {
    return [];
  }
  return entries
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const name = normalizeString(entry.name);
      const qualified = normalizeString(entry.qualified_name ?? entry.qualifiedName);
      const methodId = qualified ?? (moduleId && name ? `${moduleId}::${className}.${name}` : null);
      if (!methodId) {
        return null;
      }
      const lineno = normalizeLineNumber(entry.line ?? entry.lineno);
      const lineCount = normalizeLineNumber(entry.line_count ?? entry.lineCount);
      const docstringQuality = entry.docstring_quality ?? entry.docstringQuality ?? null;
      const decorators = normalizeDecorators(entry.decorators);
      const decoratorsDetailed = normalizeDecoratorDetails(
        entry.decorators_detailed ?? entry.decoratorsDetailed ?? null
      );
      const returnsKind = entry.returns_kind ?? entry.returnsKind ?? null;
      const metrics = {
        coverage: entry.coverage ?? null,
        lineCount,
      };
      return {
        id: methodId,
        name: name ?? methodId,
        lineno,
        signature: entry.signature ?? null,
        docstringQuality,
        decorators,
        decoratorsDetailed,
        returnsKind,
        metrics,
      };
    })
    .filter(Boolean);
}

function resolveExportSymbol(symbol, context) {
  const {
    moduleId,
    functionIndex,
    classIndex,
    globalIndex,
    exposureIndex,
    missingSet,
  } = context;

  const functionEntry = functionIndex.get(symbol);
  if (functionEntry) {
    return {
      symbol,
      kind: "function",
      defined: true,
      origin: "local",
      moduleId,
      functionId: buildFunctionIdentifier(functionEntry, moduleId),
      classQualifiedName: null,
      valueKind: null,
      lineno: normalizeLineNumber(functionEntry.line ?? functionEntry.lineno),
      signature: normalizeString(functionEntry.signature),
      docstringQuality: functionEntry.docstring_quality ?? null,
      sourceModule: null,
      sourceName: null,
      sourceQualifiedName: null,
      sourceImportKind: null,
      sourceLevel: null,
    };
  }

  const classEntry = classIndex.get(symbol);
  if (classEntry) {
    return {
      symbol,
      kind: "class",
      defined: true,
      origin: "local",
      moduleId,
      functionId: null,
      classQualifiedName: buildClassQualifiedName(classEntry, moduleId),
      valueKind: null,
      lineno: normalizeLineNumber(classEntry.line),
      signature: null,
      docstringQuality: classEntry.docstring_quality ?? null,
      sourceModule: null,
      sourceName: null,
      sourceQualifiedName: null,
      sourceImportKind: null,
      sourceLevel: null,
    };
  }

  const globalEntry = globalIndex.get(symbol);
  if (globalEntry) {
    return {
      symbol,
      kind: "global",
      defined: true,
      origin: "local",
      moduleId,
      functionId: null,
      classQualifiedName: null,
      valueKind: normalizeString(globalEntry.value_kind ?? globalEntry.valueKind),
      lineno: normalizeLineNumber(globalEntry.lineno ?? globalEntry.line),
      signature: null,
      docstringQuality: null,
      sourceModule: null,
      sourceName: null,
      sourceQualifiedName: null,
      sourceImportKind: null,
      sourceLevel: null,
    };
  }

  const exposure = exposureIndex.get(symbol);
  if (exposure) {
    return {
      symbol,
      kind: "reexport",
      defined: true,
      origin: "reexport",
      moduleId,
      functionId: null,
      classQualifiedName: null,
      valueKind: null,
      lineno: exposure.lineno,
      signature: null,
      docstringQuality: null,
      sourceModule: exposure.module ?? null,
      sourceName: exposure.original ?? null,
      sourceQualifiedName: exposure.qualified ?? null,
      sourceImportKind: exposure.importKind,
      sourceLevel: exposure.level,
    };
  }

  const isMissing = missingSet.has(symbol);
  return {
    symbol,
    kind: isMissing ? "missing" : "unknown",
    defined: false,
    origin: isMissing ? "missing" : "unknown",
    moduleId,
    functionId: null,
    classQualifiedName: null,
    valueKind: null,
    lineno: null,
    signature: null,
    docstringQuality: null,
    sourceModule: null,
    sourceName: null,
    sourceQualifiedName: null,
    sourceImportKind: null,
    sourceLevel: null,
  };
}

function createFunctionRecord(fn, moduleId) {
  if (!fn || typeof fn !== "object") {
    return null;
  }

  const fallbackName = fn.name || "anonymous";
  const functionId = fn.qualified_name || (moduleId ? `${moduleId}::${fallbackName}` : null);
  if (!functionId) {
    return null;
  }

  const calls = Array.isArray(fn.calls)
    ? fn.calls
        .map((call) => call?.callee || call?.qualified_name || call?.attribute || null)
        .filter(Boolean)
    : [];
  const loggingCalls = normalizeLoggingCalls(fn?.loggingCalls ?? fn?.logging_calls);
  const decorators = normalizeDecorators(fn?.decorators);
  const decoratorsDetailed = normalizeDecoratorDetails(fn?.decorators_detailed ?? fn?.decoratorsDetailed);

  return {
    id: functionId,
    name: fn.name ?? functionId,
    moduleId,
    lineno: fn.line ?? fn.lineno ?? null,
    signature: fn.signature ?? null,
    returnsKind: fn.returns_kind ?? null,
    cyclomaticComplexity: fn.cyclomatic_complexity ?? null,
    typeHintCoverage: fn.type_hint_coverage ?? null,
    annotationCoverage: fn.annotation_quality?.coverage ?? null,
    docstringQuality: fn.docstring_quality ?? null,
    todoTags: fn.todo_tags ?? 0,
    localsSummary: fn.locals_summary ?? null,
    loggingCalls,
    decorators,
    decoratorsDetailed,
    callbackRegistrations: normalizeCallbackRegistrations(
      fn.callback_registrations ?? fn.callbackRegistrations ?? null
    ),
    ioEffects: normalizeIoEffects(fn.io_effects ?? fn.ioEffects ?? null),
    usedGlobals: normalizeUsedGlobals(fn.used_globals ?? fn.usedGlobals ?? null),
    raisedExceptions: normalizeRaisedExceptions(
      fn.raises ?? fn.raised_exceptions ?? fn.raisedExceptions ?? null
    ),
    metrics: {
      coverage: fn.coverage ?? null,
      lineCount: fn.line_count ?? null,
    },
    calls,
  };
}

function normalizeLoggingCalls(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((call) => {
      if (!call || typeof call !== "object") {
        return null;
      }
      const levelRaw = call.level ?? call.log_level ?? call.levelname ?? null;
      const level = typeof levelRaw === "string" && levelRaw.trim().length > 0 ? levelRaw.trim().toLowerCase() : null;
      const linenoRaw = call.lineno ?? call.line ?? call.line_number ?? null;
      const linenoNumeric = Number.isFinite(Number(linenoRaw)) ? Number(linenoRaw) : null;
      const message = typeof call.message === "string" && call.message.trim().length > 0 ? call.message.trim() : null;
      const loggerName = typeof call.logger === "string" && call.logger.trim().length > 0 ? call.logger.trim() : null;
      if (!level && linenoNumeric === null && !message && !loggerName) {
        return null;
      }
      return {
        level,
        lineno: linenoNumeric,
        message,
        logger: loggerName,
      };
    })
    .filter(Boolean);
}

function normalizeIoEffects(value) {
  const source = value && typeof value === "object" ? value : {};
  const reads = source.reads === true || source.read === true || source.file === true || source.filesystem === true;
  const writes = source.writes === true || source.write === true || source.fileio === true;
  const env = source.env === true || source.environment === true || source.environ === true;
  const network = source.network === true || source.socket === true || source.http === true;

  const activeFlags = [];
  if (reads) {
    activeFlags.push("reads");
  }
  if (writes) {
    activeFlags.push("writes");
  }
  if (env) {
    activeFlags.push("env");
  }
  if (network) {
    activeFlags.push("network");
  }

  activeFlags.sort((left, right) => left.localeCompare(right));

  return {
    reads,
    writes,
    env,
    network,
    hasEffects: activeFlags.length > 0,
    activeFlags,
    flagCount: activeFlags.length,
  };
}

function normalizeRaisedExceptions(value) {
  if (!Array.isArray(value)) {
    return [];
  }

  const seen = new Set();
  const normalized = [];

  value.forEach((entry) => {
    let raw = null;
    let moduleName = null;
    let qualifiedName = null;
    let type = null;
    let message = null;
    let lineno = null;

    if (typeof entry === "string") {
      raw = entry.trim();
    } else if (entry && typeof entry === "object") {
      raw = normalizeString(
        entry.exception ?? entry.expression ?? entry.representation ?? entry.raw ?? entry.name ?? null
      );
      moduleName = normalizeString(entry.module ?? entry.module_name ?? entry.moduleId ?? entry.module_id ?? null);
      qualifiedName = normalizeString(
        entry.qualified_name ?? entry.qualifiedName ?? entry.qualname ?? entry.exception_qualified_name ?? null
      );
      type = normalizeString(entry.type ?? entry.exception_type ?? entry.class ?? entry.kind ?? null);
      message = normalizeString(entry.message ?? entry.detail ?? entry.reason ?? null);
      lineno = normalizeLineNumber(entry.lineno ?? entry.line ?? entry.line_number ?? null);
    } else if (entry !== null && entry !== undefined) {
      raw = String(entry).trim();
    }

    if (!type || type.length === 0 || !message) {
      const inference = inferExceptionTypeAndMessage(raw ?? qualifiedName ?? type ?? null);
      if (!type && inference.type) {
        type = inference.type;
      }
      if (!message && inference.message) {
        message = inference.message;
      }
    }

    if (!qualifiedName && type) {
      qualifiedName = type;
    }

    if (!raw && qualifiedName) {
      raw = qualifiedName;
    }

    if (!type && !raw) {
      return;
    }

    const dedupeKey = `${type ?? ""}|${message ?? ""}|${qualifiedName ?? ""}`;
    if (seen.has(dedupeKey)) {
      return;
    }
    seen.add(dedupeKey);

    normalized.push({
      type: type ?? null,
      message: message ?? null,
      raw: raw ?? null,
      qualifiedName,
      module: moduleName,
      lineno,
    });
  });

  normalized.sort((left, right) => {
    const leftType = left.type ?? "";
    const rightType = right.type ?? "";
    if (leftType !== rightType) {
      return leftType.localeCompare(rightType);
    }
    const leftMessage = left.message ?? "";
    const rightMessage = right.message ?? "";
    if (leftMessage !== rightMessage) {
      return leftMessage.localeCompare(rightMessage);
    }
    const leftLineno = Number.isFinite(left.lineno) ? left.lineno : Number.MAX_SAFE_INTEGER;
    const rightLineno = Number.isFinite(right.lineno) ? right.lineno : Number.MAX_SAFE_INTEGER;
    if (leftLineno !== rightLineno) {
      return leftLineno - rightLineno;
    }
    const leftQualified = left.qualifiedName ?? "";
    const rightQualified = right.qualifiedName ?? "";
    if (leftQualified !== rightQualified) {
      return leftQualified.localeCompare(rightQualified);
    }
    return 0;
  });

  return normalized;
}

function inferExceptionTypeAndMessage(raw) {
  if (typeof raw !== "string") {
    return { type: null, message: null };
  }
  const trimmed = raw.trim();
  if (!trimmed) {
    return { type: null, message: null };
  }
  const openIndex = trimmed.indexOf("(");
  if (openIndex < 0) {
    return { type: trimmed, message: null };
  }
  const type = trimmed.slice(0, openIndex).trim();
  const closeIndex = trimmed.lastIndexOf(")");
  const messageSlice = closeIndex > openIndex ? trimmed.slice(openIndex + 1, closeIndex) : trimmed.slice(openIndex + 1);
  let message = messageSlice.trim();
  if (
    (message.startsWith("'") && message.endsWith("'")) ||
    (message.startsWith('"') && message.endsWith('"'))
  ) {
    message = message.slice(1, -1);
  }
  return {
    type: type || trimmed,
    message: message || null,
  };
}

function normalizeUsedGlobals(value) {
  if (!Array.isArray(value)) {
    return [];
  }

  const seen = new Set();
  const normalized = [];

  value.forEach((entry) => {
    const name = normalizeString(entry);
    if (!name || seen.has(name)) {
      return;
    }
    seen.add(name);
    normalized.push(name);
  });

  normalized.sort((left, right) => left.localeCompare(right));
  return normalized;
}

function normalizeDecorators(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((entry) => {
      if (typeof entry === "string") {
        const trimmed = entry.trim();
        return trimmed.length > 0 ? trimmed : null;
      }
      if (entry && typeof entry === "object") {
        const name = typeof entry.name === "string" ? entry.name.trim() : null;
        return name && name.length > 0 ? name : null;
      }
      return null;
    })
    .filter(Boolean);
}

function normalizeDecoratorDetails(value) {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }

      const name = normalizeString(entry.name ?? entry.decorator ?? entry.id ?? null);
      const moduleName = normalizeString(entry.module ?? entry.module_name ?? entry.moduleId ?? entry.module_id ?? null);
      const qualifiedName = normalizeString(entry.qualified_name ?? entry.qualifiedName ?? entry.qualname ?? null);
      const expression = normalizeString(
        entry.call ?? entry.expression ?? entry.representation ?? entry.expr ?? entry.source ?? null
      );

      const args = Array.isArray(entry.args)
        ? entry.args
            .map((arg) => normalizeString(arg))
            .filter((arg) => typeof arg === "string" && arg.length > 0)
        : [];

      const kwargs = [];
      if (entry.kwargs && typeof entry.kwargs === "object") {
        Object.entries(entry.kwargs).forEach(([key, rawValue]) => {
          if (typeof key !== "string" || key.trim().length === 0) {
            return;
          }
          const valueString = normalizeString(rawValue);
          if (!valueString) {
            return;
          }
          kwargs.push({ name: key.trim(), value: valueString });
        });
      }

      if (!name && args.length === 0 && kwargs.length === 0 && !expression) {
        return null;
      }

      return {
        name,
        module: moduleName,
        qualifiedName,
        args,
        kwargs,
        expression,
      };
    })
    .filter(Boolean);
}

function normalizeClassBaseReference(raw) {
  if (typeof raw !== "string") {
    return null;
  }
  let candidate = raw.trim();
  if (!candidate) {
    return null;
  }
  const genericIndex = candidate.indexOf("[");
  if (genericIndex >= 0) {
    candidate = candidate.slice(0, genericIndex);
  }
  const callIndex = candidate.indexOf("(");
  if (callIndex >= 0) {
    candidate = candidate.slice(0, callIndex);
  }
  candidate = candidate.replace(/\s+/g, "");
  if (!candidate) {
    return null;
  }
  return candidate;
}

function resolveClassInheritanceRelationships(classMap) {
  if (!(classMap instanceof Map)) {
    return { derivedByBase: new Map() };
  }

  const nameIndex = new Map();
  classMap.forEach((record) => {
    const key = (record?.name ?? "").toLowerCase();
    if (!nameIndex.has(key)) {
      nameIndex.set(key, []);
    }
    nameIndex.get(key).push(record);
    if (!Array.isArray(record?.resolvedBases)) {
      record.resolvedBases = [];
    }
    if (!Array.isArray(record?.derivedClassIds)) {
      record.derivedClassIds = [];
    }
  });

  const derivedMap = new Map();

  classMap.forEach((record) => {
    if (!record || typeof record !== "object") {
      return;
    }
    const bases = Array.isArray(record.bases) ? record.bases : [];
    const resolvedBases = [];
    const seen = new Set();
    bases.forEach((rawBase) => {
      const resolution = resolveClassBaseReference(rawBase, record, classMap, nameIndex);
      if (!resolution) {
        return;
      }
      const dedupeKey = `${resolution.normalized}|${resolution.classId ?? "unknown"}`;
      if (seen.has(dedupeKey)) {
        return;
      }
      seen.add(dedupeKey);
      resolvedBases.push(resolution);
      if (resolution.classId) {
        const existing = derivedMap.get(resolution.classId) ?? new Set();
        existing.add(record.id);
        derivedMap.set(resolution.classId, existing);
      }
    });
    record.resolvedBases = resolvedBases;
  });

  derivedMap.forEach((derivedSet, classId) => {
    const record = classMap.get(classId);
    if (record) {
      record.derivedClassIds = Array.from(derivedSet).sort((left, right) => left.localeCompare(right));
    }
  });

  classMap.forEach((record) => {
    if (!Array.isArray(record.derivedClassIds)) {
      record.derivedClassIds = [];
    }
  });

  return { derivedByBase: derivedMap };
}

function resolveClassBaseReference(rawBase, record, classMap, nameIndex) {
  const normalized = normalizeClassBaseReference(rawBase);
  if (!normalized) {
    return null;
  }

  const lookup = findClassReference(normalized, record, classMap, nameIndex);

  let matchType = "external";
  let moduleId = lookup.moduleId ?? null;
  if (lookup.classId) {
    matchType = lookup.moduleId === record.moduleId ? "local" : "project";
  } else if (normalized === "object" || normalized === "Exception") {
    matchType = "builtin";
    moduleId = null;
  } else if (!moduleId && normalized === record.name) {
    matchType = "self";
  } else if (!moduleId && !normalized.includes(".")) {
    matchType = "unknown";
  }

  return {
    raw: rawBase,
    normalized,
    classId: lookup.classId ?? null,
    moduleId,
    matchType,
  };
}

function findClassReference(normalized, record, classMap, nameIndex) {
  const segments = normalized.split(".");
  const candidateName = segments[segments.length - 1];
  const candidateModule = segments.length > 1 ? segments.slice(0, -1).join(".") : null;

  const directCandidates = [];
  if (candidateModule) {
    directCandidates.push(`${candidateModule}.${candidateName}`);
  }
  if (record?.moduleId) {
    directCandidates.push(`${record.moduleId}.${candidateName}`);
  }

  for (const candidateId of directCandidates) {
    if (classMap.has(candidateId)) {
      const match = classMap.get(candidateId);
      return { classId: match.id, moduleId: match.moduleId };
    }
  }

  const nameMatches = nameIndex.get(candidateName.toLowerCase()) ?? [];
  if (nameMatches.length === 1) {
    const match = nameMatches[0];
    return { classId: match.id, moduleId: match.moduleId };
  }

  return { classId: null, moduleId: candidateModule };
}

function buildClassInheritanceIndex(classMap) {
  if (!(classMap instanceof Map)) {
    return {
      derivedByBase: new Map(),
      modules: new Map(),
      stats: {
        classCount: 0,
        modulesWithClasses: 0,
        rootClasses: 0,
        leafClasses: 0,
        externalBaseReferences: 0,
      },
    };
  }

  const modulesWithClasses = new Map();
  const derivedByBase = new Map();
  let externalBaseReferences = 0;

  classMap.forEach((record) => {
    if (!record || typeof record !== "object") {
      return;
    }
    if (!modulesWithClasses.has(record.moduleId)) {
      modulesWithClasses.set(record.moduleId, []);
    }
    modulesWithClasses.get(record.moduleId).push(record.id);

    const resolvedBases = Array.isArray(record.resolvedBases) ? record.resolvedBases : [];
    resolvedBases.forEach((base) => {
      if (base.classId) {
        const derivedSet = derivedByBase.get(base.classId) ?? new Set();
        derivedSet.add(record.id);
        derivedByBase.set(base.classId, derivedSet);
      } else if (base.matchType === "external" || base.matchType === "builtin") {
        externalBaseReferences += 1;
      }
    });
  });

  modulesWithClasses.forEach((list, moduleId) => {
    modulesWithClasses.set(moduleId, list.sort((left, right) => left.localeCompare(right)));
  });

  const derivedByBaseSorted = new Map();
  derivedByBase.forEach((derivedSet, classId) => {
    derivedByBaseSorted.set(classId, Array.from(derivedSet).sort((left, right) => left.localeCompare(right)));
  });

  const stats = {
    classCount: classMap.size,
    modulesWithClasses: modulesWithClasses.size,
    rootClasses: 0,
    leafClasses: 0,
    externalBaseReferences,
  };

  classMap.forEach((record) => {
    const resolvedBases = Array.isArray(record.resolvedBases) ? record.resolvedBases : [];
    const derivedClassIds = Array.isArray(record.derivedClassIds) ? record.derivedClassIds : [];
    if (resolvedBases.length === 0) {
      stats.rootClasses += 1;
    }
    if (derivedClassIds.length === 0) {
      stats.leafClasses += 1;
    }
  });

  return {
    derivedByBase: derivedByBaseSorted,
    modules: modulesWithClasses,
    stats,
  };
}

function normalizeDynamicCode(value) {
  if (!value || typeof value !== "object") {
    return null;
  }

  const flagsSource = value.flags && typeof value.flags === "object" ? value.flags : {};
  const flags = {
    exec: flagsSource.exec === true,
    dynamicImport: flagsSource.dynamic_import === true || flagsSource.dynamicImport === true,
    metaclass: flagsSource.metaclass === true,
    globalsMutation: flagsSource.globals_mutation === true || flagsSource.globalsMutation === true,
  };

  const activeFlags = Object.entries(flags)
    .filter(([, enabled]) => enabled)
    .map(([flagKey]) => flagKey);

  const events = Array.isArray(value.events)
    ? value.events
        .map((entry) => {
          if (!entry || typeof entry !== "object") {
            return null;
          }

          const kind = normalizeString(entry.kind ?? entry.type ?? entry.category ?? null) ?? "unknown";
          const detail = normalizeString(entry.detail ?? entry.description ?? entry.expr ?? entry.value ?? null);
          const lineno = normalizeLineNumber(entry.lineno ?? entry.line ?? entry.line_number ?? null);

          if (!kind && detail === null && lineno === null) {
            return null;
          }

          return {
            kind: kind ?? "unknown",
            detail,
            lineno,
          };
        })
        .filter(Boolean)
        .sort((left, right) => {
          if (left.kind !== right.kind) {
            return left.kind.localeCompare(right.kind);
          }
          const leftLine = Number.isFinite(left.lineno) ? left.lineno : Number.MAX_SAFE_INTEGER;
          const rightLine = Number.isFinite(right.lineno) ? right.lineno : Number.MAX_SAFE_INTEGER;
          if (leftLine !== rightLine) {
            return leftLine - rightLine;
          }
          const leftDetail = left.detail ?? "";
          const rightDetail = right.detail ?? "";
          return leftDetail.localeCompare(rightDetail);
        })
    : [];

  const hasDynamic = activeFlags.length > 0 || events.length > 0;
  if (!hasDynamic) {
    return null;
  }

  return {
    hasDynamic: true,
    flags,
    activeFlags,
    flagCount: activeFlags.length,
    events,
    eventCount: events.length,
  };
}

function normalizeModuleGlobals(entries) {
  if (!Array.isArray(entries)) {
    return [];
  }

  const results = [];
  const seen = new Set();

  entries.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }
    const name = normalizeString(entry.name ?? entry.identifier ?? entry.id ?? null);
    if (!name || seen.has(name)) {
      return;
    }
    seen.add(name);

    const valueKind = normalizeString(entry.value_kind ?? entry.valueKind ?? entry.kind ?? null) ?? "unknown";
    const lineno = normalizeLineNumber(entry.lineno ?? entry.line ?? entry.line_number ?? null);

    results.push({
      name,
      valueKind,
      lineno,
    });
  });

  results.sort((left, right) => {
    const nameCompare = left.name.localeCompare(right.name);
    if (nameCompare !== 0) {
      return nameCompare;
    }
    const leftLine = Number.isFinite(left.lineno) ? left.lineno : Number.MAX_SAFE_INTEGER;
    const rightLine = Number.isFinite(right.lineno) ? right.lineno : Number.MAX_SAFE_INTEGER;
    return leftLine - rightLine;
  });

  return results;
}

function normalizeUnusedImports(entries) {
  if (!Array.isArray(entries)) {
    return [];
  }

  const results = [];
  const seen = new Set();

  entries.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }

    const target = normalizeString(entry.target ?? entry.symbol ?? entry.name ?? null);
    const moduleName = normalizeString(entry.module ?? null);
    const importedAs = normalizeString(entry.imported_as ?? entry.importedAs ?? entry.alias ?? null);
    const key = `${moduleName ?? ""}|${target ?? ""}|${importedAs ?? ""}`;
    if (seen.has(key)) {
      return;
    }
    seen.add(key);

    const kind = normalizeString(entry.kind ?? entry.import_kind ?? null) ?? "import";
    const lineno = normalizeLineNumber(entry.lineno ?? entry.line ?? entry.line_number ?? null);

    results.push({
      target,
      module: moduleName,
      importedAs,
      kind,
      lineno,
    });
  });

  results.sort((left, right) => {
    const leftLine = Number.isFinite(left.lineno) ? left.lineno : Number.MAX_SAFE_INTEGER;
    const rightLine = Number.isFinite(right.lineno) ? right.lineno : Number.MAX_SAFE_INTEGER;
    if (leftLine !== rightLine) {
      return leftLine - rightLine;
    }
    const leftTarget = left.target ?? "";
    const rightTarget = right.target ?? "";
    if (leftTarget !== rightTarget) {
      return leftTarget.localeCompare(rightTarget);
    }
    const leftAlias = left.importedAs ?? "";
    const rightAlias = right.importedAs ?? "";
    return leftAlias.localeCompare(rightAlias);
  });

  return results;
}

function normalizeUnreachableFunctions(entries, moduleId) {
  if (!Array.isArray(entries)) {
    return [];
  }

  const results = [];
  const seen = new Set();

  entries.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }

    const qualifiedName = normalizeString(entry.qualified_name ?? entry.qualifiedName ?? entry.name ?? null);
    if (!qualifiedName) {
      return;
    }
    if (seen.has(qualifiedName)) {
      return;
    }
    seen.add(qualifiedName);

    const name = normalizeString(entry.name ?? entry.function ?? null) ?? qualifiedName;
    const parentClass = normalizeString(entry.parent_class ?? entry.parentClass ?? null);
    const kind = normalizeString(entry.kind ?? entry.type ?? null) ?? "function";
    const lineno = normalizeLineNumber(entry.lineno ?? entry.line ?? entry.line_number ?? null);

    results.push({
      name,
      qualifiedName,
      parentClass,
      kind,
      lineno,
      moduleId: moduleId ?? null,
    });
  });

  results.sort((left, right) => {
    const leftKind = left.kind ?? "";
    const rightKind = right.kind ?? "";
    if (leftKind !== rightKind) {
      return leftKind.localeCompare(rightKind);
    }
    const leftLine = Number.isFinite(left.lineno) ? left.lineno : Number.MAX_SAFE_INTEGER;
    const rightLine = Number.isFinite(right.lineno) ? right.lineno : Number.MAX_SAFE_INTEGER;
    if (leftLine !== rightLine) {
      return leftLine - rightLine;
    }
    return left.qualifiedName.localeCompare(right.qualifiedName);
  });

  return results;
}

function normalizeEntrypointSignals(value) {
  const hasMainGuard = value?.has_main_guard === true || value?.hasMainGuard === true;
  const cliParser = value?.cli_parser === true || value?.cliParser === true;
  return {
    hasMainGuard,
    cliParser,
    candidates: [],
  };
}

function buildCallGraphInboundIndex(functionCallMap) {
  const inbound = new Map();
  if (!(functionCallMap instanceof Map)) {
    return inbound;
  }

  functionCallMap.forEach((targets, sourceId) => {
    if (!Array.isArray(targets)) {
      return;
    }
    targets.forEach((targetId) => {
      if (!targetId || typeof targetId !== "string") {
        return;
      }
      let inboundSet = inbound.get(targetId);
      if (!inboundSet) {
        inboundSet = new Set();
        inbound.set(targetId, inboundSet);
      }
      inboundSet.add(sourceId);
    });
  });

  return inbound;
}

function determineEntrypointReason(fnRecord, metadata, inboundIndex) {
  const name = typeof fnRecord?.name === "string" ? fnRecord.name.toLowerCase() : "";
  const outboundCount = Array.isArray(fnRecord?.calls) ? fnRecord.calls.length : 0;
  const inboundCount = inboundIndex.get(fnRecord?.id)?.size ?? 0;
  const matchesExact = ENTRYPOINT_NAME_HINTS.includes(name);
  const matchesSuffix = ENTRYPOINT_SUFFIX_HINTS.some((suffix) => name.endsWith(suffix));

  if (metadata.hasMainGuard && (matchesExact || matchesSuffix)) {
    return ENTRYPOINT_REASON.MAIN_GUARD_NAME;
  }
  if (metadata.cliParser && (matchesExact || matchesSuffix)) {
    return ENTRYPOINT_REASON.CLI_PARSER_NAME;
  }
  if (metadata.hasMainGuard && outboundCount > 0 && inboundCount === 0) {
    return ENTRYPOINT_REASON.MAIN_GUARD_ISOLATED;
  }
  if (metadata.cliParser && outboundCount > 0 && inboundCount === 0) {
    return ENTRYPOINT_REASON.CLI_PARSER_ISOLATED;
  }
  return null;
}

function populateEntrypointCandidates(modules, functions, callGraph) {
  const functionCallMap = callGraph?.functions instanceof Map ? callGraph.functions : new Map();
  const inboundIndex = buildCallGraphInboundIndex(functionCallMap);
  const index = new Map();

  modules.forEach((moduleRecord, moduleId) => {
    const entryMeta = normalizeEntrypointSignals(moduleRecord?.entrypoints);
    const moduleFunctionIds = Array.isArray(moduleRecord?.functions) ? moduleRecord.functions : [];
    const candidates = [];

    moduleFunctionIds.forEach((functionId) => {
      const fnRecord = functions.get(functionId);
      if (!fnRecord) {
        return;
      }
      const reason = determineEntrypointReason(fnRecord, entryMeta, inboundIndex);
      if (!reason) {
        return;
      }
      const outboundTargets = functionCallMap.get(functionId);
      candidates.push({
        id: fnRecord.id,
        name: fnRecord.name ?? fnRecord.id,
        moduleId: moduleRecord.moduleId,
        reason,
        inboundCount: inboundIndex.get(functionId)?.size ?? 0,
        outboundCount: Array.isArray(outboundTargets) ? outboundTargets.length : 0,
      });
    });

    candidates.sort((left, right) => {
      if (right.outboundCount !== left.outboundCount) {
        return right.outboundCount - left.outboundCount;
      }
      if (left.reason !== right.reason) {
        return left.reason.localeCompare(right.reason);
      }
      return left.name.localeCompare(right.name);
    });

    moduleRecord.entrypoints = {
      ...entryMeta,
      candidates,
    };

    if (candidates.length > 0) {
      index.set(moduleId, {
        moduleId: moduleRecord.moduleId,
        hasMainGuard: entryMeta.hasMainGuard,
        cliParser: entryMeta.cliParser,
        candidates,
      });
    }
  });

  return index;
}

function normalizeCallbackRegistrations(value, options = {}) {
  if (!Array.isArray(value)) {
    return [];
  }

  const includeFunction = options.includeFunction === true;

  return value
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }

      const expression = normalizeString(
        entry.expression ?? entry.call ?? entry.representation ?? entry.expr ?? entry.source ?? null
      );
      const method = normalizeString(entry.method ?? entry.method_name ?? entry.methodName ?? null);
      const kind = normalizeString(entry.kind ?? entry.type ?? null);
      const root = normalizeString(entry.root ?? entry.binding ?? null);
      const moduleName = normalizeString(entry.module ?? entry.module_name ?? entry.moduleId ?? entry.module_id ?? null);
      const resolved = normalizeString(entry.resolved ?? entry.resolved_target ?? entry.resolvedTarget ?? null);
      const target = normalizeString(entry.target ?? entry.target_value ?? entry.targetValue ?? null);
      const targetKind = normalizeString(entry.target_kind ?? entry.targetKind ?? null);
      const targetVia = normalizeString(entry.target_via ?? entry.targetVia ?? null);
      const lineno = normalizeLineNumber(entry.lineno ?? entry.line ?? entry.line_number ?? null);

      if (!expression && !target && !method) {
        return null;
      }

      const registration = {
        expression,
        method,
        kind,
        root,
        module: moduleName,
        resolved,
        target,
        targetKind,
        targetVia,
        lineno,
      };

      if (includeFunction) {
        const functionName = normalizeString(
          entry.function ?? entry.function_name ?? entry.functionName ?? entry.qualified_name ?? null
        );
        if (functionName) {
          registration.function = functionName;
        }
      }

      return registration;
    })
    .filter(Boolean);
}

function normalizeString(value) {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return null;
}

function buildScreeningCallIndex(screening) {
  if (!screening || typeof screening !== "object") {
    return new Map();
  }

  const edges = screening.graphs?.calls;
  if (!Array.isArray(edges)) {
    return new Map();
  }

  const index = new Map();
  edges.forEach((edge) => {
    if (!Array.isArray(edge) || edge.length < 2) {
      return;
    }
    const [source, target] = edge;
    if (!source || !target) {
      return;
    }
    const existing = index.get(source) ?? [];
    if (!existing.includes(target)) {
      existing.push(target);
      index.set(source, existing);
    }
  });
  return index;
}

function buildScreeningHistory(screening) {
  if (!screening || typeof screening !== "object") {
    return {
      events: [],
      packs: new Map(),
      latest: null,
    };
  }

  const historyEntries = Array.isArray(screening.score_history) ? [...screening.score_history] : [];
  if (historyEntries.length === 0 && screening.score_snapshot && typeof screening.score_snapshot === "object") {
    historyEntries.push(screening.score_snapshot);
  }
  const events = [];
  const packs = new Map();

  historyEntries.forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }

    const timestamp = typeof entry.timestamp === "string" ? entry.timestamp : null;
    const context = typeof entry.context === "object" && entry.context !== null ? entry.context : {};
    const packEntries = Array.isArray(entry.packs) ? entry.packs : [];

    packEntries.forEach((pack) => {
      if (!pack || typeof pack !== "object") {
        return;
      }

      const packId = typeof pack.id === "string" && pack.id.trim() ? pack.id : null;
      const packLabel = typeof pack.label === "string" && pack.label.trim() ? pack.label : null;
      let scoreValue = null;
      if (pack.score !== null && pack.score !== undefined && pack.score !== "") {
        const numericScore = Number(pack.score);
        if (Number.isFinite(numericScore)) {
          scoreValue = numericScore;
        }
      }
      const severity = typeof pack.severity === "string" ? pack.severity : "unknown";
      const thresholds = typeof pack.thresholds === "object" && pack.thresholds !== null ? pack.thresholds : {};
      let warning = null;
      if (thresholds.warning !== null && thresholds.warning !== undefined && thresholds.warning !== "") {
        const warningThreshold = Number(thresholds.warning);
        if (Number.isFinite(warningThreshold)) {
          warning = warningThreshold;
        }
      }
      let failure = null;
      if (thresholds.failure !== null && thresholds.failure !== undefined && thresholds.failure !== "") {
        const failureThreshold = Number(thresholds.failure);
        if (Number.isFinite(failureThreshold)) {
          failure = failureThreshold;
        }
      }

      const event = {
        timestamp,
        packId,
        packLabel,
        severity,
        score: scoreValue,
        thresholds: {
          warning,
          failure,
        },
        context,
        metrics: typeof pack.metrics === "object" && pack.metrics !== null ? pack.metrics : {},
      };

      events.push(event);

      const key = packId ?? packLabel ?? "unknown";
      const bucket = packs.get(key) ?? [];
      bucket.push(event);
      packs.set(key, bucket);
    });
  });

  events.sort((left, right) => {
    const leftTimestamp = left.timestamp ?? "";
    const rightTimestamp = right.timestamp ?? "";
    return leftTimestamp.localeCompare(rightTimestamp);
  });

  packs.forEach((bucket, key) => {
    bucket.sort((left, right) => {
      const leftTimestamp = left.timestamp ?? "";
      const rightTimestamp = right.timestamp ?? "";
      return leftTimestamp.localeCompare(rightTimestamp);
    });
    packs.set(key, bucket);
  });

  return {
    events,
    packs,
    latest: events.length > 0 ? events[events.length - 1] : null,
  };
}

function buildMetricsCache(inventory, modules, functions, screening) {
  const moduleMetrics = new Map();
  modules.forEach((moduleRecord, moduleId) => {
    moduleMetrics.set(moduleId, {
      gitChurn: moduleRecord.gitChurn ?? null,
      coverageSignals: moduleRecord.coverageSignals ?? null,
      lineCount: moduleRecord.lineCount ?? null,
    });
  });

  const functionMetrics = new Map();
  functions.forEach((functionRecord, functionId) => {
    functionMetrics.set(functionId, {
      complexity: functionRecord.cyclomaticComplexity ?? null,
      coverage: functionRecord.metrics.coverage ?? null,
      lineCount: functionRecord.metrics.lineCount ?? null,
      todoTags: functionRecord.todoTags ?? 0,
    });
  });

  return {
    repository: inventory?.statistics ?? {},
    modules: moduleMetrics,
    functions: functionMetrics,
    screening: screening?.statistics ?? screening?.summary ?? {},
  };
}

function validateInventorySchema(inventory) {
  const version = inventory?.schema_version;
  if (typeof version !== "number") {
    throw new Error("CommandView inventory is missing schema_version.");
  }
  if (!SUPPORTED_INVENTORY_SCHEMA_VERSIONS.has(version)) {
    throw new Error(`Unsupported CommandView schema_version ${version}.`);
  }
}

function buildHierarchyMetadata(modules, functions, callGraph) {
  const rootBuckets = new Map();
  const domainBuckets = new Map();

  modules.forEach((moduleRecord) => {
    const root = deriveRootSegment(moduleRecord.moduleId);
    const domain = deriveDomainId(moduleRecord.moduleId);
    const moduleFunctions = moduleRecord.functions ?? [];

    const rootBucket = rootBuckets.get(root) ?? createHierarchyBucket(root, null);
    appendModuleData(rootBucket, moduleRecord.id, moduleFunctions);
    rootBuckets.set(root, rootBucket);

    const domainBucket = domainBuckets.get(domain) ?? createHierarchyBucket(domain, root);
    appendModuleData(domainBucket, moduleRecord.id, moduleFunctions);
    domainBuckets.set(domain, domainBucket);
  });

  const moduleNodes = Array.from(modules.values()).map((moduleRecord) => ({
    id: moduleRecord.id,
    moduleId: moduleRecord.moduleId,
    relativePath: moduleRecord.relativePath,
    packageName: moduleRecord.packageName,
    domainId: deriveDomainId(moduleRecord.moduleId),
    functionCount: moduleRecord.functions?.length ?? 0,
  }));

  const functionNodes = Array.from(functions.values()).map((functionRecord) => ({
    id: functionRecord.id,
    moduleId: functionRecord.moduleId,
    name: functionRecord.name,
    metrics: functionRecord.metrics,
  }));

  const neighborhood = new Map();
  const runtimeEdges = callGraph.functions ?? new Map();
  const screeningEdges = callGraph.screening ?? new Map();
  functions.forEach((_functionRecord, functionId) => {
    const adjacency = new Set();
    (runtimeEdges.get(functionId) ?? []).forEach((target) => adjacency.add(target));
    (screeningEdges.get(functionId) ?? []).forEach((target) => adjacency.add(target));
    neighborhood.set(functionId, Array.from(adjacency));
  });

  return {
    root: serializeHierarchyBuckets(rootBuckets),
    domain: serializeHierarchyBuckets(domainBuckets),
    module: moduleNodes.sort((a, b) => a.id.localeCompare(b.id)),
    function: functionNodes.sort((a, b) => a.id.localeCompare(b.id)),
    neighborhood,
  };
}

function createHierarchyBucket(id, parentId) {
  return {
    id,
    parentId,
    modules: new Set(),
    functions: new Set(),
  };
}

function appendModuleData(bucket, moduleId, functionIds) {
  bucket.modules.add(moduleId);
  functionIds.forEach((fnId) => bucket.functions.add(fnId));
}

function serializeHierarchyBuckets(buckets) {
  return Array.from(buckets.values())
    .map((bucket) => ({
      id: bucket.id,
      parentId: bucket.parentId,
      moduleCount: bucket.modules.size,
      functionCount: bucket.functions.size,
    }))
    .sort((a, b) => a.id.localeCompare(b.id));
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

function buildViewLevels(modules, functions, hierarchy, callGraph) {
  const level0 = buildRootLevel(hierarchy, functions, callGraph);
  const level1 = buildDomainLevel(hierarchy, functions, callGraph);
  const level2 = buildModuleLevel(modules, functions, callGraph);
  const level3 = buildFunctionLevelGraphs(modules, functions, callGraph);
  const level4 = buildNeighborhoodDetail(functions, hierarchy.neighborhood);
  return { level0, level1, level2, level3, level4 };
}

function buildRootLevel(hierarchy, functions, callGraph) {
  const nodes = hierarchy.root.map((bucket) => ({
    id: bucket.id,
    moduleCount: bucket.moduleCount,
    functionCount: bucket.functionCount,
  }));
  const edges = aggregateEdges(functions, callGraph, deriveRootSegment);
  return { nodes, edges };
}

function buildDomainLevel(hierarchy, functions, callGraph) {
  const nodes = hierarchy.domain.map((bucket) => ({
    id: bucket.id,
    parentId: bucket.parentId ?? null,
    moduleCount: bucket.moduleCount,
    functionCount: bucket.functionCount,
  }));
  const edges = aggregateEdges(functions, callGraph, deriveDomainId);
  return { nodes, edges };
}

function buildModuleLevel(modules, functions, callGraph) {
  const nodes = Array.from(modules.values())
    .map((moduleRecord) => ({
      id: moduleRecord.id,
      packageName: moduleRecord.packageName,
      functionCount: moduleRecord.functions?.length ?? 0,
      domainId: deriveDomainId(moduleRecord.moduleId),
      rootId: deriveRootSegment(moduleRecord.moduleId),
    }))
    .sort((a, b) => a.id.localeCompare(b.id));
  const edges = aggregateModuleEdges(functions, callGraph);
  return { nodes, edges };
}

function buildFunctionLevelGraphs(modules, functions, callGraph) {
  const moduleGraphs = new Map();
  const adjacency = callGraph.functions ?? new Map();
  modules.forEach((moduleRecord) => {
    const fnIds = moduleRecord.functions ?? [];
    const fnSet = new Set(fnIds);
    const nodes = fnIds
      .map((fnId) => functions.get(fnId))
      .filter(Boolean)
      .map((fn) => ({
        id: fn.id,
        name: fn.name,
        metrics: fn.metrics,
        complexity: fn.cyclomaticComplexity ?? null,
        coverage: fn.metrics?.coverage ?? null,
      }))
      .sort((a, b) => a.id.localeCompare(b.id));
    const edges = [];
    fnIds.forEach((fnId) => {
      const targets = adjacency.get(fnId) ?? [];
      targets.forEach((targetId) => {
        if (fnSet.has(targetId)) {
          edges.push({ source: fnId, target: targetId });
        }
      });
    });
    moduleGraphs.set(moduleRecord.id, { nodes, edges });
  });
  return moduleGraphs;
}

function buildNeighborhoodDetail(functions, neighborhood) {
  const detail = new Map();
  functions.forEach((functionRecord, functionId) => {
    const neighbors = neighborhood.get(functionId) ?? [];
    detail.set(functionId, {
      focus: {
        id: functionRecord.id,
        moduleId: functionRecord.moduleId,
        name: functionRecord.name,
        metrics: functionRecord.metrics,
        complexity: functionRecord.cyclomaticComplexity ?? null,
        coverage: functionRecord.metrics?.coverage ?? null,
      },
      neighbors: neighbors
        .map((neighborId) => functions.get(neighborId))
        .filter(Boolean)
        .map((fn) => ({
          id: fn.id,
          moduleId: fn.moduleId,
          name: fn.name,
          metrics: fn.metrics,
          complexity: fn.cyclomaticComplexity ?? null,
          coverage: fn.metrics?.coverage ?? null,
        })),
    });
  });
  return detail;
}

function aggregateEdges(functions, callGraph, groupingFn) {
  const moduleByFunction = new Map();
  functions.forEach((fn) => {
    moduleByFunction.set(fn.id, fn.moduleId);
  });
  const adjacency = callGraph.functions ?? new Map();
  const counts = new Map();
  adjacency.forEach((targets, sourceId) => {
    const sourceModule = moduleByFunction.get(sourceId);
    if (!sourceModule) {
      return;
    }
    const sourceGroup = groupingFn(sourceModule);
    targets.forEach((targetId) => {
      const targetModule = moduleByFunction.get(targetId);
      if (!targetModule) {
        return;
      }
      const targetGroup = groupingFn(targetModule);
      const key = `${sourceGroup}->${targetGroup}`;
      const count = counts.get(key) ?? 0;
      counts.set(key, count + 1);
    });
  });
  return Array.from(counts.entries()).map(([key, weight]) => {
    const [source, target] = key.split("->");
    return { source, target, weight };
  });
}

function aggregateModuleEdges(functions, callGraph) {
  const moduleByFunction = new Map();
  functions.forEach((fn) => {
    moduleByFunction.set(fn.id, fn.moduleId);
  });
  const adjacency = callGraph.functions ?? new Map();
  const counts = new Map();
  adjacency.forEach((targets, sourceId) => {
    const sourceModule = moduleByFunction.get(sourceId);
    if (!sourceModule) {
      return;
    }
    targets.forEach((targetId) => {
      const targetModule = moduleByFunction.get(targetId);
      if (!targetModule) {
        return;
      }
      const key = `${sourceModule}->${targetModule}`;
      const count = counts.get(key) ?? 0;
      counts.set(key, count + 1);
    });
  });
  return Array.from(counts.entries()).map(([key, weight]) => {
    const [source, target] = key.split("->");
    return { source, target, weight };
  });
}

function initializeLevelControls() {
  const buttonsContainer = document.getElementById("level-buttons");
  const sidebar = document.getElementById("level-sidebar");
  if (!buttonsContainer || !sidebar) {
    return;
  }

  levelUi.buttons.clear();
  buttonsContainer.innerHTML = "";

  LEVEL_DEFINITIONS.forEach((definition) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.level = definition.value;
    button.textContent = definition.label;
    button.addEventListener("click", () => {
      setLevel(definition.value);
    });
    levelUi.buttons.set(definition.value, button);
    buttonsContainer.appendChild(button);
  });

  levelUi.sidebar = sidebar;
  updateLevelButtonsState();
  renderLevelSidebar();
}

function updateLevelButtonsState() {
  levelUi.buttons.forEach((button, levelKey) => {
    const available = isLevelAvailable(levelKey);
    button.disabled = !available;
    button.classList.toggle("active", state.currentLevel === levelKey);
  });
}

function isLevelAvailable(levelKey) {
  if (!state.levels) {
    return false;
  }

  switch (levelKey) {
    case "level0":
    case "level1":
    case "level2": {
      const nodes = state.levels[levelKey]?.nodes ?? [];
      return Array.isArray(nodes) && nodes.length > 0;
    }
    case "level3":
      return state.levels.level3 instanceof Map && state.levels.level3.size > 0;
    case "level4":
      return state.levels.level4 instanceof Map && state.levels.level4.size > 0;
    default:
      return false;
  }
}

function ensureCurrentLevelIsAvailable() {
  if (isLevelAvailable(state.currentLevel)) {
    return;
  }
  const fallback = LEVEL_DEFINITIONS.find((definition) => isLevelAvailable(definition.value));
  state.currentLevel = fallback?.value ?? "level0";
}

function getLevelDefinition(levelKey) {
  return LEVEL_DEFINITIONS.find((definition) => definition.value === levelKey) ?? null;
}

function getLevelNodeCount(levelKey) {
  if (!state.levels) {
    return 0;
  }

  switch (levelKey) {
    case "level0":
    case "level1":
    case "level2": {
      const nodes = state.levels[levelKey]?.nodes ?? [];
      return Array.isArray(nodes) ? nodes.length : 0;
    }
    case "level3": {
      const moduleId = state.levelSelections.moduleId;
      const moduleGraphs = state.levels.level3 instanceof Map ? state.levels.level3 : null;
      const moduleGraph = moduleId && moduleGraphs ? moduleGraphs.get(moduleId) : null;
      const nodes = moduleGraph?.nodes ?? [];
      return Array.isArray(nodes) ? nodes.length : 0;
    }
    case "level4": {
      const functionId = state.levelSelections.functionId;
      const neighborhoods = state.levels.level4 instanceof Map ? state.levels.level4 : null;
      const detail = functionId && neighborhoods ? neighborhoods.get(functionId) : null;
      if (!detail) {
        return 0;
      }
      const neighbors = Array.isArray(detail.neighbors) ? detail.neighbors.length : 0;
      return 1 + neighbors;
    }
    default:
      return 0;
  }
}

function buildZoomSuggestion(levelKey, nodeCount) {
  if (!Number.isFinite(nodeCount) || nodeCount <= LEVEL_NODE_THRESHOLD) {
    return null;
  }

  switch (levelKey) {
    case "level0":
      return "Consider zooming to Level 1 to narrow the view.";
    case "level1":
      return "Consider zooming to Level 2 to explore modules.";
    case "level2":
      return "Consider zooming to Level 3 for function-level detail.";
    case "level3":
      return "Consider zooming to Level 4 to isolate a single function.";
    default:
      return null;
  }
}

function setLevel(levelKey) {
  if (!levelKey || !isLevelAvailable(levelKey)) {
    return;
  }

  if (Array.isArray(state.activeViews) && state.activeViews.length > 0) {
    clearActiveViewSelection({ suppressStatus: true });
  }

  if (state.currentLevel !== levelKey) {
    state.currentLevel = levelKey;
  }

  updateLevelButtonsState();
  renderLevelSidebar();
  renderBreadcrumb();
  void renderCurrentLevel();
}

function setLevelWithFallback(preferredLevel, fallbackLevels = []) {
  if (preferredLevel && isLevelAvailable(preferredLevel)) {
    setLevel(preferredLevel);
    return;
  }

  for (const levelKey of fallbackLevels) {
    if (isLevelAvailable(levelKey)) {
      setLevel(levelKey);
      return;
    }
  }

  ensureCurrentLevelIsAvailable();
  updateLevelButtonsState();
  renderLevelSidebar();
  renderBreadcrumb();
  void renderCurrentLevel();
}

function drillDownFromRoot(rootId) {
  if (!rootId) {
    return;
  }
  setRootSelection(rootId);
  setLevelWithFallback("level1", ["level2", "level3", "level4", "level0"]);
}

function drillDownFromDomain(domainId, parentId) {
  if (!domainId) {
    return;
  }
  if (parentId) {
    state.levelSelections.rootId = parentId;
  }
  setDomainSelection(domainId);
  setLevelWithFallback("level2", ["level3", "level4", "level1"]);
}

function drillDownFromModule(moduleId) {
  if (!moduleId) {
    return;
  }
  setModuleSelection(moduleId);
  setLevelWithFallback("level3", ["level4", "level2"]);
}

function drillDownFromFunction(functionId, moduleId) {
  if (!functionId) {
    return;
  }
  setFunctionSelection(functionId, moduleId);
  setLevelWithFallback("level4", ["level3"]);
}

function renderLevelSidebar() {
  if (!levelUi.sidebar) {
    levelUi.sidebar = document.getElementById("level-sidebar");
  }
  const sidebar = levelUi.sidebar;
  if (!sidebar) {
    return;
  }

  const options = collectSidebarEntries();
  sidebar.innerHTML = "";

  if (options.length === 0) {
    const item = document.createElement("li");
    item.classList.add("sidebar-empty");
    item.textContent = state.levels
      ? "This level has no data to display."
      : "Select a CommandView artifact to enable zoom levels.";
    sidebar.appendChild(item);
    return;
  }

  options.forEach((option) => {
    const item = document.createElement("li");
    if (option.message) {
      item.classList.add("sidebar-empty");
      item.textContent = option.message;
      sidebar.appendChild(item);
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.textContent = option.label;
    button.disabled = option.disabled ?? false;
    if (option.active) {
      button.classList.add("selected");
    }
    button.addEventListener("click", () => {
      applySidebarSelection(option.id);
    });
    item.appendChild(button);
    sidebar.appendChild(item);
  });
}

function initializeBreadcrumb() {
  breadcrumbUi.container = document.getElementById("breadcrumb");
  renderBreadcrumb();
}

function renderBreadcrumb() {
  if (!breadcrumbUi.container) {
    breadcrumbUi.container = document.getElementById("breadcrumb");
  }
  const container = breadcrumbUi.container;
  if (!container) {
    return;
  }

  const entries = collectBreadcrumbEntries();
  container.innerHTML = "";

  if (entries.length === 0) {
    const placeholder = document.createElement("span");
    placeholder.classList.add("breadcrumb-empty");
    placeholder.textContent = state.activeOption
      ? "Breadcrumb data unavailable for this selection."
      : "Select a CommandView artifact to begin.";
    container.appendChild(placeholder);
    return;
  }

  entries.forEach((entry, index) => {
    if (index > 0) {
      const separator = document.createElement("span");
      separator.classList.add("breadcrumb-separator");
      separator.textContent = ">";
      container.appendChild(separator);
    }

    if (entry.clickable) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = entry.label;
      button.addEventListener("click", () => {
        setLevel(entry.targetLevel);
      });
      container.appendChild(button);
      return;
    }

    const span = document.createElement("span");
    span.textContent = entry.label;
    if (entry.active) {
      span.classList.add("breadcrumb-current");
      span.setAttribute("aria-current", "page");
    } else {
      span.setAttribute("aria-current", "false");
    }
    container.appendChild(span);
  });
}

function collectBreadcrumbEntries() {
  if (!state.activeOption || !state.levels) {
    return [];
  }

  const entries = [];
  const currentLevel = state.currentLevel;

  const rootEntry = buildAggregateBreadcrumbEntry("level0", state.levelSelections.rootId, {
    active: currentLevel === "level0",
    targetLevel: "level0",
  });
  if (rootEntry) {
    entries.push(rootEntry);
  }

  if (state.levelSelections.domainId) {
    const domainEntry = buildAggregateBreadcrumbEntry("level1", state.levelSelections.domainId, {
      active: currentLevel === "level1",
      targetLevel: "level1",
    });
    if (domainEntry) {
      entries.push(domainEntry);
    }
  }

  const moduleEntry = buildModuleBreadcrumbEntry(state.levelSelections.moduleId, {
    active: currentLevel === "level2" || currentLevel === "level3",
  });
  if (moduleEntry) {
    entries.push(moduleEntry);
  }

  const functionEntry = buildFunctionBreadcrumbEntry(state.levelSelections.functionId, {
    active: currentLevel === "level4",
  });
  if (functionEntry) {
    entries.push(functionEntry);
  }

  return entries;
}

function buildAggregateBreadcrumbEntry(levelKey, nodeId, options) {
  const node = resolveAggregateNode(levelKey, nodeId);
  const label = formatBreadcrumbLabel(levelKey, node);
  if (!label) {
    return null;
  }

  const isAvailable = isLevelAvailable(levelKey);
  const active = options.active ?? false;
  const targetLevel = options.targetLevel ?? levelKey;

  return {
    label,
    targetLevel,
    active,
    clickable: isAvailable && !active,
  };
}

function buildModuleBreadcrumbEntry(moduleId, options) {
  if (!moduleId) {
    return null;
  }
  const node = resolveModuleNode(moduleId);
  const label = formatBreadcrumbLabel("level2", node);
  if (!label) {
    return null;
  }

  const targetLevel = isLevelAvailable("level3") ? "level3" : "level2";
  const active = options.active ?? false;

  const canNavigate = isLevelAvailable(targetLevel) && !active;
  return {
    label,
    targetLevel,
    active,
    clickable: canNavigate,
  };
}

function buildFunctionBreadcrumbEntry(functionId, options) {
  if (!functionId || !isLevelAvailable("level4")) {
    return null;
  }
  const record = resolveFunctionRecord(functionId);
  const label = formatBreadcrumbLabel("level4", record);
  if (!label) {
    return null;
  }

  const active = options.active ?? false;
  return {
    label,
    targetLevel: "level4",
    active,
    clickable: !active,
  };
}

function findMatchingOption(entries, previousOption) {
  if (!previousOption || !Array.isArray(entries)) {
    return null;
  }

  const relativePath = previousOption.relative_path ?? null;
  if (relativePath) {
    const matchByPath = findOptionByPredicate(entries, (option) => option.relative_path === relativePath);
    if (matchByPath) {
      return matchByPath;
    }
  }

  const slug = previousOption.slug ?? null;
  if (slug) {
    const matchBySlug = findOptionByPredicate(entries, (option) => option.slug === slug);
    if (matchBySlug) {
      return matchBySlug;
    }
  }

  return null;
}

function findOptionByPredicate(entries, predicate) {
  for (const entry of entries) {
    if (!entry || !Array.isArray(entry.options)) {
      continue;
    }
    for (const option of entry.options) {
      if (predicate(option ?? {})) {
        return option;
      }
    }
  }
  return null;
}

function resolveAggregateNode(levelKey, nodeId) {
  if (!state.levels || !nodeId) {
    return null;
  }
  const nodes = state.levels[levelKey]?.nodes ?? [];
  if (!Array.isArray(nodes)) {
    return null;
  }
  return nodes.find((node) => node.id === nodeId) ?? null;
}

function resolveModuleNode(moduleId) {
  if (!state.levels || !moduleId) {
    return null;
  }
  const nodes = state.levels.level2?.nodes ?? [];
  if (!Array.isArray(nodes)) {
    return null;
  }
  return nodes.find((node) => node.id === moduleId) ?? null;
}

function resolveFunctionRecord(functionId) {
  if (!state.normalizedData || !functionId) {
    return null;
  }
  const functionsMap = state.normalizedData.functions;
  if (functionsMap instanceof Map) {
    return functionsMap.get(functionId) ?? null;
  }
  return null;
}

function formatBreadcrumbLabel(levelKey, node) {
  if (!node) {
    switch (levelKey) {
      case "level0":
        return "Overview";
      case "level1":
        return "Domain";
      case "level2":
      case "level3":
        return "Module";
      case "level4":
        return "Function";
      default:
        return null;
    }
  }

  switch (levelKey) {
    case "level0":
    case "level1":
      return node.id ?? null;
    case "level2":
    case "level3":
      return node.id ?? null;
    case "level4":
      return node.name ?? node.id ?? null;
    default:
      return null;
  }
}

function collectSidebarEntries() {
  if (!state.levels) {
    return [];
  }

  switch (state.currentLevel) {
    case "level0": {
      const nodes = state.levels.level0?.nodes ?? [];
      return nodes.map((node) => ({
        id: node.id,
        label: formatAggregateLabel(node),
        active: state.levelSelections.rootId === node.id,
      }));
    }
    case "level1": {
      const nodes = state.levels.level1?.nodes ?? [];
      return nodes.map((node) => ({
        id: node.id,
        label: formatAggregateLabel(node),
        active: state.levelSelections.domainId === node.id,
      }));
    }
    case "level2": {
      const nodes = state.levels.level2?.nodes ?? [];
      return nodes.map((node) => ({
        id: node.id,
        label: formatModuleLabel(node),
        active: state.levelSelections.moduleId === node.id,
      }));
    }
    case "level3": {
      const nodes = state.levels.level2?.nodes ?? [];
      if (!Array.isArray(nodes) || nodes.length === 0) {
        return [{ message: "No modules recorded in this CommandView payload." }];
      }
      return nodes.map((node) => ({
        id: node.id,
        label: formatModuleLabel(node),
        active: state.levelSelections.moduleId === node.id,
      }));
    }
    case "level4": {
      const moduleId = state.levelSelections.moduleId;
      if (!moduleId) {
        return [{ message: "Select a module at Level 3 to inspect function neighborhoods." }];
      }
      const moduleGraphs = state.levels.level3 instanceof Map ? state.levels.level3 : null;
      const moduleGraph = moduleGraphs?.get(moduleId) ?? null;
      const nodes = moduleGraph?.nodes ?? [];
      if (!Array.isArray(nodes) || nodes.length === 0) {
        return [{ message: "Selected module has no functions recorded." }];
      }
      return nodes.map((node) => ({
        id: node.id,
        label: formatFunctionSidebarLabel(node),
        active: state.levelSelections.functionId === node.id,
      }));
    }
    default:
      return [];
  }
}

function formatAggregateLabel(node) {
  const modules = typeof node.moduleCount === "number" ? node.moduleCount : 0;
  const functions = typeof node.functionCount === "number" ? node.functionCount : 0;
  return `${node.id}\n${modules} modules, ${functions} functions`;
}

function formatModuleLabel(node) {
  const functions = typeof node.functionCount === "number" ? node.functionCount : 0;
  return `${node.id}\n${functions} functions`;
}

function formatFunctionSidebarLabel(node) {
  const parts = [node.name ?? node.id];
  const metrics = node.metrics ?? {};
  if (typeof metrics.lineCount === "number") {
    parts.push(`LOC ${metrics.lineCount}`);
  }
  if (typeof metrics.coverage === "number") {
    parts.push(`Cov ${formatCoveragePercent(metrics.coverage)}`);
  }
  return parts.join(" | ");
}

function applySidebarSelection(targetId) {
  if (!targetId) {
    return;
  }

  const changed = setLevelSelectionValue(state.currentLevel, targetId);
  if (!changed) {
    return;
  }

  synchronizeSelections();
  renderLevelSidebar();
  renderBreadcrumb();
  void renderCurrentLevel();
}

function getSelectionKeyForLevel(levelKey) {
  switch (levelKey) {
    case "level0":
      return "rootId";
    case "level1":
      return "domainId";
    case "level2":
    case "level3":
      return "moduleId";
    case "level4":
      return "functionId";
    default:
      return null;
  }
}

function setLevelSelectionValue(levelKey, targetId) {
  const selectionKey = getSelectionKeyForLevel(levelKey);
  if (!selectionKey) {
    return false;
  }

  if (state.levelSelections[selectionKey] === targetId) {
    return false;
  }

  state.levelSelections[selectionKey] = targetId;
  return true;
}

function synchronizeSelections() {
  if (!state.levels) {
    state.levelSelections.rootId = null;
    state.levelSelections.domainId = null;
    state.levelSelections.moduleId = null;
    state.levelSelections.functionId = null;
    return;
  }

  const level0Ids = (state.levels.level0?.nodes ?? []).map((node) => node.id);
  const level1Ids = (state.levels.level1?.nodes ?? []).map((node) => node.id);
  const moduleIds = (state.levels.level2?.nodes ?? []).map((node) => node.id);

  state.levelSelections.rootId = ensureSelectionInSet(state.levelSelections.rootId, level0Ids);
  state.levelSelections.domainId = ensureSelectionInSet(state.levelSelections.domainId, level1Ids);
  ensureDomainSelectionForRoot(state.levelSelections.rootId);
  state.levelSelections.moduleId = ensureSelectionInSet(state.levelSelections.moduleId, moduleIds);
  ensureModuleSelectionForDomain(state.levelSelections.domainId);

  ensureFunctionSelection();
}

function ensureFunctionSelection() {
  const moduleId = state.levelSelections.moduleId;
  const moduleGraphs = state.levels?.level3 instanceof Map ? state.levels.level3 : null;
  const moduleGraph = moduleId && moduleGraphs ? moduleGraphs.get(moduleId) : null;
  const functionIds = moduleGraph?.nodes?.map((node) => node.id) ?? [];
  state.levelSelections.functionId = ensureSelectionInSet(state.levelSelections.functionId, functionIds);
}

function ensureSelectionInSet(currentId, candidates) {
  if (!Array.isArray(candidates) || candidates.length === 0) {
    return null;
  }
  if (currentId && candidates.includes(currentId)) {
    return currentId;
  }
  return candidates[0];
}

function ensureDomainSelectionForRoot(rootId) {
  const domainNodes = Array.isArray(state.levels?.level1?.nodes) ? state.levels.level1.nodes : [];
  if (domainNodes.length === 0) {
    state.levelSelections.domainId = null;
    return;
  }

  const matching = typeof rootId === "string"
    ? domainNodes.filter((node) => node.parentId === rootId)
    : domainNodes;

  if (matching.length === 0) {
    if (!domainNodes.some((node) => node.id === state.levelSelections.domainId)) {
      state.levelSelections.domainId = domainNodes[0].id;
    }
    return;
  }

  if (!matching.some((node) => node.id === state.levelSelections.domainId)) {
    state.levelSelections.domainId = matching[0].id;
  }
}

function ensureModuleSelectionForDomain(domainId) {
  const moduleNodes = Array.isArray(state.levels?.level2?.nodes) ? state.levels.level2.nodes : [];
  if (moduleNodes.length === 0) {
    state.levelSelections.moduleId = null;
    return;
  }

  const matching = typeof domainId === "string"
    ? moduleNodes.filter((node) => node.domainId === domainId)
    : moduleNodes;

  if (matching.length === 0) {
    if (!moduleNodes.some((node) => node.id === state.levelSelections.moduleId)) {
      state.levelSelections.moduleId = moduleNodes[0].id;
    }
    return;
  }

  if (!matching.some((node) => node.id === state.levelSelections.moduleId)) {
    state.levelSelections.moduleId = matching[0].id;
  }
}

function getDomainNodeById(domainId) {
  if (!domainId || !Array.isArray(state.levels?.level1?.nodes)) {
    return null;
  }
  return state.levels.level1.nodes.find((node) => node.id === domainId) ?? null;
}

function getModuleNodeById(moduleId) {
  if (!moduleId || !Array.isArray(state.levels?.level2?.nodes)) {
    return null;
  }
  return state.levels.level2.nodes.find((node) => node.id === moduleId) ?? null;
}

function setRootSelection(rootId) {
  if (!rootId) {
    return;
  }
  state.levelSelections.rootId = rootId;
  ensureDomainSelectionForRoot(rootId);
  ensureModuleSelectionForDomain(state.levelSelections.domainId);
  ensureFunctionSelection();
}

function setDomainSelection(domainId) {
  if (!domainId) {
    return;
  }
  const domainNode = getDomainNodeById(domainId);
  if (domainNode?.parentId) {
    state.levelSelections.rootId = domainNode.parentId;
  }
  state.levelSelections.domainId = domainId;
  ensureDomainSelectionForRoot(state.levelSelections.rootId);
  ensureModuleSelectionForDomain(state.levelSelections.domainId);
  ensureFunctionSelection();
}

function setModuleSelection(moduleId) {
  if (!moduleId) {
    return;
  }
  const moduleNode = getModuleNodeById(moduleId);
  if (moduleNode?.rootId) {
    state.levelSelections.rootId = moduleNode.rootId;
  }
  if (moduleNode?.domainId) {
    state.levelSelections.domainId = moduleNode.domainId;
  }
  ensureDomainSelectionForRoot(state.levelSelections.rootId);
  state.levelSelections.moduleId = moduleId;
  ensureModuleSelectionForDomain(state.levelSelections.domainId);
  ensureFunctionSelection();
}

function setFunctionSelection(functionId, moduleId) {
  if (moduleId) {
    setModuleSelection(moduleId);
  }
  if (functionId) {
    state.levelSelections.functionId = functionId;
  }
  ensureFunctionSelection();
}

function buildMermaidDefinition(levelKey) {
  if (!state.levels) {
    return null;
  }

  switch (levelKey) {
    case "level0":
      return buildAggregateMermaid(
        state.levels.level0,
        (node) => formatAggregateLabel(node),
        (node, sanitizedId) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromRoot(node.id);
          });
        },
        (node, sanitizedId) => buildAggregateNodeStyle("level0", node, sanitizedId),
        (edge, source, target, label) => formatDottedEdge(edge, source, target, label)
      );
    case "level1":
      return buildAggregateMermaid(
        state.levels.level1,
        (node) => formatAggregateLabel(node),
        (node, sanitizedId) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromDomain(node.id, node.parentId ?? null);
          });
        },
        (node, sanitizedId) => buildAggregateNodeStyle("level1", node, sanitizedId),
        (edge, source, target, label) => formatDottedEdge(edge, source, target, label)
      );
    case "level2":
      return buildAggregateMermaid(
        state.levels.level2,
        (node) => formatModuleLabel(node),
        (node, sanitizedId) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromModule(node.id);
          });
        },
        (node, sanitizedId) => buildAggregateNodeStyle("level2", node, sanitizedId)
      );
    case "level3": {
      const moduleId = state.levelSelections.moduleId;
      const moduleGraphs = state.levels.level3 instanceof Map ? state.levels.level3 : null;
      const moduleGraph = moduleId && moduleGraphs ? moduleGraphs.get(moduleId) : null;
      if (!moduleId || !moduleGraph) {
        return null;
      }
      return buildModuleFunctionsMermaid(
        moduleId,
        moduleGraph,
        (node, sanitizedId) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromFunction(node.id, moduleId);
          });
        },
        (node, sanitizedId, isFocus) => buildFunctionNodeStyle(node, sanitizedId, isFocus)
      );
    }
    case "level4": {
      const functionId = state.levelSelections.functionId;
      const neighborhoods = state.levels.level4 instanceof Map ? state.levels.level4 : null;
      const detail = functionId && neighborhoods ? neighborhoods.get(functionId) : null;
      if (!detail) {
        return null;
      }
      return buildFunctionNeighborhoodMermaid(
        detail,
        (node, sanitizedId, isFocus) => {
          registerRenderInteraction(sanitizedId, () => {
            drillDownFromFunction(node.id, node.moduleId ?? null);
          });
        },
        (node, sanitizedId, isFocus) => buildFunctionNodeStyle(node, sanitizedId, isFocus)
      );
    }
    default:
      return null;
  }
}

function buildExportContractMatrixViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const isScopedSelection = Boolean(moduleId || domainId || rootId);

  // Filter modules based on current zoom level selection
  let filteredModules = new Map();
  let scopeDescription = "repository";

  if (moduleId) {
    // Level 2+: Show only the selected module
    const moduleData = modules.get(moduleId);
    if (moduleData) {
      filteredModules.set(moduleId, moduleData);
      scopeDescription = moduleId;
    }
  } else if (domainId) {
    // Level 1: Show modules in the selected domain
    for (const [modId, modData] of modules.entries()) {
      if (modId.startsWith(domainId) || modId.includes(domainId)) {
        filteredModules.set(modId, modData);
      }
    }
    scopeDescription = domainId;
  } else if (rootId) {
    // Level 0: Show modules in the selected root
    for (const [modId, modData] of modules.entries()) {
      if (modId.startsWith(rootId) || modId.includes(rootId)) {
        filteredModules.set(modId, modData);
      }
    }
    scopeDescription = rootId;
  }
  
  // Fallback: if filtering resulted in no modules, show all modules
  if (filteredModules.size === 0) {
    filteredModules = modules;
    scopeDescription = "repository";
  }

  let result = buildExportContractMatrixDiagram(filteredModules, {
    viewLabel: "Dependency · Export Contract Matrix",
    rootId,
    domainId,
    moduleId,
    scopeDescription,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Export Contract Matrix diagram." };
  }

  if (result.message && isScopedSelection && scopeDescription !== "repository") {
    const fallbackNotice = `No export contracts recorded for "${scopeDescription}". Showing repository-wide matrix instead.`;
    const fallbackResult = buildExportContractMatrixDiagram(modules, {
      viewLabel: "Dependency · Export Contract Matrix",
      rootId: null,
      domainId: null,
      moduleId: null,
      scopeDescription: "repository",
      fallbackNotice,
    });
    if (fallbackResult && !fallbackResult.message) {
      result = fallbackResult;
    }
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
  };
}

function buildCircularImportDetectionViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const isScopedSelection = Boolean(moduleId || domainId || rootId);
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;

  let filteredModules = new Map();
  let scopeDescription = "repository";
  let fallbackNotice = null;

  if (moduleId) {
    const moduleRecord = modules.get(moduleId);
    if (moduleRecord) {
      filteredModules.set(moduleId, moduleRecord);
      scopeDescription = moduleId;
    }
  } else if (domainId) {
    modules.forEach((record, identifier) => {
      if (identifier.startsWith(domainId) || identifier.includes(domainId)) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = domainId;
  } else if (rootId) {
    modules.forEach((record, identifier) => {
      if (identifier.startsWith(rootId) || identifier.includes(rootId)) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = rootId;
  }

  if (filteredModules.size === 0) {
    filteredModules = modules;
    scopeDescription = "repository";
  }

  let result = buildCircularImportDetectionDiagram(filteredModules, {
    viewLabel: "Dependency · Circular Import Detection",
    scopeDescription,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Circular Import Detection diagram." };
  }

  if (result.message && isScopedSelection && scopeDescription !== "repository") {
    const fallbackNotice = `No circular imports detected for "${scopeDescription}". Showing repository cycles instead.`;
    const fallbackResult = buildCircularImportDetectionDiagram(modules, {
      viewLabel: "Dependency · Circular Import Detection",
      scopeDescription: "repository",
      fallbackNotice,
    });
    if (fallbackResult && !fallbackResult.message) {
      result = fallbackResult;
    }
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildModuleDependencyGraphViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const filteredModules = modules;

  const dependencySummaries = new Map();
  filteredModules.forEach((moduleRecord, moduleId) => {
    if (moduleRecord?.dependencySummary && typeof moduleRecord.dependencySummary === "object") {
      dependencySummaries.set(moduleId, moduleRecord.dependencySummary);
    }
  });

  const result = buildModuleDependencyGraphDiagram(filteredModules, {
    viewLabel: "Dependency · Module Dependency Graph",
    rootId,
    domainId,
    dependencySummaries,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Module Dependency Graph diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
  };
}

function buildLayerArchitectureValidationViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const isScopedSelection = Boolean(moduleId || domainId || rootId);
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;

  let filteredModules = new Map();
  let scopeDescription = "repository";
  let fallbackNotice = null;

  if (moduleId) {
    const moduleRecord = modules.get(moduleId);
    if (moduleRecord) {
      filteredModules.set(moduleId, moduleRecord);
      scopeDescription = moduleId;
    }
  } else if (domainId) {
    modules.forEach((record, identifier) => {
      if (identifier.startsWith(domainId) || identifier.includes(domainId)) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = domainId;
  } else if (rootId) {
    modules.forEach((record, identifier) => {
      if (identifier.startsWith(rootId) || identifier.includes(rootId)) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = rootId;
  }

  if (filteredModules.size === 0) {
    filteredModules = modules;
    scopeDescription = "repository";
    if (isScopedSelection && selectionLabel) {
      fallbackNotice = `No layer-classified modules recorded for "${selectionLabel}". Showing repository adjacency validation instead.`;
    } else if (isScopedSelection) {
      fallbackNotice = "No layer-classified modules recorded for the current selection. Showing repository adjacency validation instead.";
    }
  }

  let result = buildLayerArchitectureValidationDiagram(filteredModules, {
    viewLabel: "Dependency · Layer Architecture Validation",
    rootId,
    domainId,
    moduleId,
    scopeDescription,
    evaluateLayerTransition,
    fallbackNotice,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Layer Architecture Validation diagram." };
  }

  if (result.message && isScopedSelection && scopeDescription !== "repository") {
    const fallbackMessage = fallbackNotice
      ?? (selectionLabel
        ? `No layer-classified modules recorded for "${selectionLabel}". Showing repository adjacency validation instead.`
        : "No layer-classified modules recorded for the current selection. Showing repository adjacency validation instead.");
    const fallbackResult = buildLayerArchitectureValidationDiagram(modules, {
      viewLabel: "Dependency · Layer Architecture Validation",
      rootId: null,
      domainId: null,
      moduleId: null,
      scopeDescription: "repository",
      evaluateLayerTransition,
      fallbackNotice: fallbackMessage,
    });
    if (fallbackResult && !fallbackResult.message) {
      result = fallbackResult;
    }
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildExternalVsInternalDependencyMapViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const isScopedSelection = Boolean(moduleId || domainId || rootId);
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;

  let filteredModules = new Map();
  let scopeDescription = "repository";
  let fallbackNotice = null;

  if (moduleId) {
    const moduleRecord = modules.get(moduleId);
    if (moduleRecord) {
      filteredModules.set(moduleId, moduleRecord);
      scopeDescription = moduleId;
    }
  } else if (domainId) {
    modules.forEach((record, identifier) => {
      if (identifier.startsWith(domainId) || identifier.includes(domainId)) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = domainId;
  } else if (rootId) {
    modules.forEach((record, identifier) => {
      if (identifier.startsWith(rootId) || identifier.includes(rootId)) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = rootId;
  } else {
    filteredModules = modules;
  }

  if (filteredModules.size === 0) {
    filteredModules = modules;
    scopeDescription = "repository";
    if (isScopedSelection) {
      fallbackNotice = selectionLabel
        ? `No dependency mix metadata recorded for "${selectionLabel}". Showing repository map instead.`
        : "No dependency mix metadata recorded for the current selection. Showing repository map instead.";
    }
  }

  const usingRepositoryScope = filteredModules === modules;

  let result = buildExternalVsInternalDependencyMapDiagram(filteredModules, {
    viewLabel: "Dependency · External vs Internal Dependency Map",
    rootId: usingRepositoryScope ? null : rootId,
    domainId: usingRepositoryScope ? null : domainId,
    moduleId: usingRepositoryScope ? null : moduleId,
    scopeDescription,
    fallbackNotice,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build External vs Internal Dependency Map diagram." };
  }

  if (result.message && isScopedSelection && !usingRepositoryScope) {
    const repositoryFallbackNotice = selectionLabel
      ? `No dependency mix metadata recorded for "${selectionLabel}". Showing repository map instead.`
      : "No dependency mix metadata recorded for the current selection. Showing repository map instead.";
    const fallbackResult = buildExternalVsInternalDependencyMapDiagram(modules, {
      viewLabel: "Dependency · External vs Internal Dependency Map",
      rootId: null,
      domainId: null,
      moduleId: null,
      scopeDescription: "repository",
      fallbackNotice: repositoryFallbackNotice,
    });
    if (fallbackResult && !fallbackResult.message) {
      result = fallbackResult;
    }
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildDynamicCodeWatchlistViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const repositoryHasDynamic = hasDynamicCodeData(modules);

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const isScopedSelection = Boolean(selectionLabel);

  let filteredModules = new Map();
  let scopeDescription = "repository";
  let fallbackNotice = null;

  if (moduleId) {
    const moduleRecord = modules.get(moduleId);
    if (moduleRecord) {
      filteredModules.set(moduleId, moduleRecord);
      scopeDescription = moduleId;
    }
  } else if (domainId) {
    modules.forEach((record, identifier) => {
      if (typeof identifier === "string" && (identifier.startsWith(domainId) || identifier.includes(domainId))) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = domainId;
  } else if (rootId) {
    modules.forEach((record, identifier) => {
      if (typeof identifier === "string" && (identifier.startsWith(rootId) || identifier.includes(rootId))) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = rootId;
  } else {
    filteredModules = modules;
  }

  const scopedHasDynamic = hasDynamicCodeData(filteredModules);
  if (!scopedHasDynamic) {
    filteredModules = modules;
    scopeDescription = "repository";
    if (isScopedSelection && repositoryHasDynamic) {
      fallbackNotice = selectionLabel
        ? `No dynamic code signals recorded for "${selectionLabel}". Showing repository watchlist instead.`
        : "No dynamic code signals recorded for the current selection. Showing repository watchlist instead.";
    }
  }

  let result = buildDynamicCodeWatchlistDiagram(filteredModules, {
    viewLabel: "Event Dynamics · Dynamic Code Watchlist",
    scopeDescription,
    fallbackNotice,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Dynamic Code Watchlist diagram." };
  }

  if (result.message && isScopedSelection && repositoryHasDynamic) {
    const fallbackResult = buildDynamicCodeWatchlistDiagram(modules, {
      viewLabel: "Event Dynamics · Dynamic Code Watchlist",
      scopeDescription: "repository",
      fallbackNotice: selectionLabel
        ? `No dynamic code signals recorded for "${selectionLabel}". Showing repository watchlist instead.`
        : "No dynamic code signals recorded for the current selection. Showing repository watchlist instead.",
    });
    if (fallbackResult && !fallbackResult.message) {
      result = fallbackResult;
    }
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildCallbackRegistrationMapViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const repositoryHasCallbacks = hasCallbackRegistrationData(modules);

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const isScopedSelection = Boolean(selectionLabel);

  let filteredModules = new Map();
  let scopeDescription = "repository";
  let fallbackNotice = null;

  if (moduleId) {
    const moduleRecord = modules.get(moduleId);
    if (moduleRecord) {
      filteredModules.set(moduleId, moduleRecord);
      scopeDescription = moduleId;
    }
  } else if (domainId) {
    modules.forEach((record, identifier) => {
      if (typeof identifier === "string" && (identifier.startsWith(domainId) || identifier.includes(domainId))) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = domainId;
  } else if (rootId) {
    modules.forEach((record, identifier) => {
      if (typeof identifier === "string" && (identifier.startsWith(rootId) || identifier.includes(rootId))) {
        filteredModules.set(identifier, record);
      }
    });
    scopeDescription = rootId;
  } else {
    filteredModules = modules;
  }

  const scopedHasCallbacks = hasCallbackRegistrationData(filteredModules);
  if (!scopedHasCallbacks) {
    filteredModules = modules;
    scopeDescription = "repository";
    if (isScopedSelection && repositoryHasCallbacks) {
      fallbackNotice = selectionLabel
        ? `No callback registrations recorded for "${selectionLabel}". Showing repository map instead.`
        : "No callback registrations recorded for the current selection. Showing repository map instead.";
    }
  }

  let result = buildCallbackRegistrationMapDiagram(filteredModules, {
    viewLabel: "Event Dynamics · Callback Registration Map",
    scopeDescription,
    fallbackNotice,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Callback Registration Map diagram." };
  }

  if (result.message && isScopedSelection && repositoryHasCallbacks) {
    const fallbackResult = buildCallbackRegistrationMapDiagram(modules, {
      viewLabel: "Event Dynamics · Callback Registration Map",
      scopeDescription: "repository",
      fallbackNotice: selectionLabel
        ? `No callback registrations recorded for "${selectionLabel}". Showing repository map instead.`
        : "No callback registrations recorded for the current selection. Showing repository map instead.",
    });
    if (fallbackResult && !fallbackResult.message) {
      result = fallbackResult;
    }
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function hasCallbackRegistrationData(candidate) {
  const modules = candidate instanceof Map ? candidate : candidate ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return false;
  }
  for (const record of modules.values()) {
    if (Array.isArray(record?.callbackRegistrations) && record.callbackRegistrations.length > 0) {
      return true;
    }
  }
  return false;
}

function hasDynamicCodeData(candidate) {
  const modules = candidate instanceof Map ? candidate : candidate ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return false;
  }
  for (const record of modules.values()) {
    if (record?.dynamicCode?.hasDynamic === true) {
      return true;
    }
  }
  return false;
}

function buildFunctionCallGraphViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modules = normalized.modules instanceof Map ? normalized.modules : normalized.modules ?? null;
  const functionsMap = normalized.functions instanceof Map ? normalized.functions : normalized.functions ?? null;
  const callGraph = normalized.callGraph?.functions instanceof Map
    ? normalized.callGraph.functions
    : normalized.callGraph?.functions ?? null;

  const result = buildFunctionCallGraphDiagram(modules, functionsMap, callGraph, {
    moduleId: state.levelSelections.moduleId,
    focusFunctionId: state.levelSelections.functionId,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Function Call Graph diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label ?? `${result.moduleId ?? "Module"} · Function Call Graph`,
    statusMessage: result.statusMessage,
  };
}

function buildCrossModuleFunctionReferencesViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const functionsValue = normalized.functions;
  const functionsMap = functionsValue instanceof Map ? functionsValue : functionsValue ?? null;
  if (!(functionsMap instanceof Map) || functionsMap.size === 0) {
    return { message: "Function metadata has not been normalized for this CommandView artifact." };
  }

  const callGraphValue = normalized.callGraph?.functions;
  const callGraph = callGraphValue instanceof Map ? callGraphValue : callGraphValue ?? null;
  if (!(callGraph instanceof Map) || callGraph.size === 0) {
    return { message: "Call graph data is not available in this CommandView artifact." };
  }

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const hasScopedSelection = Boolean(selectionLabel);

  const focusModules = new Set();
  let selectionMatched = false;
  let scopeDescription = "repository";

  if (moduleId && modules.has(moduleId)) {
    focusModules.add(moduleId);
    selectionMatched = true;
    scopeDescription = moduleId;
  } else if (domainId) {
    modules.forEach((_record, identifier) => {
      if (identifier.startsWith(domainId) || identifier.includes(`${domainId}.`)) {
        focusModules.add(identifier);
        selectionMatched = true;
      }
    });
    if (selectionMatched) {
      scopeDescription = domainId;
    }
  } else if (rootId) {
    modules.forEach((_record, identifier) => {
      if (identifier.startsWith(rootId) || identifier.includes(`${rootId}.`)) {
        focusModules.add(identifier);
        selectionMatched = true;
      }
    });
    if (selectionMatched) {
      scopeDescription = rootId;
    }
  }

  const initialOptions = {
    viewLabel: "Coupling Insight · Cross-Module Function References",
    scopeDescription: selectionMatched ? scopeDescription : "repository",
  };

  if (selectionMatched) {
    initialOptions.focusModules = Array.from(focusModules);
  } else if (hasScopedSelection) {
    initialOptions.fallbackNotice = selectionLabel
      ? `No modules matched selection "${selectionLabel}". Showing repository coupling instead.`
      : "No modules matched the current selection. Showing repository coupling instead.";
  }

  let result = buildCrossModuleFunctionReferencesDiagram(modules, functionsMap, callGraph, initialOptions);

  if (result && result.message && selectionMatched) {
    const fallbackNotice = selectionLabel
      ? `No cross-module references recorded for "${selectionLabel}". Showing repository coupling instead.`
      : "No cross-module references recorded for the current selection. Showing repository coupling instead.";
    const fallbackResult = buildCrossModuleFunctionReferencesDiagram(modules, functionsMap, callGraph, {
      viewLabel: "Coupling Insight · Cross-Module Function References",
      scopeDescription: "repository",
      fallbackNotice,
    });
    if (fallbackResult && !fallbackResult.message) {
      result = fallbackResult;
    }
  }

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Cross-Module Function References diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildImportChainDepthViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const hasScopedSelection = Boolean(selectionLabel);

  const focusModules = new Set();
  let selectionMatched = false;
  let scopeDescription = "repository";

  if (moduleId && modules.has(moduleId)) {
    focusModules.add(moduleId);
    selectionMatched = true;
    scopeDescription = moduleId;
  } else if (domainId) {
    modules.forEach((_record, identifier) => {
      if (identifier.startsWith(domainId) || identifier.includes(`${domainId}.`)) {
        focusModules.add(identifier);
        selectionMatched = true;
      }
    });
    if (selectionMatched) {
      scopeDescription = domainId;
    }
  } else if (rootId) {
    modules.forEach((_record, identifier) => {
      if (identifier.startsWith(rootId) || identifier.includes(`${rootId}.`)) {
        focusModules.add(identifier);
        selectionMatched = true;
      }
    });
    if (selectionMatched) {
      scopeDescription = rootId;
    }
  }

  const initialOptions = {
    viewLabel: "Coupling Insight · Import Chain Depth",
    scopeDescription: selectionMatched ? scopeDescription : "repository",
  };

  if (selectionMatched) {
    initialOptions.focusModules = Array.from(focusModules);
  } else if (hasScopedSelection) {
    initialOptions.fallbackNotice = selectionLabel
      ? `No modules matched selection "${selectionLabel}". Showing repository import chains instead.`
      : "No modules matched the current selection. Showing repository import chains instead.";
  }

  let result = buildImportChainDepthDiagram(modules, initialOptions);

  if (result && result.message && selectionMatched) {
    const fallbackNotice = selectionLabel
      ? `No import chains recorded for "${selectionLabel}". Showing repository import chains instead.`
      : "No import chains recorded for the current selection. Showing repository import chains instead.";
    const fallbackResult = buildImportChainDepthDiagram(modules, {
      viewLabel: "Coupling Insight · Import Chain Depth",
      scopeDescription: "repository",
      fallbackNotice,
    });
    if (fallbackResult && !fallbackResult.message) {
      result = fallbackResult;
    }
  }

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Import Chain Depth diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildEntrypointTraceDiagramViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const functionsValue = normalized.functions;
  const functionsMap = functionsValue instanceof Map ? functionsValue : functionsValue ?? null;
  if (!(functionsMap instanceof Map) || functionsMap.size === 0) {
    return { message: "Function metadata has not been normalized for this CommandView artifact." };
  }

  const callGraphValue = normalized.callGraph?.functions;
  const callGraph = callGraphValue instanceof Map ? callGraphValue : callGraphValue ?? null;
  if (!(callGraph instanceof Map) || callGraph.size === 0) {
    return { message: "Call graph data is not available in this CommandView artifact." };
  }

  const entrypointsValue = normalized.entrypoints;
  const entrypointMap = entrypointsValue instanceof Map ? entrypointsValue : entrypointsValue ?? null;
  if (!(entrypointMap instanceof Map) || entrypointMap.size === 0) {
    return { message: "Entrypoint candidates were not detected in this CommandView artifact." };
  }

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const isScopedSelection = Boolean(selectionLabel);

  const scopedModuleIds = new Set();
  let scopeDescription = "repository";
  let selectionMatched = false;

  if (moduleId) {
    if (modules.has(moduleId)) {
      scopedModuleIds.add(moduleId);
      scopeDescription = moduleId;
      selectionMatched = true;
    }
  } else if (domainId) {
    modules.forEach((record, identifier) => {
      if (identifier.startsWith(domainId) || identifier.includes(`${domainId}.`)) {
        scopedModuleIds.add(identifier);
        selectionMatched = true;
      }
    });
    if (selectionMatched) {
      scopeDescription = domainId;
    }
  } else if (rootId) {
    modules.forEach((record, identifier) => {
      if (identifier.startsWith(rootId) || identifier.includes(`${rootId}.`)) {
        scopedModuleIds.add(identifier);
        selectionMatched = true;
      }
    });
    if (selectionMatched) {
      scopeDescription = rootId;
    }
  }

  if (!selectionMatched) {
    modules.forEach((_, identifier) => {
      scopedModuleIds.add(identifier);
    });
    scopeDescription = "repository";
  }

  const scopedEntrypoints = new Map();
  entrypointMap.forEach((value, identifier) => {
    if (scopedModuleIds.has(identifier)) {
      scopedEntrypoints.set(identifier, value);
    }
  });

  let fallbackNotice = null;
  let targetEntrypoints = scopedEntrypoints;
  let targetScopeDescription = scopeDescription;

  if (targetEntrypoints.size === 0) {
    if (!isScopedSelection) {
      return { message: "Entrypoint candidates were not detected in this CommandView artifact." };
    }

    if (entrypointMap.size === 0) {
      return { message: "Entrypoint candidates were not detected in this CommandView artifact." };
    }

    targetEntrypoints = entrypointMap;
    targetScopeDescription = "repository";
    const fallbackLabel = selectionLabel ?? scopeDescription;
    fallbackNotice = fallbackLabel
      ? `No entrypoint candidates recorded for "${fallbackLabel}". Showing repository candidates instead.`
      : "No entrypoint candidates recorded for the current selection. Showing repository candidates instead.";
  }

  const moduleIds = Array.from(targetEntrypoints.keys());

  const result = buildEntrypointTraceDiagram(modules, functionsMap, callGraph, targetEntrypoints, {
    viewLabel: "Code Flow · Entrypoint Trace",
    scopeDescription: targetScopeDescription,
    moduleIds,
    fallbackNotice,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Entrypoint Trace diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildClassInheritanceHierarchyViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const classesValue = normalized.classes;
  const classes = classesValue instanceof Map ? classesValue : classesValue ?? null;
  if (!(classes instanceof Map) || classes.size === 0) {
    return { message: "Class inheritance metadata is not available in this CommandView artifact." };
  }

  const rootId = state.levelSelections.rootId ?? null;
  const domainId = state.levelSelections.domainId ?? null;
  const moduleId = state.levelSelections.moduleId ?? null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const isScopedSelection = Boolean(selectionLabel);

  const scopedClassIds = new Set();
  let scopeDescription = "repository";

  if (moduleId) {
    classes.forEach((record, classId) => {
      if (record?.moduleId === moduleId) {
        scopedClassIds.add(classId);
      }
    });
    scopeDescription = moduleId;
  } else if (domainId) {
    classes.forEach((record, classId) => {
      if (isModuleWithinScope(record?.moduleId, domainId)) {
        scopedClassIds.add(classId);
      }
    });
    scopeDescription = domainId;
  } else if (rootId) {
    classes.forEach((record, classId) => {
      if (isModuleWithinScope(record?.moduleId, rootId)) {
        scopedClassIds.add(classId);
      }
    });
    scopeDescription = rootId;
  } else {
    classes.forEach((_, classId) => scopedClassIds.add(classId));
  }

  let fallbackNotice = null;

  if (scopedClassIds.size === 0) {
    classes.forEach((_, classId) => scopedClassIds.add(classId));
    scopeDescription = "repository";
    if (isScopedSelection && selectionLabel) {
      fallbackNotice = `No classes recorded for "${selectionLabel}". Showing repository hierarchy instead.`;
    } else if (isScopedSelection) {
      fallbackNotice = "No classes recorded for the current selection. Showing repository hierarchy instead.";
    }
  }

  if (scopedClassIds.size === 0) {
    return { message: "Class inheritance metadata is not available in this CommandView artifact." };
  }

  const targetClassIds = collectClassInheritanceScope(scopedClassIds, classes);
  const targetClasses = new Map();
  targetClassIds.forEach((classId) => {
    const record = classes.get(classId);
    if (record) {
      targetClasses.set(classId, record);
    }
  });

  if (targetClasses.size === 0) {
    return { message: "Class inheritance metadata is not available in this CommandView artifact." };
  }

  const primaryClassIds = new Set();
  targetClasses.forEach((_, classId) => {
    if (!isScopedSelection || scopedClassIds.has(classId)) {
      primaryClassIds.add(classId);
    }
  });

  if (primaryClassIds.size === 0) {
    targetClasses.forEach((_, classId) => primaryClassIds.add(classId));
  }

  const result = buildClassInheritanceHierarchyDiagram(targetClasses, {
    viewLabel: "Code Flow · Class Inheritance Hierarchy",
    scopeDescription,
    fallbackNotice,
    primaryClassIds,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Class Inheritance Hierarchy diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildExceptionFlowViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const functionsValue = normalized.functions;
  const functionsMap = functionsValue instanceof Map ? functionsValue : functionsValue ?? null;
  if (!(functionsMap instanceof Map) || functionsMap.size === 0) {
    return { message: "Function metadata has not been normalized for this CommandView artifact." };
  }

  const repositoryFunctions = collectFunctionsWithExceptions(functionsMap);
  if (repositoryFunctions.length === 0) {
    return { message: "No exceptions were recorded in this CommandView artifact." };
  }

  const repositoryFunctionSet = new Set(repositoryFunctions);

  const selections = state.levelSelections ?? {};
  const focusFunctionId = typeof selections.functionId === "string" ? selections.functionId : null;
  const moduleId = typeof selections.moduleId === "string" ? selections.moduleId : null;
  const domainId = typeof selections.domainId === "string" ? selections.domainId : null;
  const rootId = typeof selections.rootId === "string" ? selections.rootId : null;

  const focusRecord = focusFunctionId ? functionsMap.get(focusFunctionId) : null;
  const focusRaisesExceptions = Boolean(focusRecord && functionRaisesExceptions(focusRecord));

  let scopedFunctionIds = new Set();
  let scopeDescription = "repository";
  let fallbackNotice = null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const isScopedSelection = Boolean(selectionLabel);

  if (focusRaisesExceptions) {
    scopedFunctionIds.add(focusFunctionId);
    const focusModuleId = focusRecord?.moduleId ?? resolveModuleIdFromFunctionId(focusFunctionId);
    if (focusModuleId) {
      scopeDescription = focusModuleId;
    }
  }

  if (!focusRaisesExceptions && moduleId && modules.has(moduleId)) {
    collectModuleExceptionFunctionIds(modules.get(moduleId), functionsMap).forEach((functionId) => {
      scopedFunctionIds.add(functionId);
    });
    if (scopedFunctionIds.size > 0) {
      scopeDescription = moduleId;
    }
  }

  if (scopedFunctionIds.size === 0 && domainId) {
    modules.forEach((moduleRecord, identifier) => {
      if (!isModuleWithinScope(identifier, domainId)) {
        return;
      }
      collectModuleExceptionFunctionIds(moduleRecord, functionsMap).forEach((functionId) => {
        scopedFunctionIds.add(functionId);
      });
    });
    if (scopedFunctionIds.size > 0) {
      scopeDescription = domainId;
    }
  }

  if (scopedFunctionIds.size === 0 && rootId) {
    modules.forEach((moduleRecord, identifier) => {
      if (!isModuleWithinScope(identifier, rootId)) {
        return;
      }
      collectModuleExceptionFunctionIds(moduleRecord, functionsMap).forEach((functionId) => {
        scopedFunctionIds.add(functionId);
      });
    });
    if (scopedFunctionIds.size > 0) {
      scopeDescription = rootId;
    }
  }

  if (scopedFunctionIds.size === 0) {
    scopedFunctionIds = new Set(repositoryFunctionSet);
    scopeDescription = "repository";
    if (isScopedSelection && selectionLabel) {
      fallbackNotice = `No exceptions recorded for "${selectionLabel}". Showing repository map instead.`;
    } else if (isScopedSelection) {
      fallbackNotice = "No exceptions recorded for the current selection. Showing repository map instead.";
    }
  }

  if (scopedFunctionIds.size === 0) {
    return { message: "No exceptions were recorded in this CommandView artifact." };
  }

  const allowedFunctionIds = new Set();
  scopedFunctionIds.forEach((functionId) => {
    if (repositoryFunctionSet.has(functionId)) {
      allowedFunctionIds.add(functionId);
    }
  });

  if (allowedFunctionIds.size === 0) {
    return { message: "No exceptions were recorded in this CommandView artifact." };
  }

  const result = buildExceptionFlowMapDiagram(modules, functionsMap, {
    viewLabel: "State Effects · Exception Flow Map",
    scopeDescription,
    fallbackNotice,
    allowedFunctionIds,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Exception Flow Map diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildIoEffectsViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const functionsValue = normalized.functions;
  const functionsMap = functionsValue instanceof Map ? functionsValue : functionsValue ?? null;
  if (!(functionsMap instanceof Map) || functionsMap.size === 0) {
    return { message: "Function metadata has not been normalized for this CommandView artifact." };
  }

  const repositoryFunctions = collectFunctionsWithIoEffects(functionsMap);
  if (repositoryFunctions.length === 0) {
    return { message: "No IO effects were detected in this CommandView artifact." };
  }

  const repositoryFunctionSet = new Set(repositoryFunctions);

  const selections = state.levelSelections ?? {};
  const focusFunctionId = typeof selections.functionId === "string" ? selections.functionId : null;
  const moduleId = typeof selections.moduleId === "string" ? selections.moduleId : null;
  const domainId = typeof selections.domainId === "string" ? selections.domainId : null;
  const rootId = typeof selections.rootId === "string" ? selections.rootId : null;

  const focusRecord = focusFunctionId ? functionsMap.get(focusFunctionId) : null;
  const focusHasEffects = Boolean(focusRecord && functionHasIoEffects(focusRecord));

  let scopedFunctionIds = new Set();
  let scopeDescription = "repository";
  let fallbackNotice = null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const isScopedSelection = Boolean(selectionLabel);

  if (focusHasEffects) {
    scopedFunctionIds.add(focusFunctionId);
    const focusModuleId = focusRecord?.moduleId ?? resolveModuleIdFromFunctionId(focusFunctionId);
    if (focusModuleId) {
      scopeDescription = focusModuleId;
    }
  }

  if (!focusHasEffects && moduleId && modules.has(moduleId)) {
    collectModuleIoFunctionIds(modules.get(moduleId), functionsMap).forEach((functionId) => {
      scopedFunctionIds.add(functionId);
    });
    if (scopedFunctionIds.size > 0) {
      scopeDescription = moduleId;
    }
  }

  if (scopedFunctionIds.size === 0 && domainId) {
    modules.forEach((moduleRecord, identifier) => {
      if (!isModuleWithinScope(identifier, domainId)) {
        return;
      }
      collectModuleIoFunctionIds(moduleRecord, functionsMap).forEach((functionId) => {
        scopedFunctionIds.add(functionId);
      });
    });
    if (scopedFunctionIds.size > 0) {
      scopeDescription = domainId;
    }
  }

  if (scopedFunctionIds.size === 0 && rootId) {
    modules.forEach((moduleRecord, identifier) => {
      if (!isModuleWithinScope(identifier, rootId)) {
        return;
      }
      collectModuleIoFunctionIds(moduleRecord, functionsMap).forEach((functionId) => {
        scopedFunctionIds.add(functionId);
      });
    });
    if (scopedFunctionIds.size > 0) {
      scopeDescription = rootId;
    }
  }

  if (scopedFunctionIds.size === 0) {
    scopedFunctionIds = new Set(repositoryFunctionSet);
    scopeDescription = "repository";
    if (isScopedSelection && selectionLabel) {
      fallbackNotice = `No IO effects recorded for "${selectionLabel}". Showing repository map instead.`;
    } else if (isScopedSelection) {
      fallbackNotice = "No IO effects recorded for the current selection. Showing repository map instead.";
    }
  }

  if (scopedFunctionIds.size === 0) {
    return { message: "No IO effects were detected in this CommandView artifact." };
  }

  const allowedFunctionIds = new Set();
  scopedFunctionIds.forEach((functionId) => {
    if (repositoryFunctionSet.has(functionId)) {
      allowedFunctionIds.add(functionId);
    }
  });

  if (allowedFunctionIds.size === 0) {
    return { message: "No IO effects were detected in this CommandView artifact." };
  }

  const result = buildIoEffectsDiagram(modules, functionsMap, {
    viewLabel: "State Effects · IO Effects Diagram",
    scopeDescription,
    fallbackNotice,
    allowedFunctionIds,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build IO Effects diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildGlobalVariableUsageViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const functionsValue = normalized.functions;
  const functionsMap = functionsValue instanceof Map ? functionsValue : functionsValue ?? null;
  if (!(functionsMap instanceof Map) || functionsMap.size === 0) {
    return { message: "Function metadata has not been normalized for this CommandView artifact." };
  }

  const repositoryFunctions = collectFunctionsWithGlobalUsage(functionsMap);
  if (repositoryFunctions.length === 0) {
    return { message: "No global variable usage was detected in this CommandView artifact." };
  }

  const repositoryFunctionSet = new Set(repositoryFunctions);

  const selections = state.levelSelections ?? {};
  const focusFunctionId = typeof selections.functionId === "string" ? selections.functionId : null;
  const moduleId = typeof selections.moduleId === "string" ? selections.moduleId : null;
  const domainId = typeof selections.domainId === "string" ? selections.domainId : null;
  const rootId = typeof selections.rootId === "string" ? selections.rootId : null;

  const focusRecord = focusFunctionId ? functionsMap.get(focusFunctionId) : null;
  const focusUsesGlobals = Boolean(focusRecord && functionUsesGlobals(focusRecord));

  let scopedFunctionIds = new Set();
  let scopeDescription = "repository";
  let fallbackNotice = null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const isScopedSelection = Boolean(selectionLabel);

  if (focusUsesGlobals) {
    scopedFunctionIds.add(focusFunctionId);
    const focusModuleId = focusRecord?.moduleId ?? resolveModuleIdFromFunctionId(focusFunctionId);
    if (focusModuleId) {
      scopeDescription = focusModuleId;
    }
  }

  if (!focusUsesGlobals && moduleId && modules.has(moduleId)) {
    collectModuleGlobalUsageFunctionIds(modules.get(moduleId), functionsMap).forEach((functionId) => {
      scopedFunctionIds.add(functionId);
    });
    if (scopedFunctionIds.size > 0) {
      scopeDescription = moduleId;
    }
  }

  if (scopedFunctionIds.size === 0 && domainId) {
    modules.forEach((moduleRecord, identifier) => {
      if (!isModuleWithinScope(identifier, domainId)) {
        return;
      }
      collectModuleGlobalUsageFunctionIds(moduleRecord, functionsMap).forEach((functionId) => {
        scopedFunctionIds.add(functionId);
      });
    });
    if (scopedFunctionIds.size > 0) {
      scopeDescription = domainId;
    }
  }

  if (scopedFunctionIds.size === 0 && rootId) {
    modules.forEach((moduleRecord, identifier) => {
      if (!isModuleWithinScope(identifier, rootId)) {
        return;
      }
      collectModuleGlobalUsageFunctionIds(moduleRecord, functionsMap).forEach((functionId) => {
        scopedFunctionIds.add(functionId);
      });
    });
    if (scopedFunctionIds.size > 0) {
      scopeDescription = rootId;
    }
  }

  if (scopedFunctionIds.size === 0) {
    scopedFunctionIds = new Set(repositoryFunctionSet);
    scopeDescription = "repository";
    if (isScopedSelection && selectionLabel) {
      fallbackNotice = `No global variable usage recorded for "${selectionLabel}". Showing repository map instead.`;
    } else if (isScopedSelection) {
      fallbackNotice = "No global variable usage recorded for the current selection. Showing repository map instead.";
    }
  }

  if (scopedFunctionIds.size === 0) {
    return { message: "No global variable usage was detected in this CommandView artifact." };
  }

  const allowedFunctionIds = new Set();
  scopedFunctionIds.forEach((functionId) => {
    if (repositoryFunctionSet.has(functionId)) {
      allowedFunctionIds.add(functionId);
    }
  });

  if (allowedFunctionIds.size === 0) {
    return { message: "No global variable usage was detected in this CommandView artifact." };
  }

  const result = buildGlobalVariableUsageMapDiagram(modules, functionsMap, {
    viewLabel: "State Effects · Global Variable Usage Map",
    scopeDescription,
    fallbackNotice,
    allowedFunctionIds,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Global Variable Usage Map diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function collectFunctionsWithExceptions(functionsMap) {
  if (!(functionsMap instanceof Map)) {
    return [];
  }
  const results = [];
  functionsMap.forEach((record, functionId) => {
    if (functionRaisesExceptions(record)) {
      results.push(functionId);
    }
  });
  results.sort((left, right) => left.localeCompare(right));
  return results;
}

function collectModuleExceptionFunctionIds(moduleRecord, functionsMap) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return [];
  }
  const functionIds = Array.isArray(moduleRecord.functions) ? moduleRecord.functions : [];
  return functionIds.filter((functionId) => {
    if (!functionsMap.has(functionId)) {
      return false;
    }
    return functionRaisesExceptions(functionsMap.get(functionId));
  });
}

function functionRaisesExceptions(record) {
  if (!record || typeof record !== "object") {
    return false;
  }
  const raised = Array.isArray(record.raisedExceptions) ? record.raisedExceptions : [];
  return raised.length > 0;
}

function collectFunctionsWithIoEffects(functionsMap) {
  if (!(functionsMap instanceof Map)) {
    return [];
  }
  const results = [];
  functionsMap.forEach((record, functionId) => {
    if (functionHasIoEffects(record)) {
      results.push(functionId);
    }
  });
  results.sort((left, right) => left.localeCompare(right));
  return results;
}

function collectModuleIoFunctionIds(moduleRecord, functionsMap) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return [];
  }
  const functionIds = Array.isArray(moduleRecord.functions) ? moduleRecord.functions : [];
  return functionIds.filter((functionId) => {
    if (!functionsMap.has(functionId)) {
      return false;
    }
    return functionHasIoEffects(functionsMap.get(functionId));
  });
}

function functionHasIoEffects(record) {
  if (!record || typeof record !== "object") {
    return false;
  }
  const effects = record.ioEffects;
  if (!effects || typeof effects !== "object") {
    return false;
  }
  if (effects.hasEffects === true) {
    return true;
  }
  return effects.reads === true || effects.writes === true || effects.env === true || effects.network === true;
}

function collectFunctionsWithGlobalUsage(functionsMap) {
  if (!(functionsMap instanceof Map)) {
    return [];
  }
  const results = [];
  functionsMap.forEach((record, functionId) => {
    if (functionUsesGlobals(record)) {
      results.push(functionId);
    }
  });
  results.sort((left, right) => left.localeCompare(right));
  return results;
}

function collectModuleGlobalUsageFunctionIds(moduleRecord, functionsMap) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return [];
  }
  const functionIds = Array.isArray(moduleRecord.functions) ? moduleRecord.functions : [];
  return functionIds.filter((functionId) => {
    if (!functionsMap.has(functionId)) {
      return false;
    }
    return functionUsesGlobals(functionsMap.get(functionId));
  });
}

function functionUsesGlobals(record) {
  if (!record || typeof record !== "object") {
    return false;
  }
  const usedGlobals = Array.isArray(record.usedGlobals) ? record.usedGlobals : [];
  return usedGlobals.length > 0;
}

function buildMethodCallChainViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const functionsValue = normalized.functions;
  const functionsMap = functionsValue instanceof Map ? functionsValue : functionsValue ?? null;
  if (!(functionsMap instanceof Map) || functionsMap.size === 0) {
    return { message: "Function metadata has not been normalized for this CommandView artifact." };
  }

  const callGraphValue = normalized.callGraph?.functions;
  const callGraph = callGraphValue instanceof Map ? callGraphValue : callGraphValue ?? null;
  if (!(callGraph instanceof Map) || callGraph.size === 0) {
    return { message: "Call graph data is not available in this CommandView artifact." };
  }

  const repositoryMethodIds = collectRepositoryMethodIds(functionsMap);
  if (repositoryMethodIds.length === 0) {
    return { message: "Class method metadata is not available in this CommandView artifact." };
  }

  const repositoryMethodSet = new Set(repositoryMethodIds);

  const selections = state.levelSelections ?? {};
  const focusFunctionId = typeof selections.functionId === "string" ? selections.functionId : null;
  const moduleId = typeof selections.moduleId === "string" ? selections.moduleId : null;
  const domainId = typeof selections.domainId === "string" ? selections.domainId : null;
  const rootId = typeof selections.rootId === "string" ? selections.rootId : null;

  const focusIsMethod = Boolean(focusFunctionId && isClassMethodId(focusFunctionId) && functionsMap.has(focusFunctionId));

  let scopedMethodIds = new Set();
  let scopeDescription = "repository";
  let fallbackNotice = null;
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;
  const isScopedSelection = Boolean(selectionLabel);

  if (focusIsMethod) {
    scopedMethodIds.add(focusFunctionId);
    const focusModuleId = resolveModuleIdFromFunctionId(focusFunctionId);
    if (focusModuleId) {
      scopeDescription = focusModuleId;
    }
  }

  if (!focusIsMethod && moduleId && modules.has(moduleId)) {
    collectModuleMethodIds(modules.get(moduleId), functionsMap).forEach((methodId) => {
      scopedMethodIds.add(methodId);
    });
    if (scopedMethodIds.size > 0) {
      scopeDescription = moduleId;
    }
  }

  if (scopedMethodIds.size === 0 && domainId) {
    modules.forEach((moduleRecord, identifier) => {
      if (!isModuleWithinScope(identifier, domainId)) {
        return;
      }
      collectModuleMethodIds(moduleRecord, functionsMap).forEach((methodId) => {
        scopedMethodIds.add(methodId);
      });
    });
    if (scopedMethodIds.size > 0) {
      scopeDescription = domainId;
    }
  }

  if (scopedMethodIds.size === 0 && rootId) {
    modules.forEach((moduleRecord, identifier) => {
      if (!isModuleWithinScope(identifier, rootId)) {
        return;
      }
      collectModuleMethodIds(moduleRecord, functionsMap).forEach((methodId) => {
        scopedMethodIds.add(methodId);
      });
    });
    if (scopedMethodIds.size > 0) {
      scopeDescription = rootId;
    }
  }

  if (scopedMethodIds.size > 0 && scopedMethodIds.size < repositoryMethodSet.size) {
    expandMethodScope(scopedMethodIds, callGraph, functionsMap);
  }

  if (scopedMethodIds.size === 0) {
    scopedMethodIds = new Set(repositoryMethodSet);
    scopeDescription = "repository";
    if (isScopedSelection && selectionLabel) {
      fallbackNotice = `No class methods recorded for "${selectionLabel}". Showing repository chains instead.`;
    } else if (isScopedSelection) {
      fallbackNotice = "No class methods recorded for the current selection. Showing repository chains instead.";
    }
  }

  if (scopedMethodIds.size === 0) {
    return { message: "Class method metadata is not available in this CommandView artifact." };
  }

  const focusMethodId = focusIsMethod && scopedMethodIds.has(focusFunctionId) ? focusFunctionId : null;

  const result = buildMethodCallChainDiagram(modules, functionsMap, callGraph, {
    viewLabel: "Code Flow · Method Call Chain",
    scopeDescription,
    fallbackNotice,
    focusFunctionId: focusMethodId,
    moduleId,
    allowedFunctionIds: scopedMethodIds,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Method Call Chain diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function isModuleWithinScope(moduleId, scopePrefix) {
  if (!moduleId || !scopePrefix) {
    return false;
  }
  if (moduleId === scopePrefix) {
    return true;
  }
  if (moduleId.startsWith(`${scopePrefix}.`)) {
    return true;
  }
  return moduleId.includes(`${scopePrefix}.`);
}

function collectClassInheritanceScope(primaryIds, classes) {
  const closure = new Set();
  const queue = [];

  primaryIds.forEach((identifier) => {
    if (classes.has(identifier) && !closure.has(identifier)) {
      closure.add(identifier);
      queue.push(identifier);
    }
  });

  while (queue.length > 0) {
    const classId = queue.shift();
    const record = classes.get(classId);
    if (!record || typeof record !== "object") {
      continue;
    }

    const resolvedBases = Array.isArray(record.resolvedBases) ? record.resolvedBases : [];
    resolvedBases.forEach((base) => {
      if (base?.classId && classes.has(base.classId) && !closure.has(base.classId)) {
        closure.add(base.classId);
        queue.push(base.classId);
      }
    });

    const derivedClassIds = Array.isArray(record.derivedClassIds) ? record.derivedClassIds : [];
    derivedClassIds.forEach((derivedId) => {
      if (classes.has(derivedId) && !closure.has(derivedId)) {
        closure.add(derivedId);
        queue.push(derivedId);
      }
    });
  }

  return closure;
}

function collectRepositoryMethodIds(functionsMap) {
  const results = [];
  functionsMap.forEach((_, functionId) => {
    if (isClassMethodId(functionId)) {
      results.push(functionId);
    }
  });
  results.sort((left, right) => left.localeCompare(right));
  return results;
}

function collectModuleMethodIds(moduleRecord, functionsMap) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return [];
  }
  const functionIds = Array.isArray(moduleRecord.functions) ? moduleRecord.functions : [];
  return functionIds.filter((functionId) => isClassMethodId(functionId) && functionsMap.has(functionId));
}

function expandMethodScope(methodIds, callGraph, functionsMap) {
  if (!(methodIds instanceof Set) || methodIds.size === 0) {
    return;
  }
  if (!(callGraph instanceof Map) || callGraph.size === 0) {
    return;
  }
  const queue = Array.from(methodIds.values());
  const visited = new Set(queue);
  while (queue.length > 0) {
    const functionId = queue.shift();
    const rawTargets = callGraph.get(functionId);
    const targets = Array.isArray(rawTargets)
      ? rawTargets
      : rawTargets instanceof Set
      ? Array.from(rawTargets)
      : [];
    targets.forEach((targetId) => {
      if (!isClassMethodId(targetId) || !functionsMap.has(targetId)) {
        return;
      }
      if (!visited.has(targetId)) {
        visited.add(targetId);
        methodIds.add(targetId);
        queue.push(targetId);
      }
    });
  }
}

function isClassMethodId(functionId) {
  if (typeof functionId !== "string" || functionId.length === 0) {
    return false;
  }
  const separatorIndex = functionId.indexOf("::");
  if (separatorIndex < 0) {
    return false;
  }
  const remainder = functionId.slice(separatorIndex + 2);
  return remainder.includes(".");
}

function resolveModuleIdFromFunctionId(functionId) {
  if (typeof functionId !== "string" || functionId.length === 0) {
    return null;
  }
  const separatorIndex = functionId.indexOf("::");
  if (separatorIndex < 0) {
    return null;
  }
  return functionId.slice(0, separatorIndex);
}

function buildFunctionInventoryOverviewViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modules = normalized.modules instanceof Map ? normalized.modules : normalized.modules ?? null;
  const functionsMap = normalized.functions instanceof Map ? normalized.functions : normalized.functions ?? null;

  const result = buildFunctionInventoryOverviewDiagram(modules, functionsMap, {
    viewLabel: "Health · Function Inventory Overview",
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Function Inventory Overview diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    stats: result.stats,
    policyDetails: result.policyDetails,
  };
}

function buildScreeningSignalTimelineViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized || !normalized.screeningHistory) {
    return { message: "Screening history has not been loaded for this CommandView artifact." };
  }

  const artifactLabel = state.activeOption?.label ?? state.activeOption?.slug ?? "CommandView Artifact";
  const result = buildScreeningTimelineDiagram(normalized.screeningHistory, { artifactLabel });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Screening Signal Timeline diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
  };
}

function buildComplexityHeatmapViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const scope = resolveComplexityHeatmapScope(
    {
      functions: normalized.functions,
      modules: normalized.modules,
      neighborhoods: state.levels?.level4 ?? null,
    },
    {
      currentLevel: state.currentLevel,
      selections: {
        rootId: state.levelSelections.rootId,
        domainId: state.levelSelections.domainId,
        moduleId: state.levelSelections.moduleId,
        functionId: state.levelSelections.functionId,
      },
    }
  );

  if (scope?.message) {
    return { message: scope.message };
  }

  const functionsMap = scope?.functions instanceof Map ? scope.functions : null;
  if (!functionsMap || functionsMap.size === 0) {
    const emptyMessage = scope?.emptyMessage ?? "No complexity metrics recorded for this selection.";
    return { message: emptyMessage };
  }

  const result = buildComplexityHeatmapDiagram(functionsMap, {
    viewLabel: "Quality Metrics · Complexity Heatmap",
    centerLabel: scope?.centerLabel,
    moduleMetrics: normalized.metrics?.modules,
    moduleAggregateLimit: 3,
    coverageRiskThreshold: 0.6,
    statusMessageFormatter: (stats) => formatComplexityHeatmapStatus(stats, scope?.statusContext),
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Complexity Heatmap diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
  };
}

function buildCyclomaticComplexityMapViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const scope = resolveComplexityHeatmapScope(
    {
      functions: normalized.functions,
      modules: normalized.modules,
      neighborhoods: state.levels?.level4 ?? null,
    },
    {
      currentLevel: state.currentLevel,
      selections: {
        rootId: state.levelSelections.rootId,
        domainId: state.levelSelections.domainId,
        moduleId: state.levelSelections.moduleId,
        functionId: state.levelSelections.functionId,
      },
    }
  );

  if (scope?.message) {
    return { message: scope.message };
  }

  const functionsMap = scope?.functions instanceof Map ? scope.functions : null;
  if (!functionsMap || functionsMap.size === 0) {
    const emptyMessage = scope?.emptyMessage ?? "No complexity metrics recorded for this selection.";
    return { message: emptyMessage };
  }

  const result = buildCyclomaticComplexityMapDiagram(functionsMap, {
    viewLabel: "Quality Metrics · Cyclomatic Complexity Map",
    scopeDescription: scope?.statusContext ?? "repository",
    modules: normalized.modules,
    moduleLimit: 12,
    functionLimit: 6,
    coverageRiskThreshold: 0.6,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Cyclomatic Complexity Map diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function formatComplexityHeatmapStatus(stats, context) {
  const extreme = typeof stats?.extreme === "number" ? stats.extreme : 0;
  const high = typeof stats?.high === "number" ? stats.high : 0;
  const moderate = typeof stats?.moderate === "number" ? stats.moderate : 0;
  const low = typeof stats?.low === "number" ? stats.low : 0;
  const unknown = typeof stats?.unknown === "number" ? stats.unknown : 0;
  const maxComplexity = Number.isFinite(stats?.maxComplexity) ? stats.maxComplexity : null;
  const prefix = context ? `Rendered Complexity Heatmap for ${context}` : "Rendered Complexity Heatmap";
  const suffix = maxComplexity !== null ? `, max complexity ${Math.round(maxComplexity)}` : "";
  const coverageStats = stats?.coverage ?? null;
  let coverageSnippet = "";
  if (coverageStats && typeof coverageStats === "object" && Number.isFinite(coverageStats.average)) {
    const avgPercent = Math.round(coverageStats.average * 100);
    const below = typeof coverageStats.belowThreshold === "number" ? coverageStats.belowThreshold : 0;
    const thresholdPercent = Number.isFinite(coverageStats.threshold) ? Math.round(coverageStats.threshold * 100) : null;
    const belowSnippet = below > 0 && thresholdPercent !== null ? `, ${below} below ${thresholdPercent}%` : "";
    coverageSnippet = ` Avg coverage ${avgPercent}%${belowSnippet}`;
  }

  const aggregates = Array.isArray(stats?.moduleAggregates) ? stats.moduleAggregates : [];
  let moduleSnippet = "";
  if (aggregates.length > 0) {
    const formatted = aggregates
      .slice(0, 2)
      .map((aggregate) => formatModuleAggregateSnippet(aggregate))
      .filter(Boolean)
      .join("; ");
    if (formatted) {
      moduleSnippet = ` Hot modules: ${formatted}`;
    }
  }

  return `${prefix} (extreme ${extreme}, high ${high}, moderate ${moderate}, low ${low}, unknown ${unknown}${suffix}).${coverageSnippet}${moduleSnippet}`;
}

function formatModuleAggregateSnippet(aggregate) {
  if (!aggregate || typeof aggregate !== "object") {
    return "";
  }
  const moduleId = typeof aggregate.moduleId === "string" ? aggregate.moduleId : null;
  if (!moduleId) {
    return "";
  }
  const hot = typeof aggregate.hotFunctions === "number" ? aggregate.hotFunctions : aggregate.extreme + aggregate.high;
  const extreme = typeof aggregate.extreme === "number" ? aggregate.extreme : 0;
  const averageCoverage = Number.isFinite(aggregate.coverageAverage)
    ? Math.round(aggregate.coverageAverage * 100)
    : null;
  const churnCommits = Number.isFinite(aggregate.churn?.commitCount) ? aggregate.churn.commitCount : null;
  const churnNet = Number.isFinite(aggregate.churn?.netChanges) ? aggregate.churn.netChanges : null;

  const parts = [];
  if (hot > 0) {
    parts.push(`hot ${hot}`);
    if (extreme > 0) {
      parts.push(`${extreme} extreme`);
    }
  }
  if (averageCoverage !== null) {
    parts.push(`cov ${averageCoverage}%`);
  }
  if (churnCommits !== null) {
    let churnSnippet = `${churnCommits}c`;
    if (churnNet !== null && churnNet !== 0) {
      churnSnippet += churnNet > 0 ? `/+${churnNet}` : `/${churnNet}`;
    }
    parts.push(`churn ${churnSnippet}`);
  }

  if (parts.length === 0) {
    return moduleId;
  }
  return `${moduleId} (${parts.join(", ")})`;
}

function buildLoggingFlowViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const scope = resolveLoggingFlowScope(
    {
      functions: normalized.functions,
      modules: normalized.modules,
      neighborhoods: state.levels?.level4 ?? null,
    },
    {
      currentLevel: state.currentLevel,
      selections: {
        rootId: state.levelSelections.rootId,
        domainId: state.levelSelections.domainId,
        moduleId: state.levelSelections.moduleId,
        functionId: state.levelSelections.functionId,
      },
    }
  );

  if (scope?.message) {
    return { message: scope.message };
  }

  const functionsMap = scope?.functions instanceof Map ? scope.functions : null;
  if (!functionsMap || functionsMap.size === 0) {
    const emptyMessage = scope?.emptyMessage ?? "No logging events recorded for this selection.";
    return { message: emptyMessage };
  }

  const result = buildLoggingFlowDiagram(functionsMap, {
    viewLabel: "Quality Metrics · Logging Flow",
    centerLabel: scope?.centerLabel,
    screeningHistory: normalized.screeningHistory,
    statusMessageFormatter: (stats) => formatLoggingFlowStatus(stats, scope?.statusContext),
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Logging Flow diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
  };
}

function formatLoggingFlowStatus(stats, context) {
  const emitters = typeof stats?.emitters === "number" ? stats.emitters : 0;
  const silent = typeof stats?.silent === "number" ? stats.silent : 0;
  const bucketCounts = stats?.bucketCounts ?? {};
  const events = stats?.events ?? {};
  const severityOrder = ["critical", "error", "warning", "info", "debug", "unknown"];
  const bucketSummary = severityOrder
    .filter((key) => bucketCounts[key] !== undefined)
    .map((key) => `${key} ${bucketCounts[key] ?? 0}`)
    .join(", ");
  const eventSummary = severityOrder
    .filter((key) => events[key] !== undefined)
    .map((key) => `${key} ${events[key] ?? 0}`)
    .join(", ");
  const topModule = Array.isArray(stats?.topModules) && stats.topModules.length > 0 ? stats.topModules[0] : null;
  const trailingNotes = [];
  if (topModule) {
    trailingNotes.push(`top module ${topModule.moduleId} (${topModule.callCount} calls, ${topModule.emitters} emitters)`);
  }
  const screeningNote = describeLoggingFlowScreening(stats?.screening);
  if (screeningNote) {
    trailingNotes.push(screeningNote);
  }
  const trailingSuffix = trailingNotes.length > 0 ? `; ${trailingNotes.join("; ")}` : "";
  const prefix = context ? `Rendered Logging Flow for ${context}` : "Rendered Logging Flow";
  return `${prefix} (emitters ${emitters}, silent ${silent}, buckets ${bucketSummary || "none"}, events ${eventSummary || "none"}${trailingSuffix}).`;
}

function describeLoggingFlowScreening(screening) {
  if (!screening || typeof screening !== "object") {
    return null;
  }
  if (typeof screening.alertSummary === "string" && screening.alertSummary.trim().length > 0) {
    return `screening ${screening.alertSummary.trim()}`;
  }
  const severity = typeof screening.latestSeverity === "string" ? screening.latestSeverity.trim() : "";
  if (!severity) {
    return null;
  }
  if (severity !== "critical" && severity !== "warning") {
    return null;
  }
  const upper = severity.toUpperCase();
  const windowSize = Number.isFinite(screening.windowSize) && screening.windowSize > 0 ? screening.windowSize : null;
  const recentCounts = typeof screening.recentCounts === "object" && screening.recentCounts !== null ? screening.recentCounts : {};
  const recentCount = recentCounts[severity] ?? null;
  const streakLength = Number.isFinite(screening.streakLength) && screening.streakLength > 1 ? screening.streakLength : null;
  const details = [];
  if (windowSize && recentCount !== null) {
    details.push(`${recentCount}/${windowSize} recent`);
  }
  if (streakLength) {
    details.push(`${streakLength}-event streak`);
  }
  const suffix = details.length > 0 ? ` (${details.join(", ")})` : "";
  return `screening ${upper}${suffix}`;
}

function buildPublicVsPrivateApiViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const scope = resolvePublicVsPrivateApiScope(modules, {
    rootId: state.levelSelections.rootId,
    domainId: state.levelSelections.domainId,
    moduleId: state.levelSelections.moduleId,
  });

  if (scope?.message) {
    return { message: scope.message };
  }

  const result = buildPublicVsPrivateApiDiagram(scope.modules, {
    viewLabel: "Quality Metrics · Public vs Private API",
    scopeDescription: scope.scopeDescription,
    fallbackNotice: scope.fallbackNotice ?? undefined,
    moduleLimit: scope.moduleLimit ?? undefined,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Public vs Private API diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function resolvePublicVsPrivateApiScope(modules, selections) {
  const moduleId = typeof selections?.moduleId === "string" ? selections.moduleId : null;
  const domainId = typeof selections?.domainId === "string" ? selections.domainId : null;
  const rootId = typeof selections?.rootId === "string" ? selections.rootId : null;

  const isScopedSelection = Boolean(moduleId || domainId || rootId);
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;

  let scopedModules = new Map();
  let scopeDescription = "repository";

  if (moduleId && modules.has(moduleId)) {
    scopedModules.set(moduleId, modules.get(moduleId));
    scopeDescription = moduleId;
  } else if (domainId) {
    modules.forEach((moduleRecord, identifier) => {
      if (isModuleWithinScope(identifier, domainId)) {
        scopedModules.set(identifier, moduleRecord);
      }
    });
    if (scopedModules.size > 0) {
      scopeDescription = domainId;
    }
  } else if (rootId) {
    modules.forEach((moduleRecord, identifier) => {
      if (isModuleWithinScope(identifier, rootId)) {
        scopedModules.set(identifier, moduleRecord);
      }
    });
    if (scopedModules.size > 0) {
      scopeDescription = rootId;
    }
  }

  if (scopedModules.size === 0) {
    scopedModules = modules;
    scopeDescription = "repository";
  }

  let eligibleModules = filterModulesWithApiSurface(scopedModules);

  if (eligibleModules.size === 0) {
    const repositoryEligible = filterModulesWithApiSurface(modules);
    if (repositoryEligible.size === 0) {
      return { message: "Public vs Private API surface metadata is unavailable for this CommandView artifact." };
    }

    const fallbackNotice = isScopedSelection
      ? selectionLabel
        ? `API surface metadata missing for "${selectionLabel}". Showing repository coverage instead.`
        : "API surface metadata missing for the current selection. Showing repository coverage instead."
      : null;

    eligibleModules = repositoryEligible;
    scopeDescription = "repository";

    return {
      modules: eligibleModules,
      scopeDescription,
      fallbackNotice,
      moduleLimit: undefined,
    };
  }

  return {
    modules: eligibleModules,
    scopeDescription,
    fallbackNotice: null,
    moduleLimit: undefined,
  };
}

function filterModulesWithApiSurface(modules) {
  const map = new Map();
  if (!(modules instanceof Map)) {
    return map;
  }
  modules.forEach((record, identifier) => {
    if (hasModuleApiSurface(record)) {
      map.set(identifier, record);
    }
  });
  return map;
}

function hasModuleApiSurface(moduleRecord) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return false;
  }
  const apiSurface = moduleRecord.apiSurface;
  if (!apiSurface || typeof apiSurface !== "object") {
    return false;
  }

  const exportedSymbols = Array.isArray(apiSurface.exportedSymbols) ? apiSurface.exportedSymbols : [];
  const reexports = Array.isArray(apiSurface.reexports) ? apiSurface.reexports : [];
  const missing = Array.isArray(apiSurface.missingExports) ? apiSurface.missingExports : [];

  const functionsPublic = Array.isArray(apiSurface.functions?.public) ? apiSurface.functions.public : [];
  const functionsInternal = Array.isArray(apiSurface.functions?.internal) ? apiSurface.functions.internal : [];
  const classesPublic = Array.isArray(apiSurface.classes?.public) ? apiSurface.classes.public : [];
  const classesInternal = Array.isArray(apiSurface.classes?.internal) ? apiSurface.classes.internal : [];
  const globalsPublic = Array.isArray(apiSurface.globals?.public) ? apiSurface.globals.public : [];
  const globalsInternal = Array.isArray(apiSurface.globals?.internal) ? apiSurface.globals.internal : [];

  if (
    exportedSymbols.length === 0 &&
    reexports.length === 0 &&
    missing.length === 0 &&
    functionsPublic.length === 0 &&
    functionsInternal.length === 0 &&
    classesPublic.length === 0 &&
    classesInternal.length === 0 &&
    globalsPublic.length === 0 &&
    globalsInternal.length === 0
  ) {
    return false;
  }

  return true;
}

function buildDocumentationCoverageMapViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const scope = resolveDocumentationCoverageScope(
    {
      functions: normalized.functions,
      modules: normalized.modules,
      neighborhoods: state.levels?.level4 ?? null,
    },
    {
      currentLevel: state.currentLevel,
      selections: {
        rootId: state.levelSelections.rootId,
        domainId: state.levelSelections.domainId,
        moduleId: state.levelSelections.moduleId,
        functionId: state.levelSelections.functionId,
      },
    }
  );

  if (scope?.message) {
    return { message: scope.message };
  }

  const functionsMap = scope?.functions instanceof Map ? scope.functions : null;
  if (!functionsMap || functionsMap.size === 0) {
    const emptyMessage = scope?.emptyMessage ?? "No documentation metrics recorded for this selection.";
    return { message: emptyMessage };
  }

  const result = buildDocumentationCoverageMapDiagram(functionsMap, {
    viewLabel: "Quality Metrics · Documentation Coverage Map",
    centerLabel: scope?.centerLabel,
    statusMessageFormatter: (stats) => formatDocumentationCoverageStatus(stats, scope?.statusContext),
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Documentation Coverage Map diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
  };
}

function formatDocumentationCoverageStatus(stats, context) {
  const documented = typeof stats?.documented === "number" ? stats.documented : 0;
  const missing = typeof stats?.missing === "number" ? stats.missing : 0;
  const unknown = typeof stats?.unknown === "number" ? stats.unknown : 0;
  const prefix = context ? `Rendered Documentation Coverage Map for ${context}` : "Rendered Documentation Coverage Map";
  return `${prefix} (documented ${documented}, missing ${missing}, unknown ${unknown}).`;
}

function buildTypeCoverageMapViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const scope = resolveTypeCoverageScope(
    {
      functions: normalized.functions,
      modules: normalized.modules,
      neighborhoods: state.levels?.level4 ?? null,
    },
    {
      currentLevel: state.currentLevel,
      selections: {
        rootId: state.levelSelections.rootId,
        domainId: state.levelSelections.domainId,
        moduleId: state.levelSelections.moduleId,
        functionId: state.levelSelections.functionId,
      },
    }
  );

  if (scope?.message) {
    return { message: scope.message };
  }

  const functionsMap = scope?.functions instanceof Map ? scope.functions : null;
  if (!functionsMap || functionsMap.size === 0) {
    const emptyMessage = scope?.emptyMessage ?? "No type coverage metrics recorded for this selection.";
    return { message: emptyMessage };
  }

  const result = buildTypeCoverageMapDiagram(functionsMap, {
    viewLabel: "Quality Metrics · Type Coverage Map",
    centerLabel: scope?.centerLabel,
    statusMessageFormatter: (stats) => formatTypeCoverageStatus(stats, scope?.statusContext),
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Type Coverage Map diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
  };
}

function formatTypeCoverageStatus(stats, context) {
  const strong = typeof stats?.strong === "number" ? stats.strong : 0;
  const moderate = typeof stats?.moderate === "number" ? stats.moderate : 0;
  const weak = typeof stats?.weak === "number" ? stats.weak : 0;
  const unknown = typeof stats?.unknown === "number" ? stats.unknown : 0;
  const prefix = context ? `Rendered Type Coverage Map for ${context}` : "Rendered Type Coverage Map";
  return `${prefix} (strong ${strong}, moderate ${moderate}, weak ${weak}, unknown ${unknown}).`;
}

function buildTestCoverageMappingViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const functionsValue = normalized.functions;
  const functionsMap = functionsValue instanceof Map ? functionsValue : functionsValue ?? null;
  if (!(functionsMap instanceof Map) || functionsMap.size === 0) {
    return { message: "Function metadata has not been normalized for this CommandView artifact." };
  }

  const scope = resolveTestCoverageScope(modules, functionsMap, {
    rootId: state.levelSelections.rootId,
    domainId: state.levelSelections.domainId,
    moduleId: state.levelSelections.moduleId,
  });

  if (scope?.message) {
    return { message: scope.message };
  }

  const result = buildTestCoverageMappingDiagram(scope.modules, functionsMap, {
    viewLabel: "Risk & Assurance · Test Coverage Mapping",
    centerLabel: scope.centerLabel ?? "Test Coverage Mapping",
    scopeDescription: scope.scopeDescription,
    fallbackNotice: scope.fallbackNotice ?? undefined,
    moduleLimit: scope.moduleLimit ?? undefined,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Test Coverage Mapping diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildGitChurnRiskMapViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const scope = resolveGitChurnScope(modules, {
    rootId: state.levelSelections.rootId,
    domainId: state.levelSelections.domainId,
    moduleId: state.levelSelections.moduleId,
  });

  if (scope?.message) {
    return { message: scope.message };
  }

  const functionsValue = normalized.functions;
  const functionsMap = functionsValue instanceof Map ? functionsValue : functionsValue ?? null;

  const baselines =
    normalized.metrics?.repository?.git_churn ??
    state.inventoryPayload?.statistics?.git_churn ??
    null;

  const result = buildGitChurnRiskMapDiagram(scope.modules, {
    functions: functionsMap,
    baselines,
    viewLabel: "Risk & Assurance · Git Churn Risk Map",
    centerLabel: scope.centerLabel ?? "Git Churn Risk Map",
    scopeDescription: scope.scopeDescription,
    fallbackNotice: scope.fallbackNotice ?? undefined,
    moduleLimit: scope.moduleLimit ?? undefined,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Git Churn Risk Map diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function buildDeadCodeDetectionViewDefinition() {
  const normalized = state.normalizedData;
  if (!normalized) {
    return { message: "Normalized CommandView data is unavailable." };
  }

  const modulesValue = normalized.modules;
  const modules = modulesValue instanceof Map ? modulesValue : modulesValue ?? null;
  if (!(modules instanceof Map) || modules.size === 0) {
    return { message: "Module metadata has not been normalized for this CommandView artifact." };
  }

  const scope = resolveDeadCodeScope(modules, {
    rootId: state.levelSelections.rootId,
    domainId: state.levelSelections.domainId,
    moduleId: state.levelSelections.moduleId,
  });

  if (scope?.message) {
    return { message: scope.message };
  }

  const result = buildDeadCodeDetectionDiagram(scope.modules, {
    viewLabel: "Risk & Assurance · Dead Code Detection",
    centerLabel: scope.centerLabel ?? "Dead Code Detection",
    scopeDescription: scope.scopeDescription,
    fallbackNotice: scope.fallbackNotice ?? undefined,
    moduleLimit: scope.moduleLimit ?? undefined,
    functionLimit: scope.functionLimit ?? undefined,
    importLimit: scope.importLimit ?? undefined,
  });

  if (!result || typeof result !== "object") {
    return { message: "Unable to build Dead Code Detection diagram." };
  }

  if (result.message) {
    return { message: result.message };
  }

  return {
    definition: result.definition,
    label: result.label,
    statusMessage: result.statusMessage,
    statusDetails: Array.isArray(result.statusDetails) ? result.statusDetails : [],
    stats: result.stats,
  };
}

function resolveTestCoverageScope(modules, functionsMap, selections) {
  const moduleId = typeof selections?.moduleId === "string" ? selections.moduleId : null;
  const domainId = typeof selections?.domainId === "string" ? selections.domainId : null;
  const rootId = typeof selections?.rootId === "string" ? selections.rootId : null;

  const isScopedSelection = Boolean(moduleId || domainId || rootId);
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;

  let scopedModules = new Map();
  let scopeDescription = "repository";

  if (moduleId && modules.has(moduleId)) {
    scopedModules.set(moduleId, modules.get(moduleId));
    scopeDescription = moduleId;
  } else if (domainId) {
    modules.forEach((moduleRecord, identifier) => {
      if (isModuleWithinScope(identifier, domainId)) {
        scopedModules.set(identifier, moduleRecord);
      }
    });
    if (scopedModules.size > 0) {
      scopeDescription = domainId;
    }
  } else if (rootId) {
    modules.forEach((moduleRecord, identifier) => {
      if (isModuleWithinScope(identifier, rootId)) {
        scopedModules.set(identifier, moduleRecord);
      }
    });
    if (scopedModules.size > 0) {
      scopeDescription = rootId;
    }
  }

  if (scopedModules.size === 0) {
    scopedModules = modules;
    scopeDescription = "repository";
  }

  let eligibleModules = filterModulesWithCoverageTelemetry(scopedModules, functionsMap);

  if (eligibleModules.size === 0) {
    const repositoryEligible = filterModulesWithCoverageTelemetry(modules, functionsMap);
    if (repositoryEligible.size === 0) {
      return { message: "Test coverage metadata is not available in this CommandView artifact." };
    }
    const fallbackNotice = isScopedSelection
      ? selectionLabel
        ? `No coverage signals recorded for "${selectionLabel}". Showing repository coverage instead.`
        : "No coverage signals recorded for the current selection. Showing repository coverage instead."
      : null;
    return {
      modules: repositoryEligible,
      scopeDescription: "repository",
      fallbackNotice,
      centerLabel: "Test Coverage · repository",
      moduleLimit: undefined,
    };
  }

  const resolvedDescription = scopeDescription ?? "repository";
  return {
    modules: eligibleModules,
    scopeDescription: resolvedDescription,
    fallbackNotice: null,
    centerLabel: `Test Coverage · ${resolvedDescription}`,
    moduleLimit: undefined,
  };
}

function resolveGitChurnScope(modules, selections) {
  const moduleId = typeof selections?.moduleId === "string" ? selections.moduleId : null;
  const domainId = typeof selections?.domainId === "string" ? selections.domainId : null;
  const rootId = typeof selections?.rootId === "string" ? selections.rootId : null;

  const isScopedSelection = Boolean(moduleId || domainId || rootId);
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;

  let scopedModules = new Map();
  let scopeDescription = "repository";

  if (moduleId && modules.has(moduleId)) {
    scopedModules.set(moduleId, modules.get(moduleId));
    scopeDescription = moduleId;
  } else if (domainId) {
    modules.forEach((moduleRecord, identifier) => {
      if (isModuleWithinScope(identifier, domainId)) {
        scopedModules.set(identifier, moduleRecord);
      }
    });
    if (scopedModules.size > 0) {
      scopeDescription = domainId;
    }
  } else if (rootId) {
    modules.forEach((moduleRecord, identifier) => {
      if (isModuleWithinScope(identifier, rootId)) {
        scopedModules.set(identifier, moduleRecord);
      }
    });
    if (scopedModules.size > 0) {
      scopeDescription = rootId;
    }
  }

  if (scopedModules.size === 0) {
    scopedModules = modules;
    scopeDescription = "repository";
  }

  const eligibleModules = filterModulesWithGitChurn(scopedModules);

  if (eligibleModules.size === 0) {
    const repositoryEligible = filterModulesWithGitChurn(modules);
    if (repositoryEligible.size === 0) {
      return { message: "Git churn metrics are not available in this CommandView artifact." };
    }
    const fallbackNotice = isScopedSelection
      ? selectionLabel
        ? `No git churn metrics recorded for "${selectionLabel}". Showing repository churn instead.`
        : "No git churn metrics recorded for the current selection. Showing repository churn instead."
      : null;
    return {
      modules: repositoryEligible,
      scopeDescription: "repository",
      fallbackNotice,
      centerLabel: "Git Churn · repository",
      moduleLimit: undefined,
    };
  }

  const resolvedDescription = scopeDescription ?? "repository";
  return {
    modules: eligibleModules,
    scopeDescription: resolvedDescription,
    fallbackNotice: null,
    centerLabel: `Git Churn · ${resolvedDescription}`,
    moduleLimit: undefined,
  };
}

function resolveDeadCodeScope(modules, selections) {
  const moduleId = typeof selections?.moduleId === "string" ? selections.moduleId : null;
  const domainId = typeof selections?.domainId === "string" ? selections.domainId : null;
  const rootId = typeof selections?.rootId === "string" ? selections.rootId : null;

  const isScopedSelection = Boolean(moduleId || domainId || rootId);
  const selectionLabel = moduleId ?? domainId ?? rootId ?? null;

  let scopedModules = new Map();
  let scopeDescription = "repository";

  if (moduleId && modules.has(moduleId)) {
    scopedModules.set(moduleId, modules.get(moduleId));
    scopeDescription = moduleId;
  } else if (domainId) {
    modules.forEach((moduleRecord, identifier) => {
      if (isModuleWithinScope(identifier, domainId)) {
        scopedModules.set(identifier, moduleRecord);
      }
    });
    if (scopedModules.size > 0) {
      scopeDescription = domainId;
    }
  } else if (rootId) {
    modules.forEach((moduleRecord, identifier) => {
      if (isModuleWithinScope(identifier, rootId)) {
        scopedModules.set(identifier, moduleRecord);
      }
    });
    if (scopedModules.size > 0) {
      scopeDescription = rootId;
    }
  }

  if (scopedModules.size === 0) {
    scopedModules = modules;
    scopeDescription = "repository";
  }

  const eligibleModules = filterModulesWithDeadCodeSignals(scopedModules);

  if (eligibleModules.size === 0) {
    const repositoryEligible = filterModulesWithDeadCodeSignals(modules);
    if (repositoryEligible.size === 0) {
      return { message: "Dead code signals are not available in this CommandView artifact." };
    }
    const fallbackNotice = isScopedSelection
      ? selectionLabel
        ? `No dead code signals recorded for "${selectionLabel}". Showing repository dead code signals instead.`
        : "No dead code signals recorded for the current selection. Showing repository dead code signals instead."
      : null;
    return {
      modules: repositoryEligible,
      scopeDescription: "repository",
      fallbackNotice,
      centerLabel: "Dead Code · repository",
      moduleLimit: undefined,
      functionLimit: undefined,
      importLimit: undefined,
    };
  }

  const resolvedDescription = scopeDescription ?? "repository";
  return {
    modules: eligibleModules,
    scopeDescription: resolvedDescription,
    fallbackNotice: null,
    centerLabel: `Dead Code · ${resolvedDescription}`,
    moduleLimit: undefined,
    functionLimit: undefined,
    importLimit: undefined,
  };
}

function filterModulesWithGitChurn(modules) {
  const map = new Map();
  if (!(modules instanceof Map)) {
    return map;
  }
  modules.forEach((moduleRecord, identifier) => {
    if (moduleHasGitChurnTelemetry(moduleRecord)) {
      map.set(identifier, moduleRecord);
    }
  });
  return map;
}

function filterModulesWithCoverageTelemetry(modules, functionsMap) {
  const map = new Map();
  if (!(modules instanceof Map)) {
    return map;
  }
  modules.forEach((moduleRecord, identifier) => {
    if (moduleHasCoverageTelemetry(moduleRecord, functionsMap)) {
      map.set(identifier, moduleRecord);
    }
  });
  return map;
}

function filterModulesWithDeadCodeSignals(modules) {
  const map = new Map();
  if (!(modules instanceof Map)) {
    return map;
  }
  modules.forEach((moduleRecord, identifier) => {
    if (moduleHasDeadCodeTelemetry(moduleRecord)) {
      map.set(identifier, moduleRecord);
    }
  });
  return map;
}

function moduleHasCoverageTelemetry(moduleRecord, functionsMap) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return false;
  }
  const coverageSignals = moduleRecord.coverageSignals ?? null;
  const hasTestImports = Array.isArray(coverageSignals?.imports) && coverageSignals.imports.length > 0;
  const hasMatchesFlag = coverageSignals?.has_matches === true;

  const functionIds = Array.isArray(moduleRecord.functions) ? moduleRecord.functions : [];
  const hasCoverageMetrics = functionIds.some((functionId) => {
    const fn = functionsMap instanceof Map ? functionsMap.get(functionId) : null;
    return Number.isFinite(resolveCoverageValue(fn));
  });

  return hasCoverageMetrics || hasTestImports || hasMatchesFlag;
}

function moduleHasDeadCodeTelemetry(moduleRecord) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return false;
  }
  if (Array.isArray(moduleRecord.unreachableFunctions) && moduleRecord.unreachableFunctions.some((entry) => entry && typeof entry === "object")) {
    return true;
  }
  if (Array.isArray(moduleRecord.unusedImports) && moduleRecord.unusedImports.some((entry) => entry && typeof entry === "object")) {
    return true;
  }
  return false;
}

function moduleHasGitChurnTelemetry(moduleRecord) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return false;
  }
  const churn = moduleRecord.gitChurn ?? moduleRecord.git_churn ?? null;
  if (!churn || typeof churn !== "object") {
    return false;
  }
  const commitsRaw = churn.commit_count ?? churn.commits;
  const additionsRaw = churn.additions;
  const deletionsRaw = churn.deletions;
  const netRaw = churn.net_changes ?? churn.netChanges;

  const commits = Number(commitsRaw);
  const additions = Number(additionsRaw);
  const deletions = Number(deletionsRaw);
  const net = Number(netRaw);

  const hasCommitData = Number.isFinite(commits) && commits > 0;
  const hasLineData = (Number.isFinite(additions) && additions > 0) || (Number.isFinite(deletions) && deletions > 0);
  const hasNetData = Number.isFinite(net) && net !== 0;

  return hasCommitData || hasLineData || hasNetData;
}

function buildAggregateMermaid(levelData, labelFactory, onNode, styleFactory, edgeFormatter) {
  if (!levelData || !Array.isArray(levelData.nodes) || levelData.nodes.length === 0) {
    return null;
  }

  const lines = ["graph LR"];
  const idMap = new Map();

  levelData.nodes.forEach((node) => {
    const sanitizedId = sanitizeMermaidId(node.id);
    idMap.set(node.id, sanitizedId);
    const label = labelFactory(node);
    lines.push(`  ${sanitizedId}["${escapeMermaidLabel(label)}"]`);
    if (typeof onNode === "function") {
      onNode(node, sanitizedId);
    }
    if (typeof styleFactory === "function") {
      const styleLine = styleFactory(node, sanitizedId);
      if (styleLine) {
        lines.push(styleLine);
      }
    }
  });

  const edges = Array.isArray(levelData.edges) ? levelData.edges : [];
  edges.forEach((edge) => {
    const source = idMap.get(edge.source);
    const target = idMap.get(edge.target);
    if (!source || !target) {
      return;
    }
    const weightLabel = typeof edge.weight === "number" && edge.weight > 1 ? `|${edge.weight}|` : "";
    if (typeof edgeFormatter === "function") {
      const formatted = edgeFormatter(edge, source, target, weightLabel);
      if (formatted) {
        lines.push(formatted);
      }
      return;
    }
    lines.push(`  ${source} -->${weightLabel} ${target}`);
  });

  return lines.join("\n");
}

function buildModuleFunctionsMermaid(moduleId, moduleGraph, onNode, styleFactory, edgeFormatter) {
  if (!moduleGraph || !Array.isArray(moduleGraph.nodes) || moduleGraph.nodes.length === 0) {
    return null;
  }

  const lines = ["graph TD"];
  const idMap = new Map();
  const sanitizedModuleId = sanitizeMermaidId(`module_${moduleId}`);
  lines.push(`  subgraph ${sanitizedModuleId}["${escapeMermaidLabel(moduleId)}"]`);

  moduleGraph.nodes.forEach((node) => {
    const sanitizedId = sanitizeMermaidId(node.id);
    idMap.set(node.id, sanitizedId);
    const label = formatFunctionNodeLabel(node, state.levelSelections.functionId === node.id);
    lines.push(`    ${sanitizedId}["${escapeMermaidLabel(label)}"]`);
    if (typeof onNode === "function") {
      onNode(node, sanitizedId);
    }
    if (typeof styleFactory === "function") {
      const styleLine = styleFactory(node, sanitizedId, state.levelSelections.functionId === node.id);
      if (styleLine) {
        lines.push(styleLine);
      }
    }
  });

  lines.push("  end");

  const edges = Array.isArray(moduleGraph.edges) ? moduleGraph.edges : [];
  edges.forEach((edge) => {
    const source = idMap.get(edge.source);
    const target = idMap.get(edge.target);
    if (!source || !target) {
      return;
    }
    if (typeof edgeFormatter === "function") {
      const formatted = edgeFormatter(edge, source, target);
      if (formatted) {
        lines.push(formatted);
      }
      return;
    }
    lines.push(`  ${source} --> ${target}`);
  });

  return lines.join("\n");
}

function formatFunctionNodeLabel(node, isFocus) {
  const parts = [];
  if (isFocus) {
    parts.push("Focus");
  }
  parts.push(node.name ?? node.id);
  const metrics = node.metrics ?? {};
  const metricParts = [];
  if (typeof metrics.lineCount === "number") {
    metricParts.push(`LOC ${metrics.lineCount}`);
  }
  if (typeof metrics.coverage === "number") {
    metricParts.push(`Cov ${formatCoveragePercent(metrics.coverage)}`);
  }
  if (metricParts.length > 0) {
    parts.push(metricParts.join(" | "));
  }
  if (!isFocus && node.moduleId) {
    parts.push(node.moduleId);
  }
  return parts.join("\n");
}

function buildAggregateNodeStyle(levelKey, node, sanitizedId) {
  const palette = NODE_STYLE_PALETTE.aggregate;
  let fill = palette.baseFill;
  let stroke = palette.baseStroke;
  let strokeWidth = "1.5px";

  const functionCount = typeof node.functionCount === "number" ? node.functionCount : null;
  const severity = classifyAggregateSeverity(functionCount);

  if (severity === "critical") {
    fill = palette.criticalFill;
    stroke = palette.criticalStroke;
    strokeWidth = "3px";
  } else if (severity === "alert") {
    fill = palette.alertFill;
    stroke = palette.alertStroke;
    strokeWidth = "2.5px";
  } else if (severity === "caution") {
    fill = palette.cautionFill;
    stroke = palette.cautionStroke;
    strokeWidth = "2px";
  }

  return `  style ${sanitizedId} fill:${fill},stroke:${stroke},stroke-width:${strokeWidth}`;
}

function buildFunctionNodeStyle(node, sanitizedId, isFocus) {
  const palette = NODE_STYLE_PALETTE.function;
  let fill = isFocus ? palette.focusFill : palette.baseFill;
  let stroke = isFocus ? palette.focusStroke : palette.baseStroke;
  let strokeWidth = isFocus ? "2px" : "1.5px";

  const complexity = resolveComplexityValue(node);
  const complexitySeverity = classifyComplexitySeverity(complexity);
  if (complexitySeverity === "alert") {
    fill = palette.alertFill;
    stroke = palette.alertStroke;
    strokeWidth = "3px";
  } else if (complexitySeverity === "caution") {
    fill = palette.cautionFill;
    stroke = palette.cautionStroke;
    strokeWidth = ensureStrokeWidth(strokeWidth, 2);
  }

  const coverage = resolveCoverageValue(node);
  const coverageClass = classifyCoverageState(coverage);
  if (coverageClass === "strong" && !complexitySeverity) {
    stroke = palette.strongStroke;
  } else if (coverageClass === "caution") {
    stroke = palette.weakStroke;
    strokeWidth = ensureStrokeWidth(strokeWidth, 2);
  } else if (coverageClass === "alert") {
    stroke = palette.alertCoverageStroke;
    strokeWidth = ensureStrokeWidth(strokeWidth, 2.5);
  }

  return `  style ${sanitizedId} fill:${fill},stroke:${stroke},stroke-width:${strokeWidth}`;
}

function classifyAggregateSeverity(functionCount) {
  if (!Number.isFinite(functionCount)) {
    return null;
  }
  if (functionCount >= AGGREGATE_FUNCTION_THRESHOLDS.critical) {
    return "critical";
  }
  if (functionCount >= AGGREGATE_FUNCTION_THRESHOLDS.alert) {
    return "alert";
  }
  if (functionCount >= AGGREGATE_FUNCTION_THRESHOLDS.caution) {
    return "caution";
  }
  return null;
}

function resolveComplexityValue(node) {
  if (Number.isFinite(node?.complexity)) {
    return Number(node.complexity);
  }
  if (Number.isFinite(node?.metrics?.complexity)) {
    return Number(node.metrics.complexity);
  }
  if (Number.isFinite(node?.metrics?.cyclomaticComplexity)) {
    return Number(node.metrics.cyclomaticComplexity);
  }
  return null;
}

function classifyComplexitySeverity(value) {
  if (!Number.isFinite(value)) {
    return null;
  }
  if (value >= COMPLEXITY_THRESHOLDS.alert) {
    return "alert";
  }
  if (value >= COMPLEXITY_THRESHOLDS.caution) {
    return "caution";
  }
  return null;
}

function resolveCoverageValue(node) {
  const metricsCoverage = node?.metrics?.coverage;
  if (Number.isFinite(metricsCoverage)) {
    return Number(metricsCoverage);
  }
  if (Number.isFinite(node?.coverage)) {
    return Number(node.coverage);
  }
  return null;
}

function classifyCoverageState(value) {
  if (!Number.isFinite(value)) {
    return null;
  }
  if (value < COVERAGE_THRESHOLDS.alert) {
    return "alert";
  }
  if (value < COVERAGE_THRESHOLDS.caution) {
    return "caution";
  }
  if (value >= COVERAGE_THRESHOLDS.strong) {
    return "strong";
  }
  return null;
}

function formatDottedEdge(edge, source, target, label) {
  const trimmedLabel = typeof label === "string" ? label.trim() : "";
  if (trimmedLabel) {
    return `  ${source} -. ${trimmedLabel} .-> ${target}`;
  }
  return `  ${source} -.-> ${target}`;
}

function ensureStrokeWidth(currentWidth, minimum) {
  const numeric = Number.parseFloat(typeof currentWidth === "string" ? currentWidth : String(currentWidth ?? ""));
  const safeBase = Number.isFinite(numeric) ? numeric : 0;
  const resolved = Math.max(safeBase, Number(minimum));
  return `${resolved}px`;
}

function buildFunctionNeighborhoodMermaid(detail, onNode, styleFactory, edgeFormatter) {
  if (!detail || !detail.focus) {
    return null;
  }

  const focus = detail.focus;
  const neighbors = Array.isArray(detail.neighbors) ? detail.neighbors : [];
  const lines = ["graph TD"];
  const idMap = new Map();

  const focusId = sanitizeMermaidId(focus.id);
  idMap.set(focus.id, focusId);
  lines.push(`  ${focusId}["${escapeMermaidLabel(formatFunctionNodeLabel(focus, true))}"]`);
  if (typeof onNode === "function") {
    onNode(focus, focusId, true);
  }
  if (typeof styleFactory === "function") {
    const focusStyle = styleFactory(focus, focusId, true);
    if (focusStyle) {
      lines.push(focusStyle);
    }
  }

  if (neighbors.length === 0) {
    const noteId = sanitizeMermaidId(`${focus.id}_note`);
    lines.push(`  ${noteId}["${escapeMermaidLabel("No neighbors recorded")}"]`);
    if (typeof edgeFormatter === "function") {
      const formattedNoteEdge = edgeFormatter({ source: focus.id, target: `${focus.id}_note` }, focusId, noteId);
      if (formattedNoteEdge) {
        lines.push(formattedNoteEdge);
      }
    } else {
      lines.push(`  ${focusId} --> ${noteId}`);
    }
    return lines.join("\n");
  }

  neighbors.forEach((neighbor) => {
    const sanitizedId = sanitizeMermaidId(neighbor.id);
    idMap.set(neighbor.id, sanitizedId);
    lines.push(`  ${sanitizedId}["${escapeMermaidLabel(formatFunctionNodeLabel(neighbor, false))}"]`);
    if (typeof onNode === "function") {
      onNode(neighbor, sanitizedId, false);
    }
    if (typeof styleFactory === "function") {
      const styleLine = styleFactory(neighbor, sanitizedId, false);
      if (styleLine) {
        lines.push(styleLine);
      }
    }
    if (typeof edgeFormatter === "function") {
      const formatted = edgeFormatter({ source: focus.id, target: neighbor.id }, focusId, sanitizedId);
      if (formatted) {
        lines.push(formatted);
      }
    } else {
      lines.push(`  ${focusId} --> ${sanitizedId}`);
    }
  });

  return lines.join("\n");
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

let mermaidIdCounter = 0;

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

function formatCoveragePercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "-";
  }
  if (numeric <= 1) {
    return `${Math.round(numeric * 100)}%`;
  }
  return `${Math.round(numeric)}%`;
}

function collectRequiredDecoratorPolicies() {
  const names = new Set();
  const config = getViewerConfig();
  mergeRequiredDecoratorNames(names, config?.requiredDecorators);
  mergeRequiredDecoratorNames(names, config?.decoratorPolicies?.required);
  mergeRequiredDecoratorNames(names, config?.policies?.decorators?.required);

  const inventory = state.inventoryPayload ?? {};
  mergeRequiredDecoratorNames(names, inventory?.policies?.decorators?.required);
  mergeRequiredDecoratorNames(names, inventory?.metadata?.policies?.decorators?.required);
  mergeRequiredDecoratorNames(names, inventory?.metadata?.decorators?.required);
  mergeRequiredDecoratorNames(names, inventory?.quality_metrics?.requiredDecorators);
  mergeRequiredDecoratorNames(names, inventory?.quality_metrics?.decorators?.required);

  return Array.from(names);
}

function mergeRequiredDecoratorNames(target, source) {
  if (!(target instanceof Set) || !source) {
    return;
  }
  const names = normalizeRequiredDecoratorSource(source);
  names.forEach((name) => {
    if (name.length > 0) {
      target.add(name);
    }
  });
}

function normalizeRequiredDecoratorSource(source) {
  if (!source) {
    return [];
  }
  if (typeof source === "string") {
    const trimmed = source.trim();
    return trimmed.length > 0 ? [trimmed] : [];
  }
  if (Array.isArray(source)) {
    const collected = [];
    source.forEach((entry) => {
      if (typeof entry === "string") {
        const trimmed = entry.trim();
        if (trimmed.length > 0) {
          collected.push(trimmed);
        }
      } else if (entry && typeof entry === "object") {
        const name = typeof entry.name === "string"
          ? entry.name
          : typeof entry.decorator === "string"
            ? entry.decorator
            : typeof entry.id === "string"
              ? entry.id
              : null;
        if (name) {
          const trimmed = name.trim();
          if (trimmed.length > 0) {
            collected.push(trimmed);
          }
        }
      }
    });
    return collected;
  }
  if (typeof source === "object") {
    if (Array.isArray(source.required)) {
      return normalizeRequiredDecoratorSource(source.required);
    }
    if (typeof source.required === "string") {
      return normalizeRequiredDecoratorSource([source.required]);
    }
  }
  return [];
}

function collectDecoratorPolicyArtifacts() {
  const sources = [];
  const push = (value) => {
    if (value === null || value === undefined) {
      return;
    }
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (trimmed.length > 0) {
        sources.push(trimmed);
      }
      return;
    }
    if (Array.isArray(value)) {
      if (value.length > 0) {
        sources.push(value.map((entry) => entry));
      }
      return;
    }
    if (typeof value === "object") {
      const keys = Object.keys(value);
      if (keys.length > 0) {
        sources.push(value);
      }
    }
  };

  const config = getViewerConfig() ?? {};
  push(config.requiredDecorators);
  push(config.decoratorPolicies);
  push(config.policies?.decorators);

  const inventory = state.inventoryPayload ?? {};
  push(inventory.decoratorPolicies);
  push(inventory.policies?.decorators);
  push(inventory.metadata?.decorators);
  push(inventory.metadata?.policies?.decorators);
  push(inventory.quality_metrics?.decorators);
  push(inventory.quality_metrics?.requiredDecorators);

  const normalized = state.normalizedData ?? {};
  push(normalized.decoratorPolicies);
  push(normalized.policies?.decorators);

  return sources.length === 0 ? null : sources;
}
  function buildDecoratorUsageMapViewDefinition() {
    const normalized = state.normalizedData;
    if (!normalized) {
      return { message: "Normalized CommandView data is unavailable." };
    }

    const scope = resolveDecoratorUsageScope(
      {
        functions: normalized.functions,
        modules: normalized.modules,
        neighborhoods: state.levels?.level4 ?? null,
      },
      {
        currentLevel: state.currentLevel,
        selections: {
          rootId: state.levelSelections.rootId,
          domainId: state.levelSelections.domainId,
          moduleId: state.levelSelections.moduleId,
          functionId: state.levelSelections.functionId,
        },
      }
    );

    if (scope?.message) {
      return { message: scope.message };
    }

    const functionsMap = scope?.functions instanceof Map ? scope.functions : null;
    if (!functionsMap || functionsMap.size === 0) {
      const emptyMessage = scope?.emptyMessage ?? "No decorator usage recorded for this selection.";
      return { message: emptyMessage };
    }

    const result = buildDecoratorUsageMapDiagram(functionsMap, {
      viewLabel: "Quality Metrics · Decorator Usage Map",
      centerLabel: scope?.centerLabel,
      policyConfig: collectDecoratorPolicyArtifacts(),
      requiredDecorators: collectRequiredDecoratorPolicies(),
      statusMessageFormatter: (stats, topDecorator) =>
        formatDecoratorUsageStatus(stats, scope?.statusContext, topDecorator),
    });

    if (!result || typeof result !== "object") {
      return { message: "Unable to build Decorator Usage Map diagram." };
    }

    if (result.message) {
      return { message: result.message };
    }

    return {
      definition: result.definition,
      label: result.label,
      statusMessage: result.statusMessage,
    };
  }

  function formatDecoratorUsageStatus(stats, context, topDecorator) {
    const decorated = typeof stats?.decorated === "number" ? stats.decorated : 0;
    const undecorated = typeof stats?.undecorated === "number" ? stats.undecorated : 0;
    const uniqueDecorators = typeof stats?.uniqueDecorators === "number" ? stats.uniqueDecorators : 0;
    const prefix = context ? `Rendered Decorator Usage Map for ${context}` : "Rendered Decorator Usage Map";
    const segments = [
      `decorated ${decorated}`,
      `undecorated ${undecorated}`,
      `${uniqueDecorators} unique decorators`,
    ];
    const topName = topDecorator?.label ?? topDecorator?.name ?? null;
    const topCount = typeof topDecorator?.count === "number" ? topDecorator.count : 0;
    if (topName) {
      segments.push(`top ${topName} x${topCount}`);
    } else {
      segments.push("no decorators recorded");
    }
    const missingRequired = Array.isArray(stats?.missingRequiredDecorators)
      ? stats.missingRequiredDecorators.filter((name) => typeof name === "string" && name.length > 0)
      : [];
    if (missingRequired.length > 0) {
      segments.push(`missing required ${missingRequired.join(", ")}`);
    }
    return `${prefix} (${segments.join(", ")}).`;
  }


function seedDefaultSelections() {
  if (!state.levels) {
    state.levelSelections.rootId = null;
    state.levelSelections.domainId = null;
    state.levelSelections.moduleId = null;
    state.levelSelections.functionId = null;
    return;
  }

  const level0Nodes = state.levels.level0?.nodes ?? [];
  const level1Nodes = state.levels.level1?.nodes ?? [];
  const moduleNodes = state.levels.level2?.nodes ?? [];

  state.levelSelections.rootId = level0Nodes[0]?.id ?? null;
  state.levelSelections.domainId = level1Nodes[0]?.id ?? null;
  state.levelSelections.moduleId = moduleNodes[0]?.id ?? null;

  ensureFunctionSelection();
}

async function renderCurrentLevel() {
  if (!state.activeOption) {
    clearDiagram();
    updateStatus("Select a CommandView artifact to render a diagram.");
    return;
  }

  const views = Array.isArray(state.activeViews) ? state.activeViews : [];
  const hasActiveView = views.length > 0 && state.activeViewIndex >= 0 && state.activeViewIndex < views.length;
  if (hasActiveView) {
    const handled = await renderActiveView();
    if (handled) {
      return;
    }
  }

  resetRenderInteractions();
  const definition = buildMermaidDefinition(state.currentLevel);
  const levelDefinition = getLevelDefinition(state.currentLevel);
  const levelLabel = levelDefinition?.label ?? state.currentLevel;

  if (!definition) {
    clearDiagram();
    updateStatus(`${levelLabel} has no data for ${state.activeOption.label}.`);
    return;
  }

  updateStatus(`Rendering ${levelLabel} for ${state.activeOption.label}…`);
  state.diagramDefinition = definition;
  updateExportButtonState();
  const rendered = await renderDiagram(definition);
  if (rendered) {
    const nodeCount = getLevelNodeCount(state.currentLevel);
    const nodeDetail = nodeCount > 0 ? ` (${nodeCount} nodes)` : "";
    const suggestion = buildZoomSuggestion(state.currentLevel, nodeCount);
    const baseMessage = `Rendered ${levelLabel} for ${state.activeOption.label}${nodeDetail}.`;
    updateStatus(suggestion ? `${baseMessage} ${suggestion}` : baseMessage);
  }
}

async function renderActiveView() {
  const views = Array.isArray(state.activeViews) ? state.activeViews : [];
  if (views.length === 0) {
    state.activeViewIndex = -1;
    return false;
  }

  if (state.activeViewIndex < 0 || state.activeViewIndex >= views.length) {
    state.activeViewIndex = views.length - 1;
  }

  const descriptor = views[state.activeViewIndex];
  if (!descriptor) {
    clearActiveViewSelection({ silent: true, suppressStatus: true });
    return false;
  }

  const metadata = getViewMetadata(descriptor.packId, descriptor.viewId);
  if (!metadata) {
    removeActiveView(state.activeViewIndex, { suppressRender: true, suppressStatus: true });
    return state.activeViewIndex >= 0 ? renderActiveView() : false;
  }

  const availability = evaluateViewAvailability(metadata.view);
  if (!availability.available || typeof availability.builder !== "function") {
    clearDiagram();
    state.diagramDefinition = null;
    updateExportButtonState();
    updateStatus(availability.reason ?? `View ${metadata.view.label} is not available for rendering yet.`);
    setStatusDetails([]);
    return true;
  }

  resetRenderInteractions();
  setStatusDetails([]);
  const builderResult = await Promise.resolve(
    availability.builder({
      state,
      pack: metadata.pack,
      view: metadata.view,
      descriptor,
    })
  );
  const builderStatusDetails = deriveBuilderStatusDetails(builderResult);

  if (!builderResult || typeof builderResult.definition !== "string" || builderResult.definition.trim().length === 0) {
    clearDiagram();
    const fallbackMessage = builderResult?.message ?? `No diagram available for ${metadata.view.label} yet.`;
    updateStatus(fallbackMessage);
    state.diagramDefinition = null;
    updateExportButtonState();
    if (builderStatusDetails.length > 0) {
      setStatusDetails(builderStatusDetails);
    }
    return true;
  }

  const label = builderResult.label ?? `${metadata.pack.title} · ${metadata.view.label}`;
  updateStatus(builderResult.preRenderMessage ?? `Rendering ${label}…`);
  state.diagramDefinition = builderResult.definition;
  updateExportButtonState();

  const rendered = await renderDiagram(builderResult.definition);
  if (rendered) {
    const successMessage = builderResult.statusMessage ?? `Rendered ${label}.`;
    updateStatus(successMessage);
  }

  if (builderStatusDetails.length > 0) {
    setStatusDetails(builderStatusDetails);
  }

  return true;
}

async function renderDiagram(definition) {
  const container = document.getElementById("diagram");
  if (!container || !window.mermaid) {
    return false;
  }

  try {
    const renderKey = `viewer-diagram-${Date.now()}`;
    const { svg } = await window.mermaid.render(renderKey, definition);
    container.innerHTML = svg;
    attachRenderInteractions(container);
    initializeDiagramZoom(container);
    return true;
  } catch (error) {
    console.error("Mermaid render failed", error);
    updateStatus("Unable to render diagram preview (see console for details).");
    return false;
  }
}

function initializeDiagramZoom(container) {
  if (!container) return;

  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  // Reset zoom state when new diagram loads
  state.zoom.scale = 1;
  state.zoom.translateX = 0;
  state.zoom.translateY = 0;

  // Apply initial transform
  applyZoomTransform(svgElement);

  // Remove existing listeners to avoid duplicates
  container.removeEventListener('wheel', handleDiagramWheel);
  container.removeEventListener('mousedown', handleDiagramMouseDown);

  // Add zoom and pan event listeners
  container.addEventListener('wheel', handleDiagramWheel, { passive: false });
  container.addEventListener('mousedown', handleDiagramMouseDown);

  console.log('[initializeDiagramZoom] Zoom controls initialized');
}

function handleDiagramWheel(event) {
  event.preventDefault();
  
  const container = event.currentTarget;
  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  // Get mouse position relative to container
  const rect = container.getBoundingClientRect();
  const mouseX = event.clientX - rect.left;
  const mouseY = event.clientY - rect.top;

  // Calculate zoom delta (negative deltaY = zoom in)
  const zoomDelta = event.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.max(0.1, Math.min(200, state.zoom.scale * zoomDelta));

  // Adjust translation to zoom towards mouse position
  const scaleChange = newScale / state.zoom.scale;
  state.zoom.translateX = mouseX - (mouseX - state.zoom.translateX) * scaleChange;
  state.zoom.translateY = mouseY - (mouseY - state.zoom.translateY) * scaleChange;
  state.zoom.scale = newScale;

  applyZoomTransform(svgElement);
  updateZoomIndicator();
}

function handleDiagramMouseDown(event) {
  // Only pan with left mouse button or when space key is held
  if (event.button !== 0) return;

  const container = event.currentTarget;
  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  // Don't pan if clicking on an interactive element
  if (event.target.classList.contains('diagram-node-action')) {
    return;
  }

  state.zoom.isPanning = true;
  state.zoom.startX = event.clientX - state.zoom.translateX;
  state.zoom.startY = event.clientY - state.zoom.translateY;

  container.style.cursor = 'grabbing';

  const handleMouseMove = (e) => {
    if (!state.zoom.isPanning) return;
    
    state.zoom.translateX = e.clientX - state.zoom.startX;
    state.zoom.translateY = e.clientY - state.zoom.startY;
    
    applyZoomTransform(svgElement);
  };

  const handleMouseUp = () => {
    state.zoom.isPanning = false;
    container.style.cursor = 'grab';
    
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };

  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
}

function applyZoomTransform(svgElement) {
  if (!svgElement) return;
  
  const transform = `translate(${state.zoom.translateX}px, ${state.zoom.translateY}px) scale(${state.zoom.scale})`;
  svgElement.style.transform = transform;
  svgElement.style.transformOrigin = '0 0';
  svgElement.style.transition = 'transform 0.1s ease-out';
}

function updateZoomIndicator() {
  const indicator = document.getElementById('zoom-indicator');
  if (indicator) {
    indicator.textContent = `${Math.round(state.zoom.scale * 100)}%`;
  }
}

function resetDiagramZoom() {
  const container = document.getElementById('diagram');
  if (!container) return;

  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  state.zoom.scale = 1;
  state.zoom.translateX = 0;
  state.zoom.translateY = 0;

  applyZoomTransform(svgElement);
  updateZoomIndicator();
  updateStatus('Zoom reset to 100%');
}

function zoomIn() {
  const container = document.getElementById('diagram');
  if (!container) return;

  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  const rect = container.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  const newScale = Math.min(200, state.zoom.scale * 1.2);
  const scaleChange = newScale / state.zoom.scale;
  
  state.zoom.translateX = centerX - (centerX - state.zoom.translateX) * scaleChange;
  state.zoom.translateY = centerY - (centerY - state.zoom.translateY) * scaleChange;
  state.zoom.scale = newScale;

  applyZoomTransform(svgElement);
  updateZoomIndicator();
}

function zoomOut() {
  const container = document.getElementById('diagram');
  if (!container) return;

  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  const rect = container.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  const newScale = Math.max(0.1, state.zoom.scale * 0.8);
  const scaleChange = newScale / state.zoom.scale;
  
  state.zoom.translateX = centerX - (centerX - state.zoom.translateX) * scaleChange;
  state.zoom.translateY = centerY - (centerY - state.zoom.translateY) * scaleChange;
  state.zoom.scale = newScale;

  applyZoomTransform(svgElement);
  updateZoomIndicator();
}

function attachRenderInteractions(container) {
  if (!container || !(state.renderInteractions instanceof Map)) {
    return;
  }

  state.renderInteractions.forEach((handler, elementId) => {
    const safeId = typeof CSS !== "undefined" && typeof CSS.escape === "function"
      ? CSS.escape(elementId)
      : elementId.replace(/([^a-zA-Z0-9_-])/g, "\\$1");
    const target = container.querySelector(`#${safeId}`);
    if (!target) {
      return;
    }

    const invokeHandler = () => {
      try {
        handler();
      } catch (error) {
        console.error("Diagram interaction handler failed", error);
      }
    };

    const clickListener = (event) => {
      event.preventDefault();
      event.stopPropagation();
      invokeHandler();
    };

    const keyListener = (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        event.stopPropagation();
        invokeHandler();
      }
    };

    target.classList.add("diagram-node-action");
    target.setAttribute("tabindex", "0");
    target.setAttribute("role", "button");
    target.addEventListener("click", clickListener);
    target.addEventListener("keydown", keyListener);
  });
}

function renderViewPacks() {
  if (!packUi.container) {
    packUi.container = document.getElementById("view-pack-container");
  }

  if (!packUi.container) {
    return;
  }

  packUi.container.innerHTML = "";

  const activeViews = Array.isArray(state.activeViews) ? state.activeViews : [];

  VIEW_PACKS.forEach((pack) => {
    const section = document.createElement("section");
    section.className = "view-pack";

    const heading = document.createElement("h3");
    heading.className = "view-pack-heading";
    heading.textContent = pack.title;
    section.appendChild(heading);

    if (pack.description) {
      const packNote = document.createElement("p");
      packNote.className = "view-pack-note";
      packNote.textContent = pack.description;
      section.appendChild(packNote);
    }

    const list = document.createElement("ul");
    list.className = "view-pack-list";

    pack.views.forEach((view) => {
      const item = document.createElement("li");

      const button = document.createElement("button");
      button.type = "button";
      button.className = "view-pack-button";
      button.dataset.packId = pack.id;
      button.dataset.viewId = view.id;
      button.dataset.status = view.status ?? "planned";
      button.dataset.filename = view.filename ?? "";
      button.textContent = view.label;

      const availability = evaluateViewAvailability(view);
      const descriptorIndex = activeViews.findIndex((entry) => entry.packId === pack.id && entry.viewId === view.id);
      const isOpen = descriptorIndex >= 0;
      const isActive = isOpen && state.activeViewIndex === descriptorIndex;
      const canInteract = availability.available || isOpen;

      if (canInteract) {
        button.disabled = false;
        button.title = isOpen
          ? availability.reason
            ? `Open view (requirements pending: ${availability.reason})`
            : "Switch to this view tab."
          : "Select to render this view.";
        button.addEventListener("click", () => {
          selectView(pack.id, view.id);
        });
      } else {
        button.disabled = true;
        button.title = availability.reason ?? view.note ?? "View wiring pending implementation.";
      }

      if (isActive) {
        button.classList.add("selected");
        button.setAttribute("aria-pressed", "true");
      } else if (isOpen) {
        button.classList.add("open");
        button.setAttribute("aria-pressed", "mixed");
      } else {
        button.setAttribute("aria-pressed", "false");
      }

      item.appendChild(button);

      if (view.description) {
        const description = document.createElement("p");
        description.className = "view-pack-note";
        description.textContent = view.description;
        item.appendChild(description);
      }

      if (!availability.available) {
        if (availability.reason) {
          const availabilityNote = document.createElement("p");
          availabilityNote.className = "view-pack-note";
          availabilityNote.textContent = availability.reason;
          item.appendChild(availabilityNote);
        }
        if (view.note) {
          const note = document.createElement("p");
          note.className = "view-pack-note";
          note.textContent = view.note;
          item.appendChild(note);
        }
      } else if (view.note) {
        const note = document.createElement("p");
        note.className = "view-pack-note";
        note.textContent = view.note;
        item.appendChild(note);
      }

      list.appendChild(item);
    });

    section.appendChild(list);
    packUi.container.appendChild(section);
  });
}

function clearActiveViewSelection(options = {}) {
  const { silent = false, suppressStatus = false } = options ?? {};
  const hadSelection = Array.isArray(state.activeViews) && state.activeViews.length > 0;
  state.activeViews = [];
  state.activeViewIndex = -1;
  if (!silent) {
    renderViewPacks();
    renderViewTabs();
  }
  if (hadSelection && !suppressStatus) {
    updateStatus("View selection cleared; returning to zoom levels.");
  }
}

function selectView(packId, viewId) {
  const metadata = getViewMetadata(packId, viewId);
  if (!metadata) {
    updateStatus("Unable to locate the requested view definition.");
    return;
  }

  if (!Array.isArray(state.activeViews)) {
    state.activeViews = [];
  }

  const existingIndex = state.activeViews.findIndex((entry) => entry.packId === packId && entry.viewId === viewId);
  if (existingIndex >= 0) {
    state.activeViewIndex = existingIndex;
    renderViewPacks();
    renderViewTabs();
    updateStatus(`Displaying ${metadata.pack.title} · ${metadata.view.label}.`);
    void renderCurrentLevel();
    return;
  }

  const availability = evaluateViewAvailability(metadata.view);
  if (!availability.available) {
    updateStatus(availability.reason ?? "This view is not available yet.");
    return;
  }

  state.activeViews.push({ packId, viewId });
  state.activeViewIndex = state.activeViews.length - 1;
  renderViewPacks();
  renderViewTabs();
  updateStatus(`Preparing ${metadata.pack.title} · ${metadata.view.label}…`);
  void renderCurrentLevel();
}

function renderViewTabs() {
  if (!viewTabsUi.container) {
    viewTabsUi.container = document.getElementById("view-tabs");
  }

  const container = viewTabsUi.container;
  if (!container) {
    return;
  }

  const views = Array.isArray(state.activeViews) ? state.activeViews : [];
  container.innerHTML = "";
  container.classList.toggle("view-tabs-empty", views.length === 0);
  container.setAttribute("role", "tablist");

  const zoomButton = document.createElement("button");
  zoomButton.type = "button";
  zoomButton.className = "view-tab";
  zoomButton.dataset.tab = "zoom";
  zoomButton.setAttribute("role", "tab");
  zoomButton.textContent = "Zoom Levels";
  const zoomActive = views.length === 0 || state.activeViewIndex === -1;
  if (zoomActive) {
    zoomButton.classList.add("active");
  }
  zoomButton.setAttribute("aria-selected", zoomActive ? "true" : "false");
  zoomButton.addEventListener("click", () => {
    if (state.activeViewIndex !== -1 || views.length > 0) {
      clearActiveViewSelection({ suppressStatus: true });
      renderViewTabs();
      void renderCurrentLevel();
      updateStatus("Switched to zoom levels.");
    }
  });
  container.appendChild(zoomButton);

  views.forEach((descriptor, index) => {
    const metadata = getViewMetadata(descriptor.packId, descriptor.viewId);
    const label = metadata ? `${metadata.pack.title} · ${metadata.view.label}` : `${descriptor.packId} · ${descriptor.viewId}`;

    const wrapper = document.createElement("div");
    wrapper.className = "view-tab-wrapper";
    container.appendChild(wrapper);

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "view-tab";
    trigger.setAttribute("role", "tab");
    trigger.textContent = label;
    const isActive = state.activeViewIndex === index;
    trigger.setAttribute("aria-selected", isActive ? "true" : "false");
    if (isActive) {
      trigger.classList.add("active");
    }
    trigger.addEventListener("click", () => {
      if (state.activeViewIndex === index) {
        return;
      }
      state.activeViewIndex = index;
      renderViewPacks();
      renderViewTabs();
      updateStatus(`Displaying ${label}.`);
      void renderCurrentLevel();
    });
    wrapper.appendChild(trigger);

    const close = document.createElement("button");
    close.type = "button";
    close.className = "view-tab-close";
    close.setAttribute("aria-label", `Close ${label}`);
    close.textContent = "x";
    close.addEventListener("click", (event) => {
      event.stopPropagation();
      removeActiveView(index);
    });
    wrapper.appendChild(close);
  });
}

function removeActiveView(index, options = {}) {
  if (!Array.isArray(state.activeViews) || index < 0 || index >= state.activeViews.length) {
    return;
  }

  const { suppressRender = false, suppressStatus = false } = options ?? {};

  state.activeViews.splice(index, 1);
  if (state.activeViews.length === 0) {
    state.activeViewIndex = -1;
  } else if (state.activeViewIndex > index) {
    state.activeViewIndex -= 1;
  } else if (state.activeViewIndex >= state.activeViews.length) {
    state.activeViewIndex = state.activeViews.length - 1;
  } else if (state.activeViewIndex === index) {
    state.activeViewIndex = Math.min(index, state.activeViews.length - 1);
  }

  renderViewPacks();
  renderViewTabs();

  if (suppressRender) {
    return;
  }

  if (state.activeViewIndex >= 0) {
    const descriptor = state.activeViews[state.activeViewIndex];
    const metadata = descriptor ? getViewMetadata(descriptor.packId, descriptor.viewId) : null;
    const label = metadata ? `${metadata.pack.title} · ${metadata.view.label}` : "view";
    if (!suppressStatus) {
      updateStatus(`Closed view; displaying ${label}.`);
    }
    void renderCurrentLevel();
  } else {
    if (!suppressStatus) {
      updateStatus("Closed view; returning to zoom levels.");
    }
    void renderCurrentLevel();
  }
}

function renderSelector() {
  const list = document.getElementById("selector-list");
  console.log("[renderSelector] List element:", list);
  if (!list) {
    console.error("[renderSelector] selector-list element not found!");
    return;
  }

  list.innerHTML = "";
  console.log("[renderSelector] Rendering", state.entries.length, "entries");
  state.entries.forEach((entry) => {
    entry.options.forEach((option) => {
      console.log("[renderSelector] Adding option:", option.label);
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.slug = option.slug;
      button.dataset.relativePath = option.relative_path;
      button.textContent = option.label;
      button.addEventListener("click", () => {
        void selectOption(option);
      });
      if (state.activeOption?.relative_path === option.relative_path) {
        button.classList.add("selected");
      }
      item.appendChild(button);
      list.appendChild(item);
    });
  });
  console.log("[renderSelector] Rendered", list.children.length, "items");
}

async function selectOption(option) {
  console.log("[selectOption] Selecting option:", option);
  persistActiveSelectionMemory();
  clearActiveViewSelection({ silent: true, suppressStatus: true });
  state.activeOption = option;
  state.diagramDefinition = null;
  updateExportButtonState();
  renderSelector();
  updateStatus(`Loading ${option.label}…`);
  try {
    const record = await loadCommandViewPayloads(option);
    const loadedSegments = record.screening ? "inventory + screening" : "inventory";
    updateStatus(`Loaded ${option.label} (${loadedSegments}); preparing zoom controls…`);

    seedDefaultSelections();
    restoreSelectionMemory(option);
    synchronizeSelections();
    ensureCurrentLevelIsAvailable();
    updateLevelButtonsState();
    renderLevelSidebar();
    renderBreadcrumb();
    renderViewPacks();
    renderViewTabs();

    if (record.normalized) {
      console.debug("Normalized CommandView data", record.normalized);
    }

    await renderCurrentLevel();
  } catch (error) {
    console.error("Failed to load CommandView artifacts", error);
    clearDiagram();
    const detail = error instanceof Error ? error.message : String(error);
    updateStatus(`Failed to load ${option.label}; ${detail}`);
    renderViewPacks();
    renderViewTabs();
  }
}

function exportCurrentDiagram() {
  if (!state.diagramDefinition || state.diagramDefinition.trim().length === 0) {
    updateStatus("No diagram available to export yet.");
    updateExportButtonState();
    return;
  }

  const filename = buildDiagramExportFilename();
  const blob = new Blob([state.diagramDefinition], { type: "text/plain" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  updateStatus(`Exported Mermaid definition as ${filename}.`);
}

function wireRefresh() {
  const button = document.getElementById("refresh-button");
  if (!button) {
    return;
  }

  headerUi.refreshButton = button;

  button.addEventListener("click", async () => {
    button.disabled = true;
    updateStatus("Refreshing selector data...");
    try {
      await refreshSelectorData();
    } catch (error) {
      console.error("Refresh failed", error);
      updateStatus(`Refresh failed: ${error.message}`);
    } finally {
      button.disabled = false;
    }
  });
}

function buildSelectorUrl(endpoint) {
  if (!endpoint || typeof endpoint !== "string") {
    return null;
  }

  const trimmed = endpoint.trim();
  if (trimmed.length === 0) {
    return null;
  }

  if (/\.json$/i.test(trimmed)) {
    return trimmed;
  }

  const base = ensureTrailingSlash(trimmed);
  return `${base}selector.json`;
}

async function refreshSelectorData(options = {}) {
  const { allowFallback = true } = options;
  const config = getViewerConfig();
  const selectorEndpoint = config.selectorApiEndpoint || config.reportsBaseUrl || DEFAULT_REPORTS_BASE_URL;
  const selectorUrl = buildSelectorUrl(selectorEndpoint);

  console.log("[refreshSelectorData] Config:", config);
  console.log("[refreshSelectorData] Endpoint:", selectorEndpoint);
  console.log("[refreshSelectorData] Selector URL:", selectorUrl);

  if (!selectorUrl) {
    updateStatus("No selector endpoint configured; using demo data.");
    if (allowFallback) {
      await bootstrapDemoPayload();
    }
    return;
  }

  try {
    updateStatus(`Fetching selector data from ${selectorUrl}...`);
    console.log("[refreshSelectorData] Fetching from:", selectorUrl);
    const response = await fetch(selectorUrl, { cache: "no-cache" });

    console.log("[refreshSelectorData] Response status:", response.status, response.statusText);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const payload = await response.json();
    console.log("[refreshSelectorData] Payload received:", payload);

    if (!payload.entries || !Array.isArray(payload.entries)) {
      throw new Error("Invalid selector payload format");
    }

    console.log("[refreshSelectorData] Setting entries:", payload.entries.length, "groups");
    setEntries(payload.entries);
    updateStatus(`Refreshed selector data (${payload.entries.length} artifact groups loaded).`);
  } catch (error) {
    console.error("[refreshSelectorData] Error:", error);
    if (!allowFallback) {
      throw error;
    }
    updateStatus(`Could not fetch selector data (${error.message}); using demo data.`);
    await bootstrapDemoPayload();
  }
}

function wireExport() {
  const button = document.getElementById("export-button");
  if (!button) {
    return;
  }

  headerUi.exportButton = button;
  button.addEventListener("click", () => {
    exportCurrentDiagram();
  });
  updateExportButtonState();
}

function wireUpdate() {
  const button = getUpdateButton();
  if (!button) {
    console.warn("[wireUpdate] update-button element not found");
    return;
  }

  const { start } = resolveUpdateEndpoints();
  if (!start) {
    button.disabled = true;
    button.title = "Configure viewerConfig.updateApiEndpoint to enable updates.";
    return;
  }

  button.addEventListener("click", () => {
    void handleUpdateButtonClick();
  });
}

function wireZoomControls() {
  const zoomInBtn = document.getElementById("zoom-in-btn");
  const zoomOutBtn = document.getElementById("zoom-out-btn");
  const zoomResetBtn = document.getElementById("zoom-reset-btn");

  if (zoomInBtn) {
    zoomInBtn.addEventListener("click", () => {
      zoomIn();
    });
  }

  if (zoomOutBtn) {
    zoomOutBtn.addEventListener("click", () => {
      zoomOut();
    });
  }

  if (zoomResetBtn) {
    zoomResetBtn.addEventListener("click", () => {
      resetDiagramZoom();
    });
  }

  console.log('[wireZoomControls] Zoom control buttons wired');
}

function initializeSidebarResize() {
  const resizeHandle = document.getElementById('sidebar-resize-handle');
  const sidebar = document.querySelector('.viewer-sidebar');
  
  if (!resizeHandle || !sidebar) {
    console.warn('[initializeSidebarResize] Resize handle or sidebar not found');
    return;
  }

  // Load saved width from localStorage
  const savedWidth = loadSidebarWidth();
  if (savedWidth) {
    applySidebarWidth(savedWidth);
  }

  resizeHandle.addEventListener('mousedown', handleSidebarMouseDown);
  
  console.log('[initializeSidebarResize] Sidebar resize initialized');
}

function initializeStatusPanelResize() {
  const resizeHandle = document.getElementById('status-panel-resize-handle');
  const statusPanel = document.getElementById('status-panel');
  
  if (!resizeHandle || !statusPanel) {
    console.warn('[initializeStatusPanelResize] Resize handle or status panel not found');
    return;
  }

  // Load saved height from localStorage
  const savedHeight = loadStatusPanelHeight();
  if (savedHeight) {
    applyStatusPanelHeight(savedHeight);
  }

  resizeHandle.addEventListener('mousedown', handleStatusPanelMouseDown);
  
  console.log('[initializeStatusPanelResize] Status panel resize initialized');
}

function handleStatusPanelMouseDown(event) {
  event.preventDefault();
  
  const statusPanel = document.getElementById('status-panel');
  if (!statusPanel) return;

  state.statusPanel.isResizing = true;
  state.statusPanel.startY = event.clientY;
  state.statusPanel.startHeight = statusPanel.offsetHeight;

  const resizeHandle = document.getElementById('status-panel-resize-handle');
  if (resizeHandle) {
    resizeHandle.classList.add('resizing');
  }

  document.body.classList.add('status-panel-resizing');

  document.addEventListener('mousemove', handleStatusPanelMouseMove);
  document.addEventListener('mouseup', handleStatusPanelMouseUp);
}

function handleStatusPanelMouseMove(event) {
  if (!state.statusPanel.isResizing) return;

  // Note: moving up (negative delta) should increase height
  const delta = state.statusPanel.startY - event.clientY;
  const newHeight = state.statusPanel.startHeight + delta;
  
  // Constrain height between min and max
  const constrainedHeight = Math.max(100, Math.min(600, newHeight));
  
  applyStatusPanelHeight(constrainedHeight);
}

function handleStatusPanelMouseUp() {
  if (!state.statusPanel.isResizing) return;

  state.statusPanel.isResizing = false;

  const resizeHandle = document.getElementById('status-panel-resize-handle');
  if (resizeHandle) {
    resizeHandle.classList.remove('resizing');
  }

  document.body.classList.remove('status-panel-resizing');

  document.removeEventListener('mousemove', handleStatusPanelMouseMove);
  document.removeEventListener('mouseup', handleStatusPanelMouseUp);

  // Save the new height
  saveStatusPanelHeight(state.statusPanel.height);
}

function applyStatusPanelHeight(height) {
  const statusPanel = document.getElementById('status-panel');
  if (!statusPanel) return;

  statusPanel.style.height = `${height}px`;
  statusPanel.style.maxHeight = `${height}px`;
  state.statusPanel.height = height;
}

function saveStatusPanelHeight(height) {
  try {
    localStorage.setItem('viewer-status-panel-height', height.toString());
  } catch (error) {
    console.warn('[saveStatusPanelHeight] Failed to save status panel height', error);
  }
}

function loadStatusPanelHeight() {
  try {
    const saved = localStorage.getItem('viewer-status-panel-height');
    if (saved) {
      const height = parseInt(saved, 10);
      if (Number.isFinite(height) && height >= 100 && height <= 600) {
        return height;
      }
    }
  } catch (error) {
    console.warn('[loadStatusPanelHeight] Failed to load status panel height', error);
  }
  return null;
}

function handleSidebarMouseDown(event) {
  event.preventDefault();
  
  const sidebar = document.querySelector('.viewer-sidebar');
  if (!sidebar) return;

  state.sidebar.isResizing = true;
  state.sidebar.startX = event.clientX;
  state.sidebar.startWidth = sidebar.offsetWidth;

  const resizeHandle = document.getElementById('sidebar-resize-handle');
  if (resizeHandle) {
    resizeHandle.classList.add('resizing');
  }

  document.body.classList.add('sidebar-resizing');

  document.addEventListener('mousemove', handleSidebarMouseMove);
  document.addEventListener('mouseup', handleSidebarMouseUp);
}

function handleSidebarMouseMove(event) {
  if (!state.sidebar.isResizing) return;

  const delta = event.clientX - state.sidebar.startX;
  const newWidth = state.sidebar.startWidth + delta;
  
  // Constrain width between min and max
  const constrainedWidth = Math.max(200, Math.min(600, newWidth));
  
  applySidebarWidth(constrainedWidth);
}

function handleSidebarMouseUp() {
  if (!state.sidebar.isResizing) return;

  state.sidebar.isResizing = false;

  const resizeHandle = document.getElementById('sidebar-resize-handle');
  if (resizeHandle) {
    resizeHandle.classList.remove('resizing');
  }

  document.body.classList.remove('sidebar-resizing');

  document.removeEventListener('mousemove', handleSidebarMouseMove);
  document.removeEventListener('mouseup', handleSidebarMouseUp);

  // Save the new width
  saveSidebarWidth(state.sidebar.width);
}

function applySidebarWidth(width) {
  const sidebar = document.querySelector('.viewer-sidebar');
  if (!sidebar) return;

  sidebar.style.width = `${width}px`;
  state.sidebar.width = width;
}

function saveSidebarWidth(width) {
  try {
    localStorage.setItem('viewer-sidebar-width', width.toString());
  } catch (error) {
    console.warn('[saveSidebarWidth] Failed to save sidebar width', error);
  }
}

function loadSidebarWidth() {
  try {
    const saved = localStorage.getItem('viewer-sidebar-width');
    if (saved) {
      const width = parseInt(saved, 10);
      if (!isNaN(width) && width >= 200 && width <= 600) {
        return width;
      }
    }
  } catch (error) {
    console.warn('[loadSidebarWidth] Failed to load sidebar width', error);
  }
  return null;
}

async function bootstrapDemoPayload() {
  const demoPayload = {
    generated_at: new Date().toISOString(),
    entries: [
      {
        slug: "scripts_commandview",
        options: [
          {
            slug: "scripts_commandview",
            label: "scripts_commandview (sample)",
            relative_path:
              "index_scan/repo_studios__command_center__scripts_index/scripts_commandview_20251105-2049.json",
          },
        ],
      },
    ],
  };

  setEntries(demoPayload.entries);
  updateStatus("Demo payload loaded (replace with real selector data).");
}

function setEntries(entries) {
  console.log("[setEntries] Called with entries:", entries);
  persistActiveSelectionMemory();
  clearActiveViewSelection({ silent: true, suppressStatus: true });
  const previousOption = state.activeOption;
  state.entries = Array.isArray(entries) ? entries : [];
  console.log("[setEntries] State entries set to:", state.entries);
  renderSelector();
  const nextOption = findMatchingOption(state.entries, previousOption) ?? state.entries[0]?.options?.[0];
  console.log("[setEntries] Next option to select:", nextOption);
  if (nextOption) {
    void selectOption(nextOption);
  } else {
    state.activeOption = null;
    state.levels = null;
    state.normalizedData = null;
    state.levelSelections.rootId = null;
    state.levelSelections.domainId = null;
    state.levelSelections.moduleId = null;
    state.levelSelections.functionId = null;
    updateLevelButtonsState();
    renderLevelSidebar();
    renderBreadcrumb();
    updateStatus("No CommandView artifacts available.");
    clearDiagram();
    renderViewPacks();
    renderViewTabs();
  }
}

async function bootstrap() {
  console.log('[bootstrap] Starting viewer bootstrap...');
  try {
    console.log('[bootstrap] Step 1: initializeMermaid');
    initializeMermaid();
    console.log('[bootstrap] Step 2: initializeLevelControls');
    initializeLevelControls();
    console.log('[bootstrap] Step 3: initializeBreadcrumb');
    initializeBreadcrumb();
    console.log('[bootstrap] Step 4: renderViewTabs');
    renderViewTabs();
    console.log('[bootstrap] Step 5: renderViewPacks');
    renderViewPacks();
    console.log('[bootstrap] Step 6: wireRefresh');
    wireRefresh();
    console.log('[bootstrap] Step 7: wireExport');
    wireExport();
    console.log('[bootstrap] Step 7.5: wireUpdate');
    wireUpdate();
    console.log('[bootstrap] Step 8: wireZoomControls');
    wireZoomControls();
    console.log('[bootstrap] Step 9: initializeSidebarResize');
    initializeSidebarResize();
    console.log('[bootstrap] Step 9.5: initializeStatusPanelResize');
    initializeStatusPanelResize();
    console.log('[bootstrap] Step 10: updateStatus');
    updateStatus("Loading selector data...");
    console.log('[bootstrap] Step 11: refreshSelectorData');
    await refreshSelectorData();
    console.log('[bootstrap] Bootstrap completed successfully');
  } catch (error) {
    console.error("[bootstrap] Viewer bootstrap failed", error);
    updateStatus("Viewer bootstrap failed; check console logs.");
    // Also show error in loading overlay if still visible
    const loading = document.getElementById('loading-overlay');
    if (loading && loading.style.display !== 'none') {
      loading.innerHTML = `
        <div style="text-align: center; max-width: 600px; padding: 20px;">
          <div style="font-size: 24px; margin-bottom: 10px; color: #f48771;">⚠️</div>
          <div style="color: #f48771; font-weight: bold; margin-bottom: 10px;">Bootstrap Failed</div>
          <div style="font-size: 14px; margin-bottom: 10px;">${error.message}</div>
          <div style="font-size: 12px; color: #858585; margin-top: 20px;">
            Check browser console (F12) for details
          </div>
        </div>
      `;
    }
  }
}

console.log('[viewer.js] Setting up bootstrap trigger, readyState:', document.readyState);

if (document.readyState === "loading") {
  console.log('[viewer.js] Document still loading, adding DOMContentLoaded listener');
  document.addEventListener("DOMContentLoaded", () => {
    console.log('[viewer.js] DOMContentLoaded event fired, calling bootstrap');
    void bootstrap();
  });
} else {
  console.log('[viewer.js] Document already loaded, calling bootstrap immediately');
  void bootstrap();
}

console.log('[viewer.js] Script loading completed');

export const __test__ = {
  createModuleRecord,
  evaluateLayerTransition,
  buildModuleImportEdges,
  buildModuleExportSummary,
  createFunctionRecord,
  normalizeDecorators,
  normalizeDecoratorDetails,
  normalizeDynamicCode,
  setNormalizedDataForTest(normalized) {
    state.normalizedData = normalized ?? null;
    state.levels = normalized?.levels ?? null;
  },
  setLevelSelectionsForTest(selections) {
    if (!selections || typeof selections !== "object") {
      return;
    }
    state.levelSelections = {
      ...state.levelSelections,
      ...selections,
    };
  },
  resetViewStateForTest() {
    state.inventoryPayload = null;
    state.inventoryUrl = null;
    state.screeningPayload = null;
    state.screeningUrl = null;
    state.normalizedData = null;
    state.levels = null;
    state.levelSelections = {
      rootId: null,
      domainId: null,
      moduleId: null,
      functionId: null,
    };
    state.diagramDefinition = null;
    state.statusMessage = "";
    state.statusDetails = [];
  },
  buildLayerArchitectureValidationViewDefinitionForTest: buildLayerArchitectureValidationViewDefinition,
  buildModuleApiSurfaceForTest: buildModuleApiSurface,
  buildExportContractMatrixViewDefinitionForTest: buildExportContractMatrixViewDefinition,
  buildExternalVsInternalDependencyMapViewDefinitionForTest: buildExternalVsInternalDependencyMapViewDefinition,
  buildCallbackRegistrationMapViewDefinitionForTest: buildCallbackRegistrationMapViewDefinition,
  buildDynamicCodeWatchlistViewDefinitionForTest: buildDynamicCodeWatchlistViewDefinition,
  buildEntrypointTraceDiagramViewDefinitionForTest: buildEntrypointTraceDiagramViewDefinition,
  buildClassInheritanceHierarchyViewDefinitionForTest: buildClassInheritanceHierarchyViewDefinition,
  buildMethodCallChainViewDefinitionForTest: buildMethodCallChainViewDefinition,
  buildPublicVsPrivateApiViewDefinitionForTest: buildPublicVsPrivateApiViewDefinition,
  buildTestCoverageMappingViewDefinitionForTest: buildTestCoverageMappingViewDefinition,
  buildGitChurnRiskMapViewDefinitionForTest: buildGitChurnRiskMapViewDefinition,
  buildDeadCodeDetectionViewDefinitionForTest: buildDeadCodeDetectionViewDefinition,
  buildCyclomaticComplexityMapViewDefinitionForTest: buildCyclomaticComplexityMapViewDefinition,
  buildIoEffectsViewDefinitionForTest: buildIoEffectsViewDefinition,
  buildExceptionFlowViewDefinitionForTest: buildExceptionFlowViewDefinition,
  buildGlobalVariableUsageViewDefinitionForTest: buildGlobalVariableUsageViewDefinition,
  resolveTestCoverageScopeForTest(modules, functions, selections) {
    return resolveTestCoverageScope(modules, functions, selections);
  },
  resolveGitChurnScopeForTest(modules, selections) {
    return resolveGitChurnScope(modules, selections);
  },
  resolveDeadCodeScopeForTest(modules, selections) {
    return resolveDeadCodeScope(modules, selections);
  },
  moduleHasCoverageTelemetryForTest: moduleHasCoverageTelemetry,
  moduleHasGitChurnTelemetryForTest: moduleHasGitChurnTelemetry,
  moduleHasDeadCodeTelemetryForTest: moduleHasDeadCodeTelemetry,
  hasDynamicCodeDataForTest: hasDynamicCodeData,
  normalizeEntrypointSignalsForTest: normalizeEntrypointSignals,
  populateEntrypointCandidatesForTest(modules, functions, callGraph) {
    return populateEntrypointCandidates(modules, functions, callGraph);
  },
  createClassRecord,
  finalizeClassInheritanceForTest(classMap) {
    if (!(classMap instanceof Map)) {
      throw new Error("classMap must be a Map instance");
    }
    resolveClassInheritanceRelationships(classMap);
    return buildClassInheritanceIndex(classMap);
  },
};
