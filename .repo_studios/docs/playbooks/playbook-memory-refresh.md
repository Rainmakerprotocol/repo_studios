---
title: Repo Studios Memory Refresh Playbook
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
  - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 0.3.0
updated: 2025-10-18
summary: >-
  Operational workflow for refreshing and verifying the Repo Studios memory store used for RAG workloads.
tags:
  - memory
  - playbook
  - rag
legacy_source: .repo_studios_legacy/repo_docs/agent_memory_workflow.md
---

# Repo Studios Memory Refresh Playbook

Audience: Repo Studios automation | Memory maintainers

Run this playbook whenever documentation sources change or a scheduled refresh is due. It codifies the redact → embed → index → stamp → verify cycle for the vector store.

---

## Triggers

- Markdown or content updates inside `mrp/training_docs/` or other configured source folders.
- Nightly scheduled job (recommended cadence: 24 hours).
- Manual operator request when memory drift is detected.

---

## Preconditions

- `.venv` is active with required dependencies installed.
- Write access to `mrp/vector_db/` (entries, index, stamp).
- Redaction policies from `mrp/policies.md` are loaded and current.
- Adequate disk space exists for embeddings growth and log rotation.

---

## Execution Steps

1. **Redact**
   - Apply denylist and regex rules to sources, tagging redacted entries as `"redacted": true` while keeping provenance metadata (checksum).
2. **Embed**
   - Use the project interpreter to append or update JSON objects in `mrp/vector_db/entries.jsonl`.
   - Record metadata keys such as `model_id`, `embedder_version`, `source_path`, `checksum`, `tags`, and `updated_at`.
3. **Update Index**
   - Refresh `mrp/vector_db/index.json` and `INDEX.md` with entry totals, distinct sources, and timestamps when maintained.
4. **Stamp**
   - Atomically update `mrp/vector_db/.last_refresh.stamp` after successful embedding (write temp file then move).
5. **Verify**
   - Tail `tmp_embed_monitoring.log` for `ERROR` or `Traceback` entries.
   - Confirm expected files appear in `entries.jsonl` and that line counts increased or checksums changed.
   - Ensure stamp mtime matches the latest entry timestamp within five seconds.

---

## Outputs

- Updated `mrp/vector_db/entries.jsonl` and `.last_refresh.stamp`.
- Optional refreshed index files (`index.json`, `INDEX.md`).
- Monitoring log `tmp_embed_monitoring.log`.

---

## Success Criteria

- `entries.jsonl` updated with new or refreshed embeddings.
- Time since last refresh ≤ 86,400 seconds unless an override is recorded.
- Verification log contains zero fatal errors.
- Stamp timestamp is greater than or equal to the newest entry timestamp.

---

## Observability Signals

| Signal | Source | Status |
| --- | --- | --- |
| `memory_entries_total` | Metrics exporter | planned |
| `memory_embed_failures_total` | Metrics exporter | planned |
| `memory_last_refresh_timestamp` | Metrics exporter | planned |
| `memory_staleness_seconds` | Derived (now - stamp mtime) | planned |
| Entries line count | File system | active |
| Stamp mtime | File system | active |

Until metrics are live, rely on file system checks and log inspection.

---

## Rollback

- Restore the previous backup of `entries.jsonl` if the embed step corrupts data.
- Adjust redaction policies when over-filtering occurs and rerun the workflow.
- Re-run the pipeline using the correct interpreter if dependency mismatches caused failures.

---

## Related Resources

- Memory overview: `mrp/README.md`
- Redaction policies: `mrp/policies.md`
- Embedding CLI guide: `scripts/embed_training_docs.md`
- Markdown standards: `.repo_studios/docs/standards/global/std-global-markdown-authoring.md`

---

## Agent Block (Machine-Readable)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: memory-refresh
      title: Refresh RAG memory store
      triggers: [doc_change, nightly, manual]
      preconditions:
        - env_active: true
        - policies_loaded: true
        - can_write_vector_db: true
      steps: [redact, embed, update_index, stamp, verify]
      outputs:
        - mrp/vector_db/entries.jsonl
        - mrp/vector_db/.last_refresh.stamp
      success:
        staleness_seconds_max: 86400
        errors_in_logs: 0
      observability:
        counters: [memory_entries_total, memory_embed_failures_total]
        gauges: [memory_last_refresh_timestamp, memory_staleness_seconds]
      rollback:
        - restore_backup_entries
        - adjust_policies_and_retry
    - id: memory-anchor-audit
      title: Check headings after doc edits
      steps:
        - run_anchor_health: make anchor-health
        - inspect_anchor_report_latest: true
      severity: info
```
<!-- agents:end:agent_instructions -->
