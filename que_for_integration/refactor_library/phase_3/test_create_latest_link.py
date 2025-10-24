"""Tests for artifact_lifecycle.versioning.create_latest_link module.

Tests cover:
- Successful hardlink creation
- Fallback to file copy
- Overwriting existing destination
- Error handling for missing source
- Error handling for invalid inputs
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add library to path for import
sys.path.insert(0, str(Path(__file__).parents[3] / ".repo_studios" / "library"))

from artifact_lifecycle.versioning.create_latest_link import create_latest_link


class TestCreateLatestLink:
    """Test suite for create_latest_link function."""
    
    def test_creates_hardlink_successfully(self, tmp_path: Path) -> None:
        """Test successful hardlink creation."""
        source = tmp_path / "source.txt"
        destination = tmp_path / "latest.txt"
        
        source.write_text("test content", encoding="utf-8")
        
        create_latest_link(source, destination)
        
        assert destination.exists()
        assert destination.read_text(encoding="utf-8") == "test content"
        
        # Verify it's a hardlink (same inode)
        assert source.stat().st_ino == destination.stat().st_ino
    
    def test_fallback_to_copy_on_hardlink_failure(self, tmp_path: Path) -> None:
        """Test fallback to file copy when hardlink fails."""
        source = tmp_path / "source.txt"
        destination = tmp_path / "latest.txt"
        
        source.write_text("test content", encoding="utf-8")
        
        # Mock hardlink_to to raise OSError (simulating cross-device link)
        with patch.object(Path, "hardlink_to", side_effect=OSError("Cross-device link")):
            create_latest_link(source, destination)
        
        assert destination.exists()
        assert destination.read_text(encoding="utf-8") == "test content"
        
        # Verify it's NOT a hardlink (different inodes)
        assert source.stat().st_ino != destination.stat().st_ino
    
    def test_overwrites_existing_destination(self, tmp_path: Path) -> None:
        """Test that existing destination is replaced."""
        source = tmp_path / "source.txt"
        destination = tmp_path / "latest.txt"
        
        source.write_text("new content", encoding="utf-8")
        destination.write_text("old content", encoding="utf-8")
        
        create_latest_link(source, destination)
        
        assert destination.read_text(encoding="utf-8") == "new content"
    
    def test_raises_error_on_missing_source(self, tmp_path: Path) -> None:
        """Test FileNotFoundError when source doesn't exist."""
        source = tmp_path / "nonexistent.txt"
        destination = tmp_path / "latest.txt"
        
        with pytest.raises(FileNotFoundError, match="Source file does not exist"):
            create_latest_link(source, destination)
    
    def test_raises_error_on_directory_source(self, tmp_path: Path) -> None:
        """Test ValueError when source is a directory."""
        source = tmp_path / "source_dir"
        destination = tmp_path / "latest.txt"
        
        source.mkdir()
        
        with pytest.raises(ValueError, match="Source must be a file"):
            create_latest_link(source, destination)
    
    def test_creates_in_subdirectory(self, tmp_path: Path) -> None:
        """Test creating link in nested directory structure."""
        source = tmp_path / "artifacts" / "report-20251023.json"
        destination = tmp_path / "artifacts" / "latest_report.json"
        
        source.parent.mkdir(parents=True)
        source.write_text('{"status": "ok"}', encoding="utf-8")
        
        create_latest_link(source, destination)
        
        assert destination.exists()
        assert destination.read_text(encoding="utf-8") == '{"status": "ok"}'
    
    def test_preserves_file_content_exactly(self, tmp_path: Path) -> None:
        """Test that file content is preserved byte-for-byte."""
        source = tmp_path / "binary.dat"
        destination = tmp_path / "latest.dat"
        
        # Binary content
        binary_data = bytes([0, 1, 2, 255, 254, 253])
        source.write_bytes(binary_data)
        
        create_latest_link(source, destination)
        
        assert destination.read_bytes() == binary_data
    
    def test_multiple_calls_to_same_destination(self, tmp_path: Path) -> None:
        """Test calling function multiple times with same destination."""
        source1 = tmp_path / "source1.txt"
        source2 = tmp_path / "source2.txt"
        destination = tmp_path / "latest.txt"
        
        source1.write_text("version 1", encoding="utf-8")
        source2.write_text("version 2", encoding="utf-8")
        
        create_latest_link(source1, destination)
        assert destination.read_text(encoding="utf-8") == "version 1"
        
        create_latest_link(source2, destination)
        assert destination.read_text(encoding="utf-8") == "version 2"
    
    def test_handles_unicode_content(self, tmp_path: Path) -> None:
        """Test handling of unicode content."""
        source = tmp_path / "unicode.txt"
        destination = tmp_path / "latest.txt"
        
        unicode_content = "Hello 世界 🌍 Ñoño"
        source.write_text(unicode_content, encoding="utf-8")
        
        create_latest_link(source, destination)
        
        assert destination.read_text(encoding="utf-8") == unicode_content


class TestCreateLatestLinkIntegration:
    """Integration tests simulating real-world usage patterns."""
    
    def test_artifact_versioning_workflow(self, tmp_path: Path) -> None:
        """Test typical artifact versioning workflow."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        
        # Create multiple versioned reports
        reports = [
            artifacts_dir / "report-20251023_100000.json",
            artifacts_dir / "report-20251023_110000.json",
            artifacts_dir / "report-20251023_120000.json",
        ]
        
        for idx, report in enumerate(reports):
            report.write_text(f'{{"version": {idx + 1}}}', encoding="utf-8")
        
        # Point 'latest' to each in sequence
        latest = artifacts_dir / "latest_report.json"
        
        for report in reports:
            create_latest_link(report, latest)
            content = latest.read_text(encoding="utf-8")
            assert f'"version": {reports.index(report) + 1}' in content
        
        # Latest should point to most recent
        assert '{"version": 3}' in latest.read_text(encoding="utf-8")
    
    def test_cross_format_linking(self, tmp_path: Path) -> None:
        """Test linking different file formats."""
        formats = [
            ("report.json", '{"status": "ok"}'),
            ("report.md", "# Report\n\nStatus: OK"),
            ("report.log", "status=ok\n"),
        ]
        
        for filename, content in formats:
            source = tmp_path / filename
            destination = tmp_path / f"latest_{filename}"
            
            source.write_text(content, encoding="utf-8")
            create_latest_link(source, destination)
            
            assert destination.read_text(encoding="utf-8") == content


@pytest.fixture
def cleanup_test_files(tmp_path: Path):
    """Cleanup fixture (though tmp_path auto-cleans)."""
    yield
    # Explicit cleanup if needed
    pass


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
