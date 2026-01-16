from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tests.tests_command_center.monkey_patch import helpers

SUMMARIZER_PATH = helpers.COMMAND_CENTER_SCRIPTS / "summarizers" / "summarize_monkey_patch_overview.py"

summarizer_module = helpers.load_optional_module(
    "summarize_monkey_patch_overview",
    SUMMARIZER_PATH,
)

if summarizer_module is None:
    pytest.skip("Monkey Patch overview summarizer not yet implemented.", allow_module_level=True)


def test_summary_includes_signals_and_top_drivers(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)

    consumer_base = repo_root / "consumer"
    producer_base = repo_root / "producer"
    aggregator_base = repo_root / "aggregator"
    output_base = repo_root / "summaries"

    for directory in (consumer_base, producer_base, aggregator_base, output_base):
        directory.mkdir(parents=True, exist_ok=True)

    # Seed two runs so timestamp-only discovery can locate the latest.
    older_slug = "20260116-1700"
    newer_slug = "20260116-1717"

    producer_run = producer_base / newer_slug
    producer_run.mkdir(parents=True, exist_ok=True)
    (producer_run / "matches.json").write_text(
        json.dumps(
            [
                {"file": "src/a.py"},
                {"file": "src/b.py"},
            ]
        ),
        encoding="utf-8",
    )
    (producer_run / "report.json").write_text("[]", encoding="utf-8")

    for slug in (older_slug, newer_slug):
        consumer_run = consumer_base / slug
        consumer_run.mkdir(parents=True, exist_ok=True)
        (consumer_run / "summary.json").write_text(
            json.dumps(
                {
                    "total_findings": 10,
                    "counts_by_risk": {"HIGH": 1, "MODERATE": 2, "SAFE": 7},
                    "run_metadata": {"scan_dir": str(producer_run)},
                }
            ),
            encoding="utf-8",
        )
        (consumer_run / "bundle_summary.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "generated_at": "2026-01-16T17:17:47Z",
                    "source": "structured",
                    "scan_dir": str(producer_run),
                    "top_files": [["src/a.py", 4], ["src/b.py", 3]],
                    "top_categories": [["sys_modules_assignment", 6], ["builtins_mutation", 1]],
                }
            ),
            encoding="utf-8",
        )

    agg_run = aggregator_base / newer_slug
    agg_run.mkdir(parents=True, exist_ok=True)
    (agg_run / "trend.md").write_text("# trend\n", encoding="utf-8")
    (agg_run / "bundle_summary.json").write_text("{}", encoding="utf-8")
    (agg_run / "trend.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-01-16T17:17:47+00:00",
                "mode": "consumer",
                "runs_considered": 2,
                "latest": {
                    "prev": {"ts": "2026-01-16T17:00:31+00:00", "total": 10, "counts": {"HIGH": 1, "MODERATE": 2, "SAFE": 7}},
                    "cur": {"ts": "2026-01-16T17:17:47+00:00", "total": 10, "counts": {"HIGH": 1, "MODERATE": 2, "SAFE": 7}},
                    "delta": {"HIGH": 0, "MODERATE": 0, "SAFE": 0},
                },
                "signals": {
                    "latest": {
                        "has_previous": True,
                        "prev_run_slug": "20260116-1700",
                        "prev_ts": "2026-01-16T17:00:31+00:00",
                        "delta_total": 0,
                        "delta_by_risk": {"HIGH": 0, "MODERATE": 0, "SAFE": 0},
                        "pct_total": 0.0,
                        "pct_by_risk": {"HIGH": 0.0, "MODERATE": 0.0, "SAFE": 0.0},
                        "changed": False,
                        "changed_levels": [],
                    },
                    "rolling_3": {"window": 3, "sample_size": 2, "total_avg": 10.0},
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    fixed_timestamp = datetime(2026, 1, 16, 17, 18, tzinfo=UTC)
    result = summarizer_module.run(
        [
            "--repo-root",
            str(repo_root),
            "--consumer-output-dir",
            str(consumer_base),
            "--producer-output-dir",
            str(producer_base),
            "--aggregator-output-dir",
            str(aggregator_base),
            "--output-dir",
            str(output_base),
            "--timestamp",
            fixed_timestamp.isoformat(),
            "--log-level",
            "ERROR",
            "--artifacts-to-keep",
            "5",
        ]
    )

    run_dir = Path(result["run_dir"])
    summary_path = run_dir / "summary.md"
    assert summary_path.exists()

    summary_md = summary_path.read_text(encoding="utf-8")
    assert "## Trend Signals" in summary_md
    assert "Delta HIGH/MODERATE/SAFE" in summary_md
    assert "## Top Drivers" in summary_md
    assert "### Top Files" in summary_md
    assert "src/a.py" in summary_md
    assert "### Top Categories" in summary_md
    assert "sys_modules_assignment" in summary_md
    assert "## Actions" in summary_md
