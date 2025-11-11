from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
DEPENDENCY_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "module_dependency_graph.js"
)
CALL_GRAPH_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "function_call_graph.js"
)
EXPORT_MATRIX_MODULE_PATH = (
  REPO_STUDIOS_ROOT
  / "command_center"
  / "viewer"
  / "ui"
  / "builders"
  / "export_contract_matrix.js"
)
EXTERNAL_DEPENDENCY_MODULE_PATH = (
  REPO_STUDIOS_ROOT
  / "command_center"
  / "viewer"
  / "ui"
  / "builders"
  / "external_vs_internal_dependency_map.js"
)
LAYER_ARCHITECTURE_MODULE_PATH = (
  REPO_STUDIOS_ROOT
  / "command_center"
  / "viewer"
  / "ui"
  / "builders"
  / "layer_architecture_validation.js"
)

if not DEPENDENCY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected module dependency graph builder at {DEPENDENCY_MODULE_PATH}")

if not CALL_GRAPH_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function call graph builder at {CALL_GRAPH_MODULE_PATH}")

if not EXPORT_MATRIX_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
  raise AssertionError(f"Expected export contract matrix builder at {EXPORT_MATRIX_MODULE_PATH}")

if not LAYER_ARCHITECTURE_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected layer architecture validation builder at {LAYER_ARCHITECTURE_MODULE_PATH}")

if not EXTERNAL_DEPENDENCY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected external vs internal dependency map builder at {EXTERNAL_DEPENDENCY_MODULE_PATH}")


@pytest.fixture(scope="module", autouse=True)
def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Node.js runtime is required for viewer builder tests: {exc}")


def _run_node_module(script: str) -> dict[str, object]:
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.stderr.strip():
        pytest.fail(f"Node.js script wrote to stderr: {result.stderr}")
    return json.loads(result.stdout.strip())


def test_dependency_pack_view_coexists_with_function_call_graph() -> None:
    script = f"""
import {{ buildModuleDependencyGraphDiagram }} from "{DEPENDENCY_MODULE_PATH.as_uri()}";
import {{ buildFunctionCallGraphDiagram }} from "{CALL_GRAPH_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "beta.helpers", category: "internal", unused: false, functions: ["alpha.core::bootstrap"] }},
    ],
    functions: ["alpha.core::bootstrap", "alpha.core::render"],
  }}],
  ["beta.helpers", {{
    importEdges: [
      {{ target: "alpha.core", category: "internal", unused: false, functions: ["beta.helpers::support"] }},
    ],
    functions: ["beta.helpers::support"],
  }}],
]);

const functions = new Map([
  ["alpha.core::bootstrap", {{ name: "bootstrap", moduleId: "alpha.core", metrics: {{ lineCount: 40, coverage: 0.8 }} }}],
  ["alpha.core::render", {{ name: "render", moduleId: "alpha.core", metrics: {{ lineCount: 20, coverage: 0.6 }} }}],
  ["beta.helpers::support", {{ name: "support", moduleId: "beta.helpers", metrics: {{ lineCount: 10 }} }}],
]);

const callGraph = new Map([
  ["alpha.core::bootstrap", ["alpha.core::render"]],
  ["alpha.core::render", []],
  ["beta.helpers::support", []],
]);

const dependencySummaries = new Map([
  ["alpha.core", {{ internal: {{ count: 1, modules: ["beta.helpers"] }} }}],
  ["beta.helpers", {{ internal: {{ count: 1, modules: ["alpha.core"] }} }}],
]);

const dependencyFirst = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});
const callGraphFirst = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "alpha.core" }});
const dependencySecond = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});
const callGraphSecond = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "alpha.core" }});

console.log(JSON.stringify({{
  dependencyDefinitionStable: dependencyFirst.definition === dependencySecond.definition,
  dependencyStatusStable: dependencyFirst.statusMessage === dependencySecond.statusMessage,
  callGraphDefinitionStable: callGraphFirst.definition === callGraphSecond.definition,
  callGraphStatusStable: callGraphFirst.statusMessage === callGraphSecond.statusMessage,
  dependencyLabel: dependencyFirst.label,
  callGraphLabel: callGraphFirst.label,
}}));
"""
    payload = _run_node_module(script)

    assert payload["dependencyDefinitionStable"] is True
    assert payload["dependencyStatusStable"] is True
    assert payload["callGraphDefinitionStable"] is True
    assert payload["callGraphStatusStable"] is True
    assert "Dependency" in payload["dependencyLabel"]
    assert "Function Call Graph" in payload["callGraphLabel"]


