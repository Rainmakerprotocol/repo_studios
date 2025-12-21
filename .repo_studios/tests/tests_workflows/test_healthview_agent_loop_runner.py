from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest


def _load_module_from_path(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


def _write_checkbox_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "file_path",
                "line_number",
                "heading_h1",
                "heading_h2",
                "heading_h3",
                "heading_h4",
                "checkbox_text",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def test_runner_selection_prefers_earliest_stage_then_line(tmp_path: Path) -> None:
    repo_root = tmp_path
    csv_path = repo_root / ".repo_studios" / "docs" / "pipeline" / "checkbox_report" / "outputs" / "checkbox_report.csv"
    csv_path.parent.mkdir(parents=True)

    tier1_path = ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md"

    rows = [
        {
            "file_path": tier1_path,
            "line_number": "999",
            "heading_h1": "HealthView Orchestration Pipeline",
            "heading_h2": "10. Stage 7 – Running the Complete Suite",
            "heading_h3": "",
            "heading_h4": "",
            "checkbox_text": "S7 item — pending until Tier-2 DONE is checked. See: [Tier-2 record](tier2_roster/tier2_full_suite_overview_roster.md#s7r-001-meta-orchestrator)",
        },
        {
            "file_path": tier1_path,
            "line_number": "10",
            "heading_h1": "HealthView Orchestration Pipeline",
            "heading_h2": "4. Stage 1 – Testing Perspectives",
            "heading_h3": "4.1 Stage 1.1: Test Execution Telemetry",
            "heading_h4": "",
            "checkbox_text": "Stage 1.1 item — pending until Tier-2 DONE is checked. See: [Tier-2 record](tier2_roster/tier2_test_execution_telemetry_roster.md#record--run_test_execution_telemetrypy)",
        },
    ]
    _write_checkbox_csv(csv_path, rows)

    spec = {
        "version": "1.0",
        "name": "HealthView Agent Execution Loop",
        "scope": {
            "root_docs": [".repo_studios/docs/pipeline/healthview_orchestration_pipeline/"],
            "tier1_entry": tier1_path,
            "allowed_actions": ["read_docs"],
        },
        "inputs": {
            "checkbox_report_csv": ".repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv",
            "tier1_gate_files": [tier1_path],
            "doc_index_command": ["make", "-C", ".repo_studios", "doc-index"],
        },
        "selection": {
            "source": "checkbox_report_csv",
            "strict_stage_order": True,
            "filters": {"tier": "tier-1", "require_tier2_link": True, "exclude_placeholders": True},
            "kind_priority": ["tier1_script_pending", "tier1_stop_gate", "other"],
        },
        "mapping": {
            "extract_tier2_link_from_checkbox_text": True,
            "require_link_anchor": True,
            "prefer_link_path_prefixes": ["tier2_roster/"],
        },
    }

    runner_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "orchestrators"
        / "healthview"
        / "run_healthview_agent_loop.py"
    )
    runner = _load_module_from_path(
        "repo_studios.scripts.orchestrators.healthview.run_healthview_agent_loop",
        runner_path,
    )

    candidate = runner.select_next_candidate(spec, repo_root=repo_root)
    assert candidate.stage.label == "1.1"
    assert candidate.line_number == 10


def test_runner_filters_placeholders(tmp_path: Path) -> None:
    repo_root = tmp_path
    csv_path = repo_root / ".repo_studios" / "docs" / "pipeline" / "checkbox_report" / "outputs" / "checkbox_report.csv"
    csv_path.parent.mkdir(parents=True)

    tier1_path = ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md"
    rows = [
        {
            "file_path": tier1_path,
            "line_number": "1",
            "heading_h1": "HealthView Orchestration Pipeline",
            "heading_h2": "9. Stage 6 – Process Governance",
            "heading_h3": "9.1 Stage 6.1: Standards Integrity",
            "heading_h4": "",
            "checkbox_text": "<script>.py — pending until Tier-2 DONE is checked. See: <Tier-2 roster record anchor>",
        }
    ]
    _write_checkbox_csv(csv_path, rows)

    spec = {
        "version": "1.0",
        "name": "HealthView Agent Execution Loop",
        "inputs": {
            "checkbox_report_csv": ".repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv",
            "tier1_gate_files": [tier1_path],
            "doc_index_command": ["make", "-C", ".repo_studios", "doc-index"],
        },
        "selection": {
            "source": "checkbox_report_csv",
            "strict_stage_order": True,
            "filters": {"tier": "tier-1", "require_tier2_link": True, "exclude_placeholders": True},
            "kind_priority": ["tier1_script_pending", "tier1_stop_gate", "other"],
        },
        "mapping": {
            "prefer_link_path_prefixes": ["tier2_roster/"],
            "require_link_anchor": True,
        },
    }

    runner_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "orchestrators"
        / "healthview"
        / "run_healthview_agent_loop.py"
    )
    runner = _load_module_from_path(
        "repo_studios.scripts.orchestrators.healthview.run_healthview_agent_loop",
        runner_path,
    )

    with pytest.raises(RuntimeError, match="No Tier-1 checkbox candidates"):
        runner.select_next_candidate(spec, repo_root=repo_root)


def test_anchor_extraction_matches_existing_roster_links(tmp_path: Path) -> None:
    runner_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "orchestrators"
        / "healthview"
        / "run_healthview_agent_loop.py"
    )
    runner = _load_module_from_path(
        "repo_studios.scripts.orchestrators.healthview.run_healthview_agent_loop",
        runner_path,
    )

    markdown = """
#### Record — collect_test_log_reports.py

Some text.
"""
    anchors = runner._extract_markdown_anchors(markdown)
    assert "record--collect_test_log_reportspy" in anchors
