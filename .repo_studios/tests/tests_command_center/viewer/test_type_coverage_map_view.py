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
    / "type_coverage_map.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected type coverage map builder module at {MODULE_PATH}")


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


def test_type_coverage_map_requires_functions() -> None:
    script = f"""
import {{ buildTypeCoverageMapDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildTypeCoverageMapDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert "message" in payload
    assert payload["message"].startswith("No functions recorded")


def test_type_coverage_map_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildTypeCoverageMapDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["alpha::f1", {{ name: "f1", moduleId: "alpha", typeHintCoverage: 0.9 }}],
  ["alpha::f2", {{ name: "f2", moduleId: "alpha", annotationCoverage: 0.6 }}],
  ["beta::g1", {{ name: "g1", moduleId: "beta", metrics: {{ coverage: 0.3 }} }}],
  ["gamma::h1", {{ name: "h1", moduleId: "gamma" }}],
]);
const result = buildTypeCoverageMapDiagram(functions, {{
  viewLabel: "Quality Metrics · Type Coverage Map",
  centerLabel: "Type Coverage Overview",
  bucketLimit: 5,
}});
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    definition = payload.get("definition")
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "Type Coverage Overview" in definition
    assert "classDef typeStrong" in definition
    assert "classDef typeWeak" in definition
    assert "Functions: 1" in definition

    status_message = payload.get("statusMessage")
    assert isinstance(status_message, str)
    assert "Rendered Type Coverage Map" in status_message

    stats = payload.get("stats")
    assert stats == {"strong": 1, "moderate": 1, "weak": 1, "unknown": 1}


def test_type_coverage_map_definition_is_stable_across_repeated_calls() -> None:
    script = f"""
import {{ buildTypeCoverageMapDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["sample::main", {{ name: "main", moduleId: "sample", typeHintCoverage: 0.85 }}],
  ["sample::helper", {{ name: "helper", moduleId: "sample", annotationCoverage: 0.55 }}],
]);
const first = buildTypeCoverageMapDiagram(functions);
const second = buildTypeCoverageMapDiagram(functions);
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
