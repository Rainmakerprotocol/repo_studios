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


def test_test_coverage_mapping_requires_coverage_signals() -> None:
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
}});
moduleRecord.functions = ['alpha.core::utility'];

const modules = new Map([[moduleRecord.moduleId, moduleRecord]]);

const functionRecord = api.createFunctionRecord({{
  name: 'utility',
  line_count: 8,
}}, 'alpha.core');
const functions = new Map([[functionRecord.id, functionRecord]]);

api.setNormalizedDataForTest({{
  modules,
  functions,
}});

const result = api.buildTestCoverageMappingViewDefinitionForTest();

api.resetViewStateForTest();
console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  message: result.message ?? null,
}}));
"""
    )

    payload = _run_node_module(script)

    assert payload["message"] == "Test coverage metadata is not available in this CommandView artifact."


def test_test_coverage_mapping_falls_back_to_repository_when_scope_empty() -> None:
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

const moduleCovered = api.createModuleRecord({{
  module_id: 'alpha.core',
  relative_path: 'alpha/core.py',
  coverage_signals: {{
    imports: ['tests.test_alpha'],
    has_matches: true,
  }},
}});
moduleCovered.functions = ['alpha.core::covered', 'alpha.core::partial'];

const moduleScoped = api.createModuleRecord({{
  module_id: 'beta.utils',
  relative_path: 'beta/utils.py',
}});
moduleScoped.functions = ['beta.utils::helper'];

const modules = new Map([
  [moduleCovered.moduleId, moduleCovered],
  [moduleScoped.moduleId, moduleScoped],
]);

const fnCovered = api.createFunctionRecord({{
  name: 'covered',
  coverage: 1.0,
  line_count: 12,
}}, 'alpha.core');
const fnPartial = api.createFunctionRecord({{
  name: 'partial',
  coverage: 0.55,
  line_count: 18,
}}, 'alpha.core');
const fnHelper = api.createFunctionRecord({{
  name: 'helper',
  line_count: 9,
}}, 'beta.utils');

const functions = new Map([
  [fnCovered.id, fnCovered],
  [fnPartial.id, fnPartial],
  [fnHelper.id, fnHelper],
]);

api.setNormalizedDataForTest({{
  modules,
  functions,
}});
api.setLevelSelectionsForTest({{
  moduleId: 'beta.utils',
}});

const result = api.buildTestCoverageMappingViewDefinitionForTest();

api.resetViewStateForTest();
console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  definitionPrefix: typeof result.definition === 'string' ? result.definition.slice(0, 8) : null,
  statusMessage: result.statusMessage ?? null,
  fallbackIncluded: result.statusMessage?.includes('Showing repository coverage instead.') ?? false,
  displayedModules: result.stats?.displayedModules ?? null,
  moduleCount: result.stats?.moduleCount ?? null,
}}));
"""
    )

    payload = _run_node_module(script)

    assert payload["definitionPrefix"] == "graph TD"
    assert payload["fallbackIncluded"] is True
    assert payload["displayedModules"] == 1
    assert payload["moduleCount"] == 1
    assert "Rendered Test Coverage Mapping" in payload["statusMessage"]


def test_module_has_coverage_telemetry_detects_signals() -> None:
    script = (
        _scaffold_viewer_environment()
        + f"""
const originalLog = console.log;
const originalWarn = console.warn || (() => {{}});
console.log = () => {{}};
console.warn = () => {{}};

const viewer = await import('{VIEWER_PATH.as_uri()}');
const api = viewer.__test__;

const moduleWithCoverage = api.createModuleRecord({{
  module_id: 'alpha.core',
  coverage_signals: {{ imports: ['tests.test_alpha'] }},
}});
moduleWithCoverage.functions = ['alpha.core::covered'];

const moduleWithoutCoverage = api.createModuleRecord({{
  module_id: 'beta.utils',
}});
moduleWithoutCoverage.functions = ['beta.utils::helper'];

const fnCovered = api.createFunctionRecord({{
  name: 'covered',
  coverage: 0.9,
}}, 'alpha.core');
const fnHelper = api.createFunctionRecord({{
  name: 'helper',
}}, 'beta.utils');

const functions = new Map([
  [fnCovered.id, fnCovered],
  [fnHelper.id, fnHelper],
]);

const withCoverage = api.moduleHasCoverageTelemetryForTest(moduleWithCoverage, functions);
const withoutCoverage = api.moduleHasCoverageTelemetryForTest(moduleWithoutCoverage, functions);

api.resetViewStateForTest();
console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  withCoverage,
  withoutCoverage,
}}));
"""
    )

    payload = _run_node_module(script)

    assert payload["withCoverage"] is True
    assert payload["withoutCoverage"] is False
