---
title: Healthview Manifest Example
status: draft
version: 2025-12-04
owner: repo_studios_ai
tags:
  - healthview
  - orchestration
  - examples
---

# Healthview Manifest Schema Example

This example captures the canonical layout for Healthview manifest bundles emitted by the topic
orchestrators. The JSON mirrors the CommandView schema while relocating artifacts under
`.repo_studios/command_center/reports/healthview/<topic>/<timestamp>/`.

```json
{
  "schema_version": 1,
  "viewer": "healthview",
  "topic": "test_execution_telemetry",
  "run_slug": "20251203-1712",
  "generated_at": "2025-12-03T17:12:25+00:00",
  "artifacts": {
    "summary_markdown": ".repo_studios/command_center/reports/healthview/test_execution_telemetry/20251203-1712/test_execution_telemetry_summary.md",
    "summary_json": ".repo_studios/command_center/reports/healthview/test_execution_telemetry/20251203-1712/test_execution_telemetry_summary.json",
    "telemetry": ".repo_studios/command_center/reports/healthview/test_execution_telemetry/20251203-1712/telemetry.json",
    "manifest": ".repo_studios/command_center/reports/healthview/test_execution_telemetry/20251203-1712/manifest.json"
  },
  "inputs": {
    "logs_dir": ".repo_studios/reports/producer_reports/test_log_reports",
    "coverage_report": ".repo_studios/reports/producer_reports/test_coverage_reports",
    "heatmap_run": ".repo_studios/reports/aggregator_reports/churn_complexity_heatmap"
  },
  "telemetry": {
    "topic": "test-execution-telemetry",
    "success": true,
    "steps": [
      {
        "name": "collect",
        "status": "success",
        "started_at": "2025-12-03T17:11:00+00:00",
        "finished_at": "2025-12-03T17:11:05+00:00"
      },
      {
        "name": "analyse",
        "status": "success",
        "started_at": "2025-12-03T17:11:05+00:00",
        "finished_at": "2025-12-03T17:12:10+00:00"
      },
      {
        "name": "summarize",
        "status": "success",
        "started_at": "2025-12-03T17:12:10+00:00",
        "finished_at": "2025-12-03T17:12:25+00:00"
      }
    ]
  }
}
```

## Selector Integration Notes

- **Viewer slug**: always `healthview` to distinguish bundles from CommandView assets.
- **Topic slug**: matches the orchestrator’s topic (for example `test_execution_telemetry`).
- **Bundle naming**: reuse `<topic>_<artifact>_<timestamp>` stems to keep parity with
  CommandView selectors while directing paths under the Healthview root.
- **Retention**: manifests are pruned via `--artifacts-to-keep`; selectors should expect the latest
  run to appear first when sorted lexicographically by `run_slug`.

## Usage Guidance

When wiring UI tabs or agent workflows, load the manifest JSON, present the Markdown summary for
human-readable context, and hydrate drilldown links using the artifact paths above. Telemetry steps
provide runtime diagnostics and should be surfaced in dashboards alongside bundle timestamps.