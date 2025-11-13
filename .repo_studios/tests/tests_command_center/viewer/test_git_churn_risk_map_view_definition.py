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


def test_git_churn_risk_map_requires_churn_data() -> None:
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
moduleRecord.functions = ['alpha.core::service'];

const modules = new Map([[moduleRecord.moduleId, moduleRecord]]);

api.setNormalizedDataForTest({{
  modules,
}});

const result = api.buildGitChurnRiskMapViewDefinitionForTest();

api.resetViewStateForTest();
console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  message: result.message ?? null,
}}));
"""
    )

    payload = _run_node_module(script)

    assert payload["message"] == "Git churn metrics are not available in this CommandView artifact."


def test_git_churn_risk_map_falls_back_to_repository_when_scope_empty() -> None:
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

const moduleChurn = api.createModuleRecord({{
  module_id: 'alpha.core',
  relative_path: 'alpha/core.py',
  git_churn: {{
    commit_count: 10,
    additions: 200,
    deletions: 80,
    net_changes: 120,
  }},
}});
moduleChurn.functions = ['alpha.core::service'];

const moduleScoped = api.createModuleRecord({{
  module_id: 'beta.utils',
  relative_path: 'beta/utils.py',
}});
moduleScoped.functions = ['beta.utils::helper'];

const modules = new Map([
  [moduleChurn.moduleId, moduleChurn],
  [moduleScoped.moduleId, moduleScoped],
]);

const functions = new Map();

api.setNormalizedDataForTest({{
  modules,
  functions,
  metrics: {{
    repository: {{
      git_churn: {{
        files_with_data: 2,
        total_commits: 12,
        total_additions: 280,
        total_deletions: 80,
        net_changes: 200,
      }},
    }},
  }},
}});
api.setLevelSelectionsForTest({{
  moduleId: 'beta.utils',
}});

const result = api.buildGitChurnRiskMapViewDefinitionForTest();

api.resetViewStateForTest();
console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  definitionPrefix: typeof result.definition === 'string' ? result.definition.slice(0, 8) : null,
  statusMessage: result.statusMessage ?? null,
  fallbackIncluded: result.statusMessage?.includes('Showing repository churn instead.') ?? false,
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
    assert "Rendered Git Churn Risk Map" in payload["statusMessage"]


def test_module_has_git_churn_telemetry_detects_metrics() -> None:
    script = (
        _scaffold_viewer_environment()
        + f"""
const originalLog = console.log;
const originalWarn = console.warn || (() => {{}});
console.log = () => {{}};
console.warn = () => {{}};

const viewer = await import('{VIEWER_PATH.as_uri()}');
const api = viewer.__test__;

const moduleWithChurn = api.createModuleRecord({{
  module_id: 'alpha.core',
  git_churn: {{
    commit_count: 5,
    additions: 40,
    deletions: 10,
    net_changes: 30,
  }},
}});

const moduleWithoutChurn = api.createModuleRecord({{
  module_id: 'beta.utils',
}});

const withChurn = api.moduleHasGitChurnTelemetryForTest(moduleWithChurn);
const withoutChurn = api.moduleHasGitChurnTelemetryForTest(moduleWithoutChurn);

api.resetViewStateForTest();
console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  withChurn,
  withoutChurn,
}}));
"""
    )

    payload = _run_node_module(script)

    assert payload["withChurn"] is True
    assert payload["withoutChurn"] is False
