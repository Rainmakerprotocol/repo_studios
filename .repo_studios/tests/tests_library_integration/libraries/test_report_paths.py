"""Unit tests for report_paths.py canonical path registry.

Tests cover all exported functions and constants with full coverage
of success and error paths.
"""

from __future__ import annotations

import sys
from pathlib import Path, PosixPath, WindowsPath

import pytest

# Add the libraries path to enable imports
_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "command_center" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from libraries.report_paths import (
    AGGREGATOR_REPORTS,
    CONSUMER_REPORTS,
    HEALTHVIEW_ROOT,
    ORCHESTRATOR_REPORTS,
    PRODUCER_REPORTS,
    RAWVIEW,
    REPORTS_ROOT,
    REPO_STUDIOS_ROOT,
    SUMMARIZER_REPORTS,
    VALID_TIER_CLASSES,
    TierClass,
    build_absolute_topic_path,
    build_topic_path,
    get_all_class_roots,
    get_class_root,
    get_default_output_dir,
    infer_class_from_script,
    validate_output_path,
)


class TestConstants:
    """Tests for module-level constants."""

    def test_repo_studios_root_is_path(self) -> None:
        """REPO_STUDIOS_ROOT is a Path object."""
        assert isinstance(REPO_STUDIOS_ROOT, Path)

    def test_repo_studios_root_value(self) -> None:
        """REPO_STUDIOS_ROOT has correct value."""
        assert str(REPO_STUDIOS_ROOT) == ".repo_studios"

    def test_reports_root_is_child_of_repo_studios(self) -> None:
        """REPORTS_ROOT is under REPO_STUDIOS_ROOT."""
        assert REPORTS_ROOT.parts[0] == REPO_STUDIOS_ROOT.parts[0]
        assert REPORTS_ROOT.parts == (".repo_studios", "reports")

    def test_healthview_root_is_child_of_reports(self) -> None:
        """HEALTHVIEW_ROOT is under REPORTS_ROOT."""
        assert HEALTHVIEW_ROOT.parts == (".repo_studios", "reports", "healthview")

    def test_aggregator_reports_path(self) -> None:
        """AGGREGATOR_REPORTS has correct path."""
        assert AGGREGATOR_REPORTS.parts == (".repo_studios", "reports", "healthview", "aggregator_reports")

    def test_consumer_reports_path(self) -> None:
        """CONSUMER_REPORTS has correct path."""
        assert CONSUMER_REPORTS.parts == (".repo_studios", "reports", "healthview", "consumer_reports")

    def test_orchestrator_reports_path(self) -> None:
        """ORCHESTRATOR_REPORTS has correct path."""
        assert ORCHESTRATOR_REPORTS.parts == (".repo_studios", "reports", "healthview", "orchestrator_reports")

    def test_producer_reports_path(self) -> None:
        """PRODUCER_REPORTS has correct path."""
        assert PRODUCER_REPORTS.parts == (".repo_studios", "reports", "healthview", "producer_reports")

    def test_rawview_path(self) -> None:
        """RAWVIEW has correct path."""
        assert RAWVIEW.parts == (".repo_studios", "reports", "healthview", "rawview")

    def test_summarizer_reports_path(self) -> None:
        """SUMMARIZER_REPORTS has correct path."""
        assert SUMMARIZER_REPORTS.parts == (".repo_studios", "reports", "healthview", "summarizer_reports")

    def test_valid_tier_classes_is_frozenset(self) -> None:
        """VALID_TIER_CLASSES is immutable."""
        assert isinstance(VALID_TIER_CLASSES, frozenset)

    def test_valid_tier_classes_contains_all_classes(self) -> None:
        """VALID_TIER_CLASSES contains all expected classes."""
        expected = {"aggregator", "consumer", "orchestrator", "producer", "rawview", "summarizer"}
        assert VALID_TIER_CLASSES == expected


