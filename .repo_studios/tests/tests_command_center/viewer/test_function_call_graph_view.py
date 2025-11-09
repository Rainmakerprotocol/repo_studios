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

if not CALL_GRAPH_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function call graph builder module at {CALL_GRAPH_MODULE_PATH}")


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


def test_function_call_graph_requires_modules() -> None:
    script = f"""
import {{ buildFunctionCallGraphDiagram }} from "{CALL_GRAPH_MODULE_PATH.as_uri()}";
const result = buildFunctionCallGraphDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert payload["message"].startswith("No modules recorded")


def test_function_call_graph_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildFunctionCallGraphDiagram }} from "{CALL_GRAPH_MODULE_PATH.as_uri()}";
const modules = new Map([
  ["alpha.module", {{ functions: ["alpha.module::f1", "alpha.module::f2"] }}],
  ["beta.module", {{ functions: ["beta.module::g1"] }}],
]);
const functions = new Map([
  ["alpha.module::f1", {{ name: "f1", moduleId: "alpha.module", metrics: {{ lineCount: 25, coverage: 0.75 }} }}],
  ["alpha.module::f2", {{ name: "f2", moduleId: "alpha.module", metrics: {{ lineCount: 30, coverage: 0.9 }} }}],
  ["beta.module::g1", {{ name: "g1", moduleId: "beta.module", metrics: {{ lineCount: 10 }} }}],
]);
const callGraph = new Map([
  ["alpha.module::f1", ["alpha.module::f2"]],
  ["alpha.module::f2", []],
  ["beta.module::g1", []],
]);
const result = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "alpha.module", focusFunctionId: "alpha.module::f2", viewLabel: "Code Flow · Function Call Graph" }});
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    definition = payload.get("definition")
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "classDef local" in definition
    assert "classDef focus" in definition
    assert "alpha_module__f1" in definition
    assert "alpha_module__f2" in definition

    status_message = payload.get("statusMessage")
    assert isinstance(status_message, str)
    assert "Rendered Function Call Graph for alpha.module" in status_message
    assert payload["nodeCount"] == 2
    assert payload["edgeCount"] == 1
    label = payload.get("label")
    assert isinstance(label, str)
    assert "Code Flow" in label
    assert "Function Call Graph" in label


def test_function_call_graph_definition_is_stable_across_repeated_calls() -> None:
    script = f"""
import {{ buildFunctionCallGraphDiagram }} from "{CALL_GRAPH_MODULE_PATH.as_uri()}";
const modules = new Map([
  ["sample.module", {{ functions: ["sample.module::main", "sample.module::helper"] }}],
]);
const functions = new Map([
  ["sample.module::main", {{ name: "main", moduleId: "sample.module", metrics: {{ lineCount: 42, coverage: 0.8 }} }}],
  ["sample.module::helper", {{ name: "helper", moduleId: "sample.module", metrics: {{ lineCount: 12, coverage: 0.6 }} }}],
]);
const callGraph = new Map([
  ["sample.module::main", ["sample.module::helper"]],
  ["sample.module::helper", []],
]);
const first = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "sample.module" }});
const second = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "sample.module" }});
console.log(JSON.stringify({{
  firstDefinition: first.definition,
  secondDefinition: second.definition,
  firstStatus: first.statusMessage,
  secondStatus: second.statusMessage,
  firstNodeCount: first.nodeCount,
  secondNodeCount: second.nodeCount,
  firstEdgeCount: first.edgeCount,
  secondEdgeCount: second.edgeCount,
}}));
"""
    payload = _run_node_module(script)

    assert payload["firstDefinition"] == payload["secondDefinition"]
    assert payload["firstStatus"] == payload["secondStatus"]
    assert payload["firstNodeCount"] == payload["secondNodeCount"]
    assert payload["firstEdgeCount"] == payload["secondEdgeCount"]
