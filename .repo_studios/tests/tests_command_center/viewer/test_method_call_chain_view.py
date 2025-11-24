from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
BUILDER_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "method_call_chain.js"

if not BUILDER_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected method call chain builder at {BUILDER_PATH}")


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


def test_method_call_chain_renders_sequence_diagram() -> None:
    script = f"""
import {{ buildMethodCallChainDiagram }} from "{BUILDER_PATH.as_uri()}";

const modules = new Map([
  ["alpha.workflow", {{ moduleId: "alpha.workflow", functions: [
    "alpha.workflow::Workflow.start",
    "alpha.workflow::Workflow.validate",
    "alpha.workflow::Workflow.finalize"
  ] }}],
  ["beta.notifications", {{ moduleId: "beta.notifications", functions: [
    "beta.notifications::Notifier.send"
  ] }}],
]);

const functions = new Map([
  ["alpha.workflow::Workflow.start", {{
    id: "alpha.workflow::Workflow.start",
    name: "Workflow.start",
    moduleId: "alpha.workflow",
    metrics: {{ coverage: 0.8 }},
    calls: ["alpha.workflow::Workflow.validate", "beta.notifications::Notifier.send"],
  }}],
  ["alpha.workflow::Workflow.validate", {{
    id: "alpha.workflow::Workflow.validate",
    name: "Workflow.validate",
    moduleId: "alpha.workflow",
    metrics: {{ coverage: 0.75 }},
    calls: ["alpha.workflow::Workflow.finalize"],
  }}],
  ["alpha.workflow::Workflow.finalize", {{
    id: "alpha.workflow::Workflow.finalize",
    name: "Workflow.finalize",
    moduleId: "alpha.workflow",
    metrics: {{ coverage: 0.7 }},
    calls: [],
  }}],
  ["beta.notifications::Notifier.send", {{
    id: "beta.notifications::Notifier.send",
    name: "Notifier.send",
    moduleId: "beta.notifications",
    metrics: {{ coverage: 0.9 }},
    calls: [],
  }}],
]);

const callGraph = new Map([
  ["alpha.workflow::Workflow.start", ["alpha.workflow::Workflow.validate", "beta.notifications::Notifier.send"]],
  ["alpha.workflow::Workflow.validate", ["alpha.workflow::Workflow.finalize"]],
]);

const allowed = new Set([
  "alpha.workflow::Workflow.start",
  "alpha.workflow::Workflow.validate",
  "alpha.workflow::Workflow.finalize",
  "beta.notifications::Notifier.send",
]);

const result = buildMethodCallChainDiagram(modules, functions, callGraph, {{
  scopeDescription: "alpha.workflow",
  focusFunctionId: "alpha.workflow::Workflow.start",
  allowedFunctionIds: allowed,
}});

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
    assert definition.startswith("sequenceDiagram")
    assert "alpha_workflow_Workflow" in definition
    assert "beta_notifications_Notifier" in definition
    assert "start() -> validate()" in definition

    status = payload["statusMessage"]
    assert "Method Call Chain" in status

    stats = payload["stats"]
    assert stats["methodCount"] == 4
    assert stats["classCount"] == 2
    assert stats["edgeCount"] == 3
    assert stats["depth"] == 2

    details = payload["statusDetails"]
    assert isinstance(details, list)
    call_chain_detail = next(item for item in details if item.get("title") == "Call Chain")
    assert call_chain_detail["items"][0]["value"].startswith("Workflow.start")


def test_method_call_chain_reports_missing_methods() -> None:
    script = f"""
import {{ buildMethodCallChainDiagram }} from "{BUILDER_PATH.as_uri()}";

const modules = new Map([
  ["alpha.standalone", {{ moduleId: "alpha.standalone", functions: ["alpha.standalone::main"] }}],
]);

const functions = new Map([
  ["alpha.standalone::main", {{
    id: "alpha.standalone::main",
    name: "main",
    moduleId: "alpha.standalone",
    calls: [],
  }}],
]);

const callGraph = new Map([
  ["alpha.standalone::main", []],
]);

const result = buildMethodCallChainDiagram(modules, functions, callGraph, {{ scopeDescription: "alpha.standalone" }});

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"] == "No class methods were detected in this scope."
