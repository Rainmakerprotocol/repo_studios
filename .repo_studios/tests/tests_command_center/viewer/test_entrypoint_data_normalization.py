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
    output = result.stdout.strip()
    return json.loads(output)


def test_entrypoint_candidates_populated_for_main_guard_and_cli_modules() -> None:
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

const modules = new Map();
const functions = new Map();
const functionCallGraph = new Map();

const moduleRunner = __test__.createModuleRecord({{
  module_id: 'alpha.runner',
  relative_path: 'alpha/runner.py',
  entrypoints: {{ has_main_guard: true, cli_parser: false }},
}});
const functionMain = __test__.createFunctionRecord({{
  name: 'main',
  qualified_name: 'alpha.runner::main',
  calls: [{{ qualified_name: 'alpha.runner::execute_pipeline' }}],
  line: 10,
}}, moduleRunner.id);
const functionExecute = __test__.createFunctionRecord({{
  name: 'execute_pipeline',
  qualified_name: 'alpha.runner::execute_pipeline',
  calls: [],
  line: 20,
}}, moduleRunner.id);
moduleRunner.functions = [functionMain.id, functionExecute.id];
modules.set(moduleRunner.id, moduleRunner);
functions.set(functionMain.id, functionMain);
functions.set(functionExecute.id, functionExecute);
functionCallGraph.set(functionMain.id, functionMain.calls);
functionCallGraph.set(functionExecute.id, functionExecute.calls);

const moduleCli = __test__.createModuleRecord({{
  module_id: 'beta.cli',
  relative_path: 'beta/cli.py',
  entrypoints: {{ has_main_guard: false, cli_parser: true }},
}});
const functionCliMain = __test__.createFunctionRecord({{
  name: 'cli_main',
  qualified_name: 'beta.cli::cli_main',
  calls: [],
  line: 5,
}}, moduleCli.id);
const functionHelper = __test__.createFunctionRecord({{
  name: 'helper',
  qualified_name: 'beta.cli::helper',
  calls: [],
  line: 12,
}}, moduleCli.id);
moduleCli.functions = [functionCliMain.id, functionHelper.id];
modules.set(moduleCli.id, moduleCli);
functions.set(functionCliMain.id, functionCliMain);
functions.set(functionHelper.id, functionHelper);
functionCallGraph.set(functionCliMain.id, functionCliMain.calls);
functionCallGraph.set(functionHelper.id, functionHelper.calls);

const entrypointIndex = __test__.populateEntrypointCandidatesForTest(modules, functions, {{ functions: functionCallGraph }});

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  moduleEntrypoints: Array.from(modules.values()).map((record) => ({{
    moduleId: record.moduleId,
    hasMainGuard: Boolean(record.entrypoints?.hasMainGuard),
    cliParser: Boolean(record.entrypoints?.cliParser),
    candidates: Array.isArray(record.entrypoints?.candidates) ? record.entrypoints.candidates : [],
  }})),
  indexEntries: Array.from(entrypointIndex.entries()).map(([moduleId, payload]) => ({{
    moduleId,
    candidateIds: payload.candidates.map((candidate) => candidate.id),
    reasons: payload.candidates.map((candidate) => candidate.reason),
  }})),
}}));
"""

    payload = _run_node_module(script)

    modules_payload = {entry["moduleId"]: entry for entry in payload["moduleEntrypoints"]}

    runner = modules_payload["alpha.runner"]
    assert runner["hasMainGuard"] is True
    assert runner["cliParser"] is False
    runner_candidates = runner["candidates"]
    assert any(candidate["name"] == "main" for candidate in runner_candidates)
    assert all(candidate["name"] != "execute_pipeline" for candidate in runner_candidates)
    assert any(candidate["reason"] == "main-guard-name-match" for candidate in runner_candidates)

    cli_module = modules_payload["beta.cli"]
    assert cli_module["hasMainGuard"] is False
    assert cli_module["cliParser"] is True
    cli_candidates = cli_module["candidates"]
    assert any(candidate["name"] == "cli_main" for candidate in cli_candidates)
    assert all(candidate["name"] != "helper" for candidate in cli_candidates)
    assert any(candidate["reason"] == "cli-parser-name-match" for candidate in cli_candidates)

    index_entries = {entry["moduleId"]: entry for entry in payload["indexEntries"]}
    assert index_entries["alpha.runner"]["candidateIds"] == ["alpha.runner::main"]
    assert index_entries["beta.cli"]["candidateIds"] == ["beta.cli::cli_main"]
