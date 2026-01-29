from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_test_coverage_inventory.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_test_coverage_inventory", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_coverage_fixture(repo_root: Path, *, hits_for_uncovered: int = 0) -> Path:
    coverage_dir = repo_root / ".repo_studios" / "tests" / "fixtures" / "test_run_coverage"
    coverage_dir.mkdir(parents=True, exist_ok=True)
    coverage_xml = coverage_dir / "coverage.xml"
    coverage_xml.write_text(
        """<?xml version=\"1.0\"?>
<coverage line-rate=\"0\" branch-rate=\"0\" version=\"1\">
  <sources>
    <source>{source}</source>
  </sources>
  <packages>
    <package name=\"src\" line-rate=\"0\" branch-rate=\"0\">
      <classes>
        <class name=\"alpha\" filename=\"src/alpha.py\" line-rate=\"0\" branch-rate=\"0\">
          <lines>
            <line number=\"2\" hits=\"1\"/>
            <line number=\"6\" hits=\"{hits}\"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""".format(source=repo_root.as_posix(), hits=hits_for_uncovered),
        encoding="utf-8",
    )
    return coverage_xml


def test_generates_structured_artifacts(tmp_path: Path):
    mod = _load_module()

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)
    src_dir = repo_root / "src"
    src_dir.mkdir()
    module_path = src_dir / "alpha.py"
    module_path.write_text(
        "def covered():\n    return 1\n\n\ndef uncovered():\n    return 2\n",
        encoding="utf-8",
    )

    coverage_xml = _write_coverage_fixture(repo_root)

    output_root = repo_root / ".repo_studios" / "reports" / "healthview"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-xml",
            str(coverage_xml),
            "--output-dir",
            str(output_root),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    run_dir = output_root / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240101-0000"
    assert run_dir.is_dir()

    bundle_files = sorted(path.name for path in run_dir.iterdir() if path.is_file())
    assert bundle_files == ["manifest.json", "summary.md", "telemetry.json"]

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["viewer_slug"] == mod.VIEWER_SLUG
    assert manifest["topic"] == mod.TOPIC_SLUG
    assert manifest["run_timestamp"] == "20240101-0000"
    assert manifest["status"] == "ok"
    assert "inputs" in manifest

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["viewer_slug"] == mod.VIEWER_SLUG
    assert telemetry["topic"] == mod.TOPIC_SLUG
    assert telemetry["run_timestamp"] == "20240101-0000"
    assert telemetry["status"] == "ok"

    payload = telemetry["payload"]
    summary = payload["summary"]
    assert summary["status"] == "ok"
    assert summary["total_files"] == 1
    assert summary["total_functions"] == 2
    assert summary["covered_functions"] == 1
    assert summary["overall_coverage_pct"] == pytest.approx(50.0)

    files = payload["files"]
    assert len(files) == 1
    file_entry = files[0]
    assert file_entry["path"].replace("\\", "/") == "src/alpha.py"
    assert file_entry["function_count"] == 2
    assert file_entry["functions_covered"] == 1
    assert file_entry["uncovered_functions"] == ["uncovered"]

    markdown = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "Test Coverage Inventory" in markdown
    assert "src/alpha.py" in markdown

    assert not list((output_root / mod.VIEWER_SLUG / mod.TOPIC_SLUG).glob("latest_*"))


def test_threshold_enforcement_and_pruning(tmp_path: Path):
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()
    src_dir = repo_root / "src"
    src_dir.mkdir()
    module_path = src_dir / "alpha.py"
    module_path.write_text(
        "def covered():\n    return 1\n\n\ndef uncovered():\n    return 2\n",
        encoding="utf-8",
    )

    coverage_xml = _write_coverage_fixture(repo_root)

    output_root = repo_root / ".repo_studios" / "reports" / "healthview"
    base_dir = output_root / mod.VIEWER_SLUG / mod.TOPIC_SLUG
    base_dir.mkdir(parents=True, exist_ok=True)

    stale_slugs = ["20240101-0000", "20240102-0000", "20240103-0000"]
    for slug in stale_slugs:
        run_dir = base_dir / slug
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "telemetry.json").write_text("{}\n", encoding="utf-8")

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-xml",
            str(coverage_xml),
            "--output-dir",
            str(output_root),
            "--timestamp",
            "2024-02-04T00:00:00+00:00",
            "--min-coverage",
            "90",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1

    run_dir = base_dir / "20240204-0000"
    assert run_dir.is_dir()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    payload = telemetry["payload"]
    summary = payload["summary"]
    assert summary["status"] == "threshold_failed"
    assert summary["files_below_threshold"] == ["src/alpha.py"]

    remaining = sorted(path.name for path in base_dir.iterdir() if path.is_dir())
    assert remaining == [
        "20240103-0000",
        "20240204-0000",
    ]

    assert not list(base_dir.glob("latest_*"))


