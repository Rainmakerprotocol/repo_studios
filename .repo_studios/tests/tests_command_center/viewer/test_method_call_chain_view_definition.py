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


def test_method_call_chain_view_uses_scope_selection() -> None:
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

const viewer = await import('{VIEWER_PATH.as_uri()}');
const api = viewer.__test__;

api.resetViewStateForTest();

const modules = new Map([
  ["alpha.workflow", {{ moduleId: "alpha.workflow", functions: [
    "alpha.workflow::Workflow.start",
    "alpha.workflow::Workflow.validate",
    "alpha.workflow::Workflow.finalize"
  ] }}],
  ["beta.notifications", {{ moduleId: "beta.notifications", functions: [
    "beta.notifications::Notifier.send"
  ] }}],
]);

const functions = new Map([
  ["alpha.workflow::Workflow.start", {{
    id: "alpha.workflow::Workflow.start",
    name: "Workflow.start",
    moduleId: "alpha.workflow",
    calls: ["alpha.workflow::Workflow.validate", "beta.notifications::Notifier.send"],
  }}],
  ["alpha.workflow::Workflow.validate", {{
    id: "alpha.workflow::Workflow.validate",
    name: "Workflow.validate",
    moduleId: "alpha.workflow",
    calls: ["alpha.workflow::Workflow.finalize"],
  }}],
  ["alpha.workflow::Workflow.finalize", {{
    id: "alpha.workflow::Workflow.finalize",
    name: "Workflow.finalize",
    moduleId: "alpha.workflow",
    calls: [],
  }}],
  ["beta.notifications::Notifier.send", {{
    id: "beta.notifications::Notifier.send",
    name: "Notifier.send",
    moduleId: "beta.notifications",
    calls: [],
  }}],
]);

const callGraph = new Map([
  ["alpha.workflow::Workflow.start", ["alpha.workflow::Workflow.validate", "beta.notifications::Notifier.send"]],
  ["alpha.workflow::Workflow.validate", ["alpha.workflow::Workflow.finalize"]],
]);

const normalized = {{
  modules,
  functions,
  callGraph: {{ functions: callGraph }},
}};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({{ moduleId: 'alpha.workflow', functionId: 'alpha.workflow::Workflow.start' }});

const result = api.buildMethodCallChainViewDefinitionForTest();

api.resetViewStateForTest();

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  hasDefinition: typeof result.definition === 'string',
  statusMessage: result.statusMessage,
  stats: result.stats,
  details: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    assert payload["hasDefinition"] is True
    assert "Method Call Chain" in payload["statusMessage"]
    stats = payload["stats"]
    assert stats["methodCount"] == 4
    assert stats["classCount"] == 2
    details = payload["details"]
    assert isinstance(details, list)
    assert any(item.get("title") == "Call Chain" for item in details)


def test_method_call_chain_view_falls_back_to_repository_scope() -> None:
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

const viewer = await import('{VIEWER_PATH.as_uri()}');
const api = viewer.__test__;

api.resetViewStateForTest();

const modules = new Map([
  ["alpha.workflow", {{ moduleId: "alpha.workflow", functions: [
    "alpha.workflow::Workflow.start",
    "alpha.workflow::Workflow.validate"
  ] }}],
  ["gamma.utility", {{ moduleId: "gamma.utility", functions: ["gamma.utility::main"] }}],
]);

const functions = new Map([
  ["alpha.workflow::Workflow.start", {{
    id: "alpha.workflow::Workflow.start",
    name: "Workflow.start",
    moduleId: "alpha.workflow",
    calls: ["alpha.workflow::Workflow.validate"],
  }}],
  ["alpha.workflow::Workflow.validate", {{
    id: "alpha.workflow::Workflow.validate",
    name: "Workflow.validate",
    moduleId: "alpha.workflow",
    calls: [],
  }}],
  ["gamma.utility::main", {{
    id: "gamma.utility::main",
    name: "main",
    moduleId: "gamma.utility",
    calls: [],
  }}],
]);

const callGraph = new Map([
  ["alpha.workflow::Workflow.start", ["alpha.workflow::Workflow.validate"]],
]);

const normalized = {{
  modules,
  functions,
  callGraph: {{ functions: callGraph }},
}};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({{ moduleId: 'gamma.utility' }});

const result = api.buildMethodCallChainViewDefinitionForTest();

api.resetViewStateForTest();

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  message: result.message ?? null,
  statusMessage: result.statusMessage ?? null,
  details: result.statusDetails ?? [],
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"] is None
    assert payload["statusMessage"] and "Showing repository chains" in payload["statusMessage"]
    info_detail = payload["details"][0]
    assert info_detail["type"] == "info"
    assert "fallback" in info_detail["title"].lower()
