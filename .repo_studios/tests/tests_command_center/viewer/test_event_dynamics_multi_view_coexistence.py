from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
CALLBACK_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "callback_registration_map.js"
)
CALL_GRAPH_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "function_call_graph.js"
DYNAMIC_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "dynamic_code_watchlist.js"

if not CALLBACK_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected callback registration map builder at {CALLBACK_MODULE_PATH}")

if not CALL_GRAPH_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function call graph builder module at {CALL_GRAPH_MODULE_PATH}")

if not DYNAMIC_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected dynamic code watchlist builder at {DYNAMIC_MODULE_PATH}")


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


def test_callback_registration_map_coexists_with_function_call_graph_view() -> None:
    script = f"""
import {{ buildCallbackRegistrationMapDiagram }} from "{CALLBACK_MODULE_PATH.as_uri()}";
import {{ buildFunctionCallGraphDiagram }} from "{CALL_GRAPH_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.callbacks", {{
    functions: [
      "alpha.callbacks::register_handlers",
      "alpha.callbacks::register_timer",
    ],
    callbackRegistrations: [
      {{
        function: "alpha.callbacks::register_handlers",
        expression: "dispatcher.register_callback",
        method: "register_callback",
        target: "beta.handlers.handle_event",
        targetKind: "attribute",
        targetVia: "callback",
        resolved: "beta.handlers.handle_event",
        module: "alpha.dispatcher",
        root: "dispatcher",
        lineno: 42,
      }},
      {{
        function: "alpha.callbacks::register_timer",
        expression: "timer.add_listener",
        method: "add_listener",
        target: "alpha.callbacks::on_tick",
        targetKind: "name",
        module: "alpha.timer",
        root: "timer",
        lineno: 88,
      }},
    ],
  }}],
  ["beta.handlers", {{
    functions: ["beta.handlers::handle_event"],
  }}],
]);

const functions = new Map([
  ["alpha.callbacks::register_handlers", {{ name: "register_handlers", moduleId: "alpha.callbacks", metrics: {{ lineCount: 30, coverage: 0.8 }} }}],
  ["alpha.callbacks::register_timer", {{ name: "register_timer", moduleId: "alpha.callbacks", metrics: {{ lineCount: 15, coverage: 0.6 }} }}],
  ["beta.handlers::handle_event", {{ name: "handle_event", moduleId: "beta.handlers", metrics: {{ lineCount: 20, coverage: 0.7 }} }}],
]);

const callGraph = new Map([
  ["alpha.callbacks::register_handlers", ["alpha.callbacks::register_timer", "beta.handlers::handle_event"]],
  ["alpha.callbacks::register_timer", []],
  ["beta.handlers::handle_event", []],
]);

const callbackFirst = buildCallbackRegistrationMapDiagram(modules, {{ scopeDescription: "repository" }});
const callGraphFirst = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "alpha.callbacks" }});
const callbackSecond = buildCallbackRegistrationMapDiagram(modules, {{ scopeDescription: "repository" }});
const callGraphSecond = buildFunctionCallGraphDiagram(modules, functions, callGraph, {{ moduleId: "alpha.callbacks" }});

console.log(JSON.stringify({{
  callbackDefinitionStable: callbackFirst.definition === callbackSecond.definition,
  callbackStatusStable: callbackFirst.statusMessage === callbackSecond.statusMessage,
  callGraphDefinitionStable: callGraphFirst.definition === callGraphSecond.definition,
  callGraphStatusStable: callGraphFirst.statusMessage === callGraphSecond.statusMessage,
  callbackStatusMessage: callbackFirst.statusMessage,
  callGraphStatusMessage: callGraphFirst.statusMessage,
  callbackStats: callbackFirst.stats,
}}));
"""

    payload = _run_node_module(script)

    assert payload["callbackDefinitionStable"] is True
    assert payload["callbackStatusStable"] is True
    assert payload["callGraphDefinitionStable"] is True
    assert payload["callGraphStatusStable"] is True

    callback_status = payload["callbackStatusMessage"]
    assert isinstance(callback_status, str)
    assert "Callback Registration Map" in callback_status
    assert "2 emitters" in callback_status

    call_graph_status = payload["callGraphStatusMessage"]
    assert isinstance(call_graph_status, str)
    assert "Function Call Graph" in call_graph_status

    stats = payload["callbackStats"]
    assert stats["registrations"] == 2
    assert stats["emitters"] == 2
    assert stats["targets"] == 2


def test_dynamic_code_watchlist_coexists_with_callback_registration_map() -> None:
    script = f"""
import {{ buildCallbackRegistrationMapDiagram }} from "{CALLBACK_MODULE_PATH.as_uri()}";
import {{ buildDynamicCodeWatchlistDiagram }} from "{DYNAMIC_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.callbacks", {{
    functions: [
      "alpha.callbacks::register_handlers",
      "alpha.callbacks::register_timer",
    ],
    callbackRegistrations: [
      {{
        function: "alpha.callbacks::register_handlers",
        expression: "dispatcher.register_callback",
        method: "register_callback",
        target: "beta.handlers.handle_event",
        targetKind: "attribute",
        targetVia: "callback",
        resolved: "beta.handlers.handle_event",
        module: "alpha.dispatcher",
        root: "dispatcher",
        lineno: 42,
      }},
    ],
    dynamicCode: {{
      hasDynamic: true,
      flags: {{ exec: true, dynamicImport: false, metaclass: false, globalsMutation: false }},
      activeFlags: ["exec"],
      flagCount: 1,
      events: [
        {{ kind: "exec", detail: "exec(stmt)", lineno: 55 }},
      ],
      eventCount: 1,
    }},
  }}],
  ["beta.handlers", {{
    functions: ["beta.handlers::handle_event"],
    callbackRegistrations: [],
    dynamicCode: null,
  }}],
]);

const dynamicFirst = buildDynamicCodeWatchlistDiagram(modules, {{ scopeDescription: "repository" }});
const callbackFirst = buildCallbackRegistrationMapDiagram(modules, {{ scopeDescription: "repository" }});
const dynamicSecond = buildDynamicCodeWatchlistDiagram(modules, {{ scopeDescription: "repository" }});
const callbackSecond = buildCallbackRegistrationMapDiagram(modules, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  dynamicDefinitionStable: dynamicFirst.definition === dynamicSecond.definition,
  dynamicStatusStable: dynamicFirst.statusMessage === dynamicSecond.statusMessage,
  callbackDefinitionStable: callbackFirst.definition === callbackSecond.definition,
  callbackStatusStable: callbackFirst.statusMessage === callbackSecond.statusMessage,
  dynamicStatusMessage: dynamicFirst.statusMessage,
  dynamicStats: dynamicFirst.stats,
}}));
"""

    payload = _run_node_module(script)

    assert payload["dynamicDefinitionStable"] is True
    assert payload["dynamicStatusStable"] is True
    assert payload["callbackDefinitionStable"] is True
    assert payload["callbackStatusStable"] is True

    dynamic_status = payload["dynamicStatusMessage"]
    assert isinstance(dynamic_status, str)
    assert "Dynamic Code Watchlist" in dynamic_status
    assert "1 module" in dynamic_status

    stats = payload["dynamicStats"]
    assert stats["modules"] == 1
    assert stats["flagTriggerCount"] == 1
    assert stats["eventCount"] == 1
