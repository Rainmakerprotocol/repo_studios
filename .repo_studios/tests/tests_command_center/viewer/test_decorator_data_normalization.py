from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
VIEWER_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "viewer.js"

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


def test_create_function_record_normalizes_decorators() -> None:
    script = """
globalThis.window = globalThis.window || {};
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
  window.mermaid = { initialize: () => {}, render: async () => ({ svg: "" }) };
}

globalThis.document = {
  readyState: "loading",
  addEventListener: () => {},
};

globalThis.localStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
};

const originalLog = console.log;
console.log = () => {};

const { __test__ } = await import("MODULE_PATH");

const fn = {
  name: "decorate",
  decorators: [" identity ", { name: "retry " }, ""],
  decorators_detailed: [
    {
      name: "identity",
      module: "effects.module",
      qualified_name: "effects.module.identity",
      args: [],
      kwargs: {},
      call: "@identity",
    },
    {
      name: "retry ",
      args: [" 3 ", 5],
      kwargs: { on: "'ValueError' ", jitter: "0.1" },
      expression: " @retry(3, on='ValueError', jitter=0.1) ",
    },
    null,
  ],
};

const record = __test__.createFunctionRecord(fn, "alpha.module");

console.log = originalLog;

console.log(JSON.stringify({
  id: record.id,
  decorators: record.decorators,
  details: record.decoratorsDetailed,
}));
"""
    script = script.replace("MODULE_PATH", VIEWER_MODULE_PATH.as_uri())
    payload = _run_node_module(script)

    assert payload["id"] == "alpha.module::decorate"
    assert payload["decorators"] == ["identity", "retry"]
    assert payload["details"] == [
        {
            "name": "identity",
            "module": "effects.module",
            "qualifiedName": "effects.module.identity",
            "args": [],
            "kwargs": [],
            "expression": "@identity",
        },
        {
            "name": "retry",
            "module": None,
            "qualifiedName": None,
            "args": ["3", "5"],
            "kwargs": [
                {"name": "on", "value": "'ValueError'"},
                {"name": "jitter", "value": "0.1"},
            ],
            "expression": "@retry(3, on='ValueError', jitter=0.1)",
        },
    ]
