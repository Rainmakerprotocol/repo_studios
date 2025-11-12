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
CYCLOMATIC_COMPLEXITY_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "cyclomatic_complexity_map.js"
)
LOGGING_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "logging_flow.js"
)
DECORATOR_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "decorator_usage_map.js"
)
PUBLIC_PRIVATE_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "public_vs_private_api.js"
)

if not TYPE_COVERAGE_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected type coverage builder module at {TYPE_COVERAGE_MODULE_PATH}")

if not DOCUMENTATION_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected documentation coverage builder module at {DOCUMENTATION_MODULE_PATH}")

if not COMPLEXITY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected complexity heatmap builder module at {COMPLEXITY_MODULE_PATH}")

if not CYCLOMATIC_COMPLEXITY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(
        f"Expected cyclomatic complexity map builder module at {CYCLOMATIC_COMPLEXITY_MODULE_PATH}"
    )

if not LOGGING_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected logging flow builder module at {LOGGING_MODULE_PATH}")

if not DECORATOR_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected decorator usage builder module at {DECORATOR_MODULE_PATH}")

if not PUBLIC_PRIVATE_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected public vs private API builder module at {PUBLIC_PRIVATE_MODULE_PATH}")


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
    import {{ buildCyclomaticComplexityMapDiagram }} from "{CYCLOMATIC_COMPLEXITY_MODULE_PATH.as_uri()}";
    import {{ buildLoggingFlowDiagram }} from "{LOGGING_MODULE_PATH.as_uri()}";
    import {{ buildDecoratorUsageMapDiagram }} from "{DECORATOR_MODULE_PATH.as_uri()}";
    import {{ buildPublicVsPrivateApiDiagram }} from "{PUBLIC_PRIVATE_MODULE_PATH.as_uri()}";

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
        decorators: ["auth", "cache"],
        decoratorsDetailed: [
            {{ name: "auth", module: "alpha.decorators", args: [], kwargs: {{}} }},
            {{ name: "cache", args: ["300"], kwargs: {{ key: "'user_id'" }} }},
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
        decorators: [],
    }}],
    ["beta::g1", {{
        name: "g1",
        moduleId: "beta",
        metrics: {{ coverage: 0.3, complexity: 4, lineCount: 120 }},
        docstringQuality: {{ status: "stale" }},
            loggingCalls: [
                {{ message: "no level recorded" }},
            ],
        decorators: ["cache"],
        decoratorsDetailed: [
            {{ name: "cache", module: "shared.decorators", args: [], kwargs: {{}} }},
        ],
    }}],
]);

