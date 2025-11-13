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
    / "test_coverage_mapping.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected test coverage mapping builder at {MODULE_PATH}")


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


def test_test_coverage_mapping_requires_modules() -> None:
    script = f"""
import {{ buildTestCoverageMappingDiagram }} from \"{MODULE_PATH.as_uri()}\";
const result = buildTestCoverageMappingDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert payload["message"].startswith("No modules recorded")


def test_test_coverage_mapping_renders_definition_and_stats() -> None:
    script = f"""
import {{ buildTestCoverageMappingDiagram }} from \"{MODULE_PATH.as_uri()}\";

const modules = new Map([
  ["alpha.core", {{
    moduleId: "alpha.core",
    functions: [
      "alpha.core::covered",
      "alpha.core::partial",
      "alpha.core::unknown",
    ],
    coverageSignals: {{
      has_matches: true,
      imports: ["tests.test_alpha", "tests.integration.alpha_suite"],
    }},
  }}],
  ["beta.utils", {{
    moduleId: "beta.utils",
    functions: ["beta.utils::uncovered"],
    coverageSignals: {{ has_matches: false, imports: [] }},
  }}],
]);

const functions = new Map([
  ["alpha.core::covered", {{
    id: "alpha.core::covered",
    name: "covered",
    moduleId: "alpha.core",
    metrics: {{ coverage: 1.0, lineCount: 15 }},
  }}],
  ["alpha.core::partial", {{
    id: "alpha.core::partial",
    name: "partial",
    moduleId: "alpha.core",
    metrics: {{ coverage: 0.62, lineCount: 20 }},
  }}],
  ["alpha.core::unknown", {{
    id: "alpha.core::unknown",
    name: "unknown",
    moduleId: "alpha.core",
    metrics: {{ lineCount: 6 }},
  }}],
  ["beta.utils::uncovered", {{
    id: "beta.utils::uncovered",
    name: "uncovered",
    moduleId: "beta.utils",
    metrics: {{ coverage: 0.0, lineCount: 12 }},
  }}],
]);

const result = buildTestCoverageMappingDiagram(modules, functions, {{ scopeDescription: \"repository\" }});

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
    assert "module_alpha_core" in definition
    assert "tests.test_alpha" in definition

    status = payload["statusMessage"]
    assert "Rendered Test Coverage Mapping" in status
    assert "modules 2/2" in status

    stats = payload["stats"]
    assert stats["moduleCount"] == 2
    assert stats["displayedModules"] == 2
    assert stats["uncoveredFunctions"] == 1
    assert stats["partialFunctions"] == 1
    assert stats["tests"]["total"] == 2
    assert stats["modulesWithoutTests"] == 1
    assert stats["coverageAverage"] == pytest.approx((1 + 0.62 + 0) / 3, rel=1e-9)

    details = {detail["title"]: detail for detail in payload["statusDetails"]}
    assert set(details) == {"alpha.core", "beta.utils"}

    beta_detail = details["beta.utils"]
    assert beta_detail["uncovered"] == 1
    assert beta_detail["testCount"] == 0
    assert beta_detail["hasTestSignal"] is False

    alpha_detail = details["alpha.core"]
    assert alpha_detail["partial"] == 1
    assert alpha_detail["testCount"] == 2
    assert len(alpha_detail["displayedFunctions"]) == 2
    assert alpha_detail["hiddenFunctionCount"] == 0


def test_test_coverage_mapping_is_deterministic() -> None:
    script = f"""
import {{ buildTestCoverageMappingDiagram }} from \"{MODULE_PATH.as_uri()}\";

const modules = new Map([
  ["alpha.core", {{
    moduleId: "alpha.core",
    functions: [
      "alpha.core::covered",
      "alpha.core::partial",
    ],
    coverageSignals: {{ has_matches: true, imports: ["tests.test_alpha"] }},
  }}],
]);

const functions = new Map([
  ["alpha.core::covered", {{
    id: "alpha.core::covered",
    name: "covered",
    moduleId: "alpha.core",
    metrics: {{ coverage: 1.0, lineCount: 10 }},
  }}],
  ["alpha.core::partial", {{
    id: "alpha.core::partial",
    name: "partial",
    moduleId: "alpha.core",
    metrics: {{ coverage: 0.45, lineCount: 8 }},
  }}],
]);

const first = buildTestCoverageMappingDiagram(modules, functions, {{ scopeDescription: "repository" }});
const second = buildTestCoverageMappingDiagram(modules, functions, {{ scopeDescription: \"repository\" }});

console.log(JSON.stringify({{
  sameDefinition: first.definition === second.definition,
  sameStatus: first.statusMessage === second.statusMessage,
  sameStats: JSON.stringify(first.stats) === JSON.stringify(second.stats),
}}));
"""
    payload = _run_node_module(script)

    assert payload["sameDefinition"] is True
    assert payload["sameStatus"] is True
    assert payload["sameStats"] is True
