from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
BUILDER_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "entrypoint_trace_diagram.js"
VIEWER_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "viewer.js"

if not BUILDER_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected entrypoint trace builder at {BUILDER_PATH}")

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


def test_entrypoint_trace_diagram_renders_trace() -> None:
    script = f"""
import {{ buildEntrypointTraceDiagram }} from "{BUILDER_PATH.as_uri()}";

const modules = new Map([
  ["alpha.runner", {{ moduleId: "alpha.runner", functions: ["alpha.runner::main", "alpha.runner::setup", "alpha.runner::execute"] }}],
  ["beta.worker", {{ moduleId: "beta.worker", functions: ["beta.worker::boot"] }}],
]);

const functions = new Map([
  ["alpha.runner::main", {{ id: "alpha.runner::main", name: "main", moduleId: "alpha.runner", metrics: {{ coverage: 0.82, cyclomaticComplexity: 6 }}, calls: ["alpha.runner::setup", "beta.worker::boot"] }}],
  ["alpha.runner::setup", {{ id: "alpha.runner::setup", name: "setup", moduleId: "alpha.runner", metrics: {{ coverage: 0.7, cyclomaticComplexity: 3 }}, calls: ["alpha.runner::execute"] }}],
  ["alpha.runner::execute", {{ id: "alpha.runner::execute", name: "execute", moduleId: "alpha.runner", metrics: {{ coverage: 0.6, cyclomaticComplexity: 4 }}, calls: [] }}],
  ["beta.worker::boot", {{ id: "beta.worker::boot", name: "boot", moduleId: "beta.worker", metrics: {{ coverage: 0.9, cyclomaticComplexity: 2 }}, calls: [] }}],
]);

const callGraph = new Map([
  ["alpha.runner::main", ["alpha.runner::setup", "beta.worker::boot"]],
  ["alpha.runner::setup", ["alpha.runner::execute"]],
]);

const entrypoints = new Map([
  ["alpha.runner", {{
    moduleId: "alpha.runner",
    hasMainGuard: true,
    cliParser: false,
    candidates: [
      {{ id: "alpha.runner::main", name: "main", moduleId: "alpha.runner", reason: "main-guard-name-match", outboundCount: 2, inboundCount: 0 }},
    ],
  }}],
]);

const result = buildEntrypointTraceDiagram(modules, functions, callGraph, entrypoints, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  definition: result.definition,
  statusMessage: result.statusMessage,
  stats: result.stats,
  details: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    definition = payload["definition"]
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "classDef entrypoint" in definition
    assert "alpha_runner__main" in definition
    assert "beta_worker__boot" in definition

    status = payload["statusMessage"]
    assert status == "Rendered Entrypoint Trace for repository (1 entrypoint, 3 downstream functions)."

    stats = payload["stats"]
    assert stats["entrypoints"] == 1
    assert stats["downstreamFunctions"] == 3
    assert stats["edgeCount"] == 3
    assert stats["moduleCount"] == 1

    details = payload["details"]
    assert isinstance(details, list)
    assert details[0]["type"] == "list"
    first_item = details[0]["items"][0]
    assert first_item["label"].startswith("alpha.runner :: main")
    assert "Outbound: 2" in first_item["value"]


def test_entrypoint_trace_diagram_reports_missing_candidates() -> None:
    script = f"""
import {{ buildEntrypointTraceDiagram }} from "{BUILDER_PATH.as_uri()}";

const modules = new Map([
  ["alpha.runner", {{ moduleId: "alpha.runner", functions: ["alpha.runner::main"] }}],
]);

const functions = new Map([
  ["alpha.runner::main", {{ id: "alpha.runner::main", name: "main", moduleId: "alpha.runner", metrics: {{}} }}],
]);

const callGraph = new Map([
  ["alpha.runner::main", []],
]);

const entrypoints = new Map();

const result = buildEntrypointTraceDiagram(modules, functions, callGraph, entrypoints, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"] == "Entrypoint candidates were not detected in this CommandView artifact."


def test_entrypoint_trace_view_falls_back_to_repository_scope() -> None:
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
  ["alpha.runner", {{ moduleId: "alpha.runner", functions: ["alpha.runner::main", "alpha.runner::setup"] }}],
  ["beta.worker", {{ moduleId: "beta.worker", functions: ["beta.worker::boot"] }}],
]);

const functions = new Map([
  ["alpha.runner::main", {{ id: "alpha.runner::main", name: "main", moduleId: "alpha.runner", metrics: {{ coverage: 0.85 }}, calls: ["alpha.runner::setup"] }}],
  ["alpha.runner::setup", {{ id: "alpha.runner::setup", name: "setup", moduleId: "alpha.runner", metrics: {{ coverage: 0.7 }}, calls: [] }}],
  ["beta.worker::boot", {{ id: "beta.worker::boot", name: "boot", moduleId: "beta.worker", metrics: {{ coverage: 0.9 }}, calls: [] }}],
]);

const entrypoints = new Map([
  ["alpha.runner", {{
    moduleId: "alpha.runner",
    hasMainGuard: true,
    cliParser: false,
    candidates: [
      {{ id: "alpha.runner::main", name: "main", moduleId: "alpha.runner", reason: "main-guard-name-match", outboundCount: 1, inboundCount: 0 }},
    ],
  }}],
]);

const callGraph = new Map([
  ["alpha.runner::main", ["alpha.runner::setup"]],
  ["alpha.runner::setup", []],
]);

const normalized = {{
  modules,
  functions,
  callGraph: {{ functions: callGraph }},
  entrypoints,
}};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({{ moduleId: 'beta.worker' }});

const result = api.buildEntrypointTraceDiagramViewDefinitionForTest();

api.resetViewStateForTest();

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  hasDefinition: typeof result.definition === 'string',
  statusMessage: result.statusMessage,
  statusDetails: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    assert payload["hasDefinition"] is True
    assert "Showing repository candidates" in payload["statusMessage"]
    info_detail = payload["statusDetails"][0]
    assert info_detail["type"] == "info"
    assert "fallback" in info_detail["title"].lower()
