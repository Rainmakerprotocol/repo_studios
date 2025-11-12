from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
VIEWER_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "viewer.js"
)

if not VIEWER_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected viewer module at {VIEWER_PATH}")


@pytest.fixture(scope="module", autouse=True)
def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Node.js runtime is required for viewer view-definition tests: {exc}")


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


def _build_common_script(prefix: str) -> str:
    return f"""
if (!globalThis.window) {{
  globalThis.window = {{}};
}}
if (!window.addEventListener) {{
  window.addEventListener = () => {{}};
}}
if (!window.removeEventListener) {{
  window.removeEventListener = () => {{}};
}}
if (!window.viewerConfig) {{
  window.viewerConfig = {{}};
}}
if (!window.mermaid) {{
  window.mermaid = {{ initialize: () => {{}}, render: async () => ({{ svg: '' }}) }};
}}
if (!globalThis.document) {{
  globalThis.document = {{ readyState: 'loading', addEventListener: () => {{}} }};
}}
if (!globalThis.localStorage) {{
  globalThis.localStorage = {{ getItem: () => null, setItem: () => {{}}, removeItem: () => {{}} }};
}}

const originalLog = console.log;
const originalWarn = console.warn || (() => {{}});
console.log = () => {{}};
console.warn = () => {{}};

const viewer = await import('{VIEWER_PATH.as_uri()}');
const api = viewer.__test__;

api.resetViewStateForTest();

const classes = new Map([
  ["alpha.base.Base", {{
    id: "alpha.base.Base",
    name: "Base",
    moduleId: "alpha.base",
    methods: [],
    attributes: [],
    resolvedBases: [],
    derivedClassIds: ["gamma.controller.Derived"],
  }}],
  ["beta.support.ServiceMixin", {{
    id: "beta.support.ServiceMixin",
    name: "ServiceMixin",
    moduleId: "beta.support",
    methods: [],
    attributes: [],
    resolvedBases: [],
    derivedClassIds: ["gamma.controller.Derived"],
  }}],
  ["gamma.controller.Derived", {{
    id: "gamma.controller.Derived",
    name: "Derived",
    moduleId: "gamma.controller",
    methods: [],
    attributes: [],
    resolvedBases: [
      {{ raw: "Base", normalized: "alpha.base.Base", classId: "alpha.base.Base", matchType: "project" }},
      {{ raw: "ServiceMixin", normalized: "beta.support.ServiceMixin", classId: "beta.support.ServiceMixin", matchType: "project" }},
    ],
    derivedClassIds: [],
  }}],
]);

const modules = new Map([
  ["alpha.base", {{ moduleId: "alpha.base", classes: ["alpha.base.Base"], classCount: 1 }}],
  ["beta.support", {{ moduleId: "beta.support", classes: ["beta.support.ServiceMixin"], classCount: 1 }}],
  ["gamma.controller", {{ moduleId: "gamma.controller", classes: ["gamma.controller.Derived"], classCount: 1 }}],
]);

api.setNormalizedDataForTest({{
  classes,
  modules,
}});
{prefix}
const result = api.buildClassInheritanceHierarchyViewDefinitionForTest();

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  definition: result.definition,
  statusMessage: result.statusMessage,
  statusDetails: result.statusDetails,
  stats: result.stats,
}}));
"""


def test_class_inheritance_view_definition_scopes_to_module() -> None:
    prefix = "api.setLevelSelectionsForTest({ moduleId: 'gamma.controller' });"
    payload = _run_node_module(_build_common_script(prefix))

    definition = payload["definition"]
    assert isinstance(definition, str)
    assert definition.startswith("graph TD")
    assert "gamma_controller_Derived" in definition
    assert "alpha_base_Base" in definition

    status = payload["statusMessage"]
    assert status.startswith("Rendered Class Inheritance Hierarchy for gamma.controller")
    assert "fallback" not in status.lower()

    stats = payload["stats"]
    assert stats["classCount"] == 3
    assert stats["moduleCount"] == 3

    details = payload["statusDetails"]
    assert isinstance(details, list)
    assert not any(detail.get("type") == "info" for detail in details)


def test_class_inheritance_view_definition_falls_back_to_repository() -> None:
    prefix = "api.setLevelSelectionsForTest({ moduleId: 'delta.missing' });"
    payload = _run_node_module(_build_common_script(prefix))

    status = payload["statusMessage"]
    assert status.endswith("Showing repository hierarchy instead.")

    details = payload["statusDetails"]
    info_section = next(item for item in details if item.get("type") == "info")
    assert "Scope fallback applied" in info_section["title"]
    assert "delta.missing" in info_section["description"]
