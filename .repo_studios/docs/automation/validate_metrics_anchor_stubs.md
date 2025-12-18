---
title: validate_metrics_anchor_stubs.py
audience: [Copilot, Agents, Developer]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.1.0
updated: 2025-12-18
tags: [automation, markdown, anchors, metrics, producer, healthview]
related_files:
  - .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py
  - .repo_studios/tests/tests_producers/test_validate_metrics_anchor_stubs.py
  - .repo_studios/Makefile
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - REPORT_NAMING_STANDARDS.md
---

# validate_metrics_anchor_stubs.py

## Purpose

`validate_metrics_anchor_stubs.py` scans repository markdown for links into
`docs/api/metrics_orchestrator.md` and ensures each referenced anchor has a matching
legacy stub entry under the "Legacy Anchor Compatibility" section.

The producer emits a canonical positional bundle (manifest + summary + telemetry), applies
history pruning, and supports an anchor allowlist for transitional exceptions.

## Invocation

```bash
python .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports \
  --artifacts-to-keep 5 \
  --log-level INFO
```

From `.repo_studios/`, run `make studio-validate-metrics-anchor-stubs` to execute with
repository defaults.

### Key arguments

- `--repo-root`: repository root used to resolve markdown files and legacy stub locations.
- `--output-dir`: destination for positional bundles (defaults to
  `.repo_studios/reports/producer_reports`).
- `--legacy-file`: alternate path to the metrics orchestrator markdown file.
- `--allowlist-path`: JSON file containing `{"anchors": [...]}` for temporarily
  permitted missing anchors.
- `--artifacts-to-keep`: number of historical run directories retained after pruning
  (minimum 1, default 10).
- `--log-level`: logging verbosity (`INFO` default).

## Outputs

Each execution produces a canonical bundle under:

`.repo_studios/reports/producer_reports/healthview/metrics_anchor_stub_validation/<YYYYMMDD-HHMM>/`

Containing exactly:

- `manifest.json`: run metadata (viewer/topic/timestamp), catalog provenance, and a compact summary.
- `summary.md`: human-readable digest of findings.
- `telemetry.json`: extracted metrics plus the full payload retained under `payload.report`.

`latest_*` pointers are not written.

Historical run directories are pruned after each execution according to the
configured retention window.

## Diagnostics

- `summary.files_checked`: total markdown files scanned.
- `summary.anchors_referenced`: count of unique anchors encountered in links.
- `summary.missing_count`: anchors remaining after allowlist application.
- `summary.allowlisted_count`: anchors suppressed by the allowlist during the run.
- `missing[*]`: per-anchor records (name plus referencing files) for rapid remediation.

## Testing

`pytest .repo_studios/tests/tests_producers/test_validate_metrics_anchor_stubs.py`

The suite covers clean runs, missing anchor detection, allowlist handling, artifact
creation, and pruning when the retention window is constrained to a single run.

## Operational notes

- Ensure `docs/api/metrics_orchestrator.md` retains the "Legacy Anchor Compatibility"
  section structure; adjust `_normalize_anchor` if the anchor generation rules change.
- Document long-lived exceptions in the architecture log and track them in the
  allowlist JSON with justification.
- Downstream CI jobs should parse `telemetry.json` and `manifest.json` to classify failures
  rather than relying on string matching in logs.
