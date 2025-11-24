from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
VIEWER_MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "viewer.js"

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


def test_create_module_record_collects_import_edges() -> None:
    script = f"""
import path from 'path';

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
  module_id: 'alpha.utils.formatters',
  path: 'alpha/utils/formatters.py',
  functions: [],
  import_graph: [
    {{
      kind: 'import',
      module: null,
      lineno: 3,
      edges: [
        {{ target: 'os', category: 'standard_library', unused: false, functions: ['alpha.utils.formatters::slugify'], via: [] }},
        {{ target: 'alpha.utils.serializers', category: 'internal', unused: true, functions: [], via: ['serializers'] }},
      ],
    }},
    {{
      kind: 'from',
      module: 'alpha.utils.decorators',
      lineno: 5,
      edges: [
        {{ target: 'alpha.utils.decorators.audit', category: 'internal', unused: false, functions: ['alpha.utils.formatters::slugify', 'alpha.utils.formatters::render'], via: ['audit'] }},
        {{ target: 'alpha.vendor.requests', category: 'third_party', unused: false, functions: [], via: ['requests'] }},
        null,
      ],
    }},
  ],
}});

console.log = originalLog;

console.log(JSON.stringify({{
  moduleId: record.moduleId,
  importEdges: record.importEdges,
}}));
"""
    payload = _run_node_module(script)

    assert payload["moduleId"] == "alpha.utils.formatters"
    edges = payload["importEdges"]
    assert isinstance(edges, list)

    # Ensure internal targets were captured with metadata.
    internal = [edge for edge in edges if edge["category"] == "internal"]
    assert len(internal) == 2
    targets = {edge["target"] for edge in internal}
    assert targets == {"alpha.utils.serializers", "alpha.utils.decorators.audit"}
    audit_edge = next(edge for edge in internal if edge["target"] == "alpha.utils.decorators.audit")
    assert audit_edge["unused"] is False
    assert sorted(audit_edge["functions"]) == [
        "alpha.utils.formatters::render",
        "alpha.utils.formatters::slugify",
    ]

    # External dependencies should remain with their categories and trimmed aliases.
    external = [edge for edge in edges if edge["category"] == "third_party"]
    assert external and external[0]["importedAs"] == "requests"

    stdlib = [edge for edge in edges if edge["category"] == "standard_library"]
    assert stdlib and stdlib[0]["target"] == "os"
