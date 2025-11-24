from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "complexity_heatmap.js"

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected complexity heatmap builder module at {MODULE_PATH}")


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


def test_complexity_heatmap_requires_functions() -> None:
    script = f"""
import {{ buildComplexityHeatmapDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildComplexityHeatmapDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert "message" in payload
    assert payload["message"].startswith("No complexity metrics recorded")


def test_complexity_heatmap_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildComplexityHeatmapDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["alpha::f1", {{ name: "f1", moduleId: "alpha", cyclomaticComplexity: 22, metrics: {{ lineCount: 210, coverage: 0.52 }} }}],
  ["alpha::f2", {{ name: "f2", moduleId: "alpha", cyclomaticComplexity: 11, metrics: {{ lineCount: 150, coverage: 0.78 }} }}],
  ["beta::g1", {{ name: "g1", moduleId: "beta", metrics: {{ complexity: 7, lineCount: 80, coverage: 0.63 }} }}],
  ["gamma::h1", {{ name: "h1", moduleId: "gamma", cyclomaticComplexity: 3, metrics: {{ coverage: 0.9 }} }}],
  ["delta::k1", {{ name: "k1", moduleId: "delta" }}],
]);
const moduleMetrics = new Map([
  ["alpha", {{ gitChurn: {{ commit_count: 18, net_changes: 42 }} }}],
  ["beta", {{ gitChurn: {{ commit_count: 4, net_changes: -3 }} }}],
  ["gamma", {{ gitChurn: {{ commit_count: 2 }} }}],
]);
const result = buildComplexityHeatmapDiagram(functions, {{
  viewLabel: "Quality Metrics · Complexity Heatmap",
  centerLabel: "Complexity Overview",
  bucketLimit: 3,
  moduleMetrics,
  moduleAggregateLimit: 2,
  coverageRiskThreshold: 0.6,
}});
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    definition = payload.get("definition")
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "Complexity Overview" in definition
    assert "classDef complexityExtreme" in definition
    assert "classDef complexityLow" in definition
    assert "Functions:" in definition
    assert "Cov:" in definition
    assert "Churn:" in definition

    status_message = payload.get("statusMessage")
    assert isinstance(status_message, str)
    assert "Rendered Complexity Heatmap" in status_message
    assert "extreme 1" in status_message
    assert "max complexity" in status_message

    stats = payload.get("stats")
    assert stats["extreme"] == 1
    assert stats["high"] == 1
    assert stats["moderate"] == 1
    assert stats["low"] == 1
    assert stats["unknown"] == 1
    assert stats["maxComplexity"] == 22

    coverage = stats.get("coverage")
    assert isinstance(coverage, dict)
    assert coverage["count"] == 4
    assert coverage["belowThreshold"] == 1

    module_aggregates = stats.get("moduleAggregates")
    assert isinstance(module_aggregates, list)
    assert module_aggregates
    top_module = module_aggregates[0]
    assert top_module["moduleId"] == "alpha"
    assert top_module["hotFunctions"] == 2
    assert top_module["churn"]["commitCount"] == 18


def test_complexity_heatmap_definition_is_stable_across_repeated_calls() -> None:
    script = f"""
import {{ buildComplexityHeatmapDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["sample::main", {{ name: "main", moduleId: "sample", cyclomaticComplexity: 13, metrics: {{ coverage: 0.7 }} }}],
  ["sample::helper", {{ name: "helper", moduleId: "sample", metrics: {{ complexity: 6, coverage: 0.62 }} }}],
]);
const moduleMetrics = new Map([
  ["sample", {{ gitChurn: {{ commit_count: 5 }} }}],
]);
const options = {{
  moduleMetrics,
  moduleAggregateLimit: 2,
}};
const first = buildComplexityHeatmapDiagram(functions, options);
const second = buildComplexityHeatmapDiagram(functions, options);
console.log(JSON.stringify({{
  firstDefinition: first.definition,
  secondDefinition: second.definition,
  firstStatus: first.statusMessage,
  secondStatus: second.statusMessage,
  firstStats: first.stats,
  secondStats: second.stats,
}}));
"""
    payload = _run_node_module(script)

    assert payload["firstDefinition"] == payload["secondDefinition"]
    assert payload["firstStatus"] == payload["secondStatus"]
    assert payload["firstStats"] == payload["secondStats"]
