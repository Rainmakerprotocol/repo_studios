from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_AGGREGATOR_PATH = Path(__file__).resolve().parents[2] / "scripts" / "aggregators" / "analyze_monkey_patch_trends.py"


def _load_module(name: str, path: Path):
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_consumer_bundle(
    root: Path,
    dt: datetime,
    *,
    total: int,
    counts: dict[str, int],
    scan_dir: Path,
) -> Path:
    name = f"monkey_patch_risk-{dt.strftime('%Y-%m-%d_%H%M%S')}"
    bundle_dir = root / name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "total_findings": total,
        "counts_by_risk": counts,
        "run_metadata": {"scan_dir": str(scan_dir)},
    }
    (bundle_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    metadata = {
        "schema_version": 1,
        "generated_at": dt.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "consumer",
        "scan_dir": str(scan_dir),
    }
    (bundle_dir / "bundle_summary.json").write_text(json.dumps(metadata), encoding="utf-8")
    return bundle_dir


def _write_producer_run(root: Path, dt: datetime, findings: list[dict[str, object]]) -> Path:
    name = dt.strftime("%Y-%m-%d_%H%M%S")
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(json.dumps(findings), encoding="utf-8")
    return run_dir


def test_prefers_consumer_bundles(tmp_path):
    aggregator = _load_module("analyze_monkey_patch_trends", _AGGREGATOR_PATH)

    consumer_base = tmp_path / "consumer"
    producer_base = tmp_path / "producer"
    output_base = tmp_path / "aggregator"

    scan_a = producer_base / "scan_a"
    scan_b = producer_base / "scan_b"
    scan_a.mkdir(parents=True, exist_ok=True)
    scan_b.mkdir(parents=True, exist_ok=True)

    dt1 = datetime(2025, 11, 23, 16, 0, tzinfo=UTC)
    dt2 = datetime(2025, 11, 24, 16, 0, tzinfo=UTC)
    _write_consumer_bundle(
        consumer_base,
        dt1,
        total=5,
        counts={"HIGH": 2, "MODERATE": 1, "SAFE": 2},
        scan_dir=scan_a,
    )
    _write_consumer_bundle(
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
    latest = trend_json["latest"]
    assert latest["cur"]["counts"]["MODERATE"] == 3
    assert latest["delta"]["MODERATE"] == 2
    latest_md = Path(result["trend_markdown"]).read_text(encoding="utf-8")
    assert "Run: " in latest_md
    snapshot_path = result["consumer_snapshot"]
    assert snapshot_path is not None
    assert Path(snapshot_path).exists()
    assert (output_base / "latest_trend.json").exists()


def test_fallback_to_producer_reports(tmp_path):
    aggregator = _load_module("analyze_monkey_patch_trends", _AGGREGATOR_PATH)

    consumer_base = tmp_path / "consumer"
    producer_base = tmp_path / "producer"
    output_base = tmp_path / "aggregator"

    dt1 = datetime(2025, 11, 22, 12, 0, tzinfo=UTC)
    dt2 = datetime(2025, 11, 23, 12, 0, tzinfo=UTC)
    _write_producer_run(
        producer_base,
        dt1,
        findings=[
            {"category": "sys_modules_assignment", "is_test": False, "is_module_scope": True},
            {"category": "attribute_reassignment_on_import", "is_test": True},
        ],
    )
    _write_producer_run(
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
    assert runs[-1]["counts_by_risk"]["MODERATE"] == 2
    assert result["consumer_snapshot"] is None


def test_retention_prunes_old_runs(tmp_path):
    aggregator = _load_module("analyze_monkey_patch_trends", _AGGREGATOR_PATH)

    consumer_base = tmp_path / "consumer"
    producer_base = tmp_path / "producer"
    output_base = tmp_path / "aggregator"

    # Seed consumer bundles for the new run.
    scan_dir = producer_base / "scan_dir"
    scan_dir.mkdir(parents=True, exist_ok=True)
    dt1 = datetime(2025, 11, 23, 10, 0, tzinfo=UTC)
    dt2 = datetime(2025, 11, 24, 10, 0, tzinfo=UTC)
    _write_consumer_bundle(
        consumer_base,
        dt1,
        total=4,
        counts={"HIGH": 1, "MODERATE": 1, "SAFE": 2},
        scan_dir=scan_dir,
    )
    _write_consumer_bundle(
        consumer_base,
        dt2,
        total=5,
        counts={"HIGH": 1, "MODERATE": 2, "SAFE": 2},
        scan_dir=scan_dir,
    )

    # Pre-existing bundles to prune.
    stale_dir = output_base / "monkey_patch_trends-2025-11-20_120000"
    stale_dir.mkdir(parents=True, exist_ok=True)
    (stale_dir / "trend.json").write_text("{}", encoding="utf-8")
    (stale_dir / "trend.md").write_text("", encoding="utf-8")
    (stale_dir / "bundle_summary.json").write_text("{}", encoding="utf-8")
    recent_dir = output_base / "monkey_patch_trends-2025-11-21_120000"
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

    remaining = list(output_base.glob("monkey_patch_trends-*"))
    assert len(remaining) == 2
    assert Path(stale_dir.resolve()).as_posix() in [Path(p).resolve().as_posix() for p in result["pruned"]]
    assert (output_base / "latest_trend.md").exists()
