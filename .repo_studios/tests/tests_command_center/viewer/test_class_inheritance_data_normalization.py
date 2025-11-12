from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
VIEWER_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "viewer.js"
)

if not VIEWER_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected viewer module at {VIEWER_MODULE_PATH}")


@pytest.fixture(scope="module", autouse=True)
def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Node.js runtime is required for viewer normalization tests: {exc}")


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


def test_class_inheritance_relations_are_normalized_and_resolved() -> None:
    script = f"""
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

const {{ __test__ }} = await import('{VIEWER_MODULE_PATH.as_uri()}');

const classes = new Map();

const baseModule = __test__.createModuleRecord({{
  module_id: 'alpha.base',
  relative_path: 'alpha/base.py',
}});
const mixinModule = __test__.createModuleRecord({{
  module_id: 'beta.support',
  relative_path: 'beta/support.py',
}});
const controllerModule = __test__.createModuleRecord({{
  module_id: 'gamma.controller',
  relative_path: 'gamma/controller.py',
}});

const baseClass = __test__.createClassRecord({{
  name: 'Base',
  line: 5,
  bases: [],
  methods: [],
  attributes: [],
}}, baseModule.id);
const mixinClass = __test__.createClassRecord({{
  name: 'ServiceMixin',
  line: 8,
  bases: [],
  methods: [],
  attributes: [],
}}, mixinModule.id);
const controllerBaseClass = __test__.createClassRecord({{
  name: 'ControllerBase',
  line: 10,
  bases: [],
  methods: [],
  attributes: [],
}}, controllerModule.id);
const derivedClass = __test__.createClassRecord({{
  name: 'Derived',
  line: 25,
  bases: ['ControllerBase', 'alpha.base.Base', 'beta.support.ServiceMixin', 'object'],
  methods: [{{ name: 'execute', qualified_name: 'gamma.controller::Derived.execute', line: 40 }}],
  attributes: [{{ name: 'state', lineno: 32 }}],
}}, controllerModule.id);

baseModule.classes = [baseClass.id];
mixinModule.classes = [mixinClass.id];
controllerModule.classes = [controllerBaseClass.id, derivedClass.id];

classes.set(baseClass.id, baseClass);
classes.set(mixinClass.id, mixinClass);
classes.set(controllerBaseClass.id, controllerBaseClass);
classes.set(derivedClass.id, derivedClass);

const inheritanceSummary = __test__.finalizeClassInheritanceForTest(classes);

const preparedBase = classes.get(baseClass.id);
const preparedMixin = classes.get(mixinClass.id);
const preparedControllerBase = classes.get(controllerBaseClass.id);
const preparedDerived = classes.get(derivedClass.id);

console.log = originalLog;
console.warn = originalWarn;

console.log(JSON.stringify({{
  baseResolved: preparedDerived.resolvedBases,
  baseDerived: preparedBase.derivedClassIds,
  mixinDerived: preparedMixin.derivedClassIds,
  controllerDerived: preparedControllerBase.derivedClassIds,
  derivedResolved: preparedDerived.resolvedBases,
  derivedLeaf: preparedDerived.derivedClassIds,
  summary: {{
    stats: inheritanceSummary.stats,
    derivedByBase: Array.from(inheritanceSummary.derivedByBase.entries()),
    modules: Array.from(inheritanceSummary.modules.entries()),
  }},
}}));
"""

    payload = _run_node_module(script)

    derived_bases = {(entry["normalized"], entry.get("matchType"), entry.get("classId")) for entry in payload["derivedResolved"]}

    assert ("ControllerBase", "local", "gamma.controller.ControllerBase") in derived_bases
    assert ("alpha.base.Base", "project", "alpha.base.Base") in derived_bases
    assert ("beta.support.ServiceMixin", "project", "beta.support.ServiceMixin") in derived_bases
    assert ("object", "builtin", None) in derived_bases

    assert payload["baseDerived"] == ["gamma.controller.Derived"]
    assert payload["mixinDerived"] == ["gamma.controller.Derived"]
    assert payload["controllerDerived"] == ["gamma.controller.Derived"]
    assert payload["derivedLeaf"] == []

    summary = payload["summary"]
    assert summary["stats"]["classCount"] == 4
    assert summary["stats"]["rootClasses"] == 3
    assert summary["stats"]["leafClasses"] == 1
    assert summary["stats"]["externalBaseReferences"] == 1

    derived_by_base = {item[0]: item[1] for item in summary["derivedByBase"]}
    assert derived_by_base["alpha.base.Base"] == ["gamma.controller.Derived"]
    assert derived_by_base["gamma.controller.ControllerBase"] == ["gamma.controller.Derived"]

    modules_with_classes = {item[0]: item[1] for item in summary["modules"]}
    assert modules_with_classes["gamma.controller"] == [
        "gamma.controller.ControllerBase",
        "gamma.controller.Derived",
    ]
