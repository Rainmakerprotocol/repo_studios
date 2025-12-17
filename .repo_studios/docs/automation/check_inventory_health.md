---
title: Automation — check_inventory_health
audience: [Copilot, Agents, Developers]
role: [Documentation, Automation]
owners: [repo_studios]
status: active
version: 1
updated_at: 2025-12-15
tags: [automation, healthview, inventory, ci, thresholds, positional-encoding]
related_files:
  - .repo_studios/scripts/producers/check_inventory_health.py
  - .repo_studios/tests/tests_producers/test_check_inventory_health.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/libraries/prune_logs.py
---

# Automation — check_inventory_health

See `.github/instructions/markdown.instructions.md` for repo-wide Markdown rules (last reviewed 2025-12-15).

## Goals

- Validate inventory summary metrics against CI thresholds and baseline deltas.
- Emit positional-encoded, canonical artifacts for downstream consumption.
- Exit non-zero when breaches are detected so CI can gate merges.

## System Context

- Script: `.repo_studios/scripts/producers/check_inventory_health.py`
- Viewer/topic: `healthview / inventory_health`
- Default reports root: `.repo_studios/command_center/reports`

Output layout (positional encoding):

```text
<reports_root>/healthview/inventory_health/<YYYYMMDD-HHMM>/
  manifest.json
  summary.md
  telemetry.json
```

Inputs:

- Inventory overview telemetry (default): `.repo_studios/reports/producer_reports/healthview/inventory_overview/`
  - The health check selects the latest `<YYYYMMDD-HHMM>` run folder and reads `telemetry.json`.
- Baseline JSON (default): `.repo_studios/config/inventory/inventory_summary_baseline.json`
- Thresholds JSON (default): `config/ci_inventory_thresholds.json`

Exit codes:

- `0` — passed (no issues)
- `1` — failed (threshold breach detected)
- `2` — summary input missing

## Agent Instructions

<!-- agents:begin:automation_check_inventory_health -->
```yaml
audience: [Copilot, Agents]
script: .repo_studios/scripts/producers/check_inventory_health.py
viewer_slug: healthview
topic: inventory_health
artifacts:
  - role: manifest
    path: healthview/inventory_health/<YYYYMMDD-HHMM>/manifest.json
  - role: summary
    path: healthview/inventory_health/<YYYYMMDD-HHMM>/summary.md
  - role: telemetry
    path: healthview/inventory_health/<YYYYMMDD-HHMM>/telemetry.json
run:
  - make -C .repo_studios studio-check-inventory-health
notes:
  - Prefer telemetry.json for programmatic triage.
  - summary.md is intended for humans scanning CI failures.
```
<!-- agents:end:automation_check_inventory_health -->

## Human Notes

### Typical usage

- Make target:
  - `make -C .repo_studios studio-check-inventory-health`

- Direct invocation:
  - `python .repo_studios/scripts/producers/check_inventory_health.py --repo-root . --output-dir .repo_studios/command_center/reports`

### Retention (pruning)

The producer prunes historical run folders under:

- `<reports_root>/healthview/inventory_health/`

using `.repo_studios/command_center/scripts/libraries/prune_logs.py:prune_run_directories(keep=N, current_run=...)`.

## Reference Prompts

- "Load the latest inventory_health telemetry and list the failing thresholds."
- "Show the delta between baseline total and current total assets for the latest run."

## Update Log

- 2025-12-15 — Added positional-encoding output layout, canonical artifacts, and Make target usage.