class TestGetClassRoot:
    """Tests for get_class_root function."""

    def test_producer_returns_correct_path(self) -> None:
        """get_class_root('producer') returns PRODUCER_REPORTS."""
        result = get_class_root("producer")
        assert result == PRODUCER_REPORTS

    def test_consumer_returns_correct_path(self) -> None:
        """get_class_root('consumer') returns CONSUMER_REPORTS."""
        result = get_class_root("consumer")
        assert result == CONSUMER_REPORTS

    def test_aggregator_returns_correct_path(self) -> None:
        """get_class_root('aggregator') returns AGGREGATOR_REPORTS."""
        result = get_class_root("aggregator")
        assert result == AGGREGATOR_REPORTS

    def test_summarizer_returns_correct_path(self) -> None:
        """get_class_root('summarizer') returns SUMMARIZER_REPORTS."""
        result = get_class_root("summarizer")
        assert result == SUMMARIZER_REPORTS

    def test_orchestrator_returns_correct_path(self) -> None:
        """get_class_root('orchestrator') returns ORCHESTRATOR_REPORTS."""
        result = get_class_root("orchestrator")
        assert result == ORCHESTRATOR_REPORTS

    def test_rawview_returns_correct_path(self) -> None:
        """get_class_root('rawview') returns RAWVIEW."""
        result = get_class_root("rawview")
        assert result == RAWVIEW

    def test_invalid_class_raises_value_error(self) -> None:
        """get_class_root raises ValueError for unknown class."""
        with pytest.raises(ValueError, match="Unknown tier class"):
            get_class_root("invalid_class")  # type: ignore[arg-type]

    def test_error_message_lists_valid_classes(self) -> None:
        """Error message includes list of valid tier classes."""
        with pytest.raises(ValueError) as exc_info:
            get_class_root("bogus")  # type: ignore[arg-type]
        assert "aggregator" in str(exc_info.value)
        assert "producer" in str(exc_info.value)


class TestBuildTopicPath:
    """Tests for build_topic_path function."""

    def test_producer_anchor_inventory(self) -> None:
        """build_topic_path builds correct path for producer/anchor_inventory."""
        result = build_topic_path("producer", "anchor_inventory")
        assert result.parts == (".repo_studios", "reports", "healthview", "producer_reports", "anchor_inventory")

    def test_consumer_fault_artifacts(self) -> None:
        """build_topic_path builds correct path for consumer/fault_artifacts."""
        result = build_topic_path("consumer", "fault_artifacts")
        assert result.parts == (".repo_studios", "reports", "healthview", "consumer_reports", "fault_artifacts")

    def test_aggregator_docs_health_signals(self) -> None:
        """build_topic_path builds correct path for aggregator topic."""
        result = build_topic_path("aggregator", "docs_health_signals")
        assert result.parts == (".repo_studios", "reports", "healthview", "aggregator_reports", "docs_health_signals")

    def test_summarizer_fault_diagnostics_overview(self) -> None:
        """build_topic_path builds correct path for summarizer topic."""
        result = build_topic_path("summarizer", "fault_diagnostics_overview")
        expected = (".repo_studios", "reports", "healthview", "summarizer_reports", "fault_diagnostics_overview")
        assert result.parts == expected

    def test_empty_topic_raises_value_error(self) -> None:
        """build_topic_path raises ValueError for empty topic."""
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            build_topic_path("producer", "")

    def test_none_topic_raises_value_error(self) -> None:
        """build_topic_path raises ValueError for None topic."""
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            build_topic_path("producer", None)  # type: ignore[arg-type]

    def test_invalid_tier_class_propagates_error(self) -> None:
        """build_topic_path propagates ValueError from get_class_root."""
        with pytest.raises(ValueError, match="Unknown tier class"):
            build_topic_path("invalid", "topic")  # type: ignore[arg-type]


class TestBuildAbsoluteTopicPath:
    """Tests for build_absolute_topic_path function."""

    def test_builds_absolute_path(self) -> None:
        """build_absolute_topic_path creates absolute path from repo root."""
        repo_root = Path("/home/user/repo")
        result = build_absolute_topic_path(repo_root, "producer", "anchor_inventory")
        expected = Path("/home/user/repo/.repo_studios/reports/healthview/producer_reports/anchor_inventory")
        assert result == expected

    def test_windows_style_path(self) -> None:
        """build_absolute_topic_path works with Windows-style paths."""
        repo_root = Path("C:/Users/dev/repo")
        result = build_absolute_topic_path(repo_root, "aggregator", "docs_health")
        # Path will normalize separators
        assert "aggregator_reports" in str(result)
        assert "docs_health" in str(result)

    def test_preserves_repo_root_type(self) -> None:
        """Result is a Path object."""
        repo_root = Path("/tmp/test")
        result = build_absolute_topic_path(repo_root, "consumer", "test_topic")
        assert isinstance(result, Path)


