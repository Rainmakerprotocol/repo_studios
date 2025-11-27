# summarize_standards.py

**Last updated:** 2025-11-27

## Purpose

`summarize_standards.py` provides a lightweight telemetry probe for the standards catalog. It reads
the canonical standards index (surfaced through the `latest_index.yaml` pointer) and the optional
pending extraction queue, then emits log lines that capture rule counts, extraction state, and
pending backlog. The script is typically invoked inside orchestration flows to confirm that the
index is fresh and to highlight any extraction work that still needs review.

## Invocation

```bash
python .repo_studios/scripts/summarizers/summarize_standards.py \
  --label summary
```

### Environment overrides

- `INDEX_PATH`: alternate path to the standards index. Defaults to
    `.repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml` and falls
    back to `.repo_studios/scripts/repo_standards_index.yaml` when the pointer is missing.
- `PENDING_PATH`: alternate path to the pending extraction queue (default `.repo_studios/scripts/repo_standards_pending.yaml`).
- `STANDARDS_SUMMARY_LOG_LEVEL`: logging verbosity (`INFO` by default).

## Outputs

The script writes structured log lines only; there are no artifact bundles. Key messages include:

- Total rule count.
- Extraction statistics (`extracted_count`, `auto_accept`, `pending_file`).
- Markdown-derived rule identifiers (sampled) when present.
- Pending queue line count when the configured pending file exists.

These logs are consumed by orchestrators and CI telemetry to verify that the standards index is
current before downstream automation runs.

## Testing

`pytest .repo_studios/tests/tests_summarizers/test_summarize_standards.py`

The regression tests cover successful summary logging and verify the legacy index fallback behaviour
when the canonical pointer is absent.
