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
    / "exception_flow_map.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected Exception Flow builder at {MODULE_PATH}")


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


def test_exception_flow_map_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildExceptionFlowMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.errors", {{
    moduleId: "alpha.errors",
    functions: [
      "alpha.errors::load",
      "alpha.errors::save",
    ],
  }}],
  ["beta.handlers", {{
    moduleId: "beta.handlers",
    functions: ["beta.handlers::handle"],
  }}],
]);

const functions = new Map([
  ["alpha.errors::load", {{
    id: "alpha.errors::load",
    moduleId: "alpha.errors",
    name: "load",
    raisedExceptions: [
      {{ type: "ValueError", message: "bad state", qualifiedName: "ValueError", lineno: 24 }},
      {{ type: "IOError", qualifiedName: "IOError", lineno: 30 }},
    ],
  }}],
  ["alpha.errors::save", {{
    id: "alpha.errors::save",
    moduleId: "alpha.errors",
    name: "save",
    raisedExceptions: [
      {{ type: "RuntimeError", message: "persist failed", qualifiedName: "RuntimeError", lineno: 40 }},
    ],
  }}],
  ["beta.handlers::handle", {{
    id: "beta.handlers::handle",
    moduleId: "beta.handlers",
    name: "handle",
    raisedExceptions: [
      {{ type: "ValueError", message: "bad state", qualifiedName: "ValueError", lineno: 12 }},
    ],
  }}],
]);

const result = buildExceptionFlowMapDiagram(modules, functions, {{ scopeDescription: "repository" }});

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
    assert "alpha.errors" in definition
    assert "ValueError" in definition

    status = payload["statusMessage"]
    assert status == (
        "Rendered Exception Flow Map for repository (2 modules, 3 functions, 3 exceptions, 4 raise events)."
    )

    stats = payload["stats"]
    assert stats["modules"] == 2
    assert stats["functions"] == 3
    assert stats["exceptions"] == 3
    assert stats["raiseEvents"] == 4

    top_modules_detail = next(
        (detail for detail in payload["details"] if detail.get("title") == "Top Modules"),
        None,
    )
    assert top_modules_detail is not None
    assert any("alpha.errors" in item["header"] for item in top_modules_detail["items"])

    top_exceptions_detail = next(
        (detail for detail in payload["details"] if detail.get("title") == "Top Exceptions"),
        None,
    )
    assert top_exceptions_detail is not None
    assert any("ValueError" in item["header"] for item in top_exceptions_detail["items"])


def test_exception_flow_map_returns_message_when_empty() -> None:
    script = f"""
import {{ buildExceptionFlowMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.noop", {{
    moduleId: "alpha.noop",
    functions: ["alpha.noop::noop"],
  }}],
]);

const functions = new Map([
  ["alpha.noop::noop", {{
    id: "alpha.noop::noop",
    moduleId: "alpha.noop",
    name: "noop",
    raisedExceptions: [],
  }}],
]);

const result = buildExceptionFlowMapDiagram(modules, functions);

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"] == "No exceptions were recorded in this CommandView artifact."


def test_exception_flow_map_appends_fallback_notice() -> None:
    script = f"""
import {{ buildExceptionFlowMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.errors", {{
    moduleId: "alpha.errors",
    functions: ["alpha.errors::raise"],
  }}],
]);

const functions = new Map([
  ["alpha.errors::raise", {{
    id: "alpha.errors::raise",
    moduleId: "alpha.errors",
    name: "raise",
    raisedExceptions: [
      {{ type: "RuntimeError", message: "boom", qualifiedName: "RuntimeError" }},
    ],
  }}],
]);

const result = buildExceptionFlowMapDiagram(modules, functions, {{
  scopeDescription: "alpha.errors",
  fallbackNotice: "Showing repository map instead.",
}});

console.log(JSON.stringify({{
  statusMessage: result.statusMessage,
  details: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    assert payload["statusMessage"].endswith("Showing repository map instead.")
    info_detail = payload["details"][0]
    assert info_detail["type"] == "info"
    assert "fallback" in info_detail["title"].lower()