class TestInferClassFromScript:
    """Tests for infer_class_from_script function."""

    def test_producers_folder_returns_producer(self) -> None:
        """Scripts in /producers/ folder return 'producer'."""
        assert infer_class_from_script("scripts/producers/generate_anchor_inventory.py") == "producer"

    def test_consumers_folder_returns_consumer(self) -> None:
        """Scripts in /consumers/ folder return 'consumer'."""
        assert infer_class_from_script("scripts/consumers/generate_fault_artifacts.py") == "consumer"

    def test_aggregators_folder_returns_aggregator(self) -> None:
        """Scripts in /aggregators/ folder return 'aggregator'."""
        assert infer_class_from_script("scripts/aggregators/aggregate_docs_health.py") == "aggregator"

    def test_summarizers_folder_returns_summarizer(self) -> None:
        """Scripts in /summarizers/ folder return 'summarizer'."""
        assert infer_class_from_script("scripts/summarizers/summarize_health.py") == "summarizer"

    def test_orchestrators_folder_returns_orchestrator(self) -> None:
        """Scripts in /orchestrators/ folder return 'orchestrator'."""
        assert infer_class_from_script("command_center/scripts/orchestrators/run_health.py") == "orchestrator"

    def test_rawview_folder_returns_rawview(self) -> None:
        """Scripts in /rawview/ folder return 'rawview'."""
        assert infer_class_from_script("scripts/rawview/emit_raw.py") == "rawview"

    def test_unknown_path_returns_none(self) -> None:
        """Unknown paths return None."""
        assert infer_class_from_script("some/unknown/path.py") is None

    def test_handles_backslashes(self) -> None:
        """Windows-style paths with backslashes are handled."""
        assert infer_class_from_script("scripts\\producers\\generate.py") == "producer"

    def test_case_insensitive(self) -> None:
        """Path matching is case-insensitive."""
        assert infer_class_from_script("Scripts/PRODUCERS/generate.py") == "producer"

    def test_accepts_path_object(self) -> None:
        """Function accepts Path objects."""
        result = infer_class_from_script(Path("scripts/consumers/process.py"))
        assert result == "consumer"

    def test_full_absolute_path(self) -> None:
        """Works with full absolute paths."""
        path = "/home/user/repo/.repo_studios/scripts/aggregators/agg.py"
        assert infer_class_from_script(path) == "aggregator"


class TestGetDefaultOutputDir:
    """Tests for get_default_output_dir function."""

    def test_producer_script_returns_producer_reports(self) -> None:
        """Producer scripts return PRODUCER_REPORTS."""
        result = get_default_output_dir("scripts/producers/generate_anchor_inventory.py")
        assert result == PRODUCER_REPORTS

    def test_consumer_script_returns_consumer_reports(self) -> None:
        """Consumer scripts return CONSUMER_REPORTS."""
        result = get_default_output_dir("scripts/consumers/classify.py")
        assert result == CONSUMER_REPORTS

    def test_aggregator_script_returns_aggregator_reports(self) -> None:
        """Aggregator scripts return AGGREGATOR_REPORTS."""
        result = get_default_output_dir("scripts/aggregators/aggregate.py")
        assert result == AGGREGATOR_REPORTS

    def test_unknown_path_raises_value_error(self) -> None:
        """Unknown script paths raise ValueError."""
        with pytest.raises(ValueError, match="Cannot infer tier class"):
            get_default_output_dir("some/random/script.py")

    def test_error_includes_script_path(self) -> None:
        """Error message includes the problematic path."""
        with pytest.raises(ValueError) as exc_info:
            get_default_output_dir("mystery/location.py")
        assert "mystery/location.py" in str(exc_info.value)


