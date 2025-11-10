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
    / "module_dependency_graph.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected module dependency graph builder at {MODULE_PATH}")


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


def test_module_dependency_graph_requires_modules() -> None:
    script = f"""
import {{ buildModuleDependencyGraphDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildModuleDependencyGraphDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert payload["message"].startswith("No modules recorded")


def test_module_dependency_graph_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildModuleDependencyGraphDiagram }} from "{MODULE_PATH.as_uri()}";
const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "beta.helpers", category: "internal", unused: false, functions: ["alpha.core::build", "alpha.core::sync"], via: ["helpers"] }},
      {{ target: "beta.helpers", category: "internal", unused: true, functions: [], via: [] }},
      {{ target: "os", category: "standard_library", unused: false, functions: [] }},
    ],
    functions: ["alpha.core::build", "alpha.core::sync"],
  }}],
  ["beta.helpers", {{
    importEdges: [
      {{ target: "alpha.core.builder", category: "internal", unused: false, functions: ["beta.helpers::assist"], via: ["builder"] }},
      {{ target: "alpha.vendor.requests", category: "third_party", unused: false, functions: [] }},
    ],
    functions: ["beta.helpers::assist"],
  }}],
  ["gamma.orphan", {{ importEdges: [], functions: [] }}],
]);

const dependencySummaries = new Map([
  ["alpha.core", {{
    internal: {{ count: 1, modules: ["beta.helpers"] }},
    standard_library: {{ count: 1, modules: ["os"] }},
    third_party: {{ count: 0, modules: [] }},
  }}],
  ["beta.helpers", {{
    internal: {{ count: 1, modules: ["alpha.core"] }},
    third_party: {{ count: 1, modules: ["alpha.vendor.requests"] }},
  }}],
]);

const result = buildModuleDependencyGraphDiagram(modules, {{
  dependencySummaries,
  rootId: "alpha",
}});

console.log(JSON.stringify({{
  definition: result.definition,
  label: result.label,
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
    assert "beta_helpers" in definition
    assert "2 imports" in definition

    status = payload["statusMessage"]
    assert "Rendered Module Dependency Graph" in status
    assert "repository" not in status  # scope should mention root alpha
    assert "unused import" in status

    stats = payload["stats"]
    assert stats == {
        "modules": 3,
        "edges": 2,
        "unusedEdges": 1,
        "orphans": ["gamma.orphan"],
        "topImporters": [
            {
                "moduleId": "alpha.core",
                "outgoingEdges": 1,
                "outgoingStatements": 2,
                "outgoingUnused": 1,
                "targets": ["beta.helpers"],
            },
            {
                "moduleId": "beta.helpers",
                "outgoingEdges": 1,
                "outgoingStatements": 1,
                "outgoingUnused": 0,
                "targets": ["alpha.core"],
            },
        ],
        "topCouplings": [
            {
                "functions": 2,
                "source": "alpha.core",
                "statements": 2,
                "target": "beta.helpers",
                "unused": 1,
            },
            {
                "functions": 1,
                "source": "beta.helpers",
                "statements": 1,
                "target": "alpha.core",
                "unused": 0,
            },
        ],
        "externalDependencies": [
            {"category": "standard_library", "count": 1},
            {"category": "third_party", "count": 1},
        ],
    }

    details = payload["statusDetails"]
    assert isinstance(details, list) and details
    snapshot = details[0]
    assert snapshot["type"] == "stat-summary"
    assert any(entry["label"] == "Modules" and entry["value"] == "3" for entry in snapshot["items"])

    top_list = next(desc for desc in details if desc["type"] == "list" and desc["title"] == "Top Module Couplings")
    assert any(item["header"].startswith("alpha.core") for item in top_list["items"])


def test_module_dependency_graph_definition_is_stable_across_repeated_calls() -> None:
    script = f"""
import {{ buildModuleDependencyGraphDiagram }} from "{MODULE_PATH.as_uri()}";
const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "beta.helpers", category: "internal", unused: false, functions: ["alpha.core::build"] }},
    ],
    functions: ["alpha.core::build"],
  }}],
  ["beta.helpers", {{ importEdges: [], functions: [] }}],
]);

const dependencySummaries = new Map([
  ["alpha.core", {{ internal: {{ count: 1, modules: ["beta.helpers"] }} }}],
]);

const first = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});
const second = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});

console.log(JSON.stringify({{
  definitionEqual: first.definition === second.definition,
  statusEqual: first.statusMessage === second.statusMessage,
  statsEqual: JSON.stringify(first.stats) === JSON.stringify(second.stats),
}}));
"""
    payload = _run_node_module(script)

    assert payload["definitionEqual"] is True
    assert payload["statusEqual"] is True
    assert payload["statsEqual"] is True
