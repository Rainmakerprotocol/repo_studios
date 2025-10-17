import importlib.util
import sys
from pathlib import Path


def _import_test_log_health_report():
    """Dynamically import .repo_studios/test_log_health_report.py as a module.

    We avoid package import complications by loading from the file path directly.
    """
    module_path = Path(".repo_studios/test_log_health_report.py")
    spec = importlib.util.spec_from_file_location("test_log_health_report", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_pick_best_junit_prefers_multi_test_over_internal(tmp_path: Path):
    mod = _import_test_log_health_report()

    # Create an internal-only junit artifact: tests=1 with testcase classname="pytest" name="internal"
    internal_xml = tmp_path / "junit_internal.xml"
    internal_xml.write_text(
        """
<testsuites>
  <testsuite name="pytest" tests="1" failures="0" errors="1" skipped="0">
    <testcase classname="pytest" name="internal">
      <error message="BrokenPipeError">Traceback...</error>
    </testcase>
  </testsuite>
  </testsuites>
        """.strip(),
        encoding="utf-8",
    )

    # Create a normal multi-test junit artifact with higher total count
    multi_xml = tmp_path / "junit_main.xml"
    multi_xml.write_text(
        """
<testsuites>
  <testsuite name="pytest" tests="3" failures="0" errors="0" skipped="0">
    <testcase classname="pkg.tests" name="test_a" />
    <testcase classname="pkg.tests" name="test_b" />
    <testcase classname="pkg.tests" name="test_c" />
  </testsuite>
</testsuites>
        """.strip(),
        encoding="utf-8",
    )

    picked = mod._pick_best_junit(tmp_path)
    assert picked is not None, "_pick_best_junit returned None"
    assert picked.name == multi_xml.name, f"expected {multi_xml.name}, got {picked.name}"
