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
COMPLEXITY_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "complexity_heatmap.js"
)
LOGGING_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "logging_flow.js"
)

if not TYPE_COVERAGE_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected type coverage builder module at {TYPE_COVERAGE_MODULE_PATH}")

if not DOCUMENTATION_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected documentation coverage builder module at {DOCUMENTATION_MODULE_PATH}")

if not COMPLEXITY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected complexity heatmap builder module at {COMPLEXITY_MODULE_PATH}")

if not LOGGING_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected logging flow builder module at {LOGGING_MODULE_PATH}")


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
    import {{ buildComplexityHeatmapDiagram }} from "{COMPLEXITY_MODULE_PATH.as_uri()}";
    import {{ buildLoggingFlowDiagram }} from "{LOGGING_MODULE_PATH.as_uri()}";

const functions = new Map([
    ["alpha::f1", {{
        name: "f1",
        moduleId: "alpha",
        typeHintCoverage: 0.9,
        cyclomaticComplexity: 18,
        docstringQuality: {{ exists: true, status: "present" }},
            loggingCalls: [
                {{ level: "ERROR", lineno: 10 }},
                {{ level: "info", lineno: 12 }},
            ],
    }}],
    ["alpha::f2", {{
        name: "f2",
        moduleId: "alpha",
        annotationCoverage: 0.6,
        metrics: {{ complexity: 9 }},
        docstringQuality: {{ exists: false, status: "missing" }},
            loggingCalls: [
                {{ level: "warning", lineno: 8 }},
            ],
    }}],
    ["beta::g1", {{
        name: "g1",
        moduleId: "beta",
        metrics: {{ coverage: 0.3, complexity: 4, lineCount: 120 }},
        docstringQuality: {{ status: "stale" }},
            loggingCalls: [
                {{ message: "no level recorded" }},
            ],
    }}],
]);

const typeCoverageFirst = buildTypeCoverageMapDiagram(functions, {{ viewLabel: "Quality Metrics · Type Coverage Map" }});
const documentationResult = buildDocumentationCoverageMapDiagram(functions, {{ viewLabel: "Quality Metrics · Documentation Coverage Map" }});
const complexityResult = buildComplexityHeatmapDiagram(functions, {{ viewLabel: "Quality Metrics · Complexity Heatmap" }});
const typeCoverageSecond = buildTypeCoverageMapDiagram(functions, {{ viewLabel: "Quality Metrics · Type Coverage Map" }});
const complexitySecond = buildComplexityHeatmapDiagram(functions, {{ viewLabel: "Quality Metrics · Complexity Heatmap" }});
    const loggingFirst = buildLoggingFlowDiagram(functions, {{ viewLabel: "Quality Metrics · Logging Flow" }});
    const loggingSecond = buildLoggingFlowDiagram(functions, {{ viewLabel: "Quality Metrics · Logging Flow" }});

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
    complexityFirstDefinition: complexityResult.definition,
    complexitySecondDefinition: complexitySecond.definition,
    complexityFirstStatus: complexityResult.statusMessage,
    complexitySecondStatus: complexitySecond.statusMessage,
    complexityFirstStats: complexityResult.stats,
    complexitySecondStats: complexitySecond.stats,
        loggingFirstDefinition: loggingFirst.definition,
        loggingSecondDefinition: loggingSecond.definition,
        loggingFirstStatus: loggingFirst.statusMessage,
        loggingSecondStatus: loggingSecond.statusMessage,
        loggingFirstStats: loggingFirst.stats,
        loggingSecondStats: loggingSecond.stats,
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
    assert payload["complexityFirstDefinition"].startswith("graph TD")
    assert payload["complexitySecondDefinition"].startswith("graph TD")
    assert payload["complexityFirstDefinition"] == payload["complexitySecondDefinition"]
    assert payload["complexityFirstStatus"] == payload["complexitySecondStatus"]
    assert payload["complexityFirstStats"] == payload["complexitySecondStats"]
    assert payload["complexityFirstStats"]["extreme"] == 1
    assert payload["complexityFirstStats"]["high"] == 0
    assert payload["complexityFirstStats"]["moderate"] == 1
    assert payload["complexityFirstStats"]["low"] == 1
    assert payload["complexityFirstStats"]["unknown"] == 0
    assert payload["complexityFirstStats"]["maxComplexity"] == 18
    assert "Rendered Complexity Heatmap" in payload["complexityFirstStatus"]
    assert payload["loggingFirstDefinition"] == payload["loggingSecondDefinition"]
    assert payload["loggingFirstStatus"] == payload["loggingSecondStatus"]
    assert payload["loggingFirstStats"] == payload["loggingSecondStats"]
    assert payload["loggingFirstStats"] == {
        "emitters": 3,
        "silent": 0,
        "bucketCounts": {
            "critical": 0,
            "error": 1,
            "warning": 1,
            "info": 0,
            "debug": 0,
            "unknown": 1,
            "silent": 0,
        },
        "events": {
            "critical": 0,
            "error": 1,
            "warning": 1,
            "info": 1,
            "debug": 0,
            "unknown": 1,
        },
        "topModules": [
            {
                "moduleId": "alpha",
                "callCount": 3,
                "emitters": 2,
                "highestLevel": "error",
                "levelCounts": {
                    "critical": 0,
                    "error": 1,
                    "warning": 1,
                    "info": 1,
                    "debug": 0,
                    "unknown": 0,
                },
            },
            {
                "moduleId": "beta",
                "callCount": 1,
                "emitters": 1,
                "highestLevel": "unknown",
                "levelCounts": {
                    "critical": 0,
                    "error": 0,
                    "warning": 0,
                    "info": 0,
                    "debug": 0,
                    "unknown": 1,
                },
            },
        ],
    }
    assert "Rendered Logging Flow" in payload["loggingFirstStatus"]