def test_helper_timestamp_and_filename_resolution(tmp_path: Path) -> None:
    mod = _load_module()

    parsed = mod._parse_timestamp("2024-01-01T00:00:00")
    assert parsed.tzinfo is not None
    assert mod._timestamp_slug(parsed) == "20240101-0000"

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    src_dir = repo_root / "src"
    src_dir.mkdir()
    (src_dir / "alpha.py").write_text("print('ok')\n", encoding="utf-8")

    resolved = mod._resolve_filename("src/alpha.py", repo_root=repo_root, sources=[repo_root])
    assert resolved == (repo_root / "src" / "alpha.py").resolve()

    absolute = mod._resolve_filename(str(resolved), repo_root=repo_root, sources=[])
    assert absolute == resolved



def test_refresh_coverage_xml_continue_on_error_emits_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_module()

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)
    src_dir = repo_root / "src"
    src_dir.mkdir()
    (src_dir / "alpha.py").write_text(
        "def covered():\n    return 1\n\n\ndef uncovered():\n    return 2\n",
        encoding="utf-8",
    )

    output_root = repo_root / ".repo_studios" / "reports" / "healthview"
    coverage_xml = repo_root / "coverage.xml"

    calls: list[dict[str, object]] = []

    def _fake_run(argv: list[str], *, cwd: str, check: bool, env: dict[str, str]):
        calls.append({"argv": list(argv), "cwd": cwd, "env": dict(env)})

        class _Result:
            def __init__(self, returncode: int) -> None:
                self.returncode = returncode

        suite = None
        if "-q" in argv:
            suite_index = argv.index("-q") + 1
            if suite_index < len(argv):
                suite = argv[suite_index]
        return _Result(1 if str(suite or "").endswith("tests_suite_a") else 0)

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)

    coverage_mod = types.ModuleType("coverage")
    coverage_exceptions_mod = types.ModuleType("coverage.exceptions")

    class FakeNoDataError(Exception):
        pass

    class FakeCoverage:
        def __init__(self, config_file: str | None = None, data_file: str | None = None) -> None:
            self.config_file = config_file
            self.data_file = data_file

        def load(self) -> None:
            return None

        def xml_report(self, outfile: str) -> None:
            Path(outfile).write_text(
                """<?xml version=\"1.0\"?>
<coverage line-rate=\"0\" branch-rate=\"0\" version=\"1\">
  <sources>
    <source>{source}</source>
  </sources>
  <packages>
    <package name=\"src\" line-rate=\"0\" branch-rate=\"0\">
      <classes>
        <class name=\"alpha\" filename=\"src/alpha.py\" line-rate=\"0\" branch-rate=\"0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
            <line number=\"2\" hits=\"1\"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""".format(source=repo_root.as_posix()),
                encoding="utf-8",
            )

    coverage_mod.Coverage = FakeCoverage
    coverage_exceptions_mod.NoDataError = FakeNoDataError
    monkeypatch.setitem(sys.modules, "coverage", coverage_mod)
    monkeypatch.setitem(sys.modules, "coverage.exceptions", coverage_exceptions_mod)

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-xml",
            str(coverage_xml),
            "--output-dir",
            str(output_root),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--refresh-coverage-xml",
            "--refresh-continue-on-error",
            "--refresh-cov-target",
            ".",
            "--refresh-tests",
            "tests_suite_a",
            "tests_suite_b",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    assert coverage_xml.exists()
    assert len(calls) == 2
    assert "COVERAGE_FILE" in calls[0]["env"]
    assert calls[0]["env"]["COVERAGE_FILE"] == calls[1]["env"]["COVERAGE_FILE"]
    assert "--cov-append" not in calls[0]["argv"]
    assert "--cov-append" in calls[1]["argv"]

    run_dir = output_root / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240101-0000"
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    inputs = manifest["inputs"]
    assert inputs["refresh_coverage_xml"] is True
    assert inputs["refresh_continue_on_error"] is True
    assert inputs["refresh_exit_code"] == 1
    suite_results = inputs["refresh_suite_results"]
    assert isinstance(suite_results, list)
    assert [entry["exit_code"] for entry in suite_results] == [1, 0]


