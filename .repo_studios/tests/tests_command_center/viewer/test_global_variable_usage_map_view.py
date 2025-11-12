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
    / "global_variable_usage_map.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected global variable usage builder at {MODULE_PATH}")


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


def test_global_variable_usage_map_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildGlobalVariableUsageMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.config", {{
    moduleId: "alpha.config",
    globals: [
      {{ name: "SETTINGS", valueKind: "dict", lineno: 5 }},
      {{ name: "FLAG", valueKind: "bool", lineno: 12 }},
    ],
    functions: [
      "alpha.config::load",
      "alpha.config::toggle",
    ],
  }}],
  ["beta.feature", {{
    moduleId: "beta.feature",
    globals: [
      {{ name: "LIMIT", valueKind: "int", lineno: 8 }},
    ],
    functions: [
      "beta.feature::check",
    ],
  }}],
]);

const functions = new Map([
  ["alpha.config::load", {{
    id: "alpha.config::load",
    moduleId: "alpha.config",
    name: "load",
    usedGlobals: ["SETTINGS"],
  }}],
  ["alpha.config::toggle", {{
    id: "alpha.config::toggle",
    moduleId: "alpha.config",
    name: "toggle",
    usedGlobals: ["SETTINGS", "FLAG"],
  }}],
  ["beta.feature::check", {{
    id: "beta.feature::check",
    moduleId: "beta.feature",
    name: "check",
    usedGlobals: ["LIMIT"],
  }}],
]);

const result = buildGlobalVariableUsageMapDiagram(modules, functions, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  definition: result.definition,
  statusMessage: result.statusMessage,
  stats: result.stats,
  details: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    definition = payload["definition"]
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "subgraph" in definition
    assert "alpha.config" in definition

    status = payload["statusMessage"]
    assert status == (
        "Rendered Global Variable Usage Map for repository (2 modules, 3 globals, 3 functions, 4 references)."
    )

    stats = payload["stats"]
    assert stats["modules"] == 2
    assert stats["globals"] == 3
    assert stats["functions"] == 3
    assert stats["usageCount"] == 4

    top_modules_detail = next(
        (detail for detail in payload["details"] if detail.get("title") == "Top Modules"),
        None,
    )
    assert top_modules_detail is not None
    top_module_headers = [item["header"] for item in top_modules_detail["items"]]
    assert "alpha.config" in top_module_headers


def test_global_variable_usage_map_returns_message_when_no_usage() -> None:
    script = f"""
import {{ buildGlobalVariableUsageMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.config", {{
    moduleId: "alpha.config",
    globals: [
      {{ name: "SETTINGS", valueKind: "dict", lineno: 5 }},
    ],
    functions: ["alpha.config::noop"],
  }}],
]);

const functions = new Map([
  ["alpha.config::noop", {{
    id: "alpha.config::noop",
    moduleId: "alpha.config",
    name: "noop",
    usedGlobals: [],
  }}],
]);

const result = buildGlobalVariableUsageMapDiagram(modules, functions);

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"] == "No global variable usage was detected in this CommandView artifact."


def test_global_variable_usage_map_appends_fallback_notice() -> None:
    script = f"""
import {{ buildGlobalVariableUsageMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.config", {{
    moduleId: "alpha.config",
    globals: [
      {{ name: "SETTINGS", valueKind: "dict", lineno: 5 }},
    ],
    functions: ["alpha.config::load"],
  }}],
]);

const functions = new Map([
  ["alpha.config::load", {{
    id: "alpha.config::load",
    moduleId: "alpha.config",
    name: "load",
    usedGlobals: ["SETTINGS"],
  }}],
]);

const result = buildGlobalVariableUsageMapDiagram(modules, functions, {{
  scopeDescription: "alpha.config",
  fallbackNotice: "Showing repository map instead.",
}});

console.log(JSON.stringify({{
  statusMessage: result.statusMessage,
  details: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    assert payload["statusMessage"].endswith("Showing repository map instead.")
    first_detail = payload["details"][0]
    assert first_detail["type"] == "info"
    assert "fallback" in first_detail["title"].lower()
