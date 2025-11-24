from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "cross_module_function_references.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected cross module function references builder at {MODULE_PATH}")


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


def test_cross_module_references_renders_definition() -> None:
    script = f"""
import {{ buildCrossModuleFunctionReferencesDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{ moduleId: "alpha.core", functions: ["alpha.core::bootstrap", "alpha.core::delegate"] }}],
  ["beta.utils", {{ moduleId: "beta.utils", functions: ["beta.utils::support"] }}],
  ["gamma.analytics", {{ moduleId: "gamma.analytics", functions: ["gamma.analytics::evaluate"] }}],
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
]);

const result = buildCrossModuleFunctionReferencesDiagram(modules, functions, callGraph, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  definition: result.definition,
  statusMessage: result.statusMessage,
  stats: result.stats,
  statusDetails: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    definition = payload["definition"]
    assert isinstance(definition, str)
    assert definition.startswith("graph LR")
    assert "alpha_core" in definition
    assert "beta_utils" in definition

    status = payload["statusMessage"]
    assert "Cross-Module Function References" in status
    assert "3 edges" in status

    stats = payload["stats"]
    assert stats["crossModuleEdges"] == 3
    assert stats["crossModuleCalls"] == 3
    assert stats["modulesWithCoupling"] == 3

    details = payload["statusDetails"]
    assert isinstance(details, list) and details
    assert details[0]["type"] == "stat-summary"


def test_cross_module_references_returns_message_when_empty() -> None:
    script = f"""
import {{ buildCrossModuleFunctionReferencesDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{ moduleId: "alpha.core", functions: ["alpha.core::bootstrap", "alpha.core::delegate"] }}],
]);

const functions = new Map([
  ["alpha.core::bootstrap", {{ moduleId: "alpha.core" }}],
  ["alpha.core::delegate", {{ moduleId: "alpha.core" }}],
]);

const callGraph = new Map([
  ["alpha.core::bootstrap", ["alpha.core::delegate"]],
  ["alpha.core::delegate", []],
]);

const result = buildCrossModuleFunctionReferencesDiagram(modules, functions, callGraph, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"].startswith("No cross-module function references recorded")


def test_cross_module_references_focus_filters_edges() -> None:
    script = f"""
import {{ buildCrossModuleFunctionReferencesDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{ moduleId: "alpha.core", functions: ["alpha.core::bootstrap", "alpha.core::delegate"] }}],
  ["beta.utils", {{ moduleId: "beta.utils", functions: ["beta.utils::support"] }}],
  ["gamma.analytics", {{ moduleId: "gamma.analytics", functions: ["gamma.analytics::evaluate"] }}],
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
]);

const focusResult = buildCrossModuleFunctionReferencesDiagram(modules, functions, callGraph, {{
  scopeDescription: "gamma.analytics",
  focusModules: ["gamma.analytics"],
}});

console.log(JSON.stringify({{
  statusMessage: focusResult.statusMessage,
  stats: focusResult.stats,
}}));
"""

    payload = _run_node_module(script)

    stats = payload["stats"]
    assert stats["crossModuleEdges"] == 2
    assert stats["crossModuleCalls"] == 2

    status = payload["statusMessage"]
    assert "2 edges" in status
