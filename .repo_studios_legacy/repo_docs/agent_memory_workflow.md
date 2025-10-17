---
title: Agent Memory Workflow
audience: [repo, Jarvis2, Developer]
role: [Operational-Doc, Memory-Source]
owners: ["@docs-owners"]
status: active
version: 0.2.0
updated_at: 2025-09-28
tags: [memory, rag, embeddings, refresh]
related_files:
  - mrp/README.md
  - mrp/policies.md
  - mrp/vector_db/entries.jsonl
  - mrp/vector_db/index.json
  - scripts/embed_training_docs.md
---

## Overview

Machine- and human-readable protocol for when and how agents refresh the memory store
for Retrieval-Augmented Generation (RAG).

## Triggers

* On Markdown/content change under `mrp/training_docs/` (or configured sources)
* Nightly schedule (e.g., once every 24h)
* Manual operator request (on-demand refresh)

## Preconditions & Validations

* Environment active: `.venv` present; required packages installed in same interpreter
* Write permissions to `mrp/vector_db/`
* Policies loaded: denylist/redaction rules from `mrp/policies.md`
* Sufficient disk space for entries growth and logs

## Steps (High Level)

* Redact → Embed → Update Index → Stamp → Verify

### Step Details

1. Redact
  * Apply denylist and regex redaction to sources; tag entries as `redacted: true` when applicable (provenance retained via checksum)

1. Embed
  * Run the embedder with the project interpreter and append/update JSONL entries in `mrp/vector_db/entries.jsonl` (one JSON object per line)
  * Include metadata keys: `model_id`, `model_version`, `dims`, `embedder_version`, `source_path`, `checksum`, `tags`, `updated_at`

1. Update Index
  * If present, update `mrp/vector_db/index.json` (machine) and `mrp/vector_db/INDEX.md` (human) with total entries, distinct source files, and last refresh timestamp

1. Stamp
  * Touch `mrp/vector_db/.last_refresh.stamp` only on successful completion (atomic: write to temp then mv)

1. Verify

* Tail last 200 lines of `tmp_embed_monitoring.log` for errors (`ERROR`, `Traceback`)
* Grep expected filenames in `entries.jsonl` (ensures inclusion)
* Confirm counts increased (line count delta) or checksums changed for updated docs
* If index present, ensure `last_refresh` matches stamp mtime (tolerance ≤ 5s)

## Outputs & Artifacts

* Updated `mrp/vector_db/entries.jsonl`
* Updated `mrp/vector_db/.last_refresh.stamp`
* Optional: refreshed `mrp/vector_db/index.json` and `mrp/vector_db/INDEX.md`
* Log file: `tmp_embed_monitoring.log`
* (Planned) Metrics: `memory_entries_total`, `memory_embed_failures_total`, `memory_last_refresh_timestamp`, `memory_staleness_seconds`

## Success Criteria

* Entries appended or updated (`entries_updated: true`)
* Last refresh staleness ≤ 86,400 seconds (24h) unless override flag set
* No fatal errors in monitoring log (zero `Traceback` occurrences)
* Stamp mtime ≥ newest entry `updated_at`
* Optional index reflects new total count

## Observability (Signals)

| Signal | Source | Status | Notes |
| ------ | ------ | ------ | ----- |
| memory_entries_total | Metrics exporter | planned | Increments on successful embed batch |
| memory_embed_failures_total | Metrics exporter | planned | Increment per failed file / exception |
| memory_last_refresh_timestamp | Metrics exporter | planned | Unix epoch of last success |
| memory_staleness_seconds | Derived (now - last_refresh) | planned | Alert if above threshold |
| entries.jsonl line count | File system | active | Fast proxy for total entries |
| stamp mtime | File system | active | Single source of freshness truth |

Interim (pre-metrics) verification uses file system + log tail only.

## Risks & Rollback

* Over-redaction or denylist blocking: review policies, re-run with adjusted rules
* Partial writes: revert to prior backup of `entries.jsonl` (if maintained) and re-run
* Interpreter mismatch: switch to `.venv` python and re-run

## Anchor Health Cross-Link

If this document's headings are modified or new memory-related plan docs are created, run `make anchor-health` and review `.repo_studios/anchor_health/anchor_report_latest.json` to ensure no new duplicate H1/H2 slug clusters were introduced. Prefer AI-prefixed disambiguating headings for new phased plans (see `repo_standards_markdown.md`).

## Related Docs

* Memory Repo overview: `mrp/README.md`
* Policies: `mrp/policies.md`
* Embed runbook: `scripts/embed_training_docs.md`

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: memory-refresh
      title: Refresh memory embeddings
      triggers: [on_doc_change, nightly, manual]
      preconditions:
        - env_active: true
        - policies_loaded: true
        - can_write_vector_db: true
      steps: [redact, embed, update_index, stamp, verify]
      outputs:
        - mrp/vector_db/entries.jsonl
        - mrp/vector_db/.last_refresh.stamp
      success:
        entries_updated: true
        staleness_below_sec: 86400
      observability:
        counters: [memory_entries_total, memory_embed_failures_total]
        gauges: [memory_last_refresh_timestamp, memory_staleness_seconds]
      rollback:
        - restore_prior_entries_backup
        - adjust_policies_and_retry
    - id: memory-refresh-health-check
      title: Validate memory freshness and integrity
      steps:
        - check_stamp_exists: true
        - compare_stamp_vs_entries: true
        - search_log_for_errors: true
        - verify_staleness_threshold: 86400
      severity: warn
    - id: memory-doc-anchor-scan
      title: Scan for heading collisions post-edit
      steps:
        - run_anchor_health: optional
        - inspect_anchor_report_latest: true
      severity: info
```
<!-- agents:end:agent_instructions -->
