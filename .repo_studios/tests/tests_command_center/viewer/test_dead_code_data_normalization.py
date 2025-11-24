from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
VIEWER_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "viewer.js"

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


def _scaffold_viewer_environment() -> str:
    return """
if (!globalThis.window) {
  globalThis.window = {};
}
if (!window.addEventListener) {
  window.addEventListener = () => {};
}
if (!window.removeEventListener) {
  window.removeEventListener = () => {};
}
if (!window.viewerConfig) {
  window.viewerConfig = {};
}
if (!window.mermaid) {
  window.mermaid = { initialize: () => {}, render: async () => ({ svg: '' }) };
}
if (!globalThis.document) {
  globalThis.document = { readyState: 'loading', addEventListener: () => {} };
}
if (!globalThis.localStorage) {
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
}
"""


def test_dead_code_normalization_sanitizes_unused_imports_and_unreachable_functions() -> None:
    script = (
        _scaffold_viewer_environment()
        + f"""
const originalLog = console.log;
const originalWarn = console.warn || (() => {{}});
console.log = () => {{}};
console.warn = () => {{}};

const viewer = await import('{VIEWER_PATH.as_uri()}');
const api = viewer.__test__;

api.resetViewStateForTest();

const moduleRecord = api.createModuleRecord({{
  module_id: 'alpha.core',
  relative_path: 'alpha/core.py',
  unused_imports: [
    {{ target: 'collections.Counter', module: 'collections', imported_as: 'Counter', kind: 'from', lineno: 12 }},
    {{ target: 'sys', module: null, imported_as: 'sys', kind: 'import', lineno: 4 }},
    {{ target: 'sys', module: null, imported_as: 'sys', kind: 'import', lineno: 4 }},  // duplicate
  ],
  unreachable_functions: [
    {{ qualified_name: 'alpha.core::helper', name: 'helper', kind: 'function', lineno: 88 }},
    {{ qualified_name: 'alpha.core::utilities.Helper.run', name: 'run', parent_class: 'utilities.Helper', kind: 'method', lineno: 144 }},
  ],
}});

const response = {{
  unusedImports: moduleRecord.unusedImports,
  unreachableFunctions: moduleRecord.unreachableFunctions,
}};

api.resetViewStateForTest();
console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify(response));
"""
    )

    payload = _run_node_module(script)

    unused_imports = payload["unusedImports"]
    assert unused_imports == [
        {
            "target": "sys",
            "module": None,
            "importedAs": "sys",
            "kind": "import",
            "lineno": 4,
        },
        {
            "target": "collections.Counter",
            "module": "collections",
            "importedAs": "Counter",
            "kind": "from",
            "lineno": 12,
        },
    ]

    unreachable = payload["unreachableFunctions"]
    assert unreachable == [
        {
            "name": "helper",
            "qualifiedName": "alpha.core::helper",
            "parentClass": None,
            "kind": "function",
            "lineno": 88,
            "moduleId": "alpha.core",
        },
        {
            "name": "run",
            "qualifiedName": "alpha.core::utilities.Helper.run",
            "parentClass": "utilities.Helper",
            "kind": "method",
            "lineno": 144,
            "moduleId": "alpha.core",
        },
    ]
