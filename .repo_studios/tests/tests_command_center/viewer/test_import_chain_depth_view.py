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
    / "import_chain_depth.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected import chain depth builder at {MODULE_PATH}")


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


def test_import_chain_depth_requires_modules() -> None:
    script = f"""
import {{ buildImportChainDepthDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildImportChainDepthDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert payload["message"].startswith("No modules recorded")


def test_import_chain_depth_renders_definition_and_stats() -> None:
    script = f"""
import {{ buildImportChainDepthDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "os", category: "standard_library" }},
      {{ target: "beta.utils", category: "internal" }},
    ],
  }}],
  ["beta.utils", {{
    importEdges: [
      {{ target: "math", category: "standard_library" }},
      {{ target: "gamma.analytics", category: "internal" }},
    ],
  }}],
  ["gamma.analytics", {{
    importEdges: [
      {{ target: "beta.utils", category: "internal" }},
    ],
  }}],
  ["delta.orphan", {{ importEdges: [] }}],
]);

const result = buildImportChainDepthDiagram(modules, {{ scopeDescription: "repository" }});

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
    assert definition.startswith("graph TD")
    assert "alpha_core" in definition
    assert "gamma_analytics" in definition

    status = payload["statusMessage"]
    assert "Import Chain Depth" in status
    assert "modules" in status

    stats = payload["stats"]
    assert stats["modulesInChain"] == 3
    assert stats["maxDepth"] >= 2
    assert stats["uniqueStandardLibraryCount"] == 2
    assert stats["unreachableCount"] == 1

    details = payload["statusDetails"]
    assert isinstance(details, list) and details
    assert details[0]["type"] == "stat-summary"


def test_import_chain_depth_focus_filters_modules() -> None:
    script = f"""
import {{ buildImportChainDepthDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "os", category: "standard_library" }},
      {{ target: "beta.utils", category: "internal" }},
    ],
  }}],
  ["beta.utils", {{
    importEdges: [
      {{ target: "alpha.core", category: "internal" }},
    ],
  }}],
  ["gamma.analytics", {{
    importEdges: [
      {{ target: "beta.utils", category: "internal" }},
    ],
  }}],
]);

const focusResult = buildImportChainDepthDiagram(modules, {{
  scopeDescription: "gamma.analytics",
  focusModules: ["gamma.analytics"],
}});

console.log(JSON.stringify({{
  definition: focusResult.definition,
  stats: focusResult.stats,
  statusMessage: focusResult.statusMessage,
}}));
"""
    payload = _run_node_module(script)

    definition = payload["definition"]
    assert "gamma_analytics" in definition
    assert "alpha_core" in definition  # ancestors required for chain context

    stats = payload["stats"]
    assert stats["modulesInChain"] == 3
    assert stats["maxDepth"] >= 2

    status = payload["statusMessage"]
    assert "gamma.analytics" in status
