from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
VIEWER_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "viewer.js"
)

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


def test_io_effects_view_respects_module_scope() -> None:
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
  module_id: 'alpha.io',
  relative_path: 'alpha/io.py',
}});
moduleRecord.functions = [
  'alpha.io::load',
  'alpha.io::save',
];

const fnLoad = api.createFunctionRecord({{
  name: 'load',
  io_effects: {{ reads: true, writes: true, env: false, network: false }},
}}, 'alpha.io');

const fnSave = api.createFunctionRecord({{
  name: 'save',
  io_effects: {{ reads: false, writes: true, env: false, network: false }},
}}, 'alpha.io');

const modules = new Map();
modules.set(moduleRecord.moduleId, moduleRecord);

const functions = new Map([
  [fnLoad.id, fnLoad],
  [fnSave.id, fnSave],
]);

api.setNormalizedDataForTest({{
  modules,
  functions,
  callGraph: {{ functions: new Map() }},
}});
api.setLevelSelectionsForTest({{ moduleId: 'alpha.io' }});

const result = api.buildIoEffectsViewDefinitionForTest();

api.resetViewStateForTest();

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  hasDefinition: typeof result.definition === 'string',
  statusMessage: result.statusMessage,
  stats: result.stats,
}}));
"""
    )

    payload = _run_node_module(script)

    assert payload["hasDefinition"] is True
    assert "alpha.io" in payload["statusMessage"]
    stats = payload["stats"]
    assert stats["modules"] == 1
    assert stats["functions"] == 2
    assert stats["effectFlags"] == 3


def test_io_effects_view_falls_back_to_repository_scope() -> None:
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

const moduleIo = api.createModuleRecord({{
  module_id: 'alpha.io',
  relative_path: 'alpha/io.py',
}});
moduleIo.functions = ['alpha.io::load'];

const moduleSafe = api.createModuleRecord({{
  module_id: 'beta.safe',
  relative_path: 'beta/safe.py',
}});
moduleSafe.functions = ['beta.safe::noop'];

const fnLoad = api.createFunctionRecord({{
  name: 'load',
  io_effects: {{ reads: true, writes: false, env: false, network: false }},
}}, 'alpha.io');

const fnNoop = api.createFunctionRecord({{
  name: 'noop',
  io_effects: {{ reads: false, writes: false, env: false, network: false }},
}}, 'beta.safe');

const modules = new Map([
  [moduleIo.moduleId, moduleIo],
  [moduleSafe.moduleId, moduleSafe],
]);

const functions = new Map([
  [fnLoad.id, fnLoad],
  [fnNoop.id, fnNoop],
]);

api.setNormalizedDataForTest({{
  modules,
  functions,
  callGraph: {{ functions: new Map() }},
}});
api.setLevelSelectionsForTest({{ moduleId: 'beta.safe' }});

const result = api.buildIoEffectsViewDefinitionForTest();

api.resetViewStateForTest();

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  message: result.message ?? null,
  statusMessage: result.statusMessage ?? null,
  details: result.statusDetails ?? [],
}}));
"""
    )

    payload = _run_node_module(script)

    assert payload["message"] is None
    assert payload["statusMessage"] is not None
    assert "repository" in payload["statusMessage"]
    assert "Showing repository map instead" in payload["statusMessage"]
    info_detail = payload["details"][0]
    assert info_detail["type"] == "info"
    assert "fallback" in info_detail["title"].lower()
