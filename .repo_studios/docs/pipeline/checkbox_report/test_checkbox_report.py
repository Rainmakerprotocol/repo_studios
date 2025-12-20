"""Tests for the checkbox report generator."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SPEC_PATH = Path(__file__).with_name("checkbox_report.py")
MODULE_NAME = "docs.pipeline.checkbox_report.checkbox_report"
spec = importlib.util.spec_from_file_location(MODULE_NAME, SPEC_PATH)
checkbox_report = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = checkbox_report
spec.loader.exec_module(checkbox_report)  # type: ignore[arg-type]


def test_scan_file_detects_unchecked_checkboxes(tmp_path: Path) -> None:
    repo_root = tmp_path
    markdown = repo_root / "sample.md"
    markdown.write_text(
        """---
title: sample
---
# Stage One
Intro text

- [ ] First open task
- [x] Completed task

```md
- [ ] ignore inside code
```

Stage Two
-----
* [ ] Second open task
""",
        encoding="utf-8",
    )

    records = checkbox_report.scan_file(markdown, repo_root)

    assert len(records) == 2
    assert records[0].heading_h1 == "Stage One"
    assert records[0].text == "First open task"
    assert records[1].heading_h2 == "Stage Two"
    assert records[1].text == "Second open task"


def test_scan_file_detects_ordered_checkboxes(tmp_path: Path) -> None:
    repo_root = tmp_path
    markdown = repo_root / "ordered.md"
    markdown.write_text(
        """1. [ ] Ordered first\n2. [x] Ordered done\n3. [ ] Ordered third\n""",
        encoding="utf-8",
    )

    records = checkbox_report.scan_file(markdown, repo_root)

    assert [record.text for record in records] == [
        "Ordered first",
        "Ordered third",
    ]


def test_render_markdown_summary_handles_empty_records(tmp_path: Path) -> None:
    repo_root = tmp_path
    outputs = repo_root / "outputs"
    outputs.mkdir()
    csv_path = outputs / "checkbox_report.csv"
    csv_path.touch()
    markdown_path = outputs / "checkbox_report.md"
    script_path = repo_root / "checkbox_report.py"
    script_path.touch()
    search_root = repo_root / ".repo_studios" / "docs" / "pipeline"
    search_root.mkdir(parents=True)

    content = checkbox_report.render_markdown_summary(
        records=[],
        csv_path=csv_path,
        markdown_path=markdown_path,
        repo_root=repo_root,
        script_path=script_path,
        search_root=search_root,
    )

    assert "Total unchecked tasks: 0" in content
    assert "All checklists are currently complete." in content
    assert "checkbox_report.csv" in content
    assert "checkbox_report.md" in content
    assert ".repo_studios/docs/pipeline" in content


def test_main_rejects_search_dir_outside_pipeline(tmp_path: Path) -> None:
    repo_root = tmp_path
    allowed = repo_root / ".repo_studios" / "docs" / "pipeline"
    allowed.mkdir(parents=True)
    (allowed / "ok.md").write_text("# Ok\n", encoding="utf-8")

    outputs = repo_root / "outputs"
    outputs.mkdir()

    rejected_root = repo_root / ".repo_studios"
    try:
        checkbox_report.main(
            [
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(outputs),
                "--search-dir",
                str(rejected_root),
            ]
        )
    except SystemExit as exc:
        assert "must be within" in str(exc)
    else:
        raise AssertionError("Expected checkbox_report to reject search-dir outside pipeline")
