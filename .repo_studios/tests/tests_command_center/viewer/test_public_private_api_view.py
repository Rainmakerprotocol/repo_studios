from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "public_vs_private_api.js"

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected public vs private API builder module at {MODULE_PATH}")


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


def test_public_private_api_requires_modules() -> None:
    script = f"""
import {{ buildPublicVsPrivateApiDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildPublicVsPrivateApiDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert payload["message"] == "No modules recorded in this CommandView artifact."


def test_public_private_api_renders_mermaid_definition() -> None:
    script = f"""
import {{ buildPublicVsPrivateApiDiagram }} from "{MODULE_PATH.as_uri()}";
const modules = new Map([
  ["alpha.api", {{
    moduleId: "alpha.api",
    apiSurface: {{
      hasDeclaredExports: true,
      strategy: "explicit",
      exportedSymbols: ["PublicClass", "exported_func", "CONFIG"],
      reexports: [
        {{ symbol: "external_api", sourceModule: "external.lib", sourceName: "external_api", lineno: 4 }},
      ],
      missingExports: [],
      functions: {{
        public: [
          {{
            id: "alpha.api::exported_func",
            name: "exported_func",
            category: "exported",
            coverage: 0.86,
            typeHintCoverage: 0.74,
            lineno: 12,
          }},
        ],
        internal: [
          {{
            id: "alpha.api::_helper",
            name: "_helper",
            category: "private",
            coverage: 0.48,
            lineno: 30,
          }},
          {{
            id: "alpha.api::internal_tool",
            name: "internal_tool",
            category: "internal",
            coverage: 0.63,
            typeHintCoverage: 0.25,
            lineno: 34,
          }},
        ],
      }},
      classes: {{
        public: [
          {{
            id: "alpha.api::PublicClass",
            name: "PublicClass",
            category: "exported",
            methodCount: 5,
            coverage: 0.91,
            typeHintCoverage: 0.8,
            lineno: 50,
          }},
        ],
        internal: [
          {{
            id: "alpha.api::_Utility",
            name: "_Utility",
            category: "internal",
            methodCount: 2,
            coverage: 0.22,
            lineno: 70,
          }},
        ],
      }},
      globals: {{
        public: [
          {{
            id: "alpha.api::CONFIG",
            name: "CONFIG",
            category: "exported",
            valueKind: "dict",
            lineno: 5,
          }},
        ],
        internal: [
          {{
            id: "alpha.api::_SECRET",
            name: "_SECRET",
            category: "private",
            valueKind: "str",
            lineno: 6,
          }},
        ],
      }},
    }},
  }}],
  ["beta.utils", {{
    moduleId: "beta.utils",
    apiSurface: {{
      hasDeclaredExports: false,
      strategy: "implicit",
      exportedSymbols: [],
      reexports: [],
      missingExports: [
        {{ symbol: "MISSING_ALIAS", kind: "missing" }},
      ],
      functions: {{
        public: [
          {{
            id: "beta.utils::utility",
            name: "utility",
            category: "implicit",
            coverage: 0.52,
            typeHintCoverage: 0.1,
            lineno: 14,
          }},
        ],
        internal: [
          {{
            id: "beta.utils::_cache_seed",
            name: "_cache_seed",
            category: "internal",
            coverage: 0.4,
            lineno: 20,
          }},
        ],
      }},
      classes: {{ public: [], internal: [] }},
      globals: {{
        public: [],
        internal: [
          {{
            id: "beta.utils::_CACHE",
            name: "_CACHE",
            category: "private",
            valueKind: "dict",
            lineno: 3,
          }},
        ],
      }},
    }},
  }}],
]);
const result = buildPublicVsPrivateApiDiagram(modules, {{
  viewLabel: "Quality Metrics · Public vs Private API",
  scopeDescription: "repository",
  moduleLimit: 10,
  symbolLimit: 4,
  reexportLimit: 2,
  missingLimit: 2,
}});
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    definition = payload.get("definition")
    assert isinstance(definition, str)
    assert definition.startswith("graph LR")
    assert "Public Surface" in definition
    assert "Internal Surface" in definition
    assert "alpha.api" in definition
    assert "beta.utils" in definition
    assert "external.lib" in definition
    assert "MISSING_ALIAS" in definition

    status_message = payload.get("statusMessage")
    assert isinstance(status_message, str)
    assert status_message.startswith("Rendered Public vs Private API Map for repository")
    assert "3 exported" in status_message
    assert "1 implicit" in status_message
    assert "3 internal" in status_message
    assert "3 private" in status_message

    stats = payload.get("stats")
    assert stats == {
        "totalModules": 2,
        "visibleModules": 2,
        "hiddenModules": 0,
        "exported": 3,
        "implicit": 1,
        "internal": 3,
        "private": 3,
        "reexports": 1,
        "missing": 1,
        "modulesWithImplicit": [
            {
                "moduleId": "beta.utils",
                "count": 1,
                "samples": ["utility"],
            }
        ],
        "modulesWithoutDeclaredExports": ["beta.utils"],
        "modulesWithMissingExports": [
            {
                "moduleId": "beta.utils",
                "count": 1,
                "symbols": ["MISSING_ALIAS"],
            }
        ],
    }

    status_details = payload.get("statusDetails")
    assert isinstance(status_details, list)
    assert status_details
    assert status_details[0]["type"] == "stat-summary"
    assert any(detail.get("type") == "pill-list" for detail in status_details)
    assert any(
        detail.get("type") == "list" and "Declared But Missing" in detail.get("title", "") for detail in status_details
    )
