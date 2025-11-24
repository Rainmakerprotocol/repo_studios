from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
BUILDER_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "class_inheritance_hierarchy.js"

if not BUILDER_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected class inheritance hierarchy builder at {BUILDER_PATH}")


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


def test_class_inheritance_hierarchy_renders_relationships() -> None:
    script = f"""
import {{ buildClassInheritanceHierarchyDiagram }} from "{BUILDER_PATH.as_uri()}";

const classes = new Map([
  ["alpha.base.Base", {{
    id: "alpha.base.Base",
    name: "Base",
    moduleId: "alpha.base",
    methods: [{{ id: "alpha.base::Base.method", name: "method" }}],
    attributes: [{{ name: "state" }}],
    methodCount: 1,
    attributeCount: 1,
    resolvedBases: [],
    derivedClassIds: ["gamma.controller.Derived"],
    docstringQuality: {{ exists: true }},
    codeSmells: [],
  }}],
  ["beta.support.ServiceMixin", {{
    id: "beta.support.ServiceMixin",
    name: "ServiceMixin",
    moduleId: "beta.support",
    methods: [],
    attributes: [],
    methodCount: 0,
    attributeCount: 0,
    resolvedBases: [],
    derivedClassIds: ["gamma.controller.Derived"],
    docstringQuality: {{ exists: false }},
    codeSmells: ["long-inheritance"],
  }}],
  ["gamma.controller.Derived", {{
    id: "gamma.controller.Derived",
    name: "Derived",
    moduleId: "gamma.controller",
    methods: [{{ id: "gamma.controller::Derived.execute", name: "execute" }}],
    attributes: [],
    methodCount: 1,
    attributeCount: 0,
    resolvedBases: [
      {{ raw: "Base", normalized: "alpha.base.Base", classId: "alpha.base.Base", matchType: "project" }},
      {{ raw: "ServiceMixin", normalized: "beta.support.ServiceMixin", classId: "beta.support.ServiceMixin", matchType: "project" }},
      {{ raw: "ExternalFramework.Controller", normalized: "external.framework.Controller", classId: null, matchType: "external" }},
      {{ raw: "object", normalized: "object", classId: null, matchType: "builtin" }},
    ],
    derivedClassIds: [],
    docstringQuality: {{ exists: true }},
    codeSmells: [],
  }}],
]);

const result = buildClassInheritanceHierarchyDiagram(classes, {{
  primaryClassIds: new Set(["gamma.controller.Derived"]),
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
    assert "gamma_controller_Derived --> alpha_base_Base" in definition
    assert "gamma_controller_Derived --> beta_support_ServiceMixin" in definition
    assert "gamma_controller_Derived -.->" in definition
    assert "class gamma_controller_Derived local" in definition

    status = payload["statusMessage"]
    assert status == "Rendered Class Inheritance Hierarchy for repository (3 classes, 2 roots, 1 leaves)."

    stats = payload["stats"]
    assert stats["classCount"] == 3
    assert stats["rootClasses"] == 2
    assert stats["leafClasses"] == 1
    assert stats["edgeCount"] == 4  # includes two internal, one external, one builtin reference
    assert stats["placeholderCount"] == 2
    assert stats["externalBaseReferences"] == 1
    assert stats["builtinBaseReferences"] == 1

    details = payload["statusDetails"]
    assert isinstance(details, list)
    module_section = next(item for item in details if item.get("title") == "Module Distribution")
    assert any(entry["label"] == "gamma.controller" for entry in module_section["items"])
    unresolved_section = next(item for item in details if item.get("title") == "Unresolved Bases")
    assert any("External base" in entry["value"] for entry in unresolved_section["items"])
    assert any("Builtin base" in entry["value"] for entry in unresolved_section["items"])


def test_class_inheritance_hierarchy_reports_missing_data() -> None:
    script = f"""
import {{ buildClassInheritanceHierarchyDiagram }} from "{BUILDER_PATH.as_uri()}";

const classes = new Map();

const result = buildClassInheritanceHierarchyDiagram(classes, {{ scopeDescription: "alpha.module" }});

console.log(JSON.stringify({{
  message: result.message,
}}));
"""

    payload = _run_node_module(script)

    assert payload["message"] == "Class inheritance metadata is not available in this scope."
