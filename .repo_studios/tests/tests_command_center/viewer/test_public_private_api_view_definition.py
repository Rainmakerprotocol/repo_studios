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


@pytest.fixture(scope="module", autouse=True)
def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Node.js runtime is required for viewer view-definition tests: {exc}")


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


def _bootstrap_viewer_globals() -> str:
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


def test_public_private_api_view_falls_back_to_repository() -> None:
    script = """
__BOOTSTRAP__

const originalLog = console.log;
console.log = () => {};

const { __test__: api } = await import('__VIEWER__');

const emptyModule = api.createModuleRecord({
  module_id: 'alpha.empty',
  relative_path: 'alpha/empty.py',
  path: 'alpha/empty.py',
  imports_detailed: [],
  exports: { symbols: [], missing: [], dynamic: false },
});

const apiModule = api.createModuleRecord({
  module_id: 'beta.api',
  relative_path: 'beta/api.py',
  path: 'beta/api.py',
  imports_detailed: [],
  exports: { symbols: ['public_func'], missing: [], dynamic: false },
});

const publicFunction = api.createFunctionRecord({
  name: 'public_func',
  qualified_name: 'beta.api::public_func',
  line: 10,
  signature: 'def public_func()',
  coverage: 0.8,
  type_hint_coverage: 0.6,
  docstring_quality: { exists: true },
}, 'beta.api');
const privateFunction = api.createFunctionRecord({
  name: '_internal',
  qualified_name: 'beta.api::_internal',
  line: 18,
  signature: 'def _internal()',
  coverage: 0.4,
}, 'beta.api');

apiModule.functions = [publicFunction.id, privateFunction.id];

const functions = new Map([
  [publicFunction.id, publicFunction],
  [privateFunction.id, privateFunction],
]);
const classes = new Map();

const apiSurface = api.buildModuleApiSurfaceForTest(apiModule, functions, classes);
apiModule.apiSurface = apiSurface;

const modules = new Map([
  [emptyModule.id, emptyModule],
  [apiModule.id, apiModule],
]);

const normalized = {
  modules,
  functions,
  callGraph: { functions: new Map() },
  metrics: {},
  levels: null,
  screeningHistory: null,
};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({ rootId: null, domainId: null, moduleId: emptyModule.id });

const result = api.buildPublicVsPrivateApiViewDefinitionForTest();

api.resetViewStateForTest();
console.log = originalLog;

console.log(JSON.stringify({
  hasDefinition: typeof result.definition === 'string',
  statusMessage: result.statusMessage,
  statusDetails: result.statusDetails,
  stats: result.stats,
}));
"""
    script = script.replace("__BOOTSTRAP__", _bootstrap_viewer_globals())
    script = script.replace("__VIEWER__", VIEWER_MODULE_PATH.as_uri())

    payload = _run_node_module(script)

    assert payload["hasDefinition"] is True
    assert "Showing repository coverage instead" in payload["statusMessage"]
    status_details = payload["statusDetails"]
    assert isinstance(status_details, list)
    assert status_details
    assert status_details[0]["type"] == "info"
    assert "alpha.empty" in status_details[0]["description"]
    stats = payload["stats"]
    assert stats["totalModules"] == 1
    assert isinstance(stats.get("modulesWithoutDeclaredExports"), list)


def test_public_private_api_view_scoped_module_renders_without_fallback() -> None:
    script = """
__BOOTSTRAP__

const originalLog = console.log;
console.log = () => {};

const { __test__: api } = await import('__VIEWER__');

const apiModule = api.createModuleRecord({
  module_id: 'gamma.surface',
  relative_path: 'gamma/surface.py',
  path: 'gamma/surface.py',
  imports_detailed: [],
  exports: { symbols: ['exposed'], missing: ['ghost'], dynamic: false },
});

const exportedFunction = api.createFunctionRecord({
  name: 'exposed',
  qualified_name: 'gamma.surface::exposed',
  line: 12,
  signature: 'def exposed()',
  coverage: 0.9,
}, 'gamma.surface');
const implicitFunction = api.createFunctionRecord({
  name: 'helper',
  qualified_name: 'gamma.surface::helper',
  line: 20,
  signature: 'def helper()',
  coverage: 0.5,
}, 'gamma.surface');

apiModule.functions = [exportedFunction.id, implicitFunction.id];

const functions = new Map([
  [exportedFunction.id, exportedFunction],
  [implicitFunction.id, implicitFunction],
]);
const classes = new Map();

const apiSurface = api.buildModuleApiSurfaceForTest(apiModule, functions, classes);
apiModule.apiSurface = apiSurface;

const modules = new Map([[apiModule.id, apiModule]]);
const normalized = {
  modules,
  functions,
  callGraph: { functions: new Map() },
  metrics: {},
  levels: null,
  screeningHistory: null,
};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({ rootId: null, domainId: null, moduleId: apiModule.id });

const result = api.buildPublicVsPrivateApiViewDefinitionForTest();

api.resetViewStateForTest();
console.log = originalLog;

console.log(JSON.stringify({
  hasDefinition: typeof result.definition === 'string',
  statusMessage: result.statusMessage,
  statusDetails: result.statusDetails,
  stats: result.stats,
}));
"""
    script = script.replace("__BOOTSTRAP__", _bootstrap_viewer_globals())
    script = script.replace("__VIEWER__", VIEWER_MODULE_PATH.as_uri())

    payload = _run_node_module(script)

    assert payload["hasDefinition"] is True
    assert "gamma.surface" in payload["statusMessage"]
    assert "repository" not in payload["statusMessage"]
    status_details = payload["statusDetails"]
    assert isinstance(status_details, list)
    assert status_details[0]["type"] == "stat-summary"
    stats = payload["stats"]
    assert stats["totalModules"] == 1
    assert stats["missing"] >= 1
    assert stats["modulesWithMissingExports"][0]["moduleId"] == "gamma.surface"
