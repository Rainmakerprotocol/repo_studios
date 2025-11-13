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
    encoding="utf-8",
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


def test_dead_code_detection_requires_dead_code_signals() -> None:
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

const modules = new Map([[moduleRecord.moduleId, moduleRecord]]);

api.setNormalizedDataForTest({{
  modules,
}});

const result = api.buildDeadCodeDetectionViewDefinitionForTest();

api.resetViewStateForTest();
console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  message: result.message ?? null,
}}));
"""
    )

    payload = _run_node_module(script)

    assert payload["message"] == "Dead code signals are not available in this CommandView artifact."


def test_dead_code_detection_falls_back_to_repository_when_scope_empty() -> None:
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

const moduleSignals = api.createModuleRecord({{
  module_id: 'alpha.core',
  relative_path: 'alpha/core.py',
  unreachable_functions: [
    {{ qualified_name: 'alpha.core::orphan', name: 'orphan', lineno: 44 }},
  ],
  unused_imports: [
    {{ target: 'json', imported_as: 'json', lineno: 12 }},
  ],
}});

const moduleScoped = api.createModuleRecord({{
  module_id: 'beta.utils',
  relative_path: 'beta/utils.py',
}});

const modules = new Map([
  [moduleSignals.moduleId, moduleSignals],
  [moduleScoped.moduleId, moduleScoped],
]);

api.setNormalizedDataForTest({{
  modules,
}});
api.setLevelSelectionsForTest({{
  moduleId: 'beta.utils',
}});

const result = api.buildDeadCodeDetectionViewDefinitionForTest();

api.resetViewStateForTest();
console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  definitionPrefix: typeof result.definition === 'string' ? result.definition.slice(0, 8) : null,
  statusMessage: result.statusMessage ?? null,
  fallbackIncluded: result.statusMessage?.includes('Showing repository dead code signals instead.') ?? false,
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
    assert "Dead Code Detection" in payload["statusMessage"]


def test_module_has_dead_code_telemetry_detects_signals() -> None:
    script = (
        _scaffold_viewer_environment()
        + f"""
const originalLog = console.log;
const originalWarn = console.warn || (() => {{}});
console.log = () => {{}};
console.warn = () => {{}};

const viewer = await import('{VIEWER_PATH.as_uri()}');
const api = viewer.__test__;

const moduleWithSignals = api.createModuleRecord({{
  module_id: 'alpha.core',
  unreachable_functions: [{{ qualified_name: 'alpha.core::orphan', name: 'orphan' }}],
}});

const moduleWithoutSignals = api.createModuleRecord({{
  module_id: 'beta.utils',
}});

const withSignals = api.moduleHasDeadCodeTelemetryForTest(moduleWithSignals);
const withoutSignals = api.moduleHasDeadCodeTelemetryForTest(moduleWithoutSignals);

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  withSignals,
  withoutSignals,
}}));
"""
    )

    payload = _run_node_module(script)

    assert payload["withSignals"] is True
    assert payload["withoutSignals"] is False
