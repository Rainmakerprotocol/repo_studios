from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "documentation_coverage_map.js"

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected documentation coverage map builder module at {MODULE_PATH}")


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


def test_documentation_coverage_map_requires_functions() -> None:
    script = f"""
import {{ buildDocumentationCoverageMapDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildDocumentationCoverageMapDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert "message" in payload
    assert payload["message"].startswith("No functions recorded")


def test_documentation_coverage_map_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildDocumentationCoverageMapDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["alpha::f1", {{ name: "f1", moduleId: "alpha", docstringQuality: {{ exists: true, status: "present" }} }}],
  ["alpha::f2", {{ name: "f2", moduleId: "alpha", docstringQuality: {{ exists: false, status: "missing" }} }}],
  ["beta::g1", {{ name: "g1", moduleId: "beta", docstringQuality: {{ status: "stale" }} }}],
  ["gamma::h1", {{ name: "h1", moduleId: "gamma" }}],
]);
const result = buildDocumentationCoverageMapDiagram(functions, {{
  viewLabel: "Quality Metrics · Documentation Coverage Map",
  centerLabel: "Documentation Overview",
  bucketLimit: 5,
}});
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    definition = payload.get("definition")
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "Documentation Overview" in definition
    assert "classDef docDocumented" in definition
    assert "classDef docMissing" in definition
    assert "Functions: 1" in definition

    status_message = payload.get("statusMessage")
    assert isinstance(status_message, str)
    assert "Rendered Documentation Coverage Map" in status_message

    stats = payload.get("stats")
    assert stats == {"documented": 1, "missing": 1, "unknown": 2}


def test_documentation_coverage_map_definition_is_stable_across_repeated_calls() -> None:
    script = f"""
import {{ buildDocumentationCoverageMapDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["sample::main", {{ name: "main", moduleId: "sample", docstringQuality: {{ exists: true }} }}],
  ["sample::helper", {{ name: "helper", moduleId: "sample", docstringQuality: {{ exists: false }} }}],
]);
const first = buildDocumentationCoverageMapDiagram(functions);
const second = buildDocumentationCoverageMapDiagram(functions);
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