class TestValidateOutputPath:
    """Tests for validate_output_path function."""

    def test_valid_producer_path_returns_true(self) -> None:
        """Valid producer path returns True."""
        path = Path(".repo_studios/reports/healthview/producer_reports/anchor_inventory")
        assert validate_output_path(path) is True

    def test_valid_consumer_path_returns_true(self) -> None:
        """Valid consumer path returns True."""
        path = Path(".repo_studios/reports/healthview/consumer_reports/fault_artifacts")
        assert validate_output_path(path) is True

    def test_valid_aggregator_path_returns_true(self) -> None:
        """Valid aggregator path returns True."""
        path = Path(".repo_studios/reports/healthview/aggregator_reports/docs_health")
        assert validate_output_path(path) is True

    def test_valid_rawview_path_returns_true(self) -> None:
        """Valid rawview path returns True."""
        path = Path(".repo_studios/reports/healthview/rawview/raw_data")
        assert validate_output_path(path) is True

    def test_missing_tier_class_returns_false(self) -> None:
        """Path without tier class folder returns False."""
        path = Path(".repo_studios/reports/healthview/anchor_inventory")
        assert validate_output_path(path) is False

    def test_missing_healthview_returns_false(self) -> None:
        """Path without healthview folder returns False."""
        path = Path(".repo_studios/reports/producer_reports/anchor_inventory")
        assert validate_output_path(path) is False

    def test_random_path_returns_false(self) -> None:
        """Completely unrelated path returns False."""
        path = Path("/tmp/some/random/path")
        assert validate_output_path(path) is False

    def test_absolute_valid_path_returns_true(self) -> None:
        """Absolute paths with valid structure return True."""
        path = Path("/home/user/repo/.repo_studios/reports/healthview/producer_reports/topic")
        assert validate_output_path(path) is True


class TestGetAllClassRoots:
    """Tests for get_all_class_roots function."""

    def test_returns_dict(self) -> None:
        """get_all_class_roots returns a dictionary."""
        result = get_all_class_roots()
        assert isinstance(result, dict)

    def test_contains_all_tier_classes(self) -> None:
        """Result contains all tier classes."""
        result = get_all_class_roots()
        expected_keys = {"aggregator", "consumer", "orchestrator", "producer", "rawview", "summarizer"}
        assert set(result.keys()) == expected_keys

    def test_values_are_paths(self) -> None:
        """All values are Path objects."""
        result = get_all_class_roots()
        for value in result.values():
            assert isinstance(value, Path)

    def test_returns_copy_not_reference(self) -> None:
        """Returns a copy, not the internal mapping."""
        result1 = get_all_class_roots()
        result2 = get_all_class_roots()
        # Modifying one should not affect the other
        result1["producer"] = Path("/modified")
        assert result2["producer"] == PRODUCER_REPORTS

    def test_producer_value_matches_constant(self) -> None:
        """Producer value matches PRODUCER_REPORTS constant."""
        result = get_all_class_roots()
        assert result["producer"] == PRODUCER_REPORTS

    def test_aggregator_value_matches_constant(self) -> None:
        """Aggregator value matches AGGREGATOR_REPORTS constant."""
        result = get_all_class_roots()
        assert result["aggregator"] == AGGREGATOR_REPORTS


class TestPathHierarchy:
    """Tests verifying the path hierarchy is consistent."""

    def test_all_class_roots_under_healthview(self) -> None:
        """All class roots are under HEALTHVIEW_ROOT."""
        for tier_class in VALID_TIER_CLASSES:
            root = get_class_root(tier_class)  # type: ignore[arg-type]
            # Check that healthview is in the path parts
            assert "healthview" in root.parts

    def test_all_class_roots_are_relative(self) -> None:
        """All class roots are relative paths."""
        for tier_class in VALID_TIER_CLASSES:
            root = get_class_root(tier_class)  # type: ignore[arg-type]
            assert not root.is_absolute()

    def test_topic_paths_add_one_level(self) -> None:
        """build_topic_path adds exactly one level to class root."""
        class_root = get_class_root("producer")
        topic_path = build_topic_path("producer", "my_topic")
        assert len(topic_path.parts) == len(class_root.parts) + 1
        assert topic_path.parts[-1] == "my_topic"
