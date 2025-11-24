from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "cyclomatic_complexity_map.js"

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected cyclomatic complexity map builder module at {MODULE_PATH}")


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


def test_cyclomatic_complexity_map_requires_functions() -> None:
    script = textwrap.dedent(
        f"""
                import {{ buildCyclomaticComplexityMapDiagram }} from \"{MODULE_PATH.as_uri()}\";
                const result = buildCyclomaticComplexityMapDiagram();
                console.log(JSON.stringify(result));
                """
    )
    payload = _run_node_module(script)

    assert payload["message"] == "No complexity metrics recorded in this CommandView artifact."


def test_cyclomatic_complexity_map_renders_definition() -> None:
    script = textwrap.dedent(
        f"""
                import {{ buildCyclomaticComplexityMapDiagram }} from \"{MODULE_PATH.as_uri()}\";

                const functions = new Map([
                    ["alpha::controller", {{
                        name: "controller",
                        moduleId: "alpha.core",
                        cyclomaticComplexity: 21,
                        metrics: {{ coverage: 0.42, lineCount: 230 }},
                    }}],
                    ["alpha::helper", {{
                        name: "helper",
                        moduleId: "alpha.core",
                        metrics: {{ complexity: 8, coverage: 0.71, lineCount: 90 }},
                    }}],
                    ["beta::service", {{
                        name: "service",
                        moduleId: "beta.runtime",
                        cyclomaticComplexity: 15,
                        metrics: {{ coverage: 0.55, lineCount: 140 }},
                    }}],
                    ["beta::formatter", {{
                        name: "formatter",
                        moduleId: "beta.runtime",
                        metrics: {{ complexity: 3, coverage: 0.9, lineCount: 60 }},
                    }}],
                ]);

                const result = buildCyclomaticComplexityMapDiagram(functions, {{
                    viewLabel: "Quality Metrics · Cyclomatic Complexity Map",
                    scopeDescription: "repository",
                    moduleLimit: 5,
                    functionLimit: 4,
                    coverageRiskThreshold: 0.6,
                }});

                console.log(JSON.stringify(result));
                """
    )

    payload = _run_node_module(script)

    definition = payload["definition"]
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "alpha_core" in definition
    assert "Extreme Complexity" in definition

    status_message = payload["statusMessage"]
    assert "Rendered Cyclomatic Complexity Map" in status_message
    assert "extreme 2" in status_message

    stats = payload["stats"]
    assert stats["totalModules"] == 2
    assert stats["displayedModules"] == 2
    assert stats["hiddenModules"] == 0
    assert stats["extreme"] == 2
    assert stats["high"] == 0
    assert stats["moderate"] == 1
    assert stats["low"] == 1
    assert stats["unknown"] == 0
    assert stats["maxComplexity"] == 21
    assert stats["averageComplexity"] == pytest.approx(11.75, rel=1e-9)
    assert stats["coverageAverage"] == pytest.approx(0.645, rel=1e-9)
    assert stats["coverageBelowThreshold"] == 2
    assert stats["coverageThreshold"] == 0.6

    top_modules = stats["topModules"]
    assert isinstance(top_modules, list)
    assert len(top_modules) == 2
    assert top_modules[0]["moduleId"] == "alpha.core"
    assert top_modules[0]["extreme"] == 1
    assert top_modules[0]["high"] == 0
    assert top_modules[0]["averageComplexity"] == pytest.approx(14.5, rel=1e-9)
    assert top_modules[0]["maxComplexity"] == 21
    assert top_modules[1]["moduleId"] == "beta.runtime"
    assert top_modules[1]["extreme"] == 1
    assert top_modules[1]["high"] == 0
    assert top_modules[1]["averageComplexity"] == pytest.approx(9.0, rel=1e-9)
    assert top_modules[1]["maxComplexity"] == 15

    status_details = payload["statusDetails"]
    assert isinstance(status_details, list)
    assert status_details
    assert status_details[0]["title"] in {"alpha.core", "beta.runtime"}
