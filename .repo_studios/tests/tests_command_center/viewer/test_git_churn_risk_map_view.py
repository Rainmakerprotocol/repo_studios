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
    / "git_churn_risk_map.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected git churn risk map builder at {MODULE_PATH}")


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


def test_git_churn_risk_map_requires_modules() -> None:
    script = f"""
import {{ buildGitChurnRiskMapDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildGitChurnRiskMapDiagram();
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert payload["message"].startswith("No modules recorded")


def test_git_churn_risk_map_renders_definition_and_stats() -> None:
    script = f"""
import {{ buildGitChurnRiskMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    moduleId: "alpha.core",
    gitChurn: {{
      commit_count: 24,
      additions: 1200,
      deletions: 300,
      net_changes: 900,
      latest_commit: {{
        hash: "1111",
        timestamp: "2025-11-10T12:00:00+00:00"
      }},
    }},
    functions: [
      "alpha.core::service",
      "alpha.core::helper",
    ],
  }}],
  ["beta.utils", {{
    moduleId: "beta.utils",
    gitChurn: {{
      commit_count: 6,
      additions: 120,
      deletions: 30,
      net_changes: 90,
      latest_commit: {{
        hash: "2222",
        timestamp: "2025-11-09T02:30:00+00:00"
      }},
    }},
    functions: ["beta.utils::utility"],
  }}],
  ["gamma.adapters", {{
    moduleId: "gamma.adapters",
    gitChurn: {{
      commit_count: 2,
      additions: 10,
      deletions: 4,
      net_changes: 6,
      latest_commit: {{
        hash: "3333",
        timestamp: "2025-11-08T21:10:00+00:00"
      }},
    }},
    functions: ["gamma.adapters::bridge"],
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
    metrics: {{ coverage: 0.77 }},
  }}],
  ["beta.utils::utility", {{
    id: "beta.utils::utility",
    moduleId: "beta.utils",
    metrics: {{ coverage: 0.31 }},
  }}],
  ["gamma.adapters::bridge", {{
    id: "gamma.adapters::bridge",
    moduleId: "gamma.adapters",
    metrics: {{ coverage: 0.94 }},
  }}],
]);

const baselines = {{
  files_with_data: 6,
  total_commits: 36,
  total_additions: 900,
  total_deletions: 300,
  net_changes: 600,
}};

const result = buildGitChurnRiskMapDiagram(modules, {{
  functions,
  baselines,
  scopeDescription: "repository",
}});

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
    assert "class module_alpha_core churnCritical" in definition

    status = payload["statusMessage"]
    assert "Rendered Git Churn Risk Map" in status
    assert "modules" in status

    stats = payload["stats"]
    assert stats["moduleCount"] == 3
    assert stats["displayedModules"] == 3
    assert stats["critical"] >= 1
    assert stats["medianCommits"] >= 2

    details = {detail["title"]: detail for detail in payload["statusDetails"]}
    assert set(details) == {"alpha.core", "beta.utils", "gamma.adapters"}
    assert details["alpha.core"]["severity"] == "critical"
    assert details["beta.utils"]["commits"] == 6
    assert details["gamma.adapters"]["linesChanged"] == 14


def test_git_churn_risk_map_is_deterministic() -> None:
    script = f"""
import {{ buildGitChurnRiskMapDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    moduleId: "alpha.core",
    gitChurn: {{ commit_count: 8, additions: 100, deletions: 20, net_changes: 80 }},
  }}],
  ["beta.utils", {{
    moduleId: "beta.utils",
    gitChurn: {{ commit_count: 4, additions: 40, deletions: 10, net_changes: 30 }},
  }}],
]);

const baselines = {{
  files_with_data: 2,
  total_commits: 12,
  total_additions: 140,
  total_deletions: 30,
  net_changes: 110,
}};

const first = buildGitChurnRiskMapDiagram(modules, {{ baselines, scopeDescription: "repository" }});
const second = buildGitChurnRiskMapDiagram(modules, {{ baselines, scopeDescription: "repository" }});

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
