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

if not DEPENDENCY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected module dependency graph builder at {DEPENDENCY_MODULE_PATH}")

if not CALL_GRAPH_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function call graph builder at {CALL_GRAPH_MODULE_PATH}")


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
