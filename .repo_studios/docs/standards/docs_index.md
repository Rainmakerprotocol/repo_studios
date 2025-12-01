# Repo Studios Documentation Index

This index enumerates governed documentation surfaces that participate in Repo Studios integrity checks.

```json
{
  "documents": [
    {
      "category": "global",
      "doc_id": "docs_integrity_handbook",
      "path": "docs/standards/global/std-docs-integrity-handbook.md",
      "stability": "stable",
      "json_block": true
    },
    {
      "category": "global",
      "doc_id": "std_global_markdown_authoring",
      "path": "docs/standards/global/std-global-markdown-authoring.md",
      "stability": "stable",
      "json_block": false
    }
  ],
  "content_hash": "b6713346ddadab055c2b2b3f393def91d120fef716bf209dfcbbc94fb2f6ffc9"
}
```

<!-- BEGIN:DOCS_INDEX_TABLE -->

| Category | Doc ID | File | Summary | JSON | Stability |
|----------|--------|------|---------|------|-----------|
| Global | docs_integrity_handbook | standards/global/std-docs-integrity-handbook.md | docs_integrity_handb | yes | stable |
| Global | std_global_markdown_authoring | standards/global/std-global-markdown-authoring.md | std_global_markdown_ | no | stable |

<!-- END:DOCS_INDEX_TABLE -->

## Healthview Artifacts

The Standards Integrity orchestrator (`.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`) publishes Healthview bundles to `.repo_studios/command_center/reports/healthview/standards_integrity/`, writing `manifest.json`, `summary.md`, and `telemetry.json` for each timestamped run. Invoke `make -C .repo_studios studio-orchestrate-standards` to refresh the artifacts alongside the standards index producers.
