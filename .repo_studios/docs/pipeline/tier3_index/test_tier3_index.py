#!/usr/bin/env python3
"""
Tests for generate_tier3_index.py

Validates tier3 index generation, YAML parsing, validation, and aggregation.
"""

import copy
import logging
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from generate_tier3_index import (
    REQUIRED_TIER3_KEYS,
    VALID_CATEGORIES,
    VALID_STATUSES,
    create_index_entry,
    find_tier3_files,
    generate_index,
    load_tier3_yaml,
    run,
    validate_tier3_yaml,
)


# Sample valid tier3 YAML
VALID_TIER3 = {
    "tool": {
        "id": "test_script",
        "name": "Test Script",
        "description": "A test script for validation",
        "keywords": ["test", "validation"]
    },
    "invocation": {
        "command_template": "python {script_path} --arg {value}",
        "script_path": ".repo_studios/scripts/test_script.py",
        "importable": True,
        "entry_function": "run"
    },
    "parameters": [
        {
            "name": "value",
            "type": "string",
            "required": True,
            "description": "Test value"
        }
    ],
    "outputs": {
        "primary": {
            "type": "file",
            "format": "json",
            "path_pattern": "outputs/result.json"
        }
    },
    "behavior": {
        "idempotent": True,
        "side_effects": ["writes file"],
        "duration_estimate": "< 1 second"
    },
    "metadata": {
        "category": "utility",
        "status": "active",
        "version": "1.0.0"
    }
}


@pytest.fixture
def temp_pipeline_dir(tmp_path):
    """Create temporary pipeline directory structure."""
    pipeline_dir = tmp_path / ".repo_studios" / "docs" / "pipeline"
    pipeline_dir.mkdir(parents=True)
    return pipeline_dir


