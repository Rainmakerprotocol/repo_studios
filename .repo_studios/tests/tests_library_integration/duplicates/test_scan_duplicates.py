"""Tests for the library integration duplicate scanning module."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from textwrap import dedent

import pytest

MODULE_DIR = Path(__file__).resolve().parents[4] / ".repo_studios" / "scripts" / "library_integration" / "duplicates"
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from scan_duplicates import (  # type: ignore  # noqa: E402
    FunctionExtractor,
    FunctionInfo,
    compute_ast_similarity,
    group_duplicates,
    _extract_top_offenders,
)


class TestFunctionExtraction:
    def test_extracts_simple_function(self, tmp_path: Path) -> None:
        source = dedent(
            """
            def hello_world():
                print("Hello, World!")
            """
        )
        tree = ast.parse(source)
        extractor = FunctionExtractor(source, tmp_path / "test.py", tmp_path)
        extractor.visit(tree)
        assert len(extractor.functions) == 1
        func = extractor.functions[0]
        assert func.function_name == "hello_world"
        assert func.is_function is True

    def test_extracts_function_with_args(self, tmp_path: Path) -> None:
        source = dedent(
            """
            def add(a: int, b: int) -> int:
                return a + b
            """
        )
        tree = ast.parse(source)
        extractor = FunctionExtractor(source, tmp_path / "test.py", tmp_path)
        extractor.visit(tree)
        assert len(extractor.functions) == 1
        func = extractor.functions[0]
        assert "a, b" in func.signature

    def test_extracts_multiple_functions(self, tmp_path: Path) -> None:
        source = dedent(
            """
            def func1():
                pass

            def func2():
                pass

            def func3():
                pass
            """
        )
        tree = ast.parse(source)
        extractor = FunctionExtractor(source, tmp_path / "test.py", tmp_path)
        extractor.visit(tree)
        assert len(extractor.functions) == 3
        names = [f.function_name for f in extractor.functions]
        assert names == ["func1", "func2", "func3"]

    def test_computes_code_hash(self, tmp_path: Path) -> None:
        source1 = dedent(
            """
            def example():
                x = 1
                return x
            """
        )
        source2 = dedent(
            """
            def example():
                x = 1
                return x
            """
        )
        extractor1 = FunctionExtractor(source1, tmp_path / "file1.py", tmp_path)
        extractor1.visit(ast.parse(source1))
        extractor2 = FunctionExtractor(source2, tmp_path / "file2.py", tmp_path)
        extractor2.visit(ast.parse(source2))
        assert extractor1.functions[0].code_hash == extractor2.functions[0].code_hash


class TestDuplicateDetection:
    def test_detects_exact_duplicates(self) -> None:
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
            code_hash="abc123",
            signature="def _copy_latest()",
            body_lines=["def _copy_latest():", "    pass"],
        )
        groups = group_duplicates([func1, func2], similarity_threshold=0.85, min_lines=2)
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_ignores_short_functions(self) -> None:
        func = FunctionInfo(
            file="file.py",
            line_start=1,
            line_end=2,
            function_name="tiny",
            is_function=True,
            code_hash="xyz789",
            signature="def tiny()",
            body_lines=["def tiny(): pass"],
        )
        groups = group_duplicates([func], similarity_threshold=0.85, min_lines=3)
        assert len(groups) == 0


class TestSimilarityScoring:
    def test_identical_functions_score_one(self, tmp_path: Path) -> None:
        source = dedent(
            """
            def example():
                x = 1
                return x
            """
        )
        extractor = FunctionExtractor(source, tmp_path / "test.py", tmp_path)
        extractor.visit(ast.parse(source))
        func = extractor.functions[0]
        similarity = compute_ast_similarity(func, func)
        assert similarity == pytest.approx(1.0)

    def test_different_functions_score_low(self, tmp_path: Path) -> None:
        source1 = dedent(
            """
            def func1():
                return 1
            """
        )
        source2 = dedent(
            """
            def func2():
                x = []
                for i in range(10):
                    x.append(i * 2)
                return sum(x)
            """
        )
        extractor1 = FunctionExtractor(source1, tmp_path / "file1.py", tmp_path)
        extractor1.visit(ast.parse(source1))
        extractor2 = FunctionExtractor(source2, tmp_path / "file2.py", tmp_path)
        extractor2.visit(ast.parse(source2))
        similarity = compute_ast_similarity(extractor1.functions[0], extractor2.functions[0])
        assert similarity < 0.5


class TestLibraryPathReference:
    def test_occurrence_structure(self) -> None:
        func = FunctionInfo(
            file="file.py",
            line_start=1,
            line_end=5,
            function_name="example",
            is_function=True,
            code_hash="aaa111",
            signature="def example()",
            body_lines=["def example():", "    return 1"],
        )
        occurrence = func.to_occurrence()
        assert occurrence["file"] == "file.py"
        assert "line_start" in occurrence and "line_end" in occurrence


class TestTopOffenders:
    def test_extract_top_offenders_includes_location_details(self, tmp_path: Path) -> None:
        source_file = tmp_path / "foo.py"
        source_file.write_text("def foo():\n    return 1\n", encoding="utf-8")
        matrix = [
            {
                "function_name": "foo",
                "producer_duplicate_count": 0,
                "producer_instances": [],
                "scanner_groups": [
                    {
                        "occurrences": [
                            {
                                "file": "foo.py",
                                "line_start": 1,
                                "line_end": 2,
                                "sample_line": "def foo():",
                            }
                        ]
                    }
                ],
            }
        ]

        offenders = _extract_top_offenders(matrix, tmp_path, limit=5)
        assert len(offenders) == 1
        offender = offenders[0]
        assert offender["occurrence_count"] == 1
        detail = offender["occurrences"][0]
        assert detail["path"] == "foo.py"
        assert detail["line_start"] == 1
        assert detail["line_end"] == 2
        assert detail["line_count"] == 2
        assert detail["sample_line"].startswith("def foo")
