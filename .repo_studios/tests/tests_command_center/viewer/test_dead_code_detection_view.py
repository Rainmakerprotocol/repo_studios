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
    / "dead_code_detection.js"
)

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected dead code detection builder at {MODULE_PATH}")


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


def test_dead_code_detection_requires_modules() -> None:
    script = f"""
import {{ buildDeadCodeDetectionDiagram }} from "{MODULE_PATH.as_uri()}";
const result = buildDeadCodeDetectionDiagram();
console.log(JSON.stringify(result));
"""

    payload = _run_node_module(script)

    assert payload["message"].startswith("No modules recorded in this CommandView artifact.")


def test_dead_code_detection_renders_definition_and_stats() -> None:
    script = f"""
import {{ buildDeadCodeDetectionDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    moduleId: "alpha.core",
    unreachableFunctions: [
      {{ name: "orphan", qualified_name: "alpha.core::orphan", lineno: 120 }},
      {{ name: "helper", qualified_name: "alpha.core::helper", lineno: 95 }},
      {{ name: "legacy", qualified_name: "alpha.core::legacy", lineno: 210, parent_class: "Legacy" }},
      {{ name: "shadow", qualified_name: "alpha.core::shadow", lineno: 60 }},
      {{ name: "unused_hook", qualified_name: "alpha.core::unused_hook", lineno: 15 }},
    ],
    unusedImports: [
      {{ target: "collections.Counter", imported_as: "Counter", module: "collections", lineno: 6, kind: "from" }},
      {{ target: "math", imported_as: "math", lineno: 3, kind: "import" }},
    ],
  }}],
  ["beta.utils", {{
    moduleId: "beta.utils",
    unreachableFunctions: [
      {{ name: "unused", qualified_name: "beta.utils::unused", lineno: 44 }},
    ],
    unusedImports: [
      {{ target: "json", imported_as: "json", lineno: 11, kind: "import" }},
      {{ target: "uuid.uuid4", imported_as: "uuid4", module: "uuid", lineno: 18, kind: "from" }},
    ],
  }}],
  ["gamma.adapters", {{
    moduleId: "gamma.adapters",
    unusedImports: [
      {{ target: "typing.Optional", imported_as: "Optional", module: "typing", lineno: 5, kind: "from" }},
    ],
  }}],
  ["delta.clean", {{
    moduleId: "delta.clean",
  }}],
]);

const result = buildDeadCodeDetectionDiagram(modules, {{ scopeDescription: "repository" }});

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
    assert "class module_alpha_core deadCritical" in definition
    assert "deadFunction" in definition
    assert "deadImport" in definition

    status_message = payload["statusMessage"]
    assert "Dead Code Detection" in status_message
    assert "modules" in status_message

    stats = payload["stats"]
    assert stats["moduleCount"] == 3
    assert stats["displayedModules"] == 3
    assert stats["critical"] == 1
    assert stats["moderate"] >= 1
    assert stats["observed"] >= 1
    assert stats["unreachableFunctions"] >= 6
    assert stats["unusedImports"] >= 5

    details = {detail["title"]: detail for detail in payload["statusDetails"]}
    assert set(details) == {"alpha.core", "beta.utils", "gamma.adapters"}
    assert details["alpha.core"]["unreachableCount"] == 5
    assert details["beta.utils"]["unusedImportCount"] == 2
    assert details["gamma.adapters"]["unusedImportCount"] == 1
    assert len(details["alpha.core"]["highlightedFunctions"]) >= 1


def test_dead_code_detection_is_deterministic() -> None:
    script = f"""
import {{ buildDeadCodeDetectionDiagram }} from "{MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.core", {{
    moduleId: "alpha.core",
    unreachableFunctions: [{{ name: "unused", qualified_name: "alpha.core::unused", lineno: 12 }}],
    unusedImports: [{{ target: "sys", imported_as: "sys", lineno: 4 }}],
  }}],
  ["beta.utils", {{
    moduleId: "beta.utils",
    unusedImports: [{{ target: "os", imported_as: "os", lineno: 7 }}],
  }}],
]);

const first = buildDeadCodeDetectionDiagram(modules, {{ scopeDescription: "repository" }});
const second = buildDeadCodeDetectionDiagram(modules, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  definitionStable: first.definition === second.definition,
  statusStable: first.statusMessage === second.statusMessage,
  detailStable: JSON.stringify(first.statusDetails) === JSON.stringify(second.statusDetails),
}}));
"""

    payload = _run_node_module(script)

    assert payload["definitionStable"] is True
    assert payload["statusStable"] is True
    assert payload["detailStable"] is True
