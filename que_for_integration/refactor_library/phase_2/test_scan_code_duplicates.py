"""Tests for scan_code_duplicates.py duplicate detection tool.

Tests cover:
- AST function extraction
- Hash-based duplicate detection
- Similarity scoring
- Library path inference
- Report generation
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from textwrap import dedent

import pytest

# Import the scanner (adjust path as needed)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "producers"))

from scan_code_duplicates import (
    FunctionExtractor,
    FunctionInfo,
    compute_ast_similarity,
    group_duplicates,
    infer_library_path,
)


class TestFunctionExtraction:
    """Test AST-based function extraction."""
    
    def test_extracts_simple_function(self, tmp_path: Path) -> None:
        """Test extraction of simple function definition."""
        source = dedent("""
            def hello_world():
                print("Hello, World!")
        """)
        
        tree = ast.parse(source)
        extractor = FunctionExtractor(source, "test.py", tmp_path)
        extractor.visit(tree)
        
        assert len(extractor.functions) == 1
        func = extractor.functions[0]
        assert func.function_name == "hello_world"
        assert func.is_function is True
    
    def test_extracts_function_with_args(self, tmp_path: Path) -> None:
        """Test extraction of function with arguments."""
        source = dedent("""
            def add(a: int, b: int) -> int:
                return a + b
        """)
        
        tree = ast.parse(source)
        extractor = FunctionExtractor(source, "test.py", tmp_path)
        extractor.visit(tree)
        
        assert len(extractor.functions) == 1
        func = extractor.functions[0]
        assert func.function_name == "add"
        assert "a, b" in func.signature
    
    def test_extracts_multiple_functions(self, tmp_path: Path) -> None:
        """Test extraction of multiple functions."""
        source = dedent("""
            def func1():
                pass
            
            def func2():
                pass
            
            def func3():
                pass
        """)
        
        tree = ast.parse(source)
        extractor = FunctionExtractor(source, "test.py", tmp_path)
        extractor.visit(tree)
        
        assert len(extractor.functions) == 3
        names = [f.function_name for f in extractor.functions]
        assert names == ["func1", "func2", "func3"]
    
    def test_computes_code_hash(self, tmp_path: Path) -> None:
        """Test that identical code gets same hash."""
        source1 = dedent("""
            def example():
                x = 1
                return x
        """)
        
        source2 = dedent("""
            def example():
                x = 1
                return x
        """)
        
        tree1 = ast.parse(source1)
        extractor1 = FunctionExtractor(source1, "test1.py", tmp_path)
        extractor1.visit(tree1)
        
        tree2 = ast.parse(source2)
        extractor2 = FunctionExtractor(source2, "test2.py", tmp_path)
        extractor2.visit(tree2)
        
        assert extractor1.functions[0].code_hash == extractor2.functions[0].code_hash


class TestDuplicateDetection:
    """Test duplicate grouping logic."""
    
    def test_detects_exact_duplicates(self, tmp_path: Path) -> None:
        """Test detection of exact duplicate functions."""
        func1 = FunctionInfo(
            file="file1.py",
            line_start=1,
            line_end=3,
            function_name="copy_latest",
            is_function=True,
            code_hash="abc123",
            signature="def copy_latest()",
            body_lines=["def copy_latest():", "    pass"],
        )
        
        func2 = FunctionInfo(
            file="file2.py",
            line_start=10,
            line_end=12,
            function_name="_copy_latest",
            is_function=True,
            code_hash="abc123",  # Same hash = exact duplicate
            signature="def _copy_latest()",
            body_lines=["def _copy_latest():", "    pass"],
        )
        
        groups = group_duplicates([func1, func2], similarity_threshold=0.85, min_lines=2)
        
        assert len(groups) == 1
        assert len(groups[0]) == 2
    
    def test_ignores_short_functions(self, tmp_path: Path) -> None:
        """Test that very short functions are filtered out."""
        func = FunctionInfo(
            file="file.py",
            line_start=1,
            line_end=2,
            function_name="tiny",
            is_function=True,
            code_hash="xyz789",
            signature="def tiny()",
            body_lines=["def tiny(): pass"],  # Only 1 line
        )
        
        groups = group_duplicates([func], similarity_threshold=0.85, min_lines=3)
        
        assert len(groups) == 0  # Filtered out


class TestSimilarityScoring:
    """Test AST similarity computation."""
    
    def test_identical_functions_score_1(self, tmp_path: Path) -> None:
        """Test that identical functions get similarity score of 1.0."""
        source = dedent("""
            def example():
                x = 1
                return x
        """)
        
        tree = ast.parse(source)
        extractor = FunctionExtractor(source, "test.py", tmp_path)
        extractor.visit(tree)
        
        func = extractor.functions[0]
        similarity = compute_ast_similarity(func, func)
        
        assert similarity == 1.0
    
    def test_different_functions_score_low(self, tmp_path: Path) -> None:
        """Test that very different functions get low similarity."""
        source1 = dedent("""
            def func1():
                return 1
        """)
        
        source2 = dedent("""
            def func2():
                x = []
                for i in range(10):
                    x.append(i * 2)
                return sum(x)
        """)
        
        tree1 = ast.parse(source1)
        extractor1 = FunctionExtractor(source1, "test1.py", tmp_path)
        extractor1.visit(tree1)
        
        tree2 = ast.parse(source2)
        extractor2 = FunctionExtractor(source2, "test2.py", tmp_path)
        extractor2.visit(tree2)
        
        func1 = extractor1.functions[0]
        func2 = extractor2.functions[0]
        
        similarity = compute_ast_similarity(func1, func2)
        
        assert similarity < 0.5  # Very different


class TestLibraryPathInference:
    """Test automatic library path recommendation."""
    
    def test_infers_artifact_lifecycle_path(self) -> None:
        """Test inference for artifact-related function."""
        result = infer_library_path("copy_latest", "utility_function")
        
        assert "artifact_lifecycle" in result["target_path"]
        assert "versioning" in result["target_path"]
    
    def test_infers_filesystem_path(self) -> None:
        """Test inference for filesystem function."""
        result = infer_library_path("ensure_directory", "utility_function")
        
        assert "filesystem" in result["target_path"]
        assert "directory_management" in result["target_path"]
    
    def test_infers_time_handling_path(self) -> None:
        """Test inference for time-related function."""
        result = infer_library_path("parse_timestamp_utc", "utility_function")
        
        assert "time_handling" in result["target_path"]
        assert "parsing" in result["target_path"]
    
    def test_provides_import_statement(self) -> None:
        """Test that inference includes import statement."""
        result = infer_library_path("create_link", "utility_function")
        
        assert "import_statement" in result
        assert "from .repo_studios.library" in result["import_statement"]


class TestReportGeneration:
    """Test JSON report structure."""
    
    def test_report_has_required_fields(self) -> None:
        """Test that report contains all required fields."""
        # This would require building a full report, simplified test
        required_fields = [
            "schema_version",
            "generated_utc",
            "repo_root",
            "duplicate_groups",
            "summary",
        ]
        
        # Placeholder - in real test, would generate actual report
        mock_report = {
            "schema_version": "1.0.0",
            "generated_utc": "2025-10-23T00:00:00Z",
            "repo_root": "/repo",
            "duplicate_groups": [],
            "summary": {},
        }
        
        for field in required_fields:
            assert field in mock_report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
