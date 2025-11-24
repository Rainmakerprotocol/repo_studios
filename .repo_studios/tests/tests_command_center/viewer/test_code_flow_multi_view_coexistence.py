from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
CALL_GRAPH_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "function_call_graph.js"
ENTRYPOINT_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "entrypoint_trace_diagram.js"
)
CLASS_INHERITANCE_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "class_inheritance_hierarchy.js"
)
METHOD_CHAIN_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "method_call_chain.js"
INVENTORY_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "function_inventory_overview.js"
)

if not CALL_GRAPH_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function call graph builder module at {CALL_GRAPH_MODULE_PATH}")

if not ENTRYPOINT_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected entrypoint trace builder module at {ENTRYPOINT_MODULE_PATH}")

if not INVENTORY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function inventory builder module at {INVENTORY_MODULE_PATH}")

if not METHOD_CHAIN_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected method call chain builder module at {METHOD_CHAIN_MODULE_PATH}")


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


def test_code_flow_call_graph_coexists_with_health_overview() -> None:
    script = f"""
import {{ buildFunctionCallGraphDiagram }} from "{CALL_GRAPH_MODULE_PATH.as_uri()}";
import {{ buildEntrypointTraceDiagram }} from "{ENTRYPOINT_MODULE_PATH.as_uri()}";
import {{ buildClassInheritanceHierarchyDiagram }} from "{CLASS_INHERITANCE_MODULE_PATH.as_uri()}";
import {{ buildFunctionInventoryOverviewDiagram }} from "{INVENTORY_MODULE_PATH.as_uri()}";
import {{ buildMethodCallChainDiagram }} from "{METHOD_CHAIN_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["sample.module", {{ moduleId: "sample.module", functions: ["sample.module::main", "sample.module::helper"] }}],
  ["orchestrator.module", {{ moduleId: "orchestrator.module", functions: ["orchestrator.module::entry"] }}],
  ["workflow.pipeline", {{ moduleId: "workflow.pipeline", functions: [
    "workflow.pipeline::Coordinator.start",
    "workflow.pipeline::Coordinator.prepare",
    "workflow.pipeline::Coordinator.execute"
  ] }}],
  ["notifications.bridge", {{ moduleId: "notifications.bridge", functions: [
    "notifications.bridge::Notifier.dispatch",
    "notifications.bridge::Notifier.logDelivery"
  ] }}],
]);
const functions = new Map([
  ["sample.module::main", {{
    name: "main",
    moduleId: "sample.module",
    metrics: {{ lineCount: 48, coverage: 0.82 }},
    docstringQuality: {{ exists: true }},
    typeHintCoverage: 0.75,
    todoTags: 1,
  }}],
  ["sample.module::helper", {{
    name: "helper",
    moduleId: "sample.module",
    metrics: {{ lineCount: 16, coverage: 0.65 }},
    docstringQuality: {{ exists: false }},
    annotationCoverage: 0.4,
    todoTags: 0,
  }}],
  ["orchestrator.module::entry", {{
    name: "entry",
    moduleId: "orchestrator.module",
    metrics: {{ coverage: 0.9, cyclomaticComplexity: 5 }},
    calls: ["sample.module::main"],
  }}],
  ["workflow.pipeline::Coordinator.start", {{
    name: "Coordinator.start",
    moduleId: "workflow.pipeline",
    calls: ["workflow.pipeline::Coordinator.prepare", "notifications.bridge::Notifier.dispatch"],
    metrics: {{ coverage: 0.81 }},
  }}],
  ["workflow.pipeline::Coordinator.prepare", {{
    name: "Coordinator.prepare",
    moduleId: "workflow.pipeline",
    calls: ["workflow.pipeline::Coordinator.execute"],
    metrics: {{ coverage: 0.78 }},
  }}],
  ["workflow.pipeline::Coordinator.execute", {{
    name: "Coordinator.execute",
    moduleId: "workflow.pipeline",
    calls: ["notifications.bridge::Notifier.logDelivery"],
    metrics: {{ coverage: 0.74 }},
  }}],
  ["notifications.bridge::Notifier.dispatch", {{
    name: "Notifier.dispatch",
    moduleId: "notifications.bridge",
    calls: ["notifications.bridge::Notifier.logDelivery"],
    metrics: {{ coverage: 0.9 }},
  }}],
  ["notifications.bridge::Notifier.logDelivery", {{
    name: "Notifier.logDelivery",
    moduleId: "notifications.bridge",
    calls: [],
    metrics: {{ coverage: 0.92 }},
  }}],
]);
const callGraph = new Map([
  ["sample.module::main", ["sample.module::helper"]],
  ["sample.module::helper", []],
  ["orchestrator.module::entry", ["sample.module::main"]],
  ["workflow.pipeline::Coordinator.start", ["workflow.pipeline::Coordinator.prepare", "notifications.bridge::Notifier.dispatch"]],
  ["workflow.pipeline::Coordinator.prepare", ["workflow.pipeline::Coordinator.execute"]],
  ["workflow.pipeline::Coordinator.execute", ["notifications.bridge::Notifier.logDelivery"]],
  ["notifications.bridge::Notifier.dispatch", ["notifications.bridge::Notifier.logDelivery"]],
]);

const entrypoints = new Map([
  ["orchestrator.module", {{
    moduleId: "orchestrator.module",
    hasMainGuard: true,
    cliParser: false,
    candidates: [
      {{ id: "orchestrator.module::entry", name: "entry", moduleId: "orchestrator.module", reason: "main-guard-name-match", outboundCount: 1, inboundCount: 0 }},
    ],
  }}],
]);

const classes = new Map([
  ["sample.module.Base", {{
    id: "sample.module.Base",
    moduleId: "sample.module",
    methodCount: 1,
    attributeCount: 0,
    resolvedBases: [],
    derivedClassIds: ["sample.module.Controller"],
    docstringQuality: {{ exists: true }},
  }}],
  ["sample.module.Controller", {{
    id: "sample.module.Controller",
    moduleId: "sample.module",
    methodCount: 2,
    attributeCount: 1,
    resolvedBases: [{{ classId: "sample.module.Base", matchType: "local", normalized: "sample.module.Base" }}],
    derivedClassIds: ["orchestrator.module.Workflow"],
    docstringQuality: {{ exists: false }},
  }}],
  ["orchestrator.module.Workflow", {{
    id: "orchestrator.module.Workflow",
    moduleId: "orchestrator.module",
    methodCount: 1,
    attributeCount: 0,
    resolvedBases: [
      {{ classId: "sample.module.Controller", matchType: "project", normalized: "sample.module.Controller" }},
      {{ raw: "framework.ExternalBase", normalized: "framework.ExternalBase", matchType: "external" }},
    ],
    derivedClassIds: [],
    docstringQuality: {{ exists: true }},
  }}],
]);

const overviewFirst = buildFunctionInventoryOverviewDiagram(modules, functions, {{ viewLabel: "Health · Overview" }});
const callGraphResult = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "sample.module", focusFunctionId: "sample.module::main", viewLabel: "Code Flow · Function Call Graph" }});
const entrypointTrace = buildEntrypointTraceDiagram(modules, functions, callGraph, entrypoints, {{ scopeDescription: "repository" }});
const classHierarchy = buildClassInheritanceHierarchyDiagram(classes, {{
  primaryClassIds: new Set(["orchestrator.module.Workflow"]),
  scopeDescription: "repository",
}});
const callGraphSecond = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "sample.module", focusFunctionId: "sample.module::main", viewLabel: "Code Flow · Function Call Graph" }});
const overviewSecond = buildFunctionInventoryOverviewDiagram(modules, functions, {{ viewLabel: "Health · Overview" }});
const inheritanceFirst = buildClassInheritanceHierarchyDiagram(classes, {{
  primaryClassIds: new Set(["sample.module.Controller"]),
  scopeDescription: "repository",
}});
const inheritanceSecond = buildClassInheritanceHierarchyDiagram(classes, {{
  primaryClassIds: new Set(["sample.module.Controller"]),
  scopeDescription: "repository",
}});
const methodScope = new Set([
  "workflow.pipeline::Coordinator.start",
  "workflow.pipeline::Coordinator.prepare",
  "workflow.pipeline::Coordinator.execute",
  "notifications.bridge::Notifier.dispatch",
  "notifications.bridge::Notifier.logDelivery",
]);
const methodChainFirst = buildMethodCallChainDiagram(modules, functions, callGraph, {{
  scopeDescription: "workflow.pipeline",
  focusFunctionId: "workflow.pipeline::Coordinator.start",
  allowedFunctionIds: methodScope,
}});
const methodChainSecond = buildMethodCallChainDiagram(modules, functions, callGraph, {{
  scopeDescription: "workflow.pipeline",
  focusFunctionId: "workflow.pipeline::Coordinator.start",
  allowedFunctionIds: methodScope,
}});

console.log(JSON.stringify({{
  overviewFirstDefinition: overviewFirst.definition,
  overviewSecondDefinition: overviewSecond.definition,
  overviewFirstStatus: overviewFirst.statusMessage,
  overviewSecondStatus: overviewSecond.statusMessage,
  overviewFirstStats: overviewFirst.stats,
  overviewSecondStats: overviewSecond.stats,
  callGraphDefinition: callGraphResult.definition,
  callGraphStatus: callGraphResult.statusMessage,
  callGraphLabel: callGraphResult.label,
  callGraphNodeCount: callGraphResult.nodeCount,
  callGraphEdgeCount: callGraphResult.edgeCount,
  callGraphDefinitionAfterEntrypoint: callGraphSecond.definition,
  entrypointDefinition: entrypointTrace.definition,
  entrypointStatus: entrypointTrace.statusMessage,
  entrypointStats: entrypointTrace.stats,
  classHierarchyDefinition: classHierarchy.definition,
  classHierarchyStatus: classHierarchy.statusMessage,
  inheritanceDefinition: inheritanceFirst.definition,
  inheritanceStatus: inheritanceFirst.statusMessage,
  inheritanceStats: inheritanceFirst.stats,
  inheritanceDefinitionAfterCallGraph: inheritanceSecond.definition,
  methodChainDefinition: methodChainFirst.definition,
  methodChainStatus: methodChainFirst.statusMessage,
  methodChainStats: methodChainFirst.stats,
  methodChainDefinitionAfterInheritance: methodChainSecond.definition,
}}));
"""
    payload = _run_node_module(script)

    assert payload["overviewFirstDefinition"] == payload["overviewSecondDefinition"]
    assert payload["overviewFirstStatus"] == payload["overviewSecondStatus"]
    assert payload["overviewFirstStats"] == payload["overviewSecondStats"]
    assert payload["callGraphDefinition"].startswith("graph TD")
    assert "sample_module__main" in payload["callGraphDefinition"]
    assert "sample_module__helper" in payload["callGraphDefinition"]
    assert "Rendered Function Call Graph for sample.module" in payload["callGraphStatus"]
    call_graph_label = payload.get("callGraphLabel")
    assert isinstance(call_graph_label, str)
    assert "Code Flow" in call_graph_label
    assert "Function Call Graph" in call_graph_label
    assert payload["callGraphNodeCount"] == 2
    assert payload["callGraphEdgeCount"] == 1
    assert payload["callGraphDefinition"] == payload["callGraphDefinitionAfterEntrypoint"]

    entrypoint_definition = payload["entrypointDefinition"]
    assert isinstance(entrypoint_definition, str)
    assert entrypoint_definition.startswith("graph TD")
    assert "orchestrator_module__entry" in entrypoint_definition
    assert "sample_module__main" in entrypoint_definition

    entrypoint_status = payload["entrypointStatus"]
    assert "Rendered Entrypoint Trace for repository" in entrypoint_status

    entrypoint_stats = payload["entrypointStats"]
    assert entrypoint_stats["entrypoints"] == 1
    assert entrypoint_stats["downstreamFunctions"] >= 1

    class_hierarchy_definition = payload["classHierarchyDefinition"]
    assert isinstance(class_hierarchy_definition, str)
    assert class_hierarchy_definition.startswith("graph TD")
    assert "orchestrator_module_Workflow" in class_hierarchy_definition
    assert "sample_module_Controller" in class_hierarchy_definition

    class_hierarchy_status = payload["classHierarchyStatus"]
    assert "Rendered Class Inheritance Hierarchy" in class_hierarchy_status

    inheritance_definition = payload["inheritanceDefinition"]
    assert isinstance(inheritance_definition, str)
    assert inheritance_definition.startswith("graph TD")
    assert "sample_module_Controller" in inheritance_definition
    assert "sample_module_Base" in inheritance_definition
    assert inheritance_definition == payload["inheritanceDefinitionAfterCallGraph"]

    inheritance_status = payload["inheritanceStatus"]
    assert inheritance_status.startswith("Rendered Class Inheritance Hierarchy")

    inheritance_stats = payload["inheritanceStats"]
    assert inheritance_stats["classCount"] == 3
    assert inheritance_stats["moduleCount"] == 2

    method_chain_definition = payload["methodChainDefinition"]
    assert isinstance(method_chain_definition, str)
    assert method_chain_definition.startswith("sequenceDiagram")
    assert "workflow_pipeline_Coordinator" in method_chain_definition
    assert "notifications_bridge_Notifier" in method_chain_definition
    assert payload["methodChainDefinition"] == payload["methodChainDefinitionAfterInheritance"]

    method_chain_status = payload["methodChainStatus"]
    assert "Rendered Method Call Chain for workflow.pipeline" in method_chain_status

    method_chain_stats = payload["methodChainStats"]
    assert method_chain_stats == {
        "startMethod": "workflow.pipeline :: Coordinator.start",
        "methodCount": 5,
        "classCount": 2,
        "depth": 2,
        "edgeCount": 5,
        "moduleCount": 2,
        "truncated": False,
    }
