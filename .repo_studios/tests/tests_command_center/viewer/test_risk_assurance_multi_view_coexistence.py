from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
TEST_COVERAGE_MODULE_PATH = (
    REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "test_coverage_mapping.js"
)
GIT_CHURN_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "git_churn_risk_map.js"
DEAD_CODE_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "dead_code_detection.js"

if not TEST_COVERAGE_MODULE_PATH.exists():  # pragma: no cover
    raise AssertionError(f"Expected test coverage builder at {TEST_COVERAGE_MODULE_PATH}")
if not GIT_CHURN_MODULE_PATH.exists():  # pragma: no cover
    raise AssertionError(f"Expected git churn builder at {GIT_CHURN_MODULE_PATH}")
if not DEAD_CODE_MODULE_PATH.exists():  # pragma: no cover
    raise AssertionError(f"Expected dead code builder at {DEAD_CODE_MODULE_PATH}")


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
        encoding="utf-8",
    )
    if result.stderr.strip():
        pytest.fail(f"Node.js script wrote to stderr: {result.stderr}")
    return json.loads(result.stdout.strip())


def test_risk_assurance_views_coexist() -> None:
    script = f"""
import {{ buildTestCoverageMappingDiagram }} from "{TEST_COVERAGE_MODULE_PATH.as_uri()}";
import {{ buildGitChurnRiskMapDiagram }} from "{GIT_CHURN_MODULE_PATH.as_uri()}";
import {{ buildDeadCodeDetectionDiagram }} from "{DEAD_CODE_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    moduleId: "alpha.core",
    functions: ["alpha.core::service", "alpha.core::helper"],
    coverageSignals: {{
      imports: ["tests/test_alpha.py::TestAlpha::test_service"],
      has_matches: true,
    }},
    gitChurn: {{
      commit_count: 14,
      additions: 420,
      deletions: 120,
      net_changes: 300,
    }},
    unreachableFunctions: [
      {{ qualified_name: "alpha.core::legacy", name: "legacy", lineno: 210 }},
    ],
    unusedImports: [
      {{ target: "collections.Counter", imported_as: "Counter", module: "collections", lineno: 12 }},
    ],
  }}],
  ["beta.utils", {{
    moduleId: "beta.utils",
    functions: ["beta.utils::utility"],
    coverageSignals: {{
      imports: ["tests/test_beta.py::TestBeta::test_utility"],
      has_matches: true,
    }},
    gitChurn: {{
      commit_count: 4,
      additions: 80,
      deletions: 20,
      net_changes: 60,
    }},
    unreachableFunctions: [
      {{ qualified_name: "beta.utils::unused", name: "unused", lineno: 48 }},
    ],
    unusedImports: [
      {{ target: "json", imported_as: "json", lineno: 14 }},
    ],
  }}],
]);

const functions = new Map([
  ["alpha.core::service", {{
    id: "alpha.core::service",
    moduleId: "alpha.core",
    metrics: {{ coverage: 0.52 }},
  }}],
  ["alpha.core::helper", {{
    id: "alpha.core::helper",
    moduleId: "alpha.core",
    metrics: {{ coverage: 0.73 }},
  }}],
  ["beta.utils::utility", {{
    id: "beta.utils::utility",
    moduleId: "beta.utils",
    metrics: {{ coverage: 0.34 }},
  }}],
]);

const callGraph = new Map([
  ["alpha.core::service", ["alpha.core::helper"]],
  ["alpha.core::helper", []],
  ["beta.utils::utility", []],
]);

const baselines = {{
  files_with_data: 2,
  total_commits: 18,
  total_additions: 500,
  total_deletions: 140,
  net_changes: 360,
}};

const coverageFirst = buildTestCoverageMappingDiagram(modules, functions, {{
  scopeDescription: "repository",
  centerLabel: "Test Coverage Mapping",
}});
const churnFirst = buildGitChurnRiskMapDiagram(modules, {{
  functions,
  baselines,
  scopeDescription: "repository",
}});
const deadCodeFirst = buildDeadCodeDetectionDiagram(modules, {{
  scopeDescription: "repository",
}});

const coverageSecond = buildTestCoverageMappingDiagram(modules, functions, {{
  scopeDescription: "repository",
  centerLabel: "Test Coverage Mapping",
}});
const churnSecond = buildGitChurnRiskMapDiagram(modules, {{
  functions,
  baselines,
  scopeDescription: "repository",
}});
const deadCodeSecond = buildDeadCodeDetectionDiagram(modules, {{
  scopeDescription: "repository",
}});

console.log(JSON.stringify({{
  coverageDefinitionStable: coverageFirst.definition === coverageSecond.definition,
  coverageStatusStable: coverageFirst.statusMessage === coverageSecond.statusMessage,
  churnDefinitionStable: churnFirst.definition === churnSecond.definition,
  churnStatusStable: churnFirst.statusMessage === churnSecond.statusMessage,
  deadCodeDefinitionStable: deadCodeFirst.definition === deadCodeSecond.definition,
  deadCodeStatusStable: deadCodeFirst.statusMessage === deadCodeSecond.statusMessage,
  labels: [coverageFirst.label, churnFirst.label, deadCodeFirst.label],
}}));
"""

    payload = _run_node_module(script)

    assert payload["coverageDefinitionStable"] is True
    assert payload["coverageStatusStable"] is True
    assert payload["churnDefinitionStable"] is True
    assert payload["churnStatusStable"] is True
    assert payload["deadCodeDefinitionStable"] is True
    assert payload["deadCodeStatusStable"] is True
    assert payload["labels"] == [
        "Risk & Assurance · Test Coverage Mapping",
        "Risk & Assurance · Git Churn Risk Map",
        "Risk & Assurance · Dead Code Detection",
    ]
