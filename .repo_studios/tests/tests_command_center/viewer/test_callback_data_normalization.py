from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
VIEWER_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "viewer.js"


@pytest.fixture(scope="module", autouse=True)
def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Node.js runtime is required for viewer normalization tests: {exc}")


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


def test_callback_metadata_normalization() -> None:
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
console.log = () => {{}};

const {{ __test__ }} = await import('{VIEWER_MODULE_PATH.as_uri()}');

const moduleRecord = __test__.createModuleRecord({{
  module_id: 'alpha.callbacks',
  relative_path: 'alpha/callbacks.py',
  path: 'alpha/callbacks.py',
  import_graph: [],
  functions: [],
  callback_registrations: [
    {{
      expression: 'dispatcher.register_callback',
      method: 'register_callback',
      kind: 'attribute',
      root: 'dispatcher',
      module: 'alpha.dispatcher',
      resolved: 'alpha.dispatcher.register_callback',
      target: 'beta.handlers.handle_event',
      target_kind: 'attribute',
      target_via: 'callback',
      lineno: 42,
      function: 'alpha.callbacks::register_handlers',
    }},
    {{
      expression: 'timer.add_listener',
      kind: 'attribute',
      root: 'timer',
      module: 'alpha.timer',
      target: 'alpha.callbacks::on_tick',
      target_kind: 'name',
      lineno: 88,
      function: 'alpha.callbacks::register_timer',
    }},
  ],
}});

const functionRecord = __test__.createFunctionRecord({{
  qualified_name: 'alpha.callbacks::register_handlers',
  name: 'register_handlers',
  line: 10,
  callback_registrations: [
    {{
      expression: 'dispatcher.register_callback',
      method: 'register_callback',
      kind: 'attribute',
      root: 'dispatcher',
      module: 'alpha.dispatcher',
      resolved: 'alpha.dispatcher.register_callback',
      target: 'beta.handlers.handle_event',
      target_kind: 'attribute',
      target_via: 'callback',
      lineno: 42,
    }},
  ],
  logging_calls: [],
  decorators: [],
  decorators_detailed: [],
  calls: [],
}}, 'alpha.callbacks');

console.log = originalLog;

console.log(JSON.stringify({{
  module: moduleRecord.callbackRegistrations,
  function: functionRecord.callbackRegistrations,
}}));
"""

    payload = _run_node_module(script)

    assert payload["module"] == [
        {
            "expression": "dispatcher.register_callback",
            "method": "register_callback",
            "kind": "attribute",
            "root": "dispatcher",
            "module": "alpha.dispatcher",
            "resolved": "alpha.dispatcher.register_callback",
            "target": "beta.handlers.handle_event",
            "targetKind": "attribute",
            "targetVia": "callback",
            "lineno": 42,
            "function": "alpha.callbacks::register_handlers",
        },
        {
            "expression": "timer.add_listener",
            "method": None,
            "kind": "attribute",
            "root": "timer",
            "module": "alpha.timer",
            "resolved": None,
            "target": "alpha.callbacks::on_tick",
            "targetKind": "name",
            "targetVia": None,
            "lineno": 88,
            "function": "alpha.callbacks::register_timer",
        },
    ]

    assert payload["function"] == [
        {
            "expression": "dispatcher.register_callback",
            "method": "register_callback",
            "kind": "attribute",
            "root": "dispatcher",
            "module": "alpha.dispatcher",
            "resolved": "alpha.dispatcher.register_callback",
            "target": "beta.handlers.handle_event",
            "targetKind": "attribute",
            "targetVia": "callback",
            "lineno": 42,
        }
    ]
