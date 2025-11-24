from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "type_coverage_scope.js"

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected type coverage scope module at {MODULE_PATH}")


@pytest.fixture(scope="module", autouse=True)
def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Node.js runtime is required for viewer helper tests: {exc}")


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


def test_scope_filters_to_selected_root() -> None:
    script = f"""
import {{ resolveTypeCoverageScope }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["alpha::f1", {{ moduleId: "alpha.service.module1", typeHintCoverage: 0.9 }}],
  ["alpha::f2", {{ moduleId: "alpha.service.module2", typeHintCoverage: 0.6 }}],
  ["beta::g1", {{ moduleId: "beta.core.module", typeHintCoverage: 0.4 }}],
]);
const modules = new Map([
  ["alpha.service.module1", {{ moduleId: "alpha.service.module1", functions: ["alpha::f1"] }}],
  ["alpha.service.module2", {{ moduleId: "alpha.service.module2", functions: ["alpha::f2"] }}],
  ["beta.core.module", {{ moduleId: "beta.core.module", functions: ["beta::g1"] }}],
]);
const scope = resolveTypeCoverageScope(
  {{ functions, modules }},
  {{ currentLevel: "level0", selections: {{ rootId: "alpha" }} }}
);
console.log(JSON.stringify({{
  keys: scope.functions ? Array.from(scope.functions.keys()) : null,
  centerLabel: scope.centerLabel,
  statusContext: scope.statusContext,
}}));
"""
    payload = _run_node_module(script)

    assert payload["keys"] == ["alpha::f1", "alpha::f2"]
    assert "Root: alpha" in payload["centerLabel"]
    assert payload["statusContext"] == "root alpha"


def test_scope_filters_to_selected_module() -> None:
    script = f"""
import {{ resolveTypeCoverageScope }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["alpha::f1", {{ moduleId: "alpha.service.module1", typeHintCoverage: 0.9 }}],
  ["alpha::f2", {{ moduleId: "alpha.service.module1", typeHintCoverage: 0.4 }}],
  ["beta::g1", {{ moduleId: "beta.core.module", typeHintCoverage: 0.7 }}],
]);
const modules = new Map([
  ["alpha.service.module1", {{ moduleId: "alpha.service.module1", functions: ["alpha::f1", "alpha::f2"] }}],
  ["beta.core.module", {{ moduleId: "beta.core.module", functions: ["beta::g1"] }}],
]);
const scope = resolveTypeCoverageScope(
  {{ functions, modules }},
  {{ currentLevel: "level3", selections: {{ moduleId: "alpha.service.module1" }} }}
);
console.log(JSON.stringify({{
  keys: scope.functions ? Array.from(scope.functions.keys()) : null,
  centerLabel: scope.centerLabel,
  statusContext: scope.statusContext,
}}));
"""
    payload = _run_node_module(script)

    assert payload["keys"] == ["alpha::f1", "alpha::f2"]
    assert "Module: alpha.service.module1" in payload["centerLabel"]
    assert payload["statusContext"] == "module alpha.service.module1"


def test_scope_reports_empty_module_message() -> None:
    script = f"""
import {{ resolveTypeCoverageScope }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["beta::g1", {{ moduleId: "beta.core.module", typeHintCoverage: 0.7 }}],
]);
const modules = new Map([
  ["alpha.service.module1", {{ moduleId: "alpha.service.module1", functions: [] }}],
  ["beta.core.module", {{ moduleId: "beta.core.module", functions: ["beta::g1"] }}],
]);
const scope = resolveTypeCoverageScope(
  {{ functions, modules }},
  {{ currentLevel: "level2", selections: {{ moduleId: "alpha.service.module1" }} }}
);
console.log(JSON.stringify({{
  size: scope.functions ? scope.functions.size : null,
  emptyMessage: scope.emptyMessage ?? null,
}}));
"""
    payload = _run_node_module(script)

    assert payload["size"] == 0
    assert payload["emptyMessage"] == "Module alpha.service.module1 has no functions recorded for type coverage."
