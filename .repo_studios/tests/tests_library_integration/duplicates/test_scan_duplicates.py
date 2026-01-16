"""Tests for the Command Center duplicate scanning module."""

from __future__ import annotations

import ast
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Callable

import pytest

SCRIPTS_ROOT = Path(__file__).resolve().parents[4] / ".repo_studios" / "command_center" / "scripts"


def _load_slugify() -> Callable[[Path], str]:
    try:
        module = importlib.import_module("libraries")
    except ModuleNotFoundError:  # pragma: no cover - test sandbox fallback
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        module = importlib.import_module("libraries")
    return module.slugify_relative


slugify_relative = _load_slugify()

MODULE_DIR = SCRIPTS_ROOT / "aggregators"
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from scan_duplicates import (  # type: ignore  # noqa: E402
    FunctionExtractor,
    FunctionInfo,
    Paths,
    RunArtifacts,
    VIEWER_SLUG,
    TOPIC_SLUG,
    compute_ast_similarity,
    group_duplicates,
    scan_python_files,
    write_outputs,
    _extract_top_offenders,
    _slugify_relative,
)


def test_slugify_relative_aliases_library() -> None:
    assert _slugify_relative is slugify_relative


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


class TestFileScanning:
    def test_skips_hidden_and_ignored_directories(self, tmp_path: Path) -> None:
        target = tmp_path / "target"
        target.mkdir()
        allowed_pkg = target / "pkg"
        allowed_pkg.mkdir()
        (allowed_pkg / "__init__.py").write_text("", encoding="utf-8")
        ignored = target / "__pycache__"
        ignored.mkdir()
        (ignored / "ignored.py").write_text("# cache", encoding="utf-8")
        hidden = target / ".hidden"
        hidden.mkdir()
        (hidden / "hidden.py").write_text("# hidden", encoding="utf-8")

        discovered = scan_python_files(target)

        assert allowed_pkg / "__init__.py" in discovered
        assert all(path.name != "ignored.py" for path in discovered)
        assert all(path.name != "hidden.py" for path in discovered)


class TestOutputMirroring:
    def _build_paths(self, repo_root: Path, target: Path, reports_root: Path) -> Paths:
        slug = slugify_relative(target.relative_to(repo_root))
        index_dir = target / f"{target.name}_index"
        return Paths(
            repo_root=repo_root,
            target=target,
            output_dir=reports_root,
            target_slug=slug,
            source_name=target.name,
            target_index_dir=index_dir,
        )

    def test_write_outputs_mirrors_to_slugged_directory(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        target = repo_root / "src"
        target.mkdir()
        reports_root = repo_root / "reports"
        paths = self._build_paths(repo_root, target, reports_root)
        payload = {"metadata": {"target": "src"}, "stats": {}, "entries": []}
        summary = "# Summary\n"
        timestamp = datetime(2025, 11, 29, 21, 2, tzinfo=timezone.utc)

        artifacts = write_outputs(payload, summary, paths, timestamp=timestamp, keep=3)

        assert isinstance(artifacts, RunArtifacts)

        viewer_dir = reports_root / VIEWER_SLUG / TOPIC_SLUG / artifacts.slug
        assert artifacts.viewer_matrix.parent == viewer_dir
        assert artifacts.viewer_summary.parent == viewer_dir

        for path in (
            artifacts.viewer_matrix,
            artifacts.viewer_summary,
            artifacts.index_matrix,
            artifacts.index_summary,
        ):
            assert path.exists()
            assert path.read_text(encoding="utf-8")

        assert artifacts.viewer_matrix.read_text(encoding="utf-8") == artifacts.index_matrix.read_text(encoding="utf-8")
        assert artifacts.viewer_summary.read_text(encoding="utf-8") == artifacts.index_summary.read_text(encoding="utf-8")

        assert artifacts.viewer_matrix.name == f"{paths.source_name}_duplicate_matrix.json"
        assert artifacts.index_matrix.name == f"{paths.source_name}_duplicate_matrix-{artifacts.slug}.json"
        assert artifacts.index_summary.name == f"{paths.source_name}_duplicate_summary-{artifacts.slug}.md"

        matrices = list(paths.target_index_dir.glob(f"{paths.source_name}_duplicate_matrix-*.json"))
        summaries = list(paths.target_index_dir.glob(f"{paths.source_name}_duplicate_summary-*.md"))
        assert matrices == [artifacts.index_matrix]
        assert summaries == [artifacts.index_summary]

        latest_aliases = list((reports_root / VIEWER_SLUG / TOPIC_SLUG).glob("latest_*"))
        assert not latest_aliases

    def test_retention_prunes_old_runs(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        target = repo_root / "src"
        target.mkdir()
        reports_root = repo_root / "reports"
        paths = self._build_paths(repo_root, target, reports_root)
        payload = {"metadata": {"target": "src"}, "stats": {}, "entries": []}
        summary = "# Summary\n"
        timestamps: list[datetime] = []
        for offset in range(5):
            moment = datetime(2025, 10, 20 + offset, 12, offset, tzinfo=timezone.utc)
            timestamps.append(moment)
            write_outputs(payload, summary, paths, timestamp=moment, keep=2)

        matrices = sorted(paths.target_index_dir.glob(f"{paths.source_name}_duplicate_matrix-*.json"))
        assert len(matrices) == 2
        actual_slugs = sorted(
            path.stem.split(f"{paths.source_name}_duplicate_matrix-")[1] for path in matrices
        )
        expected_slugs = sorted(moment.strftime("%Y%m%d-%H%M") for moment in timestamps[-2:])
        assert actual_slugs == expected_slugs

        topic_dir = reports_root / VIEWER_SLUG / TOPIC_SLUG
        run_dirs = sorted(node for node in topic_dir.iterdir() if node.is_dir())
        assert len(run_dirs) == 2
        viewer_slugs = sorted(node.name for node in run_dirs)
        assert viewer_slugs == expected_slugs

    def test_retention_caps_keep_at_five(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        target = repo_root / "src"
        target.mkdir()
        reports_root = repo_root / "reports"
        paths = self._build_paths(repo_root, target, reports_root)
        payload = {"metadata": {"target": "src"}, "stats": {}, "entries": []}
        summary = "# Summary\n"

        for offset in range(7):
            moment = datetime(2025, 10, 1 + offset, 12, 0, tzinfo=timezone.utc)
            write_outputs(payload, summary, paths, timestamp=moment, keep=10)

        topic_dir = reports_root / VIEWER_SLUG / TOPIC_SLUG
        run_dirs = sorted(node for node in topic_dir.iterdir() if node.is_dir())
        assert len(run_dirs) == 5
