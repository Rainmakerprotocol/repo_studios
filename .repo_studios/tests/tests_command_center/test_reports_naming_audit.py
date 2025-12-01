from __future__ import annotations

import json
from pathlib import Path

from command_center.scripts.utilities import reports_naming_audit as audit


def _create_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("stub", encoding="utf-8")


def test_audit_reports_compliance_and_violations(tmp_path: Path) -> None:
    reports_root = tmp_path / "reports"
    compliant = reports_root / "commandview" / "topic-one" / "20250101-0000" / "manifest.json"
    _create_file(compliant)
    latest_alias = reports_root / "commandview" / "topic-one" / "latest_manifest.json"
    _create_file(latest_alias)
    bad_slug = reports_root / "bad viewer" / "Topic Two" / "20250101-0000" / "SUMMARY.MD"
    _create_file(bad_slug)

    summary = audit.audit_reports(
        reports_root,
        artifact_roles=["manifest.json", "summary.md"],
        allowed_viewers=["commandview", "healthview"],
        ignore_prefixes=[],
        collect_suggestions=True,
    )

    assert summary["total_files"] == 3
    assert summary["compliant_files"] == 1
    assert summary["violation_count"] == 2
    assert {issue for issue in summary["issue_totals"]} == {
        "latest_alias_present",
        "insufficient_depth",
        "invalid_viewer_slug",
        "invalid_topic_slug",
        "unexpected_artifact_name",
    }
    assert summary["latest_aliases"] == ["commandview/topic-one/latest_manifest.json"]
    suggestions = summary["rename_suggestions"]
    assert any(entry["suggested"].endswith("summary.md") for entry in suggestions)


def test_run_writes_outputs_and_threshold(tmp_path: Path) -> None:
    reports_root = tmp_path / "reports"
    good = reports_root / "healthview" / "topic-two" / "20250102-1200" / "summary.md"
    _create_file(good)
    bad = reports_root / "healthview" / "Topic Three" / "20250102_1200" / "metrics.JSON"
    _create_file(bad)

    output_dir = tmp_path / "out"
    args = [
        "--reports-root",
        str(reports_root),
        "--output-dir",
        str(output_dir),
        "--artifact-roles",
        "summary.md",
        "metrics.json",
        "--allowed-viewers",
        "healthview",
        "--fail-threshold",
        "0",
        "--dry-run-rename",
        "--log-level",
        "ERROR",
    ]

    summary = audit.run(args)

    json_path = output_dir / "summary.json"
    md_path = output_dir / "summary.md"
    assert json_path.is_file()
    assert md_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["violation_count"] == summary["violation_count"]
    assert payload["rename_suggestions"] == summary["rename_suggestions"]
    assert any("Topic Three" not in entry["suggested"] for entry in summary["rename_suggestions"])


def test_main_respects_fail_threshold(tmp_path: Path) -> None:
    reports_root = tmp_path / "reports"
    _create_file(reports_root / "commandview" / "demo" / "20250101-0000" / "manifest.json")
    _create_file(reports_root / "commandview" / "demo" / "latest_manifest.json")

    exit_code = audit.main([
        "--reports-root",
        str(reports_root),
        "--artifact-roles",
        "manifest.json",
        "--fail-threshold",
        "0",
        "--log-level",
        "ERROR",
    ])

    assert exit_code == 1

    exit_code_ok = audit.main([
        "--reports-root",
        str(reports_root),
        "--artifact-roles",
        "manifest.json",
        "--fail-threshold",
        "10",
        "--log-level",
        "ERROR",
    ])

    assert exit_code_ok == 0