def test_export_contract_matrix_coexists_with_dependency_view() -> None:
    script = f"""
import {{ buildModuleDependencyGraphDiagram }} from "{DEPENDENCY_MODULE_PATH.as_uri()}";
import {{ buildExportContractMatrixDiagram }} from "{EXPORT_MATRIX_MODULE_PATH.as_uri()}";

const originalLog = console.log;
console.log = () => {{}};

const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "beta.helpers", category: "internal", unused: false, functions: ["alpha.core::bootstrap"] }},
    ],
    functions: ["alpha.core::bootstrap", "alpha.core::render"],
    exportSummary: {{
      declared: ["bootstrap", "render", "CONFIG"],
      counts: {{ declared: 3, local: 3, functions: 2, classes: 0, globals: 1, reexports: 0, missing: 0 }},
      resolved: [
        {{ symbol: "bootstrap", kind: "function", defined: true, signature: "def bootstrap()", lineno: 10 }},
        {{ symbol: "render", kind: "function", defined: true, signature: "def render()", lineno: 28 }},
        {{ symbol: "CONFIG", kind: "global", defined: true, valueKind: "dict", lineno: 5 }},
      ],
    }},
  }}],
  ["beta.helpers", {{
    importEdges: [
      {{ target: "alpha.core", category: "internal", unused: false, functions: ["beta.helpers::support"] }},
    ],

    functions: ["beta.helpers::support"],
    exportSummary: {{
      declared: ["support", "MISSING_UTIL"],
      counts: {{ declared: 2, local: 1, functions: 1, classes: 0, globals: 0, reexports: 0, missing: 1 }},
      missing: ["MISSING_UTIL"],
      resolved: [
        {{ symbol: "support", kind: "function", defined: true, signature: "def support()", lineno: 15 }},
        {{ symbol: "MISSING_UTIL", kind: "missing", defined: false }},
      ],
    }},
  }}],
]);

const dependencySummaries = new Map([
  ["alpha.core", {{ internal: {{ count: 1, modules: ["beta.helpers"] }} }}],
  ["beta.helpers", {{ internal: {{ count: 1, modules: ["alpha.core"] }} }}],
]);

const exportFirst = buildExportContractMatrixDiagram(modules, {{ scopeDescription: "repository scope" }});
const dependencyFirst = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});
const exportSecond = buildExportContractMatrixDiagram(modules, {{ scopeDescription: "repository scope" }});
const dependencySecond = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});

console.log = originalLog;

console.log(JSON.stringify({{
  exportDefinitionStable: exportFirst.definition === exportSecond.definition,
  exportStatusStable: exportFirst.statusMessage === exportSecond.statusMessage,
  exportLabel: exportFirst.label,
  exportStats: exportFirst.stats,
  dependencyDefinitionStable: dependencyFirst.definition === dependencySecond.definition,
  dependencyStatusStable: dependencyFirst.statusMessage === dependencySecond.statusMessage,
  dependencyLabel: dependencyFirst.label,
}}));
"""

    payload = _run_node_module(script)

    assert payload["exportDefinitionStable"] is True
    assert payload["exportStatusStable"] is True
    assert payload["dependencyDefinitionStable"] is True
    assert payload["dependencyStatusStable"] is True
    assert "Export Contract Matrix" in payload["exportLabel"]
    assert "Dependency" in payload["dependencyLabel"]
    assert payload["exportStats"]["modules"] == 2
    assert payload["exportStats"]["missingSymbols"] == 1


