from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
GLOBAL_USAGE_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "global_variable_usage_map.js"
)
IO_EFFECTS_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "io_effects_diagram.js"
)
EXCEPTION_FLOW_MODULE_PATH = (
    REPO_STUDIOS_ROOT
    / "command_center"
    / "viewer"
    / "ui"
    / "builders"
    / "exception_flow_map.js"
)

if not GLOBAL_USAGE_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected global variable usage builder at {GLOBAL_USAGE_MODULE_PATH}")

if not IO_EFFECTS_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected IO effects builder at {IO_EFFECTS_MODULE_PATH}")

if not EXCEPTION_FLOW_MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected exception flow builder at {EXCEPTION_FLOW_MODULE_PATH}")


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


def test_global_variable_usage_map_coexists_with_io_effects_diagram() -> None:
    script = f"""
import {{ buildGlobalVariableUsageMapDiagram }} from "{GLOBAL_USAGE_MODULE_PATH.as_uri()}";
import {{ buildIoEffectsDiagram }} from "{IO_EFFECTS_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.state", {{
    moduleId: "alpha.state",
    globals: [
      {{ name: "SETTINGS", valueKind: "dict", lineno: 5 }},
      {{ name: "FLAG", valueKind: "bool", lineno: 12 }},
    ],
    functions: [
      "alpha.state::configure",
      "alpha.state::persist",
    ],
  }}],
  ["beta.runtime", {{
    moduleId: "beta.runtime",
    globals: [
      {{ name: "MAX_RETRIES", valueKind: "int", lineno: 9 }},
    ],
    functions: [
      "beta.runtime::bootstrap",
    ],
  }}],
]);

const functions = new Map([
  ["alpha.state::configure", {{
    id: "alpha.state::configure",
    moduleId: "alpha.state",
    name: "configure",
    usedGlobals: ["SETTINGS"],
    ioEffects: {{
      reads: true,
      writes: false,
      env: true,
      network: false,
      hasEffects: true,
      activeFlags: ["reads", "env"],
      flagCount: 2,
    }},
    raisedExceptions: [
      {{ type: "ValueError", message: "invalid setting", qualifiedName: "ValueError", lineno: 18 }},
    ],
  }}],
  ["alpha.state::persist", {{
    id: "alpha.state::persist",
    moduleId: "alpha.state",
    name: "persist",
    usedGlobals: ["SETTINGS", "FLAG"],
    ioEffects: {{
      reads: false,
      writes: true,
      env: false,
      network: false,
      hasEffects: true,
      activeFlags: ["writes"],
      flagCount: 1,
    }},
    raisedExceptions: [
      {{ type: "IOError", message: "write failed", qualifiedName: "IOError", lineno: 42 }},
    ],
  }}],
  ["beta.runtime::bootstrap", {{
    id: "beta.runtime::bootstrap",
    moduleId: "beta.runtime",
    name: "bootstrap",
    usedGlobals: ["MAX_RETRIES"],
    ioEffects: {{
      reads: false,
      writes: false,
      env: false,
      network: true,
      hasEffects: true,
      activeFlags: ["network"],
      flagCount: 1,
    }},
    raisedExceptions: [
      {{ type: "RuntimeError", message: "startup failed", qualifiedName: "RuntimeError", lineno: 7 }},
    ],
  }}],
]);

const globalFirst = buildGlobalVariableUsageMapDiagram(modules, functions, {{ scopeDescription: "repository" }});
const ioFirst = buildIoEffectsDiagram(modules, functions, {{ scopeDescription: "repository" }});
const globalSecond = buildGlobalVariableUsageMapDiagram(modules, functions, {{ scopeDescription: "repository" }});
const ioSecond = buildIoEffectsDiagram(modules, functions, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  globalDefinitionStable: globalFirst.definition === globalSecond.definition,
  globalStatusStable: globalFirst.statusMessage === globalSecond.statusMessage,
  ioDefinitionStable: ioFirst.definition === ioSecond.definition,
  ioStatusStable: ioFirst.statusMessage === ioSecond.statusMessage,
  globalStatus: globalFirst.statusMessage,
  ioStatus: ioFirst.statusMessage,
  globalStats: globalFirst.stats,
  ioStats: ioFirst.stats,
}}));
"""

    payload = _run_node_module(script)

    assert payload["globalDefinitionStable"] is True
    assert payload["globalStatusStable"] is True
    assert payload["ioDefinitionStable"] is True
    assert payload["ioStatusStable"] is True

    assert payload["globalStatus"] == (
        "Rendered Global Variable Usage Map for repository (2 modules, 3 globals, 3 functions, 4 references)."
    )
    assert payload["ioStatus"] == "Rendered IO Effects Diagram for repository (2 modules, 3 functions, 4 effect flags)."

    global_stats = payload["globalStats"]
    assert global_stats["modules"] == 2
    assert global_stats["usageCount"] == 4

    io_stats = payload["ioStats"]
    assert io_stats["modules"] == 2
    assert io_stats["effectFlags"] == 4