def test_refresh_coverage_xml_without_continue_on_error_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_module()

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)
    output_root = repo_root / ".repo_studios" / "reports" / "healthview"
    coverage_xml = repo_root / "coverage.xml"

    def _fake_run(*_args: object, **_kwargs: object):
        class _Result:
            returncode = 5

        return _Result()

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)

    coverage_mod = types.ModuleType("coverage")
    coverage_exceptions_mod = types.ModuleType("coverage.exceptions")

    class FakeNoDataError(Exception):
        pass

    class FakeCoverage:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def load(self) -> None:
            return None

        def xml_report(self, outfile: str) -> None:
            Path(outfile).write_text("<?xml version=\"1.0\"?><coverage></coverage>", encoding="utf-8")

    coverage_mod.Coverage = FakeCoverage
    coverage_exceptions_mod.NoDataError = FakeNoDataError
    monkeypatch.setitem(sys.modules, "coverage", coverage_mod)
    monkeypatch.setitem(sys.modules, "coverage.exceptions", coverage_exceptions_mod)

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-xml",
            str(coverage_xml),
            "--output-dir",
            str(output_root),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--refresh-coverage-xml",
            "--refresh-tests",
            "tests_suite_a",
            "--log-level",
            "ERROR",
        ]
    )

    # Exit code 2 means error; the refresh_exit_code is captured in result dict
    assert exit_code == 2
    assert not (output_root / mod.VIEWER_SLUG / mod.TOPIC_SLUG).exists()


def test_refresh_omit_tests_creates_and_removes_cov_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_module()

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)
    src_dir = repo_root / "src"
    src_dir.mkdir()
    (src_dir / "alpha.py").write_text("def covered():\n    return 1\n", encoding="utf-8")

    output_root = repo_root / ".repo_studios" / "reports" / "healthview"
    coverage_xml = repo_root / "coverage.xml"

    cov_config_paths: list[Path] = []

    def _fake_run(argv: list[str], *, cwd: str, check: bool, env: dict[str, str]):
        for token in argv:
            if token.startswith("--cov-config="):
                cov_config_paths.append(Path(token.split("=", 1)[1]))

        class _Result:
            returncode = 0

        return _Result()

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)

    coverage_mod = types.ModuleType("coverage")
    coverage_exceptions_mod = types.ModuleType("coverage.exceptions")

    class FakeNoDataError(Exception):
        pass

    class FakeCoverage:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def load(self) -> None:
            return None

        def xml_report(self, outfile: str) -> None:
            Path(outfile).write_text(
                """<?xml version=\"1.0\"?>
<coverage line-rate=\"0\" branch-rate=\"0\" version=\"1\">
  <sources>
    <source>{source}</source>
  </sources>
  <packages>
    <package name=\"src\" line-rate=\"0\" branch-rate=\"0\">
      <classes>
        <class name=\"alpha\" filename=\"src/alpha.py\" line-rate=\"0\" branch-rate=\"0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
            <line number=\"2\" hits=\"1\"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""".format(source=repo_root.as_posix()),
                encoding="utf-8",
            )

    coverage_mod.Coverage = FakeCoverage
    coverage_exceptions_mod.NoDataError = FakeNoDataError
    monkeypatch.setitem(sys.modules, "coverage", coverage_mod)
    monkeypatch.setitem(sys.modules, "coverage.exceptions", coverage_exceptions_mod)

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-xml",
            str(coverage_xml),
            "--output-dir",
            str(output_root),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--refresh-coverage-xml",
            "--refresh-omit-tests",
            "--refresh-tests",
            "tests_suite_a",
            "--refresh-cov-target",
            ".",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    assert cov_config_paths
    assert all(not path.exists() for path in cov_config_paths)
