from __future__ import annotations

from pathlib import Path

from libraries import (
    build_test_log_report,
    select_junit_artifact,
)


def _write_junit(path: Path, *, tests: int = 2, failures: int = 1, skipped: int = 0, errors: int = 0) -> None:
    content = f"""
<testsuite name=\"pytest\" tests=\"{tests}\" failures=\"{failures}\" errors=\"{errors}\" skipped=\"{skipped}\">
  <testcase classname=\"pkg.test_mod\" name=\"test_pass\" />
  <testcase classname=\"pkg.test_mod\" name=\"test_skip\">
    <skipped message=\"xfail\" />
  </testcase>
</testsuite>
""".strip()
    path.write_text(content, encoding="utf-8")


def _write_pytest_log(path: Path) -> None:
    content = """
=============================== warnings summary ===============================
repo/tests/test_mod.py:10: UserWarning: sample
  warnings.warn("sample")
=========================== slowest 1 durations ================================
1.23s call repo/tests/test_mod.py::test_warn
=================================== FAILURES ===================================
Traceback (most recent call last):
  File "repo/tests/test_mod.py", line 10, in test_warn
    raise AssertionError("boom")
AssertionError: boom
""".lstrip()
    path.write_text(content, encoding="utf-8")


def test_build_test_log_report_parses_artifacts(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    junit_path = logs_dir / "junit_run.xml"
    log_path = logs_dir / "pytest_20250101.txt"
    _write_junit(junit_path)
    _write_pytest_log(log_path)

    result = build_test_log_report(logs_dir)

    summary = result.report["summary"]
    assert summary["total"] == 2
    assert summary["warnings_total"] == 1
    assert summary["tracebacks"] == 1
    warnings = result.report["warnings"]["by_type"]
    assert warnings["UserWarning"] == 1
    slow_tests = result.report["slow_tests"]
    assert slow_tests[0]["nodeid"] == "repo/tests/test_mod.py::test_warn"

    markdown = result.markdown
    assert "## Summary" in markdown


def test_select_junit_artifact_skips_internal_only(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    internal = logs_dir / "junit_internal.xml"
    internal.write_text(
        """
<testsuite name=\"pytest\" tests=\"1\" failures=\"0\">
  <testcase classname=\"pytest\" name=\"internal\" />
</testsuite>
""".strip(),
        encoding="utf-8",
    )
    preferred = logs_dir / "junit_real.xml"
    _write_junit(preferred, tests=4, failures=0, skipped=0, errors=0)

    selected = select_junit_artifact(logs_dir)

    assert selected == preferred
