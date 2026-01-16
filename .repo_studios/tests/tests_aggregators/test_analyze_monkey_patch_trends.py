from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tests.tests_command_center.monkey_patch.helpers import (
    load_monkey_patch_trends_aggregator_module,
    write_consumer_bundle,
    write_producer_run,
)


def test_prefers_consumer_bundles(tmp_path):
    aggregator = load_monkey_patch_trends_aggregator_module()

    consumer_base = tmp_path / "consumer"
    producer_base = tmp_path / "producer"
    output_base = tmp_path / "aggregator"

    scan_a = producer_base / "scan_a"
    scan_b = producer_base / "scan_b"
    scan_a.mkdir(parents=True, exist_ok=True)
    scan_b.mkdir(parents=True, exist_ok=True)

    dt1 = datetime(2025, 11, 23, 16, 0, tzinfo=UTC)
    dt2 = datetime(2025, 11, 24, 16, 0, tzinfo=UTC)
    write_consumer_bundle(
        consumer_base,
        dt1,
        total=5,
        counts={"HIGH": 2, "MODERATE": 1, "SAFE": 2},
        scan_dir=scan_a,
    )
    write_consumer_bundle(
        consumer_base,
        dt2,
        total=6,
        counts={"HIGH": 1, "MODERATE": 3, "SAFE": 2},
        scan_dir=scan_b,
    )

    result = aggregator.run(
        [
            "--consumer-base",
            str(consumer_base),
            "--producer-base",
            str(producer_base),
            "--output-base",
            str(output_base),
            "--artifacts-to-keep",
            "5",
        ]
    )

    assert result["mode"] == "consumer"
    assert result["runs"] == 2
    trend_json = json.loads(Path(result["trend_json"]).read_text(encoding="utf-8"))
    assert trend_json["mode"] == "consumer"
    assert trend_json["runs_considered"] == 2
    assert trend_json["runs"][-1]["run_slug"] == "20251124-1600"
    last_signals = trend_json["runs"][-1]["signals"]
    assert last_signals["has_previous"] is True
    assert last_signals["prev_run_slug"] == "20251123-1600"
    assert last_signals["delta_total"] == 1
    assert last_signals["delta_by_risk"] == {"HIGH": -1, "MODERATE": 2, "SAFE": 0}
    assert last_signals["changed"] is True
    assert last_signals["changed_levels"] == ["HIGH", "MODERATE"]
    assert last_signals["pct_total"] == pytest.approx(0.2)
    assert last_signals["pct_by_risk"]["HIGH"] == pytest.approx(-0.5)
    assert last_signals["pct_by_risk"]["MODERATE"] == pytest.approx(2.0)
    assert last_signals["pct_by_risk"]["SAFE"] == pytest.approx(0.0)

    assert "signals" in trend_json
    assert trend_json["signals"]["latest"]["delta_total"] == 1
    latest = trend_json["latest"]
    assert latest["cur"]["counts"]["MODERATE"] == 3
    assert latest["delta"]["MODERATE"] == 2
    latest_md = Path(result["trend_markdown"]).read_text(encoding="utf-8")
    assert "Run Slug:" in latest_md
    assert "## Delta vs Previous" in latest_md
    snapshot_path = result["consumer_snapshot"]
    assert snapshot_path is not None
    assert Path(snapshot_path).exists()
    # HOP compliance: no pointer files


def test_fallback_to_producer_reports(tmp_path):
    aggregator = load_monkey_patch_trends_aggregator_module()

    consumer_base = tmp_path / "consumer"
    producer_base = tmp_path / "producer"
    output_base = tmp_path / "aggregator"

    dt1 = datetime(2025, 11, 22, 12, 0, tzinfo=UTC)
    dt2 = datetime(2025, 11, 23, 12, 0, tzinfo=UTC)
    write_producer_run(
        producer_base,
        dt1,
        findings=[
            {"category": "sys_modules_assignment", "is_test": False, "is_module_scope": True},
            {"category": "attribute_reassignment_on_import", "is_test": True},
        ],
    )
    write_producer_run(
        producer_base,
        dt2,
        findings=[
            {"category": "global_env_mutation", "is_test": False, "is_module_scope": True},
            {"category": "global_env_mutation", "is_test": True},
            {"category": "attribute_reassignment_on_import", "is_test": True},
        ],
    )

    result = aggregator.run(
        [
            "--consumer-base",
            str(consumer_base),
            "--producer-base",
            str(producer_base),
            "--output-base",
            str(output_base),
            "--artifacts-to-keep",
            "5",
        ]
    )

    assert result["mode"] == "producer_fallback"
    trend_json = json.loads(Path(result["trend_json"]).read_text(encoding="utf-8"))
    assert trend_json["notes"]
    runs = trend_json["runs"]
    assert runs[-1]["counts_by_risk"]["HIGH"] == 1
    assert runs[-1]["counts_by_risk"]["MODERATE"] == 1
    assert runs[-1]["counts_by_risk"]["SAFE"] == 1
    assert result["consumer_snapshot"] is None


def test_retention_prunes_old_runs(tmp_path):
    aggregator = load_monkey_patch_trends_aggregator_module()

    consumer_base = tmp_path / "consumer"
    producer_base = tmp_path / "producer"
    output_base = tmp_path / "aggregator"

    # Seed consumer bundles for the new run.
    scan_dir = producer_base / "scan_dir"
    scan_dir.mkdir(parents=True, exist_ok=True)
    dt1 = datetime(2025, 11, 23, 10, 0, tzinfo=UTC)
    dt2 = datetime(2025, 11, 24, 10, 0, tzinfo=UTC)
    write_consumer_bundle(
        consumer_base,
        dt1,
        total=4,
        counts={"HIGH": 1, "MODERATE": 1, "SAFE": 2},
        scan_dir=scan_dir,
    )
    write_consumer_bundle(
        consumer_base,
        dt2,
        total=5,
        counts={"HIGH": 1, "MODERATE": 2, "SAFE": 2},
        scan_dir=scan_dir,
    )

    # Pre-existing bundles to prune (HOP-compliant slug format).
    stale_dir = output_base / "20251120-1200"
    stale_dir.mkdir(parents=True, exist_ok=True)
    (stale_dir / "trend.json").write_text("{}", encoding="utf-8")
    (stale_dir / "trend.md").write_text("", encoding="utf-8")
    (stale_dir / "bundle_summary.json").write_text("{}", encoding="utf-8")
    recent_dir = output_base / "20251121-1200"
    recent_dir.mkdir(parents=True, exist_ok=True)
    (recent_dir / "trend.json").write_text("{}", encoding="utf-8")
    (recent_dir / "trend.md").write_text("", encoding="utf-8")
    (recent_dir / "bundle_summary.json").write_text("{}", encoding="utf-8")

    result = aggregator.run(
        [
            "--consumer-base",
            str(consumer_base),
            "--producer-base",
            str(producer_base),
            "--output-base",
            str(output_base),
            "--artifacts-to-keep",
            "2",
        ]
    )

    # All directories should match YYYYMMDD-HHMM pattern now
    remaining = [d for d in output_base.iterdir() if d.is_dir()]
    assert len(remaining) == 2
    assert Path(stale_dir.resolve()).as_posix() in [Path(p).resolve().as_posix() for p in result["pruned"]]
    # HOP compliance: no pointer files