def test_external_dependency_map_coexists_with_dependency_view() -> None:
    script = f"""
import {{ buildModuleDependencyGraphDiagram }} from "{DEPENDENCY_MODULE_PATH.as_uri()}";
import {{ buildExternalVsInternalDependencyMapDiagram }} from "{EXTERNAL_DEPENDENCY_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "beta.utils", category: "internal", unused: false, functions: ["alpha.core::bootstrap"] }},
      {{ target: "requests", category: "third_party", unused: false, functions: ["alpha.core::bootstrap"] }},
    ],
  }}],
  ["beta.utils", {{
    importEdges: [
      {{ target: "alpha.core", category: "internal", unused: false, functions: ["beta.utils::assist"] }},
    ],
  }}],
]);

const dependencySummaries = new Map([
  ["alpha.core", {{ internal: {{ count: 1, modules: ["beta.utils"] }}, third_party: {{ count: 1, modules: ["requests"] }} }}],
  ["beta.utils", {{ internal: {{ count: 1, modules: ["alpha.core"] }} }}],
]);

const dependencyFirst = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});
const externalFirst = buildExternalVsInternalDependencyMapDiagram(modules, {{ scopeDescription: "repository" }});
const dependencySecond = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});
const externalSecond = buildExternalVsInternalDependencyMapDiagram(modules, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  dependencyDefinitionStable: dependencyFirst.definition === dependencySecond.definition,
  dependencyStatusStable: dependencyFirst.statusMessage === dependencySecond.statusMessage,
  externalDefinitionStable: externalFirst.definition === externalSecond.definition,
  externalStatusStable: externalFirst.statusMessage === externalSecond.statusMessage,
  externalStats: externalFirst.stats,
  dependencyLabel: dependencyFirst.label,
  externalLabel: externalFirst.label,
}}));
"""

    payload = _run_node_module(script)

    assert payload["dependencyDefinitionStable"] is True
    assert payload["dependencyStatusStable"] is True
    assert payload["externalDefinitionStable"] is True
    assert payload["externalStatusStable"] is True
    assert "Module Dependency Graph" in payload["dependencyLabel"]
    assert "External vs Internal Dependency Map" in payload["externalLabel"]
    assert payload["externalStats"]["modules"] == 2
    assert payload["externalStats"]["externalPackages"] == 1


