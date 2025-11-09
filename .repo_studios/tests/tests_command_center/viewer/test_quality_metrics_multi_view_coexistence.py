from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
TYPE_COVERAGE_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "type_coverage_map.js"
)
DOCUMENTATION_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "documentation_coverage_map.js"
)

if not TYPE_COVERAGE_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected type coverage builder module at {TYPE_COVERAGE_MODULE_PATH}")

if not DOCUMENTATION_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected documentation coverage builder module at {DOCUMENTATION_MODULE_PATH}")


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


def test_quality_metrics_views_coexist_without_state_reset() -> None:
    script = f"""
import {{ buildTypeCoverageMapDiagram }} from "{TYPE_COVERAGE_MODULE_PATH.as_uri()}";
import {{ buildDocumentationCoverageMapDiagram }} from "{DOCUMENTATION_MODULE_PATH.as_uri()}";

const functions = new Map([
    ["alpha::f1", {{
        name: "f1",
        moduleId: "alpha",
        typeHintCoverage: 0.9,
        docstringQuality: {{ exists: true, status: "present" }},
    }}],
    ["alpha::f2", {{
        name: "f2",
        moduleId: "alpha",
        annotationCoverage: 0.6,
        docstringQuality: {{ exists: false, status: "missing" }},
    }}],
    ["beta::g1", {{
        name: "g1",
        moduleId: "beta",
        metrics: {{ coverage: 0.3 }},
        docstringQuality: {{ status: "stale" }},
    }}],
]);

const typeCoverageFirst = buildTypeCoverageMapDiagram(functions, {{ viewLabel: "Quality Metrics · Type Coverage Map" }});
const documentationResult = buildDocumentationCoverageMapDiagram(functions, {{ viewLabel: "Quality Metrics · Documentation Coverage Map" }});
const typeCoverageSecond = buildTypeCoverageMapDiagram(functions, {{ viewLabel: "Quality Metrics · Type Coverage Map" }});

console.log(JSON.stringify({{
    typeCoverageFirstDefinition: typeCoverageFirst.definition,
    typeCoverageSecondDefinition: typeCoverageSecond.definition,
    typeCoverageFirstStatus: typeCoverageFirst.statusMessage,
    typeCoverageSecondStatus: typeCoverageSecond.statusMessage,
    typeCoverageFirstStats: typeCoverageFirst.stats,
    typeCoverageSecondStats: typeCoverageSecond.stats,
    documentationDefinition: documentationResult.definition,
    documentationStatus: documentationResult.statusMessage,
    documentationStats: documentationResult.stats,
}}));
"""
    payload = _run_node_module(script)

    assert payload["typeCoverageFirstDefinition"] == payload["typeCoverageSecondDefinition"]
    assert payload["typeCoverageFirstStatus"] == payload["typeCoverageSecondStatus"]
    assert payload["typeCoverageFirstStats"] == payload["typeCoverageSecondStats"]
    assert payload["documentationDefinition"].startswith("graph TD")
    assert "Documentation Coverage Map" in payload["documentationDefinition"]
    assert "Rendered Documentation Coverage Map" in payload["documentationStatus"]
    assert payload["documentationStats"] == {"documented": 1, "missing": 1, "unknown": 1}