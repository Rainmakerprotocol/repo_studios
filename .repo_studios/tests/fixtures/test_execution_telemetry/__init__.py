"""Shared fixtures for Test Execution Telemetry orchestration tests."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

SUMMARY_TIMESTAMP = "2025-01-01_1200"
CAPTURE_PREFIX = "pytest_log_capture"

BASIC_LOG = dedent(
        """
        ============================= test session starts =============================
        platform win32 -- Python 3.11.0, pytest-7.4.4
        rootdir: /repo
        collected 2 items

        tests/test_sample.py::test_fail FAILED                                          [50%]
        tests/test_sample.py::test_skip SKIPPED (not run)

        =========================== short test summary info ===========================
        FAILED tests/test_sample.py::test_fail - AssertionError: boom
        SKIPPED tests/test_sample.py::test_skip - reason
        =================== 1 failed, 1 skipped in 0.12s ==============================
        """
).strip()

BASIC_JUNIT = dedent(
        """
        <?xml version='1.0' encoding='utf-8'?>
        <testsuite name="pytest" tests="2" failures="1" errors="0" skipped="1" time="0.12">
            <testcase classname="tests.test_sample" name="test_fail" file="tests/test_sample.py" time="0.01">
                <failure message="AssertionError: boom">details</failure>
            </testcase>
            <testcase classname="tests.test_sample" name="test_skip" file="tests/test_sample.py" time="0.0">
                <skipped message="reason" />
            </testcase>
        </testsuite>
        """
).strip()

TELEMETRY_TIMESTAMP = "2025-12-01_0101"

TELEMETRY_LOG = dedent(
        """
        ============================= test session starts =============================
        collected 2 items

        ============================= slowest 1 durations =============================
        0.750s call tests/sample_test.py::test_slow
        ============================= warnings summary =============================
        tests/sample_test.py:10: UserWarning: sample warning
        =========================== short test summary info ============================
        FAILED tests/sample_test.py::test_failure - AssertionError: boom
        SKIPPED tests/sample_test.py::test_skip - reason
        """
).strip()

TELEMETRY_JUNIT = dedent(
        """
        <testsuite name="pytest" tests="3" failures="1" skipped="1">
            <testcase file="tests/sample_test.py" classname="tests.sample_test" name="test_failure">
                <failure message="AssertionError">boom</failure>
            </testcase>
            <testcase file="tests/sample_test.py" classname="tests.sample_test" name="test_skip">
                <skipped message="reason" />
            </testcase>
            <testcase file="tests/sample_test.py" classname="tests.sample_test" name="test_slow" />
        </testsuite>
        """
).strip()


def write_pytest_bundle(
    log_dir: Path,
    timestamp: str,
    *,
    log_text: str = BASIC_LOG,
    junit_text: str = BASIC_JUNIT,
) -> tuple[Path, Path]:
    """Write a pytest log + junit bundle using the provided text fixtures."""

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"pytest_{timestamp}.txt"
    log_path.write_text(log_text + "\n", encoding="utf-8")
    junit_path = log_dir / f"junit_{timestamp}.xml"
    junit_path.write_text(junit_text + "\n", encoding="utf-8")
    return log_path, junit_path


def seed_capture_run(
    logs_root: Path,
    timestamp: str = TELEMETRY_TIMESTAMP,
    *,
    log_text: str = TELEMETRY_LOG,
    junit_text: str = TELEMETRY_JUNIT,
    run_slug: str | None = None,
) -> Path:
    """Create a pytest_log_capture-* run directory populated with sample artifacts."""

    normalized = timestamp.replace("-", "") if run_slug is None else run_slug
    run_dir = logs_root / f"{CAPTURE_PREFIX}-{normalized}"
    write_pytest_bundle(run_dir, timestamp, log_text=log_text, junit_text=junit_text)
    return run_dir


__all__ = [
    "SUMMARY_TIMESTAMP",
    "CAPTURE_PREFIX",
    "BASIC_LOG",
    "BASIC_JUNIT",
    "TELEMETRY_TIMESTAMP",
    "TELEMETRY_LOG",
    "TELEMETRY_JUNIT",
    "write_pytest_bundle",
    "seed_capture_run",
]
