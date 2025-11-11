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


def test_create_module_record_classifies_script_layers() -> None:
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

const producer = __test__.createModuleRecord({{
  module_id: 'scripts.producers.generate_anchor_inventory',
  relative_path: 'scripts/producers/generate_anchor_inventory.py',
  path: '.repo_studios/scripts/producers/generate_anchor_inventory.py',
  import_graph: [],
  functions: [],
}});

const orchestrator = __test__.createModuleRecord({{
  module_id: 'command_center.scripts.orchestrators.run_command_center_pipeline',
  relative_path: 'command_center/scripts/orchestrators/run_command_center_pipeline.py',
  path: '.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py',
  import_graph: [],
  functions: [],
}});

const unknown = __test__.createModuleRecord({{
  module_id: 'docs.automation.generate_docs_index',
  relative_path: 'docs/automation/generate_docs_index.py',
  path: 'docs/automation/generate_docs_index.py',
  import_graph: [],
  functions: [],
}});

console.log = originalLog;

console.log(JSON.stringify({{
  producer: {{ tier: producer.layerTier, label: producer.layerLabel, index: producer.layerIndex }},
  orchestrator: {{ tier: orchestrator.layerTier, label: orchestrator.layerLabel, index: orchestrator.layerIndex }},
  unknown: {{ tier: unknown.layerTier, label: unknown.layerLabel, index: unknown.layerIndex }},
}}));
"""

    payload = _run_node_module(script)

    assert payload["producer"] == {"tier": "producers", "label": "Producers", "index": 0}
    assert payload["orchestrator"] == {"tier": "orchestrators", "label": "Orchestrators", "index": 3}
    assert payload["unknown"] == {"tier": "unclassified", "label": "Unclassified", "index": 99}


def test_evaluate_layer_transition_applies_adjacency_defaults() -> None:
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

const forward = __test__.evaluateLayerTransition('producers', 'consumers');
const peer = __test__.evaluateLayerTransition('aggregators', 'aggregators');
const backward = __test__.evaluateLayerTransition('aggregators', 'producers');
const skip = __test__.evaluateLayerTransition('aggregators', 'summarizers');
const unknown = __test__.evaluateLayerTransition('unclassified', 'consumers');

console.log = originalLog;

console.log(JSON.stringify({{
  forward,
  peer,
  backward,
  skip,
  unknown,
}}));
"""

    payload = _run_node_module(script)

    assert payload["forward"] == {
        "allowed": True,
        "classification": "forward",
        "reason": "Producers feed Consumers with normalized inventories.",
    }
    assert payload["peer"] == {
        "allowed": True,
        "classification": "peer",
        "reason": "Aggregators can compose peer modules for composite analyses.",
    }
    assert payload["backward"] == {
        "allowed": False,
        "classification": "backward",
        "reason": "Aggregators should not depend on downstream execution tiers beyond Orchestrators.",
    }
    assert payload["skip"] == {
        "allowed": False,
        "classification": "skip",
        "reason": "Aggregators must hand off to Orchestrators before Summarizers.",
    }
    assert payload["unknown"] == {
        "allowed": True,
        "classification": "unclassified",
        "reason": "One or both modules are unclassified; defer manual review but do not hard-fail the transition.",
    }


def test_layer_architecture_validation_view_surfaces_violations() -> None:
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

const viewer = await import('{VIEWER_MODULE_PATH.as_uri()}');
const api = viewer.__test__;

api.resetViewStateForTest();

const modules = new Map();
const register = (record) => {{
  if (record) {{
    modules.set(record.id, record);
  }}
}};

register(api.createModuleRecord({{
  module_id: 'scripts.producers.generate_inventory',
  relative_path: 'scripts/producers/generate_inventory.py',
  path: '.repo_studios/scripts/producers/generate_inventory.py',
}}));

register(api.createModuleRecord({{
  module_id: 'scripts.consumers.enrich_inventory',
  relative_path: 'scripts/consumers/enrich_inventory.py',
  path: '.repo_studios/scripts/consumers/enrich_inventory.py',
}}));

register(api.createModuleRecord({{
  module_id: 'scripts.orchestrators.run_pipeline',
  relative_path: 'scripts/orchestrators/run_pipeline.py',
  path: '.repo_studios/scripts/orchestrators/run_pipeline.py',
}}));

register(api.createModuleRecord({{
  module_id: 'scripts.summarizers.publish_summary',
  relative_path: 'scripts/summarizers/publish_summary.py',
  path: '.repo_studios/scripts/summarizers/publish_summary.py',
}}));

register(api.createModuleRecord({{
  module_id: 'docs.automation.generate_docs_index',
  relative_path: 'docs/automation/generate_docs_index.py',
  path: 'docs/automation/generate_docs_index.py',
  import_graph: [{{
    edges: [
      {{ target: 'scripts.producers.generate_inventory', category: 'internal' }},
    ],
  }}],
}}));

register(api.createModuleRecord({{
  module_id: 'scripts.aggregators.aggregate_signal',
  relative_path: 'scripts/aggregators/aggregate_signal.py',
  path: '.repo_studios/scripts/aggregators/aggregate_signal.py',
  import_graph: [{{
    edges: [
      {{ target: 'scripts.orchestrators.run_pipeline', category: 'internal' }},
      {{ target: 'scripts.producers.generate_inventory', category: 'internal' }},
      {{ target: 'scripts.consumers.enrich_inventory', category: 'internal' }},
      {{ target: 'scripts.summarizers.publish_summary', category: 'internal', unused: true }},
    ],
  }}],
  dependency_summary: {{ violations: {{ layers: 'Inventory flagged aggregator layer violations.' }} }},
}}));