def test_exception_flow_map_coexists_with_global_variable_usage_map() -> None:
    script = f"""
import {{ buildExceptionFlowMapDiagram }} from "{EXCEPTION_FLOW_MODULE_PATH.as_uri()}";
import {{ buildGlobalVariableUsageMapDiagram }} from "{GLOBAL_USAGE_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.state", {{
    moduleId: "alpha.state",
    globals: [
      {{ name: "SETTINGS", valueKind: "dict", lineno: 5 }},
      {{ name: "FLAG", valueKind: "bool", lineno: 12 }},
    ],
    functions: [
      "alpha.state::configure",
      "alpha.state::persist",
    ],
  }}],
  ["beta.runtime", {{
    moduleId: "beta.runtime",
    globals: [
      {{ name: "MAX_RETRIES", valueKind: "int", lineno: 9 }},
    ],
    functions: [
      "beta.runtime::bootstrap",
    ],
  }}],
]);

const functions = new Map([
  ["alpha.state::configure", {{
    id: "alpha.state::configure",
    moduleId: "alpha.state",
    name: "configure",
    usedGlobals: ["SETTINGS"],
    ioEffects: {{
      reads: true,
      writes: false,
      env: true,
      network: false,
      hasEffects: true,
      activeFlags: ["reads", "env"],
      flagCount: 2,
    }},
    raisedExceptions: [
      {{ type: "ValueError", message: "invalid setting", qualifiedName: "ValueError", lineno: 18 }},
    ],
  }}],
  ["alpha.state::persist", {{
    id: "alpha.state::persist",
    moduleId: "alpha.state",
    name: "persist",
    usedGlobals: ["SETTINGS", "FLAG"],
    ioEffects: {{
      reads: false,
      writes: true,
      env: false,
      network: false,
      hasEffects: true,
      activeFlags: ["writes"],
      flagCount: 1,
    }},
    raisedExceptions: [
      {{ type: "IOError", message: "write failed", qualifiedName: "IOError", lineno: 42 }},
    ],
  }}],
  ["beta.runtime::bootstrap", {{
    id: "beta.runtime::bootstrap",
    moduleId: "beta.runtime",
    name: "bootstrap",
    usedGlobals: ["MAX_RETRIES"],
    ioEffects: {{
      reads: false,
      writes: false,
      env: false,
      network: true,
      hasEffects: true,
      activeFlags: ["network"],
      flagCount: 1,
    }},
    raisedExceptions: [
      {{ type: "RuntimeError", message: "startup failed", qualifiedName: "RuntimeError", lineno: 7 }},
    ],
  }}],
]);

const exceptionFirst = buildExceptionFlowMapDiagram(modules, functions, {{ scopeDescription: "repository" }});
const globalFirst = buildGlobalVariableUsageMapDiagram(modules, functions, {{ scopeDescription: "repository" }});
const exceptionSecond = buildExceptionFlowMapDiagram(modules, functions, {{ scopeDescription: "repository" }});
const globalSecond = buildGlobalVariableUsageMapDiagram(modules, functions, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  exceptionDefinitionStable: exceptionFirst.definition === exceptionSecond.definition,
  exceptionStatusStable: exceptionFirst.statusMessage === exceptionSecond.statusMessage,
  globalDefinitionStable: globalFirst.definition === globalSecond.definition,
  globalStatusStable: globalFirst.statusMessage === globalSecond.statusMessage,
  exceptionStatus: exceptionFirst.statusMessage,
  exceptionStats: exceptionFirst.stats,
}}));
"""

    payload = _run_node_module(script)

    assert payload["exceptionDefinitionStable"] is True
    assert payload["exceptionStatusStable"] is True
    assert payload["globalDefinitionStable"] is True
    assert payload["globalStatusStable"] is True

    assert payload["exceptionStatus"] == (
        "Rendered Exception Flow Map for repository (2 modules, 3 functions, 3 exceptions, 3 raise events)."
    )

    exception_stats = payload["exceptionStats"]
    assert exception_stats["modules"] == 2
    assert exception_stats["exceptions"] == 3
    assert exception_stats["raiseEvents"] == 3