def test_layer_architecture_validation_coexists_with_dependency_view() -> None:
    script = f"""
import {{ buildModuleDependencyGraphDiagram }} from "{DEPENDENCY_MODULE_PATH.as_uri()}";
import {{ buildLayerArchitectureValidationDiagram }} from "{LAYER_ARCHITECTURE_MODULE_PATH.as_uri()}";

const layerIndexById = {{
  producers: 0,
  consumers: 1,
  aggregators: 2,
  orchestrators: 3,
  summarizers: 4,
  unclassified: 99,
}};

const adjacencyAllowed = {{
  producers: new Set(["producers", "consumers"]),
  consumers: new Set(["consumers", "aggregators"]),
  aggregators: new Set(["aggregators", "orchestrators"]),
  orchestrators: new Set(["orchestrators", "summarizers"]),
  summarizers: new Set(["summarizers"]),
}};

const evaluateLayerTransition = (sourceLayerId, targetLayerId) => {{
  const source = typeof sourceLayerId === "string" ? sourceLayerId : "unclassified";
  const target = typeof targetLayerId === "string" ? targetLayerId : "unclassified";
  if (source === "unclassified" || target === "unclassified") {{
    return {{ allowed: true, classification: "unclassified", reason: "Unclassified module passthrough." }};
  }}
  const sourceIndex = layerIndexById[source] ?? layerIndexById.unclassified;
  const targetIndex = layerIndexById[target] ?? layerIndexById.unclassified;
  const delta = targetIndex - sourceIndex;
  let classification;
  if (delta === 0) {{
    classification = "peer";
  }} else if (delta === 1) {{
    classification = "forward";
  }} else if (delta > 1) {{
    classification = "skip";
  }} else {{
    classification = "backward";
  }}
  const allowed = adjacencyAllowed[source]?.has(target) ?? false;
  const reason = allowed ? "Allowed by adjacency defaults." : "Violates adjacency defaults.";
  return {{ allowed, classification, reason }};
}};

const modules = new Map([
  ["scripts.producers.generate_inventory", {{
    moduleId: "scripts.producers.generate_inventory",
    layerTier: "producers",
    layerLabel: "Producers",
    layerIndex: 0,
    importEdges: [],
  }}],
  ["scripts.consumers.enrich_inventory", {{
    moduleId: "scripts.consumers.enrich_inventory",
    layerTier: "consumers",
    layerLabel: "Consumers",
    layerIndex: 1,
    importEdges: [
      {{ target: "scripts.producers.generate_inventory", category: "internal", unused: false }},
    ],
  }}],
  ["scripts.aggregators.aggregate_signal", {{
    moduleId: "scripts.aggregators.aggregate_signal",
    layerTier: "aggregators",
    layerLabel: "Aggregators",
    layerIndex: 2,
    importEdges: [
      {{ target: "scripts.producers.generate_inventory", category: "internal", unused: false }},
      {{ target: "scripts.consumers.enrich_inventory", category: "internal", unused: false }},
      {{ target: "scripts.orchestrators.run_pipeline", category: "internal", unused: false }},
      {{ target: "scripts.summarizers.publish_summary", category: "internal", unused: true }},
    ],
    dependencySummary: {{ violations: {{ layers: "Inventory flagged aggregator layer violations." }} }},
  }}],
  ["scripts.orchestrators.run_pipeline", {{
    moduleId: "scripts.orchestrators.run_pipeline",
    layerTier: "orchestrators",
    layerLabel: "Orchestrators",
    layerIndex: 3,
    importEdges: [
      {{ target: "scripts.aggregators.aggregate_signal", category: "internal", unused: false }},
    ],
  }}],
  ["scripts.summarizers.publish_summary", {{
    moduleId: "scripts.summarizers.publish_summary",
    layerTier: "summarizers",
    layerLabel: "Summarizers",
    layerIndex: 4,
    importEdges: [],
  }}],
  ["docs.automation.generate_docs_index", {{
    moduleId: "docs.automation.generate_docs_index",
    layerTier: "unclassified",
    layerLabel: "Unclassified",
    layerIndex: 99,
    importEdges: [
      {{ target: "scripts.producers.generate_inventory", category: "internal", unused: false }},
    ],
  }}],
]);

const dependencySummaries = new Map([
  ["scripts.producers.generate_inventory", {{ internal: {{ count: 0 }} }}],
  ["scripts.consumers.enrich_inventory", {{ internal: {{ count: 1, modules: ["scripts.producers.generate_inventory"] }} }}],
  ["scripts.aggregators.aggregate_signal", {{ internal: {{ count: 3, modules: ["scripts.producers.generate_inventory", "scripts.consumers.enrich_inventory", "scripts.orchestrators.run_pipeline"] }} }}],
  ["scripts.orchestrators.run_pipeline", {{ internal: {{ count: 1, modules: ["scripts.aggregators.aggregate_signal"] }} }}],
  ["scripts.summarizers.publish_summary", {{ internal: {{ count: 0 }} }}],
  ["docs.automation.generate_docs_index", {{ internal: {{ count: 1, modules: ["scripts.producers.generate_inventory"] }} }}],
]);

const layerOptions = {{
  scopeDescription: "repository",
  evaluateLayerTransition,
}};

const layerFirst = buildLayerArchitectureValidationDiagram(modules, layerOptions);
const dependencyFirst = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});
const layerSecond = buildLayerArchitectureValidationDiagram(modules, layerOptions);
const dependencySecond = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});

console.log(JSON.stringify({{
  layerDefinitionStable: layerFirst.definition === layerSecond.definition,
  layerStatusStable: layerFirst.statusMessage === layerSecond.statusMessage,
  dependencyDefinitionStable: dependencyFirst.definition === dependencySecond.definition,
  dependencyStatusStable: dependencyFirst.statusMessage === dependencySecond.statusMessage,
  layerLabel: layerFirst.label,
  violationEdges: layerFirst.stats?.violationEdges ?? null,
}}));
"""

    payload = _run_node_module(script)

    assert payload["layerDefinitionStable"] is True
    assert payload["layerStatusStable"] is True
    assert payload["dependencyDefinitionStable"] is True
    assert payload["dependencyStatusStable"] is True
    assert "Layer Architecture Validation" in payload["layerLabel"]
    assert payload["violationEdges"] == 5
