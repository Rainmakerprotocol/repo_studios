from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "complexity_heatmap_scope.js"

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected complexity heatmap scope module at {MODULE_PATH}")


@pytest.fixture(scope="module", autouse=True)
def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover
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


def test_scope_filters_to_selected_domain() -> None:
    script = f"""
import {{ resolveComplexityHeatmapScope }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["alpha::f1", {{ moduleId: "alpha.service.module1", metrics: {{ complexity: 12 }} }}],
  ["alpha::f2", {{ moduleId: "alpha.service.module2", metrics: {{ complexity: 8 }} }}],
  ["beta::g1", {{ moduleId: "beta.core.module", metrics: {{ complexity: 5 }} }}],
]);
const modules = new Map([
  ["alpha.service.module1", {{ moduleId: "alpha.service.module1", functions: ["alpha::f1"] }}],
  ["alpha.service.module2", {{ moduleId: "alpha.service.module2", functions: ["alpha::f2"] }}],
  ["beta.core.module", {{ moduleId: "beta.core.module", functions: ["beta::g1"] }}],
]);
const scope = resolveComplexityHeatmapScope(
  {{ functions, modules }},
  {{ currentLevel: "level1", selections: {{ domainId: "alpha.service" }} }}
);
console.log(JSON.stringify({{
  keys: scope.functions ? Array.from(scope.functions.keys()) : null,
  centerLabel: scope.centerLabel,
  statusContext: scope.statusContext,
}}));
"""
    payload = _run_node_module(script)

    assert payload["keys"] == ["alpha::f1", "alpha::f2"]
    assert "Domain: alpha.service" in payload["centerLabel"]
    assert payload["statusContext"] == "domain alpha.service"


def test_scope_reports_missing_domain_message() -> None:
    script = f"""
import {{ resolveComplexityHeatmapScope }} from "{MODULE_PATH.as_uri()}";
const functions = new Map([
  ["beta::g1", {{ moduleId: "beta.core.module", metrics: {{ complexity: 5 }} }}],
]);
const modules = new Map([
  ["beta.core.module", {{ moduleId: "beta.core.module", functions: ["beta::g1"] }}],
]);
const scope = resolveComplexityHeatmapScope(
  {{ functions, modules }},
  {{ currentLevel: "level1", selections: {{ domainId: "alpha.service" }} }}
);
console.log(JSON.stringify({{
  size: scope.functions ? scope.functions.size : null,
  emptyMessage: scope.emptyMessage ?? null,
}}));
"""
    payload = _run_node_module(script)

    assert payload["size"] == 0
    assert payload["emptyMessage"] == "Domain alpha.service has no modules recorded for this scope."
