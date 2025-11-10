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

const result = buildExportContractMatrixDiagram(modules, {{ rootId: "alpha" }});

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
    assert definition.startswith("graph TD")
    assert "subgraph alpha_contracts_api_exports_group" in definition
    assert "expose_api" in definition
    assert "re-export" in definition
    assert "Dynamic __all__" in definition

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

const result = buildExportContractMatrixDiagram(modules);

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

const first = buildExportContractMatrixDiagram(modules);
const second = buildExportContractMatrixDiagram(modules);

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
