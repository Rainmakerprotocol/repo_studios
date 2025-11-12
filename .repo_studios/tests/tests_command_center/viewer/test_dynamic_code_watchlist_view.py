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
    / "dynamic_code_watchlist.js"
)
VIEWER_PATH = (
  REPO_STUDIOS_ROOT
  / "command_center"
  / "viewer"
  / "ui"
  / "viewer.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected dynamic code watchlist builder at {MODULE_PATH}")

if not VIEWER_PATH.exists():  # pragma: no cover - guard against missing assets
  raise AssertionError(f"Expected viewer module at {VIEWER_PATH}")


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


def test_dynamic_code_watchlist_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildDynamicCodeWatchlistDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.audit", {{
    dynamicCode: {{
      hasDynamic: true,
      flags: {{ exec: true, dynamicImport: false, metaclass: false, globalsMutation: true }},
      activeFlags: ["exec", "globalsMutation"],
      flagCount: 2,
      events: [
        {{ kind: "exec", detail: "exec(stmt)", lineno: 12 }},
        {{ kind: "dynamic_import", detail: "importlib.import_module('alpha.audit')", lineno: 40 }},
      ],
      eventCount: 2,
    }},
  }}],
  ["beta.loader", {{
    dynamicCode: {{
      hasDynamic: true,
      flags: {{ exec: false, dynamicImport: true, metaclass: false, globalsMutation: false }},
      activeFlags: ["dynamicImport"],
      flagCount: 1,
      events: [
        {{ kind: "dynamic_import", detail: "importlib.import_module('beta.plugins')", lineno: 22 }},
      ],
      eventCount: 1,
    }},
  }}],
  ["gamma.safe", {{
    dynamicCode: null,
  }}],
]);

const result = buildDynamicCodeWatchlistDiagram(modules, {{ scopeDescription: "repository" }});

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
    assert "alpha.audit" in definition
    assert "Flags: exec(), globals mutation" in definition

    status = payload["statusMessage"]
    assert status == "Rendered Dynamic Code Watchlist for repository (2 modules, 3 flag triggers, 3 events)."

    stats = payload["stats"]
    assert stats["modules"] == 2
    assert stats["flagTriggerCount"] == 3
    assert stats["eventCount"] == 3
    assert stats["flagTypes"] == 3

    flag_breakdown = {entry["label"]: entry["count"] for entry in stats["flagBreakdown"]}
    assert flag_breakdown == {
        "dynamic import": 1,
        "exec()": 1,
        "globals mutation": 1,
    }

    details = payload["details"]
    assert isinstance(details, list)
    assert details[0]["type"] == "stat-summary"


def test_dynamic_code_watchlist_returns_message_when_no_data() -> None:
    script = f"""
import {{ buildDynamicCodeWatchlistDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.audit", {{ dynamicCode: null }}],
]);

const result = buildDynamicCodeWatchlistDiagram(modules);

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"] == "No dynamic code signals recorded for this CommandView artifact."


def test_dynamic_code_watchlist_definition_is_stable() -> None:
    script = f"""
import {{ buildDynamicCodeWatchlistDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.audit", {{
    dynamicCode: {{
      hasDynamic: true,
      flags: {{ exec: true, dynamicImport: true, metaclass: false, globalsMutation: false }},
      activeFlags: ["exec", "dynamicImport"],
      flagCount: 2,
      events: [
        {{ kind: "exec", detail: "exec(stmt)", lineno: 12 }},
        {{ kind: "dynamic_import", detail: "importlib.import_module('alpha.audit')", lineno: 40 }},
      ],
      eventCount: 2,
    }},
  }}],
]);

const first = buildDynamicCodeWatchlistDiagram(modules);
const second = buildDynamicCodeWatchlistDiagram(modules);

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


def test_dynamic_code_watchlist_view_falls_back_to_repository_scope() -> None:
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
  module_id: 'alpha.audit',
  relative_path: 'alpha/audit.py',
  path: 'alpha/audit.py',
  import_graph: [],
  functions: [],
  dynamic_code: {{
    flags: {{ exec: true, dynamic_import: true, metaclass: false, globals_mutation: false }},
    events: [
      {{ kind: 'exec', detail: 'exec(stmt)', lineno: 22 }},
    ],
  }},
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
api.setLevelSelectionsForTest({{ moduleId: 'gamma.missing' }});

const result = api.buildDynamicCodeWatchlistViewDefinitionForTest();

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
    assert "Showing repository watchlist" in payload["statusMessage"]
    info_detail = payload["statusDetails"][0]
    assert info_detail["type"] == "info"
    assert "fallback" in info_detail["title"].lower()
