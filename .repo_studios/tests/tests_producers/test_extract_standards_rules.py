from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from textwrap import dedent

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "producers"
    / "extract_standards_rules.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "extract_standards_rules", _MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_extract_rules_combines_marker_and_heading(tmp_path: Path) -> None:
    mod = _load_module()
    source = tmp_path / "rule_source.md"
    source.write_text(
        dedent(
            """
            <!-- standards:rule
            id: anchor-guideline
            categories: markdown docs
            severity: WARN
            applies_to: docs/**/*.md docs/**/*.markdown
            summary: Provide anchor naming guidance
            rationale: Keeps navigation consistent across docs.
            -->
            <!-- /standards:rule -->

            ### Rule: Provide Inline Anchors
            - Summary: Add consistent anchors for headings
            - Rationale: Ensures cross-link parity
            - Severity: ERROR
            - Applies-To: docs/**/*.md, docs/**/*.markdown
            - Categories: markdown docs
            """
        ).strip(),
        encoding="utf-8",
    )

    rules, diagnostics = mod.extract_rules(source, ["markdown"], set())

    assert {rule["id"] for rule in rules} == {
        "anchor-guideline",
        "provide-inline-anchors",
    }

    marker_rule = next(rule for rule in rules if rule["id"] == "anchor-guideline")
    assert marker_rule["severity"] == "warn"
    assert marker_rule["category_ids"] == ["markdown", "docs"]
    assert marker_rule["applies_to"] == [
        "docs/**/*.md",
        "docs/**/*.markdown",
    ]
    assert marker_rule["source"]["file"] == "rule_source.md"

    heading_rule = next(rule for rule in rules if rule["id"] == "provide-inline-anchors")
    assert heading_rule["severity"] == "error"
    assert heading_rule["category_ids"] == ["markdown", "docs"]
    assert heading_rule["applies_to"] == [
        "docs/**/*.md",
        "docs/**/*.markdown",
    ]

    assert diagnostics["rules_found"] == 2
    assert diagnostics["invalid_severity_rules"] == []
    assert diagnostics["duplicate_ids"] == []


def test_extract_rules_reports_invalid_severity(tmp_path: Path) -> None:
    mod = _load_module()
    source = tmp_path / "invalid_rule.md"
    source.write_text(
        dedent(
            """
            <!-- standards:rule
            id: invalid-severity-rule
            categories: docs
            severity: UNKNOWN
            applies_to: docs/**/*.md
            summary: Missing severity value
            rationale: Should be filtered out
            -->
            <!-- /standards:rule -->
            """
        ).strip(),
        encoding="utf-8",
    )

    rules, diagnostics = mod.extract_rules(source, ["docs"], set())

    assert rules == []
    assert diagnostics["rules_found"] == 0
    assert diagnostics["invalid_severity_rules"] == ["invalid-severity-rule"]
    assert diagnostics["duplicate_ids"] == []
