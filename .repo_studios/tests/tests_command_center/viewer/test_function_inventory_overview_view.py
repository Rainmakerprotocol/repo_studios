from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "function_inventory_overview.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function inventory builder module at {MODULE_PATH}")


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


def test_function_inventory_overview_requires_modules() -> None:
    script = f"""
import {{ buildFunctionInventoryOverviewDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildFunctionInventoryOverviewDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert "message" in payload
    assert payload["message"].startswith("No modules recorded")


def test_function_inventory_overview_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildFunctionInventoryOverviewDiagram }} from "{MODULE_PATH.as_uri()}";
const modules = new Map([
  ["alpha.module", {{ moduleId: "alpha.module" }}],
  ["beta.module", {{ moduleId: "beta.module" }}],
  ["alpha.helper", {{ moduleId: "alpha.helper" }}],
]);
const functions = new Map([
  ["alpha.module::f1", {{ docstringQuality: {{ exists: true }}, typeHintCoverage: 1.0, todoTags: 0 }}],
  ["alpha.module::f2", {{ docstringQuality: {{ exists: false }}, annotationCoverage: 0.5, todoTags: 2 }}],
  ["beta.module::g1", {{ docstringQuality: {{ exists: true }}, typeHintCoverage: 0.75, todoTags: 0 }}],
    ["alpha.helper::h1", {{ docstringQuality: {{ status: "present" }}, todoTags: 1 }}],
]);
const result = buildFunctionInventoryOverviewDiagram(modules, functions, {{ viewLabel: "Custom Label" }});
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    definition = payload.get("definition")
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "Docstrings" in definition
    assert "Type Hints" in definition
    assert "TODO Hotspots" in definition
    assert "Modules: 3" in definition  # top roots aggregated

    status_message = payload.get("statusMessage")
    assert isinstance(status_message, str)
    assert "modules 3" in status_message
    assert "functions 4" in status_message

    stats = payload.get("stats")
    assert isinstance(stats, dict)
    assert stats["docstringWith"] == 3
    assert stats["docstringTotal"] == 4
    assert stats["todoFunctionCount"] == 2
    assert stats["typeCoverageSamples"] == 3
    assert stats["topRoots"][0]["root"] == "alpha"


def test_function_inventory_overview_definition_is_stable_across_repeated_calls() -> None:
    script = f"""
import {{ buildFunctionInventoryOverviewDiagram }} from "{MODULE_PATH.as_uri()}";
const modules = new Map([
  ["root.alpha", {{ moduleId: "root.alpha" }}],
  ["root.beta", {{ moduleId: "root.beta" }}],
]);
const functions = new Map([
  ["root.alpha::f1", {{ docstringQuality: {{ exists: true }}, typeHintCoverage: 0.8, todoTags: 0 }}],
  ["root.beta::g1", {{ docstringQuality: {{ exists: false }}, annotationCoverage: 0.6, todoTags: 0 }}],
]);
const first = buildFunctionInventoryOverviewDiagram(modules, functions);
const second = buildFunctionInventoryOverviewDiagram(modules, functions);
console.log(JSON.stringify({{
  firstDefinition: first.definition,
  secondDefinition: second.definition,
  firstStatus: first.statusMessage,
  secondStatus: second.statusMessage,
  firstStats: first.stats,
  secondStats: second.stats
}}));
"""
    payload = _run_node_module(script)

    assert payload["firstDefinition"] == payload["secondDefinition"]
    assert payload["firstStatus"] == payload["secondStatus"]
    assert payload["firstStats"] == payload["secondStats"]