const modules = new Map([
    ["alpha.api", {{
        moduleId: "alpha.api",
        apiSurface: {{
            hasDeclaredExports: true,
            strategy: "explicit",
            exportedSymbols: ["public_func", "CONFIG"],
            reexports: [],
            missingExports: [],
            functions: {{
                public: [
                    {{
                        id: "alpha.api::public_func",
                        name: "public_func",
                        category: "exported",
                        coverage: 0.82,
                        typeHintCoverage: 0.61,
                        lineno: 10,
                    }},
                ],
                internal: [
                    {{
                        id: "alpha.api::_helper",
                        name: "_helper",
                        category: "private",
                        coverage: 0.4,
                        typeHintCoverage: 0.1,
                        lineno: 22,
                    }},
                ],
            }},
            classes: {{ public: [], internal: [] }},
            globals: {{
                public: [
                    {{
                        id: "alpha.api::CONFIG",
                        name: "CONFIG",
                        category: "exported",
                        valueKind: "dict",
                        lineno: 3,
                    }},
                ],
                internal: [],
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
            missingExports: [],
            functions: {{
                public: [
                    {{
                        id: "beta.utils::util_main",
                        name: "util_main",
                        category: "implicit",
                        coverage: 0.55,
                        lineno: 8,
                    }},
                ],
                internal: [
                    {{
                        id: "beta.utils::_local",
                        name: "_local",
                        category: "private",
                        coverage: 0.2,
                        lineno: 12,
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
                        category: "internal",
                        valueKind: "dict",
                        lineno: 2,
                    }},
                ],
            }},
        }},
    }}],
]);

const typeCoverageFirst = buildTypeCoverageMapDiagram(functions, {{ viewLabel: "Quality Metrics · Type Coverage Map" }});
const documentationResult = buildDocumentationCoverageMapDiagram(functions, {{ viewLabel: "Quality Metrics · Documentation Coverage Map" }});
const complexityResult = buildComplexityHeatmapDiagram(functions, {{ viewLabel: "Quality Metrics · Complexity Heatmap" }});
const typeCoverageSecond = buildTypeCoverageMapDiagram(functions, {{ viewLabel: "Quality Metrics · Type Coverage Map" }});
const complexitySecond = buildComplexityHeatmapDiagram(functions, {{ viewLabel: "Quality Metrics · Complexity Heatmap" }});
const cyclomaticFirst = buildCyclomaticComplexityMapDiagram(functions, {{
        viewLabel: "Quality Metrics · Cyclomatic Complexity Map",
        scopeDescription: "repository",
        moduleLimit: 5,
        functionLimit: 5,
    }});
const cyclomaticSecond = buildCyclomaticComplexityMapDiagram(functions, {{
        viewLabel: "Quality Metrics · Cyclomatic Complexity Map",
        scopeDescription: "repository",
        moduleLimit: 5,
        functionLimit: 5,
    }});
    const loggingFirst = buildLoggingFlowDiagram(functions, {{ viewLabel: "Quality Metrics · Logging Flow" }});
    const loggingSecond = buildLoggingFlowDiagram(functions, {{ viewLabel: "Quality Metrics · Logging Flow" }});
    const decoratorFirst = buildDecoratorUsageMapDiagram(functions, {{
        viewLabel: "Quality Metrics · Decorator Usage Map",
        requiredDecorators: ["auth", "audit"],
    }});
    const decoratorSecond = buildDecoratorUsageMapDiagram(functions, {{
        viewLabel: "Quality Metrics · Decorator Usage Map",
        requiredDecorators: ["auth", "audit"],
    }});
    const publicPrivateFirst = buildPublicVsPrivateApiDiagram(modules, {{
        viewLabel: "Quality Metrics · Public vs Private API",
        scopeDescription: "repository",
    }});
    const publicPrivateSecond = buildPublicVsPrivateApiDiagram(modules, {{
        viewLabel: "Quality Metrics · Public vs Private API",
        scopeDescription: "repository",
    }});

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
        cyclomaticFirstDefinition: cyclomaticFirst.definition,
        cyclomaticSecondDefinition: cyclomaticSecond.definition,
        cyclomaticFirstStatus: cyclomaticFirst.statusMessage,
        cyclomaticSecondStatus: cyclomaticSecond.statusMessage,
        cyclomaticFirstStats: cyclomaticFirst.stats,
        cyclomaticSecondStats: cyclomaticSecond.stats,
        cyclomaticFirstDetails: cyclomaticFirst.statusDetails,
        cyclomaticSecondDetails: cyclomaticSecond.statusDetails,
        loggingFirstDefinition: loggingFirst.definition,
        loggingSecondDefinition: loggingSecond.definition,
        loggingFirstStatus: loggingFirst.statusMessage,
        loggingSecondStatus: loggingSecond.statusMessage,
        loggingFirstStats: loggingFirst.stats,
        loggingSecondStats: loggingSecond.stats,
    decoratorFirstDefinition: decoratorFirst.definition,
    decoratorSecondDefinition: decoratorSecond.definition,
    decoratorFirstStatus: decoratorFirst.statusMessage,
    decoratorSecondStatus: decoratorSecond.statusMessage,
    decoratorFirstStats: decoratorFirst.stats,
    decoratorSecondStats: decoratorSecond.stats,
    publicPrivateFirstDefinition: publicPrivateFirst.definition,
    publicPrivateSecondDefinition: publicPrivateSecond.definition,
    publicPrivateFirstStatus: publicPrivateFirst.statusMessage,
    publicPrivateSecondStatus: publicPrivateSecond.statusMessage,
    publicPrivateFirstStats: publicPrivateFirst.stats,
    publicPrivateSecondStats: publicPrivateSecond.stats,
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
    assert payload["cyclomaticFirstDefinition"].startswith("graph TD")
    assert payload["cyclomaticFirstDefinition"] == payload["cyclomaticSecondDefinition"]
    assert payload["cyclomaticFirstStatus"] == payload["cyclomaticSecondStatus"]
    assert "Rendered Cyclomatic Complexity Map" in payload["cyclomaticFirstStatus"]
    cyclomatic_stats = payload["cyclomaticFirstStats"]
    assert cyclomatic_stats == payload["cyclomaticSecondStats"]
    assert cyclomatic_stats["totalModules"] == 2
    assert cyclomatic_stats["displayedModules"] == 2
    assert cyclomatic_stats["hiddenModules"] == 0
    assert cyclomatic_stats["extreme"] == 1
    assert cyclomatic_stats["high"] == 0
    assert cyclomatic_stats["moderate"] == 1
    assert cyclomatic_stats["low"] == 1
    assert cyclomatic_stats["unknown"] == 0
    assert cyclomatic_stats["maxComplexity"] == 18
    assert cyclomatic_stats["averageComplexity"] == pytest.approx(8.75, rel=1e-9)
    assert cyclomatic_stats["coverageAverage"] == pytest.approx(0.15, rel=1e-9)
    assert cyclomatic_stats["coverageBelowThreshold"] == 3
    assert cyclomatic_stats["coverageThreshold"] == 0.6
    assert isinstance(cyclomatic_stats["topModules"], list)
    assert len(cyclomatic_stats["topModules"]) == 2
    assert cyclomatic_stats["topModules"][0]["moduleId"] == "alpha"
    assert cyclomatic_stats["topModules"][0]["extreme"] == 1
    assert cyclomatic_stats["topModules"][1]["moduleId"] == "beta"

    cyclomatic_details = payload["cyclomaticFirstDetails"]
    assert cyclomatic_details == payload["cyclomaticSecondDetails"]
    assert cyclomatic_details
    assert cyclomatic_details[0]["title"] == "alpha"
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
    assert payload["decoratorFirstDefinition"] == payload["decoratorSecondDefinition"]
    assert payload["decoratorFirstStatus"] == payload["decoratorSecondStatus"]
    assert payload["decoratorFirstStats"] == payload["decoratorSecondStats"]
    assert payload["decoratorFirstStats"] == {
        "decorated": 2,
        "undecorated": 1,
        "uniqueDecorators": 2,
        "topDecorators": [
            {"name": "cache", "count": 2},
            {"name": "auth", "count": 1},
        ],
        "requiredDecorators": ["auth", "audit"],
        "missingRequiredDecorators": ["audit"],
        "missingRequiredDetails": [
            {
                "decorator": "audit",
                "scope": "global",
                "target": None,
                "samples": [
                    {"id": "alpha::f1", "name": "f1", "moduleId": "alpha"},
                    {"id": "alpha::f2", "name": "f2", "moduleId": "alpha"},
                    {"id": "beta::g1", "name": "g1", "moduleId": "beta"},
                ],
            }
        ],
    }
    assert "Rendered Decorator Usage Map" in payload["decoratorFirstStatus"]
    assert "missing required audit" in payload["decoratorFirstStatus"]
    assert payload["publicPrivateFirstDefinition"].startswith("graph LR")
    assert payload["publicPrivateFirstDefinition"] == payload["publicPrivateSecondDefinition"]
    assert payload["publicPrivateFirstStatus"] == payload["publicPrivateSecondStatus"]
    assert payload["publicPrivateFirstStats"] == payload["publicPrivateSecondStats"]
    assert payload["publicPrivateFirstStats"] == {
        "totalModules": 2,
        "visibleModules": 2,
        "hiddenModules": 0,
        "exported": 2,
        "implicit": 1,
    "internal": 1,
        "private": 2,
        "reexports": 0,
        "missing": 0,
        "modulesWithImplicit": [
            {
                "moduleId": "beta.utils",
                "count": 1,
                "samples": ["util_main"],
            },
        ],
        "modulesWithoutDeclaredExports": ["beta.utils"],
        "modulesWithMissingExports": [],
    }
    assert "Rendered Public vs Private API Map" in payload["publicPrivateFirstStatus"]