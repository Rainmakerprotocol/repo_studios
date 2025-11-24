from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
COUPLING_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "cross_module_function_references.js"
)
CALL_GRAPH_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "function_call_graph.js"
IMPORT_CHAIN_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "import_chain_depth.js"

if not COUPLING_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected cross module function references builder at {COUPLING_MODULE_PATH}")

if not CALL_GRAPH_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function call graph builder module at {CALL_GRAPH_MODULE_PATH}")

if not IMPORT_CHAIN_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected import chain depth builder module at {IMPORT_CHAIN_MODULE_PATH}")


def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Node.js runtime is required for viewer builder tests: {exc}")


@pytest.fixture(scope="module", autouse=True)
def _node_runtime_guard() -> None:
    _ensure_node_runtime()


def _run_node_module(script: str) -> dict[str, object]:
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stderr.strip():
        pytest.fail(f"Node.js script wrote to stderr: {result.stderr}")
    return json.loads(result.stdout.strip())


def test_coupling_view_coexists_with_function_call_graph() -> None:
    script = f"""
import {{ buildCrossModuleFunctionReferencesDiagram }} from "{COUPLING_MODULE_PATH.as_uri()}";
import {{ buildFunctionCallGraphDiagram }} from "{CALL_GRAPH_MODULE_PATH.as_uri()}";
import {{ buildImportChainDepthDiagram }} from "{IMPORT_CHAIN_MODULE_PATH.as_uri()}";

const modules = new Map([
    ["alpha.core", {{
        moduleId: "alpha.core",
        functions: ["alpha.core::bootstrap", "alpha.core::delegate"],
        importEdges: [
            {{ target: "os", category: "standard_library" }},
            {{ target: "beta.utils", category: "internal" }},
        ],
    }}],
    ["beta.utils", {{
        moduleId: "beta.utils",
        functions: ["beta.utils::support"],
        importEdges: [
            {{ target: "alpha.core", category: "internal" }},
            {{ target: "math", category: "standard_library" }},
        ],
    }}],
    ["gamma.analytics", {{
        moduleId: "gamma.analytics",
        functions: ["gamma.analytics::evaluate"],
        importEdges: [
            {{ target: "beta.utils", category: "internal" }},
        ],
    }}],
]);

const functions = new Map([
  ["alpha.core::bootstrap", {{ moduleId: "alpha.core" }}],
  ["alpha.core::delegate", {{ moduleId: "alpha.core" }}],
  ["beta.utils::support", {{ moduleId: "beta.utils" }}],
  ["gamma.analytics::evaluate", {{ moduleId: "gamma.analytics" }}],
]);

const callGraph = new Map([
  ["alpha.core::bootstrap", ["alpha.core::delegate", "beta.utils::support"]],
  ["alpha.core::delegate", ["gamma.analytics::evaluate"]],
  ["gamma.analytics::evaluate", ["beta.utils::support"]],
  ["beta.utils::support", []],
]);

const couplingFirst = buildCrossModuleFunctionReferencesDiagram(modules, functions, callGraph, {{ scopeDescription: "repository" }});
const callGraphFirst = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "alpha.core" }});
const couplingSecond = buildCrossModuleFunctionReferencesDiagram(modules, functions, callGraph, {{ scopeDescription: "repository" }});
const callGraphSecond = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "alpha.core" }});
const importDepthFirst = buildImportChainDepthDiagram(modules, {{ scopeDescription: "repository" }});
const importDepthSecond = buildImportChainDepthDiagram(modules, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  couplingDefinitionStable: couplingFirst.definition === couplingSecond.definition,
  couplingStatusStable: couplingFirst.statusMessage === couplingSecond.statusMessage,
  callGraphDefinitionStable: callGraphFirst.definition === callGraphSecond.definition,
  callGraphStatusStable: callGraphFirst.statusMessage === callGraphSecond.statusMessage,
  couplingLabel: couplingFirst.label,
  callGraphLabel: callGraphFirst.label,
    importDepthDefinitionStable: importDepthFirst.definition === importDepthSecond.definition,
    importDepthStatusStable: importDepthFirst.statusMessage === importDepthSecond.statusMessage,
    importDepthLabel: importDepthFirst.label,
}}));
"""

    payload = _run_node_module(script)

    assert payload["couplingDefinitionStable"] is True
    assert payload["couplingStatusStable"] is True
    assert payload["callGraphDefinitionStable"] is True
    assert payload["callGraphStatusStable"] is True
    assert payload["importDepthDefinitionStable"] is True
    assert payload["importDepthStatusStable"] is True

    assert "Cross-Module" in payload["couplingLabel"]
    assert "Function Call Graph" in payload["callGraphLabel"]
    assert "Import Chain Depth" in payload["importDepthLabel"]
