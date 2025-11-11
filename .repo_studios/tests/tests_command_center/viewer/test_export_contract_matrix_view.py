from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "export_contract_matrix.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected export contract matrix builder at {MODULE_PATH}")


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


def test_export_contract_matrix_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildExportContractMatrixDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.contracts.api", {{
    exportSummary: {{
      declared: ["expose_api", "ExportedClass", "CONFIG", "public_helper", "MISSING_UTIL"],
      missing: ["MISSING_UTIL"],
      dynamic: false,
      counts: {{ declared: 5, functions: 1, classes: 1, globals: 1, reexports: 1, missing: 1, local: 3 }},
      resolved: [
        {{ symbol: "expose_api", kind: "function", origin: "local", defined: true, moduleId: "alpha.contracts.api", functionId: "alpha.contracts.api::expose_api", signature: "def expose_api():", lineno: 18, docstringQuality: {{ exists: true }} }},
        {{ symbol: "ExportedClass", kind: "class", origin: "local", defined: true, moduleId: "alpha.contracts.api", classQualifiedName: "alpha.contracts.api.ExportedClass", lineno: 42 }},
        {{ symbol: "CONFIG", kind: "global", origin: "local", defined: true, valueKind: "dict", lineno: 7 }},
        {{ symbol: "public_helper", kind: "reexport", origin: "reexport", defined: true, sourceModule: "alpha.shared.helpers", sourceName: "helper", sourceQualifiedName: "alpha.shared.helpers.helper", lineno: 3 }},
        {{ symbol: "MISSING_UTIL", kind: "missing", origin: "missing", defined: false }},
      ],
      hasDeclared: true,
    }},
  }}],
  ["beta.contracts.dynamic", {{
    exportSummary: {{
      declared: [],
      missing: [],
      dynamic: true,
      counts: {{ declared: 0, functions: 0, classes: 0, globals: 0, reexports: 0, missing: 0, local: 0 }},
      resolved: [],
      hasDeclared: false,
    }},
  }}],
]);

const originalLog = console.log;
console.log = () => {{}};

const result = buildExportContractMatrixDiagram(modules, {{ rootId: "alpha" }});

console.log = originalLog;

console.log(JSON.stringify({{
  definition: result.definition,
  label: result.label,
  statusMessage: result.statusMessage,
  stats: result.stats,
  statusDetails: result.statusDetails,
}}));
"""
    payload = _run_node_module(script)

    definition = payload["definition"]
    assert isinstance(definition, str)
    assert definition.startswith("classDiagram")
    assert "class alpha_contracts_api {" in definition
    assert "expose_api" in definition
    assert "public_helper from alpha.shared.helpers" in definition
    assert "+__all__ : dynamic" in definition

    status = payload["statusMessage"]
    assert "Export Contract Matrix" in status
    assert "5 declared" in status or "5 declared symbol" in status

    stats = payload["stats"]
    assert stats == {
        "modules": 2,
        "declaredSymbols": 5,
        "localSymbols": 3,
        "functions": 1,
        "classes": 1,
        "globals": 1,
        "reexports": 1,
        "missingSymbols": 1,
        "dynamicModules": 1,
        "modulesWithMissing": [
            {
                "moduleId": "alpha.contracts.api",
                "count": 1,
                "symbols": ["MISSING_UTIL"],
            }
        ],
        "dynamicOnlyModules": ["beta.contracts.dynamic"],
        "topReexports": [
            {
                "moduleId": "alpha.contracts.api",
                "symbol": "public_helper",
                "sourceModule": "alpha.shared.helpers",
                "sourceName": "helper",
            }
        ],
    }

    details = payload["statusDetails"]
    assert isinstance(details, list) and details
    summary_section = details[0]
    assert summary_section["type"] == "stat-summary"
    missing_section = next((entry for entry in details if entry["title"] == "Modules With Missing Exports"), None)
    assert missing_section is not None
    dynamic_section = next((entry for entry in details if entry["title"] == "Dynamic-only Modules"), None)
    assert dynamic_section is not None


def test_export_contract_matrix_returns_message_when_empty() -> None:
    script = f"""
import {{ buildExportContractMatrixDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.contracts.empty", {{ exportSummary: null }}],
]);

const originalLog = console.log;
console.log = () => {{}};

const result = buildExportContractMatrixDiagram(modules);

console.log = originalLog;

