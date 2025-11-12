from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
VIEWER_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "viewer.js"
)

if not VIEWER_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected viewer module at {VIEWER_MODULE_PATH}")


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


def test_normalize_dynamic_code_extracts_flags_and_events() -> None:
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

const {{ __test__ }} = await import('{VIEWER_MODULE_PATH.as_uri()}');

const payload = __test__.normalizeDynamicCode({{
  flags: {{
    exec: true,
    dynamic_import: true,
    metaclass: false,
    globals_mutation: true,
  }},
  events: [
    {{ kind: 'dynamic_import', detail: "importlib.import_module('beta.plugins')", lineno: 40 }},
    {{ kind: 'exec', detail: 'exec(stmt)', lineno: '10' }},
    {{ kind: 'dynamic_import', detail: "importlib.import_module('alpha.loader')", lineno: 15 }},
    {{ kind: 'globals_mutation', detail: "globals()['FLAG'] = True" }},
    {{ detail: 'synthetic detail', lineno: 90 }},
    null,
    {{}},
  ],
}});

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify(payload));
"""

    payload = _run_node_module(script)

    assert payload["hasDynamic"] is True
    assert payload["flagCount"] == 3
    assert payload["eventCount"] == 6

    flags = payload["flags"]
    assert flags == {
        "exec": True,
        "dynamicImport": True,
        "metaclass": False,
        "globalsMutation": True,
    }

    active_flags = payload["activeFlags"]
    assert active_flags == ["exec", "dynamicImport", "globalsMutation"]

    events = payload["events"]
    assert len(events) == 6
    assert events[0] == {
        "kind": "dynamic_import",
        "detail": "importlib.import_module('alpha.loader')",
        "lineno": 15,
    }
    assert events[1] == {
        "kind": "dynamic_import",
        "detail": "importlib.import_module('beta.plugins')",
        "lineno": 40,
    }
    assert events[2] == {
        "kind": "exec",
        "detail": "exec(stmt)",
        "lineno": 10,
    }
    assert events[3] == {
        "kind": "globals_mutation",
        "detail": "globals()['FLAG'] = True",
        "lineno": None,
    }
    assert events[4] == {
        "kind": "unknown",
        "detail": "synthetic detail",
        "lineno": 90,
    }
    assert events[5] == {
        "kind": "unknown",
        "detail": None,
        "lineno": None,
    }


def test_normalize_dynamic_code_returns_null_when_empty() -> None:
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

const {{ __test__ }} = await import('{VIEWER_MODULE_PATH.as_uri()}');

const payload = __test__.normalizeDynamicCode({{
  flags: {{ exec: false, dynamic_import: false }},
  events: [],
}});

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify(payload));
"""

    payload = _run_node_module(script)

    assert payload is None
