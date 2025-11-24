from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
INVENTORY_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "function_inventory_overview.js"
)
TIMELINE_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "screening_signal_timeline.js"
)

if not INVENTORY_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected function inventory builder module at {INVENTORY_MODULE_PATH}")

if not TIMELINE_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected screening timeline builder module at {TIMELINE_MODULE_PATH}")


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


def test_health_pack_builders_coexist_without_state_reset() -> None:
    script = f"""
import {{ buildFunctionInventoryOverviewDiagram }} from "{INVENTORY_MODULE_PATH.as_uri()}";
import {{ buildScreeningTimelineDiagram }} from "{TIMELINE_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.module", {{ moduleId: "alpha.module" }}],
  ["beta.module", {{ moduleId: "beta.module" }}],
]);
const functions = new Map([
  ["alpha.module::f1", {{ docstringQuality: {{ exists: true }}, typeHintCoverage: 0.9, todoTags: 1 }}],
  ["beta.module::g1", {{ docstringQuality: {{ exists: false }}, annotationCoverage: 0.6, todoTags: 0 }}],
]);
const history = {{
  events: [
    {{
      timestamp: "2025-11-08T12:00:00Z",
      packId: "docstring_coverage",
      packLabel: "Docstring Coverage",
      severity: "warning",
      score: 70.0,
      thresholds: {{ warning: 80, failure: 60 }},
      metrics: {{ functions_total: 5, functions_documented: 3 }},
      context: {{ folder_name: "repo-studios", inventory_generated_at: "2025-11-08T11:55:00Z" }}
    }}
  ],
}};

const overviewFirst = buildFunctionInventoryOverviewDiagram(modules, functions, {{ viewLabel: "Health · Overview" }});
const timeline = buildScreeningTimelineDiagram(history, {{ artifactLabel: "Repo Studios" }});
const overviewSecond = buildFunctionInventoryOverviewDiagram(modules, functions, {{ viewLabel: "Health · Overview" }});

console.log(JSON.stringify({{
  overviewFirstDefinition: overviewFirst.definition,
  overviewSecondDefinition: overviewSecond.definition,
  overviewFirstStatus: overviewFirst.statusMessage,
  overviewSecondStatus: overviewSecond.statusMessage,
  overviewFirstStats: overviewFirst.stats,
  overviewSecondStats: overviewSecond.stats,
  timelineDefinition: timeline.definition,
  timelineStatus: timeline.statusMessage,
  timelineEventCount: timeline.eventCount,
}}));
"""
    payload = _run_node_module(script)

    assert payload["overviewFirstDefinition"] == payload["overviewSecondDefinition"]
    assert payload["overviewFirstStatus"] == payload["overviewSecondStatus"]
    assert payload["overviewFirstStats"] == payload["overviewSecondStats"]
    assert payload["timelineDefinition"].startswith("timeline\n  title Repo Studios Screening Scores")
    assert "Docstrings" in payload["overviewFirstDefinition"]
    assert "Type Hints" in payload["overviewFirstDefinition"]
    assert payload["timelineEventCount"] == 1
    assert "Rendered Function Inventory Overview" in payload["overviewFirstStatus"]
    assert "Rendered screening timeline" in payload["timelineStatus"]
