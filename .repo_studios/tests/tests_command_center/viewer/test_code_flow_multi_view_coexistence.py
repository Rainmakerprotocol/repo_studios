from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
CALL_GRAPH_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "function_call_graph.js"
)
INVENTORY_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "function_inventory_overview.js"
)

if not CALL_GRAPH_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function call graph builder module at {CALL_GRAPH_MODULE_PATH}")

if not INVENTORY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function inventory builder module at {INVENTORY_MODULE_PATH}")


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
import {{ buildFunctionInventoryOverviewDiagram }} from "{INVENTORY_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["sample.module", {{ moduleId: "sample.module", functions: ["sample.module::main", "sample.module::helper"] }}],
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
]);
const callGraph = new Map([
  ["sample.module::main", ["sample.module::helper"]],
  ["sample.module::helper", []],
]);

const overviewFirst = buildFunctionInventoryOverviewDiagram(modules, functions, {{ viewLabel: "Health · Overview" }});
const callGraphResult = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "sample.module", focusFunctionId: "sample.module::main", viewLabel: "Code Flow · Function Call Graph" }});
const overviewSecond = buildFunctionInventoryOverviewDiagram(modules, functions, {{ viewLabel: "Health · Overview" }});

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
