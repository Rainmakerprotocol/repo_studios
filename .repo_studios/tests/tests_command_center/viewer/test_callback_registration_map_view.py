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
    / "callback_registration_map.js"
)
VIEWER_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "viewer.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected callback registration map builder at {MODULE_PATH}")


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
    )
    if result.stderr.strip():
        pytest.fail(f"Node.js script wrote to stderr: {result.stderr}")
    return json.loads(result.stdout.strip())


def test_callback_registration_map_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildCallbackRegistrationMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.callbacks", {{
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
        function: "alpha.callbacks::register_handlers",
        expression: "dispatcher.register_callback",
        method: "register_callback",
  target: "gamma.handlers.handle_event",
  targetKind: "attribute",
  targetVia: "listener",
        resolved: "gamma.handlers.handle_event",
        module: "alpha.dispatcher",
        root: "dispatcher",
        lineno: 45,
      }},
      {{
        function: "alpha.callbacks::register_timer",
        expression: "timer.add_listener",
        method: "add_listener",
  targetKind: "name",
        module: "alpha.timer",
        root: "timer",
        lineno: 88,
      }},
    ],
  }}],
  ["beta.handlers", {{ callbackRegistrations: [] }}],
]);

const result = buildCallbackRegistrationMapDiagram(modules, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  definition: result.definition,
  statusMessage: result.statusMessage,
  stats: result.stats,
  details: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    definition = payload["definition"]
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "alpha_callbacks__register_handlers" in definition
    assert "class emitter_alpha_callbacks__register_handlers emitter" in definition
    assert "beta_handlers_handle_event" in definition
    assert "Targets: 2" in definition

    status = payload["statusMessage"]
    assert "Callback Registration Map" in status
    assert "2 emitters" in status
    assert "3 registrations" in status
    assert "1 unresolved" in status

    stats = payload["stats"]
    assert stats["modules"] == 1
    assert stats["emitters"] == 2
    assert stats["targets"] == 3
    assert stats["registrations"] == 3
    assert stats["unresolvedTargets"] == 1

    channel_breakdown = {entry["label"]: entry["count"] for entry in stats["channelBreakdown"]}
    assert channel_breakdown == {"callback": 1, "listener": 1, "add_listener()": 1}

    details = payload["details"]
    assert isinstance(details, list)
    assert details[0]["type"] == "stat-summary"
    top_emitters = next((entry for entry in details if entry["title"] == "Top Emitters"), None)
    assert top_emitters is not None


def test_callback_registration_map_returns_message_when_no_data() -> None:
    script = f"""
import {{ buildCallbackRegistrationMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.callbacks", {{ callbackRegistrations: [] }}],
]);

const result = buildCallbackRegistrationMapDiagram(modules);

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"].startswith("No callback registrations recorded")


def test_callback_registration_map_definition_is_stable() -> None:
    script = f"""
import {{ buildCallbackRegistrationMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.callbacks", {{
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
  }}],
]);

const first = buildCallbackRegistrationMapDiagram(modules);
const second = buildCallbackRegistrationMapDiagram(modules);

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


def test_callback_registration_map_view_falls_back_to_repository_scope() -> None:
    script = f"""
if (!globalThis.window) {{
  globalThis.window = {{}};
}}
if (!window.addEventListener) {{
  window.addEventListener = () => {{}};
}}
if (!window.removeEventListener) {{
  window.removeEventListener = () => {{}};
}}
if (!window.viewerConfig) {{
  window.viewerConfig = {{}};
}}
if (!window.mermaid) {{
  window.mermaid = {{ initialize: () => {{}}, render: async () => ({{ svg: '' }}) }};
}}
if (!globalThis.document) {{
  globalThis.document = {{ readyState: 'loading', addEventListener: () => {{}} }};
}}
if (!globalThis.localStorage) {{
  globalThis.localStorage = {{ getItem: () => null, setItem: () => {{}}, removeItem: () => {{}} }};
}}

const originalLog = console.log;
const originalWarn = console.warn || (() => {{}});
console.log = () => {{}};
console.warn = () => {{}};

const viewer = await import('{VIEWER_PATH.as_uri()}');
const api = viewer.__test__;

api.resetViewStateForTest();

const moduleRecord = api.createModuleRecord({{
  module_id: 'alpha.callbacks',
  relative_path: 'alpha/callbacks.py',
  path: 'alpha/callbacks.py',
  import_graph: [],
  functions: [],
  callback_registrations: [
    {{
      expression: 'dispatcher.register_callback',
      method: 'register_callback',
      target: 'beta.handlers.handle_event',
  targetKind: 'attribute',
  targetVia: 'callback',
      resolved: 'beta.handlers.handle_event',
      module: 'alpha.dispatcher',
      root: 'dispatcher',
      lineno: 42,
      function: 'alpha.callbacks::register_handlers',
    }},
  ],
}});

const modules = new Map();
if (moduleRecord) {{
  modules.set(moduleRecord.id, moduleRecord);
}}

const normalized = {{
  modules,
  functions: new Map(),
  callGraph: {{ functions: new Map() }},
  metrics: {{}},
}};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({{ rootId: 'gamma.domain', domainId: null, moduleId: null }});

const result = api.buildCallbackRegistrationMapViewDefinitionForTest();

api.resetViewStateForTest();

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  hasDefinition: typeof result.definition === 'string',
  statusMessage: result.statusMessage,
  statusDetails: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    assert payload["hasDefinition"] is True
    assert "Showing repository map" in payload["statusMessage"]
    info_detail = payload["statusDetails"][0]
    assert info_detail["type"] == "info"
    assert "fallback" in info_detail["title"].lower()
