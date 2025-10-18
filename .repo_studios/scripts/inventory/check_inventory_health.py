#!/usr/bin/env python3
"""CI health checks for Repo Studios inventory summary reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_LATEST = ROOT / "reports" / "summary" / "latest" / "summary.json"
BASELINE_PATH = ROOT / "reports" / "summary" / "main_baseline.json"
THRESHOLD_PATH = ROOT / "config" / "ci_inventory_thresholds.json"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def compute_deltas(current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    deltas: Dict[str, Any] = {}
    for key in ("total",):
        if key in current and key in baseline:
            deltas[key] = current[key] - baseline[key]
    return deltas


def check_thresholds(current: Dict[str, Any], thresholds: Dict[str, Any]) -> Dict[str, str]:
    issues: Dict[str, str] = {}

    status_limits = thresholds.get("status_limits", {})
    for status, limit in status_limits.items():
        value = current.get("by_status", {}).get(status, 0)
        if value > limit:
            issues[f"status:{status}"] = f"Status '{status}' count {value} exceeds limit {limit}"

    minimum_assets = thresholds.get("minimum_assets", {})
    for asset_kind, minimum in minimum_assets.items():
        value = current.get("by_asset_kind", {}).get(asset_kind, 0)
        if value < minimum:
            issues[f"asset:{asset_kind}"] = f"Asset kind '{asset_kind}' count {value} below minimum {minimum}"

    consumer_required = thresholds.get("consumer_required", [])
    consumers = current.get("consumers", {})
    for consumer in consumer_required:
        if consumers.get(consumer, 0) == 0:
            issues[f"consumer:{consumer}"] = f"Consumer '{consumer}' missing from summary"

    return issues


def evaluate(current: Dict[str, Any], baseline: Dict[str, Any], thresholds: Dict[str, Any]) -> int:
    issues = check_thresholds(current, thresholds)
    deltas = compute_deltas(current, baseline)

    if issues:
        print("Inventory health check failed:\n")
        for key, message in issues.items():
            print(f"- {key}: {message}")
        return 1

    if deltas:
        print("Inventory health deltas vs baseline:")
        for key, delta in deltas.items():
            print(f"- {key}: {delta:+d}")

    print("Inventory health check passed.")
    return 0


def main(argv: Any = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Repo Studios inventory health thresholds.")
    parser.add_argument("--summary", default=str(SUMMARY_LATEST), help="Path to summary JSON to validate")
    parser.add_argument("--baseline", default=str(BASELINE_PATH), help="Path to baseline summary JSON")
    parser.add_argument(
        "--thresholds",
        default=str(THRESHOLD_PATH),
        help="Path to CI threshold configuration",
    )
    args = parser.parse_args(argv)

    summary_path = Path(args.summary).resolve()
    baseline_path = Path(args.baseline).resolve()
    thresholds_path = Path(args.thresholds).resolve()

    if not summary_path.exists():
        print(f"Summary file not found: {summary_path}", file=sys.stderr)
        return 1

    current = load_json(summary_path)
    baseline = load_json(baseline_path)
    thresholds = load_json(thresholds_path)

    return evaluate(current, baseline, thresholds)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
