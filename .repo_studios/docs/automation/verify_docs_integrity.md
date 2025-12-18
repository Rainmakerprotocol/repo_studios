---
title: verify_docs_integrity Producer
audience: [Copilot, Agents, Developer]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.1.0
updated: 2025-12-18
tags: [automation, producer, docs-integrity, healthview]
related_files:
  - .repo_studios/scripts/producers/verify_docs_integrity.py
  - .repo_studios/tests/tests_producers/test_verify_docs_integrity.py
  - .repo_studios/command_center/docs/db_integrations/db_integration_docs_integrity_validation.md
---

# verify_docs_integrity

## Overview

`verify_docs_integrity.py` audits governed documentation JSON blocks to ensure each fenced payload exposes a stable `content_hash`. The script also refreshes the navigation table contained in `docs/standards/docs_index.md` unless `--no-table` is supplied. When invoked with `--update`, it rewrites mismatched blocks in place and captures a structured run bundle for historical review.

## Invocation

```bash
# default index path and output location
python .repo_studios/scripts/producers/verify_docs_integrity.py --repo-root .

# dry-run with explicit artifact destination
python .repo_studios/scripts/producers/verify_docs_integrity.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports \
  --log-level DEBUG

# autofix mismatched hashes and skip table regeneration
python .repo_studios/scripts/producers/verify_docs_integrity.py \
  --repo-root . \
  --update \
  --no-table
```

### Make target

```bash
make studio-verify-docs-integrity
```

## Artifacts

Each run writes a positional-encoded bundle under:

`.repo_studios/reports/producer_reports/healthview/docs_integrity_validation/<YYYYMMDD-HHMM>/`

The run directory contains exactly three artifacts:

- `manifest.json` – run metadata, catalog identifiers, inputs, and high-level summary counts.
- `summary.md` – human-readable digest of mismatches and remediation guidance.
- `telemetry.json` – compact metrics plus a `payload` containing the full report for agent drill-down.

No `latest_*` pointers are written. History is pruned to the most recent N runs (default 10, configurable via
`--artifacts-to-keep`).

## Exit semantics

| Mode | Exit Code | Notes |
| --- | --- | --- |
| Clean verification | 0 | All governed blocks match their stored `content_hash`. |
| Mismatch (no update) | 1 | At least one governed block is stale. Inspect `report.md` for the offending paths. |
| Update pass | 0 | Mismatched blocks were refreshed because `--update` was supplied. |
| Missing inputs / errors | 1 | Required docs or index file were missing or unreadable; see `log.txt`/`report.md` for details. |

`--exit-codes-hash` preserves the legacy behavior of printing the hash of `docs/standards/exit_code_stability_policy.md` and exits without writing artifacts.

## Integration Notes

- The governed docs index lives at `docs/standards/docs_index.md`. Ensure new governed documents include a fenced JSON block so the producer can manage their `content_hash` values.
- When adding or removing governed docs, update the index JSON block; the script regenerates the markdown table automatically unless `--no-table` is used.
- Record notable enforcement changes in `.repo_studios/command_center/docs/decision_log.md` whenever new documents or policies are added to the governed set.
