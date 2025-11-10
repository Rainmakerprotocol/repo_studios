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


def _ensure_node_runtime() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Node.js runtime is required for viewer normalization tests: {exc}")


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


def test_module_export_summary_classifies_local_and_reexported_symbols() -> None:
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

const record = __test__.createModuleRecord({{
  module_id: 'alpha.contracts.api',
  path: 'alpha/contracts/api.py',
  relative_path: 'alpha/contracts/api.py',
  functions: [
    {{
      name: 'expose_api',
      qualified_name: 'alpha.contracts.api::expose_api',
      line: 18,
      signature: 'def expose_api():',
      docstring_quality: {{ exists: true, coverage: 1 }},
    }},
  ],
  classes: [
    {{
      name: 'ExportedClass',
      line: 42,
      docstring_quality: {{ exists: true }},
    }},
  ],
  globals: [
    {{ name: 'CONFIG', lineno: 7, value_kind: 'dict' }},
  ],
  imports_detailed: [
    {{
      kind: 'from',
      module: 'alpha.shared.helpers',
      names: [{{ name: 'helper', asname: 'public_helper' }}],
      lineno: 3,
      level: 0,
    }},
  ],
  exports: {{
    symbols: ['expose_api', 'ExportedClass', 'CONFIG', 'public_helper', 'public_helper'],
    missing: ['MISSING_UTIL'],
    dynamic: false,
    lineno: 2,
  }},
}});

console.log = originalLog;

const summary = record.exportSummary ?? {{}};

console.log(JSON.stringify({{
  declared: summary.declared,
  missing: summary.missing,
  dynamic: summary.dynamic,
  lineno: summary.lineno,
  counts: summary.counts,
  resolved: summary.resolved,
}}));
"""
    payload = _run_node_module(script)

    assert payload["declared"] == [
        "expose_api",
        "ExportedClass",
        "CONFIG",
        "public_helper",
        "MISSING_UTIL",
    ]
    assert payload["missing"] == ["MISSING_UTIL"]
    assert payload["dynamic"] is False
    assert payload["lineno"] == 2

    counts = payload["counts"]
    assert counts["declared"] == 5
    assert counts["functions"] == 1
    assert counts["classes"] == 1
    assert counts["globals"] == 1
    assert counts["reexports"] == 1
    assert counts["missing"] == 1
    assert counts["local"] == 3

    resolved = payload["resolved"]
    kinds = {entry["symbol"]: entry for entry in resolved}

    function_entry = kinds["expose_api"]
    assert function_entry["kind"] == "function"
    assert function_entry["defined"] is True
    assert function_entry["origin"] == "local"
    assert function_entry["functionId"] == "alpha.contracts.api::expose_api"

    class_entry = kinds["ExportedClass"]
    assert class_entry["kind"] == "class"
    assert class_entry["classQualifiedName"] == "alpha.contracts.api.ExportedClass"

    global_entry = kinds["CONFIG"]
    assert global_entry["kind"] == "global"
    assert global_entry["valueKind"] == "dict"

    reexport_entry = kinds["public_helper"]
    assert reexport_entry["kind"] == "reexport"
    assert reexport_entry["origin"] == "reexport"
    assert reexport_entry["sourceModule"] == "alpha.shared.helpers"
    assert reexport_entry["sourceName"] == "helper"
    assert reexport_entry["sourceQualifiedName"] == "alpha.shared.helpers.helper"

    missing_entry = kinds["MISSING_UTIL"]
    assert missing_entry["kind"] == "missing"
    assert missing_entry["defined"] is False
    assert missing_entry["origin"] == "missing"


def test_module_export_summary_handles_dynamic_exports() -> None:
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

const record = __test__.createModuleRecord({{
  module_id: 'alpha.contracts.dynamic',
  path: 'alpha/contracts/dynamic.py',
  relative_path: 'alpha/contracts/dynamic.py',
  exports: {{ symbols: [], dynamic: true }},
}});

console.log = originalLog;

const summary = record.exportSummary ?? {{}};

console.log(JSON.stringify({{
  declared: summary.declared,
  missing: summary.missing,
  dynamic: summary.dynamic,
  counts: summary.counts,
  hasDeclared: summary.hasDeclared,
}}));
"""
    payload = _run_node_module(script)

    assert payload["declared"] == []
    assert payload["missing"] == []
    assert payload["dynamic"] is True
    assert payload["counts"] == {
        "declared": 0,
        "functions": 0,
        "classes": 0,
        "globals": 0,
        "reexports": 0,
        "missing": 0,
        "local": 0,
    }
    assert payload["hasDeclared"] is False
