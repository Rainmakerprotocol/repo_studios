from __future__ import annotations

from pathlib import Path

import pytest

from libraries import SummarizerError, load_summarizer, run_summarizer


def _write_summarizer(tmp_path: Path, exit_code: int) -> Path:
    script = tmp_path / "dummy_summarizer.py"
    script.write_text(
        """
from __future__ import annotations

def run(argv=None):
    return {exit_code}
""".lstrip().format(exit_code=exit_code),
        encoding="utf-8",
    )
    return script


def test_load_and_run_summarizer(tmp_path: Path) -> None:
    script = _write_summarizer(tmp_path, exit_code=0)
    run_callable = load_summarizer(script, module_name="dummy_summarizer")

    run_summarizer(run_callable, argv=["--flag"], name="dummy")


def test_run_summarizer_raises_on_failure(tmp_path: Path) -> None:
    script = _write_summarizer(tmp_path, exit_code=1)
    run_callable = load_summarizer(script, module_name="failing_summarizer")

    with pytest.raises(SummarizerError):
        run_summarizer(run_callable, argv=None, name="failing")


def test_load_summarizer_without_run(tmp_path: Path) -> None:
    script = tmp_path / "missing.py"
    script.write_text("value = 3\n", encoding="utf-8")

    with pytest.raises(AttributeError):
        load_summarizer(script, module_name="missing")