console.log(JSON.stringify({{
  message: result.message,
}}));
"""
    payload = _run_node_module(script)

    assert payload["message"].startswith("Export contract metadata is not available")


def test_export_contract_matrix_definition_stable_across_calls() -> None:
    script = f"""
import {{ buildExportContractMatrixDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.contracts.api", {{
    exportSummary: {{
      declared: ["expose_api"],
      missing: [],
      dynamic: false,
      counts: {{ declared: 1, functions: 1, classes: 0, globals: 0, reexports: 0, missing: 0, local: 1 }},
      resolved: [
        {{ symbol: "expose_api", kind: "function", origin: "local", defined: true, moduleId: "alpha.contracts.api", functionId: "alpha.contracts.api::expose_api", lineno: 18 }},
      ],
      hasDeclared: true,
    }},
  }}],
]);

const originalLog = console.log;
console.log = () => {{}};

const first = buildExportContractMatrixDiagram(modules);
const second = buildExportContractMatrixDiagram(modules);

console.log = originalLog;

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


def test_export_contract_matrix_includes_fallback_notice() -> None:
    script = f"""
import {{ buildExportContractMatrixDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.contracts.api", {{
    exportSummary: {{
      declared: ["expose_api"],
      missing: [],
      dynamic: false,
      counts: {{ declared: 1, functions: 1, classes: 0, globals: 0, reexports: 0, missing: 0, local: 1 }},
      resolved: [
        {{ symbol: "expose_api", kind: "function", origin: "local", defined: true, moduleId: "alpha.contracts.api", functionId: "alpha.contracts.api::expose_api", lineno: 18 }},
      ],
      hasDeclared: true,
    }},
  }}],
]);

const originalLog = console.log;
console.log = () => {{}};

const result = buildExportContractMatrixDiagram(modules, {{ fallbackNotice: "No contracts for selected scope; rendering repository instead." }});

console.log = originalLog;

console.log(JSON.stringify({{
  statusMessage: result.statusMessage,
  statusDetails: result.statusDetails,
}}));
"""
    payload = _run_node_module(script)

    assert "Fallback" in payload["statusMessage"] or "rendering repository" in payload["statusMessage"]
    details = payload["statusDetails"]
    assert details[0]["type"] == "info"
    assert details[0]["title"].lower().startswith("scope fallback")
    assert "rendering repository" in details[0]["description"].lower()


def test_export_contract_matrix_view_falls_back_to_repository_scope() -> None:
    viewer_path = (
        REPO_STUDIOS_ROOT
        / "command_center"
        / "viewer"
        / "ui"
        / "viewer.js"
    )

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

const contractModule = api.createModuleRecord({{
  module_id: 'alpha.contracts.api',
  path: 'alpha/contracts/api.py',
  relative_path: 'alpha/contracts/api.py',
  functions: [
    {{ name: 'expose_api', qualified_name: 'alpha.contracts.api::expose_api', line: 18 }},
  ],
  exports: {{ symbols: ['expose_api'], missing: [], dynamic: false }},
}});

const emptyModule = api.createModuleRecord({{
  module_id: 'beta.contracts.empty',
  path: 'beta/contracts/empty.py',
  relative_path: 'beta/contracts/empty.py',
  exports: {{ symbols: [], missing: [], dynamic: false }},
}});

const modules = new Map();
if (contractModule) {{
  modules.set(contractModule.id, contractModule);
}}
if (emptyModule) {{
  modules.set(emptyModule.id, emptyModule);
}}

const normalized = {{
  modules,
  functions: new Map(),
  callGraph: {{ functions: new Map() }},
  metrics: {{}},
  hierarchy: {{}},
  levels: null,
  screeningHistory: null,
}};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({{ rootId: 'beta.contracts', domainId: null, moduleId: null }});

const result = api.buildExportContractMatrixViewDefinitionForTest();

api.resetViewStateForTest();

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  hasDefinition: typeof result.definition === 'string',
  statusDetails: result.statusDetails,
  statusMessage: result.statusMessage,
}}));
"""
    payload = _run_node_module(script)

    assert payload["hasDefinition"] is True
    fallback_detail = payload["statusDetails"][0]
    assert fallback_detail["type"] == "info"
    assert "fallback" in fallback_detail["title"].lower()
    assert "beta.contracts" in fallback_detail["description"]
    assert "repository" in fallback_detail["description"]