@pytest.fixture
def logger():
    """Create logger for tests."""
    logging.basicConfig(level=logging.DEBUG, force=True)
    return logging.getLogger(__name__)


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Helper to write YAML file."""
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)


class TestFindTier3Files:
    """Test tier3 file discovery."""
    
    def test_find_no_files(self, temp_pipeline_dir, logger):
        """Should return empty list when no tier3 files exist."""
        files = find_tier3_files(temp_pipeline_dir, logger)
        assert files == []
    
    def test_find_single_file(self, temp_pipeline_dir, logger):
        """Should find single tier3_*.yaml file."""
        tier3_file = temp_pipeline_dir / "tier3_test.yaml"
        tier3_file.touch()
        
        files = find_tier3_files(temp_pipeline_dir, logger)
        assert len(files) == 1
        assert files[0].name == "tier3_test.yaml"
    
    def test_find_multiple_files(self, temp_pipeline_dir, logger):
        """Should find all tier3_*.yaml files and sort them."""
        (temp_pipeline_dir / "tier3_alpha.yaml").touch()
        (temp_pipeline_dir / "tier3_beta.yaml").touch()
        (temp_pipeline_dir / "tier3_gamma.yaml").touch()
        
        files = find_tier3_files(temp_pipeline_dir, logger)
        assert len(files) == 3
        assert [f.name for f in files] == [
            "tier3_alpha.yaml",
            "tier3_beta.yaml",
            "tier3_gamma.yaml"
        ]
    
    def test_ignore_non_tier3_files(self, temp_pipeline_dir, logger):
        """Should ignore files not matching tier3_*.yaml pattern."""
        (temp_pipeline_dir / "tier3_valid.yaml").touch()
        (temp_pipeline_dir / "README.md").touch()
        (temp_pipeline_dir / "config.yaml").touch()
        (temp_pipeline_dir / "tier2_pipeline.yaml").touch()
        
        files = find_tier3_files(temp_pipeline_dir, logger)
        assert len(files) == 1
        assert files[0].name == "tier3_valid.yaml"
    
    def test_include_subdirectories(self, temp_pipeline_dir, logger):
        """Should discover tier3 files in subdirectories."""
        (temp_pipeline_dir / "tier3_root.yaml").touch()

        subdir = temp_pipeline_dir / "subdir"
        subdir.mkdir()
        (subdir / "tier3_nested.yaml").touch()

        files = find_tier3_files(temp_pipeline_dir, logger)
        assert len(files) == 2
        assert [str(f.relative_to(temp_pipeline_dir)).replace('\\', '/') for f in files] == [
            "tier3_root.yaml",
            "subdir/tier3_nested.yaml",
        ]

    def test_exclude_outputs_and_reports_dirs(self, temp_pipeline_dir, logger):
        """Should ignore tier3 files under outputs/ and reports/ directories."""
        (temp_pipeline_dir / "tier3_root.yaml").touch()

        outputs_dir = temp_pipeline_dir / "some_tool" / "outputs"
        outputs_dir.mkdir(parents=True)
        (outputs_dir / "tier3_in_outputs.yaml").touch()

        reports_dir = temp_pipeline_dir / "other" / "reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "tier3_in_reports.yaml").touch()

        files = find_tier3_files(temp_pipeline_dir, logger)
        assert [str(f.relative_to(temp_pipeline_dir)).replace('\\', '/') for f in files] == [
            "tier3_root.yaml"
        ]

    def test_exclude_pipeline_templates_and_tier3_index_dirs(self, temp_pipeline_dir, logger):
        """Should ignore internal template and index directories."""
        (temp_pipeline_dir / "tier3_root.yaml").touch()

        templates_dir = temp_pipeline_dir / "pipeline_templates"
        templates_dir.mkdir()
        (templates_dir / "tier3_template.yaml").touch()

        index_dir = temp_pipeline_dir / "tier3_index"
        index_dir.mkdir()
        (index_dir / "tier3_internal.yaml").touch()

        files = find_tier3_files(temp_pipeline_dir, logger)
        assert [str(f.relative_to(temp_pipeline_dir)).replace('\\', '/') for f in files] == [
            "tier3_root.yaml"
        ]


class TestHorizontalTier3Contracts:
    def test_horizontal_contracts_are_ignored_by_generator(self, temp_pipeline_dir, logger):
        """Horizontal Tier-3 contracts should not be indexed as tool specs."""
        horizontal = temp_pipeline_dir / "tier3_horizontal_contract.yaml"
        write_yaml(
            horizontal,
            {
                "metadata": {
                    "tier": 3,
                    "kind": "horizontal",
                    "id": "contract",
                    "status": "draft",
                    "version": "0.1.0",
                }
            },
        )

        files = find_tier3_files(temp_pipeline_dir, logger)
        assert [f.name for f in files] == ["tier3_horizontal_contract.yaml"]

        index = generate_index(files, temp_pipeline_dir, validate=True, log=logger)
        assert index["statistics"]["total_scripts"] == 0
        assert "validation" not in index


class TestValidateTier3Yaml:
    """Test tier3 YAML validation."""
    
    def test_valid_yaml(self, temp_pipeline_dir, logger):
        """Should pass validation for valid YAML."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        errors = validate_tier3_yaml(yaml_path, VALID_TIER3, logger)
        assert errors == []
    
    def test_missing_required_keys(self, temp_pipeline_dir, logger):
        """Should detect missing required top-level keys."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        incomplete = {"tool": {"id": "test"}}
        
        errors = validate_tier3_yaml(yaml_path, incomplete, logger)
        
        # Should have errors for each missing key
        missing_keys = set(REQUIRED_TIER3_KEYS) - {"tool"}
        assert len(errors) >= len(missing_keys)
        assert any("Missing required section" in e for e in errors)
    
    def test_invalid_tool_section(self, temp_pipeline_dir, logger):
        """Should detect invalid tool section."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        
        # Test non-dict tool
        data = copy.deepcopy(VALID_TIER3)
        data["tool"] = "not a dict"
        errors = validate_tier3_yaml(yaml_path, data, logger)
        assert any("'tool' must be a dictionary" in e for e in errors)
        
        # Test missing tool.id
        data = copy.deepcopy(VALID_TIER3)
        data["tool"] = {"name": "Test"}
        errors = validate_tier3_yaml(yaml_path, data, logger)
        assert any("'tool.id' is required" in e for e in errors)
    
    def test_invalid_category(self, temp_pipeline_dir, logger):
        """Should detect invalid metadata.category."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        data = copy.deepcopy(VALID_TIER3)
        data["metadata"]["category"] = "invalid_category"
        
        errors = validate_tier3_yaml(yaml_path, data, logger)
        assert any("metadata.category" in e and "invalid_category" in e for e in errors)
    
    def test_invalid_status(self, temp_pipeline_dir, logger):
        """Should detect invalid metadata.status."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        data = copy.deepcopy(VALID_TIER3)
        data["metadata"]["status"] = "invalid_status"
        
        errors = validate_tier3_yaml(yaml_path, data, logger)
        assert any("metadata.status" in e and "invalid_status" in e for e in errors)
    
    def test_missing_metadata_fields(self, temp_pipeline_dir, logger):
        """Should detect missing category and status."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        data = copy.deepcopy(VALID_TIER3)
        data["metadata"] = {}
        
        errors = validate_tier3_yaml(yaml_path, data, logger)
        assert any("'metadata.category' is required" in e for e in errors)
        assert any("'metadata.status' is required" in e for e in errors)


class TestLoadTier3Yaml:
    """Test YAML loading."""
    
    def test_load_valid_yaml(self, temp_pipeline_dir, logger):
        """Should successfully load valid YAML."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        write_yaml(yaml_path, VALID_TIER3)
        
        data, errors = load_tier3_yaml(yaml_path, validate=True, log=logger)
        
        assert data is not None
        assert errors == []
        assert data["tool"]["id"] == "test_script"
    
    def test_load_without_validation(self, temp_pipeline_dir, logger):
        """Should load without validation when validate=False."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        incomplete = {"tool": {"id": "test"}}
        write_yaml(yaml_path, incomplete)
        
        data, errors = load_tier3_yaml(yaml_path, validate=False, log=logger)
        
        assert data is not None
        assert errors == []  # No validation errors when validate=False
    
    def test_load_invalid_yaml_syntax(self, temp_pipeline_dir, logger):
        """Should handle YAML syntax errors."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        yaml_path.write_text("invalid: yaml: syntax: [unclosed", encoding='utf-8')
        
        data, errors = load_tier3_yaml(yaml_path, validate=False, log=logger)
        
        assert data is None
        assert len(errors) > 0
        assert any("parse error" in e.lower() for e in errors)
    
    def test_load_non_dict_root(self, temp_pipeline_dir, logger):
        """Should reject YAML with non-dict root."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        yaml_path.write_text("- list\n- of\n- items", encoding='utf-8')
        
        data, errors = load_tier3_yaml(yaml_path, validate=False, log=logger)
        
        assert data is None
        assert any("must be a dictionary" in e for e in errors)


class TestCreateIndexEntry:
    """Test index entry creation."""
    
    def test_create_complete_entry(self, temp_pipeline_dir):
        """Should create complete index entry from valid data."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        
        entry = create_index_entry(yaml_path, VALID_TIER3, temp_pipeline_dir)
        
        assert entry["script_id"] == "test_script"
        assert entry["name"] == "Test Script"
        assert entry["category"] == "utility"
        assert entry["tier3_file"] == "tier3_test.yaml"
        assert entry["script_path"] == ".repo_studios/scripts/test_script.py"
        assert entry["summary"] == "A test script for validation"
        assert entry["keywords"] == ["test", "validation"]
        assert entry["status"] == "active"
        assert entry["entry_point"] == "run"
        assert entry["importable"] is True
    
    def test_create_entry_with_defaults(self, temp_pipeline_dir):
        """Should use defaults for missing fields."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        minimal = {
            "tool": {},
            "invocation": {},
            "metadata": {}
        }
        
        entry = create_index_entry(yaml_path, minimal, temp_pipeline_dir)
        
        assert entry["script_id"] == "unknown"
        assert entry["name"] == "Unknown Tool"
        assert entry["category"] == "unknown"
        assert entry["script_path"] == "unknown"
        assert entry["summary"] == "No description"
        assert entry["keywords"] == []
        assert entry["status"] == "unknown"
        assert entry["entry_point"] == "unknown"
        assert entry["importable"] is False


class TestGenerateIndex:
    """Test full index generation."""
    
    def test_generate_empty_index(self, temp_pipeline_dir, logger):
        """Should generate valid index with no scripts."""
        index = generate_index([], temp_pipeline_dir, validate=False, log=logger)
        
        assert index["version"] == "1.0.0"
        assert index["statistics"]["total_scripts"] == 0
        assert index["scripts"] == []
    
    def test_generate_index_single_script(self, temp_pipeline_dir, logger):
        """Should generate index with single script."""
        yaml_path = temp_pipeline_dir / "tier3_test.yaml"
        write_yaml(yaml_path, VALID_TIER3)
        
        index = generate_index([yaml_path], temp_pipeline_dir, validate=True, log=logger)
        
        assert index["statistics"]["total_scripts"] == 1
        assert len(index["scripts"]) == 1
        assert index["scripts"][0]["script_id"] == "test_script"
    
    def test_generate_index_multiple_categories(self, temp_pipeline_dir, logger):
        """Should correctly count and categorize scripts."""
        # Create scripts in different categories
        for category in ["producer", "consumer", "aggregator"]:
            yaml_path = temp_pipeline_dir / f"tier3_{category}.yaml"
            data = copy.deepcopy(VALID_TIER3)
            data["tool"]["id"] = f"{category}_script"
            data["metadata"]["category"] = category
            write_yaml(yaml_path, data)
        
        yaml_files = list(temp_pipeline_dir.glob("tier3_*.yaml"))
        index = generate_index(yaml_files, temp_pipeline_dir, validate=True, log=logger)
        
        assert index["statistics"]["total_scripts"] == 3
        assert index["statistics"]["categories"]["producer"] == 1
        assert index["statistics"]["categories"]["consumer"] == 1
        assert index["statistics"]["categories"]["aggregator"] == 1
        
        # Check by_category indices
        assert "producer_script" in index["by_category"]["producer"]
        assert "consumer_script" in index["by_category"]["consumer"]
        assert "aggregator_script" in index["by_category"]["aggregator"]
    
    def test_generate_index_with_validation_errors(self, temp_pipeline_dir, logger):
        """Should include validation report when errors found."""
        # Create valid script
        valid_path = temp_pipeline_dir / "tier3_valid.yaml"
        write_yaml(valid_path, VALID_TIER3)
        
        # Create invalid script
        invalid_path = temp_pipeline_dir / "tier3_invalid.yaml"
        invalid_data = {"tool": {"id": "invalid"}}  # Missing required sections
        write_yaml(invalid_path, invalid_data)
        
        yaml_files = [valid_path, invalid_path]
        index = generate_index(yaml_files, temp_pipeline_dir, validate=True, log=logger)
        
        # Should process valid script
        assert index["statistics"]["total_scripts"] == 2
        
        # Should include validation report
        assert "validation" in index
        assert "validation_errors" in index["validation"]
        errors = index["validation"]["validation_errors"]
        assert any(e["tier3_file"] == "tier3_invalid.yaml" for e in errors)


class TestCLI:
    """Test command-line interface."""
    
    def test_run_help(self):
        """Should exit with 0 for --help."""
        with pytest.raises(SystemExit) as exc_info:
            run(["--help"])
        assert exc_info.value.code == 0
    
    def test_run_missing_pipeline_dir(self, tmp_path):
        """Should fail if pipeline directory doesn't exist."""
        exit_code = run([
            "--repo-root", str(tmp_path),
            "--log-level", "ERROR"
        ])
        assert exit_code == 1
    
    def test_run_empty_directory(self, temp_pipeline_dir):
        """Should succeed with empty directory."""
        repo_root = temp_pipeline_dir.parent.parent.parent
        output = temp_pipeline_dir / "tier3_index" / "outputs" / "test_index.yaml"
        
        exit_code = run([
            "--repo-root", str(repo_root),
            "--output", str(output),
            "--log-level", "ERROR"
        ])
        
        assert exit_code == 0
        assert output.exists()
        
        # Check empty index structure
        with open(output, 'r') as f:
            index = yaml.safe_load(f)
        assert index["statistics"]["total_scripts"] == 0
    
    def test_run_with_scripts(self, temp_pipeline_dir):
        """Should successfully generate index with scripts."""
        repo_root = temp_pipeline_dir.parent.parent.parent
        
        # Create test scripts
        for i in range(3):
            yaml_path = temp_pipeline_dir / f"tier3_script{i}.yaml"
            data = copy.deepcopy(VALID_TIER3)
            data["tool"]["id"] = f"script{i}"
            write_yaml(yaml_path, data)
        
        output = temp_pipeline_dir / "tier3_index" / "outputs" / "test_index.yaml"
        
        exit_code = run([
            "--repo-root", str(repo_root),
            "--output", str(output),
            "--validate",
            "--log-level", "ERROR"
        ])
        
        assert exit_code == 0
        assert output.exists()
        
        # Check generated index
        with open(output, 'r') as f:
            index = yaml.safe_load(f)
        assert index["statistics"]["total_scripts"] == 3
        assert len(index["scripts"]) == 3
    
    def test_run_validation_failure(self, temp_pipeline_dir):
        """Should exit with error when validation fails."""
        repo_root = temp_pipeline_dir.parent.parent.parent
        
        # Create invalid script
        yaml_path = temp_pipeline_dir / "tier3_invalid.yaml"
        write_yaml(yaml_path, {"tool": {}})  # Missing required fields
        
        output = temp_pipeline_dir / "tier3_index" / "outputs" / "test_index.yaml"
        
        exit_code = run([
            "--repo-root", str(repo_root),
            "--output", str(output),
            "--validate",
            "--log-level", "ERROR"
        ])
        
        assert exit_code == 1  # Should fail with validation errors
        assert output.exists()  # But still write output
