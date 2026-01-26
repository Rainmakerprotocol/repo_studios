from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "command_center" / "scripts" / "cc_producers" / "audit_helper_adoption.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_helper_adoption", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_generates_helper_adoption_report(tmp_path):
    mod = _load_module()
    repo_root = tmp_path / "repo"
    (repo_root / ".repo_studios").mkdir(parents=True)
    scope_dir = repo_root / "sources"
    scope_dir.mkdir(parents=True)
    allowed_targets = repo_root / ".repo_studios" / "command_center" / "docs" / "guardrails" / "allowed_targets.yaml"
    _write(
        allowed_targets,
        "targets:\n  - slug: sample\n    path: sources\n",
    )
    _write(scope_dir / "adopted.py", "from libraries import slugify_relative\n")
    _write(
        scope_dir / "legacy.py",
        """

def _slugify_relative(value):
	return str(value)
	""".strip()
        + "\n",
    )
    _write(scope_dir / "ignored.py", "VALUE = 1\n")

    output_dir = repo_root / ".repo_studios" / "command_center" / "reports" / "helper_adoption"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2025-11-03T17:00:00+00:00",
            "--keep",
            "5",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    # write_report_artifacts now writes to output_dir/viewer/topic/timestamp
    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20251103-1700"
    assert run_dir.is_dir()

    report = json.loads((run_dir / mod.JSON_FILENAME).read_text(encoding="utf-8"))
    helper_entry = next(item for item in report["helpers"] if item["name"] == "slugify_relative")
    assert helper_entry["summary"] == {
        "adopted": 1,
        "legacy": 1,
        "not_applicable": 1,
    }
    target_summary = helper_entry["targets"][0]
    assert target_summary["slug"] == "sample"
    assert target_summary["status"] == {
        "adopted": 1,
        "legacy": 1,
        "not_applicable": 1,
    }
    assert target_summary["files"]["legacy"] == ["sources/legacy.py"]
    assert target_summary["files"]["adopted"] == ["sources/adopted.py"]

    markdown = (run_dir / mod.MARKDOWN_FILENAME).read_text(encoding="utf-8")
    assert "| `slugify_relative` | sample | 1 | 1 | 1 |" in markdown

    # Artifacts are now organized under viewer/topic hierarchy
    assert run_dir.is_dir()


def test_format_filter_and_custom_helpers(tmp_path):
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    (repo_root / ".repo_studios").mkdir(parents=True)
    scope_dir = repo_root / "targets"
    scope_dir.mkdir(parents=True)
    allowed_targets = repo_root / ".repo_studios" / "command_center" / "docs" / "guardrails" / "allowed_targets.yaml"
    _write(
        allowed_targets,
        "targets:\n  - slug: sample\n    path: targets\n",
    )
    _write(
        scope_dir / "producer.py",
        "from libraries import copy_latest_artifact\n_copy_latest = copy_latest_artifact\n",
    )

    output_dir = repo_root / "reports"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2025-11-03T17:00:00+00:00",
            "--keep",
            "2",
            "--helper",
            "copy_latest_artifact",
            "--format",
            "json",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    # write_report_artifacts now writes to output_dir/viewer/topic/timestamp
    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20251103-1700"
    assert (run_dir / mod.JSON_FILENAME).is_file()
    assert not (run_dir / mod.MARKDOWN_FILENAME).exists()

    report = json.loads((run_dir / mod.JSON_FILENAME).read_text(encoding="utf-8"))
    assert [helper["name"] for helper in report["helpers"]] == ["copy_latest_artifact"]
    helper_entry = report["helpers"][0]
    assert helper_entry["summary"] == {
        "adopted": 1,
        "legacy": 0,
        "not_applicable": 0,
    }
    assert helper_entry["files"]["adopted"] == ["targets/producer.py"]
