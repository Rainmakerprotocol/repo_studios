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
    / "io_effects_diagram.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected IO effects builder at {MODULE_PATH}")


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


def test_io_effects_diagram_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildIoEffectsDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.io", {{
    moduleId: "alpha.io",
    functions: [
      "alpha.io::load",
      "alpha.io::save",
    ],
  }}],
  ["beta.net", {{
    moduleId: "beta.net",
    functions: ["beta.net::ping"],
  }}],
]);

const functions = new Map([
  ["alpha.io::load", {{
    id: "alpha.io::load",
    moduleId: "alpha.io",
    name: "load",
    ioEffects: {{
      reads: true,
      writes: true,
      env: false,
      network: false,
      hasEffects: true,
      activeFlags: ["reads", "writes"],
      flagCount: 2,
    }},
  }}],
  ["alpha.io::save", {{
    id: "alpha.io::save",
    moduleId: "alpha.io",
    name: "save",
    ioEffects: {{
      reads: false,
      writes: true,
      env: false,
      network: false,
      hasEffects: true,
      activeFlags: ["writes"],
      flagCount: 1,
    }},
  }}],
  ["beta.net::ping", {{
    id: "beta.net::ping",
    moduleId: "beta.net",
    name: "ping",
    ioEffects: {{
      reads: false,
      writes: false,
      env: false,
      network: true,
      hasEffects: true,
      activeFlags: ["network"],
      flagCount: 1,
    }},
  }}],
]);

const result = buildIoEffectsDiagram(modules, functions, {{ scopeDescription: "repository" }});

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
    assert "alpha.io" in definition
    assert "Reads Files" in definition

    status = payload["statusMessage"]
    assert status == "Rendered IO Effects Diagram for repository (2 modules, 3 functions, 4 effect flags)."

    stats = payload["stats"]
    assert stats["modules"] == 2
    assert stats["functions"] == 3
    assert stats["effectFlags"] == 4
    assert stats["effectBreakdown"]["writes"] == 2

    top_modules_detail = next(
        (detail for detail in payload["details"] if detail.get("title") == "Top Modules"),
        None,
    )
    assert top_modules_detail is not None
    top_module_headers = [item["header"] for item in top_modules_detail["items"]]
    assert "alpha.io" in top_module_headers


def test_io_effects_diagram_returns_message_when_no_effects() -> None:
    script = f"""
import {{ buildIoEffectsDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.io", {{
    moduleId: "alpha.io",
    functions: ["alpha.io::noop"],
  }}],
]);

const functions = new Map([
  ["alpha.io::noop", {{
    id: "alpha.io::noop",
    moduleId: "alpha.io",
    name: "noop",
    ioEffects: {{
      reads: false,
      writes: false,
      env: false,
      network: false,
      hasEffects: false,
      activeFlags: [],
      flagCount: 0,
    }},
  }}],
]);

const result = buildIoEffectsDiagram(modules, functions);

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"] == "No IO effects were detected in this CommandView artifact."


def test_io_effects_diagram_appends_fallback_notice() -> None:
    script = f"""
import {{ buildIoEffectsDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.io", {{
    moduleId: "alpha.io",
    functions: ["alpha.io::load"],
  }}],
]);

const functions = new Map([
  ["alpha.io::load", {{
    id: "alpha.io::load",
    moduleId: "alpha.io",
    name: "load",
    ioEffects: {{
      reads: true,
      writes: false,
      env: false,
      network: false,
      hasEffects: true,
      activeFlags: ["reads"],
      flagCount: 1,
    }},
  }}],
]);

const result = buildIoEffectsDiagram(modules, functions, {{
  scopeDescription: "alpha.io",
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
