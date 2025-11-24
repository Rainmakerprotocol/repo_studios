from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "external_vs_internal_dependency_map.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected external vs internal dependency map builder at {MODULE_PATH}")


def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Node.js runtime is required for viewer builder tests: {exc}")


@pytest.fixture(scope="module", autouse=True)
def _node_runtime_guard() -> None:
    _ensure_node_runtime()


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


def test_external_dependency_map_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildExternalVsInternalDependencyMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "beta.utils", category: "internal", unused: false, functions: ["alpha.core::bootstrap"], via: ["utils"] }},
      {{ target: "beta.utils.helpers", category: "internal", unused: true, functions: [] }},
      {{ target: "requests", category: "third_party", unused: false, functions: ["alpha.core::bootstrap"], via: ["requests"] }},
      {{ target: "requests.sessions", category: "third_party", unused: true, functions: [] }},
      {{ target: "json", category: "standard_library", unused: false, functions: [] }},
      {{ target: "local_unknown", category: "unknown", unused: false, functions: [] }},
    ],
    dependencySummary: {{
      internal: {{ count: 1, modules: ["beta.utils"] }},
      third_party: {{ count: 1, modules: ["requests"] }},
      standard_library: {{ count: 1, modules: ["json"] }},
      unknown: {{ count: 1, modules: ["local_unknown"] }},
    }},
  }}],
  ["beta.utils", {{
    importEdges: [
      {{ target: "alpha.core", category: "internal", unused: false, functions: ["beta.utils::help"] }},
      {{ target: "datetime", category: "standard_library", unused: false, functions: ["beta.utils::help"] }},
    ],
    dependencySummary: {{
      internal: {{ count: 1, modules: ["alpha.core"] }},
      standard_library: {{ count: 1, modules: ["datetime"] }},
    }},
  }}],
]);

const result = buildExternalVsInternalDependencyMapDiagram(modules, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  definition: result.definition,
  statusMessage: result.statusMessage,
  stats: result.stats,
  statusDetails: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    definition = payload["definition"]
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "alpha_core" in definition
    assert "class alpha_core moduleExternalDominant" in definition
    assert "external_third_party_requests" in definition
    assert "-.->|Third Party 2" in definition

    status = payload["statusMessage"]
    assert "External vs Internal Dependency Map" in status
    assert "2 modules" in status

    stats = payload["stats"]
    assert stats["modules"] == 2
    assert stats["internalTargets"] == 2
    assert stats["externalPackages"] == 4
    assert stats["unusedExternalImports"] == 1
    assert stats["aliasUsage"] == 1

    assert stats["modulesDominatedByExternal"] == [
        {
            "moduleId": "alpha.core",
            "internalCount": 1,
            "externalCount": 3,
            "unusedExternalImports": 1,
        }
    ]

    top_packages = stats["topExternalPackages"]
    assert top_packages[0]["packageName"] == "requests"
    assert top_packages[0]["statements"] == 2
    assert {pkg["packageName"] for pkg in top_packages} == {"requests", "datetime", "json", "local_unknown"}

    category_breakdown = {entry["category"]: entry for entry in stats["categoryBreakdown"]}
    assert category_breakdown["third_party"] == {
        "category": "third_party",
        "packages": 1,
        "statements": 2,
        "modules": 1,
        "unused": 1,
    }
    assert category_breakdown["standard_library"] == {
        "category": "standard_library",
        "packages": 2,
        "statements": 2,
        "modules": 2,
        "unused": 0,
    }
    assert category_breakdown["unknown"] == {
        "category": "unknown",
        "packages": 1,
        "statements": 1,
        "modules": 1,
        "unused": 0,
    }

    details = payload["statusDetails"]
    assert isinstance(details, list) and details
    assert details[0]["type"] == "stat-summary"
    dominated_section = next(
        (entry for entry in details if entry["title"] == "Modules Dominated by External Imports"), None
    )
    assert dominated_section is not None
    top_packages_section = next((entry for entry in details if entry["title"] == "Top External Packages"), None)
    assert top_packages_section is not None


def test_external_dependency_map_returns_message_when_no_modules() -> None:
    script = f"""
import {{ buildExternalVsInternalDependencyMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map();

const result = buildExternalVsInternalDependencyMapDiagram(modules);

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"].startswith("No modules recorded")


def test_external_dependency_map_definition_is_stable_across_calls() -> None:
    script = f"""
import {{ buildExternalVsInternalDependencyMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    importEdges: [
      {{ target: "beta.utils", category: "internal", unused: false }},
      {{ target: "requests", category: "third_party", unused: false }},
    ],
  }}],
  ["beta.utils", {{
    importEdges: [
      {{ target: "alpha.core", category: "internal", unused: false }},
    ],
  }}],
]);

const first = buildExternalVsInternalDependencyMapDiagram(modules);
const second = buildExternalVsInternalDependencyMapDiagram(modules);

console.log(JSON.stringify({{
  definitionEqual: first.definition === second.definition,
  statusEqual: first.statusMessage === second.statusMessage,
  statsEqual: JSON.stringify(first.stats) === JSON.stringify(second.stats),
}}));
"""

    payload = _run_node_module(script)

    assert payload["definitionEqual"] is True
    assert payload["statusEqual"] is True
    assert payload["statsEqual"] is True


def test_external_dependency_map_view_falls_back_to_repository_scope() -> None:
    viewer_path = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "viewer.js"

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

const viewer = await import('{viewer_path.as_uri()}');
const api = viewer.__test__;

api.resetViewStateForTest();

const moduleRecord = api.createModuleRecord({{
  module_id: 'alpha.core',
  relative_path: 'alpha/core.py',
  path: 'alpha/core.py',
  import_graph: [
    {{
      kind: 'import',
      module: 'requests',
      edges: [
        {{ target: 'requests', imported_as: 'requests', unused: false, functions: ['alpha.core::bootstrap'], category: 'third_party' }},
      ],
    }},
  ],
  dependency_summary: {{ third_party: {{ count: 1, modules: ['requests'] }} }},
}});

const modules = new Map();
if (moduleRecord) {{
  modules.set(moduleRecord.id, moduleRecord);
}}

const normalized = {{
  modules,
  functions: new Map(),
  callGraph: {{ functions: new Map() }},
  metrics: {{ }},
  levels: null,
}};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({{ rootId: 'beta.domain', domainId: null, moduleId: null }});

const result = api.buildExternalVsInternalDependencyMapViewDefinitionForTest();

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
    assert "Showing repository map" in payload["statusMessage"]
    info_detail = payload["statusDetails"][0]
    assert info_detail["type"] == "info"
    assert "fallback" in info_detail["title"].lower()
    assert "repository" in info_detail["description"].lower()
