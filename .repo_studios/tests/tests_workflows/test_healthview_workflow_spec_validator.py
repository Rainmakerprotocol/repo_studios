from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml


def _load_module_from_path(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


def test_workflow_spec_validator_accepts_minimal_valid_spec(tmp_path: Path) -> None:
    validator_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "utilities"
        / "validate_healthview_agent_workflow_spec.py"
    )
    validator = _load_module_from_path(
        "repo_studios.scripts.utilities.validate_healthview_agent_workflow_spec",
        validator_path,
    )

    schema_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "pipeline"
        / "healthview_orchestration_pipeline"
        / "workflows"
        / "schema"
        / "healthview_agent_execution_loop.schema.json"
    )

    spec_path = tmp_path / "spec.yaml"
    spec = {
        "version": "1.0",
        "name": "HealthView Agent Execution Loop",
        "scope": {"root_docs": [".repo_studios/docs/pipeline"], "tier1_entry": "x", "allowed_actions": ["read_docs"]},
        "inputs": {
            "checkbox_report_csv": ".repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv",
            "tier1_gate_files": [".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md"],
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
        "constraints": {
            "one_checkbox_at_a_time": True,
            "do_not_check_tier1_until_tier2_done": True,
            "no_work_outside_checkbox_flow": True,
            "no_tier3_before_stop_gates_closed": True,
        },
        "approval_gates": {"require_user_approval_for": ["begin_implementation"]},
        "workflow": {"step_0_select_work": {}},
        "post_iteration": {
            "run_doc_index": True,
            "doc_index_command_source": "inputs.doc_index_command",
            "expected_outputs": [".repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv"],
        },
        "deliverable_each_iteration": ["tier2_record_anchor"],
        "stop_conditions": ["no_remaining_checkboxes"],
    }
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")

    result = validator.validate_workflow_spec(spec_path, schema_path)
    assert result.ok


def test_workflow_spec_validator_rejects_wrong_version(tmp_path: Path) -> None:
    validator_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "utilities"
        / "validate_healthview_agent_workflow_spec.py"
    )
    validator = _load_module_from_path(
        "repo_studios.scripts.utilities.validate_healthview_agent_workflow_spec",
        validator_path,
    )

    schema_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "pipeline"
        / "healthview_orchestration_pipeline"
        / "workflows"
        / "schema"
        / "healthview_agent_execution_loop.schema.json"
    )

    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "version": "2.0",
                "name": "x",
                "scope": {"root_docs": ["x"], "tier1_entry": "x", "allowed_actions": ["x"]},
                "inputs": {"checkbox_report_csv": "x", "tier1_gate_files": ["x"], "doc_index_command": ["x"]},
                "selection": {
                    "source": "checkbox_report_csv",
                    "strict_stage_order": True,
                    "filters": {"tier": "tier-1", "require_tier2_link": True, "exclude_placeholders": True},
                    "kind_priority": ["other"],
                },
                "mapping": {
                    "extract_tier2_link_from_checkbox_text": True,
                    "require_link_anchor": True,
                    "prefer_link_path_prefixes": ["tier2_roster/"],
                },
                "constraints": {
                    "one_checkbox_at_a_time": True,
                    "do_not_check_tier1_until_tier2_done": True,
                    "no_work_outside_checkbox_flow": True,
                    "no_tier3_before_stop_gates_closed": True,
                },
                "approval_gates": {"require_user_approval_for": ["x"]},
                "workflow": {"x": {}},
                "post_iteration": {"run_doc_index": True, "doc_index_command_source": "x", "expected_outputs": ["x"]},
                "deliverable_each_iteration": ["x"],
                "stop_conditions": ["x"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = validator.validate_workflow_spec(spec_path, schema_path)
    assert not result.ok
    assert any('version must be "1.0"' in err for err in result.errors)