def test_exception_flow_map_coexists_with_io_effects_diagram() -> None:
    script = f"""
import {{ buildExceptionFlowMapDiagram }} from "{EXCEPTION_FLOW_MODULE_PATH.as_uri()}";
import {{ buildIoEffectsDiagram }} from "{IO_EFFECTS_MODULE_PATH.as_uri()}";

const modules = new Map([
  ["alpha.state", {{
    moduleId: "alpha.state",
    globals: [
      {{ name: "SETTINGS", valueKind: "dict", lineno: 5 }},
      {{ name: "FLAG", valueKind: "bool", lineno: 12 }},
    ],
    functions: [
      "alpha.state::configure",
      "alpha.state::persist",
    ],
  }}],
  ["beta.runtime", {{
    moduleId: "beta.runtime",
    globals: [
      {{ name: "MAX_RETRIES", valueKind: "int", lineno: 9 }},
    ],
    functions: [
      "beta.runtime::bootstrap",
    ],
  }}],
]);

const functions = new Map([
  ["alpha.state::configure", {{
    id: "alpha.state::configure",
    moduleId: "alpha.state",
    name: "configure",
    usedGlobals: ["SETTINGS"],
    ioEffects: {{
      reads: true,
      writes: false,
      env: true,
      network: false,
      hasEffects: true,
      activeFlags: ["reads", "env"],
      flagCount: 2,
    }},
    raisedExceptions: [
      {{ type: "ValueError", message: "invalid setting", qualifiedName: "ValueError", lineno: 18 }},
    ],
  }}],
  ["alpha.state::persist", {{
    id: "alpha.state::persist",
    moduleId: "alpha.state",
    name: "persist",
    usedGlobals: ["SETTINGS", "FLAG"],
    ioEffects: {{
      reads: false,
      writes: true,
      env: false,
      network: false,
      hasEffects: true,
      activeFlags: ["writes"],
      flagCount: 1,
    }},
    raisedExceptions: [
      {{ type: "IOError", message: "write failed", qualifiedName: "IOError", lineno: 42 }},
    ],
  }}],
  ["beta.runtime::bootstrap", {{
    id: "beta.runtime::bootstrap",
    moduleId: "beta.runtime",
    name: "bootstrap",
    usedGlobals: ["MAX_RETRIES"],
    ioEffects: {{
      reads: false,
      writes: false,
      env: false,
      network: true,
      hasEffects: true,
      activeFlags: ["network"],
      flagCount: 1,
    }},
    raisedExceptions: [
      {{ type: "RuntimeError", message: "startup failed", qualifiedName: "RuntimeError", lineno: 7 }},
    ],
  }}],
]);

const exceptionFirst = buildExceptionFlowMapDiagram(modules, functions, {{ scopeDescription: "repository" }});
const ioFirst = buildIoEffectsDiagram(modules, functions, {{ scopeDescription: "repository" }});
const exceptionSecond = buildExceptionFlowMapDiagram(modules, functions, {{ scopeDescription: "repository" }});
const ioSecond = buildIoEffectsDiagram(modules, functions, {{ scopeDescription: "repository" }});

console.log(JSON.stringify({{
  exceptionDefinitionStable: exceptionFirst.definition === exceptionSecond.definition,
  exceptionStatusStable: exceptionFirst.statusMessage === exceptionSecond.statusMessage,
  ioDefinitionStable: ioFirst.definition === ioSecond.definition,
  ioStatusStable: ioFirst.statusMessage === ioSecond.statusMessage,
  ioStatus: ioFirst.statusMessage,
}}));
"""

    payload = _run_node_module(script)

    assert payload["exceptionDefinitionStable"] is True
    assert payload["exceptionStatusStable"] is True
    assert payload["ioDefinitionStable"] is True
    assert payload["ioStatusStable"] is True
    assert payload["ioStatus"] == "Rendered IO Effects Diagram for repository (2 modules, 3 functions, 4 effect flags)."