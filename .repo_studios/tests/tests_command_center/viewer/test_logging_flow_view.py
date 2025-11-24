from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "logging_flow.js"

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected logging flow builder module at {MODULE_PATH}")


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


def test_logging_flow_requires_functions() -> None:
    script = f"""
import {{ buildLoggingFlowDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildLoggingFlowDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert "message" in payload
    assert payload["message"].startswith("No functions recorded")


def test_logging_flow_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildLoggingFlowDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["alpha::audit", {{
    name: "audit",
    moduleId: "alpha.service.logging",
    loggingCalls: [
      {{ level: "ERROR", lineno: 42, logger: "alpha.audit" }},
      {{ level: "info", lineno: 44 }},
    ],
  }}],
  ["alpha::handler", {{
    name: "handler",
    moduleId: "alpha.service.logging",
    loggingCalls: [
      {{ level: "critical", lineno: 50 }},
    ],
  }}],
  ["beta::report", {{
    name: "report",
    moduleId: "beta.core.reporting",
    loggingCalls: [
      {{ level: "warning", lineno: 12 }},
      {{ level: "exception", lineno: 18 }},
      {{ level: "ERROR", lineno: 25 }},
    ],
  }}],
  ["gamma::debugger", {{
    name: "debugger",
    moduleId: "gamma.analytics.debug",
    loggingCalls: [
      {{ level: "debug", lineno: 7 }},
      {{ level: "TRACE", lineno: 9, logger: "gamma.trace" }},
    ],
  }}],
  ["delta::silent", {{
    name: "silent",
    moduleId: "delta.helpers.silence",
    loggingCalls: [],
  }}],
  ["epsilon::mystery", {{
    name: "mystery",
    moduleId: "epsilon.misc",
    loggingCalls: [
      {{ message: "no level recorded" }},
    ],
  }}],
]);
const result = buildLoggingFlowDiagram(functions, {{
  viewLabel: "Quality Metrics · Logging Flow",
  centerLabel: "Logging Flow · Overview",
  bucketLimit: 4,
  moduleAggregateLimit: 2,
  screeningHistory: {{
    events: [
      {{ timestamp: "2025-11-08T12:00:00Z", severity: "warning", packId: "docstring_coverage", packLabel: "Docstring Coverage" }},
      {{ timestamp: "2025-11-09T09:00:00Z", severity: "critical", packId: "docstring_coverage", packLabel: "Docstring Coverage" }},
      {{ timestamp: "2025-11-09T18:00:00Z", severity: "CRITICAL", packId: "docstring_coverage", packLabel: "Docstring Coverage" }},
    ],
  }},
}});
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    definition = payload.get("definition")
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "Logging Flow" in definition
    assert "classDef logCritical" in definition
    assert "classDef logSilent" in definition

    status_message = payload.get("statusMessage")
    assert isinstance(status_message, str)
    assert "Rendered Logging Flow" in status_message
    assert "screening CRITICAL" in status_message

    stats = payload.get("stats")
    assert stats["emitters"] == 5
    assert stats["silent"] == 1
    assert stats["bucketCounts"] == {
        "critical": 1,
        "error": 2,
        "warning": 0,
        "info": 0,
        "debug": 1,
        "unknown": 1,
        "silent": 1,
    }
    assert stats["events"] == {
        "critical": 1,
        "error": 3,
        "warning": 1,
        "info": 1,
        "debug": 2,
        "unknown": 1,
    }
    top_modules = stats.get("topModules")
    assert isinstance(top_modules, list)
    assert top_modules
    assert top_modules[0]["moduleId"] == "alpha.service.logging"
    assert top_modules[0]["callCount"] == 3
    assert top_modules[0]["emitters"] == 2
    screening = stats.get("screening")
    assert screening is not None
    assert screening["latestSeverity"] == "critical"
    assert screening["streakLength"] == 2
    assert screening["recentCounts"]["critical"] == 2
    assert screening["windowSize"] == 3


def test_logging_flow_definition_is_stable_across_repeated_calls() -> None:
    script = f"""
import {{ buildLoggingFlowDiagram }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["sample::main", {{
    name: "main",
    moduleId: "sample.core",
    loggingCalls: [
      {{ level: "info", lineno: 12 }},
      {{ level: "ERROR", lineno: 18 }},
    ],
  }}],
  ["sample::helper", {{
    name: "helper",
    moduleId: "sample.core",
    loggingCalls: [
      {{ level: "debug", lineno: 5 }},
    ],
  }}],
]);
const first = buildLoggingFlowDiagram(functions);
const second = buildLoggingFlowDiagram(functions);
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
