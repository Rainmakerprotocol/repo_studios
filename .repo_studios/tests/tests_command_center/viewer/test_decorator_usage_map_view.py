from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "decorator_usage_map.js"

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected decorator usage map builder module at {MODULE_PATH}")


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


def test_decorator_usage_map_requires_functions() -> None:
    script = f"""
import {{ buildDecoratorUsageMapDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildDecoratorUsageMapDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert "message" in payload
    assert payload["message"].startswith("No functions recorded")


def test_decorator_usage_map_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildDecoratorUsageMapDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["alpha::f1", {{
    name: "f1",
    moduleId: "alpha",
    decorators: ["identity", "cache"],
    decoratorsDetailed: [
      {{ name: "identity", module: "alpha.decorators", args: [], kwargs: {{}} }},
      {{ name: "cache", args: ["300"], kwargs: {{ key: "'user_id'" }} }},
    ],
  }}],
  ["alpha::f2", {{
    name: "f2",
    moduleId: "alpha",
    decorators: ["identity"],
  }}],
  ["beta::g1", {{
    name: "g1",
    moduleId: "beta",
    decorators: [],
  }}],
  ["gamma::h1", {{
    name: "h1",
    moduleId: "gamma",
  }}],
]);
const result = buildDecoratorUsageMapDiagram(functions, {{
  viewLabel: "Quality Metrics · Decorator Usage Map",
  centerLabel: "Decorator Overview",
  bucketLimit: 3,
  decoratorLimit: 4,
  requiredDecorators: ["identity", "audit"],
}});
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    definition = payload.get("definition")
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "Decorator Overview" in definition
    assert "classDef decoratorFrequent" in definition
    assert "classDef decoratorMissing" in definition

    status_message = payload.get("statusMessage")
    assert isinstance(status_message, str)
    assert "Rendered Decorator Usage Map" in status_message
    assert "top identity x2" in status_message
    assert "missing required audit" in status_message

    stats = payload.get("stats")
    assert stats == {
        "decorated": 2,
        "undecorated": 2,
        "uniqueDecorators": 2,
        "topDecorators": [
            {"name": "identity", "count": 2},
            {"name": "cache", "count": 1},
        ],
        "requiredDecorators": ["identity", "audit"],
        "missingRequiredDecorators": ["audit"],
        "missingRequiredDetails": [
            {
                "decorator": "audit",
                "scope": "global",
                "target": None,
                "samples": [
                    {"id": "alpha::f1", "name": "f1", "moduleId": "alpha"},
                    {"id": "alpha::f2", "name": "f2", "moduleId": "alpha"},
                    {"id": "beta::g1", "name": "g1", "moduleId": "beta"},
                ],
            }
        ],
    }

    assert payload["policyDetails"] == stats["missingRequiredDetails"]


def test_decorator_usage_map_definition_is_stable_across_repeated_calls() -> None:
    script = f"""
import {{ buildDecoratorUsageMapDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["sample::main", {{ name: "main", moduleId: "sample", decorators: ["click"], decoratorsDetailed: [{{ name: "click" }}] }}],
  ["sample::helper", {{ name: "helper", moduleId: "sample", decorators: [] }}],
]);
const options = {{ decoratorLimit: 3, bucketLimit: 2 }};
const first = buildDecoratorUsageMapDiagram(functions, options);
const second = buildDecoratorUsageMapDiagram(functions, options);
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
