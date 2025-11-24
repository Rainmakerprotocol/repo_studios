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


def test_create_module_record_exposes_dependency_categories() -> None:
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

const moduleRecord = __test__.createModuleRecord({{
  module_id: 'scripts.consumers.enrich_inventory',
  relative_path: 'scripts/consumers/enrich_inventory.py',
  path: '.repo_studios/scripts/consumers/enrich_inventory.py',
  import_graph: [
    {{
      kind: 'import',
      module: 'scripts.producers',
      lineno: 5,
      edges: [
        {{
          target: 'scripts.producers.generate_inventory',
          imported_as: 'generate_inventory',
          functions: ['enrich_inventory'],
          via: ['generate_inventory'],
          unused: false,
          category: 'internal',
        }},
      ],
    }},
    {{
      kind: 'import',
      module: 'requests',
      lineno: 6,
      edges: [
        {{
          target: 'requests',
          imported_as: 'requests',
          functions: ['enrich_inventory'],
          via: [],
          unused: false,
          category: 'third_party',
        }},
      ],
    }},
    {{
      kind: 'from',
      module: 'json',
      lineno: 7,
      edges: [
        {{
          target: 'json.dumps',
          imported_as: 'dumps',
          functions: [],
          via: [],
          unused: true,
          category: 'standard_library',
        }},
      ],
    }},
    {{
      kind: 'import',
      module: 'custom_unknown',
      lineno: 8,
      edges: [
        {{
          target: 'custom_unknown',
          imported_as: 'custom_unknown',
          functions: [],
          via: [],
          unused: true,
        }},
      ],
    }},
  ],
  dependency_summary: {{
    internal: {{ count: 1, modules: ['scripts.producers.generate_inventory'] }},
    third_party: {{ count: 1, modules: ['requests'] }},
    standard_library: {{ count: 1, modules: ['json'] }},
    unknown: {{ count: 1, modules: ['custom_unknown'] }},
  }},
  functions: [],
}});

console.log = originalLog;

const categoryByTarget = new Map();
for (const edge of moduleRecord.importEdges) {{
  categoryByTarget.set(edge.target, edge.category);
}}

const buckets = new Map();
for (const edge of moduleRecord.importEdges) {{
  if (!buckets.has(edge.category)) {{
    buckets.set(edge.category, new Set());
  }}
  buckets.get(edge.category).add(edge.target);
}}

const serializedBuckets = Array.from(buckets.entries()).reduce((acc, [category, targets]) => {{
  acc[category] = Array.from(targets).sort();
  return acc;
}}, {{}});

console.log(JSON.stringify({{
  categories: Object.fromEntries(categoryByTarget.entries()),
  buckets: serializedBuckets,
  summary: moduleRecord.dependencySummary,
}}));
"""

    payload = _run_node_module(script)

    assert payload["categories"] == {
        "scripts.producers.generate_inventory": "internal",
        "requests": "third_party",
        "json.dumps": "standard_library",
        "custom_unknown": "unknown",
    }
    assert payload["buckets"]["internal"] == ["scripts.producers.generate_inventory"]
    assert payload["buckets"]["third_party"] == ["requests"]
    assert payload["buckets"]["standard_library"] == ["json.dumps"]
    assert payload["buckets"]["unknown"] == ["custom_unknown"]
    assert payload["summary"] == {
        "internal": {"count": 1, "modules": ["scripts.producers.generate_inventory"]},
        "third_party": {"count": 1, "modules": ["requests"]},
        "standard_library": {"count": 1, "modules": ["json"]},
        "unknown": {"count": 1, "modules": ["custom_unknown"]},
    }
