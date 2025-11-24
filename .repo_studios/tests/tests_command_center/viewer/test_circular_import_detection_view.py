from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
CIRCULAR_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "circular_import_detection.js"
)
DEPENDENCY_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "module_dependency_graph.js"
)

if not CIRCULAR_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected circular import detection builder at {CIRCULAR_MODULE_PATH}")

if not DEPENDENCY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected module dependency graph builder at {DEPENDENCY_MODULE_PATH}")


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


def test_circular_import_detection_is_deterministic() -> None:
    script = f"""
import {{ buildCircularImportDetectionDiagram }} from "{CIRCULAR_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["app.entry", {{
    importEdges: [
      {{ target: "shared.utils" }},
      {{ target: "app.entry" }},
    ],
  }}],
  ["shared.utils", {{
    importEdges: [
      {{ target: "shared.logging" }},
      {{ target: "app.entry" }},
    ],
  }}],
  ["shared.logging", {{
    importEdges: [
      {{ target: "shared.utils" }},
    ],
  }}],
  ["feature.alpha", {{
    importEdges: [
      {{ target: "feature.beta" }},
    ],
  }}],
  ["feature.beta", {{
    importEdges: [
      {{ target: "feature.alpha" }},
    ],
  }}],
  ["solo.loop", {{
    importEdges: [
      {{ target: "solo.loop" }},
    ],
  }}],
  ["isolated.module", {{
    importEdges: [],
  }}],
]);

const options = {{
  scopeDescription: "dependency pack scope",
  fallbackNotice: "default scope applied",
  viewLabel: "Circular Import Detection",
}};

const first = buildCircularImportDetectionDiagram(modules, options);
const second = buildCircularImportDetectionDiagram(modules, options);

console.log(JSON.stringify({{
  definitionStable: first.definition === second.definition,
  statusStable: first.statusMessage === second.statusMessage,
  label: first.label,
  statusMessage: first.statusMessage,
  stats: first.stats,
  statusDetailsCount: first.statusDetails.length,
}}));
"""

    payload = _run_node_module(script)

    assert payload["definitionStable"] is True
    assert payload["statusStable"] is True
    assert payload["label"] == "Circular Import Detection"
    assert "Detected" in payload["statusMessage"]
    assert payload["stats"]["cycleCount"] == 3
    assert payload["statusDetailsCount"] >= 2


def test_circular_import_detection_coexists_with_dependency_view() -> None:
    script = f"""
import {{ buildCircularImportDetectionDiagram }} from "{CIRCULAR_MODULE_PATH.as_uri()}";
import {{ buildModuleDependencyGraphDiagram }} from "{DEPENDENCY_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "beta.helpers" }},
      {{ target: "alpha.core" }},
    ],
  }}],
  ["beta.helpers", {{
    importEdges: [
      {{ target: "alpha.core" }},
    ],
  }}],
  ["gamma.utils", {{
    importEdges: [],
  }}],
]);

const dependencySummaries = new Map([
  ["alpha.core", {{ internal: {{ count: 1, modules: ["beta.helpers"] }} }}],
  ["beta.helpers", {{ internal: {{ count: 1, modules: ["alpha.core"] }} }}],
]);

const cycleBefore = buildCircularImportDetectionDiagram(modules, {{ scopeDescription: "dependency pack" }});
const dependencyFirst = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});
const cycleAfter = buildCircularImportDetectionDiagram(modules, {{ scopeDescription: "dependency pack" }});
const dependencySecond = buildModuleDependencyGraphDiagram(modules, {{ dependencySummaries }});

console.log(JSON.stringify({{
  cycleDefinitionStable: cycleBefore.definition === cycleAfter.definition,
  cycleStatusStable: cycleBefore.statusMessage === cycleAfter.statusMessage,
  dependencyDefinitionStable: dependencyFirst.definition === dependencySecond.definition,
  dependencyStatusStable: dependencyFirst.statusMessage === dependencySecond.statusMessage,
  cycleDefinitionContainsSubgraph: cycleBefore.definition.includes("subgraph"),
  dependencyLabel: dependencyFirst.label,
}}));
"""

    payload = _run_node_module(script)

    assert payload["cycleDefinitionStable"] is True
    assert payload["cycleStatusStable"] is True
    assert payload["dependencyDefinitionStable"] is True
    assert payload["dependencyStatusStable"] is True
    assert payload["cycleDefinitionContainsSubgraph"] is True
    assert "Dependency" in payload["dependencyLabel"]