const normalized = {{
  modules,
  functions: new Map(),
  callGraph: {{ functions: new Map() }},
  metrics: {{}},
  hierarchy: {{}},
  levels: null,
  screeningHistory: null,
}};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({{ rootId: null, domainId: null, moduleId: null }});

const result = api.buildLayerArchitectureValidationViewDefinitionForTest();

api.resetViewStateForTest();

console.log = originalLog;

console.log(JSON.stringify({{
  definition: result.definition,
  statusMessage: result.statusMessage,
  statusDetails: result.statusDetails,
  stats: result.stats,
}}));
"""

    payload = _run_node_module(script)

    definition = payload["definition"]
    assert isinstance(definition, str)
    assert definition.startswith("graph LR")
    assert "class scripts_aggregators_aggregate_signal layerNodeViolation;" in definition
    assert "scripts_aggregators_aggregate_signal -->|forward| scripts_orchestrators_run_pipeline" in definition
    assert "scripts_aggregators_aggregate_signal --x|backward| scripts_producers_generate_inventory" in definition
    assert "scripts_aggregators_aggregate_signal --x|backward| scripts_consumers_enrich_inventory" in definition
    assert "scripts_aggregators_aggregate_signal --x|skip| scripts_summarizers_publish_summary" in definition

    status = payload["statusMessage"]
    assert "Layer Architecture Validation" in status
    assert "3 violation" in status

    stats = payload["stats"]
    assert stats["violationEdges"] == 3
    assert "docs.automation.generate_docs_index" in stats["unclassifiedModules"]

    details = payload["statusDetails"]
    assert isinstance(details, list) and details
    violations_section = next((entry for entry in details if entry["title"] == "Adjacency Violations"), None)
    assert violations_section is not None
    violation_items = {item["header"]: item for item in violations_section["items"]}
    producer_header = next((header for header in violation_items if header.startswith("scripts.aggregators.aggregate_signal") and "scripts.producers.generate_inventory" in header), None)
    summarizer_header = next((header for header in violation_items if header.startswith("scripts.aggregators.aggregate_signal") and "scripts.summarizers.publish_summary" in header), None)
    assert producer_header is not None
    assert summarizer_header is not None
    assert violation_items[producer_header]["body"] == "Aggregators should not depend on downstream execution tiers beyond Orchestrators."
    assert violation_items[summarizer_header]["body"] == "Aggregators must hand off to Orchestrators before Summarizers."

    warnings_section = next((entry for entry in details if entry["title"] == "Inventory Warnings"), None)
    assert warnings_section is not None
    assert warnings_section["items"][0]["header"] == "scripts.aggregators.aggregate_signal"

    unclassified_section = next((entry for entry in details if entry["title"] == "Unclassified Modules"), None)
    assert unclassified_section is not None
    assert "docs.automation.generate_docs_index" in unclassified_section["items"]


def test_layer_architecture_validation_view_falls_back_to_repository_scope() -> None:
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

const viewer = await import('{VIEWER_MODULE_PATH.as_uri()}');
const api = viewer.__test__;

api.resetViewStateForTest();

const modules = new Map();
const register = (payload) => {{
  const record = api.createModuleRecord(payload);
  if (record) {{
    modules.set(record.id, record);
  }}
}};

register({{
  module_id: 'scripts.producers.generate_inventory',
  relative_path: 'scripts/producers/generate_inventory.py',
  path: '.repo_studios/scripts/producers/generate_inventory.py',
}});

register({{
  module_id: 'scripts.consumers.enrich_inventory',
  relative_path: 'scripts/consumers/enrich_inventory.py',
  path: '.repo_studios/scripts/consumers/enrich_inventory.py',
}});

register({{
  module_id: 'scripts.aggregators.aggregate_signal',
  relative_path: 'scripts/aggregators/aggregate_signal.py',
  path: '.repo_studios/scripts/aggregators/aggregate_signal.py',
}});

register({{
  module_id: 'scripts.orchestrators.run_pipeline',
  relative_path: 'scripts/orchestrators/run_pipeline.py',
  path: '.repo_studios/scripts/orchestrators/run_pipeline.py',
}});

register({{
  module_id: 'scripts.summarizers.publish_summary',
  relative_path: 'scripts/summarizers/publish_summary.py',
  path: '.repo_studios/scripts/summarizers/publish_summary.py',
}});

const normalized = {{
  modules,
  functions: new Map(),
  callGraph: {{ functions: new Map() }},
  metrics: {{}},
  hierarchy: {{}},
  levels: null,
  screeningHistory: null,
}};

api.setNormalizedDataForTest(normalized);
api.setLevelSelectionsForTest({{ rootId: 'unknown.pipeline', domainId: null, moduleId: null }});

const result = api.buildLayerArchitectureValidationViewDefinitionForTest();

api.resetViewStateForTest();

console.log = originalLog;

console.log(JSON.stringify({{
  statusMessage: result.statusMessage,
  statusDetails: result.statusDetails,
}}));
"""

    payload = _run_node_module(script)

    status_details = payload["statusDetails"]
    info_entry = next((entry for entry in status_details if entry["type"] == "info"), None)
    assert info_entry is not None
    assert "unknown.pipeline" in info_entry["description"]
    assert "repository" in info_entry["description"].lower()

    status_message = payload["statusMessage"]
    assert "repository" in status_message.lower()
