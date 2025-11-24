from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
VIEWER_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "viewer.js"


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


def test_public_private_api_surface_normalization() -> None:
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
console.log = () => {{}};

const {{ __test__ }} = await import('{VIEWER_MODULE_PATH.as_uri()}');

const moduleInput = {{
  module_id: 'alpha.api',
  relative_path: 'alpha/api.py',
  path: 'alpha/api.py',
  import_graph: [],
  imports_detailed: [
    {{
      kind: 'from',
      module: 'external.lib',
      names: [{{ name: 'external_api', asname: null }}],
      lineno: 2,
    }},
  ],
  functions: [
    {{ name: 'public_func', qualified_name: 'alpha.api::public_func', line: 10, signature: 'def public_func()' }},
    {{ name: '_helper', qualified_name: 'alpha.api::_helper', line: 20, signature: 'def _helper()' }},
    {{ name: 'utility', qualified_name: 'alpha.api::utility', line: 30, signature: 'def utility()' }},
  ],
  classes: [
    {{ name: 'PublicClass', line: 40, methods: [], bases: [], decorators: [] }},
    {{ name: '_InternalClass', line: 60, methods: [], bases: [], decorators: [] }},
  ],
  globals: [
    {{ name: 'CONFIG', value_kind: 'dict', lineno: 5 }},
    {{ name: '_SECRET', value_kind: 'str', lineno: 6 }},
  ],
  exports: {{
    symbols: ['public_func', 'PublicClass', 'CONFIG', 'external_api'],
    missing: ['MISSING_API'],
    lineno: 3,
  }},
}};

const moduleRecord = __test__.createModuleRecord(moduleInput);
const functionPublic = __test__.createFunctionRecord({{
  name: 'public_func',
  qualified_name: 'alpha.api::public_func',
  line: 10,
  signature: 'def public_func()',
  coverage: 0.8,
  type_hint_coverage: 0.9,
  docstring_quality: {{ coverage: 0.75 }},
}}, 'alpha.api');
const functionPrivate = __test__.createFunctionRecord({{
  name: '_helper',
  qualified_name: 'alpha.api::_helper',
  line: 20,
  signature: 'def _helper()',
  coverage: 0.6,
  type_hint_coverage: 0.0,
}}, 'alpha.api');
const functionImplicit = __test__.createFunctionRecord({{
  name: 'utility',
  qualified_name: 'alpha.api::utility',
  line: 30,
  signature: 'def utility()',
  coverage: 0.5,
  type_hint_coverage: 0.1,
}}, 'alpha.api');

const classPublic = __test__.createClassRecord({{
  name: 'PublicClass',
  line: 40,
  methods: [],
  bases: [],
  decorators: [],
}}, 'alpha.api');
const classPrivate = __test__.createClassRecord({{
  name: '_InternalClass',
  line: 60,
  methods: [],
  bases: [],
  decorators: [],
}}, 'alpha.api');

moduleRecord.functions = [functionPublic.id, functionPrivate.id, functionImplicit.id];
moduleRecord.classes = [classPublic.id, classPrivate.id];

const functions = new Map([
  [functionPublic.id, functionPublic],
  [functionPrivate.id, functionPrivate],
  [functionImplicit.id, functionImplicit],
]);
const classes = new Map([
  [classPublic.id, classPublic],
  [classPrivate.id, classPrivate],
]);

const apiSurface = __test__.buildModuleApiSurfaceForTest(moduleRecord, functions, classes);

console.log = originalLog;

console.log(JSON.stringify(apiSurface));
"""

    payload = _run_node_module(script)

    assert payload["hasDeclaredExports"] is True
    assert payload["strategy"] == "explicit"
    assert payload["exportedSymbols"] == ["CONFIG", "PublicClass", "external_api", "public_func"]

    public_functions = payload["functions"]["public"]
    internal_functions = payload["functions"]["internal"]
    assert [entry["name"] for entry in public_functions] == ["public_func"]
    assert {entry["name"] for entry in internal_functions} == {"_helper", "utility"}

    exported_entry = public_functions[0]
    assert exported_entry["category"] == "exported"
    assert exported_entry["reason"] == "Declared in __all__"
    assert exported_entry["typeHintCoverage"] == 0.9

    utility_entry = next(entry for entry in internal_functions if entry["name"] == "utility")
    assert utility_entry["category"] == "internal"
    assert utility_entry["reason"].startswith("Module defines __all__")

    private_entry = next(entry for entry in internal_functions if entry["name"] == "_helper")
    assert private_entry["category"] == "private"

    public_classes = payload["classes"]["public"]
    internal_classes = payload["classes"]["internal"]
    assert [entry["name"] for entry in public_classes] == ["PublicClass"]
    assert [entry["name"] for entry in internal_classes] == ["_InternalClass"]

    public_globals = payload["globals"]["public"]
    internal_globals = payload["globals"]["internal"]
    assert [entry["name"] for entry in public_globals] == ["CONFIG"]
    assert [entry["name"] for entry in internal_globals] == ["_SECRET"]

    assert payload["reexports"] == [
        {
            "symbol": "external_api",
            "sourceModule": "external.lib",
            "sourceName": "external_api",
            "sourceQualifiedName": "external.lib.external_api",
            "lineno": 2,
        }
    ]

    assert payload["missingExports"] == [
        {
            "symbol": "MISSING_API",
            "kind": "missing",
        }
    ]

    counts = payload["counts"]
    assert counts["functions"] == {"public": 1, "internal": 2}
    assert counts["classes"] == {"public": 1, "internal": 1}
    assert counts["globals"] == {"public": 1, "internal": 1}
    assert counts["exported"] == 4
    assert counts["reexports"] == 1
    assert counts["missing"] == 1
