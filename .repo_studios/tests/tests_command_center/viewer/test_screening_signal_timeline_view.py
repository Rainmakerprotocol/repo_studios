from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_STUDIOS_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_STUDIOS_ROOT / "command_center" / "viewer" / "ui" / "builders" / "screening_signal_timeline.js"

if not MODULE_PATH.exists():  # pragma: no cover - guard against missing assets
    raise AssertionError(f"Expected viewer timeline module at {MODULE_PATH}")


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
        # Surface stderr to help diagnose failing scripts while keeping return clean.
        pytest.fail(f"Node.js script wrote to stderr: {result.stderr}")
    return json.loads(result.stdout.strip())


def test_screening_timeline_returns_message_when_history_missing() -> None:
    history = {"events": []}
    script = f"""
import {{ buildScreeningTimelineDiagram }} from "{MODULE_PATH.as_uri()}";
const history = {json.dumps(history)};
const result = buildScreeningTimelineDiagram(history);
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    assert "message" in payload
    assert payload["message"].startswith("No screening history events")


def test_screening_timeline_renders_mermaid_definition() -> None:
    history = {
        "events": [
            {
                "timestamp": "2025-11-08T10:00:00Z",
                "packId": "docstring_coverage",
                "packLabel": "Docstring Coverage",
                "severity": "critical",
                "score": 0.0,
                "thresholds": {"warning": 80, "failure": 60},
                "metrics": {
                    "functions_total": 10,
                    "functions_documented": 2,
                },
                "context": {
                    "folder_name": "repo-studios",
                    "inventory_generated_at": "2025-11-08T09:55:00Z",
                },
            },
            {
                "timestamp": "2025-11-08T14:00:00Z",
                "packId": "docstring_coverage",
                "packLabel": "Docstring Coverage",
                "severity": "ok",
                "score": 95.0,
                "thresholds": {"warning": 80, "failure": 60},
                "metrics": {
                    "functions_total": 10,
                    "functions_documented": 9,
                },
                "context": {
                    "folder_name": "repo-studios",
                    "inventory_generated_at": "2025-11-08T13:55:00Z",
                },
            },
        ]
    }

    script = f"""
import {{ buildScreeningTimelineDiagram }} from "{MODULE_PATH.as_uri()}";
const history = {json.dumps(history)};
const result = buildScreeningTimelineDiagram(history, {{ artifactLabel: "Example Artifact" }});
console.log(JSON.stringify(result));
"""
    payload = _run_node_module(script)

    definition = payload.get("definition")
    assert isinstance(definition, str)
    assert definition.startswith("timeline\n  title Example Artifact Screening Scores")
    assert "section Docstring Coverage" in definition
    assert "[CRITICAL]" in definition
    assert "delta +95" in definition or "delta +95.0" in definition

    status_message = payload.get("statusMessage")
    assert isinstance(status_message, str)
    assert "Rendered screening timeline" in status_message
    assert "2 events" in status_message


def test_screening_timeline_definition_is_stable_across_repeated_calls() -> None:
    history = {
        "events": [
            {
                "timestamp": "2025-11-08T20:00:00Z",
                "packId": "docstring_coverage",
                "packLabel": "Docstring Coverage",
                "severity": "warning",
                "score": 70.0,
                "thresholds": {"warning": 80, "failure": 60},
                "metrics": {
                    "functions_total": 10,
                    "functions_documented": 7,
                },
                "context": {
                    "folder_name": "repo-studios",
                    "inventory_generated_at": "2025-11-08T19:55:00Z",
                },
            },
            {
                "timestamp": "2025-11-08T10:00:00Z",
                "packId": "docstring_coverage",
                "packLabel": "Docstring Coverage",
                "severity": "critical",
                "score": 40.0,
                "thresholds": {"warning": 80, "failure": 60},
                "metrics": {
                    "functions_total": 10,
                    "functions_documented": 4,
                },
                "context": {
                    "folder_name": "repo-studios",
                    "inventory_generated_at": "2025-11-08T09:55:00Z",
                },
            },
        ]
    }

    script = f"""
import {{ buildScreeningTimelineDiagram }} from "{MODULE_PATH.as_uri()}";
const history = {json.dumps(history)};
const first = buildScreeningTimelineDiagram(history, {{ artifactLabel: "Example Artifact" }});
const second = buildScreeningTimelineDiagram(history, {{ artifactLabel: "Example Artifact" }});
console.log(JSON.stringify({{
  firstDefinition: first.definition,
  secondDefinition: second.definition,
  firstStatus: first.statusMessage,
  secondStatus: second.statusMessage,
  firstEventCount: first.eventCount,
  secondEventCount: second.eventCount,
  historyEvents: history.events.map(event => event.timestamp)
}}));
"""
    payload = _run_node_module(script)

    assert payload["firstDefinition"] == payload["secondDefinition"]
    assert payload["firstStatus"] == payload["secondStatus"]
    assert payload["firstEventCount"] == payload["secondEventCount"]
    # Ensure the underlying history array order remains intact after repeated renders
    assert payload["historyEvents"] == [
        "2025-11-08T20:00:00Z",
        "2025-11-08T10:00:00Z",
    ]
