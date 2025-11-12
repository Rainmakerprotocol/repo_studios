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


def test_global_variable_usage_view_respects_module_scope() -> None:
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
  module_id: 'alpha.config',
  relative_path: 'alpha/config.py',
  globals: [
    {{ name: 'SETTINGS', value_kind: 'dict', lineno: 5 }},
    {{ name: 'FLAG', value_kind: 'bool', lineno: 12 }},
  ],
}});

moduleRecord.functions = [
  'alpha.config::load',
  'alpha.config::toggle',
];

const fnLoad = api.createFunctionRecord({{
  name: 'load',
  used_globals: ['SETTINGS'],
}}, 'alpha.config');

const fnToggle = api.createFunctionRecord({{
  name: 'toggle',
  used_globals: ['SETTINGS', 'FLAG'],
}}, 'alpha.config');

const modules = new Map();
modules.set(moduleRecord.moduleId, moduleRecord);

const functions = new Map([
  [fnLoad.id, fnLoad],
  [fnToggle.id, fnToggle],
]);

api.setNormalizedDataForTest({{
  modules,
  functions,
  callGraph: {{ functions: new Map() }},
}});
api.setLevelSelectionsForTest({{ moduleId: 'alpha.config' }});

const result = api.buildGlobalVariableUsageViewDefinitionForTest();

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
    assert "alpha.config" in payload["statusMessage"]
    stats = payload["stats"]
    assert stats["modules"] == 1
    assert stats["globals"] == 2
    assert stats["functions"] == 2
    assert stats["usageCount"] == 3


def test_global_variable_usage_view_falls_back_to_repository_scope() -> None:
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

const moduleConfig = api.createModuleRecord({{
  module_id: 'alpha.config',
  relative_path: 'alpha/config.py',
  globals: [
    {{ name: 'SETTINGS', value_kind: 'dict', lineno: 5 }},
  ],
}});
moduleConfig.functions = ['alpha.config::load'];

const moduleSafe = api.createModuleRecord({{
  module_id: 'beta.safe',
  relative_path: 'beta/safe.py',
  globals: [],
}});
moduleSafe.functions = ['beta.safe::noop'];

const fnLoad = api.createFunctionRecord({{
  name: 'load',
  used_globals: ['SETTINGS'],
}}, 'alpha.config');

const fnNoop = api.createFunctionRecord({{
  name: 'noop',
  used_globals: [],
}}, 'beta.safe');

const modules = new Map([
  [moduleConfig.moduleId, moduleConfig],
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

const result = api.buildGlobalVariableUsageViewDefinitionForTest();

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
